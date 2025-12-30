# macOS Apple Mail Accounting & Categorization CLI

> **Treat email as records to be accounted for, not messages to be read.**

A local, deterministic command-line tool for email accounting and triage on macOS. Built specifically for users with multiple email accounts (personal + work) who need fast, explainable email classification without AI or external services.

## Quick Start

```bash
# List your 20 most recent emails
python3 main.py

# Discover your email accounts (Exchange, iCloud, etc.)
python3 main.py --list-accounts

# Show ACTION items from Exchange account only
python3 main.py --account Exchange --category ACTION

# Show scoring breakdown
python3 main.py --limit 10 --why
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

This CLI application reads Apple Mail's internal SQLite database (Envelope Index) to perform fast, indexed email analysis. It scores emails using transparent weighted signals and classifies them into actionable categories.

### What it does

- ✅ **Read-only access** to Apple Mail metadata (never modifies emails)
- ✅ **Deterministic scoring** based on explicit, auditable signals
- ✅ **Multi-account support** (Exchange, iCloud, Gmail, etc.)
- ✅ **Fast queries** using SQLite indexes (thousands of emails in seconds)
- ✅ **Ledger-style output** for accounting-based email triage
- ✅ **Explainable results** with `--why` flag showing score breakdowns
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
- **Apple Mail.app** installed and configured
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
--since DAYS          Only show emails from the last N days
--unread-only         Only show unread emails
--mailbox NAME        Filter by mailbox name (e.g., "Inbox")
--account NAME        Filter by account name (e.g., "Exchange", "iCloud")
--list-accounts       List all available accounts and exit
--category CATEGORY   Filter by classification (ACTION, FYI, or IGNORE)
--why                 Show signal breakdown and score explanation
--user-name NAME      Your name (to detect personal mentions in scoring)
--db-path PATH        Explicit path to Envelope Index database
```

### Example Commands

**Discover available accounts:**
```bash
python3 main.py --list-accounts
```

**Filter by Exchange account only:**
```bash
python3 main.py --account Exchange --limit 50
```

**Show ACTION items from Exchange account:**
```bash
python3 main.py --account Exchange --category ACTION
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

### Understanding the Output Columns

| Column | Description | Example |
|--------|-------------|---------|
| **DATE** | Date email was received | `2025-01-10` |
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
| Contains `?` | +15 | Subject contains a question (likely needs response) |
| Starts with `RE:` | +10 | Reply to existing conversation |
| Newsletter/digest | -20 | Subject contains newsletter, digest, weekly update, etc. |

### Content Signals (from preview text)

| Signal | Points | Description |
|--------|--------|-------------|
| Action phrases | +20 | Contains "can you", "could you", "please advise", "urgent", etc. |
| Mentions your name | +15 | Body preview mentions your name (use `--user-name` flag) |
| Has unsubscribe | -40 | Contains unsubscribe link (strong bulk indicator) |

### Score Examples

```
Score 85 = Direct sender (+20) + Trusted domain (+10) + Question (+15) + 
           Action phrase (+20) + Mentions name (+15) + Reply (+10)
           → ACTION

Score 50 = Direct sender (+20) + Trusted domain (+10) + Reply (+10)
           → FYI

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

## How It Works: Apple Mail Envelope Index

### Data Source

Apple Mail maintains an internal SQLite database called **Envelope Index** that stores metadata for all messages:

**Typical location:**
```
~/Library/Mail/V10/MailData/Envelope Index
~/Library/Mail/V11/MailData/Envelope Index
```

The tool automatically discovers the most recent version.

### What Data Is Accessed

The Envelope Index contains:
- Message ID (ROWID)
- Subject line
- Sender address
- Date received
- Mailbox name
- Read/unread flag
- Path to .emlx file (for preview extraction)

### Read-Only Access

The tool uses SQLite's `mode=ro` (read-only) flag to ensure:
- No writes to the database
- No locks that could interfere with Apple Mail
- No risk of corruption

### .emlx Preview Extraction

For the `--why` flag, the tool may read `.emlx` files to extract body previews:
- Only reads first ~300 characters
- Strips signatures and quoted replies
- Ignores attachments
- Fails gracefully if file is missing

---

## Architecture

The tool is organized into simple, focused modules:

```
mail_index.py    - SQLite access and queries
preview.py       - .emlx body preview extraction
scoring.py       - Weighted signal scoring (WSS)
classifier.py    - Score-to-category mapping
cli.py           - Argparse and output formatting
main.py          - Application entry point
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

### Adding Trusted Domains

Edit `scoring.py` and add to `TRUSTED_DOMAINS`:

```python
TRUSTED_DOMAINS = [
    'gmail.com',
    'outlook.com',
    'yourcompany.com',  # Add your company domain
    # ... more domains
]
```

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
python3 main.py --account Exchange       # Filter to Exchange only
```

**Q: How does the tool know which account an email belongs to?**  
A: Apple Mail stores mailbox paths like "Exchange/INBOX" or "iCloud/Sent". The tool extracts the account name from the first part of the path.

**Q: My Exchange account shows up with a weird name. What do I do?**  
A: Use `--list-accounts` to see the exact account name, then use that exact string (case-sensitive) with `--account`.

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
