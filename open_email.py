"""
open_email.py - Open emails in email client applications

Supports opening emails in:
- Apple Mail (using AppleScript)
- Outlook (using AppleScript or URL scheme)
"""

import subprocess
import sys
from typing import Optional, Dict, Any


def open_email_in_apple_mail(message_id: str, subject: str, account: Optional[str] = None) -> bool:
    """
    Open an email in Apple Mail using AppleScript.
    
    Args:
        message_id: Message ID from the database
        subject: Email subject line
        account: Account name (optional, helps narrow search)
        
    Returns:
        True if successful, False otherwise
    """
    # AppleScript to find and open the email
    # We search by subject since message IDs might not match exactly
    script = f'''
    tell application "Mail"
        activate
        set foundMessage to missing value
        
        -- Try to find the message by subject
        repeat with theAccount in accounts
            repeat with theMailbox in mailboxes of theAccount
                set matchingMessages to (messages of theMailbox whose subject contains "{subject[:50]}")
                if (count of matchingMessages) > 0 then
                    set foundMessage to item 1 of matchingMessages
                    exit repeat
                end if
            end repeat
            if foundMessage is not missing value then
                exit repeat
            end if
        end repeat
        
        if foundMessage is not missing value then
            open foundMessage
            return "success"
        else
            return "not found"
        end if
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and 'success' in result.stdout:
            return True
        else:
            print(f"Could not find email in Apple Mail: {result.stderr}", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("Timeout opening email in Apple Mail", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error opening email in Apple Mail: {e}", file=sys.stderr)
        return False


def open_email_in_outlook(message_id: str, subject: str) -> bool:
    """
    Open an email in Outlook using AppleScript.
    
    Args:
        message_id: Message ID from the database
        subject: Email subject line
        
    Returns:
        True if successful, False otherwise
    """
    # Outlook AppleScript to find and open the email
    script = f'''
    tell application "Microsoft Outlook"
        activate
        set foundMessage to missing value
        
        -- Search for the message by subject
        set allMessages to messages
        repeat with theMessage in allMessages
            if subject of theMessage contains "{subject[:50]}" then
                set foundMessage to theMessage
                exit repeat
            end if
        end repeat
        
        if foundMessage is not missing value then
            open foundMessage
            return "success"
        else
            return "not found"
        end if
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and 'success' in result.stdout:
            return True
        else:
            print(f"Could not find email in Outlook: {result.stderr}", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("Timeout opening email in Outlook", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error opening email in Outlook: {e}", file=sys.stderr)
        return False


def open_email(message: Dict[str, Any], client: str = 'apple-mail') -> bool:
    """
    Open an email in the specified email client.
    
    Args:
        message: Message dictionary with at least 'message_id' and 'subject'
        client: 'apple-mail' or 'outlook'
        
    Returns:
        True if successful, False otherwise
    """
    message_id = message.get('message_id') or ''
    subject = message.get('subject') or ''
    
    if not subject:
        print("Cannot open email: no subject found", file=sys.stderr)
        return False
    
    if client == 'apple-mail' or client == 'apple_mail':
        return open_email_in_apple_mail(message_id, subject, message.get('account'))
    elif client == 'outlook':
        return open_email_in_outlook(message_id, subject)
    else:
        print(f"Unknown email client: {client}", file=sys.stderr)
        return False

