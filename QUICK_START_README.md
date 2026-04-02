# AI Employee - Quick Start Guide (FIXED)

## 🚀 Quick Start (3 Steps)

### Step 1: Start All Components
```batch
start_fixed_ai_employee.bat
```

This will start 5 windows:
1. **Gmail Watcher** (Green) - Monitors Gmail inbox
2. **WhatsApp Watcher** (Cyan) - Monitors WhatsApp Web
3. **LinkedIn Watcher** (Red) - Monitors LinkedIn
4. **Gold Orchestrator** (Yellow) - Creates drafts
5. **Action Dispatcher** (Purple) - Executes approved actions

### Step 2: Login to Accounts
- **Gmail**: Login when browser opens
- **WhatsApp**: Scan QR code (first time only)
- **LinkedIn**: Login if needed

### Step 3: Test the Workflow
```batch
test_workflow.bat
```

This will:
1. Create test file in Needs_Action
2. Gold Orchestrator creates draft in Pending_Approval
3. Move draft to Approved
4. Action Dispatcher executes and moves to Done

---

## 📋 Complete Workflow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌──────────┐     ┌──────┐
│  WATCHERS   │────▶│ Needs_Action │────▶│ Pending_Approval │────▶│ Approved │────▶│ Done │
│  (Eyes)     │     │              │     │  (Drafts)        │     │          │     │      │
└─────────────┘     └──────────────┘     └──────────────────┘     └──────────┘     └──────┘
                                                                 │
                                                                 │ Manual Step
                                                                 ▼
                                                          You move files from
                                                          Pending_Approval to
                                                          Pending_Approval/Approved
```

### Detailed Steps:

1. **Watchers Monitor** (24/7):
   - Gmail → Checks for unread emails
   - WhatsApp → Checks for new messages
   - LinkedIn → Checks notifications/messages
   - **Only messages with KEYWORDS are processed**

2. **Keywords Filter**:
   - urgent, sales, payment, invoice, deal, order
   - client, customer, quotation, proposal, overdue
   - follow up, meeting, booking, asap

3. **Needs_Action Folder**:
   - Watchers create `.md` files here
   - Only for messages with keywords

4. **Gold Orchestrator** (The Brain):
   - Watches Needs_Action folder
   - Calls Claude AI to generate reply draft
   - Creates `DRAFT_*.md` in Pending_Approval
   - Moves original file to Done

5. **Human Review** (YOU):
   - Open `Pending_Approval/DRAFT_*.md`
   - Review the AI-generated reply
   - If approved, move file to `Pending_Approval/Approved/`

6. **Action Dispatcher** (The Hands):
   - Watches Approved folder
   - Executes the action (posts to LinkedIn, sends email, etc.)
   - Moves completed file to Done

---

## 📁 Folder Structure

```
heckathon-0/
├── Needs_Action/          ← Watchers create files here
├── Pending_Approval/      ← AI creates drafts here
│   ├── DRAFT_*.md        ← Review these
│   └── Approved/          ← Move approved files here
├── Done/                  ← Completed files
├── Logs/                  ← Check here for errors
├── debug_gmail/           ← Gmail screenshots
├── debug_linkedin/        ← LinkedIn screenshots
└── ...
```

---

## 🔧 Troubleshooting

### Issue 1: Files not going to Pending_Approval
**Check**: Is Gold Orchestrator running?
```batch
python gold\tools\gold_orchestrator.py
```

**Check Logs**: `Logs/gold_orchestrator_*.log`

### Issue 2: Files not moving from Approved to Done
**Check**: Is Action Dispatcher running?
```batch
python silver\tools\action_dispatcher.py --daemon
```

**Manual Test**:
```batch
python test_action_dispatcher.py
```

### Issue 3: Gmail inbox not loading
- Check screenshots in `debug_gmail/`
- Manually login in the browser
- Restart Gmail watcher

### Issue 4: LinkedIn post not publishing
- Check screenshots in `debug_linkedin/`
- Verify you're logged into LinkedIn
- Check if post button is visible

---

## 🧪 Testing Commands

### Test Complete Workflow
```batch
test_workflow.bat
```

### Test Action Dispatcher Only
```batch
python test_action_dispatcher.py
```

### Test Gold Orchestrator Only
```batch
python gold\tools\gold_orchestrator.py
```
(Ctrl+C to stop)

### Quick Fix - Process Pending Files
```batch
quick_fix_approved.bat
```

---

## 📝 Important Notes

1. **Gold Orchestrator MUST be running** for files to move from Needs_Action to Pending_Approval

2. **Action Dispatcher MUST be running** for files to move from Approved to Done

3. **Human Review is REQUIRED** - You must manually move files from:
   - `Pending_Approval/DRAFT_*.md` → `Pending_Approval/Approved/`

4. **Keywords are ENFORCED** - Only messages with keywords will be processed

5. **Check Logs** - All errors are logged to `Logs/` folder

---

## 🎯 What Was Fixed

### Before (Bugs):
- ❌ Files going directly to Done without drafts
- ❌ Gmail inbox not loading
- ❌ LinkedIn crashing on "Start a post"
- ❌ No keyword enforcement
- ❌ No screenshot debugging

### After (Fixed):
- ✅ Files ONLY move to Done AFTER draft creation
- ✅ Gmail properly waits for inbox load
- ✅ LinkedIn has 10+ fallback selectors
- ✅ All 15 keywords enforced across all watchers
- ✅ Screenshot debugging at every step

---

## 📞 Need Help?

1. **Check Logs**: `Logs/` folder
2. **Check Screenshots**: `debug_gmail/`, `debug_linkedin/`
3. **Run Test**: `test_workflow.bat`
4. **Read Full Guide**: `FIXED_WORKFLOW_GUIDE.md`

---

## ✅ Success Indicators

You'll know it's working when:
- Needs_Action folder is usually empty (files processed quickly)
- Pending_Approval has DRAFT_*.md files waiting for your review
- Approved folder is usually empty (files executed quickly)
- Done folder has all processed files
- Logs show "SUCCESS" messages

**Example Success Log:**
```
[PROCESS] Starting analysis for: WHATSAPP_Test_20260328.md
[AI] Calling AI to generate response...
[HITL] Creating draft and action plan...
[DRAFT] Created in Pending_Approval: DRAFT_WHATSAPP_Test_20260328_20260328_120000.md
[MOVING] Moving WHATSAPP_Test_20260328.md to Done...
[SUCCESS] Task processed: WHATSAPP_Test_20260328.md
```
