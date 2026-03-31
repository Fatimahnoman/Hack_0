# 🏆 GOLD TIER - COMPLETE TESTING GUIDE (Step-by-Step)

## 📁 Complete Workflow Overview

```
Gmail/WhatsApp → Needs_Action → Pending_Approval → Approved → Action Dispatcher → Done
     ↓                ↓              ↓              ↓           ↓              ↓
  Email arrives   Auto-created   You review    Move here   Auto-detects   File + Action
  with "urgent"   by watcher     & approve                  & executes     completed
```

---

## ✅ STEP 1: Authorize Gmail (One-time setup)

```bash
# Delete old token if exists
del token.json

# Authorize Gmail
python gmail_auth.py
```

**Expected:** Browser opens → Sign in → Allow → "SUCCESS!"

---

## ✅ STEP 2: Start All Watchers

```bash
# Start Gold Tier
start_gold_tier.bat
```

**This opens 5 windows:**
1. **Action Dispatcher** - Monitors Approved folder (runs every 10 seconds)
2. **LinkedIn Auto Poster** - Posts to LinkedIn automatically
3. **Gmail Watcher** - Checks Gmail every 2 minutes
4. **WhatsApp Watcher** - Monitors WhatsApp (if configured)
5. **Odoo Inbox Importer** - One-time import, then exits

**Keep these windows open!** They run 24/7.

---

## ✅ STEP 3: Test Email Flow (Urgent/Sales Email)

### 3.1: Send Test Email to Yourself

From any email, send to your Gmail account:

**Subject:** `urgent - Test Gold Tier`
**Body:** 
```
This is a test email for Gold Tier automation.
Please process this urgently.

Recipient: test@example.com
```

### 3.2: Wait for Gmail Watcher

- Gmail Watcher checks every **2 minutes** (120 seconds)
- Watch the **Gmail Watcher window** for activity
- Or check logs: `type Logs\watcher.log`

### 3.3: File Appears in Needs_Action

After 1-2 minutes, check:
```bash
dir Needs_Action
```

You should see:
```
GMAIL_urgent_20260325_123456.md
```

### 3.4: Move to Pending_Approval

```bash
# Move file manually
move Needs_Action\GMAIL_urgent_*.md Pending_Approval\
```

### 3.5: Review the File

```bash
# Read the file
type Pending_Approval\GMAIL_urgent_*.md
```

Check:
- ✅ Has `type: email`
- ✅ Has `from:` (sender)
- ✅ Has `subject:` (urgent)
- ✅ Has `to:` (recipient - if extracted from body)

### 3.6: Move to Approved Folder

```bash
# Move to Approved for action
move Pending_Approval\GMAIL_urgent_*.md Pending_Approval\Approved\
```

### 3.7: Wait for Action Dispatcher

- Action Dispatcher checks every **10 seconds**
- Watch the **Action Dispatcher window**
- Or check logs: `type Logs\action_dispatcher_*.log`

**Expected logs:**
```
[PROCESS] Starting: GMAIL_urgent_20260325_123456.md
[PROCESS] Type: email
[EMAIL] Processing started
[EMAIL] To: test@example.com
[EMAIL] Subject: urgent - Test Gold Tier
[EMAIL] Sending via Gmail API...
[EMAIL] Email sent successfully
[EMAIL] Moved to Done
```

### 3.8: Verify Email Sent

Check:
1. **Done folder:**
   ```bash
   dir Done
   ```
   Should see: `done_GMAIL_urgent_*.md`

2. **Recipient inbox** - Email should arrive!

3. **Dashboard:**
   ```bash
   type Dashboard.md
   ```
   Should show recent activity.

---

## ✅ STEP 4: Test LinkedIn Post Flow

### 4.1: Create LinkedIn Post Draft

Create file: `Pending_Approval\linkedin_test_post.md`

```markdown
---
type: linkedin_post_draft
source: gold_tier_test
created: 2026-03-25 12:00:00
status: pending_approval
---

## LinkedIn Post Draft

🚀 Excited to announce our Gold Tier automation is working perfectly!

Autonomous AI employees are here. The future is now.

#AI #Automation #GoldTier #Innovation

---
*Test post for Gold Tier*
```

### 4.2: Move to Approved Folder

```bash
# Move to Approved
move Pending_Approval\linkedin_test_post.md Pending_Approval\Approved\
```

### 4.3: Wait for LinkedIn Auto Poster

- LinkedIn poster runs in **daemon mode** (checks every 30 seconds)
- Watch the **LinkedIn Auto Poster window**
- Browser will open automatically

**Expected flow:**
```
1. Browser opens
2. Navigates to LinkedIn
3. Clicks "Start a post"
4. Types content (slowly, 100ms/char)
5. Clicks "Post"
6. Shows "SUCCESS!"
```

### 4.4: Verify Post Published

Check:
1. **Your LinkedIn profile** - Post should be visible!
2. **Done folder:**
   ```bash
   dir Done
   ```
   Should see: `linkedin_posted_*.md`

3. **Logs:**
   ```bash
   type Logs\linkedin_*.log
   ```

---

## ✅ STEP 5: Test Sales Lead → Odoo Flow

### 5.1: Create Test Sales Lead JSON

Create file: `Inbox\test_lead_gold_tier.json`

```json
{
  "type": "sales_lead",
  "customer_name": "Test Customer Gold Tier",
  "email": "customer@test.com",
  "phone": "+923001234567",
  "product": "Gold Tier Automation",
  "amount": 100000,
  "currency": "PKR",
  "notes": "Interested in AI employee automation"
}
```

### 5.2: Run Odoo Importer

```bash
# Run importer
import_to_odoo.bat
```

**Expected:**
```
Connecting to Odoo...
✓ Connected successfully!
Processing: test_lead_gold_tier.json
✓ Created new partner: Test Customer Gold Tier
✓ Created CRM lead
✓ File moved to Done
```

### 5.3: Verify in Odoo

1. **Open Odoo:** http://localhost:8069
2. **Go to Contacts** - Should see "Test Customer Gold Tier"
3. **Go to CRM → Leads** - Should see the lead!

### 5.4: Check Done Folder

```bash
dir Done
```

Should see: `processed_test_lead_gold_tier.json`

---

## 📊 Quick Reference: File Movement Commands

### Email Flow
```bash
# Gmail Watcher auto-creates in Needs_Action
move Needs_Action\GMAIL_*.md Pending_Approval\
move Pending_Approval\GMAIL_*.md Pending_Approval\Approved\
# Action Dispatcher auto-moves to Done
```

### LinkedIn Flow
```bash
# You create in Pending_Approval
move Pending_Approval\linkedin_*.md Pending_Approval\Approved\
# LinkedIn poster auto-moves to Done
```

### Sales Lead Flow
```bash
# You create in Inbox
# Run: import_to_odoo.bat
# Auto-moves to Done
```

---

## 🔍 Monitoring & Debugging

### Check Logs

```bash
# Action Dispatcher (Email/LinkedIn execution)
type Logs\action_dispatcher_*.log

# LinkedIn (Posting details)
type Logs\linkedin_*.log

# Gmail Watcher (Inbox monitoring)
type Logs\watcher.log

# Odoo Importer
type Logs\odoo_importer_*.log
```

### Check Dashboard

```bash
type Dashboard.md
```

### Check Done Folder

```bash
# List all done files
dir Done /od

# Count files
dir Done /b | find /c ".md"
```

---

## ⚡ Quick Test Commands

### Test Everything at Once

```bash
# 1. Start watchers
start_gold_tier.bat

# 2. Create test email (send to your Gmail)
# Subject: urgent - Test
# Body: to: test@example.com

# 3. Wait 2 minutes, then move file
move Needs_Action\GMAIL_*.md Pending_Approval\Approved\

# 4. Create LinkedIn post
echo --- > Pending_Approval\test_li.md
echo type: linkedin_post_draft >> Pending_Approval\test_li.md
echo --- >> Pending_Approval\test_li.md
echo ## LinkedIn Post Draft >> Pending_Approval\test_li.md
echo Test post from Gold Tier! >> Pending_Approval\test_li.md
echo #Test >> Pending_Approval\test_li.md

# 5. Move to Approved
move Pending_Approval\test_li.md Pending_Approval\Approved\

# 6. Create sales lead
echo {{"type":"sales_lead","customer_name":"Test","email":"test@test.com"}} > Inbox\test.json

# 7. Import to Odoo
import_to_odoo.bat
```

---

## 🎯 Expected Timeline

| Action | Time |
|--------|------|
| Gmail Watcher detection | 1-2 minutes |
| Action Dispatcher execution | 10-30 seconds |
| Email sending | 5-15 seconds |
| LinkedIn post | 30-60 seconds |
| Odoo import | 2-5 seconds per file |

---

## ✅ Success Checklist

After testing, verify:

- [ ] Gmail Watcher window shows "Checking Gmail..."
- [ ] Action Dispatcher window shows "Monitoring Approved folder..."
- [ ] File appeared in `Needs_Action\` after sending email
- [ ] File moved to `Done\` after approval
- [ ] Email received at destination
- [ ] LinkedIn post visible on your profile
- [ ] Contact created in Odoo
- [ ] Dashboard.md updated with recent activity
- [ ] Logs show successful operations

---

## 🆘 Troubleshooting

### Email Not Sending

**Check:**
```bash
# Verify file has recipient
type Pending_Approval\Approved\GMAIL_*.md

# Should have: to: someone@example.com
```

**Fix:** Edit file and add `to: test@example.com` in frontmatter.

### LinkedIn Not Posting

**Check:**
```bash
# Check logs
type Logs\linkedin_*.log

# Check screenshots
dir debug_linkedin
```

**Fix:** Make sure you're logged into LinkedIn in the browser.

### Odoo Not Connecting

**Check:**
```bash
# Verify Odoo is running
curl http://localhost:8069
```

**Fix:** Start Odoo server first.

---

## 🎉 Full Test Sequence (Copy-Paste)

```bash
# 1. Authorize Gmail
del token.json
python gmail_auth.py

# 2. Start watchers
start_gold_tier.bat

# 3. Send test email to your Gmail (do this manually)
# Subject: urgent - Gold Test
# Body: Please send this to test@example.com

# 4. After 2 minutes, move file
move Needs_Action\GMAIL_*.md Pending_Approval\
move Pending_Approval\GMAIL_*.md Pending_Approval\Approved\

# 5. Wait 30 seconds, check Done folder
dir Done

# 6. Create and approve LinkedIn post
echo --- > Pending_Approval\li_test.md
echo type: linkedin_post_draft >> Pending_Approval\li_test.md
echo created: 2026-03-25 >> Pending_Approval\li_test.md
echo --- >> Pending_Approval\li_test.md
echo ## LinkedIn Post Draft >> Pending_Approval\li_test.md
echo Gold Tier is working! >> Pending_Approval\li_test.md
echo #Automation >> Pending_Approval\li_test.md

move Pending_Approval\li_test.md Pending_Approval\Approved\

# 7. Wait 1 minute, check LinkedIn

# 8. Create and import sales lead
echo {{"type":"sales_lead","customer_name":"Test Customer","email":"test@test.com","product":"AI","amount":50000}} > Inbox\test.json
import_to_odoo.bat

# 9. Check Odoo at http://localhost:8069

# 10. Check all logs
type Logs\action_dispatcher_*.log
type Logs\linkedin_*.log
type Logs\watcher.log
```

---

**Ab test karein aur Gold Tier ka maza lein!** 🚀

Koi error aaye toh logs check karein aur mujhe batayein!
