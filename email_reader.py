"""
email_reader.py - Unified interface for reading emails from different sources

This module provides a unified interface that works with both:
- Apple Mail (via MailIndexReader)
- Outlook for Mac (via OutlookIndexReader)

The interface abstracts away the differences between the two databases.
"""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from mail_index import MailIndexReader
from outlook_index import OutlookIndexReader


class EmailReader(ABC):
    """Abstract base class for email readers."""
    
    @abstractmethod
    def query_messages(
        self,
        limit: int = 20,
        since_days: Optional[int] = None,
        unread_only: bool = False,
        mailbox: Optional[str] = None,
        account: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query messages from the email database."""
        pass
    
    @abstractmethod
    def get_accounts(self) -> List[str]:
        """Get list of available accounts."""
        pass
    
    @abstractmethod
    def __enter__(self):
        """Context manager entry."""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


class AppleMailReader(EmailReader):
    """Wrapper for Apple Mail database reader."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.reader = MailIndexReader(db_path=db_path)
    
    def query_messages(self, **kwargs) -> List[Dict[str, Any]]:
        return self.reader.query_messages(**kwargs)
    
    def get_accounts(self) -> List[str]:
        return self.reader.get_accounts()
    
    def __enter__(self):
        self.reader.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reader.__exit__(exc_type, exc_val, exc_tb)


class OutlookReader(EmailReader):
    """Wrapper for Outlook database reader."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.reader = OutlookIndexReader(db_path=db_path)
    
    def query_messages(self, **kwargs) -> List[Dict[str, Any]]:
        return self.reader.query_messages(**kwargs)
    
    def get_accounts(self) -> List[str]:
        return self.reader.get_accounts()
    
    def __enter__(self):
        self.reader.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reader.__exit__(exc_type, exc_val, exc_tb)


def create_reader(client: Optional[str] = None, db_path: Optional[str] = None) -> EmailReader:
    """
    Create an email reader for the specified client.
    
    Args:
        client: 'apple-mail', 'outlook', or None for auto-detect
        db_path: Optional explicit database path
        
    Returns:
        EmailReader instance
        
    Raises:
        FileNotFoundError: If no email database is found
    """
    if client == 'apple-mail':
        return AppleMailReader(db_path=db_path)
    elif client == 'outlook':
        return OutlookReader(db_path=db_path)
    elif client is None:
        # Auto-detect: try Apple Mail first, then Outlook
        try:
            reader = AppleMailReader(db_path=db_path)
            # Test if it works by trying to connect
            with reader:
                reader.get_accounts()
            return reader
        except (FileNotFoundError, Exception):
            # Apple Mail not available, try Outlook
            try:
                reader = OutlookReader(db_path=db_path)
                with reader:
                    reader.get_accounts()
                return reader
            except (FileNotFoundError, Exception):
                raise FileNotFoundError(
                    "Could not find Apple Mail or Outlook database.\n"
                    "Make sure Apple Mail or Outlook is installed and has been run at least once."
                )
    else:
        raise ValueError(f"Unknown email client: {client}. Use 'apple-mail' or 'outlook'")

