#!/usr/bin/env python3
"""
main.py - Application Entry Point

macOS Apple Mail Accounting & Categorization CLI

WHAT THIS TOOL DOES:
- Reads Apple Mail's Envelope Index SQLite database
- Scores emails using deterministic weighted signals
- Classifies emails into ACTION / FYI / IGNORE categories
- Displays results in a ledger-style accounting table

WHAT THIS TOOL DOES NOT DO:
- Send emails
- Modify emails or mailboxes
- Use AI/GPT
- Run in background
- Make network calls

This is a read-only, deterministic email accounting tool.
"""

import sys
from typing import List, Dict, Any

from mail_index import MailIndexReader
from preview import EmailPreview
from scoring import EmailScorer
from classifier import EmailClassifier, EmailCategory
from cli import CLI, TableFormatter


def process_emails(
    messages: List[Dict[str, Any]],
    scorer: EmailScorer,
    show_preview: bool = False
) -> List[Dict[str, Any]]:
    """
    Process messages: extract preview, score, and classify.
    
    Args:
        messages: Raw message dicts from MailIndexReader
        scorer: EmailScorer instance
        show_preview: Whether to extract body previews
    
    Returns:
        List of enriched email dicts with scores and categories
    """
    processed = []
    
    for msg in messages:
        # Extract fields
        sender = msg.get('sender', '') or ''
        subject = msg.get('subject', '') or ''
        preview_text = None
        
        # Extract preview if requested and path available
        if show_preview and msg.get('emlx_path'):
            preview_text = EmailPreview.extract_from_emlx(msg['emlx_path'])
        
        # Score email
        score, signals = scorer.score_email(sender, subject, preview_text)
        
        # Classify
        category = EmailClassifier.classify(score)
        
        # Enrich message dict
        msg['score'] = score
        msg['signals'] = signals
        msg['category'] = category.value
        msg['preview'] = preview_text
        
        processed.append(msg)
    
    return processed


def main():
    """Main application entry point."""
    # Parse command-line arguments
    parser = CLI.create_parser()
    args = parser.parse_args()
    
    try:
        # Initialize mail index reader
        print("Locating Apple Mail Envelope Index...", file=sys.stderr)
        reader = MailIndexReader(db_path=args.db_path)
        
        # Handle --list-accounts flag
        if args.list_accounts:
            print("\nDiscovering accounts from mailbox paths...", file=sys.stderr)
            with reader:
                accounts = reader.get_accounts()
            
            if not accounts:
                print("\nNo accounts found.")
                return 0
            
            print(f"\nAvailable accounts ({len(accounts)}):")
            for account in accounts:
                print(f"  - {account}")
            print("\nUse --account <name> to filter by account.")
            print("Example: python main.py --account Exchange")
            return 0
        
        # Query messages
        filter_desc = []
        if args.account:
            filter_desc.append(f"account={args.account}")
        if args.mailbox:
            filter_desc.append(f"mailbox={args.mailbox}")
        if args.unread_only:
            filter_desc.append("unread only")
        if args.since:
            filter_desc.append(f"last {args.since} days")
        
        filter_str = f" ({', '.join(filter_desc)})" if filter_desc else ""
        print(f"Querying messages (limit={args.limit}{filter_str})...", file=sys.stderr)
        
        with reader:
            messages = reader.query_messages(
                limit=args.limit,
                since_days=args.since,
                unread_only=args.unread_only,
                mailbox=args.mailbox,
                account=args.account
            )
        
        if not messages:
            print("\nNo messages found matching criteria.")
            return 0
        
        print(f"Found {len(messages)} messages.", file=sys.stderr)
        print("Scoring and classifying...\n", file=sys.stderr)
        
        # Initialize scorer
        scorer = EmailScorer(user_name=args.user_name)
        
        # Process emails (extract preview only if --why is used)
        processed = process_emails(messages, scorer, show_preview=args.why)
        
        # Filter by category if requested
        if args.category:
            processed = [e for e in processed if e['category'] == args.category]
        
        if not processed:
            print(f"\nNo emails found in category: {args.category}")
            return 0
        
        # Format and display results
        table = TableFormatter.format_ledger(processed, show_explanations=args.why)
        print(table)
        
        # Display summary
        summary = TableFormatter.format_summary(processed)
        print(summary)
        
        return 0
        
    except PermissionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nMake sure Apple Mail is installed and has been run at least once.", file=sys.stderr)
        return 1
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
