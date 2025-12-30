# Microsoft Graph API Setup Guide

This guide will help you set up Microsoft Graph API access for testing.

## Step 1: Register an Application in Azure

1. Go to [Azure Portal](https://portal.azure.com)
2. Sign in with your Microsoft account (work or personal)
3. Navigate to **Azure Active Directory** > **App registrations**
4. Click **New registration**
5. Fill in:
   - **Name**: `Email Classifier Test` (or any name)
   - **Supported account types**: 
     - Select **"Accounts in any organizational directory and personal Microsoft accounts"** for maximum compatibility
   - **Redirect URI**: Leave blank for device code flow
6. Click **Register**

## Step 2: Get Your Client ID

After registration:
1. Copy the **Application (client) ID** - this is your `CLIENT_ID`
2. Note the **Directory (tenant) ID** - you can use `"common"` instead for multi-tenant

## Step 3: Configure API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Select **Delegated permissions**
5. Search for and add:
   - `Mail.Read` - Read mail in all mailboxes
6. Click **Add permissions**
7. **Important**: Click **Grant admin consent** if you're an admin (or ask your IT admin)

## Step 4: Install Required Packages

```bash
pip install msal requests
```

## Step 5: Update the Test Script

Edit `test_graph_api.py` and replace:
```python
CLIENT_ID = "YOUR_CLIENT_ID_HERE"
```

With your actual Client ID from Step 2.

## Step 6: Run the Test

```bash
python3 test_graph_api.py
```

The script will:
1. Display a URL and code
2. You open the URL in a browser
3. Enter the code
4. Sign in with your Microsoft account
5. Grant permissions
6. Fetch and display your emails

## Troubleshooting

### "Invalid client" error
- Make sure you copied the Client ID correctly
- Check that the app registration is complete

### "Insufficient privileges" error
- Make sure you added `Mail.Read` permission
- Make sure admin consent was granted (if required by your organization)

### "AADSTS70011: The provided value for the input parameter 'scope' is not valid"
- Make sure the scope is exactly `Mail.Read` (case-sensitive)

### No emails returned
- Check that you have emails in your mailbox
- Try increasing the limit in `get_emails()` function

## Next Steps

Once this test works, we can integrate it into the main tool to:
- Support both Apple Mail (local) and Outlook (Graph API)
- Use the same scoring/classification logic
- Provide a unified interface

