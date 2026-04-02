# 🥈 SILVER TIER - GMAIL + WHATSAPP WATCHERS

## 📊 Single Line Workflow

```
Gmail/WhatsApp → watchers → Bronze_Tier/Inbox or Needs_Action → Ralph Wiggum Loop → Done/
```

---

## 🎯 OVERVIEW

Silver Tier provides **Gmail and WhatsApp integration** for the AI Employee project.

**What's Included:**
- ✅ Gmail Watcher (monitors inbox 24/7)
- ✅ WhatsApp Watcher (Playwright automation)
- ✅ WhatsApp Simple (file-based alternative)
- ✅ OAuth 2.0 Authentication (Gmail)
- ✅ Keyword-based filtering
- ✅ Automatic file creation in Bronze_Tier/Needs_Action
- ✅ Integration with Ralph Wiggum Loop

**Watchers:**
| Watcher | Type | Python Version | Destination |
|---------|------|----------------|-------------|
| `gmail_watcher.py` | Gmail API | Any | Bronze_Tier/Inbox |
| `whatsapp_watcher.py` | WhatsApp Web (Playwright) | 3.11/3.12 | Bronze_Tier/Needs_Action |
| `whatsapp_watcher_simple.py` | WhatsApp (file-based) | Any | Bronze_Tier/Needs_Action |

---

## 📁 STRUCTURE

```
Silver_Tier/
├── watchers/
│   ├── gmail_watcher.py           ✅ Gmail watcher
│   ├── whatsapp_watcher.py        ✅ WhatsApp (Playwright)
│   └── whatsapp_watcher_simple.py ✅ WhatsApp (Simple)
├── schedulers/                    ✅ Scheduled tasks
├── tools/                         ✅ Utility tools
└── sessions/                      ✅ WhatsApp session storage
```

**Note:** All watchers use **Bronze_Tier vault at root level** (Inbox/, Needs_Action/, Plans/, Done/)

---

## 🚀 QUICK START

### **Gmail Watcher Setup:**

```powershell
# STEP 1: Add credentials.json to project root
# Download from: https://console.cloud.google.com/

# STEP 2: Authenticate
cd C:\Users\LENOVO\Desktop\Hack0\Ai_Employee
python gmail_auth.py

# STEP 3: Run Gmail Watcher
python Silver_Tier\watchers\gmail_watcher.py

# OR use PM2 for 24/7 monitoring
pm2 start ecosystem.config.js --only gmail_watcher
```

### **WhatsApp Watcher Setup:**

```powershell
# Install Playwright (Python 3.11/3.12 required)
pip install playwright
playwright install chromium

# Run WhatsApp Watcher
py -3.11 Silver_Tier\watchers\whatsapp_watcher.py

# OR Simple version (any Python)
python Silver_Tier\watchers\whatsapp_watcher_simple.py
```

---

## 📋 CONFIGURATION

### **Keywords Monitored:**
| Keyword | Priority |
|---------|----------|
| `urgent` | HIGH |
| `invoice` | MEDIUM |
| `payment` | MEDIUM |
| `sales` | NORMAL |

### **Check Interval:**
- Gmail: **120 seconds** (2 minutes)
- WhatsApp: **5-30 seconds** (configurable)

---

## 🔄 WORKFLOW INTEGRATION

```
┌──────────────────────────────────────────────────────┐
│  SILVER TIER → BRONZE TIER INTEGRATION               │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Gmail API                                           │
│     ↓                                                │
│  gmail_watcher.py                                    │
│     ↓                                                │
│  Bronze_Tier/Inbox/                                  │
│     ↓                                                │
│  File System Watcher (Bronze)                        │
│     ↓                                                │
│  Needs_Action/                                       │
│     ↓                                                │
│  Ralph Wiggum Loop (Claude Code)                     │
│     ↓                                                │
│  Plans/ + Dashboard.md + Done/                       │
│                                                       │
│  ─────────────────────────────────────────────────  │
│                                                       │
│  WhatsApp Web                                        │
│     ↓                                                │
│  whatsapp_watcher.py                                 │
│     ↓                                                │
│  Bronze_Tier/Needs_Action/  ← DIRECT SAVE           │
│     ↓                                                │
│  Ralph Wiggum Loop (Claude Code)                     │
│     ↓                                                │
│  Plans/ + Dashboard.md + Done/                       │
│                                                       │
└──────────────────────────────────────────────────────┘
```

---

## 📝 FILES CREATED

### **Gmail Watcher Creates:**
```markdown
---
type: email
from: Client Name <client@example.com>
subject: Urgent: Invoice Payment
received: 2026-04-02 10:00:00
priority: high
status: pending
gmail_id: 19d1d36d583f90ee
---

## Email Content

[Full email body]

---
*Imported by Gmail Watcher on 2026-04-02 10:05:00*
```

### **WhatsApp Watcher Creates:**
```markdown
---
type: whatsapp_message
contact: Contact Name
received: 2026-04-02 10:00:00
priority: high
status: pending
keywords: urgent, payment
---

## Message Content

[WhatsApp message]

---
*Ready for Ralph Wiggum Loop processing*
```

---

## 🛠️ COMMANDS

### **Run Watchers:**
```powershell
# Gmail Watcher
python Silver_Tier\watchers\gmail_watcher.py

# WhatsApp Watcher (Playwright - requires Python 3.11/3.12)
py -3.11 Silver_Tier\watchers\whatsapp_watcher.py

# WhatsApp Simple (any Python)
python Silver_Tier\watchers\whatsapp_watcher_simple.py

# PM2 (24/7)
pm2 start ecosystem.config.js
```

### **View Logs:**
```powershell
# PM2 logs
pm2 logs gmail_watcher --lines 30
pm2 logs whatsapp_watcher --lines 30

# Check folders
dir Bronze_Tier\Inbox\
dir Bronze_Tier\Needs_Action\
```

### **Authentication:**
```powershell
# Re-authenticate Gmail
del token.json
python gmail_auth.py
```

---

## 🚨 TROUBLESHOOTING

### **credentials.json not found**
```
ERROR: credentials.json not found

SOLUTION:
1. Download from Google Cloud Console
2. Place in: C:\Users\LENOVO\Desktop\Hack0\Ai_Employee\credentials.json
```

### **Token expired**
```powershell
del token.json
python gmail_auth.py
```

### **WhatsApp not detecting messages**
```
1. Make sure Python 3.11 or 3.12 is installed
2. Check browser window - WhatsApp Web should be loaded
3. Verify session is saved in Silver_Tier/sessions/
4. Check logs: type logs\whatsapp_watcher.log
```

---

## ✅ SETUP CHECKLIST

### **Gmail:**
- [ ] Google Cloud project created
- [ ] Gmail API enabled
- [ ] OAuth 2.0 credentials (Desktop app)
- [ ] `credentials.json` in project root
- [ ] `python gmail_auth.py` completed
- [ ] `token.json` generated

### **WhatsApp:**
- [ ] Python 3.11 or 3.12 installed
- [ ] `pip install playwright`
- [ ] `playwright install chromium`
- [ ] QR code scanned (first time)
- [ ] Session saved in Silver_Tier/sessions/

---

## 📊 PM2 STATUS

Expected processes after setup:

```
┌────┬──────────────────────┬──────────┐
│ id │ name                 │ status   │
├────┼──────────────────────┼──────────┤
│ 0  │ gmail_watcher        │ online   │
│ 1  │ filesystem_watcher   │ online   │
│ 2  │ workflow_processor   │ online   │
│ 3  │ orchestrator_agent   │ online   │
└────┴──────────────────────┴──────────┘
```

**Note:** WhatsApp watcher runs manually (not in PM2) due to browser automation requirements

---

## 🔒 SECURITY

- ✅ OAuth 2.0 authentication (Gmail)
- ✅ Local token storage
- ✅ Read-only Gmail access
- ✅ Session persistence (WhatsApp)
- ✅ No third-party sharing

**Scopes:**
- Gmail: `https://www.googleapis.com/auth/gmail.readonly`

---

## 📚 DOCUMENTATION

- `GMAIL_SETUP_GUIDE.md` - Complete Gmail setup
- `../gmail_auth.py` - Authentication script
- `../ecosystem.config.js` - PM2 configuration
- `../Bronze_Tier/` - Vault folders (Inbox, Needs_Action, Plans, Done)

---

*Last Updated: 2026-04-02*
*Silver Tier - Gmail + WhatsApp Watchers*
*Using Bronze_Tier Vault at Root Level*
