# 🚀 GOLD TIER - CHROME FIXED VERSION

## ✅ Fixes Applied

1. **Chrome Browser** - All watchers now use Chrome (not Firefox)
2. **Persistent Sessions** - Browsers stay open, don't close automatically
3. **Gold Tier Workflow** - Files now go to `gold/needs_action/` first
4. **HITL Process** - Manual approval required before execution

---

## 📁 CORRECT WORKFLOW (Gold Tier)

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: WATCHERS (Eyes)                                        │
│ - WhatsApp Watcher (Chrome)                                    │
│ - Gmail Watcher (API)                                          │
│ - LinkedIn Watcher (Chrome)                                    │
│                                                                 │
│ ↓ Create files in: gold/needs_action/                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: GOLD ORCHESTRATOR (Brain)                              │
│ - Reads files from gold/needs_action/                          │
│ - Calls Gemini API for AI analysis                             │
│ - Creates draft replies                                        │
│                                                                 │
│ ↓ Saves drafts to: gold/pending_approval/                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: HUMAN APPROVAL (HITL)                                  │
│ - YOU review drafts in gold/pending_approval/                  │
│ - YOU move files to: gold/pending_approval/approved/           │
│   (Drag & Drop or Cut & Paste)                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: ACTION DISPATCHER (Hands)                              │
│ - Detects files in gold/pending_approval/approved/             │
│ - Executes actions (send email, post LinkedIn, etc.)           │
│ - Has 3-stage retry logic for errors                           │
│                                                                 │
│ ↓ Moves completed to: gold/done/                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 BEFORE RUNNING

### 1. Install Chrome for Playwright
```bash
python -m playwright install chrome
```

### 2. Setup Credentials

**For Gmail:**
- Ensure `credentials.json` exists in project root
- First run will create `token.json`

**For Gemini API (Optional):**
```bash
setx GEMINI_API_KEY "your-api-key"
```

### 3. Install Dependencies
```bash
pip install playwright google-auth google-auth-oauthlib watchdog
```

---

## ▶️ HOW TO RUN

### Step 1: Run Start Script
```bash
.\start_gold_tier.bat
```

### Step 2: Browser Setup
5 windows will open:

1. **Gold Orchestrator** - AI Brain (no browser)
2. **Action Dispatcher** - Executor (no browser)
3. **WhatsApp Watcher** - Chrome window opens
   - ⚠️ **Scan QR code** if not logged in
   - ⚠️ **KEEP WINDOW OPEN** - Don't close!
4. **Gmail Watcher** - API based (no browser)
5. **LinkedIn Watcher** - Chrome window opens
   - ⚠️ **Login** if not already logged in
   - ⚠️ **KEEP WINDOW OPEN** - Don't close!

---

## 📂 FOLDER STRUCTURE

```
gold/
├── needs_action/          ← NEW files from watchers appear here
│   ├── WHATSAPP_*.md
│   ├── GMAIL_*.md
│   └── LINKEDIN_*.md
│
├── pending_approval/      ← AI drafts saved here
│   ├── DRAFT_*.md        ← Review these
│   └── approved/         ← Move files here to execute
│
├── done/                  ← Completed tasks
│   └── done_*.md
│
├── logs/                  ← All logs
│   ├── whatsapp_*.log
│   ├── gmail_*.log
│   ├── linkedin_*.log
│   ├── gold_orchestrator_*.log
│   └── action_dispatcher_*.log
│
└── plans/                 ← AI action plans
    └── PLAN_*.md
```

---

## ✅ SUCCESS INDICATORS

### You'll know it's working when:

1. ✅ **Chrome browsers stay open** (don't close automatically)
2. ✅ **New .md files appear in `gold/needs_action/`** when:
   - WhatsApp message with keywords received
   - Gmail email with keywords received
   - LinkedIn post with sales keywords found
3. ✅ **Drafts created in `gold/pending_approval/`** by Orchestrator
4. ✅ **After manual approval** → Files move to `gold/done/`

---

## 🔍 MONITORING

### Check Logs
```bash
# Open logs folder
explorer gold\logs

# Or view specific log
type gold\logs\whatsapp_*.log
```

### Check New Tasks
```bash
# See what's in needs_action
dir gold\needs_action
```

### Check Dashboard
```bash
type Dashboard.md
```

---

## 🛠️ TROUBLESHOOTING

### Browser Closes Immediately
**Fix:** Chrome might be crashing. Try:
```bash
# Reinstall Chrome for Playwright
python -m playwright install --force chrome
```

### No Files in needs_action/
**Check:**
1. Are browsers open and logged in?
2. Are you receiving messages with keywords?
3. Check logs: `gold\logs\whatsapp_*.log`

### Keywords Not Detected
**Monitored Keywords:**
```
urgent, sales, payment, invoice, deal, order,
client, customer, quotation, proposal, overdue,
follow up, meeting, booking, asap, test, hi,
hello, paid, receive, price, cost
```

### Gmail Not Working
**Fix:**
1. Ensure `credentials.json` exists
2. Delete `token.json` and re-authorize
3. Check logs: `gold\logs\gmail_*.log`

### Orchestrator Not Creating Drafts
**Check:**
1. Is `gold/needs_action/` getting files?
2. Check logs: `gold\logs\gold_orchestrator_*.log`
3. Set GEMINI_API_KEY for better AI responses

---

## 📝 MANUAL APPROVAL PROCESS

### To approve a task for execution:

1. **Review** draft in `gold/pending_approval/`
2. **Open** the .md file and check content
3. **Move** file to `gold/pending_approval/approved/`
   - Either drag & drop in File Explorer
   - Or cut (Ctrl+X) and paste (Ctrl+V)
4. **Wait** - Action Dispatcher will execute within 10 seconds
5. **Check** `gold/done/` for completed task

---

## 🎯 WHAT'S FIXED

| Issue | Before | After |
|-------|--------|-------|
| Browser | Firefox (crashes) | Chrome (stable) |
| Session | Closes immediately | Stays open persistently |
| Folder | Wrong folders | Correct gold/ hierarchy |
| Workflow | Direct to done | needs_action → approval → done |
| HITL | Missing | Manual approval required |

---

**Gold Tier is now ready! Run `.\start_gold_tier.bat` and monitor the logs!** 🚀
