# 🥈 SILVER TIER - GMAIL WATCHER SETUP GUIDE

## 📊 Single Line Workflow

```
Gmail API → gmail_watcher.py → Bronze_Tier/Inbox/ → Ralph Wiggum Loop → Done/
```

---

## 🎯 WHAT IS SILVER TIER?

Silver Tier = **Gmail Integration** with AI Employee

- 📧 Monitors your Gmail inbox 24/7
- 🔍 Detects important emails (urgent, invoice, payment, sales)
- 📁 Automatically saves emails to `Bronze_Tier/Inbox/`
- 🤖 Integrates with Bronze Tier workflow

---

## 📁 SILVER TIER STRUCTURE (CLEANED)

```
Silver_Tier/
├── watchers/
│   └── gmail_watcher.py      ✅ ONLY WATCHER (WhatsApp removed)
├── Pending_Approval/
├── schedulers/
├── schedulers_main/
└── tools/

Root Files:
├── gmail_auth.py             ✅ OAuth authentication
├── ecosystem.config.js       ✅ PM2 config (updated)
├── run_gmail_watcher.bat     ✅ Quick start
└── credentials.json          ⚠️  YOU NEED TO ADD THIS
└── token.json                ⚠️  GENERATED AFTER AUTH
```

---

## 🚀 SETUP STEPS

### **STEP 1: Google Cloud Console Setup**

1. Go to: https://console.cloud.google.com/
2. Create new project (or select existing)
3. Enable **Gmail API**
4. Create **OAuth 2.0 Credentials**
   - Application type: **Desktop app**
   - Download `credentials.json`
5. Place `credentials.json` in:
   ```
   C:\Users\LENOVO\Desktop\Hack0\Ai_Employee\credentials.json
   ```

---

### **STEP 2: Authenticate with Gmail**

```powershell
cd C:\Users\LENOVO\Desktop\Hack0\Ai_Employee

# Run authentication
python gmail_auth.py
```

**Follow the prompts:**
1. Copy the authorization URL
2. Paste in browser
3. Sign in with Google account
4. Grant permissions
5. Copy authorization code
6. Paste in terminal

**Result:** `token.json` will be created

---

### **STEP 3: Test Gmail Watcher**

```powershell
# Option 1: Run directly
cd C:\Users\LENOVO\Desktop\Hack0\Ai_Employee
python Silver_Tier\watchers\gmail_watcher.py

# Option 2: Use batch file
.\run_gmail_watcher.bat

# Option 3: Run with PM2 (24/7)
pm2 start ecosystem.config.js --only gmail_watcher
```

---

## 📋 GMAIL WATCHER CONFIGURATION

### **Keywords Monitored:**
| Keyword | Priority | Action |
|---------|----------|--------|
| `urgent` | HIGH | Save to Inbox |
| `invoice` | MEDIUM | Save to Inbox |
| `payment` | MEDIUM | Save to Inbox |
| `sales` | NORMAL | Save to Inbox |

### **Check Interval:**
- **Default:** 120 seconds (2 minutes)
- **Configurable in:** `Silver_Tier/watchers/gmail_watcher.py`

```python
CHECK_INTERVAL = 120  # Change this value
```

---

## 🔄 COMPLETE WORKFLOW

```
┌─────────────────────────────────────────────────────────┐
│              SILVER TIER WORKFLOW                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. 📧 EMAIL AAYA (Gmail)                               │
│     Subject: "Urgent: Invoice Payment"                  │
│                                                          │
│  2. 🤖 GMAIL WATCHER (Every 2 minutes)                 │
│     - Checks unread emails                              │
│     - Scans for keywords                                │
│     - Downloads important emails                        │
│                                                          │
│  3. 📁 FILE CREATED (Bronze_Tier/Inbox/)               │
│     GMAIL_Urgent_Invoice_20260402_*.md                 │
│     Contains:                                           │
│     - YAML frontmatter (from, subject, priority)        │
│     - Email content                                     │
│     - Gmail message ID                                  │
│                                                          │
│  4. 🔄 BRONZE TIER PICKS UP                            │
│     - File Watcher → Needs_Action/                      │
│     - Ralph Wiggum Loop → Processes                     │
│     - Creates Plan → Plans/                             │
│     - Updates Dashboard → Dashboard.md                  │
│     - Moves to Done → Done/                             │
│                                                          │
│  ✅ COMPLETE!                                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 FILE FORMAT (GMAIL → .md)

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

[Full email body here]

---
*Imported by Gmail Watcher on 2026-04-02 10:05:00*
```

---

## 🚨 TROUBLESHOOTING

### **credentials.json not found**
```
ERROR: credentials.json not found at C:\...\credentials.json

SOLUTION:
1. Download from Google Cloud Console
2. Place in: C:\Users\LENOVO\Desktop\Hack0\Ai_Employee\
```

### **Token expired**
```powershell
# Delete old token
del token.json

# Re-authenticate
python gmail_auth.py
```

### **No emails appearing in Inbox**
```powershell
# Check Gmail watcher logs
pm2 logs gmail_watcher --lines 50

# Test manually
python Silver_Tier\watchers\gmail_watcher.py
```

### **Gmail API not enabled**
```
1. Go to: https://console.cloud.google.com/
2. Select your project
3. APIs & Services → Library
4. Search: "Gmail API"
5. Click ENABLE
```

---

## 🎯 QUICK START COMMANDS

### **Start Gmail Watcher**
```powershell
# Direct run
python Silver_Tier\watchers\gmail_watcher.py

# PM2 (24/7)
pm2 start ecosystem.config.js --only gmail_watcher

# Check status
pm2 status gmail_watcher
```

### **View Logs**
```powershell
# PM2 logs
pm2 logs gmail_watcher --lines 30

# Live logs
pm2 logs gmail_watcher --lines 100
```

### **Stop/Restart**
```powershell
# Stop
pm2 stop gmail_watcher

# Restart
pm2 restart gmail_watcher

# Delete
pm2 delete gmail_watcher
```

---

## ✅ SETUP CHECKLIST

- [ ] Google Cloud project created
- [ ] Gmail API enabled
- [ ] OAuth 2.0 credentials created
- [ ] `credentials.json` downloaded
- [ ] `credentials.json` placed in project root
- [ ] Authentication completed (`python gmail_auth.py`)
- [ ] `token.json` generated
- [ ] Gmail watcher tested
- [ ] PM2 process started (optional)

---

## 📊 PM2 STATUS

After setup, expected status:

```
┌────┬──────────────────────┬──────────┬──────┬───────────┐
│ id │ name                 │ status   │ cpu  │ memory    │
├────┼──────────────────────┼──────────┼──────┼───────────┤
│ 0  │ gmail_watcher        │ online   │ 0%   │ 54mb      │
│ 1  │ filesystem_watcher   │ online   │ 0%   │ 20mb      │
│ 2  │ workflow_processor   │ online   │ 0%   │ 16mb      │
│ 3  │ orchestrator_agent   │ online   │ 0%   │ 47mb      │
└────┴──────────────────────┴──────────┴──────┴───────────┘
```

**Note:** WhatsApp watcher removed from PM2 config!

---

## 🔒 SECURITY NOTES

- ✅ OAuth 2.0 authentication
- ✅ Token stored locally (`token.json`)
- ✅ Read-only Gmail access
- ✅ No third-party access
- ✅ Credentials never shared

**Scopes Used:**
- `https://www.googleapis.com/auth/gmail.readonly`

---

## 📧 TEST EMAIL

Send yourself a test email:

```
To: your-email@gmail.com
Subject: Urgent: Test Invoice
Body: This is a test email for Gmail watcher
```

Wait 2 minutes, then check:
```powershell
dir Bronze_Tier\Inbox\
```

---

## 🎉 SUMMARY

| Feature | Status |
|---------|--------|
| Gmail Integration | ✅ Ready |
| WhatsApp Integration | ❌ Removed |
| OAuth Authentication | ✅ Script ready |
| PM2 Configuration | ✅ Updated |
| Bronze Tier Integration | ✅ Connected |
| Ralph Wiggum Loop | ✅ Active |

**Silver Tier:** Gmail-only setup, fully integrated with Bronze Tier! 🎯

---

*Last Updated: 2026-04-02*
*Silver Tier - Gmail Watcher (WhatsApp Removed)*
