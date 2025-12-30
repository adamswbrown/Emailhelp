"""
applescript_search.py - AppleScript-based Email Search

Provides real-time email search using AppleScript to query Mail.app directly.
This is more reliable than database queries and provides real-time results.

Based on best practices from Apple Mail MCP server.
"""

import subprocess
import json
from typing import List, Dict, Any, Optional
from datetime import datetime


def run_applescript(script: str) -> str:
    """
    Execute AppleScript and return output.
    
    Args:
        script: AppleScript code to execute
        
    Returns:
        Script output as string
        
    Raises:
        Exception: If AppleScript execution fails or times out
    """
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            raise Exception(f"AppleScript error: {result.stderr}")
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise Exception("AppleScript execution timed out")
    except Exception as e:
        raise Exception(f"AppleScript execution failed: {str(e)}")


def get_accounts() -> List[str]:
    """
    Get list of all available Mail accounts.
    
    Returns:
        List of account names
    """
    script = '''
    tell application "Mail"
        set accountList to {}
        set allAccounts to every account
        repeat with anAccount in allAccounts
            set end of accountList to name of anAccount
        end repeat
        set AppleScript's text item delimiters to "|"
        return accountList as string
    end tell
    '''
    
    try:
        result = run_applescript(script)
        if result:
            return [acc.strip() for acc in result.split('|') if acc.strip()]
        return []
    except Exception:
        return []


def search_emails(
    account: Optional[str] = None,
    mailbox: str = "INBOX",
    subject_keyword: Optional[str] = None,
    sender: Optional[str] = None,
    unread_only: bool = False,
    max_results: int = 50,
    include_content: bool = True,
    max_content_length: int = 500
) -> List[Dict[str, Any]]:
    """
    Search emails using AppleScript (real-time from Mail.app).
    
    This provides more reliable and up-to-date results than database queries.
    
    Args:
        account: Account name to search (None = all accounts)
        mailbox: Mailbox to search (default: "INBOX", use "All" for all mailboxes)
        subject_keyword: Optional keyword to search in subject (case-insensitive)
        sender: Optional sender email or name to filter by
        unread_only: Only return unread emails
        max_results: Maximum number of results to return
        include_content: Whether to include email content preview
        max_content_length: Maximum content preview length (0 = unlimited)
        
    Returns:
        List of email dictionaries with metadata
    """
    # Build search conditions
    conditions = []
    
    if subject_keyword:
        # Case-insensitive subject search
        conditions.append(f'lowercase(messageSubject) contains lowercase("{subject_keyword}")')
    
    if sender:
        conditions.append(f'messageSender contains "{sender}"')
    
    if unread_only:
        conditions.append('messageRead is false')
    
    # Combine conditions
    condition_str = ' and '.join(conditions) if conditions else 'true'
    
    # Build mailbox selection logic
    if mailbox == "All":
        mailbox_script = '''
            set allMailboxes to every mailbox of targetAccount
            set searchMailboxes to allMailboxes
        '''
    else:
        mailbox_script = f'''
            try
                set searchMailbox to mailbox "{mailbox}" of targetAccount
            on error
                if "{mailbox}" is "INBOX" then
                    set searchMailbox to mailbox "Inbox" of targetAccount
                else
                    error "Mailbox not found: {mailbox}"
                end if
            end try
            set searchMailboxes to {{searchMailbox}}
        '''
    
    # Build account filtering
    if account:
        account_filter = f'''
        repeat with anAccount in allAccounts
            set accountName to name of anAccount
            if accountName is "{account}" then
        '''
        account_filter_end = '''
            end if
        end repeat
        '''
    else:
        account_filter = '''
        repeat with anAccount in allAccounts
            set accountName to name of anAccount
        '''
        account_filter_end = 'end repeat'
    
    # Content extraction script
    if include_content:
        content_script = f'''
            try
                set msgContent to content of aMessage
                set AppleScript's text item delimiters to {{return, linefeed}}
                set contentParts to text items of msgContent
                set AppleScript's text item delimiters to " "
                set cleanText to contentParts as string
                set AppleScript's text item delimiters to ""
                
                -- Always store full content
                set fullContent to cleanText
                
                -- Create preview if length limit is set
                if {max_content_length} > 0 and length of cleanText > {max_content_length} then
                    set previewText to text 1 thru {max_content_length} of cleanText & "..."
                else
                    set previewText to cleanText
                end if
            on error
                set previewText to ""
                set fullContent to ""
            end try
        '''
    else:
        content_script = '''
            set previewText to ""
            set fullContent to ""
        '''
    
    # Build main script
    script = f'''
    on lowercase(str)
        set lowerStr to do shell script "echo " & quoted form of str & " | tr '[:upper:]' '[:lower:]'"
        return lowerStr
    end lowercase

    tell application "Mail"
        set emailData to ""
        set allAccounts to every account
        
        {account_filter}
            try
                set targetAccount to anAccount
                {mailbox_script}
                
                repeat with currentMailbox in searchMailboxes
                    set mailboxMessages to every message of currentMailbox
                    set mailboxName to name of currentMailbox
                    
                    repeat with aMessage in mailboxMessages
                        if length of emailData > 0 and (count of (text items of emailData whose contents is "|||")) >= {max_results} then
                            exit repeat
                        end if
                        
                        try
                            set messageSubject to subject of aMessage
                            set messageSender to sender of aMessage
                            set messageDate to date received of aMessage
                            set messageRead to read status of aMessage
                            
                            -- Apply search conditions
                            if {condition_str} then
                                {content_script}
                                
                                -- Output as delimited format: ||| separates emails, || separates fields
                                -- Format: account||mailbox||subject||sender||date||read||preview||content
                                set emailData to emailData & "|||" & accountName & "||" & mailboxName & "||" & messageSubject & "||" & messageSender & "||" & (messageDate as string) & "||" & messageRead & "||" & previewText & "||" & fullContent
                            end if
                        end try
                    end repeat
                end repeat
            on error errMsg
                -- Skip accounts with errors
            end try
        {account_filter_end}
        
        return emailData
    end tell
    '''
    
    try:
        result = run_applescript(script)
        emails = []
        
        # Parse delimited output
        if result and result.strip():
            email_blocks = result.split('|||')
            for block in email_blocks:
                block = block.strip()
                if not block:
                    continue
                
                parts = block.split('||')
                if len(parts) >= 7:
                    # Parse date string to timestamp
                    date_str = parts[4] if len(parts) > 4 else ''
                    timestamp = None
                    if date_str:
                        try:
                            # Try to parse AppleScript date format
                            # Format: "Monday, December 30, 2024 at 10:30:00 AM"
                            dt = datetime.strptime(date_str, "%A, %B %d, %Y at %I:%M:%S %p")
                            timestamp = dt.timestamp()
                        except (ValueError, IndexError):
                            try:
                                # Try alternative format without seconds
                                dt = datetime.strptime(date_str, "%A, %B %d, %Y at %I:%M %p")
                                timestamp = dt.timestamp()
                            except (ValueError, IndexError):
                                # If parsing fails, leave timestamp as None
                                pass
                    
                    preview = parts[6] if len(parts) > 6 else ''
                    content = parts[7] if len(parts) > 7 else preview  # Full content if available
                    
                    emails.append({
                        'account': parts[0] if len(parts) > 0 else '',
                        'mailbox': parts[1] if len(parts) > 1 else '',
                        'subject': parts[2] if len(parts) > 2 else '',
                        'sender': parts[3] if len(parts) > 3 else '',
                        'date_received': timestamp,
                        'date': date_str,
                        'read': parts[5].lower() == 'true' if len(parts) > 5 else False,
                        'preview': preview,
                        'content': content  # Full content (same as preview if limited)
                    })
        
        return emails
    except Exception as e:
        raise Exception(f"Error searching emails: {str(e)}")


def list_inbox_emails(
    account: Optional[str] = None,
    max_emails: int = 50,
    include_read: bool = True
) -> List[Dict[str, Any]]:
    """
    List emails from inbox (convenience wrapper for search_emails).
    
    Args:
        account: Optional account name to filter
        max_emails: Maximum number of emails to return
        include_read: Whether to include read emails
        
    Returns:
        List of email dictionaries
    """
    return search_emails(
        account=account,
        mailbox="INBOX",
        unread_only=not include_read,
        max_results=max_emails,
        include_content=True
    )


def get_email_content(
    account: str,
    subject_keyword: str,
    mailbox: str = "INBOX",
    max_results: int = 1
) -> List[Dict[str, Any]]:
    """
    Get full email content as plain text (unlimited length).
    
    This is useful for extracting full email content to pass to other applications.
    
    Args:
        account: Account name to search in
        subject_keyword: Keyword to search in subject (case-insensitive)
        mailbox: Mailbox to search (default: "INBOX")
        max_results: Maximum number of emails to return (default: 1)
        
    Returns:
        List of email dictionaries with full content in 'content' field
    """
    return search_emails(
        account=account,
        mailbox=mailbox,
        subject_keyword=subject_keyword,
        max_results=max_results,
        include_content=True,
        max_content_length=0  # 0 = unlimited
    )


def extract_email_content_as_text(
    account: str,
    subject_keyword: str,
    mailbox: str = "INBOX",
    include_metadata: bool = True
) -> str:
    """
    Extract email content as plain text string, ready to pass to other applications.
    
    Args:
        account: Account name to search in
        subject_keyword: Keyword to search in subject
        mailbox: Mailbox to search (default: "INBOX")
        include_metadata: Whether to include subject, sender, date headers
        
    Returns:
        Plain text string with email content (and optional metadata)
    """
    emails = get_email_content(account, subject_keyword, mailbox, max_results=1)
    
    if not emails:
        return ""
    
    email = emails[0]
    content = email.get('content', email.get('preview', ''))
    
    if include_metadata:
        lines = []
        lines.append(f"Subject: {email.get('subject', '')}")
        lines.append(f"From: {email.get('sender', '')}")
        lines.append(f"Date: {email.get('date', '')}")
        lines.append(f"Account: {email.get('account', '')}")
        lines.append("")
        lines.append("=" * 60)
        lines.append("CONTENT")
        lines.append("=" * 60)
        lines.append("")
        lines.append(content)
        return '\n'.join(lines)
    else:
        return content

