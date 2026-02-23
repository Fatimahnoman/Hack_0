# Silver Tier AI Employee

Automated workflow system with Gmail, WhatsApp, and Instagram watchers that manage tasks through an intelligent approval pipeline.

---

## 📁 Project Structure

```
Silver_Tier/
├── watchers/
│   ├── gmail_watcher.py       # Monitor Gmail for unread+important emails
│   ├── whatsapp_watcher.py    # Monitor WhatsApp Web for keyword messages
│   └── instagram_watcher.py   # Monitor Instagram for notifications
├── Vault/
│   ├── Needs_Action/          # New tasks (0-2 minutes old)
│   ├── Pending_Approval/      # Tasks waiting for your action (2+ min)
│   ├── Approved/              # Tasks marked [APPROVED]
│   ├── Done/                  # Tasks marked [DONE]
│   └── Logs/                  # Application logs
├── skills/
│   ├── auto_insta_post.py     # Auto-post to Instagram
│   └── process_needs_action.py # Process pending tasks
├── mcp_servers/               # MCP server integrations
├── sessions/                  # Browser sessions (WhatsApp, Instagram)
├── orchestrator.py            # Main runner - handles all watchers + workflow
├── workflow_manager.py        # Auto-move files between workflow stages
├── test_silver_tier.py        # Test script
├── credentials.json           # Google OAuth credentials
└── .env                       # Environment variables
```

---

## 🚀 Quick Start

### **Option 1: Run Everything (Recommended)**

```bash
cd E:\Hackathon_Zero\Silver_Tier
python orchestrator.py
```

This starts:
- ✅ Gmail Watcher
- ✅ WhatsApp Watcher
- ✅ Instagram Watcher
- ✅ Workflow Manager (auto-moves files every 60 seconds)
- ✅ Dashboard Updater

---

### **Option 2: Run Individual Watchers**

| Watcher | Command |
|---------|---------|
| Gmail Only | `python watchers/gmail_watcher.py` |
| WhatsApp Only | `python watchers/whatsapp_watcher.py` |
| Instagram Only | `python watchers/instagram_watcher.py` |
| Workflow Manager Only | `python workflow_manager.py` |

> ⚠️ **Note:** Running individual watchers won't auto-move files. Use `orchestrator.py` or run `workflow_manager.py` separately for full workflow automation.

---

### **Option 3: Hybrid Setup**

**Terminal 1:** Run Gmail watcher
```bash
python watchers/gmail_watcher.py
```

**Terminal 2:** Run Workflow Manager
```bash
python workflow_manager.py
```

---

## 🔄 Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    WORKFLOW START                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. WATCHER DETECTS (Gmail/WhatsApp/Instagram)                   │
│    - Gmail: Unread + Important emails                           │
│    - WhatsApp: Messages with keywords (urgent, invoice, etc.)   │
│    - Instagram: New notifications                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. CREATE .MD FILE IN Vault/Needs_Action/                       │
│    Filename: EMAIL_{id}.md / WHATSAPP_{contact}_{time}.md       │
│    Content: Sender, Subject, Message, Priority, Actions         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. MARK AS READ                                                 │
│    - Gmail: Email marked as read                                │
│    - WhatsApp: Message tracked as processed                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. WAIT 2 MINUTES (120 seconds)                                 │
│    - Workflow Manager checks every 60 seconds                   │
│    - Calculates file age from creation time                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. AUTO-MOVE TO Vault/Pending_Approval/                         │
│    - File automatically moved by Workflow Manager               │
│    - Log: "✓ Moved to Pending: FILENAME.md"                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. ADD MARKER (Manual - You do this)                            │
│    Open the .md file and add ONE of these markers:              │
│    - [APPROVED]  → File moves to Approved/                      │
│    - [DONE]      → File moves to Done/                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. FINAL MOVE (Automatic)                                       │
│    - Next workflow check (within 60 sec) moves the file         │
│    - Workflow complete!                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Workflow Stages

| Stage | Location | Duration | Action |
|-------|----------|----------|--------|
| **1. New Task** | `Vault/Needs_Action/` | 0-2 min | Wait for auto-move |
| **2. Pending** | `Vault/Pending_Approval/` | Until you act | Add `[APPROVED]` or `[DONE]` |
| **3a. Approved** | `Vault/Approved/` | Final | Task approved |
| **3b. Done** | `Vault/Done/` | Final | Task completed |

---

## 📝 File Format Example

**File:** `Vault/Needs_Action/EMAIL_19c8caa2f5632afc.md`

```markdown
# Gmail Email Alert

**From:** client@example.com
**Subject:** Urgent: Project Deadline
**Received:** Mon, 24 Feb 2026 10:30:00 +0500
**Platform:** Gmail
**Priority:** HIGH

---

## Email Content

Hi, this is urgent. Please submit the project ASAP...

---

## Actions Required

- [ ] Review email
- [ ] Respond if needed
- [ ] Add [APPROVED] marker to move to Approved
- [ ] Add [DONE] marker to move to Done

---

## Workflow

- Current: Needs_Action
- After 2 min: Auto-move to Pending_Approval
- Add [APPROVED] marker: Move to Approved
- Add [DONE] marker: Move to Done

---

## Status

Needs_Action
```

---

## ✅ Adding Markers

### To Approve a Task:
Open the `.md` file and add anywhere:
```
[APPROVED]
```

### To Mark as Done:
Open the `.md` file and add anywhere:
```
[DONE]
```

The Workflow Manager will automatically move the file within 60 seconds.

---

## ⚙️ Configuration

### Gmail Watcher (`watchers/gmail_watcher.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `CHECK_INTERVAL` | 300 sec | Check emails every 5 minutes |
| `SCOPES` | gmail.readonly, gmail.send, gmail.modify | OAuth permissions |

### WhatsApp Watcher (`watchers/whatsapp_watcher.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `CHECK_INTERVAL` | 60 sec | Check messages every 1 minute |
| `KEYWORDS` | invoice, payment, urgent, asap, help, price, quote, hello, hi, hey | Trigger words |

### Workflow Manager (`workflow_manager.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `CHECK_INTERVAL` | 60 sec | Check workflow every 1 minute |
| `PENDING_DELAY` | 120 sec | Wait 2 minutes before moving to Pending |

### Orchestrator (`orchestrator.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `GMAIL_CHECK_INTERVAL` | 300 sec | Gmail check frequency |
| `WHATSAPP_CHECK_INTERVAL` | 60 sec | WhatsApp check frequency |
| `INSTAGRAM_CHECK_INTERVAL` | 14400 sec | Instagram check every 4 hours |
| `WORKFLOW_CHECK_INTERVAL` | 60 sec | Workflow manager frequency |

---

## 🔧 Setup Requirements

### 1. Install Dependencies

```bash
pip install google-auth google-auth-oauthlib google-api-python-client
pip install playwright
playwright install chromium
pip install apscheduler
```

### 2. Setup Google OAuth (for Gmail)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download `credentials.json`
6. Place in `Silver_Tier/credentials.json`

### 3. First-Time Login

When you run any watcher for the first time:
- Browser will open automatically
- Sign in with your Google account
- Grant permissions
- Token saved to `token.json` (auto-generated)

---

## 📋 Scheduled Tasks (via Orchestrator)

| Task | Schedule | Description |
|------|----------|-------------|
| **Gmail Check** | Every 5 min | Check for new unread+important emails |
| **WhatsApp Check** | Every 1 min | Check for keyword messages |
| **Instagram Check** | Every 4 hours | Check for notifications |
| **Workflow Manager** | Every 1 min | Auto-move files between stages |
| **Daily Instagram Post** | 9:00 AM UTC | Auto-generate and post |
| **Dashboard Update** | Every 5 min | Update status dashboard |

---

## 🛠️ Troubleshooting

### Issue: "Insufficient Permission" Error

**Solution:** Delete `token.json` and re-run:
```bash
del token.json
python watchers/gmail_watcher.py
```

### Issue: Files not moving to Pending_Approval

**Solution:** Ensure Workflow Manager is running:
```bash
python workflow_manager.py
# Or use orchestrator
python orchestrator.py
```

### Issue: WhatsApp QR Code not showing

**Solution:** 
1. Delete session folder: `del /s sessions\whatsapp_session`
2. Re-run WhatsApp watcher
3. Scan QR code within 60 seconds

### Issue: Browser won't open

**Solution:** Install Playwright browsers:
```bash
playwright install chromium
```

---

## 📊 Logs

All logs are saved to `Vault/Logs/`:

| Log File | Description |
|----------|-------------|
| `gmail_watcher.log` | Gmail watcher activity |
| `whatsapp_watcher.log` | WhatsApp watcher activity |
| `instagram_watcher.log` | Instagram watcher activity |
| `workflow_manager.log` | File movement logs |
| `orchestrator.log` | Main orchestrator logs |

---

## 🎯 Quick Commands Reference

```bash
# Run everything (BEST)
python orchestrator.py

# Run specific watcher
python watchers/gmail_watcher.py
python watchers/whatsapp_watcher.py
python watchers/instagram_watcher.py

# Run workflow manager only
python workflow_manager.py

# Test installation
python test_silver_tier.py
```

---

## 📞 Support

For issues or questions:
1. Check logs in `Vault/Logs/`
2. Review this README
3. Check individual watcher scripts for detailed comments

---

*Generated by Silver Tier AI Employee - Hackathon Zero*
