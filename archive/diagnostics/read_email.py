#!/usr/bin/env python3
"""
read_email.py - Read full content of a specific email
"""

import sys
from mail_index import MailIndexReader
from preview import EmailPreview
import email
from email import policy
from pathlib import Path

def find_and_read_email(subject_pattern: str, account: str = None):
    """Find email by subject pattern and read its content."""
    
    reader = MailIndexReader()
    
    with reader:
        messages = reader.query_messages(limit=500, account=account)
    
    # Find matching email
    for msg in messages:
        subject = msg.get('subject', '') or ''
        if subject_pattern.lower() in subject.lower():
            print(f"Found email:")
            print(f"  Date: {msg.get('date_received')}")
            print(f"  From: {msg.get('sender', 'Unknown')}")
            print(f"  Subject: {subject}")
            print(f"  Mailbox: {msg.get('mailbox', 'Unknown')}")
            print()
            
            # Try to get emlx path
            emlx_path = msg.get('emlx_path')
            if not emlx_path:
                # Try to construct path
                # Path pattern: ~/Library/Mail/V*/mailbox_path/Messages/message_id.emlx
                message_id = msg.get('message_id')
                mailbox = msg.get('mailbox', '')
                
                if message_id and mailbox:
                    # Try to find the emlx file
                    mail_dir = Path.home() / "Library" / "Mail"
                    for v_dir in sorted(mail_dir.glob("V*"), reverse=True):
                        # Search in account directories
                        for account_dir in v_dir.glob("*"):
                            if account_dir.is_dir():
                                messages_dir = account_dir / "Messages"
                                if messages_dir.exists():
                                    emlx_file = messages_dir / f"{message_id}.emlx"
                                    if emlx_file.exists():
                                        emlx_path = str(emlx_file)
                                        break
                        if emlx_path:
                            break
                    if not emlx_path:
                        # Try alternative path structure
                        for v_dir in sorted(mail_dir.glob("V*"), reverse=True):
                            maildata_dir = v_dir / "MailData"
                            if maildata_dir.exists():
                                # Search recursively
                                for emlx_file in maildata_dir.rglob(f"{message_id}.emlx"):
                                    emlx_path = str(emlx_file)
                                    break
                            if emlx_path:
                                break
            
            if emlx_path and Path(emlx_path).exists():
                print(f"Reading email content from: {emlx_path}")
                print("=" * 80)
                
                try:
                    # Read full email
                    with open(emlx_path, 'rb') as f:
                        first_line = f.readline()  # Skip byte count
                        raw_email = f.read()
                    
                    # Parse email
                    msg_obj = email.message_from_bytes(raw_email, policy=policy.default)
                    
                    # Print headers
                    print("\nHEADERS:")
                    print("-" * 80)
                    for key in ['From', 'To', 'Cc', 'Subject', 'Date', 'Message-ID']:
                        value = msg_obj.get(key, 'N/A')
                        if value != 'N/A':
                            print(f"{key:15s}: {value}")
                    
                    # Print body
                    print("\nBODY:")
                    print("-" * 80)
                    
                    body = EmailPreview._extract_body(msg_obj)
                    if body:
                        print(body)
                    else:
                        print("[No body content found]")
                    
                    return True
                    
                except Exception as e:
                    print(f"Error reading email: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
            else:
                print("Could not locate .emlx file for this email.")
                print(f"Message ID: {msg.get('message_id')}")
                print(f"Mailbox: {msg.get('mailbox')}")
                return False
    
    print(f"No email found matching: {subject_pattern}")
    return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Read email content')
    parser.add_argument('subject', help='Subject pattern to search for')
    parser.add_argument('--account', help='Account filter (e.g., ews)')
    
    args = parser.parse_args()
    
    find_and_read_email(args.subject, args.account)

