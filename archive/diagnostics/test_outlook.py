#!/usr/bin/env python3
"""
test_outlook.py - Test Outlook integration with scoring/classification

This demonstrates that Outlook database reading works with the same
scoring and classification logic as Apple Mail.
"""

import sys
from outlook_index import OutlookIndexReader
from scoring import EmailScorer
from classifier import EmailClassifier
from cli import TableFormatter

def main():
    """Test Outlook email reading and classification."""
    print("Testing Outlook Database Integration\n")
    
    try:
        # Initialize reader
        reader = OutlookIndexReader()
        print(f"✓ Connected to Outlook database: {reader.db_path}\n")
        
        # Get accounts
        with reader:
            accounts = reader.get_accounts()
            print(f"Found accounts: {accounts}\n")
            
            # Query messages
            messages = reader.query_messages(limit=20, since_days=30)
            print(f"Found {len(messages)} messages from last 30 days\n")
            
            if not messages:
                print("No messages found.")
                return 0
            
            # Initialize scorer
            scorer = EmailScorer()
            
            # Process and score emails
            processed = []
            for msg in messages:
                sender = msg.get('sender', '') or ''
                subject = msg.get('subject', '') or ''
                preview = msg.get('preview') or None
                
                # Score email
                score, signals = scorer.score_email(sender, subject, preview)
                category = EmailClassifier.classify(score)
                
                # Enrich message
                msg['score'] = score
                msg['signals'] = signals
                msg['category'] = category.value
                
                processed.append(msg)
            
            # Display results
            table = TableFormatter.format_ledger(processed, show_explanations=False)
            print(table)
            print()
            
            # Summary
            summary = TableFormatter.format_summary(processed)
            print(summary)
            
            return 0
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())

