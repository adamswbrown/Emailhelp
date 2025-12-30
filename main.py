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

from email_reader import create_reader
from preview import EmailPreview
from scoring import EmailScorer
from classifier import EmailClassifier, EmailCategory
from cli import CLI, TableFormatter
from open_email import open_email
from email_selector import select_email_interactive


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
        # Note: Outlook uses different message file format, preview extraction may not work
        if show_preview:
            emlx_path = msg.get('emlx_path') or msg.get('message_path')
            if emlx_path:
                preview_text = EmailPreview.extract_from_emlx(emlx_path)
            # For Outlook, preview might already be in the message dict
            elif msg.get('preview'):
                preview_text = msg.get('preview')
        
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
        # Initialize email reader (supports both Apple Mail and Outlook)
        client_name = args.client if args.client != 'auto' else None
        
        if client_name:
            print(f"Using {client_name} database...", file=sys.stderr)
        else:
            print("Auto-detecting email client...", file=sys.stderr)
        
        reader = create_reader(client=client_name, db_path=args.db_path)
        
        # Detect which client we're using for display
        client_display = "Apple Mail" if isinstance(reader, __import__('email_reader').AppleMailReader) else "Outlook"
        print(f"✓ Connected to {client_display} database", file=sys.stderr)
        
        # Handle --list-accounts flag
        if args.list_accounts:
            print("\nDiscovering accounts...", file=sys.stderr)
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
        
        # Apply date filter unless --all is specified
        since_days = None if args.all else args.since
        if since_days:
            filter_desc.append(f"last {since_days} days")
        
        filter_str = f" ({', '.join(filter_desc)})" if filter_desc else ""
        print(f"Querying messages (limit={args.limit}{filter_str})...", file=sys.stderr)
        
        with reader:
            # If --open is used without other filters and no results, try without date filter
            messages = reader.query_messages(
                limit=args.limit,
                since_days=since_days,
                unread_only=args.unread_only,
                mailbox=args.mailbox,
                account=args.account
            )
            
            # If no messages found and --open is used, try without date filter to help user
            if not messages and args.open is not None and since_days:
                print("No messages found with date filter, trying without date filter...", file=sys.stderr)
                messages = reader.query_messages(
                    limit=args.limit,
                    since_days=None,
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
        
        # Process emails (extract preview for better scoring accuracy)
        # Always extract preview to detect informational patterns in content
        processed = process_emails(messages, scorer, show_preview=True)
        
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
        
        # Handle --open flag (interactive or by index)
        if args.open is not None:
            if args.open == 0:
                # Interactive selection
                email_to_open = select_email_interactive(processed)
                if not email_to_open:
                    return 0  # User cancelled
            else:
                # Direct index selection
                if args.open < 1 or args.open > len(processed):
                    print(f"Error: Index {args.open} is out of range (1-{len(processed)})", file=sys.stderr)
                    return 1
                email_to_open = processed[args.open - 1]
            
            # Determine which client to use for opening
            open_client = args.open_client if args.open_client else 'apple-mail'
            
            print(f"\nOpening email in {open_client}...", file=sys.stderr)
            success = open_email(email_to_open, client=open_client)
            
            if success:
                print("Email opened successfully.", file=sys.stderr)
                return 0
            else:
                print("Failed to open email.", file=sys.stderr)
                return 1
        
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
