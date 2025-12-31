#!/usr/bin/env python3
"""Test if the API works"""
from main_app import EmailTriageAPI
import json

# Test API
api = EmailTriageAPI(client='auto', account='ews')
print("API initialized")

# Test get_emails
try:
    result = api.get_emails(account='ews', limit=5, since_days=7)
    emails = json.loads(result)
    print(f"SUCCESS: Got {len(emails)} emails")
    if emails:
        print(f"First email: {emails[0]['subject'][:50]}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
