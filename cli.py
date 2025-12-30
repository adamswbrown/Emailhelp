"""
cli.py - Command-Line Interface and Output Formatting

Provides argparse configuration and ledger-style table output.
"""

import argparse
from typing import List, Dict, Any
from datetime import datetime


class CLI:
    """Command-line interface handler."""
    
    @staticmethod
    def create_parser() -> argparse.ArgumentParser:
        """
        Create and configure argument parser.
        
        Returns:
            Configured ArgumentParser
        """
        parser = argparse.ArgumentParser(
            prog='mail-accounting',
            description='Apple Mail Accounting & Categorization CLI - Deterministic email triage',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # List 20 most recent emails
  python main.py
  
  # List emails from Exchange account only
  python main.py --account Exchange --limit 50
  
  # List available accounts
  python main.py --list-accounts
  
  # List 50 recent emails with explanations
  python main.py --limit 50 --why
  
  # Show only unread emails from last 7 days in Exchange
  python main.py --unread-only --since 7 --account Exchange
  
  # Filter by mailbox
  python main.py --mailbox Inbox --limit 30
  
  # Show only ACTION items from Exchange
  python main.py --category ACTION --account Exchange
            """
        )
        
        # Query filters
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Maximum number of emails to display (default: 20)'
        )
        
        parser.add_argument(
            '--since',
            type=int,
            metavar='DAYS',
            help='Only show emails from the last N days'
        )
        
        parser.add_argument(
            '--unread-only',
            action='store_true',
            help='Only show unread emails'
        )
        
        parser.add_argument(
            '--mailbox',
            type=str,
            help='Filter by mailbox name (e.g., "Inbox")'
        )
        
        parser.add_argument(
            '--account',
            type=str,
            help='Filter by account name (e.g., "Exchange", "iCloud")'
        )
        
        parser.add_argument(
            '--list-accounts',
            action='store_true',
            help='List all available accounts and exit'
        )
        
        parser.add_argument(
            '--category',
            type=str,
            choices=['ACTION', 'FYI', 'IGNORE'],
            help='Filter by classification category'
        )
        
        # Output options
        parser.add_argument(
            '--why',
            action='store_true',
            help='Show signal breakdown and score explanation for each email'
        )
        
        parser.add_argument(
            '--user-name',
            type=str,
            help='Your name (to detect personal mentions in scoring)'
        )
        
        parser.add_argument(
            '--db-path',
            type=str,
            help='Explicit path to Envelope Index database (auto-detects if not provided)'
        )
        
        return parser


class TableFormatter:
    """Format email data as ledger-style tables."""
    
    @staticmethod
    def format_ledger(emails: List[Dict[str, Any]], show_explanations: bool = False) -> str:
        """
        Format emails as a ledger-style table.
        
        Args:
            emails: List of email dictionaries with metadata
            show_explanations: Whether to show signal breakdowns
        
        Returns:
            Formatted table string
        """
        if not emails:
            return "No emails found matching criteria."
        
        # Build table rows
        lines = []
        
        # Header
        header = f"{'DATE':<12} | {'FROM':<25} | {'SUBJECT':<35} | {'SCORE':>5} | {'CLASS':<7} | {'MAILBOX':<15}"
        lines.append(header)
        lines.append('-' * len(header))
        
        # Data rows
        for email in emails:
            date_str = TableFormatter._format_date(email.get('date_received'))
            sender_str = TableFormatter._format_sender(email.get('sender', ''), max_len=25)
            subject_str = TableFormatter._format_text(email.get('subject', ''), max_len=35)
            score = email.get('score', 0)
            category = email.get('category', 'UNKNOWN')
            mailbox = TableFormatter._format_text(email.get('mailbox', ''), max_len=15)
            
            row = f"{date_str:<12} | {sender_str:<25} | {subject_str:<35} | {score:>5} | {category:<7} | {mailbox:<15}"
            lines.append(row)
            
            # Add explanation if requested
            if show_explanations and 'signals' in email:
                explanation = TableFormatter._format_explanation(email['signals'])
                lines.append(f"  └─ Signals: {explanation}")
                lines.append('')
        
        return '\n'.join(lines)
    
    @staticmethod
    def _format_date(timestamp: Any) -> str:
        """
        Format Unix timestamp as YYYY-MM-DD.
        
        Args:
            timestamp: Unix timestamp (int/float) or None
        
        Returns:
            Formatted date string
        """
        if timestamp is None:
            return 'Unknown'
        
        try:
            dt = datetime.fromtimestamp(int(timestamp))
            return dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError, OSError):
            return 'Invalid'
    
    @staticmethod
    def _format_sender(sender: str, max_len: int = 25) -> str:
        """
        Format sender address for display.
        
        Args:
            sender: Full sender address
            max_len: Maximum length
        
        Returns:
            Formatted sender string
        """
        if not sender:
            return 'Unknown'
        
        # Extract domain if email address
        if '@' in sender:
            # Try to get just the domain
            parts = sender.split('@')
            if len(parts) == 2:
                domain = parts[1].strip()
                if len(domain) <= max_len:
                    return domain
        
        # Truncate if too long
        if len(sender) > max_len:
            return sender[:max_len-3] + '...'
        
        return sender
    
    @staticmethod
    def _format_text(text: str, max_len: int = 35) -> str:
        """
        Format text field for display.
        
        Args:
            text: Text to format
            max_len: Maximum length
        
        Returns:
            Formatted text string
        """
        if not text:
            return ''
        
        # Replace newlines and excessive whitespace
        text = ' '.join(text.split())
        
        # Truncate if too long
        if len(text) > max_len:
            return text[:max_len-3] + '...'
        
        return text
    
    @staticmethod
    def _format_explanation(signals: Dict[str, int]) -> str:
        """
        Format signal breakdown for display.
        
        Args:
            signals: Signal name -> points dict
        
        Returns:
            Formatted explanation string
        """
        parts = []
        for signal_name, points in sorted(signals.items(), key=lambda x: -abs(x[1])):
            sign = '+' if points >= 0 else ''
            parts.append(f"{signal_name}({sign}{points})")
        
        return ', '.join(parts)
    
    @staticmethod
    def format_summary(emails: List[Dict[str, Any]]) -> str:
        """
        Format summary statistics.
        
        Args:
            emails: List of email dictionaries
        
        Returns:
            Summary string
        """
        if not emails:
            return "No emails to summarize."
        
        # Count by category
        action_count = sum(1 for e in emails if e.get('category') == 'ACTION')
        fyi_count = sum(1 for e in emails if e.get('category') == 'FYI')
        ignore_count = sum(1 for e in emails if e.get('category') == 'IGNORE')
        
        total = len(emails)
        
        lines = [
            f"\nSummary:",
            f"  Total emails: {total}",
            f"  ACTION:  {action_count:3d} ({action_count/total*100:5.1f}%)",
            f"  FYI:     {fyi_count:3d} ({fyi_count/total*100:5.1f}%)",
            f"  IGNORE:  {ignore_count:3d} ({ignore_count/total*100:5.1f}%)",
        ]
        
        return '\n'.join(lines)
