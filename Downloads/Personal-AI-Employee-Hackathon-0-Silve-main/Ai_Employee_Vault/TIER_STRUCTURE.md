# AI Employee Vault - Tier Structure

## 📊 Project Structure

```
Ai_Employee_Vault/
│
├── 🥉 Bronze_Tier/              # Basic Tier (No External APIs)
│   ├── Inbox/                   # Main inbox for file drops
│   ├── Inbox_main/              # Backup inbox
│   ├── Needs_Action_main/       # Files requiring attention
│   ├── Pending_Approval_main/   # Files awaiting approval
│   ├── Plans_main/              # Draft plans
│   ├── Done_main/               # Completed files
│   ├── Approved/                # Approved files (for orchestrator)
│   ├── watchers/
│   │   └── filesystem_watcher.py    # 🥉 Bronze watcher
│   ├── Company_Handbook.md
│   ├── Dashboard.md
│   └── README.md
│
├── 🥈 Silver_Tier/              # Advanced Tier (External APIs)
│   ├── watchers/
│   │   ├── gmail_watcher.py         # 🥈 Gmail API
│   │   ├── whatsapp_watcher.py      # 🥈 WhatsApp (Playwright)
│   │   ├── whatsapp_watcher_simple.py # 🥈 WhatsApp (file-based)
│   │   └── linkedin_watcher.py      # 🥈 LinkedIn (removed)
│   ├── tools/
│   ├── schedulers/
│   ├── Pending_Approval/        # Silver tier approvals
│   └── watchers_main/           # Backup watchers
│
├── logs/                        # Central logs
├── mcp_servers/                 # MCP servers
│   └── email-mcp/
│
├── ecosystem.config.js          # PM2 configuration
├── orchestrator_agent.py        # Auto-reply agent
├── gmail_auth.py                # Gmail OAuth
├── credentials.json             # Gmail credentials ✅
├── token.json                   # Gmail token ✅
└── [Documentation files...]
```

---

## 🎯 Tiers Overview

### 🥉 **Bronze Tier** (Basic)

| Feature | Details |
|---------|---------|
| **Purpose** | File system monitoring |
| **External APIs** | ❌ None |
| **Credentials** | ❌ None required |
| **Watcher** | `filesystem_watcher.py` |
| **Workflow** | Inbox → Needs_Action → Done |

**Use Case:** Simple file monitoring without any external integrations.

---

### 🥈 **Silver Tier** (Advanced)

| Feature | Details |
|---------|---------|
| **Purpose** | External API integrations |
| **External APIs** | ✅ Gmail API, WhatsApp Web |
| **Credentials** | ✅ `credentials.json` + `token.json` |
| **Watchers** | `gmail_watcher.py`, `whatsapp_watcher_simple.py` |
| **Workflow** | Email/Message → Needs_Action → Pending_Approval → Done |

**Use Case:** Full automation with email and messaging integrations.

---

## 🔄 Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE WORKFLOW                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📧 GMAIL (Silver Tier)                                         │
│  Gmail → [gmail_watcher] → Bronze_Tier/Needs_Action_main/       │
│                                                                  │
│  📁 FILE DROP (Bronze Tier)                                     │
│  Bronze_Tier/Inbox/ → [filesystem_watcher] → Needs_Action_main/ │
│                                                                  │
│  💬 WHATSAPP (Silver Tier)                                      │
│  Bronze_Tier/Inbox/ → [whatsapp_watcher_simple] → Needs_Action  │
│                                                                  │
│  ─────────────────────────────────────────────────────────      │
│                                                                  │
│  🤖 ORCHESTRATOR (Automatic)                                    │
│  1. User moves file to: Bronze_Tier/Pending_Approval_main/      │
│  2. User approves by moving to: Approved/ subfolder             │
│  3. [orchestrator_agent] picks up file                          │
│  4. Sends email reply via Gmail API                             │
│  5. Moves file to: Bronze_Tier/Done_main/                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Run Commands

### **Start All Watchers + Orchestrator**

```powershell
cd C:\Users\LENOVO\Downloads\Personal-AI-Employee-Hackathon-0-Silve-main\Ai_Employee_Vault

# Start all
pm2 start ecosystem.config.js

# Check status
pm2 status

# View logs
pm2 logs --lines 30
```

---

### **Start Specific Tier**

```powershell
# Only Bronze Tier (File monitoring)
pm2 start ecosystem.config.js --only filesystem_watcher

# Only Silver Tier (Gmail + WhatsApp)
pm2 start ecosystem.config.js --only gmail_watcher,whatsapp_watcher_simple

# Only Orchestrator
pm2 start ecosystem.config.js --only orchestrator_agent
```

---

## 📋 PM2 Configuration

| ID | Name | Tier | Script Path |
|----|------|------|-------------|
| 0 | `gmail_watcher` | 🥈 Silver | `Silver_Tier/watchers/gmail_watcher.py` |
| 1 | `filesystem_watcher` | 🥉 Bronze | `Bronze_Tier/watchers/filesystem_watcher.py` |
| 2 | `whatsapp_watcher_simple` | 🥈 Silver | `Silver_Tier/watchers/whatsapp_watcher_simple.py` |
| 3 | `orchestrator_agent` | 🤖 Agent | `orchestrator_agent.py` |

---

## 📁 Folder Usage

| Folder | Tier | Purpose |
|--------|------|---------|
| `Bronze_Tier/Inbox/` | 🥉 Bronze | Main file drop location |
| `Bronze_Tier/Needs_Action_main/` | 🥉 Bronze | Files requiring attention |
| `Bronze_Tier/Pending_Approval_main/` | 🥉 Bronze | Files awaiting approval |
| `Bronze_Tier/Pending_Approval_main/Approved/` | 🤖 Orchestrator | **Approved files for auto-reply** |
| `Bronze_Tier/Done_main/` | 🥉 Bronze | Completed files |
| `Silver_Tier/watchers/` | 🥈 Silver | Gmail/WhatsApp watchers |

---

## ✅ Test Workflow

### **Test Bronze Tier (File Drop)**

```powershell
# 1. Drop a file in Inbox
echo "Test message" > Bronze_Tier\Inbox\test.txt

# 2. Wait 5 seconds
timeout /t 5

# 3. Check Needs_Action
dir Bronze_Tier\Needs_Action_main
```

---

### **Test Silver Tier (Gmail)**

```powershell
# 1. Send email to yourself with subject "urgent"
# 2. Wait 2 minutes (Gmail check interval)
# 3. Check Needs_Action
dir Bronze_Tier\Needs_Action_main
```

---

### **Test Orchestrator (Auto-Reply)**

```powershell
# 1. Move file to Approved folder
move Bronze_Tier\Needs_Action_main\GMAIL_*.md Bronze_Tier\Pending_Approval_main\Approved\

# 2. Wait 10 seconds
timeout /t 10

# 3. Check Done folder
dir Bronze_Tier\Done_main

# 4. Check orchestrator logs
pm2 logs orchestrator_agent --lines 30
```

---

## 🎯 Summary

| Tier | Watchers | Credentials | Auto-Reply |
|------|----------|-------------|------------|
| 🥉 **Bronze** | 1 (Filesystem) | ❌ None | ❌ No |
| 🥈 **Silver** | 2 (Gmail, WhatsApp) | ✅ Gmail OAuth | ✅ Yes (Orchestrator) |

---

**Total Watchers Running:** 4 (via PM2)
- 🥉 Bronze: 1 watcher
- 🥈 Silver: 2 watchers
- 🤖 Orchestrator: 1 agent

---

*Last Updated: 2026-03-23*
*AI Employee Vault - Tier-Based Structure*
