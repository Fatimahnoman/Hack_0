# 🚀 GOLD TIER - QUICK RESTART GUIDE

## ✅ Fixes Applied

1. **Session Folders Cleaned** - Purane corrupt sessions delete ho gaye
2. **WhatsApp Watcher Fixed** - Better scanning + keyword detection
3. **LinkedIn Auto Poster Fixed** - Better post submission
4. **Chrome Browser** - Proper session management

---

## ▶️ RESTART PROCEDURE

### Step 1: Close All Running Windows
Sabhi watcher windows close karein (Ctrl+C)

### Step 2: Run Start Script
```bash
.\start_gold_tier.bat
```

---

## 📊 WHAT TO EXPECT

### Windows Open (6):
1. **Gold Orchestrator** - AI Brain
2. **Action Dispatcher** - Executor
3. **WhatsApp Watcher** - Chrome browser (QR scan if needed)
4. **Gmail Watcher** - API (no browser)
5. **LinkedIn Watcher** - Chrome browser (login if needed)
6. **LinkedIn Auto Poster** - Chrome browser

### Browsers:
- **WhatsApp Web** - QR code scan karein (if not logged in)
- **LinkedIn** - Login karein (if not logged in)
- **KEEP BOTH OPEN** - Don't close!

---

## 🧪 TEST 1: LINKEDIN AUTO POST

### Already Ready:
File in `gold/pending_approval/approved/`:
```
LINKEDIN_Test_Post_20260330_053000.md
```

### Expected Flow:
1. LinkedIn Auto Poster detect karega (within 30 seconds)
2. Chrome khulega
3. LinkedIn feed open hoga
4. "Start a post" click hoga
5. Post type hoga
6. Post submit hoga
7. File move hogi `gold/done/` mein

### Success Indicators:
- ✅ "POST PUBLISHED" in logs
- ✅ File in `gold/done/`
- ✅ Post visible on LinkedIn profile

---

## 🧪 TEST 2: WHATSAPP MESSAGE TRACKING

### Test Message Bhejein:
Apne WhatsApp se kisi contact ko bhejein:
```
Hi, I need urgent help with payment
```

Ya phir test file already hai:
```
gold/needs_action/WHATSAPP_Test_Customer_20260330_053001.md
```

### Expected Flow:
1. WhatsApp Watcher scan karega (every 30 seconds)
2. Keyword detect hoga ("urgent", "payment")
3. File create hogi in `gold/needs_action/`
4. Gold Orchestrator detect karega
5. Draft create hoga in `gold/pending_approval/`
6. Aap manually approve karein (move to approved folder)
7. WhatsApp Sender execute karega

### Success Indicators:
- ✅ "KEYWORDS FOUND" in WhatsApp logs
- ✅ File in `gold/needs_action/`
- ✅ Draft in `gold/pending_approval/`

---

## 📋 MONITORING

### Check Logs:
```bash
# Open logs folder
explorer gold\logs

# WhatsApp (real-time)
type gold\logs\whatsapp_*.log

# LinkedIn (real-time)
type gold\logs\linkedin_*.log

# Orchestrator
type gold\logs\gold_orchestrator_*.log
```

### Check Folders:
```bash
# New tasks (should see files from WhatsApp)
dir gold\needs_action

# Drafts awaiting approval
dir gold\pending_approval

# Approved (ready to execute)
dir gold\pending_approval\approved

# Completed
dir gold\done
```

---

## 🛠️ TROUBLESHOOTING

### WhatsApp Not Detecting Keywords:

**Check logs:**
```
[DEBUG] 💬 Contact: Message text...
```

Agar messages dikh rahe hain lekin keywords nahi detect ho rahe:
- Messages mein yeh words hone chahiye:
  ```
  urgent, sales, payment, invoice, deal, order,
  client, customer, quotation, proposal, overdue,
  follow up, meeting, booking, asap, test, hi,
  hello, paid, receive, price, cost, help, service
  ```

### LinkedIn Post Not Submitting:

**Check screenshots:**
```
debug_linkedin\
```

**Common issues:**
1. Not logged in → Login manually
2. Modal not opening → Refresh page
3. Post button not found → Wait for page to load

### Browser Crashes (Exit Code 21):

**Solution:**
```bash
# Kill all Chrome
taskkill /F /IM chrome.exe

# Clean sessions
rmdir /s /q session\whatsapp_chrome
rmdir /s /q session\linkedin_chrome

# Restart
.\start_gold_tier.bat
```

---

## ✅ SUCCESS CHECKLIST

### LinkedIn:
- [ ] LinkedIn Auto Poster window shows "Starting..."
- [ ] Chrome opens LinkedIn
- [ ] Post is typed automatically
- [ ] Post button is clicked
- [ ] "POST PUBLISHED" in logs
- [ ] File in `gold/done/`
- [ ] Post visible on LinkedIn

### WhatsApp:
- [ ] WhatsApp Watcher shows "Scanned X chats"
- [ ] Test message contains keywords
- [ ] "KEYWORDS FOUND" in logs
- [ ] File created in `gold/needs_action/`
- [ ] Draft created by Orchestrator
- [ ] After approval, WhatsApp Sender runs

---

## 🎯 KEYBOARD SHORTCUTS

### Stop Individual Watcher:
1. Click on its window
2. Press `Ctrl+C`

### Restart All:
```bash
.\start_gold_tier.bat
```

### Quick Test LinkedIn:
```bash
python watchers\linkedin_auto_poster_fixed.py --content "Test post from Gold Tier! #automation"
```

### Quick Test WhatsApp:
```bash
python watchers\whatsapp_watcher_fixed.py
```

---

## 📞 SUPPORT

### Log Files:
```
gold/logs/whatsapp_20260330.log
gold/logs/linkedin_20260330.log
gold/logs/gold_orchestrator_20260330.log
gold/logs/action_dispatcher_20260330.log
```

### Debug Screenshots:
```
debug_linkedin/
```

### Session Folders:
```
session/whatsapp_chrome/
session/linkedin_chrome/
```

---

## 🎉 READY TO TEST!

**Ab yeh karein:**

1. ✅ Sab windows close karein
2. ✅ Run karein: `.\start_gold_tier.bat`
3. ✅ Browsers mein login karein
4. ✅ Logs monitor karein
5. ✅ Mujhe results batayein!

**Let's go! 🚀**
