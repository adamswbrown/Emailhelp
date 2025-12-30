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
import subprocess
from typing import List, Dict, Any

from email_reader import create_reader
from preview import EmailPreview
from scoring import EmailScorer
from classifier import EmailClassifier, EmailCategory
from cli import CLI, TableFormatter
from open_email import open_email
from email_selector import select_email_interactive
from applescript_search import (
    search_emails, 
    list_inbox_emails, 
    get_accounts as get_applescript_accounts,
    get_email_content,
    extract_email_content_as_text
)
from fast_content_extract import get_email_content_by_details


def process_emails(
    messages: List[Dict[str, Any]],
    scorer: EmailScorer,
    show_preview: bool = False
) -> List[Dict[str, Any]]:
    """
    Process messages: extract preview, score, and classify.
    
    Args:
        messages: Raw message dicts from MailIndexReader or AppleScript search
        scorer: EmailScorer instance
        show_preview: Whether to extract body previews (ignored if preview already exists)
    
    Returns:
        List of enriched email dicts with scores and categories
    """
    processed = []
    
    for msg in messages:
        # Extract fields
        sender = msg.get('sender', '') or ''
        subject = msg.get('subject', '') or ''
        
        # Check for content/preview (AppleScript provides both)
        preview_text = msg.get('content') or msg.get('preview')
        
        # Extract preview if not already present and requested
        if preview_text is None and show_preview:
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
    
    # Launch UI if requested
    if args.ui:
        try:
            from ui import EmailAccountingApp
            client = None if args.client == 'auto' else args.client
            app = EmailAccountingApp(client=client, account=args.account, user_name=args.user_name)
            app.run()
            return 0
        except ImportError:
            print("Error: textual package is required for UI mode.", file=sys.stderr)
            print("Install it with: pip install textual", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error launching UI: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return 1
    
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
            
            # Try AppleScript first (more reliable)
            try:
                accounts = get_applescript_accounts()
                if accounts:
                    print(f"\nAvailable accounts ({len(accounts)}) [via AppleScript]:")
                    for account in accounts:
                        print(f"  - {account}")
                    print("\nUse --account <name> to filter by account.")
                    print("Example: python main.py --account Exchange")
                    return 0
            except Exception as e:
                print(f"AppleScript account discovery failed: {e}", file=sys.stderr)
                print("Falling back to database...", file=sys.stderr)
            
            # Fall back to database
            with reader:
                accounts = reader.get_accounts()
            
            if not accounts:
                print("\nNo accounts found.")
                return 0
            
            print(f"\nAvailable accounts ({len(accounts)}) [via database]:")
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
        
        # Use AppleScript search if --search or --use-applescript is specified
        use_applescript = args.use_applescript or args.search is not None
        
        if use_applescript:
            print(f"Searching emails via AppleScript (real-time from Mail.app){filter_str}...", file=sys.stderr)
            try:
                if args.search:
                    # Check if we need full content extraction
                    if args.extract_content:
                        if not args.account:
                            print("Error: --extract-content requires --account to be specified", file=sys.stderr)
                            return 1
                        
                        # Get full content (unlimited length)
                        messages = get_email_content(
                            account=args.account,
                            subject_keyword=args.search,
                            mailbox=args.mailbox or "INBOX",
                            max_results=args.limit
                        )
                        
                        # Handle content extraction output
                        if args.output_raw:
                            # Output raw content only (for piping)
                            for msg in messages:
                                content = msg.get('content', msg.get('preview', ''))
                                print(content)
                            return 0
                        
                        if args.copy_content:
                            # Copy to clipboard
                            if not messages:
                                print("Error: No emails found to copy", file=sys.stderr)
                                return 1
                            
                            msg = messages[0]  # Copy first matching email
                            content = msg.get('content', msg.get('preview', ''))
                            
                            try:
                                # Use pbcopy on macOS
                                process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE, text=True)
                                process.communicate(input=content)
                                process.wait()
                                
                                if process.returncode == 0:
                                    print(f"Email content copied to clipboard: {msg.get('subject', 'Unknown')}", file=sys.stderr)
                                else:
                                    print("Error: Failed to copy to clipboard", file=sys.stderr)
                                    return 1
                            except Exception as e:
                                print(f"Error copying to clipboard: {e}", file=sys.stderr)
                                return 1
                            
                            return 0
                        
                        if args.output_file:
                            # Save to file(s)
                            import os
                            base_path = os.path.expanduser(args.output_file)
                            
                            if len(messages) == 1:
                                # Single file
                                with open(base_path, 'w', encoding='utf-8') as f:
                                    msg = messages[0]
                                    if args.extract_content:
                                        f.write(f"Subject: {msg.get('subject', '')}\n")
                                        f.write(f"From: {msg.get('sender', '')}\n")
                                        f.write(f"Date: {msg.get('date', '')}\n")
                                        f.write(f"Account: {msg.get('account', '')}\n")
                                        f.write("\n" + "="*60 + "\n")
                                        f.write("CONTENT\n")
                                        f.write("="*60 + "\n\n")
                                    f.write(msg.get('content', msg.get('preview', '')))
                                print(f"Content saved to: {base_path}", file=sys.stderr)
                            else:
                                # Multiple files
                                base_name, ext = os.path.splitext(base_path)
                                for i, msg in enumerate(messages, 1):
                                    file_path = f"{base_name}_{i}{ext}"
                                    with open(file_path, 'w', encoding='utf-8') as f:
                                        f.write(f"Subject: {msg.get('subject', '')}\n")
                                        f.write(f"From: {msg.get('sender', '')}\n")
                                        f.write(f"Date: {msg.get('date', '')}\n")
                                        f.write(f"Account: {msg.get('account', '')}\n")
                                        f.write("\n" + "="*60 + "\n")
                                        f.write("CONTENT\n")
                                        f.write("="*60 + "\n\n")
                                        f.write(msg.get('content', msg.get('preview', '')))
                                    print(f"Content saved to: {file_path}", file=sys.stderr)
                            return 0
                    else:
                        # Regular search with preview
                        messages = search_emails(
                            account=args.account,
                            mailbox=args.mailbox or "INBOX",
                            subject_keyword=args.search,
                            sender=args.sender,
                            unread_only=args.unread_only,
                            max_results=args.limit,
                            include_content=True,
                            max_content_length=500
                        )
                else:
                    # Use list_inbox_emails for general listing
                    messages = list_inbox_emails(
                        account=args.account,
                        max_emails=args.limit,
                        include_read=not args.unread_only
                    )
                
                # Convert AppleScript results to match database format
                # AppleScript already provides preview, so we're good
                print(f"Found {len(messages)} messages via AppleScript.", file=sys.stderr)
            except Exception as e:
                print(f"AppleScript search failed: {e}", file=sys.stderr)
                print("Falling back to database query...", file=sys.stderr)
                use_applescript = False
        
        if not use_applescript:
            print(f"Querying messages from database (limit={args.limit}{filter_str})...", file=sys.stderr)
            with reader:
                # If --open is used without other filters and no results, try without date filter
                messages = reader.query_messages(
                    limit=args.limit,
                    since_days=since_days,
                    unread_only=args.unread_only,
                    mailbox=args.mailbox,
                    account=args.account
                )
                
                # Smart fallback: If database returns no results and account is specified,
                # try AppleScript (database account filtering may be incorrect)
                if not messages and args.account and not args.use_applescript:
                    print("No messages found in database. Trying AppleScript for real-time results...", file=sys.stderr)
                    try:
                        use_applescript = True
                        messages = list_inbox_emails(
                            account=args.account,
                            max_emails=args.limit,
                            include_read=not args.unread_only
                        )
                        print(f"Found {len(messages)} messages via AppleScript.", file=sys.stderr)
                    except Exception as e:
                        print(f"AppleScript fallback failed: {e}", file=sys.stderr)
                        use_applescript = False
                
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
        
        if not use_applescript:
            print(f"Found {len(messages)} messages.", file=sys.stderr)
        
        print("Scoring and classifying...\n", file=sys.stderr)
        
        # Initialize scorer
        scorer = EmailScorer(user_name=args.user_name)
        
        # Process emails
        # For AppleScript results, preview is already included, so we don't need to extract it
        # For database results, extract preview for better scoring accuracy
        show_preview = not use_applescript  # AppleScript already includes preview
        processed = process_emails(messages, scorer, show_preview=show_preview)
        
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
        
        # Handle --copy-index flag (copy content by index)
        if args.copy_index is not None:
            if args.copy_index < 1 or args.copy_index > len(processed):
                print(f"Error: Index {args.copy_index} is out of range (1-{len(processed)})", file=sys.stderr)
                return 1
            
            email_to_copy = processed[args.copy_index - 1]
            subject = email_to_copy.get('subject', '')
            sender = email_to_copy.get('sender', '')
            
            # Determine account - try multiple sources
            account = email_to_copy.get('account', '')
            
            # Map URL protocols to account display names
            mailbox = email_to_copy.get('mailbox', '')
            url_protocol = None
            if mailbox and '://' in mailbox:
                url_protocol = mailbox.split('://')[0].lower()  # Extract protocol (ews, imap, etc.)
            
            # Get actual account names from AppleScript
            from applescript_search import get_accounts
            applescript_accounts = get_accounts()
            
            # Normalize command-line account name
            cmd_account = args.account.upper() if args.account else None
            
            # Map account names/protocols to AppleScript account names
            account_map = {
                'EWS': 'Exchange',
                'ews': 'Exchange',
                'EXCHANGE': 'Exchange',
                'exchange': 'Exchange',
            }
            
            # Determine the correct account name
            if cmd_account and cmd_account in account_map:
                # Map command-line account to AppleScript name
                mapped = account_map[cmd_account]
                if mapped in applescript_accounts:
                    account = mapped
            elif args.account and args.account in applescript_accounts:
                # Use command-line account if it matches AppleScript name
                account = args.account
            elif url_protocol == 'ews':
                # EWS protocol maps to Exchange account
                if 'Exchange' in applescript_accounts:
                    account = 'Exchange'
            elif url_protocol:
                # Try to find account by protocol
                protocol_to_account = {
                    'ews': 'Exchange',
                }
                mapped_account = protocol_to_account.get(url_protocol)
                if mapped_account and mapped_account in applescript_accounts:
                    account = mapped_account
            
            # Fallback: use first account if still not found
            if not account and applescript_accounts:
                account = applescript_accounts[0]
                print(f"Warning: Using first available account: {account}", file=sys.stderr)
            
            if not subject:
                print("Error: Email subject not found", file=sys.stderr)
                return 1
            
            if not account:
                print("Error: Email account not found. Please specify --account", file=sys.stderr)
                print(f"Available accounts: {', '.join(applescript_accounts)}", file=sys.stderr)
                return 1
            
            print(f"\nExtracting content for email #{args.copy_index}: {subject[:50]}...", file=sys.stderr)
            print(f"Using account: {account}, sender: {sender[:30]}", file=sys.stderr)
            
            try:
                # Extract mailbox name from URL if needed
                mailbox_name = "INBOX"  # Default to INBOX
                if '://' in mailbox:
                    # Default to INBOX for URL-based mailboxes
                    mailbox_name = "INBOX"
                else:
                    mailbox_name = mailbox
                
                # Use fast, targeted extraction (subject + sender)
                # This is much faster than keyword search
                print(f"Extracting content using targeted search (subject + sender)...", file=sys.stderr)
                
                content = get_email_content_by_details(
                    account=account,
                    subject=subject,
                    sender=sender,
                    mailbox=mailbox_name,
                    timeout=30  # Shorter timeout for targeted search
                )
                
                if not content:
                    print("Targeted search failed. Trying fallback method...", file=sys.stderr)
                    
                    # Fallback to keyword search
                    from applescript_search import get_email_content
                    
                    # Use first significant word from subject
                    clean_subject = subject.replace('[External]', '').replace('[', '').replace(']', '').strip()
                    subject_words = clean_subject.split()
                    skip_words = {'for', 'a', 'an', 'the', 'of', 'in', 'on', 'at', 'to', 'with'}
                    search_keyword = None
                    for word in subject_words:
                        if word.lower() not in skip_words and len(word) > 3:
                            search_keyword = word
                            break
                    
                    if not search_keyword and subject_words:
                        search_keyword = subject_words[0]
                    elif not search_keyword:
                        search_keyword = subject[:30]
                    
                    print(f"Fallback search with keyword: '{search_keyword}'", file=sys.stderr)
                    
                    messages = get_email_content(
                        account=account,
                        subject_keyword=search_keyword,
                        mailbox=mailbox_name,
                        max_results=5  # Limit to reduce timeout risk
                    )
                
                    # Find exact match from fallback results
                    matching_email = None
                    if messages:
                        for msg in messages:
                            if msg.get('subject', '').strip() == subject.strip():
                                matching_email = msg
                                break
                        if not matching_email:
                            matching_email = messages[0]
                    
                    if matching_email:
                        content = matching_email.get('content', matching_email.get('preview', ''))
                    else:
                        content = None
                else:
                    # Success with targeted search!
                    pass  # content already set
                
                if not content:
                    print("Error: Could not retrieve email content", file=sys.stderr)
                    print(f"  Account: {account}", file=sys.stderr)
                    print(f"  Subject: {subject[:60]}", file=sys.stderr)
                    print(f"  Sender: {sender[:40]}", file=sys.stderr)
                    return 1
                
                # Copy to clipboard
                process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE, text=True)
                process.communicate(input=content)
                process.wait()
                
                if process.returncode == 0:
                    print(f"✓ Email content copied to clipboard: {subject}", file=sys.stderr)
                    return 0
                else:
                    print("Error: Failed to copy to clipboard", file=sys.stderr)
                    return 1
                    
            except Exception as e:
                print(f"Error copying email content: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                return 1
        
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
