# Apple Mail MCP Evaluation & Integration Guide

## Overview

This document evaluates the [apple-mail-mcp](https://github.com/patrickfreyer/apple-mail-mcp) project and provides guidance on using it to enhance email content extraction in this project.

## Project Evaluation

### What apple-mail-mcp Provides

The [apple-mail-mcp](https://github.com/patrickfreyer/apple-mail-mcp) project is an MCP (Model Context Protocol) server that provides:

1. **Email Reading & Search**: Advanced search with full content preview
2. **Email Content Access**: Uses AppleScript to get email body text directly from Apple Mail
3. **Account & Mailbox Management**: List accounts, mailboxes, and folder structures
4. **Email Operations**: Move, reply, compose, forward emails
5. **Attachment Handling**: List and save attachments

### Key Features Relevant to This Project

#### ✅ Email Content Extraction
- **`get_email_with_content`**: Retrieves emails with full body text using AppleScript
- **`search_emails`**: Advanced search that can include email content
- Uses AppleScript's `content` property to get email body directly from Mail.app

#### ✅ Better than .emlx File Parsing
- Works for **all email types** (IMAP, Exchange, iCloud, etc.)
- Doesn't require finding .emlx files in nested directories
- More reliable for Exchange/EWS emails
- Gets content directly from Mail.app's memory

### Installation

```bash
# Clone the repository
cd /Users/adambrown/Developer/Emailhelp
git clone https://github.com/patrickfreyer/apple-mail-mcp.git apple-mail-mcp

# Install dependencies
cd apple-mail-mcp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Requirements

The project requires:
- Python 3.7+
- `fastmcp` library
- macOS with Apple Mail.app
- Full Disk Access permissions
- Mail.app Automation permissions

### Integration Approach

Instead of using it as an MCP server, we can extract the AppleScript-based email content retrieval functions to use directly in our project.

## Key AppleScript Patterns from apple-mail-mcp

### Getting Email Content

The project uses AppleScript like this:

```applescript
tell application "Mail"
    set foundMessage to (messages of mailbox "Inbox" of account "Exchange" whose subject contains "Subject Text")
    if (count of foundMessage) > 0 then
        set msgContent to content of item 1 of foundMessage
        return msgContent
    end if
end tell
```

### Benefits Over Current Approach

1. **No File System Access Needed**: Doesn't require finding .emlx files
2. **Works for All Account Types**: Exchange, IMAP, iCloud all work the same way
3. **Always Up-to-Date**: Gets content directly from Mail.app
4. **Simpler Code**: No complex path searching

### Limitations

1. **Requires Mail.app Running**: AppleScript needs Mail.app to be active
2. **Slower**: AppleScript calls are slower than file reads
3. **Permissions**: Requires Automation permissions
4. **Subject Matching**: May find wrong email if subject isn't unique

## Integration Recommendations

### Option 1: Use AppleScript Directly (Recommended)

Extract the AppleScript patterns and use them directly in `ui.py`:

```python
def get_email_content_via_applescript(subject: str, sender: str = None, account: str = None) -> Optional[str]:
    """Get email content using AppleScript (works for all account types)."""
    import subprocess
    
    script = f'''
    tell application "Mail"
        set foundMessage to missing value
        
        repeat with theAccount in accounts
            try
                repeat with theMailbox in mailboxes of theAccount
                    try
                        set matchingMessages to (messages of theMailbox whose subject contains "{subject[:50]}")
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
            return ""
        end if
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    return None
```

### Option 2: Use as MCP Server

If you want to use it as a full MCP server (for Claude Desktop integration):

1. Install the MCP server
2. Configure Claude Desktop to use it
3. Access email content through MCP tools

This is more complex but provides a full API.

## Does It Meet Your Requirements?

### ✅ Requirements Met

1. **Email Content/Preview**: Yes - can get full email body text
2. **All Account Types**: Yes - works for Exchange, IMAP, iCloud
3. **Reliable**: Yes - doesn't depend on file system structure
4. **No File Searching**: Yes - uses AppleScript instead

### ⚠️ Considerations

1. **Performance**: AppleScript is slower than file reads (but more reliable)
2. **Dependencies**: Requires Mail.app to be running
3. **Permissions**: Needs Automation permissions
4. **Subject Matching**: May need sender + date to uniquely identify emails

## Recommended Next Steps

1. **Integrate AppleScript Content Retrieval**: Update `ui.py` to use AppleScript for content extraction
2. **Add Caching**: Cache content to avoid repeated AppleScript calls
3. **Fallback Chain**: 
   - Try AppleScript first (most reliable)
   - Fall back to .emlx file parsing if AppleScript fails
   - Fall back to database preview if available

## Example Integration Code

See the updated `ui.py` which now includes AppleScript-based content extraction as a fallback when .emlx files aren't found.

## References

- [apple-mail-mcp GitHub Repository](https://github.com/patrickfreyer/apple-mail-mcp)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [AppleScript Mail.app Dictionary](https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/reference/ASLR_applications.html)

