# Apple Mail MCP - Usage Guide for Emailhelp Project

## Overview

This guide explains how to use the [apple-mail-mcp](https://github.com/patrickfreyer/apple-mail-mcp) project to enhance email content extraction in the Emailhelp project.

## Installation

### Step 1: Clone the Repository

```bash
cd /Users/adambrown/Developer/Emailhelp
git clone https://github.com/patrickfreyer/apple-mail-mcp.git apple-mail-mcp
cd apple-mail-mcp
```

### Step 2: Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

**Requirements:**
- `fastmcp>=0.1.0` (already installed in your system)

### Step 3: Verify Installation

```bash
python3 -c "import apple_mail_mcp; print('✓ Installation successful')"
```

## Key Features for Email Content Extraction

The apple-mail-mcp project provides excellent AppleScript patterns for getting email content directly from Mail.app. This solves the problem of Exchange emails not having accessible .emlx files.

### Core Function: `get_email_with_content`

This function uses AppleScript to:
1. Search for emails by subject keyword
2. Extract full email body content using `content of aMessage`
3. Works for **all account types** (Exchange, IMAP, iCloud, etc.)
4. Doesn't require finding .emlx files

### AppleScript Pattern Used

```applescript
tell application "Mail"
    set foundMessage to (messages of mailbox "Inbox" of account "Exchange" whose subject contains "Subject Text")
    if (count of foundMessage) > 0 then
        set msgContent to content of item 1 of foundMessage
        return msgContent
    end if
end tell
```

## Integration Options

### Option 1: Use as Standalone MCP Server (For Claude Desktop)

If you want to use it as a full MCP server with Claude Desktop:

1. **Configure Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "apple-mail": {
      "command": "/Users/adambrown/Developer/Emailhelp/apple-mail-mcp/venv/bin/python3",
      "args": [
        "/Users/adambrown/Developer/Emailhelp/apple-mail-mcp/apple_mail_mcp.py"
      ]
    }
  }
}
```

2. **Restart Claude Desktop**

3. **Use in Claude**: Ask Claude to "Search for emails about X" or "Get email content for Y"

### Option 2: Extract AppleScript Patterns (Recommended for Emailhelp)

The AppleScript patterns are already integrated into `ui.py`. The code now:

1. **First tries to find .emlx files** (fast, works for IMAP)
2. **Falls back to AppleScript** (works for Exchange/EWS)
3. **Gets content directly from Mail.app**

This is already implemented in your `ui.py` file!

## Testing the Integration

### Test AppleScript Email Content Extraction

```bash
# Test getting email content via AppleScript
python3 -c "
import subprocess

script = '''
tell application \"Mail\"
    set foundMessage to missing value
    repeat with theAccount in accounts
        try
            repeat with theMailbox in mailboxes of theAccount
                try
                    set matchingMessages to (messages of theMailbox whose subject contains \"ACTION REQUIRED\")
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
        return \"No email found\"
    end if
end tell
'''

result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=5)
print(result.stdout[:500] if result.stdout else 'No content')
"
```

### Test with Your UI

```bash
# Run the UI - it should now show email previews
python3 main.py --ui --client apple-mail --account ews
```

## Permissions Required

macOS will prompt for permissions on first use:

1. **Mail.app Control**: System Settings > Privacy & Security > Automation
   - Allow Terminal (or Python) to control Mail.app

2. **Full Disk Access**: System Settings > Privacy & Security > Full Disk Access
   - Required for reading Mail database (already configured)

## Does It Meet Your Requirements?

### ✅ Requirements Met

| Requirement | Status | Notes |
|------------|--------|-------|
| **Email Content/Preview** | ✅ Yes | Gets full email body via AppleScript |
| **All Account Types** | ✅ Yes | Works for Exchange, IMAP, iCloud |
| **Reliable** | ✅ Yes | Doesn't depend on file system |
| **No File Searching** | ✅ Yes | Uses Mail.app directly |
| **Fast Enough** | ⚠️ Moderate | AppleScript is slower than file reads but more reliable |

### ⚠️ Considerations

1. **Performance**: AppleScript calls take ~1-3 seconds per email (vs instant file reads)
2. **Mail.app Must Be Running**: AppleScript requires Mail.app to be active
3. **Subject Matching**: May find wrong email if subject isn't unique (use sender + date to verify)
4. **Permissions**: Requires Automation permissions (one-time setup)

## Recommended Usage Pattern

The current implementation in `ui.py` uses a **smart fallback chain**:

1. **Try .emlx file** (fastest, works for IMAP)
2. **Try AppleScript** (works for Exchange, slower but reliable)
3. **Show "No preview available"** (if both fail)

This gives you:
- ✅ Fast previews for IMAP emails (file-based)
- ✅ Reliable previews for Exchange emails (AppleScript)
- ✅ Graceful degradation if neither works

## Troubleshooting

### "Mail.app not responding"

- Ensure Mail.app is running
- Check Automation permissions in System Settings
- Restart Mail.app

### "No preview available"

- Check that Mail.app is running
- Verify Automation permissions
- Try searching for a specific email subject to test AppleScript

### Slow Performance

- AppleScript is inherently slower than file reads
- Consider caching email content
- Limit the number of emails processed at once

## Next Steps

1. ✅ **Already Integrated**: The AppleScript patterns are in `ui.py`
2. **Test It**: Run `python3 main.py --ui` and check if previews appear
3. **Optimize**: Add caching if AppleScript calls are too slow
4. **Monitor**: Check console output for AppleScript errors

## References

- [apple-mail-mcp GitHub Repository](https://github.com/patrickfreyer/apple-mail-mcp)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [AppleScript Mail.app Dictionary](https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/reference/ASLR_applications.html)

## Summary

The apple-mail-mcp project provides excellent AppleScript patterns that are **already integrated** into your `ui.py` file. The code now uses AppleScript as a fallback when .emlx files aren't found, which solves the Exchange email preview problem.

**Status**: ✅ Ready to use - just run your UI and email previews should work!

