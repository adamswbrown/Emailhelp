#!/usr/bin/env python3
"""
test_graph_api.py - Small-scale test of Microsoft Graph API

This script tests:
1. OAuth 2.0 authentication with Microsoft Graph
2. Pulling emails from your account
3. Basic email data extraction

Requirements:
    pip install msal requests
"""

import sys
import json
from typing import Optional, Dict, Any

try:
    import msal
    import requests
except ImportError:
    print("ERROR: Missing required packages.")
    print("Install with: pip install msal requests")
    sys.exit(1)


# Configuration
CLIENT_ID = "bb2c8281-6346-49f5-9dd7-9c8c09c18b2c"  # Your Application (client) ID
TENANT_ID = "95e3e402-49e1-4ad0-b73d-18c03e864448"  # Your Directory (tenant) ID
# Try tenant-specific first, fall back to "common" if needed
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# Scopes needed for reading emails
SCOPES = ["Mail.Read"]

# Graph API endpoint
GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"


def get_access_token() -> Optional[str]:
    """
    Authenticate and get access token using device code flow.
    This is the simplest method for CLI tools.
    """
    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY
    )
    
    # Try to get token from cache first
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            print("✓ Using cached token")
            return result["access_token"]
    
    # If no cached token, use device code flow
    print("Starting device code flow...")
    try:
        flow = app.initiate_device_flow(scopes=SCOPES)
    except Exception as e:
        print(f"ERROR: Failed to initiate device flow: {e}")
        print("\nPossible issues:")
        print("1. App might need to be configured as 'Public client' in Azure")
        print("2. Check Azure Portal > App registration > Authentication")
        print("3. Enable 'Allow public client flows' = Yes")
        return None
    
    if "user_code" not in flow:
        error_msg = flow.get("error", "Unknown error")
        error_desc = flow.get("error_description", "")
        print(f"ERROR: Failed to create device flow")
        print(f"Error: {error_msg}")
        if error_desc:
            print(f"Description: {error_desc}")
        print("\nPossible fixes:")
        print("1. In Azure Portal, go to your app registration")
        print("2. Authentication > Allow public client flows = Yes")
        print("3. Save and try again")
        return None
    
    print(f"\nTo sign in, use a web browser to open the page:")
    print(f"{flow['verification_uri']}")
    print(f"and enter the code: {flow['user_code']}\n")
    
    # Poll for token
    result = app.acquire_token_by_device_flow(flow)
    
    if "access_token" in result:
        print("✓ Authentication successful!")
        return result["access_token"]
    else:
        print(f"ERROR: Authentication failed: {result.get('error_description', 'Unknown error')}")
        return None


def get_emails(access_token: str, limit: int = 10) -> list:
    """
    Fetch emails from Microsoft Graph API.
    
    Args:
        access_token: OAuth access token
        limit: Maximum number of emails to fetch
        
    Returns:
        List of email dictionaries
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Graph API endpoint for messages
    url = f"{GRAPH_ENDPOINT}/me/messages"
    params = {
        "$top": limit,
        "$select": "id,subject,sender,receivedDateTime,isRead,bodyPreview",
        "$orderby": "receivedDateTime desc"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get("value", [])
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to fetch emails: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return []


def format_email(email: Dict[str, Any]) -> str:
    """Format email for display."""
    sender = email.get("sender", {}).get("emailAddress", {}).get("address", "Unknown")
    subject = email.get("subject", "(No subject)")
    received = email.get("receivedDateTime", "Unknown")
    is_read = "✓" if email.get("isRead", False) else "✗"
    
    # Parse date
    if received != "Unknown":
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(received.replace("Z", "+00:00"))
            received = dt.strftime("%Y-%m-%d %H:%M")
        except:
            pass
    
    return f"{received} | {is_read} | {sender[:30]:<30} | {subject[:50]}"


def main():
    """Main test function."""
    print("=" * 80)
    print("Microsoft Graph API Test")
    print("=" * 80)
    print()
    
    # Check if CLIENT_ID is set
    if CLIENT_ID == "YOUR_CLIENT_ID_HERE":
        print("ERROR: Please set CLIENT_ID in this script.")
        print()
        print("To get a CLIENT_ID:")
        print("1. Go to https://portal.azure.com")
        print("2. Azure Active Directory > App registrations > New registration")
        print("3. Name it (e.g., 'Email Classifier')")
        print("4. Supported account types: 'Accounts in any organizational directory'")
        print("5. Copy the Application (client) ID")
        print("6. API permissions > Add permission > Microsoft Graph > Delegated permissions")
        print("7. Add 'Mail.Read' permission")
        print("8. Update CLIENT_ID in this script")
        sys.exit(1)
    
    # Get access token
    print("Step 1: Authenticating...")
    access_token = get_access_token()
    
    if not access_token:
        print("\nFailed to get access token. Exiting.")
        sys.exit(1)
    
    print()
    
    # Fetch emails
    print("Step 2: Fetching emails...")
    emails = get_emails(access_token, limit=10)
    
    if not emails:
        print("No emails found or error occurred.")
        sys.exit(1)
    
    print(f"✓ Found {len(emails)} emails\n")
    
    # Display emails
    print("=" * 80)
    print("EMAILS")
    print("=" * 80)
    print(f"{'DATE':<20} | {'READ':<5} | {'FROM':<30} | {'SUBJECT'}")
    print("-" * 80)
    
    for email in emails:
        print(format_email(email))
    
    print()
    print("=" * 80)
    print("Test completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()

