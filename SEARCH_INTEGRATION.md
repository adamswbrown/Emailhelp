# AppleScript Email Search Integration

This document explains the new AppleScript-based email search functionality integrated into the CLI, based on best practices from the Apple Mail MCP server.

## Overview

The CLI now supports two methods for querying emails:

1. **Database Queries** (default) - Fast, but may be stale
2. **AppleScript Queries** (new) - Real-time, more reliable, directly from Mail.app

## Why AppleScript Search?

### Advantages

- **Real-time results**: Queries Mail.app directly, always up-to-date
- **More reliable**: Doesn't depend on database sync status
- **Better content extraction**: Gets full email content previews
- **Case-insensitive search**: Better search experience
- **Works with all mailboxes**: Can search across any folder

### When to Use

- When you need real-time, accurate results
- When searching by subject keyword
- When database queries are slow or incomplete
- When you need email content previews

## Usage

### Basic Search

```bash
# Search emails by subject keyword
python main.py --search "meeting"

# Search with account filter
python main.py --search "project" --account Exchange

# Search unread emails only
python main.py --search "urgent" --unread-only
```

### Advanced Search

```bash
# Search with sender filter
python main.py --search "invoice" --sender "accounting@company.com"

# Search in specific mailbox
python main.py --search "report" --mailbox Archive

# Combine filters
python main.py --search "meeting" --account Work --unread-only --limit 20
```

### Use AppleScript for All Queries

```bash
# Use AppleScript instead of database queries
python main.py --use-applescript --limit 50

# This provides real-time results even without --search
python main.py --use-applescript --account Exchange --unread-only
```

## Integration with Categorization

The AppleScript search seamlessly integrates with the existing categorization system:

```bash
# Search and categorize
python main.py --search "meeting" --category ACTION

# Search with scoring explanations
python main.py --search "project" --why

# Search and show only ACTION items
python main.py --search "urgent" --category ACTION --why
```

## How It Works

### Architecture

1. **`applescript_search.py`** - New module providing AppleScript-based search
   - `search_emails()` - Advanced search with multiple filters
   - `list_inbox_emails()` - Quick inbox listing
   - `get_accounts()` - Get account list via AppleScript

2. **CLI Integration** - New flags:
   - `--search KEYWORD` - Search by subject keyword
   - `--sender EMAIL` - Filter by sender
   - `--use-applescript` - Force AppleScript queries

3. **Automatic Fallback** - If AppleScript fails, falls back to database queries

### Search Process

1. User specifies `--search` or `--use-applescript`
2. CLI calls `applescript_search.search_emails()`
3. AppleScript queries Mail.app directly
4. Results are parsed and formatted
5. Emails are scored and categorized (same as database results)
6. Results displayed in ledger format

## Best Practices from MCP Server

### Case-Insensitive Search

The MCP server uses case-insensitive matching:
```applescript
on lowercase(str)
    set lowerStr to do shell script "echo " & quoted form of str & " | tr '[:upper:]' '[:lower:]'"
    return lowerStr
end lowercase
```

We've implemented the same approach for consistent behavior.

### Content Extraction

The MCP server extracts content previews:
- Cleans up line breaks and formatting
- Limits length for performance
- Handles errors gracefully

Our implementation follows the same pattern.

### Error Handling

- Graceful fallback to database queries
- Clear error messages
- Timeout protection (120 seconds)

### Mailbox Handling

- Handles both "INBOX" and "Inbox" variations
- Supports searching all mailboxes
- Account filtering support

## Examples

### Example 1: Find Meeting Requests

```bash
python main.py --search "meeting" --category ACTION --why
```

This will:
1. Search all emails with "meeting" in subject (case-insensitive)
2. Score and categorize them
3. Filter to ACTION items only
4. Show scoring explanations

### Example 2: Find Unread Urgent Emails

```bash
python main.py --search "urgent" --unread-only --account Work
```

### Example 3: Search and Open

```bash
python main.py --search "invoice" --open
```

This searches for invoices and lets you interactively select one to open.

### Example 4: Real-Time Inbox Check

```bash
python main.py --use-applescript --limit 20 --unread-only
```

Uses AppleScript for real-time unread email listing.

## Performance Considerations

### AppleScript Queries

- **Slower** than database queries (queries Mail.app directly)
- **More accurate** (always up-to-date)
- **Better for search** (case-insensitive, content-aware)

### Database Queries

- **Faster** (direct SQLite access)
- **May be stale** (depends on Mail.app sync)
- **Good for bulk operations** (listing many emails)

### Recommendation

- Use `--search` for keyword searches (always uses AppleScript)
- Use `--use-applescript` when you need real-time accuracy
- Use default (database) for fast bulk operations

## Troubleshooting

### "AppleScript execution failed"

- Make sure Mail.app is running
- Check that Mail.app has necessary permissions
- Try restarting Mail.app

### "No emails found"

- Verify account name matches exactly (case-sensitive)
- Check that emails exist in the specified mailbox
- Try without filters first

### "AppleScript execution timed out"

- Reduce `--limit` value
- Try searching a specific account instead of all accounts
- Check if Mail.app is responding

## Technical Details

### AppleScript Output Format

Emails are returned in delimited format:
```
|||account||mailbox||subject||sender||date||read||preview
```

This allows parsing multiple emails efficiently.

### Date Parsing

AppleScript returns dates in format:
```
"Monday, December 30, 2024 at 10:30:00 AM"
```

We parse this to Unix timestamp for compatibility with existing code.

### Content Preview

- Default length: 500 characters
- Automatically truncated with "..."
- Cleans up line breaks and formatting

## Future Enhancements

Potential improvements based on MCP server features:

1. **Date range filtering** - Search emails between dates
2. **Attachment filtering** - Find emails with/without attachments
3. **Thread search** - Search email threads
4. **Advanced sender matching** - Better sender filtering
5. **Multiple keyword search** - Search for multiple terms

## Summary

The AppleScript search integration brings real-time, reliable email search to the CLI, following best practices from the Apple Mail MCP server. It seamlessly integrates with the existing categorization system and provides a better search experience.

Use `--search` for keyword searches and `--use-applescript` when you need real-time accuracy!

