# Gold Tier Autonomous AI Employee - Implementation Guide

## ✅ Implementation Complete

All components have been implemented with the required fixes for Windows 11 stability.

---

## 📁 Gold Tier Folder Architecture

```
heckathon-0/
└── gold/
    ├── needs_action/          # Watchers drop raw task files (.md)
    ├── pending_approval/      # Orchestrator drops AI-generated drafts
    │   └── approved/          # Human moves files here to trigger execution
    ├── done/                  # Final storage for processed tasks
    ├── logs/                  # Unified logging for all components
    └── plans/                 # AI stores multi-step reasoning plans
```

---

## 🔧 Components Implemented

### 1. WhatsApp Watcher (`watchers/whatsapp_watcher_fixed.py`)

**Key Features:**
- ✅ Uses Firefox browser (stable for WhatsApp Web)
- ✅ Session lock management to prevent collisions
- ✅ "Check & Release" pattern for session sharing
- ✅ Keyword scanning for important messages
- ✅ Creates task files in `gold/needs_action/`

**Keywords Monitored:**
```
urgent, sales, payment, invoice, deal, order, client, customer,
quotation, proposal, overdue, follow up, meeting, booking, asap,
test, hi, hello, paid, receive, price, cost, quote, contract,
agreement, confirm, approval, budget
```

**Run:**
```bash
python watchers/whatsapp_watcher_fixed.py
```

---

### 2. Gold Orchestrator (`gold/tools/gold_orchestrator.py`)

**Key Features:**
- ✅ Gemini 1.5 Flash API integration
- ✅ Monitors `gold/needs_action/` folder
- ✅ Generates professional reply drafts
- ✅ Creates action plans in `gold/plans/`
- ✅ Moves drafts to `gold/pending_approval/`
- ✅ Human-in-the-Loop (HITL) workflow

**Environment Variable:**
```bash
setx GEMINI_API_KEY "your-api-key-here"
```

**Run:**
```bash
python gold/tools/gold_orchestrator.py
```

---

### 3. Action Dispatcher (`silver/tools/action_dispatcher.py`)

**Key Features:**
- ✅ Monitors `gold/pending_approval/approved/` folder
- ✅ 3-stage retry loop for session locked errors
- ✅ 10-second wait for lock release
- ✅ Executes: LinkedIn posts, Emails, WhatsApp messages
- ✅ Moves completed tasks to `gold/done/`

**Retry Logic:**
```
Stage 1: Try execution
Stage 2: If session locked → wait 10s → retry
Stage 3: Final retry after extended wait
```

**Run:**
```bash
# Daemon mode (continuous)
python silver/tools/action_dispatcher.py --daemon --interval 10

# Run once
python silver/tools/action_dispatcher.py --once
```

---

### 4. Start Script (`start_gold_tier.bat`)

**Key Features:**
- ✅ Creates Gold Tier folder structure
- ✅ Verifies dependencies
- ✅ Sets environment variables
- ✅ Launches all components in separate windows

**Run:**
```bash
start_gold_tier.bat
```

---

## 🔄 Complete Workflow

### Flow 1: WhatsApp Message → Reply Sent

```
1. WhatsApp Watcher detects message with keyword
   ↓
2. Creates file in gold/needs_action/
   Example: WHATSAPP_John_Doe_20260330_120000.md
   ↓
3. Gold Orchestrator reads file
   ↓
4. Calls Gemini API to analyze intent
   ↓
5. Creates draft in gold/pending_approval/
   Example: DRAFT_WHATSAPP_John_Doe_..._20260330_120001.md
   ↓
6. Human reviews draft
   ↓
7. Human moves file to gold/pending_approval/approved/
   ↓
8. Action Dispatcher detects approved file
   ↓
9. Executes WhatsApp sender with retry logic
   ↓
10. Moves to gold/done/ with done_ prefix
```

---

### Flow 2: Gmail → Email Reply

```
1. Gmail Watcher detects important email
   ↓
2. Creates file in gold/needs_action/
   ↓
3. Gold Orchestrator generates reply draft
   ↓
4. Draft saved to gold/pending_approval/
   ↓
5. Human reviews and approves (moves to approved/)
   ↓
6. Action Dispatcher sends via Gmail API
   ↓
7. Moves to gold/done/
```

---

### Flow 3: LinkedIn Post

```
1. Create draft or AI generates from sales lead
   ↓
2. Draft in gold/pending_approval/
   ↓
3. Human reviews and approves
   ↓
4. Action Dispatcher calls linkedin_auto_poster_fixed.py
   ↓
5. Post published to LinkedIn
   ↓
6. Moves to gold/done/
```

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
pip install watchdog google-generativeai google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client playwright
playwright install firefox
```

### Step 2: Set API Key (Optional)

```bash
setx GEMINI_API_KEY "your-gemini-api-key"
```

### Step 3: Run Start Script

```bash
start_gold_tier.bat
```

This opens 5 windows:
1. **Gold Orchestrator** - AI Brain
2. **Action Dispatcher** - Hands
3. **WhatsApp Watcher** - Eyes
4. **Gmail Watcher** - Eyes
5. **LinkedIn Auto Poster** - Hands

---

## 📊 Monitoring

### Check Logs

```bash
# All logs are in gold/logs/
type gold\logs\gold_orchestrator_*.log
type gold\logs\action_dispatcher_*.log
type gold\logs\whatsapp_watcher_*.log
```

### Check Dashboard

```bash
type Dashboard.md
```

### Check Folder Status

```bash
# Tasks waiting for AI processing
dir gold\needs_action

# Drafts awaiting human approval
dir gold\pending_approval

# Approved items ready for execution
dir gold\pending_approval\approved

# Completed tasks
dir gold\done
```

---

## 🔒 Session Lock Management

The system implements robust session lock management to prevent Watcher/Sender collisions:

### Lock File Location
```
session/whatsapp.lock
```

### Lock Behavior
- **Watcher:** Acquires lock before scanning, releases immediately after
- **Dispatcher:** Checks lock before sending, waits up to 30s if locked
- **Retry Logic:** 3 attempts with 10s delay between attempts

### Lock Timeout
- Locks older than 30 seconds are considered stale
- Stale locks are automatically ignored

---

## 🛠️ Troubleshooting

### WhatsApp Watcher Not Detecting Messages

1. **Check browser window** - Ensure WhatsApp Web is fully loaded
2. **Check QR code** - Scan QR code if logged out
3. **Check keywords** - Messages must contain monitored keywords
4. **Check logs** - `gold/logs/whatsapp_watcher_*.log`

### Orchestrator Not Creating Drafts

1. **Check Gemini API key** - Set `GEMINI_API_KEY` environment variable
2. **Check logs** - `gold/logs/gold_orchestrator_*.log`
3. **Fallback mode** - System uses heuristic fallback if AI fails

### Action Dispatcher Not Executing

1. **Check approved folder** - Files must be in `gold/pending_approval/approved/`
2. **Check session lock** - Wait for WhatsApp session to unlock
3. **Check logs** - `gold/logs/action_dispatcher_*.log`
4. **Check credentials** - Ensure Gmail OAuth is configured

### Browser Crashes (Exit Code 21)

**Fixed:** System now uses Firefox for WhatsApp Web (more stable on Windows)

```bash
# Reinstall Firefox for Playwright
python -m playwright install firefox
```

---

## 📝 File Format Examples

### WhatsApp Task File (gold/needs_action/)

```markdown
---
type: whatsapp_message
from: John Doe
message: Hi, I need urgent help with payment
priority: high
status: pending
created_at: 2026-03-30T12:00:00
source: whatsapp_web
---

## Message Content

Hi, I need urgent help with payment

## Metadata

- **Contact:** John Doe
- **Priority:** high
- **Received:** 2026-03-30 12:00:00
- **Source:** WhatsApp Web

---
*Imported by WhatsApp Watcher (Gold Tier)*
```

### Draft File (gold/pending_approval/)

```markdown
---
type: whatsapp_message
to: John Doe
subject: Re: Payment Assistance
priority: high
status: pending
---

## Content

Dear John,

Thank you for reaching out. I understand you need urgent assistance with payment.

I'm escalating this to our billing team immediately. They will contact you within 2 hours.

Best regards,
AI Employee Assistant

---
*Draft created by Gold Orchestrator*
```

### Done File (gold/done/)

```markdown
---
type: whatsapp_message
source: WHATSAPP_John_Doe_20260330_120000.md
processed_at: 2026-03-30T12:05:00
status: completed
---

# Completed

*Processed on 2026-03-30 12:05:00*

---
Original content preserved below:
---

[Original file content]
```

---

## ✅ Success Indicators

You'll know the system is working when:

1. ✅ New `.md` files appear in `gold/needs_action/` from watchers
2. ✅ Draft files appear in `gold/pending_approval/` with `DRAFT_` prefix
3. ✅ Moving files to `gold/pending_approval/approved/` triggers execution
4. ✅ Executed files appear in `gold/done/` with `done_` prefix
5. ✅ Logs are being written to `gold/logs/`
6. ✅ Dashboard.md shows recent activity

---

## 🎯 Key Improvements in This Implementation

| Issue | Fix |
|-------|-----|
| Browser Exit Code 21 | Uses Firefox instead of Chromium |
| Session Collisions | File-based lock with Check & Release |
| Folder Misalignment | Strict `gold/` hierarchy compliance |
| No Retry Logic | 3-stage retry with 10s delays |
| Missing AI Integration | Gemini 1.5 Flash API integration |
| No Session Management | Persistent session with lock file |

---

## 📞 Support

### Log Files
```
gold/logs/gold_orchestrator_YYYYMMDD.log
gold/logs/action_dispatcher_YYYYMMDD.log
gold/logs/whatsapp_watcher_YYYYMMDD.log
```

### Debug Screenshots
```
debug_whatsapp/    - WhatsApp Web screenshots
debug_linkedin/    - LinkedIn posting screenshots
```

---

**Gold Tier Autonomous AI Employee is now production-ready! 🚀**
