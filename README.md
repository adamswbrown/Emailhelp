# macOS Apple Mail Accounting & Categorization CLI

A local, deterministic command-line tool for email accounting and triage on macOS. This tool treats emails as records to be accounted for, not messages to be read.

## Overview

This CLI application reads Apple Mail's internal SQLite database (Envelope Index) to perform fast, indexed email analysis. It scores emails using transparent weighted signals and classifies them into actionable categories without using AI, external APIs, or modifying any data.

**What it does:**
- ✅ Read-only access to Apple Mail metadata
- ✅ Deterministic scoring based on explicit signals
- ✅ Classify emails as ACTION / FYI / IGNORE
- ✅ Display results in ledger-style accounting format
- ✅ Explainable behavior with `--why` flag

**What it does NOT do:**
- ❌ Send emails or modify mailboxes
- ❌ Use AI/GPT or external services
- ❌ Run as background service
- ❌ Make network calls
- ❌ Parse full email bodies (only lightweight previews)

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

### Standard Output (Ledger View)

```
Locating Apple Mail Envelope Index...
Querying messages (limit=20)...
Found 20 messages.
Scoring and classifying...

DATE        | FROM               | SUBJECT                  | SCORE | CLASS   | MAILBOX
-------------------------------------------------------------------------------------------------
2025-01-10  | partner.com        | DMC vs Azure Migrate     | 72    | ACTION  | Inbox
2025-01-10  | client.net         | Question about timeline? | 65    | ACTION  | Inbox
2025-01-09  | team.internal      | RE: Project update       | 50    | FYI     | Work
2025-01-09  | github.com         | Weekly digest            | 15    | IGNORE  | Notifications
2025-01-08  | noreply.service    | Your subscription        | 8     | IGNORE  | Inbox
2025-01-08  | colleague.com      | Can you review this?     | 70    | ACTION  | Inbox
2025-01-07  | newsletter.co      | Monthly roundup          | 5     | IGNORE  | Newsletters
2025-01-07  | boss.company       | Urgent: please advise    | 75    | ACTION  | Inbox
2025-01-06  | support.vendor     | Ticket #12345 update     | 45    | FYI     | Support
2025-01-06  | noreply.marketing  | Special offer inside     | 2     | IGNORE  | Promotions

Summary:
  Total emails: 10
  ACTION:    4 ( 40.0%)
  FYI:       2 ( 20.0%)
  IGNORE:    4 ( 40.0%)
```

### Output with Signal Explanations (`--why`)

When you use the `--why` flag, each email includes its signal breakdown:

```
DATE        | FROM               | SUBJECT                  | SCORE | CLASS   | MAILBOX
-------------------------------------------------------------------------------------------------
2025-01-10  | partner.com        | DMC vs Azure Migrate?    | 72    | ACTION  | Inbox
  └─ Signals: direct_sender(+20), trusted_domain(+10), contains_question(+15), action_phrase(+20)

2025-01-09  | noreply.service    | Weekly digest            | 12    | IGNORE  | Inbox
  └─ Signals: bulk_sender(-30), newsletter_subject(-20), has_unsubscribe(-40)

2025-01-08  | colleague.com      | Can you review this?     | 70    | ACTION  | Inbox
  └─ Signals: direct_sender(+20), trusted_domain(+10), contains_question(+15), action_phrase(+20), mentions_name(+15)
```

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

If you have multiple email accounts configured in Apple Mail (e.g., personal iCloud, work Exchange, Gmail), you can filter by specific accounts using the `--account` flag.

### Discovering Your Accounts

First, discover which accounts are available:

```bash
python3 main.py --list-accounts
```

**Example output:**
```
Available accounts (3):
  - Exchange
  - iCloud
  - Gmail

Use --account <name> to filter by account.
Example: python main.py --account Exchange
```

### How Account Filtering Works

Apple Mail stores mailbox paths that typically include the account name. For example:
- `Exchange/INBOX`
- `iCloud/Sent`
- `Gmail/Archive`

The tool extracts account names from these paths and allows you to filter messages accordingly.

### Use Cases

**Work Email Only (Exchange):**
```bash
# Focus only on your Exchange work emails
python3 main.py --account Exchange --category ACTION --limit 50
```

**Personal Email Only (iCloud):**
```bash
# Check your personal iCloud account
python3 main.py --account iCloud --unread-only
```

**Combine with Other Filters:**
```bash
# Unread ACTION items from Exchange in the last 3 days
python3 main.py --account Exchange --unread-only --since 3 --category ACTION
```

### Important Notes

- Account filtering uses pattern matching on mailbox paths
- If your Exchange account has a specific name, use that (e.g., "work@company.com")
- Use `--list-accounts` first to see the exact account names in your system
- You can combine `--account` with `--mailbox` for even more specific filtering

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

**Problem**: Tool can't locate Apple Mail database

**Solutions**:
- Ensure Apple Mail has been run at least once
- Manually specify path with `--db-path`
- Check permissions: `ls -la ~/Library/Mail/`

### "No messages found"

**Problem**: Query returns no results

**Solutions**:
- Try increasing `--limit`
- Remove filters (--unread-only, --mailbox, --category)
- Check if Mail has any messages

### Slow Performance

**Problem**: Tool takes a long time to run

**Solutions**:
- Reduce `--limit` value
- Avoid `--why` flag for large queries (requires .emlx parsing)
- Use `--mailbox` to filter specific mailboxes

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

**Q: Will this tool modify my emails or mailboxes?**  
A: No. The tool opens the database in read-only mode and never writes anything.

**Q: Does this send data to any servers?**  
A: No. All processing is 100% local. No network calls are made.

**Q: Why not use AppleScript?**  
A: AppleScript is slow for bulk operations. Direct SQLite access is much faster.

**Q: Can I use this with other email clients?**  
A: No, this is specifically designed for Apple Mail's database format.

**Q: How accurate is the classification?**  
A: The scoring is deterministic and transparent. Accuracy depends on your email patterns. Adjust thresholds in `classifier.py` to tune for your needs.

**Q: Is this safe to run?**  
A: Yes. The tool only reads data and uses SQLite's read-only mode. However, use at your own risk and always keep backups.

---

## Credits

Built with a focus on transparency, determinism, and explainability. No black boxes, no magic—just clear accounting principles applied to email management.
