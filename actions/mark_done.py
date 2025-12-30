"""
mark_done.py - Track Completed Emails

Maintains a persistent list of emails that have been marked as done.
This allows hiding completed ACTION items from the dashboard.
"""

import json
from pathlib import Path
from typing import Set, List


class DoneTracker:
    """Track which emails have been marked as done."""
    
    def __init__(self, storage_path: str = None):
        """
        Initialize done tracker.
        
        Args:
            storage_path: Path to JSON file for storage (default: ~/.email_triage_done.json)
        """
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path.home() / '.email_triage_done.json'
        
        self._done_emails: Set[str] = self._load()
    
    def _load(self) -> Set[str]:
        """Load done emails from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    return set(data.get('done_emails', []))
            except Exception as e:
                print(f"Failed to load done emails: {e}")
                return set()
        return set()
    
    def _save(self):
        """Save done emails to disk."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'done_emails': list(self._done_emails)
                }, f, indent=2)
        except Exception as e:
            print(f"Failed to save done emails: {e}")
    
    def mark_done(self, email_id: str) -> bool:
        """
        Mark an email as done.
        
        Args:
            email_id: Email ID to mark as done
        
        Returns:
            True if successful
        """
        self._done_emails.add(str(email_id))
        self._save()
        return True
    
    def mark_undone(self, email_id: str) -> bool:
        """
        Unmark an email (move back to active).
        
        Args:
            email_id: Email ID to unmark
        
        Returns:
            True if successful
        """
        self._done_emails.discard(str(email_id))
        self._save()
        return True
    
    def is_done(self, email_id: str) -> bool:
        """
        Check if an email is marked as done.
        
        Args:
            email_id: Email ID to check
        
        Returns:
            True if marked as done
        """
        return str(email_id) in self._done_emails
    
    def get_done_emails(self) -> List[str]:
        """
        Get list of all done email IDs.
        
        Returns:
            List of email IDs
        """
        return list(self._done_emails)
    
    def clear_all(self) -> bool:
        """
        Clear all done emails.
        
        Returns:
            True if successful
        """
        self._done_emails.clear()
        self._save()
        return True
    
    def filter_active_emails(self, emails: List[dict]) -> List[dict]:
        """
        Filter out done emails from a list.
        
        Args:
            emails: List of email dictionaries
        
        Returns:
            List with done emails removed
        """
        return [
            email for email in emails
            if not self.is_done(email.get('id') or email.get('message_id'))
        ]
