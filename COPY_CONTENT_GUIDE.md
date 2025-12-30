# Copy Content Functionality Guide

## How Copy Content Works

### Overview

The copy content feature extracts full email body text and copies it to your macOS clipboard, ready to paste into any application.

### Two Methods

#### Method 1: `--copy-index` (Recommended for Your Use Case)

Copy content by position in displayed results:

```bash
# Step 1: List emails
python3 main.py --account ews --category ACTION

# Step 2: Copy first email's content
python3 main.py --account ews --category ACTION --copy-index 1
```

**How it works:**
1. Displays categorized emails (same as normal query)
2. Extracts account name from mailbox URL or command-line argument
3. Maps account name (e.g., "EWS" → "Exchange") for AppleScript
4. Searches for the email by subject using AppleScript
5. Extracts full content (unlimited length)
6. Copies to clipboard using macOS `pbcopy`
7. Prints confirmation message

**Account Name Resolution:**
- Extracts from mailbox URL: `ews://...` → `ews` → `Exchange`
- Maps common protocols: `EWS`/`ews` → `Exchange`
- Uses command-line `--account` if provided
- Falls back to first available account if needed

#### Method 2: `--search --extract-content --copy-content`

Search and copy in one command:

```bash
python3 main.py --search "Availability for a call" --account ews --extract-content --copy-content
```

**How it works:**
1. Searches for emails matching subject keyword
2. Extracts full content of first matching email
3. Copies to clipboard
4. Prints confirmation

### Technical Implementation

**Content Extraction:**
- Uses AppleScript to query Mail.app directly
- Gets full email body text (unlimited length)
- Cleans HTML and normalizes formatting
- Returns plain text

**Clipboard Copy:**
- Uses macOS `pbcopy` command (built-in utility)
- Pipes content via stdin
- Handles UTF-8 encoding
- Works with any text content

**Account Name Mapping:**
```python
# Maps URL protocols and common names to AppleScript account names
account_map = {
    'EWS': 'Exchange',
    'ews': 'Exchange',
    'EXCHANGE': 'Exchange',
    'exchange': 'Exchange',
}
```

### Usage Examples

**Your Scenario:**
```bash
# List ACTION emails
python3 main.py --account ews --category ACTION

# Copy first email
python3 main.py --account ews --category ACTION --copy-index 1

# Copy second email
python3 main.py --account ews --category ACTION --copy-index 2
```

**With Different Accounts:**
```bash
# Works with any account
python3 main.py --account Exchange --category ACTION --copy-index 1
python3 main.py --account iCloud --category FYI --copy-index 1
python3 main.py --account Google --copy-index 1
```

### Troubleshooting

**Issue: "Error: Could not retrieve email content"**

**Possible causes:**
1. Account name mismatch - AppleScript needs display name ("Exchange"), not protocol ("ews")
2. Subject search too specific - Try using `--search` method instead
3. Mail.app not running - AppleScript requires Mail.app to be active
4. Permissions - May need Automation permissions

**Solutions:**
1. Use `--account Exchange` instead of `--account ews` (or let it auto-detect)
2. Try `--search` method: `python3 main.py --search "subject" --account Exchange --extract-content --copy-content`
3. Make sure Mail.app is running
4. Grant Automation permissions in System Preferences

**Issue: "Account not found"**

**Solution:**
- Check available accounts: `python3 main.py --list-accounts`
- Use the exact account name shown
- The code will auto-map "EWS"/"ews" to "Exchange" if available

### Performance Notes

- **AppleScript queries**: Slower than database (1-3 seconds for 20 emails)
- **Content extraction**: Adds ~1-2 seconds per email
- **Total time**: ~2-5 seconds for copy operation

This is acceptable because:
- You're copying one email at a time
- Accuracy is more important than speed here
- Content extraction requires AppleScript anyway

### What Gets Copied

- **Full email body text** (plain text, HTML stripped)
- **No metadata headers** (subject, sender, date are not included)
- **Ready to paste** - Just the email content

### After Copying

Once copied, you can:
- Paste with Cmd+V anywhere
- Paste into other applications
- Paste into AI tools (Claude, ChatGPT, etc.)
- Paste into text editors
- Use in scripts or workflows

### Best Practices

1. **Use `--copy-index`** when you've already listed emails
2. **Use `--search --copy-content`** when you know the subject
3. **Check account name** with `--list-accounts` if having issues
4. **Ensure Mail.app is running** for AppleScript to work
5. **Use exact account names** from `--list-accounts` output

