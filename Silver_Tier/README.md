# Silver Tier - AI Employee System

## 🎯 Overview

Silver Tier ek automated AI employee system hai jo:
- **Gmail** messages monitor karta hai
- **WhatsApp** messages monitor karta hai
- **Instagram** DMs/posts monitor karta hai
- Files ko automatically workflow stages mein move karta hai
- Tasks ko automate karta hai (e.g., Instagram posts)

---

## 📁 Folder Structure

```
Silver_Tier/
├── Vault/                          # Saara data yahan store hota hai
│   ├── Inbox/                      # New incoming files
│   ├── Needs_Action/               # Files jo action wait kar rahi hain
│   ├── Pending_Approval/           # Approval pending files
│   ├── Approved/                   # Approved files
│   ├── Done/                       # Completed files
│   ├── Logs/                       # System logs
│   ├── Plans/                      # Plan.md files
│   ├── Dashboard.md                # System status
│   └── Company_Handbook.md         # Rules & guidelines
│
├── watchers/                       # Monitoring scripts
│   ├── gmail_watcher.py            # Gmail monitor
│   ├── whatsapp_watcher.py         # WhatsApp monitor
│   └── instagram_watcher.py        # Instagram monitor
│
├── sessions/                       # Login sessions (private!)
│   ├── whatsapp_session/           # WhatsApp login data
│   └── instagram_session/          # Instagram login data
│
├── skills/                         # Automation skills
│   └── auto_insta_post.py          # Instagram auto-post
│
├── mcp_servers/
│   └── actions_mcp/
│       ├── server.py               # MCP server
│       └── README.md
│
├── orchestrator.py                 # Main runner (sab control karta hai)
├── whatsapp_login.py               # WhatsApp login script
├── instagram_login.py              # Instagram login script
├── .env                            # Secrets (never commit!)
└── credentials.json                # Gmail API credentials
```

---

## 🚀 Quick Start

### Step 1: Pehli Baar Setup

**1. WhatsApp Login:**
```bash
python whatsapp_login.py
```
- Chrome khulega
- QR code scan karo phone se
- Session save ho jayega

**2. Instagram Login:**
```bash
python instagram_login.py
```
- Username/password enter karo
- Session save ho jayega

**3. Gmail Setup:**
- `credentials.json` already configured hai
- Pehli baar run pe browser mein authorize karna hoga

---

### Step 2: System Run Karo

**Main Command:**
```bash
python orchestrator.py
```

**Yeh automatically:**
- ✅ Saare watchers start karega (Gmail, WhatsApp, Instagram)
- ✅ Har 30 seconds mein workflow process karega
- ✅ Har 60 seconds mein skills check karega
- ✅ Har 5 minutes mein Dashboard update karega

---

## 🔄 Workflow System

### File Flow
```
Inbox → Needs_Action → Pending_Approval → Approved → Done
```

### Auto-Move Rules

| Stage | Trigger | Time |
|-------|---------|------|
| Needs_Action → Pending_Approval | File age > 2 minutes | **AUTO** |
| Pending_Approval → Approved | `[APPROVED]` marker | **MANUAL** |
| Approved → Done | `[DONE]` marker | **AUTO** |

### Manual Markers Add Karna

**File kholo aur end mein add karo:**

```markdown
From: +92XXX
Message: Client ne reply manga hai

[APPROVED]  ← Approval ke liye
[DONE]      ← Completion ke liye
```

---

## 📊 Watchers Status

| Watcher | Status | Session Path |
|---------|--------|--------------|
| Gmail | ✅ Active | OAuth (no session) |
| WhatsApp | ✅ Active | `sessions/whatsapp_session/` |
| Instagram | ✅ Active | `sessions/instagram_session/` |

---

## 🛠️ Skills

### Auto Instagram Post

**Trigger:** `INSTA_*.md` file in `Needs_Action/`

**Example File:**
```markdown
From: User Request
Platform: Instagram
Action: Post

Caption: Amazing sunset! 🌅
Image: path/to/image.jpg

[APPROVED]
```

**Result:** Auto-post to Instagram!

---

## 📋 Commands Reference

| Command | Purpose |
|---------|---------|
| `python orchestrator.py` | Start full system |
| `python whatsapp_login.py` | Login to WhatsApp |
| `python instagram_login.py` | Login to Instagram |
| `python watchers/gmail_watcher.py` | Run Gmail only |
| `python watchers/whatsapp_watcher.py` | Run WhatsApp only |
| `python watchers/instagram_watcher.py` | Run Instagram only |

---

## 🔒 Security

### Never Commit These Files:
- `.env` - Contains secrets
- `credentials.json` - API credentials
- `sessions/` - Login session data
- `token.json` - OAuth tokens

**`.gitignore` already configured hai!**

---

## 📝 File Markers

| Marker | Meaning | Action |
|--------|---------|--------|
| `[APPROVED]` | Task approved | Move to Approved |
| `[DONE]` | Task completed | Move to Done |
| `[URGENT]` | High priority | Handle first |
| `[BLOCKED]` | Waiting on something | Add note |

---

## 🐛 Troubleshooting

### WhatsApp Login Issue
```bash
# Purana session delete karo
rmdir /s /q sessions\whatsapp_session
python whatsapp_login.py
```

### Chrome Crash Error
```bash
# Saare Chrome windows band karo
# Phir run karo
python orchestrator.py
```

### File Not Moving
```bash
# Check orchestrator chal raha hai
# 30 seconds wait karo (workflow interval)
```

---

## 📈 System Status Check

**Dashboard dekho:**
```bash
type Vault\Dashboard.md
```

**Current files check karo:**
```bash
dir Vault\Needs_Action\
dir Vault\Pending_Approval\
dir Vault\Approved\
dir Vault\Done\
```

---

## 🎯 Daily Workflow

1. **Morning:** `python orchestrator.py` run karo
2. **During day:** Files auto-create hongi
3. **Check:** `Vault/Needs_Action/` for new tasks
4. **Approve:** Add `[APPROVED]` marker
5. **Complete:** Add `[DONE]` marker
6. **Evening:** Check `Vault/Done/` for completed tasks

---

## 📞 Support Files

| File | Purpose |
|------|---------|
| `Vault/Dashboard.md` | System status |
| `Vault/Company_Handbook.md` | Rules & guidelines |
| `Vault/Plans/Plan.md` | Future plans |
| `Vault/Logs/` | System logs |

---

## ✅ Checklist - First Time Setup

- [ ] WhatsApp login complete
- [ ] Instagram login complete
- [ ] Gmail credentials configured
- [ ] Orchestrator run kiya
- [ ] Test message bheja (WhatsApp/Email)
- [ ] File create hui check kiya
- [ ] `[APPROVED]` marker test kiya
- [ ] `[DONE]` marker test kiya

---

**System Ready! 🚀**

For issues, check `Vault/Logs/` folder.
