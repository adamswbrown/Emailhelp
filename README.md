# Email Accounting & Categorization CLI

> **Treat email as records to be accounted for, not messages to be read.**

A local, deterministic command-line tool for email accounting and triage on macOS. Supports both **Apple Mail** and **Outlook for Mac**. Built specifically for users with multiple email accounts (personal + work) who need fast, explainable email classification without AI or external services.

## Quick Start

```bash
# List your 20 most recent emails
python3 main.py

# Discover your email accounts (Exchange, iCloud, etc.)
python3 main.py --list-accounts

# Show ACTION items from Exchange account only
# Note: Use "ews" if "Exchange" doesn't work (account filtering matches mailbox URLs)
python3 main.py --account ews --category ACTION

# Use Outlook instead of Apple Mail
python3 main.py --client outlook --limit 20

# Auto-detect email client (default)
python3 main.py --client auto

# Show scoring breakdown
python3 main.py --limit 10 --why

# Interactive email selection - choose which email to open
python3 main.py --limit 10 --open

# Open a specific email by index in Apple Mail (default)
python3 main.py --limit 10 --open 3

# Open email in Outlook instead
python3 main.py --limit 10 --open 3 --open-client outlook

# Extract email content and copy to clipboard
# Note: Use "ews" if "Exchange" doesn't work
python3 main.py --search "meeting" --account ews --extract-content --copy-content

# Copy content of first email from displayed results
python3 main.py --account ews --category ACTION --copy-index 1

# Analyze your email patterns (supports both Apple Mail and Outlook)
python3 analyze_emails.py --client apple-mail --since 30
python3 analyze_emails.py --client outlook --all

# Launch interactive TUI (Textual-based interface)
python3 main.py --ui

# Launch TUI with specific client/account
python3 main.py --ui --client apple-mail --account Exchange
```

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Command-Line Options](#command-line-options)
  - [Example Commands](#example-commands)
- [Expected Output](#expected-output)
- [Multiple Email Accounts Support](#multiple-email-accounts-support)
- [Scoring System (WSS)](#scoring-system-weighted-signal-scoring-wss)
- [Classification Rules](#classification-rules)
- [How It Works](#how-it-works-apple-mail-envelope-index)
- [Architecture](#architecture)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Overview

This CLI application reads email metadata from Apple Mail's Envelope Index or Outlook's SQLite database to perform fast, indexed email analysis. It scores emails using transparent weighted signals and classifies them into actionable categories. Supports both Apple Mail and Outlook for Mac.

### What it does

- ✅ **Read-only access** to email metadata (never modifies emails)
- ✅ **Supports both Apple Mail and Outlook for Mac**
- ✅ **Deterministic scoring** based on explicit, auditable signals
- ✅ **Multi-account support** (Exchange, iCloud, Gmail, etc.)
- ✅ **Fast queries** using SQLite indexes (thousands of emails in seconds)
- ✅ **Ledger-style output** for accounting-based email triage
- ✅ **Explainable results** with `--why` flag showing score breakdowns
- ✅ **Interactive email selection** with `--open` flag
- ✅ **Open emails in email client** directly from the command line
- ✅ **Zero dependencies** (uses Python standard library only)

### What it does NOT do

- ❌ Send emails or modify mailboxes
- ❌ Use AI/GPT or external services
- ❌ Run as background service or daemon
- ❌ Make network calls
- ❌ Parse full email bodies (only lightweight ~300 char previews)

### Key Benefits

1. **Multiple Account Support**: Perfect for users with personal + work email
2. **Transparent Scoring**: Every classification decision is explainable
3. **No Black Box**: No machine learning, no AI—just clear rules
4. **Privacy First**: 100% local processing, zero data leaves your machine
5. **Performance**: Direct SQLite access is 10-100x faster than AppleScript

---

## Requirements

- **macOS** (latest versions)
- **Apple Mail.app** OR **Outlook for Mac** installed and configured
- **Python 3.7+**
- No external dependencies (uses Python standard library only)

---

## Installation

1. Clone or download this repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Make the main script executable:
```bash
chmod +x main.py
```

3. Verify Python version:
```bash
python3 --version  # Should be 3.7 or higher
```

---

## Usage

### Basic Usage

List the 20 most recent emails:
```bash
python3 main.py
```

### Command-Line Options

```
--limit N              Maximum number of emails to display (default: 20)
--since DAYS          Only show emails from the last N days (default: 365)
--all                  Show all emails regardless of date
--unread-only         Only show unread emails
--mailbox NAME        Filter by mailbox name (e.g., "Inbox")
--account NAME        Filter by account name (e.g., "Exchange", "iCloud")
--list-accounts       List all available accounts and exit
--category CATEGORY   Filter by classification (ACTION, FYI, or IGNORE)
--client CLIENT       Email client: apple-mail, outlook, or auto (default: auto)
--open [INDEX]        Interactive email selection (--open) or open email at INDEX (--open INDEX)
--open-client CLIENT   Email client for --open: apple-mail or outlook (default: apple-mail)
--extract-content     Extract full email content (requires --search and --account)
--copy-content        Copy email content to clipboard (use with --extract-content)
--copy-index INDEX    Copy content of email at INDEX to clipboard (works with displayed results)
--output-raw          Output raw email content only (for piping to other apps)
--output-file PATH    Save email content to file (use with --extract-content)
--why                 Show signal breakdown and score explanation
--user-name NAME      Your name (to detect personal mentions in scoring)
--db-path PATH        Explicit path to email database (auto-detects if not provided)
```

### Example Commands

**Discover available accounts:**
```bash
python3 main.py --list-accounts
```

**Filter by Exchange account only:**
```bash
# Note: Use "ews" if "Exchange" doesn't work (account filtering matches mailbox URLs)
python3 main.py --account ews --limit 50
```

**Show ACTION items from Exchange account:**
```bash
# Note: Use "ews" if "Exchange" doesn't work
python3 main.py --account ews --category ACTION
```

**List 50 recent emails with explanations:**
```bash
python3 main.py --limit 50 --why
```

**Show only unread emails from last 7 days in Exchange:**
```bash
python3 main.py --unread-only --since 7 --account Exchange
```

**Filter by mailbox:**
```bash
python3 main.py --mailbox Inbox --limit 30
```

**Show only ACTION items:**
```bash
python3 main.py --category ACTION
```

**Show only IGNORE items (bulk/automated emails):**
```bash
python3 main.py --category IGNORE --limit 100
```

**Interactive email selection - choose which email to open:**
```bash
python3 main.py --limit 10 --open
```

**Open a specific email by index in Apple Mail:**
```bash
python3 main.py --limit 10 --open 3
```

**Open email in Outlook instead:**
```bash
python3 main.py --limit 10 --open 3 --open-client outlook
```

**Show all emails (no date filter):**
```bash
python3 main.py --all --limit 50
```

---

## Expected Output

### Standard Ledger View

When you run the basic command, you'll see a tabular ledger-style output:

```bash
python3 main.py --account Exchange --limit 10
```

**Output:**
```
Locating Apple Mail Envelope Index...
Querying messages (limit=10, account=Exchange)...
Found 10 messages.
Scoring and classifying...

DATE        | FROM               | SUBJECT                  | SCORE | CLASS   | MAILBOX
-------------------------------------------------------------------------------------------------
2025-01-10  | partner.com        | DMC vs Azure Migrate     | 72    | ACTION  | Exchange/Inbox
2025-01-10  | client.net         | Question about timeline? | 65    | ACTION  | Exchange/Inbox
2025-01-09  | team.internal      | RE: Project update       | 50    | FYI     | Exchange/Work
2025-01-09  | github.com         | Weekly digest            | 15    | IGNORE  | Exchange/Notifications
2025-01-08  | noreply.service    | Your subscription        | 8     | IGNORE  | Exchange/Inbox
2025-01-08  | colleague.com      | Can you review this?     | 70    | ACTION  | Exchange/Inbox
2025-01-07  | newsletter.co      | Monthly roundup          | 5     | IGNORE  | Exchange/Newsletters
2025-01-07  | boss.company       | Urgent: please advise    | 75    | ACTION  | Exchange/Inbox
2025-01-06  | support.vendor     | Ticket #12345 update     | 45    | FYI     | Exchange/Support
2025-01-06  | noreply.marketing  | Special offer inside     | 2     | IGNORE  | Exchange/Promotions

Summary:
  Total emails: 10
  ACTION:    4 ( 40.0%)
  FYI:       2 ( 20.0%)
  IGNORE:    4 ( 40.0%)
```

### Output with Signal Explanations (`--why`)

Use the `--why` flag to see exactly how each email was scored:

```bash
python3 main.py --account Exchange --category ACTION --limit 3 --why
```

**Output:**
```
Locating Apple Mail Envelope Index...
Querying messages (limit=3, account=Exchange, category after filtering)...
Found 15 messages.
Scoring and classifying...

DATE        | FROM               | SUBJECT                  | SCORE | CLASS   | MAILBOX
-------------------------------------------------------------------------------------------------
2025-01-10  | partner.com        | DMC vs Azure Migrate?    | 72    | ACTION  | Exchange/Inbox
  └─ Signals: direct_sender(+20), contains_question(+15), action_phrase(+20), trusted_domain(+10)

2025-01-09  | boss.company       | Urgent: please advise    | 75    | ACTION  | Exchange/Inbox
  └─ Signals: direct_sender(+20), action_phrase(+20), trusted_domain(+10)

2025-01-08  | colleague.com      | Can you review this?     | 70    | ACTION  | Exchange/Inbox
  └─ Signals: direct_sender(+20), trusted_domain(+10), contains_question(+15), action_phrase(+20), mentions_name(+15)

Summary:
  Total emails: 3
  ACTION:    3 (100.0%)
  FYI:       0 (  0.0%)
  IGNORE:    0 (  0.0%)
```

### List Accounts Output

```bash
python3 main.py --list-accounts
```

**Output:**
```
Locating Apple Mail Envelope Index...
Discovering accounts from mailbox paths...

Available accounts (3):
  - Exchange
  - iCloud
  - Gmail

Use --account <name> to filter by account.
Example: python main.py --account Exchange
```

**Important Note:** Account filtering matches mailbox URLs, not display names. If `--account Exchange` doesn't work, try:
- `--account ews` (for Exchange accounts - mailbox URLs use `ews://`)
- `--account imap` (for IMAP accounts)
- `--account pop` (for POP accounts)

Check the MAILBOX column in the output to see the actual URL pattern. For example, if you see `ews://494FB4...` in the mailbox column, use `--account ews` instead of `--account Exchange`.

### Understanding the Output Columns

| Column | Description | Example |
|--------|-------------|---------|
| **DATE** | Date email was received (UK format dd/mm/yyyy) | `17/03/2025` |
| **FROM** | Sender domain or address | `partner.com` |
| **SUBJECT** | Email subject (truncated to 35 chars) | `DMC vs Azure Migrate` |
| **SCORE** | Weighted signal score (0-100) | `72` |
| **CLASS** | Classification category | `ACTION`, `FYI`, or `IGNORE` |
| **MAILBOX** | Mailbox path (truncated to 15 chars) | `Exchange/Inbox` |

---

## Scoring System: Weighted Signal Scoring (WSS)

Emails are scored 0-100 using explicit, deterministic signals. All scoring is transparent and explainable.

### Sender Signals

| Signal | Points | Description |
|--------|--------|-------------|
| Direct sender | +20 | Email is from a real person (not noreply@) |
| Trusted domain | +10 | Sender domain is in trusted list (gmail.com, outlook.com, etc.) |
| Bulk sender | -30 | Sender matches bulk patterns (noreply, no-reply, automated, marketing, etc.) |

### Subject Signals

| Signal | Points | Description |
|--------|--------|-------------|
| Action required | +35 | Subject contains "ACTION REQUIRED", "action needed", etc. |
| Meeting/call request | +30 | Subject contains "availability", "schedule a call", "meeting request", etc. |
| Contains `?` | +15 | Subject contains a question (likely needs response) |
| Starts with `RE:` | +10 | Reply to existing conversation |
| General meeting mention | +15 | Subject mentions "meeting" or "call" (less specific) |
| Informational action required | -15 | "ACTION REQUIRED" but content indicates informational/license expiration |
| Newsletter/digest | -20 | Subject contains newsletter, digest, weekly update, etc. |

### Content Signals (from preview text)

| Signal | Points | Description |
|--------|--------|-------------|
| Action phrases | +20 | Contains "can you", "could you", "please advise", "urgent", "deadline", "call", "meeting", "approve", "review", etc. |
| Mentions your name | +15 | Body preview mentions your name (use `--user-name` flag) |
| Jira automated | -30 | Automated Jira follow-up emails ("following up on your recent support request", "will be closed automatically", etc.) |
| Informational notice | -15 | Contains license expiration, renewal notices, "will expire soon", "notification", etc. |
| Has unsubscribe | -40 | Contains unsubscribe link (strong bulk indicator) |

### Score Examples

```
Score 85 = Direct sender (+20) + Trusted domain (+10) + Question (+15) + 
           Action phrase (+20) + Mentions name (+15) + Reply (+10)
           → ACTION

Score 65 = Action required (+35) + Direct sender (+20) + Trusted domain (+10)
           → ACTION

Score 60 = Meeting request (+30) + Direct sender (+20) + Trusted domain (+10)
           → ACTION

Score 50 = Direct sender (+20) + Trusted domain (+10) + Reply (+10) + Meeting mention (+15)
           → FYI

Score 35 = Action required (+35) + Direct sender (+20) + Trusted domain (+10) + 
           Informational action required (-15) + Informational notice (-15)
           → FYI (license expiration notice, informational)

Score 10 = Bulk sender (-30) + Newsletter (-20) + Has unsubscribe (-40)
           → IGNORE
```

---

## Multiple Email Accounts Support

### Overview

**Perfect for users with multiple accounts** (personal iCloud + work Exchange + Gmail, etc.)

Apple Mail often manages multiple email accounts simultaneously. This tool provides first-class support for filtering and analyzing emails by specific accounts, so you can focus on your work email (Exchange) without noise from personal accounts.

### Discovering Your Accounts

First, see which accounts Apple Mail has configured:

```bash
python3 main.py --list-accounts
```

**Example output:**
```
Available accounts (3):
  - Exchange       ← Your work email
  - iCloud         ← Your personal Apple email
  - Gmail          ← Your personal Gmail

Use --account <name> to filter by account.
Example: python main.py --account Exchange
```

### How Account Filtering Works

Apple Mail stores mailbox paths that include the account name as the first part of the path:

**Mailbox path examples:**
- `Exchange/INBOX` → Account: **Exchange**
- `Exchange/Sent Messages` → Account: **Exchange**
- `iCloud/Archive` → Account: **iCloud**
- `Gmail/Important` → Account: **Gmail**

The tool extracts the account name from these paths and lets you filter accordingly.

### Common Use Cases

#### 1. Work Email Only (Exchange)

Focus exclusively on your work Exchange account:

```bash
# All Exchange emails
python3 main.py --account Exchange --limit 50

# Only ACTION items from Exchange
python3 main.py --account Exchange --category ACTION

# Unread Exchange emails from last 3 days
python3 main.py --account Exchange --unread-only --since 3
```

#### 2. Personal Email Only (iCloud/Gmail)

Check your personal account separately:

```bash
# Personal iCloud account
python3 main.py --account iCloud --limit 30

# Personal Gmail account
python3 main.py --account Gmail --unread-only
```

#### 3. Compare Accounts

See how many ACTION items you have per account:

```bash
# Work ACTION items
python3 main.py --account Exchange --category ACTION

# Personal ACTION items  
python3 main.py --account iCloud --category ACTION
```

#### 4. Combined Filters

Account filtering works with all other filters:

```bash
# Exchange INBOX only, unread, last 7 days, ACTION items
python3 main.py \
  --account Exchange \
  --mailbox INBOX \
  --unread-only \
  --since 7 \
  --category ACTION
```

### Important Notes

✅ **Account names are case-sensitive**: Use `Exchange` not `exchange`  
✅ **Use `--list-accounts` first**: See exact account names in your system  
✅ **Combine with other filters**: `--account` works with `--mailbox`, `--category`, etc.  
✅ **Pattern matching**: Account filter uses pattern matching on mailbox paths

### Workflow Recommendation

**Morning Email Triage Workflow:**

```bash
# 1. Check work ACTION items (high priority)
python3 main.py --account Exchange --category ACTION --limit 20

# 2. Review work FYI items (medium priority)
python3 main.py --account Exchange --category FYI --limit 20

# 3. Quick check of personal ACTION items
python3 main.py --account iCloud --category ACTION --limit 10

# 4. See what got filtered as IGNORE (optional)
python3 main.py --account Exchange --category IGNORE --limit 50
```

---

## Classification Rules

Emails are classified into three deterministic categories:

| Category | Score Range | Description | Action |
|----------|-------------|-------------|---------|
| **ACTION** | ≥ 60 | Requires immediate attention or response | Reply, handle, or delegate |
| **FYI** | 30-59 | Informational, may need review | Read later, archive if not relevant |
| **IGNORE** | < 30 | Bulk, automated, or low-priority | Archive or delete |

---

## How It Works: Email Database Access

### Supported Email Clients

The tool supports two email clients on macOS:

#### Apple Mail

Apple Mail maintains an internal SQLite database called **Envelope Index** that stores metadata for all messages:

**Location:**
```
~/Library/Mail/V10/MailData/Envelope Index
~/Library/Mail/V11/MailData/Envelope Index
```

The tool automatically discovers the most recent version.

#### Outlook for Mac

Outlook for Mac uses SQLite database format:

**Location:**
```
~/Library/Group Containers/UBF8T346G9.Office/Outlook/Outlook 15 Profiles/Main Profile/Data/Outlook.sqlite
```

### Auto-Detection

By default, the tool auto-detects which email client is available:
1. Tries Apple Mail first
2. Falls back to Outlook if Apple Mail is not found
3. Use `--client apple-mail` or `--client outlook` to force a specific client

**Note:** Apple Mail's database is typically more up-to-date than Outlook's local cache. Outlook may take time to sync recent emails to its local SQLite database.

### What Data Is Accessed

Both databases provide:
- Message ID
- Subject line
- Sender address
- Date received
- Mailbox/folder name
- Read/unread flag
- Preview text (Outlook) or path to .emlx file (Apple Mail)

### Read-Only Access

The tool uses SQLite's `mode=ro` (read-only) flag to ensure:
- No writes to the database
- No locks that could interfere with Apple Mail
- No risk of corruption

### Email Content Extraction

For better scoring accuracy, the tool extracts email content:
- **Apple Mail**: Reads `.emlx` files to extract body previews (~500 characters)
- **Outlook**: Uses `Message_Preview` field from the database
- Strips signatures and quoted replies
- Ignores attachments
- Fails gracefully if content is unavailable

### Opening Emails in Email Client

Use the `--open` flag to open emails directly in your email client:

- **Interactive selection**: `--open` (shows menu to choose)
- **Direct index**: `--open 3` (opens the 3rd email)
- **Choose client**: `--open-client outlook` (defaults to apple-mail)

The tool uses AppleScript to search for and open emails by subject line in the specified email client.

### Workflow Example: List, Select, and Copy Email Content

Here's a complete workflow example showing how to list categorized emails, select one, and copy its content to the clipboard:

**Step 1: List emails with categorization**
```bash
python3 main.py --account Exchange --limit 20 --category ACTION
```

This shows your ACTION items with scores and categories.

**Step 2: Copy email content by index**
```bash
# Copy the first email's content to clipboard
python3 main.py --account ews --category ACTION --copy-index 1
```

This will:
1. Use the already-displayed results
2. Extract full content of email at index 1
3. Copy it to your clipboard

**Alternative: Search and copy**
```bash
# First, note the subject line from the list above, then:
python3 main.py --search "Meeting Request" --account ews --extract-content --copy-content
```

This will:
1. Search for the email by subject keyword
2. Extract its full content
3. Copy it to your clipboard

**Complete workflow in one command:**
```bash
# List categorized emails, then extract and copy content
python3 main.py --account ews --limit 10 --category ACTION && \
python3 main.py --search "meeting" --account ews --extract-content --copy-content
```

**Alternative: Interactive selection workflow**
```bash
# 1. List and categorize emails
python3 main.py --account ews --limit 20 --category ACTION

# 2. Use interactive selection to find the email subject
python3 main.py --account ews --limit 20 --open

# 3. Copy content using the subject you found
python3 main.py --search "Subject from step 2" --account ews --extract-content --copy-content
```

**Output:**
```
Email content copied to clipboard: Meeting Request for Next Week
```

Now you can paste the email content (Cmd+V) into any application!

---

## Architecture

The tool is organized into simple, focused modules:

```
email_reader.py       - Unified interface for Apple Mail and Outlook
mail_index.py         - Apple Mail SQLite access and queries
outlook_index.py      - Outlook SQLite access and queries
preview.py            - .emlx body preview extraction
scoring.py            - Weighted signal scoring (WSS)
classifier.py         - Score-to-category mapping
cli.py                - Argparse and output formatting
main.py               - Application entry point
analyze_emails.py     - Email pattern analysis tool (supports both clients)
analyze_and_update.py - Automated rule updates based on analysis
open_email.py         - Open emails in email client (Apple Mail/Outlook)
email_selector.py     - Interactive email selection menu
applescript_search.py - AppleScript-based email search (real-time)
ui.py                 - Interactive TUI interface
```

No frameworks, no external dependencies—just clear, deterministic Python code.

---

## macOS Compatibility & Risks

### Known Risks

1. **Schema changes**: Apple Mail's database schema is undocumented and may change between macOS versions
   - **Mitigation**: Defensive queries that handle missing columns gracefully

2. **Database format**: SQLite format could theoretically change
   - **Mitigation**: SQLite is highly backward-compatible

3. **Path changes**: Envelope Index location could change in future macOS versions
   - **Mitigation**: Dynamic discovery of V* directories

4. **Permissions**: macOS may restrict access to Mail directory
   - **Mitigation**: Tool will fail with clear error message

### Tested Environments

- macOS Ventura (13.x)
- macOS Sonoma (14.x)
- macOS Sequoia (15.x)

### If the Tool Doesn't Work

1. **Check Apple Mail is installed and configured:**
   ```bash
   ls ~/Library/Mail/V*/MailData/
   ```

2. **Manually specify database path:**
   ```bash
   python3 main.py --db-path ~/Library/Mail/V10/MailData/Envelope\ Index
   ```

3. **Check for schema changes:**
   ```bash
   sqlite3 ~/Library/Mail/V*/MailData/Envelope\ Index ".schema"
   ```

---

## Design Philosophy

> **Email is treated as records to be accounted for, not messages to be read.**

This tool applies accounting principles to email management:
- **Ledger view**: Tabular display like a financial ledger
- **Categorization**: Similar to expense categories
- **Deterministic**: Same input always produces same output
- **Explainable**: Every decision can be audited with `--why`
- **Read-only**: Never modifies the source data

---

## Customization

### Analyzing Your Emails

Use the analysis script to understand your email patterns and get recommendations:

```bash
# Analyze Apple Mail emails from last 30 days
python3 analyze_emails.py --client apple-mail --since 30

# Analyze Outlook emails (all available)
python3 analyze_emails.py --client outlook --all

# Analyze specific account
python3 analyze_emails.py --client apple-mail --account "your@email.com" --since 30

# Automatically update rules based on analysis
python3 analyze_and_update.py --since 30
```

The analysis will:
- Identify common sender domains to add as trusted
- Suggest threshold adjustments if classification is unbalanced
- Show score distributions and patterns
- Provide recommendations for improvement

### Adding Trusted Domains

Edit `scoring.py` and add to `TRUSTED_DOMAINS`:

```python
TRUSTED_DOMAINS = [
    'gmail.com',
    'outlook.com',
    'altra.cloud',      # Work domain
    'microsoft.com',
    '2bcloud.io',
    'yourcompany.com',  # Add your company domain
    # ... more domains
]
```

Or use the analysis script to automatically identify and add common domains.

### Adjusting Classification Thresholds

Edit `classifier.py`:

```python
ACTION_THRESHOLD = 60  # Change to 70 for stricter ACTION classification
FYI_THRESHOLD = 30     # Change to 40 for stricter FYI classification
```

### Adding New Signals

Add signal logic to `scoring.py` in the `EmailScorer` class:

```python
# Example: Bonus points for specific sender
if 'vip@company.com' in sender_lower:
    signals['vip_sender'] = 30
    score += 30
```

### Understanding Informational Emails

The tool automatically detects informational emails (license expiration notices, renewal reminders, etc.) that have "ACTION REQUIRED" in the subject but are actually FYI. These are scored lower to classify them correctly:

- **Subject patterns**: "before your access", "will expire", "purchase a license"
- **Content patterns**: "license will expire", "complimentary access", "renewal plan"
- **Result**: Score reduced by -15 to -25 points, moving from ACTION to FYI range

This ensures that emails where you're CC'd or that are informational don't incorrectly trigger ACTION classification.

---

## Troubleshooting

### "Envelope Index not found"

**Problem:** Tool can't locate Apple Mail database

**Symptoms:**
```
Error: Envelope Index not found at: None
Make sure Apple Mail is installed and has been run at least once.
```

**Solutions:**

1. **Verify Apple Mail is installed and configured:**
   ```bash
   ls ~/Library/Mail/V*/MailData/
   ```
   You should see an "Envelope Index" file.

2. **Manually specify the database path:**
   ```bash
   # Find the exact path
   find ~/Library/Mail -name "Envelope Index" 2>/dev/null
   
   # Use explicit path
   python3 main.py --db-path ~/Library/Mail/V10/MailData/Envelope\ Index
   ```

3. **Check permissions:**
   ```bash
   ls -la ~/Library/Mail/
   ```
   Make sure you have read access to the Mail directory.

4. **Open Apple Mail at least once:**
   - Launch Apple Mail.app
   - Let it sync/load
   - Try the tool again

---

### "No messages found matching criteria"

**Problem:** Query returns no results

**Symptoms:**
```
Found 0 messages.
No messages found matching criteria.
```

**Solutions:**

1. **Remove filters and increase limit:**
   ```bash
   # Try with just a high limit
   python3 main.py --limit 100
   ```

2. **Check if specific filters are too restrictive:**
   ```bash
   # Remove account filter
   python3 main.py --limit 50
   
   # Remove unread filter
   python3 main.py --account Exchange --limit 50
   
   # Remove date filter
   python3 main.py --account Exchange --limit 50
   ```

3. **Verify account name is correct:**
   ```bash
   # List available accounts
   python3 main.py --list-accounts
   
   # Use exact account name (case-sensitive)
   python3 main.py --account Exchange  # not "exchange"
   ```

4. **Check if Apple Mail has any messages:**
   - Open Apple Mail.app
   - Verify messages are visible
   - Let Mail finish syncing

---

### Slow Performance

**Problem:** Tool takes a long time to run

**Symptoms:**
- Command hangs for 30+ seconds
- "Querying messages..." step is very slow

**Solutions:**

1. **Reduce limit:**
   ```bash
   # Instead of 1000, use 100
   python3 main.py --limit 100 --account Exchange
   ```

2. **Avoid `--why` flag for large queries:**
   ```bash
   # --why requires reading .emlx files (slower)
   # Without --why (fast)
   python3 main.py --limit 500 --account Exchange
   
   # With --why (slower, but more detailed)
   python3 main.py --limit 50 --account Exchange --why
   ```

3. **Use account and mailbox filters:**
   ```bash
   # Filter at SQL level (faster)
   python3 main.py --account Exchange --mailbox INBOX --limit 100
   ```

4. **Check Envelope Index size:**
   ```bash
   du -h ~/Library/Mail/V*/MailData/Envelope\ Index
   ```
   If it's > 500MB, queries may naturally be slower.

---

### "Permission denied" or "Operation not permitted"

**Problem:** macOS security is blocking access

**Symptoms:**
```
Error: [Errno 1] Operation not permitted
```

**Solutions:**

1. **Grant Terminal full disk access:**
   - Open **System Preferences** → **Privacy & Security** → **Full Disk Access**
   - Click the **+** button
   - Add **Terminal** (or your terminal app)
   - Restart Terminal

2. **Run from terminal app with proper permissions:**
   - Use Terminal.app (not a third-party terminal initially)
   - Try again

3. **Check file permissions explicitly:**
   ```bash
   ls -la ~/Library/Mail/V*/MailData/Envelope\ Index
   ```

---

### Incorrect or unexpected classifications

**Problem:** Emails are being classified wrong

**Example:** Important work email marked as IGNORE

**Solutions:**

1. **Use `--why` to see scoring breakdown:**
   ```bash
   python3 main.py --limit 20 --why --account Exchange
   ```
   Check which signals are firing.

2. **Customize thresholds** (see [Customization](#customization)):
   - Edit `classifier.py` to adjust ACTION/FYI/IGNORE thresholds
   - Default: ACTION ≥ 60, FYI 30-59, IGNORE < 30

3. **Add trusted domains** (see [Customization](#customization)):
   - Edit `scoring.py` to add your company domain
   - This gives +10 points to emails from trusted domains

4. **Add your name for personal mentions:**
   ```bash
   python3 main.py --user-name "YourName" --limit 20
   ```
   Emails mentioning your name get +15 points.

---

### Database locked or in use

**Problem:** SQLite database is locked

**Symptoms:**
```
Error: database is locked
```

**Solutions:**

1. **Close Apple Mail:**
   - Quit Apple Mail.app completely
   - Try the tool again

2. **Wait a moment:**
   - Apple Mail may be writing to the database
   - Wait 10-30 seconds and retry

3. **The tool uses read-only mode:**
   - This should prevent most locking issues
   - But if Mail is actively writing, brief locks can occur

---

### Missing columns or schema errors

**Problem:** Database schema doesn't match expected structure

**Symptoms:**
```
Warning: Query failed: no such column: account
```

**Solutions:**

1. **This is expected:** The tool handles missing columns gracefully
   - Warning messages are normal
   - Tool will work with available columns

2. **Check macOS/Mail version:**
   ```bash
   sw_vers  # Check macOS version
   ```
   Older versions may have different schemas.

3. **Inspect schema manually:**
   ```bash
   sqlite3 ~/Library/Mail/V*/MailData/Envelope\ Index ".schema messages"
   ```
   See what columns are actually available.

---

## Limitations

1. **macOS only**: Requires Apple Mail.app
2. **No IMAP queries**: Only reads local cache
3. **Schema dependent**: Relies on undocumented database structure
4. **English-centric**: Signal phrases are in English
5. **No learning**: Scoring rules are static (not machine learning)

---

## Contributing

This tool is designed to be simple and maintainable. Contributions should:
- Maintain deterministic behavior
- Avoid external dependencies
- Include clear inline comments
- Preserve read-only operation

---

## License

[Add your license here]

---

## FAQ

### General Questions

**Q: Will this tool modify my emails or mailboxes?**  
A: No. The tool opens the database in read-only mode (`mode=ro`) and never writes anything. It's 100% safe.

**Q: Does this send data to any servers?**  
A: No. All processing is 100% local. No network calls are made. Your email data never leaves your machine.

**Q: Why not use AppleScript?**  
A: AppleScript is 10-100x slower for bulk operations. Direct SQLite access to the Envelope Index is much faster and doesn't require Apple Mail to be running.

**Q: Can I use this with other email clients?**  
A: No, this is specifically designed for Apple Mail's database format. Other clients (Outlook, Thunderbird) use different storage systems.

**Q: Is this safe to run?**  
A: Yes. The tool only reads data and uses SQLite's read-only mode. However, as with any software, use at your own risk and always keep backups.

---

### Multi-Account Questions

**Q: I have personal iCloud and work Exchange. Can I filter by account?**  
A: Yes! This is a primary use case. Use:
```bash
python3 main.py --list-accounts          # See your accounts
python3 main.py --account ews            # Filter to Exchange (use "ews" not "Exchange")
python3 main.py --account iCloud         # Filter to iCloud
```

**Note:** If `--account Exchange` doesn't work, try `--account ews` - account filtering matches mailbox URLs which use `ews://` for Exchange accounts.

**Q: How does the tool know which account an email belongs to?**  
A: The tool filters by matching against mailbox URLs stored in the database. Exchange accounts use `ews://` URLs, IMAP uses `imap://`, etc. The `--account` filter searches for the account name within these URLs, so you may need to use the protocol prefix (e.g., `ews`) rather than the display name (e.g., `Exchange`).

**Q: My Exchange account shows up with a weird name. What do I do?**  
A: Account filtering matches mailbox URLs, not display names. If `--account Exchange` doesn't work:
1. Check the MAILBOX column in the output - look for the URL pattern (e.g., `ews://...`)
2. Use the URL protocol prefix instead: `--account ews` (for Exchange), `--account imap` (for IMAP), etc.
3. Example: If mailbox shows `ews://494FB4...`, use `--account ews` instead of `--account Exchange`

**Q: Can I filter multiple accounts at once?**  
A: Not directly, but you can run the tool twice:
```bash
python3 main.py --account Exchange --category ACTION
python3 main.py --account iCloud --category ACTION
```

---

### Scoring & Classification Questions

**Q: How accurate is the classification?**  
A: The scoring is deterministic and transparent. Accuracy depends on your email patterns. Use `--why` to see the scoring breakdown and adjust thresholds in `classifier.py` to tune for your needs.

**Q: Why did this important email get marked as IGNORE?**  
A: Use `--why` to see the signal breakdown:
```bash
python3 main.py --limit 100 --why | grep -A2 "important subject"
```
Common reasons:
- Sender is "noreply@" (-30 points)
- Subject contains "newsletter" (-20 points)  
- Body contains "unsubscribe" (-40 points)

You can customize scoring in `scoring.py` (see [Customization](#customization)).

**Q: Can I change the ACTION/FYI/IGNORE thresholds?**  
A: Yes! Edit `classifier.py`:
```python
ACTION_THRESHOLD = 60  # Change to 70 for stricter
FYI_THRESHOLD = 30     # Change to 40 for stricter
```

**Q: Why doesn't the tool use AI/machine learning?**  
A: By design. This tool prioritizes:
1. **Transparency** - You can see exactly why each email was scored
2. **Determinism** - Same email always gets same score
3. **Privacy** - No data sent to external services
4. **Control** - You can customize all the rules

---

### Technical Questions

**Q: What Python version do I need?**  
A: Python 3.7 or higher. Check with: `python3 --version`

**Q: Do I need to install any packages?**  
A: No. The tool uses only Python's standard library (sqlite3, email, argparse, etc.). No pip install needed.

**Q: Can I run this on Linux or Windows?**  
A: No. This is macOS-specific because it reads Apple Mail's proprietary database format.

**Q: Does Apple Mail need to be running?**  
A: No. The tool accesses the database directly. Apple Mail can be closed.

**Q: What if Apple changes the database schema?**  
A: The tool queries defensively and handles missing columns gracefully. It should continue working across schema changes, though specific features might break.

**Q: How fast is it?**  
A: Very fast. Querying 1000 emails typically takes < 1 second. Using `--why` (which reads .emlx files) is slower but still reasonable for ~50-100 emails.

**Q: Can I run this as a cron job?**  
A: Yes, but output is designed for terminal display. Consider redirecting output:
```bash
# Daily email report
0 9 * * * python3 /path/to/main.py --account Exchange --category ACTION --limit 20 > /tmp/email-report.txt
```

**Q: Where's the data stored?**  
A: The tool doesn't store any data. It reads directly from Apple Mail's Envelope Index at:
```
~/Library/Mail/V{VERSION}/MailData/Envelope Index
```

---

### Troubleshooting Questions

**Q: I get "Envelope Index not found" - what do I do?**  
A: See [Troubleshooting: "Envelope Index not found"](#envelope-index-not-found)

**Q: I get "Permission denied" - what do I do?**  
A: Grant Terminal full disk access in System Preferences → Privacy & Security → Full Disk Access. See [Troubleshooting: "Permission denied"](#permission-denied-or-operation-not-permitted)

**Q: The tool is very slow - how can I speed it up?**  
A: See [Troubleshooting: Slow Performance](#slow-performance)

**Q: No messages are showing up - what's wrong?**  
A: See [Troubleshooting: "No messages found matching criteria"](#no-messages-found-matching-criteria)

---

## Credits

Built with a focus on transparency, determinism, and explainability. No black boxes, no magic—just clear accounting principles applied to email management.
