#!/usr/bin/env python3
"""
ui.py - Textual-based TUI for Email Accounting

A rich terminal user interface using the textual package.
"""

import sys
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

try:
    from textual.app import App, ComposeResult
    from textual.widgets import DataTable, Header, Footer, Static, Input, Select, Button, Checkbox
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.binding import Binding
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False
    print("Error: textual package is required for UI mode.", file=sys.stderr)
    print("Install it with: pip install textual", file=sys.stderr)
    sys.exit(1)

from email_reader import create_reader
from scoring import EmailScorer
from classifier import EmailClassifier
from preview import EmailPreview
from open_email import open_email


class EmailTable(DataTable):
    """Email list table widget."""
    
    def __init__(self, emails: List[Dict[str, Any]] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.emails = emails or []
        self.cursor_type = "row"
    
    def on_mount(self) -> None:
        """Initialize the table when mounted."""
        if self.emails:
            self.add_columns("Date", "From", "Subject", "Score", "Category")
            
            for idx, email in enumerate(self.emails):
                date_str = self._format_date(email.get('date_received'))
                sender = self._format_sender(email.get('sender', ''))
                subject = email.get('subject', '')[:50]
                score = email.get('score', 0)
                category = email.get('category', '')
                
                self.add_row(
                    date_str,
                    sender,
                    subject,
                    str(score),
                    category,
                    key=str(idx)
                )
    
    def _format_date(self, timestamp: Any) -> str:
        """Format date as dd/mm/yyyy."""
        if timestamp is None:
            return 'Unknown'
        try:
            dt = datetime.fromtimestamp(int(timestamp))
            return dt.strftime('%d/%m/%Y')
        except:
            return 'Invalid'
    
    def _format_sender(self, sender: str) -> str:
        """Format sender address."""
        if '@' in sender:
            parts = sender.split('@')
            if len(parts) == 2:
                return parts[1].strip()[:25]
        return sender[:25] if sender else 'Unknown'


class EmailDetail(Static):
    """Email detail view widget."""
    
    def update_email(self, email: Dict[str, Any], show_signals: bool = True) -> None:
        """Update the detail view with email information."""
        date_str = self._format_date(email.get('date_received'))
        sender = email.get('sender', 'Unknown')
        subject = email.get('subject', 'No subject')
        score = email.get('score', 0)
        category = email.get('category', 'UNKNOWN')
        signals = email.get('signals', {})
        preview = email.get('preview', '')
        mailbox = email.get('mailbox', 'Unknown')
        
        signals_str = ', '.join([f"{k}({v:+d})" for k, v in sorted(signals.items(), key=lambda x: -abs(x[1]))])
        
        content = f"""
[bold]Date:[/bold] {date_str}
[bold]From:[/bold] {sender}
[bold]Subject:[/bold] {subject}
[bold]Score:[/bold] {score} | [bold]Category:[/bold] {category}
[bold]Mailbox:[/bold] {mailbox[:50]}

"""
        
        if show_signals and signals:
            content += f"""[bold]Signals:[/bold]
{signals_str}

"""
        
        # Show more preview text in UI (up to 2000 chars)
        preview_display = preview if preview else 'No preview available'
        if preview and len(preview) > 2000:
            preview_display = preview[:2000] + '...'
        
        content += f"""[bold]Preview:[/bold]
{preview_display}
"""
        self.update(content)
    
    def _format_date(self, timestamp: Any) -> str:
        """Format date as dd/mm/yyyy HH:MM."""
        if timestamp is None:
            return 'Unknown'
        try:
            dt = datetime.fromtimestamp(int(timestamp))
            return dt.strftime('%d/%m/%Y %H:%M')
        except:
            return 'Invalid'


class EmailAccountingApp(App):
    """Main application class."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #email_table {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
    }
    
    #email_detail {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    
    #filters {
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    
    .filter-row {
        height: 3;
    }
    
    .filter-group {
        width: 1fr;
        padding: 1;
    }
    
    Horizontal {
        height: 1fr;
    }
    
    Vertical {
        height: auto;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("o", "open_email", "Open Email"),
        Binding("r", "refresh", "Refresh"),
        Binding("f", "focus_filters", "Filters"),
        Binding("t", "focus_table", "Table"),
        Binding("l", "list_accounts", "List Accounts"),
        Binding("s", "toggle_signals", "Toggle Signals"),
    ]
    
    def __init__(self, client: Optional[str] = None, account: Optional[str] = None, user_name: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.client = client
        self.account = account
        self.user_name = user_name
        self.reader = None
        self.scorer = EmailScorer(user_name=user_name)
        self.emails: List[Dict[str, Any]] = []
        self.filtered_emails: List[Dict[str, Any]] = []
        self.available_accounts: List[str] = []
        self.show_signals = True
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        
        with Container(id="filters"):
            with Vertical():
                with Horizontal(classes="filter-row"):
                    yield Static("Limit:", classes="filter-group")
                    yield Input(placeholder="20", id="limit_input", value="20")
                    yield Static("Category:", classes="filter-group")
                    yield Select(
                        [("All", "all"), ("ACTION", "ACTION"), ("FYI", "FYI"), ("IGNORE", "IGNORE")],
                        id="category_select",
                        value="all"
                    )
                    yield Static("Days:", classes="filter-group")
                    yield Input(placeholder="365", id="days_input", value="365")
                    yield Checkbox("All", id="all_checkbox", value=False)
                
                with Horizontal(classes="filter-row"):
                    yield Static("Account:", classes="filter-group")
                    yield Select([("All", "")], id="account_select", value="")
                    yield Static("Mailbox:", classes="filter-group")
                    yield Input(placeholder="Inbox (optional)", id="mailbox_input", value="")
                    yield Static("Client:", classes="filter-group")
                    yield Select(
                        [("Auto", "auto"), ("Apple Mail", "apple-mail"), ("Outlook", "outlook")],
                        id="client_select",
                        value="auto" if not self.client else self.client
                    )
                
                with Horizontal(classes="filter-row"):
                    yield Checkbox("Unread Only", id="unread_checkbox", value=False)
                    yield Checkbox("Show Signals", id="signals_checkbox", value=True)
                    yield Static("User Name:", classes="filter-group")
                    yield Input(placeholder="Your name (optional)", id="user_name_input", value=self.user_name or "")
                    yield Button("Refresh", id="refresh_button", variant="primary")
                    yield Button("Open Email (O)", id="open_button", variant="success")
                    yield Button("List Accounts", id="list_accounts_button", variant="default")
        
        with Horizontal():
            yield EmailTable([], id="email_table")
            yield EmailDetail("Loading emails...", id="email_detail")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app starts."""
        self.title = "Email Accounting & Categorization"
        self.sub_title = "Deterministic Email Triage"
        # Use call_after_refresh to ensure UI is fully initialized
        self.call_after_refresh(self.load_accounts)
        self.call_after_refresh(self.load_emails)
    
    def load_accounts(self) -> None:
        """Load available accounts."""
        try:
            # Use client from selector if available, otherwise use initial client
            try:
                client_select = self.query_one("#client_select", Select)
                client_value = client_select.value
                client = None if client_value == "auto" else client_value
            except:
                client = self.client
            
            reader = create_reader(client=client)
            with reader:
                accounts = reader.get_accounts()
                self.available_accounts = accounts
            
            # Update account selector
            account_select = self.query_one("#account_select", Select)
            options = [("All", "")]
            if accounts:
                options.extend([(acc, acc) for acc in accounts])
            account_select.set_options(options)
            
            # Set initial value if account was provided (try partial matching)
            if self.account:
                matched = False
                for acc in accounts:
                    # Try exact match first (case-insensitive)
                    if acc.lower() == self.account.lower() or acc.lower() == (self.account + ':').lower():
                        account_select.value = acc
                        matched = True
                        break
                    # Try partial match
                    if self.account.lower() in acc.lower() or acc.lower() in self.account.lower():
                        account_select.value = acc
                        matched = True
                        break
                if not matched:
                    # If no match found, notify user but don't fail
                    self.notify(f"Account '{self.account}' not found. Available: {', '.join(accounts)}", severity="warning")
        except Exception as e:
            # If accounts can't be loaded yet (before UI is ready), store for later
            try:
                reader = create_reader(client=self.client)
                with reader:
                    accounts = reader.get_accounts()
                    self.available_accounts = accounts
            except:
                pass
    
    def load_emails(self) -> None:
        """Load emails from the database."""
        try:
            # Get filter values
            limit_input = self.query_one("#limit_input", Input)
            days_input = self.query_one("#days_input", Input)
            category_select = self.query_one("#category_select", Select)
            account_select = self.query_one("#account_select", Select)
            mailbox_input = self.query_one("#mailbox_input", Input)
            client_select = self.query_one("#client_select", Select)
            unread_checkbox = self.query_one("#unread_checkbox", Checkbox)
            all_checkbox = self.query_one("#all_checkbox", Checkbox)
            user_name_input = self.query_one("#user_name_input", Input)
            signals_checkbox = self.query_one("#signals_checkbox", Checkbox)
            
            limit = int(limit_input.value or "20")
            since_days = None if all_checkbox.value else (int(days_input.value or "365") if days_input.value else None)
            # Account: empty string means "All", convert to None for query
            account_value = account_select.value if account_select.value else ""
            account = None if account_value == "" else account_value
            # Mailbox: empty string means "All", convert to None for query
            mailbox_value = mailbox_input.value.strip() if mailbox_input.value else ""
            mailbox = None if mailbox_value == "" else mailbox_value
            client = None if client_select.value == "auto" else client_select.value
            unread_only = unread_checkbox.value
            user_name = user_name_input.value.strip() if user_name_input.value and user_name_input.value.strip() else None
            self.show_signals = signals_checkbox.value
            
            # Update scorer with user name
            if user_name:
                self.scorer = EmailScorer(user_name=user_name)
            else:
                self.scorer = EmailScorer()
            
            # Create reader
            self.reader = create_reader(client=client)
            
            with self.reader:
                messages = self.reader.query_messages(
                    limit=limit,
                    since_days=since_days,
                    account=account,
                    mailbox=mailbox,
                    unread_only=unread_only
                )
            
            # Debug: log what we're querying
            print(f"DEBUG: Query params - limit={limit}, since_days={since_days}, account={account}, mailbox={mailbox}, unread_only={unread_only}, client={client}")
            print(f"DEBUG: Found {len(messages)} messages")
            
            if not messages:
                # Try without mailbox filter if no results and mailbox was specified
                if mailbox:
                    self.notify(f"No emails found with mailbox filter. Trying without mailbox filter...", severity="warning")
                    messages = self.reader.query_messages(
                        limit=limit,
                        since_days=since_days,
                        account=account,
                        mailbox=None,
                        unread_only=unread_only
                    )
                    print(f"DEBUG: After removing mailbox filter, found {len(messages)} messages")
                
                # If still no messages and unread_only is True, try without it
                if not messages and unread_only:
                    self.notify(f"No unread emails found. Trying with all emails...", severity="warning")
                    messages = self.reader.query_messages(
                        limit=limit,
                        since_days=since_days,
                        account=account,
                        mailbox=None,
                        unread_only=False
                    )
                    print(f"DEBUG: After removing unread_only filter, found {len(messages)} messages")
            
            # Process emails (similar to main.py process_emails function)
            processed = []
            for msg in messages:
                sender = msg.get('sender', '') or ''
                subject = msg.get('subject', '') or ''
                preview_text = None
                
                # Extract full email body text for UI display
                preview_text = None
                emlx_path = msg.get('emlx_path') or msg.get('message_path')
                
                # If emlx_path not provided, try to find it from message data
                if not emlx_path:
                    # Try different ID fields - Apple Mail uses ROWID as the filename
                    message_id = msg.get('ROWID') or msg.get('message_id') or msg.get('id')
                    subject = msg.get('subject', '')
                    sender = msg.get('sender', '')
                    mailbox_url = msg.get('mailbox', '')
                    
                    if message_id:
                        # Try to find the emlx file
                        # Based on https://github.com/DePayFi/mac-mails-parse-export-csv-json
                        # .emlx files are stored in: V10/{account_id}/{mailbox}.mbox/{uuid}/Data/{numbers}/Messages/{message_id}.emlx
                        mail_dir = Path.home() / "Library" / "Mail"
                        if mail_dir.exists():
                            # Find latest version directory
                            for v_dir in sorted(mail_dir.glob("V*"), reverse=True):
                                # Search recursively for the exact filename
                                # This is the most reliable method
                                for emlx_file in v_dir.rglob(f"{message_id}.emlx"):
                                    emlx_path = str(emlx_file)
                                    break
                                
                                if emlx_path:
                                    break
                                
                                # If not found, try to narrow search by mailbox URL
                                # Extract account identifier from mailbox URL (e.g., ews://...)
                                if not emlx_path and mailbox_url:
                                    # Try to find account folder that might match
                                    # Exchange accounts often have UUIDs in their folder names
                                    for account_dir in v_dir.iterdir():
                                        if account_dir.is_dir() and not account_dir.name.startswith('.'):
                                            # Search in this account's mailboxes
                                            for emlx_file in account_dir.rglob(f"{message_id}.emlx"):
                                                emlx_path = str(emlx_file)
                                                break
                                            if emlx_path:
                                                break
                                    if emlx_path:
                                        break
                
                # Extract body text from .emlx file
                if emlx_path and Path(emlx_path).exists():
                    try:
                        import email
                        from email import policy
                        
                        # Read full email (not just preview)
                        with open(emlx_path, 'rb') as f:
                            first_line = f.readline()  # Skip byte count
                            raw_email = f.read()  # Read full email
                        
                        msg_obj = email.message_from_bytes(raw_email, policy=policy.default)
                        preview_text = EmailPreview._extract_body(msg_obj)
                        
                        # Clean up the text (remove signatures/quotes but keep more content)
                        if preview_text:
                            # Remove signatures and quoted replies, but keep more text
                            lines = preview_text.split('\n')
                            cleaned_lines = []
                            for line in lines:
                                line = line.strip()
                                
                                # Check for signature markers
                                if any(marker in line for marker in EmailPreview.SIGNATURE_MARKERS):
                                    break
                                
                                # Check for quote markers
                                is_quote = False
                                for pattern in EmailPreview.QUOTE_MARKERS:
                                    if re.search(pattern, line, re.IGNORECASE):
                                        is_quote = True
                                        break
                                
                                if is_quote:
                                    break
                                
                                if line:
                                    cleaned_lines.append(line)
                            
                            preview_text = '\n'.join(cleaned_lines)
                    except Exception as e:
                        # Fall back to preview extraction
                        preview_text = EmailPreview.extract_from_emlx(emlx_path)
                        if not preview_text:
                            print(f"Warning: Could not extract body from {emlx_path}: {e}")
                
                # For Outlook, use preview field if available
                if not preview_text and msg.get('preview'):
                    preview_text = msg.get('preview')
                
                # If still no preview, try using AppleScript to get email content
                # This works for Exchange/EWS emails that might not have .emlx files
                if not preview_text:
                    try:
                        import subprocess
                        subject = msg.get('subject', '')
                        sender = msg.get('sender', '')
                        
                        if subject:
                            # Escape quotes in subject for AppleScript
                            escaped_subject = subject.replace('"', '\\"')[:100]
                            
                            # Use AppleScript to get email content from Apple Mail
                            script = f'''
                            tell application "Mail"
                                set foundMessage to missing value
                                
                                -- Try to find the message by subject across all accounts
                                repeat with theAccount in accounts
                                    try
                                        repeat with theMailbox in mailboxes of theAccount
                                            try
                                                set matchingMessages to (messages of theMailbox whose subject contains "{escaped_subject}")
                                                if (count of matchingMessages) > 0 then
                                                    set foundMessage to item 1 of matchingMessages
                                                    exit repeat
                                                end if
                                            end try
                                        end repeat
                                        if foundMessage is not missing value then
                                            exit repeat
                                        end if
                                    end try
                                end repeat
                                
                                if foundMessage is not missing value then
                                    set msgContent to content of foundMessage
                                    return msgContent
                                else
                                    return ""
                                end if
                            end tell
                            '''
                            
                            result = subprocess.run(
                                ['osascript', '-e', script],
                                capture_output=True,
                                text=True,
                                timeout=3  # Short timeout to avoid blocking UI
                            )
                            
                            if result.returncode == 0 and result.stdout.strip():
                                preview_text = result.stdout.strip()
                                
                                # Clean up text (based on apple-mail-mcp patterns)
                                # Remove HTML if present
                                if '<' in preview_text:
                                    preview_text = re.sub(r'<[^>]+>', '', preview_text)
                                    preview_text = re.sub(r'\s+', ' ', preview_text).strip()
                                
                                # Remove signatures and quoted replies (keep more content than preview extraction)
                                if preview_text:
                                    lines = preview_text.split('\n')
                                    cleaned_lines = []
                                    for line in lines:
                                        line = line.strip()
                                        
                                        # Check for signature markers
                                        if any(marker in line for marker in EmailPreview.SIGNATURE_MARKERS):
                                            break
                                        
                                        # Check for quote markers
                                        is_quote = False
                                        for pattern in EmailPreview.QUOTE_MARKERS:
                                            if re.search(pattern, line, re.IGNORECASE):
                                                is_quote = True
                                                break
                                        
                                        if is_quote:
                                            break
                                        
                                        if line:
                                            cleaned_lines.append(line)
                                    
                                    preview_text = '\n'.join(cleaned_lines)
                                
                                # Limit length for UI display (2000 chars)
                                if preview_text and len(preview_text) > 2000:
                                    preview_text = preview_text[:2000] + '...'
                    except subprocess.TimeoutExpired:
                        # AppleScript timed out, that's OK
                        pass
                    except Exception as e:
                        # AppleScript failed, that's OK - just don't show preview
                        print(f"AppleScript preview extraction failed: {e}")
                        pass
                
                # Score email
                score, signals = self.scorer.score_email(sender, subject, preview_text)
                category = EmailClassifier.classify(score)
                
                # Enrich message dict
                msg['score'] = score
                msg['signals'] = signals
                msg['category'] = category.value
                msg['preview'] = preview_text
                
                processed.append(msg)
            
            self.emails = processed
            
            # Apply category filter
            category = category_select.value
            if category and category != "all":
                self.filtered_emails = [e for e in self.emails if e['category'] == category]
            else:
                self.filtered_emails = self.emails
            
            # Update table
            table = self.query_one("#email_table", EmailTable)
            table.clear()
            table.emails = self.filtered_emails
            
            if self.filtered_emails:
                table.add_columns("Date", "From", "Subject", "Score", "Category")
                
                for idx, email in enumerate(self.filtered_emails):
                    date_str = table._format_date(email.get('date_received'))
                    sender = table._format_sender(email.get('sender', ''))
                    subject = email.get('subject', '')[:50]
                    score = email.get('score', 0)
                    category = email.get('category', '')
                    
                    table.add_row(
                        date_str,
                        sender,
                        subject,
                        str(score),
                        category,
                        key=str(idx)
                    )
                
                # Update detail view with first email
                if self.filtered_emails:
                    detail = self.query_one("#email_detail", EmailDetail)
                    detail.update_email(self.filtered_emails[0], show_signals=self.show_signals)
                    # Focus the table so user can navigate with arrow keys
                    table.focus()
                
                self.notify(f"Loaded {len(self.filtered_emails)} emails", severity="information")
            else:
                # Show message when no emails found
                table.add_columns("Status")
                table.add_row("No emails found matching filters", key="empty")
                detail = self.query_one("#email_detail", EmailDetail)
                detail.update("[yellow]No emails found[/yellow]\n\nTry adjusting your filters:\n- Check date range\n- Check account selection\n- Check mailbox filter\n- Check unread-only filter")
                self.notify(f"No emails found (queried {len(messages)} messages, filtered to {len(self.filtered_emails)})", severity="warning")
            
        except Exception as e:
            error_msg = str(e)
            import traceback
            tb = traceback.format_exc()
            self.notify(f"Error loading emails: {error_msg}", severity="error")
            # Also update detail view with error
            detail = self.query_one("#email_detail", EmailDetail)
            detail.update(f"[bold red]Error loading emails:[/bold red]\n\n{error_msg}\n\n{tb[:500]}")
            # Print to console for debugging
            print(f"Error in load_emails: {error_msg}")
            print(tb)
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        if event.cursor_row is not None and self.filtered_emails:
            idx = int(event.cursor_row)
            if 0 <= idx < len(self.filtered_emails):
                email = self.filtered_emails[idx]
                detail = self.query_one("#email_detail", EmailDetail)
                detail.update_email(email, show_signals=self.show_signals)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "refresh_button":
            self.action_refresh()
        elif event.button.id == "open_button":
            self.action_open_email()
        elif event.button.id == "list_accounts_button":
            self.action_list_accounts()
    
    def action_refresh(self) -> None:
        """Refresh the email list."""
        self.load_emails()
    
    def action_open_email(self) -> None:
        """Open the selected email."""
        table = self.query_one("#email_table", EmailTable)
        client_select = self.query_one("#client_select", Select)
        
        if not self.filtered_emails:
            self.notify("No emails to open", severity="warning")
            return
        
        # Get the currently highlighted row
        try:
            cursor_row = table.cursor_row
            if cursor_row is not None and 0 <= cursor_row < len(self.filtered_emails):
                idx = cursor_row
            else:
                # If no row selected, use first email
                idx = 0
        except:
            idx = 0
        
        email = self.filtered_emails[idx]
        
        # Use client from selector or default
        try:
            client_value = client_select.value if client_select else None
            client = 'apple-mail' if not client_value or client_value == 'auto' else client_value
        except:
            client = 'apple-mail'
        
        try:
            success = open_email(email, client=client)
            if success:
                subject = email.get('subject', 'Unknown')[:50]
                self.notify(f"Opened: {subject}", severity="success")
            else:
                self.notify("Failed to open email", severity="warning")
        except Exception as e:
            self.notify(f"Error opening email: {e}", severity="error")
            import traceback
            print(f"Error opening email: {e}")
            print(traceback.format_exc())
    
    def action_focus_filters(self) -> None:
        """Focus the filters section."""
        self.query_one("#limit_input", Input).focus()
    
    def action_focus_table(self) -> None:
        """Focus the table."""
        self.query_one("#email_table", EmailTable).focus()
    
    def action_list_accounts(self) -> None:
        """Show available accounts."""
        if self.available_accounts:
            accounts_str = "\n".join([f"  - {acc}" for acc in self.available_accounts])
            self.notify(f"Available accounts:\n{accounts_str}", severity="information", timeout=10)
        else:
            self.notify("No accounts found. Try refreshing.", severity="warning")
    
    def action_toggle_signals(self) -> None:
        """Toggle signal display."""
        signals_checkbox = self.query_one("#signals_checkbox", Checkbox)
        signals_checkbox.value = not signals_checkbox.value
        self.show_signals = signals_checkbox.value
        # Refresh detail view if email is selected
        table = self.query_one("#email_table", EmailTable)
        if table.cursor_row is not None and self.filtered_emails:
            idx = int(table.cursor_row)
            if 0 <= idx < len(self.filtered_emails):
                email = self.filtered_emails[idx]
                detail = self.query_one("#email_detail", EmailDetail)
                detail.update_email(email, show_signals=self.show_signals)
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def main():
    """Main entry point for UI."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Email Accounting TUI')
    parser.add_argument('--client', choices=['apple-mail', 'outlook', 'auto'], default='auto',
                       help='Email client to use')
    parser.add_argument('--account', type=str, help='Filter by account')
    parser.add_argument('--user-name', type=str, help='Your name (for personal mention detection)')
    
    args = parser.parse_args()
    
    client = None if args.client == 'auto' else args.client
    
    app = EmailAccountingApp(client=client, account=args.account, user_name=args.user_name)
    app.run()


if __name__ == '__main__':
    main()
