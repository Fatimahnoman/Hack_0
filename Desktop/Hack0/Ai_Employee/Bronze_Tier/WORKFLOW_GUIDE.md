# 🥉 BRONZE TIER WORKFLOW - COMPLETE GUIDE

## 📊 Single Line Workflow

```
Watcher (Gmail/File) → Needs_Action folder → Ralph Wiggum Loop (Claude Code) → Dashboard.md + Plans → Done/
```

---

## 🎯 COMPLETE WORKFLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                  BRONZE TIER WORKFLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 📧 EMAIL/FILE AAYA                                          │
│     Gmail Watcher ya File Drop                                  │
│     ↓                                                           │
│     Inbox/                                                      │
│                                                                  │
│  2. 📁 FILE WATCHER (Automatic)                                 │
│     filesystem_watcher.py                                       │
│     ↓                                                           │
│     Moves to: Needs_Action/                                     │
│     + Creates .md metadata file                                 │
│                                                                  │
│  3. 🤖 RALPH WIGGUM LOOP (Claude Code)                          │
│     bronze_tier_processor.py                                    │
│     ↓                                                           │
│     - Reads file from Needs_Action/                             │
│     - Analyzes content (Claude Code simulation)                 │
│     - Detects keywords: urgent, invoice, payment, sales         │
│     - Creates action plan                                       │
│                                                                  │
│  4. 📋 UPDATES (Automatic)                                      │
│     - Dashboard.md updated with status                          │
│     - Plan file created in Plans/                               │
│                                                                  │
│  5. 📁 ARCHIVE (Automatic)                                      │
│     - Original file moved to Done/                              │
│     - Completion metadata added                                 │
│                                                                  │
│  ✅ COMPLETE!                                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 FOLDER STRUCTURE

```
Bronze_Tier/
├── Inbox/                    ← NEW files land here
├── Needs_Action/             ← Files waiting to be processed
├── Plans/                    ← Action plans (auto-generated)
├── Done/                     ← COMPLETED files
├── watchers/
│   └── filesystem_watcher.py ← File system monitor
├── bronze_tier_processor.py  ← Ralph Wiggum Loop (Main Processor)
├── Dashboard.md              ← Live status dashboard
├── run_bronze_workflow.bat   ← Start all processes
└── README.md                 ← This file
```

---

## 🚀 HOW TO RUN

### **Option 1: Start All Processes (Recommended)**

```powershell
# Double-click this file:
run_bronze_workflow.bat

# OR run manually:
cd C:\Users\LENOVO\Desktop\Hack0\Ai_Employee\Bronze_Tier
.\run_bronze_workflow.bat
```

This starts:
1. File System Watcher (monitors Inbox/)
2. Ralph Wiggum Loop Processor (processes Needs_Action/)

---

### **Option 2: Run Individually**

```powershell
# Terminal 1: File System Watcher
python watchers\filesystem_watcher.py

# Terminal 2: Ralph Wiggum Loop Processor
python bronze_tier_processor.py
```

---

## 📝 STEP-BY-STEP EXAMPLE

### **Test the Workflow:**

```powershell
# STEP 1: Create a test file in Inbox/
echo "Urgent: Need invoice payment of $5000" > Inbox\test_urgent.md

# STEP 2: File Watcher picks it up (within 5 seconds)
# Automatically moves to Needs_Action/

# STEP 3: Ralph Wiggum Loop processes it (within 10 seconds)
# - Analyzes content
# - Creates Plan in Plans/
# - Updates Dashboard.md
# - Moves to Done/

# STEP 4: Check results
dir Done\
dir Plans\
type Dashboard.md
```

---

## 🤖 RALPH WIGGUM LOOP (Claude Code) FEATURES

### **Content Analysis:**
- ✅ Detects **urgent** keywords → HIGH priority
- ✅ Detects **invoice/payment** → MEDIUM priority
- ✅ Detects **sales** → NORMAL priority
- ✅ Generates action plans automatically

### **Automatic Actions:**
1. ✅ Reads file from Needs_Action/
2. ✅ Extracts YAML frontmatter metadata
3. ✅ Analyzes content with Claude Code logic
4. ✅ Creates Plan file in Plans/
5. ✅ Updates Dashboard.md with stats
6. ✅ Moves processed file to Done/
7. ✅ Adds completion metadata

---

## 📊 DASHBOARD.MD

Live status dashboard with:
- Pending items count
- Processed items count
- Last processed timestamp
- System status (Active/Idle)
- Folder overview
- Quick stats

**Auto-updates** after every file processing!

---

## 🔧 CONFIGURATION

Edit `bronze_tier_processor.py` to customize:

```python
CHECK_INTERVAL = 10  # Check Needs_Action every 10 seconds
```

Edit `watchers/filesystem_watcher.py` to customize:

```python
CHECK_INTERVAL = 5  # Check Inbox every 5 seconds
```

---

## 📋 PROCESS FLOW

| Step | Action | File Location | Time |
|------|--------|---------------|------|
| 1. File created | Inbox/ | 0 sec |
| 2. Watcher detects | → Needs_Action/ | 5 sec |
| 3. Ralph Wiggum Loop processes | → Plans/ + Done/ | 10 sec |
| 4. Dashboard updated | Dashboard.md | 0 sec |

**Total Time:** ~15 seconds from drop to completion!

---

## 🎯 KEYWORDS DETECTED

| Keyword | Priority | Action Type |
|---------|----------|-------------|
| `urgent` | HIGH | urgent_response |
| `invoice` | MEDIUM | invoice_processing |
| `payment` | MEDIUM | invoice_processing |
| `sales` | NORMAL | sales_inquiry |

---

## 📁 FILE NAMING CONVENTION

### **Input:**
- `test_urgent.md`

### **After Watcher:**
- `test_urgent.md` (in Needs_Action/)

### **After Ralph Wiggum Loop:**
- Plan: `PLAN_Urgent_Invoice_20260402_044609.md` (in Plans/)
- Done: `test_urgent_COMPLETED_20260402_044609.md` (in Done/)

---

## 🚨 TROUBLESHOOTING

### **File not moving from Inbox?**
```powershell
# Check if watcher is running
python watchers\filesystem_watcher.py

# Check watchdog installation
pip install watchdog
```

### **File stuck in Needs_Action?**
```powershell
# Run processor manually
python bronze_tier_processor.py

# Check for errors in console output
```

### **Dashboard not updating?**
```powershell
# Ensure processor has write permissions
# Check if Dashboard.md is open in another program
```

---

## ✅ DAILY USAGE

### **Morning:**
```powershell
# Start workflow
.\run_bronze_workflow.bat

# Check dashboard
type Dashboard.md
```

### **During Day:**
- Drop files in `Inbox/`
- Automatic processing happens!

### **Evening:**
```powershell
# Check completed work
dir Done\

# Check plans created
dir Plans\

# Stop processes (close terminal windows)
```

---

## 🎉 SUMMARY

| Component | Purpose | Status |
|-----------|---------|--------|
| **File Watcher** | Inbox → Needs_Action | ✅ Automatic |
| **Ralph Wiggum Loop** | Process files | ✅ Automatic |
| **Dashboard** | Live status | ✅ Auto-update |
| **Plans Manager** | Create plans | ✅ Automatic |
| **Done Mover** | Archive files | ✅ Automatic |

**Bronze Tier:** 100% Automatic! No manual intervention needed! 🎯

---

*Last Updated: 2026-04-02*
*Bronze Tier - Ralph Wiggum Loop (Claude Code)*
