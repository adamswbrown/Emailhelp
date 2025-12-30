"""
mail_index.py - Apple Mail Envelope Index SQLite Access

WHY ENVELOPE INDEX:
Apple Mail maintains a SQLite database called "Envelope Index" that stores
metadata for all mail messages. This provides fast, indexed access to message
headers without parsing individual .emlx files.

LOCATION:
~/Library/Mail/V{VERSION}/MailData/Envelope Index

SCHEMA NOTES:
Apple's schema is undocumented and may vary between macOS versions.
We query defensively and handle missing columns gracefully.

COMPATIBILITY RISKS:
- Schema changes between Mail.app versions
- Database format changes (though SQLite is backward-compatible)
- Path changes in future macOS versions
"""

import sqlite3
import os
import glob
import re
from pathlib import Path
from typing import List, Dict, Optional, Any


class MailIndexReader:
    """Read-only access to Apple Mail's Envelope Index database."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the reader with the Envelope Index database.
        
        Args:
            db_path: Explicit path to Envelope Index. If None, auto-discovers.
        """
        if db_path is None:
            db_path = self._find_envelope_index()
        
        if not db_path or not os.path.exists(db_path):
            raise FileNotFoundError(f"Envelope Index not found at: {db_path}")
        
        self.db_path = db_path
        self.connection = None
    
    def _find_envelope_index(self) -> Optional[str]:
        """
        Dynamically locate the most recent Envelope Index.
        
        Returns:
            Path to Envelope Index or None if not found.
        """
        mail_dir = Path.home() / "Library" / "Mail"
        
        if not mail_dir.exists():
            return None
        
        # Check if we have read permissions
        if not os.access(mail_dir, os.R_OK):
            raise PermissionError(
                f"Cannot access {mail_dir}. "
                "macOS requires Full Disk Access permission.\n"
                "To fix: System Settings > Privacy & Security > Full Disk Access\n"
                "Add Terminal (or your Python interpreter) to the list."
            )
        
        # Find all V* directories (e.g., V10, V11)
        try:
            version_dirs = sorted(mail_dir.glob("V*"), reverse=True)
        except PermissionError:
            raise PermissionError(
                f"Cannot read {mail_dir}. "
                "macOS requires Full Disk Access permission.\n"
                "To fix: System Settings > Privacy & Security > Full Disk Access\n"
                "Add Terminal (or your Python interpreter) to the list."
            )
        
        if not version_dirs:
            # Directory exists but no V* folders found
            # This might mean Mail hasn't been run, or it's a different structure
            return None
        
        for version_dir in version_dirs:
            envelope_path = version_dir / "MailData" / "Envelope Index"
            if envelope_path.exists():
                return str(envelope_path)
        
        return None
    
    def connect(self):
        """Open read-only connection to the database."""
        if self.connection is not None:
            return
        
        # Use URI mode with read-only flag to prevent any writes
        uri = f"file:{self.db_path}?mode=ro"
        self.connection = sqlite3.connect(uri, uri=True)
        self.connection.row_factory = sqlite3.Row  # Access columns by name
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def _get_available_columns(self) -> List[str]:
        """
        Query the schema to get available columns in the messages table.
        
        Returns:
            List of column names.
        """
        cursor = self.connection.cursor()
        
        # Try common table names (schema may vary)
        for table_name in ['messages', 'message', 'mail']:
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]
                if columns:
                    return columns
            except sqlite3.Error:
                continue
        
        return []
    
    def query_messages(
        self,
        limit: int = 20,
        since_days: Optional[int] = None,
        unread_only: bool = False,
        mailbox: Optional[str] = None,
        account: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query messages from the Envelope Index.
        
        Args:
            limit: Maximum number of messages to return
            since_days: Only return messages from the last N days
            unread_only: Only return unread messages
            mailbox: Filter by mailbox name (e.g., "Inbox")
            account: Filter by account name (e.g., "Exchange", "iCloud")
        
        Returns:
            List of message dictionaries with available metadata.
        """
        self.connect()
        
        # Build SQL query defensively
        # Common column mappings (may vary by version):
        # - ROWID: unique message ID
        # - subject: message subject
        # - sender/sender_address: sender email
        # - date_received: timestamp
        # - mailbox: mailbox name
        # - read: read flag (0/1)
        
        # Start with base query - try different table names
        cursor = self.connection.cursor()
        
        # Attempt to find the messages table
        table_name = None
        for candidate in ['messages', 'message', 'mail']:
            try:
                cursor.execute(f"SELECT 1 FROM {candidate} LIMIT 1")
                table_name = candidate
                break
            except sqlite3.Error:
                continue
        
        if table_name is None:
            raise RuntimeError("Could not find messages table in Envelope Index")
        
        # Check which tables exist for joins
        # According to Apple Mail schema: sender and subject are foreign keys
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = {row[0] for row in cursor.fetchall()}
        
        has_addresses_table = 'addresses' in all_tables
        has_subjects_table = 'subjects' in all_tables
        has_mailboxes_table = 'mailboxes' in all_tables
        
        # Build SELECT clause with proper joins
        # sender and subject are foreign keys, so we need to join to get actual values
        if has_addresses_table:
            sender_col = "addr.address as sender"
        else:
            # Fallback: use sender column directly (might be integer ID)
            sender_col = f"{table_name}.sender as sender"
        
        if has_subjects_table:
            subject_col = "subj.subject as subject"
        else:
            # Fallback: use subject column directly (might be integer ID)
            subject_col = f"{table_name}.subject as subject"
        
        # Determine mailbox column - use URL from mailboxes table if available
        # We'll always try to join with mailboxes to get the URL, not just for filtering
        if has_mailboxes_table:
            mailbox_col = "mb.url as mailbox"
        else:
            mailbox_col = f"{table_name}.mailbox as mailbox"
        
        select_columns = [
            f"{table_name}.ROWID as message_id",
            subject_col,
            sender_col,
            f"{table_name}.date_received as date_received",
            mailbox_col,
            f"{table_name}.read as read"
        ]
        
        # Try to add optional columns if they exist
        available_cols = self._get_available_columns()
        optional_columns = {
            'remote_id': 'remote_id',
            'sender_address': 'sender_address', 
            'date_sent': 'date_sent',
            'flags': 'flags',
            'account': 'account'  # Account name (Exchange, iCloud, etc.)
        }
        
        for col, alias in optional_columns.items():
            if col in available_cols:
                select_columns.append(f"{table_name}.{col} as {alias}")
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        if since_days is not None:
            # date_received is typically a Unix timestamp
            where_clauses.append("date_received >= ?")
            import time
            cutoff = int(time.time()) - (since_days * 86400)
            params.append(cutoff)
        
        if unread_only:
            where_clauses.append("read = 0")
        
        # Check if we need to join with mailboxes table for account filtering
        # Account filtering requires joining with mailboxes table to check url column
        needs_mailbox_join = account is not None
        
        if mailbox and not needs_mailbox_join:
            # Only add mailbox filter here if we're not doing a join
            where_clauses.append("mailbox LIKE ?")
            params.append(f"%{mailbox}%")
        
        # Build joins for addresses, subjects, and mailboxes tables
        joins = []
        
        # Join with addresses table to get sender email address
        if has_addresses_table:
            joins.append(f"LEFT JOIN addresses addr ON {table_name}.sender = addr.rowid")
        
        # Join with subjects table to get subject text
        if has_subjects_table:
            joins.append(f"LEFT JOIN subjects subj ON {table_name}.subject = subj.rowid")
        
        # Always join with mailboxes table to get mailbox URL (needed for display and filtering)
        if has_mailboxes_table:
            joins.append(f"LEFT JOIN mailboxes mb ON {table_name}.mailbox = mb.ROWID")
            
            # Add account/mailbox filtering if needed
            if account:
                where_clauses.append("mb.url LIKE ?")
                params.append(f"%{account}%")
            
            if mailbox:
                where_clauses.append("mb.url LIKE ?")
                params.append(f"%{mailbox}%")
        else:
            # Fallback: try filtering on mailbox column directly (may not work if it's integer)
            if account:
                where_clauses.append(f"{table_name}.mailbox LIKE ?")
                params.append(f"%{account}%")
        
        # Qualify WHERE clause columns to avoid ambiguity
        qualified_where_clauses = []
        for clause in where_clauses:
            # Qualify column names that might be ambiguous
            clause = re.sub(r'\bdate_received\b', f'{table_name}.date_received', clause)
            clause = re.sub(r'\bread\b', f'{table_name}.read', clause)
            clause = re.sub(r'\bmailbox\b(?!\.)', f'{table_name}.mailbox', clause)
            qualified_where_clauses.append(clause)
        
        where_clause = " AND ".join(qualified_where_clauses) if qualified_where_clauses else "1=1"
        join_clause = " ".join(joins) if joins else ""
        
        # Build final query
        query = f"""
            SELECT {', '.join(select_columns)}
            FROM {table_name}
            {join_clause}
            WHERE {where_clause}
            ORDER BY {table_name}.date_received DESC
            LIMIT ?
        """
        
        params.append(limit)
        
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            messages = []
            for row in rows:
                msg = dict(row)
                
                # Add .emlx path if we can construct it
                # Path pattern: ~/Library/Mail/V*/mailbox_path/Messages/message_id.emlx
                # This is a best-effort attempt - actual path construction is complex
                msg['emlx_path'] = None  # Will be populated if needed
                
                messages.append(msg)
            
            return messages
            
        except sqlite3.Error as e:
            # If query fails, return empty list and log error
            print(f"Warning: Query failed: {e}")
            return []
    
    def get_mailboxes(self) -> List[str]:
        """
        Get list of unique mailbox names.
        
        Returns:
            List of mailbox names.
        """
        self.connect()
        cursor = self.connection.cursor()
        
        # Try to find mailbox column
        try:
            cursor.execute("SELECT DISTINCT mailbox FROM messages WHERE mailbox IS NOT NULL ORDER BY mailbox")
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error:
            return []
    
    def get_accounts(self) -> List[str]:
        """
        Get list of unique account names from mailbox paths.
        
        Apple Mail typically stores mailboxes with account names in the path.
        For example: "Exchange/INBOX" or "iCloud/Sent"
        
        Returns:
            List of account names extracted from mailbox paths.
        """
        self.connect()
        cursor = self.connection.cursor()
        
        try:
            # First check available columns for debugging
            available_cols = self._get_available_columns()
            
            # Get all distinct mailbox paths
            cursor.execute("SELECT DISTINCT mailbox FROM messages WHERE mailbox IS NOT NULL LIMIT 100")
            mailboxes = [row[0] for row in cursor.fetchall()]
            
            # Extract account names (typically the first part of the path)
            accounts = set()
            has_int_mailboxes = False
            for mailbox in mailboxes:
                # Skip if mailbox is None, empty
                if not mailbox:
                    continue
                
                # Track if we have integer mailbox IDs (need to join with mailboxes table)
                if isinstance(mailbox, int):
                    has_int_mailboxes = True
                    continue
                
                # Convert to string if it's not already (handles integer mailbox IDs)
                if not isinstance(mailbox, str):
                    continue
                
                # Split by common path separators
                parts = mailbox.replace('\\', '/').split('/')
                
                # The account name is usually the first non-empty part
                for part in parts:
                    if part and not part.startswith('.'):
                        accounts.add(part)
                        break
            
            # If no accounts found from mailbox paths, try account column directly
            if not accounts:
                if 'account' in available_cols:
                    cursor.execute("SELECT DISTINCT account FROM messages WHERE account IS NOT NULL AND account != ''")
                    account_rows = cursor.fetchall()
                    accounts = {str(row[0]).strip() for row in account_rows if row[0]}
            
            # If still no accounts, try mailbox_path column (some versions use this)
            if not accounts:
                if 'mailbox_path' in available_cols:
                    cursor.execute("SELECT DISTINCT mailbox_path FROM messages WHERE mailbox_path IS NOT NULL LIMIT 100")
                    paths = cursor.fetchall()
                    for row in paths:
                        path = row[0]
                        if isinstance(path, str) and path:
                            parts = path.replace('\\', '/').split('/')
                            for part in parts:
                                if part and not part.startswith('.'):
                                    accounts.add(part.strip())
                                    break
            
            # If mailbox column contains integers, join with mailboxes table to get paths
            # Based on Apple Mail schema: mailbox column is ROWID referencing mailboxes table
            if not accounts and has_int_mailboxes:
                try:
                    # Check if mailboxes table exists
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mailboxes'")
                    if cursor.fetchone():
                        # Get mailbox URLs/paths from mailboxes table
                        # The url column contains paths like "Exchange/INBOX" or "iCloud/Sent"
                        cursor.execute("""
                            SELECT DISTINCT mail.url
                            FROM messages m
                            JOIN mailboxes mail ON m.mailbox = mail.ROWID
                            WHERE mail.url IS NOT NULL AND mail.url != ''
                            LIMIT 100
                        """)
                        for url_row in cursor.fetchall():
                            url = url_row[0]
                            if isinstance(url, str) and url:
                                # URL format is typically like "Exchange/INBOX" or "iCloud/Sent"
                                parts = url.replace('\\', '/').split('/')
                                for part in parts:
                                    if part and not part.startswith('.'):
                                        accounts.add(part.strip())
                                        break
                except sqlite3.Error:
                    # If join fails, try checking mailboxes table directly
                    try:
                        cursor.execute("PRAGMA table_info(mailboxes)")
                        table_cols = [col[1] for col in cursor.fetchall()]
                        if 'url' in table_cols:
                            cursor.execute("SELECT DISTINCT url FROM mailboxes WHERE url IS NOT NULL AND url != '' LIMIT 100")
                            for url_row in cursor.fetchall():
                                url = url_row[0]
                                if isinstance(url, str) and url:
                                    parts = url.replace('\\', '/').split('/')
                                    for part in parts:
                                        if part and not part.startswith('.'):
                                            accounts.add(part.strip())
                                            break
                    except sqlite3.Error:
                        pass
            
            # If still no accounts, check other tables for account column
            if not accounts:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                all_tables = cursor.fetchall()
                for table_row in all_tables:
                    table_name = table_row[0]
                    if table_name == 'messages':
                        continue  # Already checked
                    try:
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        table_cols = [col[1] for col in cursor.fetchall()]
                        if 'account' in table_cols:
                            cursor.execute(f"SELECT DISTINCT account FROM {table_name} WHERE account IS NOT NULL AND account != ''")
                            for acc_row in cursor.fetchall():
                                if acc_row[0]:
                                    accounts.add(str(acc_row[0]).strip())
                    except sqlite3.Error:
                        continue
            
            return sorted(list(accounts)) if accounts else []
        except sqlite3.Error:
            return []
