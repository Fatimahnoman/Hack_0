# 🚀 GOLD TIER - ONE PAGE QUICK REFERENCE

## 📋 Complete Flow (Single Line)
```
Gmail → Needs_Action → Pending_Approval → Approved → [Auto] → Done + Action
```

---

## ⚡ Quick Commands (Copy-Paste)

### 1️⃣ First Time Setup
```bash
del token.json && python gmail_auth.py
start_gold_tier.bat
```

### 2️⃣ Test Email Flow
```bash
# Send email to your Gmail: Subject "urgent", Body "send to test@example.com"
# Wait 2 minutes, then:
move Needs_Action\GMAIL_*.md Pending_Approval\
move Pending_Approval\GMAIL_*.md Pending_Approval\Approved\
# Wait 30 seconds - auto moves to Done
```

### 3️⃣ Test LinkedIn Flow
```bash
# Create post (or use menu option 13)
move Pending_Approval\linkedin_*.md Pending_Approval\Approved\
# Wait 1 minute - browser opens, posts automatically
```

### 4️⃣ Test Odoo Flow
```bash
# Create JSON in Inbox\ (or use menu option 14)
import_to_odoo.bat
# Check Odoo at http://localhost:8069
```

---

## 📁 Folder Movement Map

| From | To | Command | Auto/Manual |
|------|-----|---------|-------------|
| Gmail | Needs_Action | [Auto by watcher] | Automatic |
| Needs_Action | Pending_Approval | `move Needs_Action\*.md Pending_Approval\` | Manual |
| Pending_Approval | Approved | `move Pending_Approval\*.md Pending_Approval\Approved\` | Manual |
| Approved | Done | [Auto by dispatcher] | Automatic |

---

## 🎯 Test Menu (Interactive)

```bash
test_gold_tier.bat
```

**Options:**
- 1: Authorize Gmail
- 2: Start Watchers
- 11: Move Needs_Action → Pending_Approval
- 12: Move Pending_Approval → Approved
- 13: Create Test LinkedIn Post
- 14: Create Test Sales Lead
- 15: Run Odoo Importer
- 16-18: Full Test Instructions

---

## 📊 Monitoring Commands

```bash
# Check folders
dir Needs_Action
dir Pending_Approval
dir Pending_Approval\Approved
dir Done

# Check logs
type Logs\action_dispatcher_*.log
type Logs\linkedin_*.log
type Logs\watcher.log

# Check dashboard
type Dashboard.md
```

---

## ⏱️ Expected Timings

| Action | Time |
|--------|------|
| Gmail detection | 1-2 min |
| Action Dispatcher | 10-30 sec |
| Email send | 5-15 sec |
| LinkedIn post | 30-60 sec |
| Odoo import | 2-5 sec |

---

## ✅ Success Indicators

- ✅ File appears in `Done\`
- ✅ Email received at destination
- ✅ LinkedIn post on your profile
- ✅ Contact in Odoo
- ✅ Dashboard updated

---

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Email not sending | Check `to:` field in file |
| LinkedIn timeout | Check browser is not minimized |
| Odoo connection failed | Start Odoo server |
| No files in Needs_Action | Check Gmail Watcher logs |

---

## 📞 Log Locations

```
Logs/
├── action_dispatcher_*.log  (Email/LinkedIn execution)
├── linkedin_*.log           (LinkedIn posting)
├── watcher.log              (Gmail monitoring)
└── odoo_importer_*.log      (Odoo import)
```

---

## 🎯 Full Test in 5 Minutes

```bash
# 1. Start everything (30 sec)
start_gold_tier.bat

# 2. Send test email to your Gmail (30 sec)
# Subject: urgent - Test
# Body: Send to test@example.com

# 3. Move file after 2 min (30 sec)
move Needs_Action\GMAIL_*.md Pending_Approval\Approved\

# 4. Create LinkedIn post (30 sec)
test_gold_tier.bat → Option 13
move Pending_Approval\test_*.md Pending_Approval\Approved\

# 5. Create Odoo lead (30 sec)
test_gold_tier.bat → Option 14
import_to_odoo.bat

# 6. Verify everything (1 min)
dir Done
type Dashboard.md
```

**Total: ~5 minutes for full Gold Tier test!**

---

## 🔑 Key Files

| File | Purpose |
|------|---------|
| `start_gold_tier.bat` | Start all watchers |
| `test_gold_tier.bat` | Interactive test menu |
| `gmail_auth.py` | Gmail OAuth |
| `import_to_odoo.bat` | Odoo importer |

---

**Print this page and keep it handy!** 📄
