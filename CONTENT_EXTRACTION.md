# Email Content Extraction Guide

The CLI now supports extracting full email content as plain text, making it easy to pass email content to other applications.

## Quick Answer

**Yes!** You can now extract full email content as plain text and pass it to other applications.

## Features

- ✅ Extract full email content (not just previews)
- ✅ Output raw text for piping to other applications
- ✅ Save content to files
- ✅ Works with AppleScript search (real-time, reliable)

## Usage Examples

### Complete Workflow: List, Select, and Copy Email Content

**Step 1: List emails with categorization**
```bash
python3 main.py --account Exchange --limit 20 --category ACTION
```

This shows your ACTION items with scores and categories in a ledger format.

**Step 2: Select an email and copy its content to clipboard**
```bash
# Use the subject line from step 1 to search and copy
python3 main.py --search "Meeting Request" --account Exchange --extract-content --copy-content
```

This will:
1. Search for the email by subject keyword (case-insensitive)
2. Extract its full content
3. Copy it to your clipboard

**Output:**
```
Email content copied to clipboard: Meeting Request for Next Week
```

Now you can paste the email content (Cmd+V) into any application!

**Alternative: Interactive selection workflow**
```bash
# 1. List and categorize emails
python3 main.py --account Exchange --limit 20 --category ACTION

# 2. Use interactive selection to find the email subject
python3 main.py --account Exchange --limit 20 --open

# 3. Copy content using the subject you found
python3 main.py --search "Subject from step 2" --account Exchange --extract-content --copy-content
```

### 1. Extract Full Content

```bash
# Extract full content of matching email
python main.py --search "meeting" --account Exchange --extract-content
```

This will display the full email content with metadata headers.

### 2. Copy to Clipboard

```bash
# Extract content and copy to clipboard
python main.py --search "report" --account Work --extract-content --copy-content
```

Perfect for quickly copying email content to paste into other applications!

### 3. Output Raw Text (for Piping)

```bash
# Extract content and output raw text only (no formatting)
python main.py --search "report" --account Work --extract-content --output-raw
```

Perfect for piping to other applications:

```bash
# Pipe to grep
python main.py --search "invoice" --account Exchange --extract-content --output-raw | grep "amount"

# Pipe to another script
python main.py --search "data" --account Work --extract-content --output-raw | python process_email.py

# Pipe to file
python main.py --search "summary" --account Exchange --extract-content --output-raw > email.txt
```

### 4. Save to File

```bash
# Save content to a file
python main.py --search "meeting" --account Exchange --extract-content --output-file ~/email_content.txt

# If multiple emails match, saves each to separate file
python main.py --search "report" --account Work --extract-content --output-file ~/reports/report.txt
# Creates: report_1.txt, report_2.txt, etc.
```

### 4. Combine with Categorization

```bash
# Extract content from ACTION items only
python main.py --search "urgent" --account Exchange --extract-content --category ACTION
```

## Use Cases

### Pass to AI/LLM Applications

```bash
# Extract email content and pass to Claude/GPT
python main.py --search "proposal" --account Work --extract-content --output-raw | \
  python -c "import sys; content = sys.stdin.read(); print(f'Summarize this email: {content}')"
```

### Process with Python Scripts

```bash
# Extract and process with custom script
python main.py --search "invoice" --account Exchange --extract-content --output-raw | \
  python extract_amounts.py
```

### Save for Later Analysis

```bash
# Extract all meeting emails and save them
python main.py --search "meeting" --account Exchange --extract-content --output-file ~/meetings/meeting.txt
```

### Search and Extract Multiple Emails

```bash
# Extract up to 10 matching emails
python main.py --search "report" --account Work --extract-content --limit 10 --output-file ~/reports/report.txt
# Creates: report_1.txt, report_2.txt, ..., report_10.txt
```

## Output Formats

### With Metadata (default)

When using `--extract-content` without `--output-raw`:

```
Subject: Meeting Request
From: john@example.com
Date: Monday, December 30, 2024 at 10:30 AM
Account: Exchange

============================================================
CONTENT
============================================================

Hi there,

Can we schedule a meeting for next week?

Thanks,
John
```

### Raw Content Only

When using `--output-raw`:

```
Hi there,

Can we schedule a meeting for next week?

Thanks,
John
```

## Technical Details

### How It Works

1. Uses AppleScript to query Mail.app directly
2. Extracts full email content (unlimited length)
3. Cleans up formatting (removes HTML, normalizes whitespace)
4. Outputs as plain text

### Content Extraction

- **Full content**: Unlimited length (not truncated)
- **Plain text**: HTML stripped, formatting cleaned
- **Real-time**: Queries Mail.app directly (always up-to-date)

### Limitations

- Requires `--account` to be specified (for performance)
- Requires `--search` keyword (to identify specific email)
- AppleScript queries can be slower than database queries
- Content extraction requires Mail.app to be running

## Examples for Common Workflows

### Extract Latest Email from Sender

```bash
python main.py --search "" --sender "boss@company.com" --account Work --extract-content --limit 1 --output-raw
```

### Extract All Unread Emails

```bash
python main.py --search "" --account Exchange --unread-only --extract-content --output-file ~/unread/unread.txt
```

### Extract and Categorize

```bash
# Extract ACTION items and save them
python main.py --search "" --account Work --category ACTION --extract-content --output-file ~/action_items/action.txt
```

## Integration with Other Tools

### With `jq` (JSON processing)

```bash
# Extract content and format as JSON
python main.py --search "data" --account Work --extract-content --output-raw | \
  jq -Rs '{content: .}'
```

### With `grep` (text search)

```bash
# Extract content and search for keywords
python main.py --search "report" --account Exchange --extract-content --output-raw | \
  grep -i "deadline\|urgent\|important"
```

### With `wc` (word count)

```bash
# Count words in email
python main.py --search "proposal" --account Work --extract-content --output-raw | wc -w
```

### With Custom Python Scripts

```python
#!/usr/bin/env python3
import sys
import re

# Read email content from stdin
content = sys.stdin.read()

# Extract email addresses
emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
print("Found emails:", emails)

# Extract URLs
urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
print("Found URLs:", urls)
```

Usage:
```bash
python main.py --search "email" --account Work --extract-content --output-raw | python extract_info.py
```

## Summary

✅ **Yes, you can extract full email content as plain text**

✅ **Easy to pass to other applications** with `--output-raw`

✅ **Save to files** with `--output-file`

✅ **Works seamlessly** with existing categorization features

The content extraction feature makes it easy to integrate email content into your workflows, whether you're processing with scripts, analyzing with AI tools, or saving for later review.

