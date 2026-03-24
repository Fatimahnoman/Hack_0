# Complete Workflow Guide - AI Employee

## 🎯 COMPLETE WORKFLOW

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE EMAIL WORKFLOW                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 📧 EMAIL AAYA (Automatic)                                   │
│     Gmail → [gmail_watcher] → Bronze_Tier/Inbox/               │
│                                                                  │
│  2. 🔄 WORKFLOW PROCESSOR (Automatic)                           │
│     Inbox/ → [workflow_processor] →                              │
│       ↓ Important keywords?                                      │
│       YES → Needs_Action/                                        │
│       NO → Plans/                                                │
│                                                                  │
│  3. 👤 USER REVIEW (Manual - Human in the Loop)                │
│     Needs_Action/ → User reviews → Plans/                       │
│                                                                  │
│  4. 📋 PENDING APPROVAL (Manual)                                │
│     Plans/ → User moves → Pending_Approval/                     │
│                                                                  │
│  5. ✅ OWNER APPROVAL (Manual - HITL Security)                  │
│     Pending_Approval/ → User moves → Approved/                  │
│                                                                  │
│  6. 🤖 AUTO REPLY (Automatic)                                   │
│     Approved/ → [orchestrator_agent] →                           │
│       → Email reply sent                                         │
│       → File moved to Done/                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 FOLDER STRUCTURE

```
Bronze_Tier/
├── Inbox/                 ← NEW emails land here (from Gmail watcher)
├── Needs_Action/          ← IMPORTANT emails (auto-moved by workflow processor)
├── Plans/                 ← DRAFTS for review (auto-moved if not important)
├── Pending_Approval/      ← WAITING for approval (manual move)
│   └── Approved/          ← APPROVED files trigger auto-reply
└── Done/                  ← COMPLETED (auto-moved after reply sent)
```

---

## 🚀 RUNNING PROCESSES (PM2)

```
┌────┬──────────────────────┬───────────────────────────────────┐
│ id │ name                 │ purpose                           │
├────┼──────────────────────┼───────────────────────────────────┤
│ 0  │ gmail_watcher        │ Monitors Gmail → saves to Inbox/  │
│ 1  │ filesystem_watcher   │ Monitors Inbox/ for file drops    │
│ 2  │ whatsapp_watcher_... │ Monitors WhatsApp messages        │
│ 3  │ workflow_processor   │ Inbox → Needs_Action → Plans      │
│ 4  │ orchestrator_agent   │ Approved → Reply Send → Done      │
└────┴──────────────────────┴───────────────────────────────────┘

All processes: ✅ ONLINE (24/7 via PM2)
```

---

## 📝 STEP-BY-STEP WORKFLOW

### **STEP 1: Email Arrives (Automatic)**

```
📧 Gmail se email aaya
   Subject: "Urgent meeting request"
   From: client@example.com
   ↓
🤖 gmail_watcher picks it up
   Checks keywords: urgent, invoice, payment, sales
   ↓
📁 File created in Bronze_Tier/Inbox/
   GMAIL_Urgent_meeting_20260324_123456.md
```

**No action needed from you!** ✅

---

### **STEP 2: Workflow Processing (Automatic)**

```
📂 Inbox/ mein file aayi
   ↓
🤖 workflow_processor checks it
   ↓
   Keywords match? (urgent, invoice, payment, sales)
   ↓
   YES → Move to Needs_Action/
   NO → Move to Plans/
```

**No action needed from you!** ✅

---

### **STEP 3: User Review (Manual - YOU)**

```
👤 You check Bronze_Tier/Needs_Action/
   ↓
   Review email content
   ↓
   Decide: Is this important?
   ↓
   YES → Move to Plans/ for drafting
   NO → Delete or archive
```

**YOUR ACTION REQUIRED!** 👤

```powershell
# Move to Plans folder
move Bronze_Tier\Needs_Action\GMAIL_*.md Bronze_Tier\Plans\
```

---

### **STEP 4: Create Draft (Manual - YOU)**

```
👤 You review file in Plans/
   ↓
   Create reply draft (optional)
   Or use auto-generated draft
   ↓
   Move to Pending_Approval/
```

**YOUR ACTION REQUIRED!** 👤

```powershell
# Move to Pending Approval
move Bronze_Tier\Plans\*.md Bronze_Tier\Pending_Approval\
```

---

### **STEP 5: Owner Approval (Manual - HITL Security)**

```
👤 Owner reviews draft in Pending_Approval/
   ↓
   Check content, tone, accuracy
   ↓
   APPROVE → Move to Approved/ subfolder
   REJECT → Move back to Plans/ or delete
```

**CRITICAL SECURITY STEP!** 🔒

```powershell
# Approve file (triggers auto-reply)
move Bronze_Tier\Pending_Approval\*.md Bronze_Tier\Pending_Approval\Approved\
```

---

### **STEP 6: Auto Reply Sent (Automatic)**

```
📂 Approved/ mein file aayi
   ↓
🤖 orchestrator_agent picks it up
   ↓
   Extract email data (from, subject, content)
   Generate polite reply
   Send via Gmail API
   ↓
✅ Reply sent to client
   ↓
📁 File moved to Done/
```

**No action needed from you!** ✅

---

## 🎯 QUICK COMMANDS

### **Check Status**
```powershell
pm2 status
```

### **View Logs**
```powershell
# All logs
pm2 logs --lines 30

# Specific process
pm2 logs gmail_watcher --lines 30
pm2 logs workflow_processor --lines 30
pm2 logs orchestrator_agent --lines 30
```

### **Move Files Through Workflow**
```powershell
# Step 1: Inbox to Needs_Action (usually automatic)
move Bronze_Tier\Inbox\*.md Bronze_Tier\Needs_Action\

# Step 2: Needs_Action to Plans
move Bronze_Tier\Needs_Action\*.md Bronze_Tier\Plans\

# Step 3: Plans to Pending_Approval
move Bronze_Tier\Plans\*.md Bronze_Tier\Pending_Approval\

# Step 4: Approve (triggers auto-reply)
move Bronze_Tier\Pending_Approval\*.md Bronze_Tier\Pending_Approval\Approved\
```

### **Check Folders**
```powershell
dir Bronze_Tier\Inbox
dir Bronze_Tier\Needs_Action
dir Bronze_Tier\Plans
dir Bronze_Tier\Pending_Approval\Approved
dir Bronze_Tier\Done
```

---

## 🔒 SECURITY (Human in the Loop)

### **Why HITL is Important:**

| Without HITL ❌ | With HITL ✅ |
|----------------|--------------|
| Wrong replies sent | All replies reviewed |
| No quality control | Owner approves content |
| Risk of errors | Security before sending |
| Auto-pilot mode | Human oversight |

### **Approval Checklist:**

Before moving file to `Approved/`:

- [ ] Email content reviewed
- [ ] Reply draft accurate
- [ ] Tone is polite and professional
- [ ] No sensitive information leaked
- [ ] Attachments (if any) verified

---

## 📋 EXAMPLE WORKFLOW

### **Real Example: Client Inquiry**

```
1. 📧 Email received:
   From: john@client.com
   Subject: "Urgent: Need invoice for $5000"
   
2. 🤖 gmail_watcher:
   - Detected keyword: "urgent", "invoice"
   - Priority: HIGH
   - Saved to: Inbox/GMAIL_Urgent_Need_20260324_143022.md
   
3. 🤖 workflow_processor:
   - Keywords detected: urgent, invoice
   - Moved to: Needs_Action/
   
4. 👤 You review:
   - This is important!
   - Move to: Plans/
   
5. 👤 You draft reply:
   - Add polite response
   - Move to: Pending_Approval/
   
6. 👤 Owner approves:
   - Review draft
   - Move to: Approved/
   
7. 🤖 orchestrator_agent:
   - Extract email: john@client.com
   - Generate reply: "Thank you for your inquiry..."
   - Send via Gmail
   - Move to: Done/
   
✅ COMPLETE!
```

---

## 🎯 KEYWORDS SYSTEM

### **Important Keywords (Auto-detected):**

| Keyword | Priority | Action |
|---------|----------|--------|
| `urgent` | HIGH | Move to Needs_Action |
| `invoice` | MEDIUM | Move to Needs_Action |
| `payment` | MEDIUM | Move to Needs_Action |
| `sales` | NORMAL | Move to Needs_Action |

### **No Keywords Match:**
→ File moved to `Plans/` for later review

---

## 🚨 TROUBLESHOOTING

### **Email not appearing in Inbox?**
```powershell
# Check gmail_watcher logs
pm2 logs gmail_watcher --lines 50

# Check if credentials exist
Test-Path credentials.json
Test-Path token.json
```

### **File stuck in Needs_Action?**
```powershell
# Manually move to Plans
move Bronze_Tier\Needs_Action\*.md Bronze_Tier\Plans\
```

### **Reply not sent?**
```powershell
# Check orchestrator logs
pm2 logs orchestrator_agent --lines 50

# Check if file is in Approved/
dir Bronze_Tier\Pending_Approval\Approved
```

---

## 📊 MONITORING DASHBOARD

```powershell
# Quick status check
pm2 status

# Expected output:
┌────┬──────────────────────┬──────────┬──────┬───────────┐
│ id │ name                 │ status   │ cpu  │ memory    │
├────┼──────────────────────┼──────────┼──────┼───────────┤
│ 0  │ gmail_watcher        │ online   │ 0%   │ 54mb      │
│ 1  │ filesystem_watcher   │ online   │ 0%   │ 20mb      │
│ 2  │ whatsapp_watcher_... │ online   │ 0%   │ 12mb      │
│ 3  │ workflow_processor   │ online   │ 0%   │ 16mb      │
│ 4  │ orchestrator_agent   │ online   │ 0%   │ 47mb      │
└────┴──────────────────────┴──────────┴──────┴───────────┘
```

---

## ✅ DAILY ROUTINE

### **Morning (2 minutes):**
```powershell
# Check status
pm2 status

# Check overnight emails
dir Bronze_Tier\Inbox
dir Bronze_Tier\Needs_Action
```

### **During Day (as needed):**
```powershell
# Review and move files
move Bronze_Tier\Needs_Action\file.md Bronze_Tier\Plans\
move Bronze_Tier\Plans\file.md Bronze_Tier\Pending_Approval\
move Bronze_Tier\Pending_Approval\file.md Bronze_Tier\Pending_Approval\Approved\
```

### **Evening (1 minute):**
```powershell
# Check completed work
dir Bronze_Tier\Done

# View logs
pm2 logs --lines 20
```

---

## 🎉 SUMMARY

| Step | Action | Who | Time |
|------|--------|-----|------|
| 1. Email arrives | Automatic | 🤖 | 0 sec |
| 2. Workflow processing | Automatic | 🤖 | 0 sec |
| 3. User review | Manual | 👤 | 30 sec |
| 4. Draft creation | Manual | 👤 | 2 min |
| 5. Owner approval | Manual | 👤 | 1 min |
| 6. Auto reply sent | Automatic | 🤖 | 0 sec |

**Total YOUR time:** ~3.5 minutes per email
**AI saves:** ~10 minutes (reading, drafting, sending)

---

*Last Updated: 2026-03-24*
*AI Employee Vault - Complete Workflow Guide*
