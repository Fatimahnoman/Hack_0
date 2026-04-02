# Watchers Setup Guide
========================================

## Current Status

| Watcher | Status | Method |
|---------|--------|--------|
| **filesystem_watcher** | ✅ **ONLINE** | PM2 managed |
| **gmail_watcher** | ✅ **ONLINE** | PM2 managed |
| **whatsapp_watcher_simple** | ✅ **ONLINE** | PM2 managed |

---

## Issue Summary

### ✅ RESOLVED: Gmail Watcher
- **Problem**: Missing `credentials.json` file
- **Solution**: Created `credentials.json` from client_secret file
- **Status**: Now running via PM2

### ⚠️ KNOWN: WhatsApp & LinkedIn Watchers
- **Problem**: Python 3.14 compatibility issue with greenlet DLL
- **Error**: `DLL load failed while importing _greenlet`
- **Status**: Cannot run via PM2, manual execution only with Python 3.11/3.12

---

## Fix 1: Gmail Watcher - ✅ RESOLVED

### Problem
Gmail watcher requires `credentials.json` but the file was named `client_secret_*.json`.

### Solution Applied
```cmd
copy client_secret_*.json credentials.json
```

### Current Status
✅ Running via PM2:
```
│ id │ name           │ status  │
├────┼────────────────┼─────────┤
│ 0  │ gmail_watcher  │ online  │
│ 1  │ filesystem_... │ online  │
```

### First-time Authorization (Required)
1. Run manually: `python watchers/gmail_watcher.py`
2. Browser will open for Google OAuth
3. Grant permissions
4. `token.json` will be created automatically
5. Stop with Ctrl+C
6. Restart via PM2: `pm2 restart gmail_watcher`

---

## Fix 2: WhatsApp & LinkedIn - Python 3.14 Issue

### Problem
Python 3.14 has compatibility issues with greenlet (required by Playwright).

**Error Message:**
```
[ERROR] Missing required dependency: DLL load failed while importing _greenlet
```

### Solution Options

**Option A: Use Python 3.11 or 3.12 (RECOMMENDED)**
```cmd
# Check available Python versions
py --list

# Create venv with Python 3.12 (if available)
py -3.12 -m venv venv_watchers
venv_watchers\Scripts\activate
pip install playwright
playwright install chromium

# Run watchers
python watchers/whatsapp_watcher.py
python watchers/linkedin_watcher.py
```

**Option B: Use file-based workaround**
Create files directly in `/Needs_Action`:
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
```

**Option C: Wait for greenlet/Playwright update**
```cmd
pip install --upgrade greenlet playwright
```

### Detailed Fix Guide
See: `watchers\PYTHON314_FIX.md`

---

## Quick Commands

### Check Status
```cmd
pm2 status
```

### View Logs
```cmd
pm2 logs --lines 50
pm2 logs gmail_watcher --lines 50
```

### Restart All PM2 Watchers
```cmd
pm2 restart all
```

### Start Specific Watcher
```cmd
pm2 start gmail_watcher
pm2 start filesystem_watcher
```

### Stop All
```cmd
pm2 stop all
```

### Run WhatsApp/LinkedIn Manually
```cmd
# Only works with Python 3.11/3.12
py -3.12 watchers/whatsapp_watcher.py
py -3.12 watchers/linkedin_watcher.py
```

---

## File Locations

| File | Purpose |
|------|---------|
| `watchers/filesystem_watcher.py` | Inbox folder monitoring |
| `watchers/gmail_watcher.py` | Gmail API monitoring |
| `watchers/whatsapp_watcher.py` | WhatsApp Web monitoring |
| `watchers/linkedin_watcher.py` | LinkedIn monitoring |
| `ecosystem.config.js` | PM2 configuration |
| `logs/pm2/` | PM2 log files |
| `credentials.json` | Gmail API credentials |
| `WATCHERS_SETUP.md` | This guide |
| `watchers/PYTHON314_FIX.md` | Python 3.14 fix details |

---

## Troubleshooting

### Gmail Watcher keeps stopping
1. Check if `credentials.json` exists in project root ✅
2. Run manually first to authorize: `python watchers/gmail_watcher.py`
3. Check logs: `pm2 logs gmail_watcher`

### WhatsApp/LinkedIn won't start
1. This is expected with Python 3.14
2. Use Python 3.11 or 3.12 instead
3. Or use file-based workaround
4. See `watchers\PYTHON314_FIX.md` for details

### PM2 errors
1. Delete and recreate: `pm2 delete all && pm2 start ecosystem.config.js`
2. Check logs: `pm2 logs --lines 100`
3. Check ecosystem config: `ecosystem.config.js`
