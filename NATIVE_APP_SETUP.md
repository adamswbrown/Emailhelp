# Native macOS Email Triage App - Setup Instructions

## Overview

This native macOS application provides a desktop interface for email triage with reply functionality, GPT integration, and auto-refresh capabilities.

## Requirements

- **macOS** 10.13 (High Sierra) or later
- **Python 3.7+**
- **PyWebView** for native window
- Apple Mail or Outlook for Mac configured

## Installation

### 1. Install PyWebView

```bash
pip3 install pywebview
```

### 2. Verify Installation

```bash
python3 -c "import webview; print('PyWebView installed successfully')"
```

## Running the App

### Basic Usage

```bash
# Auto-detect email client (tries Apple Mail, then Outlook)
python3 main_app.py

# Specify email client explicitly
python3 main_app.py --client apple-mail
python3 main_app.py --client outlook

# Specify default account
python3 main_app.py --account Exchange
```

### What Happens

1. **Native window opens** - Not a browser, looks like a real Mac app
2. **Emails load** - From your Mail.app or Outlook database
3. **Auto-categorization** - ACTION/FYI/IGNORE based on scoring
4. **Auto-refresh** - Checks for new emails every 3 minutes

## Features

### 1. Email Triage

- **View categorized emails** in a clean dashboard
- **ACTION** (red) - Needs immediate attention
- **FYI** (yellow) - Informational, review later
- **IGNORE** (gray) - Bulk/automated, can skip

### 2. Reply Functionality

Click "Reply" on any email to:
- **Compose in-app** using the reply editor
- **Use quick templates** (Will Review, Need More Info, etc.)
- **Send directly** via Mail.app/Outlook (background)
- **Edit in Mail.app** to add attachments, formatting, etc.

### 3. GPT Integration

Two GPT workflows:

**Copy to GPT (Analysis):**
```
1. Click "Copy to GPT" on any email
2. Context copied to clipboard with signals
3. Paste into ChatGPT
4. Get analysis, summary, or advice
```

**Draft with GPT:**
```
1. Click "Draft with GPT" on any email
2. Prompt copied asking GPT to draft reply
3. Paste into ChatGPT
4. Copy GPT's draft back
5. Paste into reply box, edit, send
```

### 4. Mark as Done

- Click "Mark Done" to hide from ACTION list
- Helps track what you've handled
- Persists across app restarts

### 5. Auto-Refresh

- Automatically checks for new emails every 3 minutes
- Toggle on/off in header
- Manual refresh button available

## Reply Workflow

### Option A: Send Directly (Fastest)

```
1. Click "Reply" on email
2. Type response or use template
3. Click "Send Now"
4. Email sent via Mail.app in background
5. Email marked as done automatically
```

### Option B: Edit in Mail.app (More Control)

```
1. Click "Reply" on email
2. Type draft in app
3. Click "Edit in Mail.app"
4. Mail.app opens with reply window
5. Add formatting, attachments, etc.
6. Send from Mail.app
```

### Option C: GPT-Assisted (Best Quality)

```
1. Click "Reply" on email
2. Click "Draft with GPT"
3. Paste into ChatGPT
4. Copy GPT's draft
5. Paste back into reply box
6. Edit as needed
7. Click "Send Now" or "Edit in Mail.app"
```

## Quick Reply Templates

Pre-loaded templates available:
- **Will Review** - "Thanks, I'll review and get back to you shortly"
- **Need More Info** - Asks for additional details
- **Following Up** - Check on previous request
- **Thanks** - Simple acknowledgment
- **Schedule Meeting** - Propose scheduling a call
- **Acknowledged** - Confirm receipt

Click any template to insert text, then customize.

## Keyboard Shortcuts

- **⌘R** - Refresh emails (future)
- **Esc** - Close reply modal
- **⌘Enter** - Send reply (when modal open) (future)

## Troubleshooting

### App won't start

**Error: "pywebview not found"**
```bash
pip3 install pywebview
```

**Error: "Email database not found"**
- Ensure Mail.app or Outlook is installed
- Open Mail.app/Outlook at least once
- Try specifying client: `--client apple-mail` or `--client outlook`

### Can't send replies

**Mail.app:**
- Ensure Mail.app is configured with account
- Check System Preferences → Privacy → Automation
- Grant Terminal (or Python) permission to control Mail

**Outlook:**
- Outlook has limited AppleScript support
- "Edit in Mail.app" opens compose window
- You may need to send manually from Outlook

### Emails not refreshing

- Click "Refresh" button manually
- Check auto-refresh is enabled (checkbox in header)
- Restart app
- Check Mail.app/Outlook is syncing

### GPT copy not working

- Clipboard access requires macOS permissions
- Try copying manually (⌘C)
- Check System Preferences → Privacy → Accessibility

## Architecture

```
main_app.py           - Native app entry point (PyWebView)
reply_handler.py      - AppleScript reply integration
actions/
  ├── gpt_export.py   - Format emails for ChatGPT
  └── mark_done.py    - Track completed emails
ui/
  ├── dashboard.html  - Main interface
  ├── style.css       - Native macOS styling
  └── app.js          - JavaScript interactions
```

## Why PyWebView?

- ✅ **Native window** - Looks like a real Mac app
- ✅ **Uses existing code** - All Python backend works unchanged
- ✅ **Fast development** - HTML/CSS/JS for UI
- ✅ **No Electron** - Lighter weight, no Node.js needed
- ✅ **Python-native** - Easy to integrate with existing tools

## Comparison with CLI

| Feature | CLI | Native App |
|---------|-----|------------|
| View emails | Terminal table | Rich UI with cards |
| Reply | Opens Mail.app | Compose in-app + send |
| GPT integration | Copy to clipboard | One-click export |
| Auto-refresh | Manual run | Every 3 minutes |
| Mark done | Not available | Yes, persists |
| Templates | Not available | 6 quick templates |
| Filter categories | --category flag | Click badges |

## Future Enhancements

Potential additions:
- [ ] Notifications for new ACTION emails
- [ ] Keyboard shortcuts
- [ ] Search/filter by sender
- [ ] Email threads/conversations
- [ ] Attachment preview
- [ ] Dark mode
- [ ] Menu bar app mode
- [ ] Package as .app bundle (double-click to run)

## Packaging as .app (Optional)

To create a double-clickable Mac app:

```bash
# Install py2app
pip3 install py2app

# Create setup file
python3 setup.py py2app

# Generates dist/EmailTriage.app
# Users can drag to Applications folder
```

## Support

For issues:
1. Check this README
2. Run `python3 main_app.py` in Terminal to see errors
3. Verify Mail.app/Outlook is working
4. Check database permissions

## License

[Your license here]
