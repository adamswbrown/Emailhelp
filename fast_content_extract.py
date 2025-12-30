"""
fast_content_extract.py - Fast email content extraction using targeted AppleScript

Uses subject + sender combination to quickly find and extract specific email content.
Much faster than broad keyword searches.
"""

import subprocess
import sys
from typing import Optional


def get_email_content_by_details(
    account: str,
    subject: str,
    sender: str,
    mailbox: str = "INBOX",
    timeout: int = 30
) -> Optional[str]:
    """
    Get email content using exact subject and sender match (fast, targeted).
    
    This is much faster than keyword search because it:
    1. Searches only the specified mailbox
    2. Matches exact subject and sender
    3. Returns immediately when found
    4. Uses shorter timeout (30 seconds)
    
    Args:
        account: Account display name (e.g., "Exchange", "iCloud")
        subject: Exact email subject
        sender: Sender email address
        mailbox: Mailbox name (default: "INBOX")
        timeout: Timeout in seconds (default: 30)
        
    Returns:
        Email content as string or None if not found
    """
    # Escape quotes in subject and sender for AppleScript
    subject_escaped = subject.replace('"', '\\"').replace('\\', '\\\\')
    sender_escaped = sender.replace('"', '\\"').replace('\\', '\\\\')
    
    # Extract just the domain from sender for matching
    sender_domain = sender.split('@')[-1] if '@' in sender else sender
    
    # Build AppleScript for targeted search
    script = f'''
    tell application "Mail"
        set foundContent to ""
        
        try
            set targetAccount to account "{account}"
            
            -- Get target mailbox
            try
                set targetMailbox to mailbox "{mailbox}" of targetAccount
            on error
                if "{mailbox}" is "INBOX" then
                    set targetMailbox to mailbox "Inbox" of targetAccount
                else
                    error "Mailbox not found: {mailbox}"
                end if
            end try
            
            -- Search for email by subject and sender domain
            -- Limit search to recent messages for speed
            set mailboxMessages to messages of targetMailbox
            set messageCount to count of mailboxMessages
            set searchLimit to 100  -- Only search recent 100 messages
            if messageCount > searchLimit then
                set searchMessages to items 1 thru searchLimit of mailboxMessages
            else
                set searchMessages to mailboxMessages
            end if
            
            repeat with aMessage in searchMessages
                try
                    set messageSubject to subject of aMessage
                    set messageSender to sender of aMessage
                    
                    -- Check if subject matches exactly and sender domain matches
                    if messageSubject is "{subject_escaped}" and messageSender contains "{sender_domain}" then
                        -- Found it! Get content and exit immediately
                        set msgContent to content of aMessage
                        return msgContent
                    end if
                end try
            end repeat
            
            -- If exact match not found, try partial subject match (first 50 chars)
            repeat with aMessage in searchMessages
                try
                    set messageSubject to subject of aMessage
                    set messageSender to sender of aMessage
                    
                    -- Try partial match on subject (in case of truncation)
                    if messageSubject contains "{subject_escaped[:50]}" and messageSender contains "{sender_domain}" then
                        set msgContent to content of aMessage
                        return msgContent
                    end if
                end try
            end repeat
            
            return "EMAIL_NOT_FOUND"
            
        on error errMsg
            return "ERROR: " & errMsg
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode != 0:
            return None
        
        output = result.stdout.strip()
        
        if output == "EMAIL_NOT_FOUND":
            return None
        elif output.startswith("ERROR:"):
            print(f"AppleScript error: {output}", file=sys.stderr)
            return None
        else:
            return output
            
    except subprocess.TimeoutExpired:
        print(f"Timeout after {timeout} seconds", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None

