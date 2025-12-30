"""
email_selector.py - Interactive email selection menu
"""

import sys
from typing import List, Dict, Any, Optional


def select_email_interactive(emails: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Display an interactive menu to select an email.
    
    Args:
        emails: List of email dictionaries
        
    Returns:
        Selected email dictionary or None if cancelled
    """
    if not emails:
        print("No emails to select from.", file=sys.stderr)
        return None
    
    # Display numbered list
    print("\n" + "=" * 80, file=sys.stderr)
    print("SELECT EMAIL TO OPEN:", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    print(file=sys.stderr)
    
    for idx, email in enumerate(emails, 1):
        date = email.get('date_received')
        sender = email.get('sender', '')[:30]
        subject = email.get('subject', '')[:50]
        score = email.get('score', 0)
        category = email.get('category', '')
        
        # Format date
        if date:
            from datetime import datetime
            try:
                date_str = datetime.fromtimestamp(date).strftime('%d/%m/%Y %H:%M')
            except:
                date_str = str(date)
        else:
            date_str = 'Unknown'
        
        print(f"  [{idx:2d}] {date_str} | {sender:<30} | {subject:<50} | {score:3d} | {category}", file=sys.stderr)
    
    print(file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    print(file=sys.stderr)
    
    # Get user input
    while True:
        try:
            choice = input("Enter email number to open (or 'q' to quit): ").strip()
            
            if choice.lower() == 'q':
                print("Cancelled.", file=sys.stderr)
                return None
            
            idx = int(choice)
            if 1 <= idx <= len(emails):
                return emails[idx - 1]
            else:
                print(f"Please enter a number between 1 and {len(emails)}.", file=sys.stderr)
        except ValueError:
            print("Please enter a valid number or 'q' to quit.", file=sys.stderr)
        except KeyboardInterrupt:
            print("\nCancelled.", file=sys.stderr)
            return None
        except EOFError:
            print("\nCancelled.", file=sys.stderr)
            return None

