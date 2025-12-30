"""
outlook_index.py - Outlook for Mac SQLite Database Access

LOCATION:
~/Library/Group Containers/UBF8T346G9.Office/Outlook/Outlook 15 Profiles/Main Profile/Data/Outlook.sqlite

SCHEMA NOTES:
Outlook uses SQLite but with a different schema than Apple Mail.
The Mail table contains message metadata directly (no joins needed for basic fields).

COMPATIBILITY RISKS:
- Schema changes between Outlook versions
- Path changes in future macOS versions
"""

import sqlite3
import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Any


class OutlookIndexReader:
    """Read-only access to Outlook for Mac's SQLite database."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the reader with the Outlook database.
        
        Args:
            db_path: Explicit path to Outlook.sqlite. If None, auto-discovers.
        """
        if db_path is None:
            db_path = self._find_outlook_db()
        
        if not db_path or not os.path.exists(db_path):
            raise FileNotFoundError(f"Outlook database not found at: {db_path}")
        
        self.db_path = db_path
        self.connection = None
    
    def _find_outlook_db(self) -> Optional[str]:
        """
        Dynamically locate the Outlook database.
        
        Returns:
            Path to Outlook.sqlite or None if not found.
        """
        # Outlook 2016/2019/365 location
        db_path = Path.home() / "Library" / "Group Containers" / "UBF8T346G9.Office" / "Outlook" / "Outlook 15 Profiles" / "Main Profile" / "Data" / "Outlook.sqlite"
        
        if db_path.exists():
            return str(db_path)
        
        # Alternative location
        db_path = Path.home() / "Library" / "Group Containers" / "UBF8T346G9.Office" / "Outlook" / "Outlook 15 Profiles" / "Main Profile" / "Outlook.sqlite"
        
        if db_path.exists():
            return str(db_path)
        
        return None
    
    def connect(self):
        """Open read-only connection to the database."""
        if self.connection is not None:
            return
        
        # Use URI mode with read-only flag
        uri = f"file:{self.db_path}?mode=ro"
        self.connection = sqlite3.connect(uri, uri=True)
        self.connection.row_factory = sqlite3.Row
    
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
    
    def query_messages(
        self,
        limit: int = 20,
        since_days: Optional[int] = None,
        unread_only: bool = False,
        mailbox: Optional[str] = None,
        account: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query messages from the Outlook database.
        
        Args:
            limit: Maximum number of messages to return
            since_days: Only return messages from the last N days
            unread_only: Only return unread messages
            mailbox: Filter by mailbox/folder name
            account: Filter by account name (email address)
        
        Returns:
            List of message dictionaries with available metadata.
        """
        self.connect()
        cursor = self.connection.cursor()
        
        # Build SELECT clause (qualify with table name to avoid ambiguity)
        select_columns = [
            "Mail.Record_RecordID as message_id",
            "Mail.Message_NormalizedSubject as subject",
            "Mail.Message_SenderAddressList as sender",
            "Mail.Message_TimeReceived as date_received",
            "Mail.Message_TimeSent as date_sent",
            "Mail.Message_ReadFlag as read",
            "Mail.Message_Preview as preview",
            "Mail.Record_FolderID as folder_id",
            "Mail.PathToDataFile as message_path"
        ]
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        if since_days is not None:
            # Message_TimeReceived is stored as Unix timestamp
            import time
            cutoff = time.time() - (since_days * 86400)
            where_clauses.append("Mail.Message_TimeReceived >= ?")
            params.append(cutoff)
        
        if unread_only:
            where_clauses.append("Mail.Message_ReadFlag = 0")
        
        if mailbox:
            # Need to join with Folders table
            where_clauses.append("Folders.Folder_Name LIKE ?")
            params.append(f"%{mailbox}%")
        
        # Build query with optional joins
        # For account filtering, we need to join through Folders table
        joins = []
        if mailbox or account:
            joins.append("LEFT JOIN Folders ON Mail.Record_FolderID = Folders.Record_RecordID")
        if account:
            # Join AccountsMail through Folders (Folders.Record_AccountUID links to AccountsMail)
            joins.append("LEFT JOIN AccountsMail ON Folders.Record_AccountUID = AccountsMail.Record_RecordID")
            
            # Filter by account email OR sender domain (since account linking may not work reliably)
            if '@' in account:
                domain = account.split('@')[1]
                where_clauses.append("(AccountsMail.Account_EmailAddress LIKE ? OR Mail.Message_SenderAddressList LIKE ?)")
                params.append(f"%{account}%")
                params.append(f"%@{domain}%")
            else:
                where_clauses.append("AccountsMail.Account_EmailAddress LIKE ?")
                params.append(f"%{account}%")
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        join_clause = " ".join(joins) if joins else ""
        
        query = f"""
            SELECT {', '.join(select_columns)}
            FROM Mail
            {join_clause}
            WHERE {where_clause}
            ORDER BY Mail.Message_TimeReceived DESC
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
                
                # Parse sender address (might be in format like "Name <email@domain.com>")
                sender = msg.get('sender', '') or ''
                if '<' in sender and '>' in sender:
                    # Extract email from "Name <email@domain.com>"
                    match = re.search(r'<([^>]+)>', sender)
                    if match:
                        sender = match.group(1)
                
                msg['sender'] = sender.strip()
                
                # Outlook stores timestamps as Unix timestamps (seconds since 1970-01-01)
                # No conversion needed, just ensure it's a float
                if msg.get('date_received'):
                    try:
                        msg['date_received'] = float(msg['date_received'])
                    except (ValueError, TypeError):
                        msg['date_received'] = None
                
                if msg.get('date_sent'):
                    try:
                        msg['date_sent'] = float(msg['date_sent'])
                    except (ValueError, TypeError):
                        msg['date_sent'] = None
                
                # Extract mailbox name if folder_id available
                if msg.get('folder_id'):
                    try:
                        cursor.execute("SELECT Folder_Name FROM Folders WHERE Folders.Record_RecordID = ?", (msg['folder_id'],))
                        folder_row = cursor.fetchone()
                        if folder_row:
                            msg['mailbox'] = folder_row[0]
                    except:
                        msg['mailbox'] = None
                else:
                    msg['mailbox'] = None
                
                # Also try to get mailbox name from join if available
                if not msg.get('mailbox') and 'Folder_Name' in msg:
                    msg['mailbox'] = msg.get('Folder_Name')
                
                messages.append(msg)
            
            return messages
            
        except sqlite3.Error as e:
            print(f"Warning: Query failed: {e}")
            return []
    
    def get_accounts(self) -> List[str]:
        """
        Get list of unique account email addresses.
        
        Returns:
            List of account email addresses.
        """
        self.connect()
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("SELECT DISTINCT Account_EmailAddress FROM AccountsMail WHERE Account_EmailAddress IS NOT NULL AND Account_EmailAddress != ''")
            accounts = [row[0] for row in cursor.fetchall()]
            return sorted(accounts)
        except sqlite3.Error:
            return []

