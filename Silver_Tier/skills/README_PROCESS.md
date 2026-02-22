# Process_Needs_Action Skill - Silver Tier (UPGRADED)

## 🎯 Overview

This is the **DEFAULT task processor** for ALL files in `Vault/Needs_Action/`.

### What It Does

1. **Auto-Creates Plans** → Every task gets a `Plan_[timestamp]_[title].md` in `Vault/Plans/`
2. **Step-by-Step Actions** → Clear checkboxes for each action
3. **Follows Company Rules** → Reads `Company_Handbook.md` strictly
4. **Sensitive Action Detection** → Auto-routes to `Pending_Approval/`
5. **MCP Execution** → Executes approved actions via MCP tools
6. **Auto-Cleanup** → Moves to `Done/` + updates `Dashboard.md`

---

## 🚀 How to Run

### Option 1: Run Standalone

```powershell
cd E:\Hackathon_Zero\Silver_Tier
python skills/process_needs_action.py
```

### Option 2: Run via Orchestrator (Recommended)

```powershell
python orchestrator.py
```

The orchestrator automatically calls this skill for all `.md` files in `Needs_Action/`.

---

## 📋 Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  New File in Vault/Needs_Action/                            │
│  (WhatsApp, Gmail, Instagram, etc.)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Process_Needs_Action Skill Triggers                        │
│  - Reads file content                                       │
│  - Extracts task info (platform, sender, priority)          │
│  - Detects action type                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Create Plan File in Vault/Plans/                           │
│  Filename: Plan_20260222_193045_John_Doe.md                 │
│  - Clear checkboxes                                         │
│  - Step-by-step actions                                     │
│  - Company rules included                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Is Action Sensitive?                                       │
│  (email, send, post, payment, delete, etc.)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
    ┌─────────┐            ┌─────────────┐
    │  NO     │            │    YES      │
    │         │            │             │
    │ Execute │            │ Move to     │
    │ via MCP │            │ Pending_    │
    │         │            │ Approval/   │
    └────┬────┘            └──────┬──────┘
         │                       │
         │                       │ Human reviews & moves
         │                       │ to Approved/
         │                       ▼
         │              ┌─────────────────┐
         │              │ Execute via MCP │
         │              └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Update Dashboard.md                                        │
│  - Log task completion                                      │
│  - Add timestamp and status                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Move Original File to Vault/Done/                          │
│  ✓ Task Complete                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 Test It Now

### Test 1: WhatsApp Message Processing

**Step 1:** Create a test file

```powershell
# Create test file in Needs_Action
echo "From: John Doe
Received: 2026-02-22 19:30:00
Platform: WhatsApp
Priority: high

Hey! Can you send me the invoice ASAP?

[APPROVED]" > Vault\Needs_Action\WHATSAPP_TEST.md
```

**Step 2:** Run the skill

```powershell
python skills/process_needs_action.py
```

**Step 3:** Check results

```powershell
# Check plan created
dir Vault\Plans\Plan_*.md

# Check file moved
dir Vault\Done\WHATSAPP_TEST.md

# Check dashboard updated
type Vault\Dashboard.md
```

---

### Test 2: Sensitive Action (Email)

**Step 1:** Create sensitive test file

```powershell
echo "From: client@example.com
Received: 2026-02-22 20:00:00
Platform: Gmail
Priority: medium

Please send the payment confirmation email.

Thanks,
Client" > Vault\Needs_Action\EMAIL_TEST.md
```

**Step 2:** Run skill

```powershell
python skills/process_needs_action.py
```

**Step 3:** Check it moved to Pending_Approval

```powershell
dir Vault\Pending_Approval\EMAIL_TEST.md
```

**Step 4:** Manually approve

```powershell
# Move to Approved
move Vault\Pending_Approval\EMAIL_TEST.md Vault\Approved\
```

**Step 5:** Skill will auto-execute via MCP

---

## 📁 Generated Plan File Example

**File:** `Vault/Plans/Plan_20260222_193045_John_Doe.md`

```markdown
# Action Plan: WHATSAPP_20260222_191008.md

**Created:** 2026-02-22 19:30:45
**Platform:** WhatsApp
**From:** John Doe
**Priority:** high
**Status:** Pending Review

---

## Task Summary

Hey! Can you send me the invoice ASAP?

---

## Company Rules (Must Follow)

1. Hamesha polite aur professional raho
2. Payment ya sensitive action > $50 pe approval lo
3. Sab kuch local Vault folder mein rakho
4. No auto-send without approval

---

## Action Steps

[x] **Step 1:** Review WhatsApp message content
    - Understand sender's request from message
[ ] **Step 2:** Draft appropriate response ⚠️ **REQUIRES APPROVAL**
    - Follow company rules for tone and content
[ ] **Step 3:** Send WhatsApp response via MCP ⚠️ **REQUIRES APPROVAL**
    - Use WhatsApp MCP tool to send reply
[ ] **Step 4:** Log response in Dashboard
    - Update Dashboard.md with action taken

---

## Approval Status

- [ ] Plan reviewed by human
- [ ] Sensitive actions approved
- [ ] Ready to execute

**Approval Note:** Move this file to `Approved/` when ready to execute.

---

## Execution Log

**Execution Time:** 2026-02-22 19:35:00
**Status:** ✓ EXECUTED
**Notes:** Task processed by Process_Needs_Action Skill

---

*Generated by Process_Needs_Action Skill - Silver Tier AI Employee*
```

---

## 🔍 Sensitive Action Detection

### Keywords That Trigger Approval

| Keyword | Action Type | Example |
|---------|-------------|---------|
| email | Communication | "Send email to..." |
| send | Communication | "Send the file..." |
| post | Social Media | "Post to Instagram..." |
| publish | Social Media | "Publish this..." |
| instagram | Social Media | "Instagram post..." |
| payment | Financial | "Process payment..." |
| pay | Financial | "Pay the invoice..." |
| money | Financial | "Transfer money..." |
| transfer | Financial | "Bank transfer..." |
| delete | Data | "Delete the file..." |
| remove | Data | "Remove from list..." |
| approve | Decision | "Approve this..." |

---

## 📊 Action Types Handled

| Action Type | Description | MCP Tool |
|-------------|-------------|----------|
| `whatsapp_response` | Reply to WhatsApp messages | (Manual) |
| `email_response` | Reply to emails | `send_email()` |
| `instagram_post` | Post to Instagram | `post_to_instagram()` |
| `instagram_response` | Reply to Instagram DMs | (Manual) |
| `general` | Other tasks | Varies |

---

## 🔄 File Movement Summary

| Stage | Folder | Trigger |
|-------|--------|---------|
| New Task | `Needs_Action/` | Created by watcher |
| Plan Created | `Plans/` | Auto by skill |
| Sensitive Detected | `Pending_Approval/` | Auto by skill |
| Human Approval | `Approved/` | Manual move |
| Execution | (via MCP) | Auto by skill |
| Complete | `Done/` | Auto by skill |

---

## 🛠️ Integration with Orchestrator

The orchestrator automatically calls this skill:

```python
# In orchestrator.py
def run_skills_check():
    for filename in files:
        if filename.endswith('.md'):
            from skills.process_needs_action import process_single_file
            process_single_file(filepath)
```

**No manual intervention needed!**

---

## 📝 Update Dashboard.md

After each task, the dashboard is updated:

```markdown
## Task Log

### WHATSAPP_20260222_191008.md - 2026-02-22 19:35:00
- Platform: WhatsApp
- From: John Doe
- Status: ✓ Completed

### EMAIL_TEST.md - 2026-02-22 20:05:00
- Platform: Gmail
- From: client@example.com
- Status: ✓ Completed
```

---

## ✅ Checklist - First Run

- [ ] Company_Handbook.md exists with rules
- [ ] Vault folders exist (Plans, Pending_Approval, etc.)
- [ ] MCP server is running
- [ ] Test file created in Needs_Action/
- [ ] Skill runs without errors
- [ ] Plan file created
- [ ] File moved correctly
- [ ] Dashboard updated

---

## 🐛 Troubleshooting

| Issue | Fix |
|-------|-----|
| Plan not created | Check `Vault/Plans/` folder exists |
| File not moving | Check file permissions |
| MCP tools not found | Run `pip install fastmcp playwright` |
| Company rules not loaded | Check `Company_Handbook.md` exists |
| Dashboard not updating | Check `Dashboard.md` is not read-only |

---

## 🎯 Quick Commands

```powershell
# Run skill standalone
python skills/process_needs_action.py

# Run full orchestrator
python orchestrator.py

# Check plans folder
dir Vault\Plans\

# Check done folder
dir Vault\Done\

# View logs
type Vault\Logs\process_needs_action.log
```

---

**DEFAULT behavior is now ACTIVE!** 🎉

All files in `Needs_Action/` will be auto-processed with plans, approval routing, and MCP execution.
