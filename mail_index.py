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
        
        # Find all V* directories (e.g., V10, V11)
        version_dirs = sorted(mail_dir.glob("V*"), reverse=True)
        
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
        mailbox: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query messages from the Envelope Index.
        
        Args:
            limit: Maximum number of messages to return
            since_days: Only return messages from the last N days
            unread_only: Only return unread messages
            mailbox: Filter by mailbox name (e.g., "Inbox")
        
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
        
        # Build SELECT clause with common columns
        # We'll handle missing columns gracefully
        select_columns = [
            "ROWID as message_id",
            "subject",
            "sender",
            "date_received",
            "mailbox",
            "read"
        ]
        
        # Try to add optional columns if they exist
        available_cols = self._get_available_columns()
        optional_columns = {
            'remote_id': 'remote_id',
            'sender_address': 'sender_address', 
            'date_sent': 'date_sent',
            'flags': 'flags'
        }
        
        for col, alias in optional_columns.items():
            if col in available_cols:
                select_columns.append(f"{col} as {alias}")
        
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
        
        if mailbox:
            where_clauses.append("mailbox LIKE ?")
            params.append(f"%{mailbox}%")
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Build final query
        query = f"""
            SELECT {', '.join(select_columns)}
            FROM {table_name}
            WHERE {where_clause}
            ORDER BY date_received DESC
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
            cursor.execute("SELECT DISTINCT mailbox FROM messages WHERE mailbox IS NOT NULL")
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error:
            return []
