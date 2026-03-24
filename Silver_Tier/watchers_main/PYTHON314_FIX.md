# WhatsApp and LinkedIn Watchers - Python 3.14 Fix
==================================================

## Problem
Python 3.14 has a compatibility issue with the `greenlet` library, which is required by Playwright.
The error message is:
```
DLL load failed while importing _greenlet: The specified module could not be found.
```

## Solution Options

### Option 1: Use Alternative Python Version (RECOMMENDED)

Create a virtual environment with Python 3.11 or 3.12:

```cmd
# Check available Python versions
py --list

# Create venv with Python 3.12 (if available)
py -3.12 -m venv venv_watchers

# Activate the virtual environment
venv_watchers\Scripts\activate

# Install dependencies
pip install playwright
playwright install chromium

# Run watchers
python watchers/whatsapp_watcher.py
python watchers/linkedin_watcher.py
```

### Option 2: Wait for Official Fix

Monitor these packages for Python 3.14 support:
- greenlet: https://pypi.org/project/greenlet/
- playwright: https://pypi.org/project/playwright/

Check for updates:
```cmd
pip install --upgrade greenlet playwright
```

### Option 3: Use Alternative Watchers (Current Workaround)

Since WhatsApp and LinkedIn watchers require Playwright, use these alternatives:

**For Email monitoring:** Use `gmail_watcher.py` (already working via PM2)

**For file-based integration:** Use `filesystem_watcher.py` (already working via PM2)
- Drop files in `/Inbox`
- Automatically processed to `/Needs_Action`

**For manual message logging:** Create files directly in `/Needs_Action`:
```markdown
---
type: whatsapp_message
from: Contact Name
subject: WhatsApp Message
received: 2026-02-27 10:00:00
priority: high
---

## Message Content

[Paste message content here]

---
*Manually logged*
```

### Option 4: Use Mobile App Integration (Future)

Consider using official APIs:
- WhatsApp Business API
- LinkedIn API

These don't require browser automation.

---

## Current Working Status

| Watcher | Status | Method |
|---------|--------|--------|
| filesystem_watcher | ✅ ONLINE | PM2 managed |
| gmail_watcher | ✅ ONLINE | PM2 managed |
| whatsapp_watcher | ⚠️ Manual only | Requires Python 3.11/3.12 |
| linkedin_watcher | ⚠️ Manual only | Requires Python 3.11/3.12 |

---

## Quick Commands

### Check PM2 Status
```cmd
pm2 status
```

### View Logs
```cmd
pm2 logs --lines 50
```

### Run with Alternative Python (if available)
```cmd
py -3.12 watchers/whatsapp_watcher.py
py -3.12 watchers/linkedin_watcher.py
```

---

## Technical Details

**Root Cause:**
- Python 3.14 changed internal C API
- greenlet's C extension needs recompilation
- Pre-built wheels not yet available for Python 3.14 on Windows

**Affected Packages:**
- greenlet < 3.4.0 (approximate)
- playwright (depends on greenlet)

**Tracking:**
- greenlet GitHub: https://github.com/python-greenlet/greenlet
- playwright GitHub: https://github.com/microsoft/playwright-python
