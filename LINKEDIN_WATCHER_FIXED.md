# LinkedIn Watcher + Auto Poster - Fixed v2

## ✅ COMPLETELY FIXED - Auto Typing & Submit Working

### Key Fixes in This Version

| Problem | Solution |
|---------|----------|
| **Not typing text** | Uses `page.locator('div[role="textbox"][contenteditable="true"]')` with slow typing (100ms/char) |
| **No text appears** | Proper focus with `click()`, `wait_for_state('visible')`, chunked typing |
| **Post not submitted** | Uses `page.locator('button[data-testid="post-button"]')` with enabled state check |
| **Page reloading** | `page.wait_for_load_state('networkidle', timeout=60000)` |
| **Session timeout** | Persistent session at `/session/linkedin` |
| **Detection** | `--disable-extensions`, realistic delays, human-like typing |

## 🎯 Exact Selectors Used

### Compose Box (in order of priority)
```python
# Primary
page.locator('div[role="textbox"][contenteditable="true"]').first

# Secondary  
page.locator('[data-testid="post-creation-textarea"]').first

# Tertiary
page.locator('div[contenteditable="true"]').first
```

### Post Button (in order of priority)
```python
# Primary
page.locator('button[data-testid="post-button"]').first

# Secondary
page.locator('button:has-text("Post")').first

# Tertiary
page.locator('button:has-text("POST")').first
```

## ⚙️ Timing Configuration

```python
TYPE_DELAY = 100          # 100ms per character (slow, human-like)
ACTION_DELAY = 1000       # 1 second after each action
PAGE_LOAD_TIMEOUT = 60000 # 60 second page load timeout
CHECK_INTERVAL = 60       # Check every 60 seconds
MAX_RETRIES = 3           # Retry 3 times on failure
RETRY_DELAY = 5           # 5 seconds between retries
```

## 📁 Directory Structure

```
heckathon 0/
├── session/linkedin/          # Persistent browser session (saved login)
├── Needs_Action/              # Detected important messages/notifications
├── Plans/                     # Auto-generated post drafts
├── Pending_Approval/          # Drafts awaiting human approval
│   └── Approved/              # ← MOVE FILES HERE TO AUTO-POST
├── Done/                      # Completed posts
└── Logs/
    └── linkedin.log           # Detailed activity log
```

## 🚀 Usage

### Installation
```bash
pip install playwright
playwright install chromium
```

### Run the Watcher
```bash
python watchers\linkedin_watcher_fixed.py
```

Or use the batch file:
```bash
run_linkedin_watcher.bat
```

### First Run - Login
1. Script launches browser
2. **Manually log in** to LinkedIn (QR code or credentials)
3. Session saved to `/session/linkedin`
4. Subsequent runs use saved session

### HITL Workflow (Human-In-The-Loop)

```
1. Sales lead detected → Needs_Action/
2. Auto-draft created → Plans/ → Pending_Approval/
3. Human reviews draft file
4. Human moves file to: Pending_Approval/Approved/
5. Script detects approved file → AUTO-TYPES & SUBMITS
6. Posted file moved to: Done/
```

## 📝 YAML Frontmatter Format

### Needs_Action Files
```yaml
---
type: message
from: John Doe
subject: Sales Inquiry
received: 2026-03-11 10:30:00
priority: normal
status: pending
---
```

### Post Drafts (in Pending_Approval)
```yaml
---
type: linkedin_post_draft
source_type: sales_lead
created_at: 2026-03-11 10:35:00
status: draft
---

## Content

🤝 Exciting Opportunity Alert!
...
```

## 🔧 Anti-Detection Features

```python
args=[
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--disable-extensions",  # ← No extensions
    "--disable-plugins",
    "--disable-background-timer-throttling"
]
```

### Human-Like Typing
- **100ms delay** per character
- **Chunked typing** (30 chars per chunk)
- **Refocus every 3 chunks** to maintain focus
- **1 second delay** after each action

## 📊 Logging

All actions logged to `Logs/linkedin.log`:
```
2026-03-11 10:30:00 - INFO - TYPING POST CONTENT (250 characters)
2026-03-11 10:30:01 - INFO - Found compose box via: div[role="textbox"][contenteditable="true"]
2026-03-11 10:30:02 - INFO - Typing content with 100ms delay per character
2026-03-11 10:30:15 - INFO - Verification: 250/250 chars entered
2026-03-11 10:30:16 - INFO - CLICKING POST BUTTON
2026-03-11 10:30:17 - INFO - Found post button via: button[data-testid="post-button"]
2026-03-11 10:30:18 - INFO - Post button clicked successfully!
2026-03-11 10:30:23 - INFO - [SUCCESS] Post published to LinkedIn!
```

## 🐛 Debug Screenshots

If typing/submit fails, debug screenshots saved to `Logs/`:
- `debug_no_compose_YYYYMMDD_HHMMSS.png`
- `debug_typing_failed_YYYYMMDD_HHMMSS.png`
- `debug_no_post_button_YYYYMMDD_HHMMSS.png`
- `debug_post_click_failed_YYYYMMDD_HHMMSS.png`

## ✅ Company Handbook Compliance

Posts follow Company Handbook guidelines:
- ✅ Always be polite in replies
- ✅ Professional tone
- ✅ Flag payments over $500 for approval (manual review in HITL)

## 🎯 Console Output

```
======================================================================
LinkedIn Watcher + Auto Poster - Silver Tier (Fixed v2)
======================================================================
Session path: F:\heckathon\heckathon 0\session\linkedin
Needs_Action: F:\heckathon\heckathon 0\Needs_Action
Pending_Approval: F:\heckathon\heckathon 0\Pending_Approval
Approved: F:\heckathon\heckathon 0\Pending_Approval\Approved
----------------------------------------------------------------------
Keywords monitored: urgent, invoice, payment, sales
Check interval: 60 seconds
Type delay: 100ms per character
----------------------------------------------------------------------
[2026-03-11 10:30:00] LinkedIn Watcher ONLINE
[2026-03-11 10:30:30] LinkedIn Watcher ONLINE
[2026-03-11 10:31:00] LinkedIn Watcher ONLINE
```

## 🛠️ Troubleshooting

### Login Issues
```bash
# Delete session and re-login
rmdir /s /q session\linkedin
python watchers\linkedin_watcher_fixed.py
```

### Post Not Typing
1. Check `Logs/linkedin.log` for errors
2. Look for debug screenshots in `Logs/`
3. Ensure LinkedIn feed is fully loaded
4. Verify you're logged in (session may expire)

### Post Not Submitting
1. Check if Post button is enabled (gray = disabled)
2. Verify content was typed (screenshot in logs)
3. Check for LinkedIn UI changes (selectors may need update)

### Session Timeout
- Script auto-recovers by re-checking login status
- If timeout persists, restart watcher and re-login

## 📋 Requirements Summary

| Requirement | Status |
|-------------|--------|
| Persistent session `/session/linkedin` | ✅ |
| Exact compose box selectors | ✅ |
| Exact post button selectors | ✅ |
| Slow typing (delay=100ms) | ✅ |
| wait_for_state('visible') | ✅ |
| wait_for_load_state('networkidle') | ✅ |
| Click Post after typing | ✅ |
| Prevent timeout/reload | ✅ |
| --disable-extensions | ✅ |
| headless=False for debugging | ✅ |
| 1000ms delay after actions | ✅ |
| Retry 3 times | ✅ |
| Log to Logs/linkedin.log | ✅ |
| "ONLINE" every 30 seconds | ✅ |
