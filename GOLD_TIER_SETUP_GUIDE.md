# GOLD TIER - COMPLETE SETUP & USER GUIDE

## ✅ Fixed Issues

### 1. Email "Missing recipient or subject" - FIXED
- **Problem:** Email files were missing `to` or `subject` fields
- **Solution:** Added automatic field extraction with fallbacks
  - Extracts recipient from multiple possible fields (`to`, `recipient`, `recipients`)
  - Extracts subject from metadata or generates one if missing
  - Tries to extract email from content body if not in metadata
  - Clear error logging shows what fields were found

### 2. LinkedIn Post Timeout - FIXED
- **Problem:** Posts were timing out after 5 minutes
- **Solution:** 
  - Increased timeout to 10 minutes (600 seconds)
  - Slow typing with 100ms delay per character
  - Multiple retry attempts (3 times with 5s delay)
  - Stable selectors with fallbacks
  - Proper focus before typing
  - Wait states after each action

---

## 📁 Folder Structure

```
heckathon-0/
├── Needs_Action/          # New items from Gmail/WhatsApp
├── Pending_Approval/      # Items awaiting approval
│   └── Approved/          # Approved items ready for action
├── Done/                  # Completed items
├── Logs/                  # All watcher logs
├── Inbox/                 # Odoo import files (JSON)
└── [scripts below]
```

---

## 🚀 QUICK START

### Step 1: Install Dependencies

```bash
# Core dependencies
pip install watchdog google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

# LinkedIn automation
pip install playwright
playwright install chromium
```

### Step 2: Setup Credentials

**Gmail OAuth:**
```bash
python gmail_auth.py
```
Follow the prompts to authorize Gmail access.

**LinkedIn:**
- Login will be handled automatically when LinkedIn poster runs
- Session is saved in `session/linkedin/`

### Step 3: Start All Watchers

```bash
start_gold_tier.bat
```

This opens 5 windows:
1. **Action Dispatcher** - Monitors Approved folder
2. **LinkedIn Auto Poster** - Auto-posts to LinkedIn
3. **Gmail Watcher** - Monitors Gmail inbox
4. **WhatsApp Watcher** - Monitors WhatsApp
5. **Odoo Inbox Importer** - One-time import

---

## 📝 COMPLETE WORKFLOW

### Flow 1: Email → Needs_Action → Approved → Sent

```
1. Gmail Watcher detects important email
   ↓
2. Creates file in Needs_Action/
   (e.g., GMAIL_urgent_20260325_123456.md)
   ↓
3. Move to Pending_Approval/ for review
   ↓
4. Move to Pending_Approval/Approved/
   ↓
5. Action Dispatcher detects file
   ↓
6. Extracts: to, subject, body, cc, bcc
   ↓
7. Sends via Gmail API
   ↓
8. Moves to Done/
```

**Email File Format:**
```markdown
---
type: email
to: client@example.com
subject: Important Update
cc: manager@example.com
from: me@company.com
---

## Email Content

Dear Client,

This is the email body...

---
*Imported by Gmail Watcher*
```

---

### Flow 2: LinkedIn Post → Approved → Posted

```
1. Create draft in Pending_Approval/
   (or auto-generated from sales lead)
   ↓
2. Move to Pending_Approval/Approved/
   ↓
3. LinkedIn Auto Poster detects file
   ↓
4. Opens browser, logs in (if needed)
   ↓
5. Clicks "Start a post"
   ↓
6. Types content (100ms/char)
   ↓
7. Clicks "Post" button
   ↓
8. Moves to Done/
```

**LinkedIn Post File Format:**
```markdown
---
type: linkedin_post_draft
source: sales_lead.md
created: 2026-03-25 19:15:53
status: pending_approval
---

## LinkedIn Post Draft

[LAUNCH] Excited to announce our new service!
Professional delivery with quality results.

#Business #Professional #Services

---
*Draft created by AI Employee*
```

---

### Flow 3: Sales Lead → Odoo CRM

```
1. JSON file in Inbox/
   ↓
2. Run: import_to_odoo.bat
   ↓
3. Creates Contact in Odoo
   ↓
4. Creates CRM Lead in Odoo
   ↓
5. Moves to Done/
```

**Sales Lead JSON Format:**
```json
{
  "type": "sales_lead",
  "customer_name": "John Doe",
  "email": "john@example.com",
  "phone": "+923001234567",
  "product": "Software Development",
  "amount": 50000,
  "currency": "PKR",
  "notes": "Interested in custom CRM solution"
}
```

---

## 🔧 TROUBLESHOOTING

### Email Not Sending

**Error:** "Missing recipient or subject"

**Solution:**
1. Check file has `to:` field in frontmatter
2. Check file has `subject:` field
3. Run Action Dispatcher with verbose logging:
   ```bash
   python silver/tools/action_dispatcher.py --once
   ```

**Error:** "OAuth failed"

**Solution:**
```bash
# Re-authorize Gmail
python gmail_auth.py
# Delete old token
del token.json
# Run again
```

---

### LinkedIn Post Failing

**Error:** "Post timed out"

**Solution:**
1. Check browser is not minimized
2. Ensure you're logged into LinkedIn
3. Check logs: `Logs/linkedin_*.log`
4. Check screenshots: `debug_linkedin/`

**Error:** "Could not find compose box"

**Solution:**
1. LinkedIn may have updated UI
2. Check `debug_linkedin/` screenshots
3. Run manual test:
   ```bash
   python watchers/linkedin_auto_poster_fixed.py --content "Test post"
   ```

**Error:** "Not logged in"

**Solution:**
- Browser will open and wait 2 minutes for manual login
- Login in the browser window
- Script will continue automatically

---

### Odoo Import Failing

**Error:** "Cannot connect to Odoo"

**Solution:**
1. Check Odoo is running: `http://localhost:8069`
2. Verify credentials:
   ```bash
   set ODOO_USERNAME=admin
   set ODOO_PASSWORD=admin
   set ODOO_DB=odoo
   ```
3. Check logs: `Logs/odoo_importer_*.log`

---

## 📊 MONITORING

### Check Logs

```bash
# Action Dispatcher
type Logs\action_dispatcher_*.log

# LinkedIn
type Logs\linkedin_*.log

# Gmail
type Logs\watcher.log

# Odoo
type Logs\odoo_importer_*.log
```

### Check Dashboard

```bash
type Dashboard.md
```

### Check Done Folder

```bash
dir Done /od
```

---

## ⚙️ CONFIGURATION

### Environment Variables

```bash
# Odoo
set ODOO_URL=http://localhost:8069
set ODOO_DB=odoo
set ODOO_USERNAME=admin
set ODOO_PASSWORD=admin

# Gmail (via credentials.json)
# LinkedIn (via browser session)
```

### Script Options

**Action Dispatcher:**
```bash
# Daemon mode (continuous)
python silver/tools/action_dispatcher.py --daemon --interval 10

# Run once
python silver/tools/action_dispatcher.py --once
```

**LinkedIn Auto Poster:**
```bash
# Direct content
python watchers/linkedin_auto_poster_fixed.py --content "Your post here"

# Specific file
python watchers/linkedin_auto_poster_fixed.py --file "path\to\file.md"

# Daemon mode
python watchers/linkedin_auto_poster_fixed.py --daemon

# Headless (no browser UI)
python watchers/linkedin_auto_poster_fixed.py --headless
```

---

## 🎯 TESTING

### Test Email Sending

1. Create test file in `Pending_Approval/Approved/`:
   ```markdown
   ---
   type: email
   to: test@example.com
   subject: Test Email
   ---
   
   ## Email Content
   
   This is a test email.
   ```

2. Run Action Dispatcher:
   ```bash
   python silver/tools/action_dispatcher.py --once
   ```

3. Check `Done/` folder and recipient inbox

---

### Test LinkedIn Post

1. Create test file:
   ```markdown
   ---
   type: linkedin_post_draft
   ---
   
   ## LinkedIn Post Draft
   
   Test post from Gold Tier automation!
   
   #Test #Automation
   ```

2. Move to `Pending_Approval/Approved/`

3. Run LinkedIn poster:
   ```bash
   python watchers/linkedin_auto_poster_fixed.py
   ```

4. Check LinkedIn profile for post

---

### Test Odoo Import

1. Create test JSON in `Inbox/`:
   ```json
   {
     "type": "sales_lead",
     "customer_name": "Test Customer",
     "email": "test@example.com",
     "phone": "1234567890",
     "product": "Test Product",
     "amount": 10000
   }
   ```

2. Run importer:
   ```bash
   import_to_odoo.bat
   ```

3. Check Odoo Contacts and CRM

---

## 📈 PERFORMANCE

### Expected Timings

| Action | Expected Time |
|--------|--------------|
| Email send | 5-15 seconds |
| LinkedIn post | 30-60 seconds |
| Odoo import (per file) | 2-5 seconds |
| Action Dispatcher check | Every 10 seconds |

### Retry Logic

| Component | Retries | Delay |
|-----------|---------|-------|
| Email send | 3 | 2s, 4s, 6s |
| LinkedIn typing | 3 | 5s |
| LinkedIn click | 3 | 5s |
| Odoo connect | 3 | 2s, 4s, 6s |

---

## 🔐 SECURITY

### Credentials

- **Gmail:** Stored in `credentials.json` and `token.json`
- **Odoo:** Use environment variables
- **LinkedIn:** Browser session in `session/linkedin/`

### Best Practices

1. Never commit `credentials.json` or `token.json` to git
2. Use `.gitignore` for sensitive files
3. Rotate OAuth credentials periodically
4. Use separate Odoo user for automation

---

## 📞 SUPPORT

### Logs Location

```
Logs/
├── action_dispatcher_20260325.log
├── linkedin_20260325.log
├── watcher.log (Gmail)
└── odoo_importer_20260325.log
```

### Debug Screenshots

```
debug_linkedin/
├── feed_loaded_*.png
├── modal_opened_*.png
├── content_typed_*.png
└── post_submitted_*.png
```

### Common Issues

| Issue | Log File | Solution |
|-------|----------|----------|
| Email not sending | action_dispatcher_*.log | Check recipient field |
| LinkedIn timeout | linkedin_*.log | Check debug screenshots |
| Odoo connection | odoo_importer_*.log | Verify credentials |

---

## ✅ VERIFICATION CHECKLIST

After setup, verify:

- [ ] Gmail OAuth authorized (`token.json` exists)
- [ ] LinkedIn session saved (`session/linkedin/` exists)
- [ ] Odoo connection working (run `import_to_odoo.bat`)
- [ ] Action Dispatcher running (check logs)
- [ ] Files moving to Done folder
- [ ] Dashboard updating
- [ ] Logs being written

---

## 🎉 SUCCESS INDICATORS

You'll know it's working when:

1. ✅ New files appear in `Needs_Action/` from Gmail
2. ✅ Approved files disappear from `Pending_Approval/Approved/`
3. ✅ Files appear in `Done/` with `processed_` prefix
4. ✅ LinkedIn posts appear on your profile
5. ✅ Emails arrive in recipient inbox
6. ✅ Contacts appear in Odoo
7. ✅ Dashboard.md shows recent activity

---

**Gold Tier is now production-ready! 🚀**
