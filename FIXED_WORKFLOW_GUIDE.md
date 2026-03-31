# AI Employee - FIXED Workflow Guide

## Overview
Complete fix for AI Employee automation with proper workflow enforcement.

## Workflow (FIXED)

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌──────────┐     ┌──────┐
│  WATCHERS   │────▶│ Needs_Action │────▶│ Pending_Approval │────▶│ Approved │────▶│ Done │
│  (Eyes)     │     │              │     │  (Drafts)        │     │          │     │      │
└─────────────┘     └──────────────┘     └──────────────────┘     └──────────┘     └──────┘
      │                    │                      │                     │              │
      │                    │                      │                     │              │
      ▼                    ▼                      ▼                     ▼              ▼
- Gmail              - Files created       - Gold Orchestrator   - Human       - Executed
- WhatsApp             with keywords         creates drafts        reviews       by Action
- LinkedIn           - Keyword filter:     - Draft includes      - Move to     Dispatcher
- Twitter              urgent, sales,        reply draft +         Approved
                         payment, etc.         action plan
```

## Keywords Enforced (ALL Watchers)

**ALL** watchers now filter messages by these keywords:

1. **urgent**
2. **sales**
3. **payment**
4. **invoice**
5. **deal**
6. **order**
7. **client**
8. **customer**
9. **quotation**
10. **proposal**
11. **overdue**
12. **follow up**
13. **meeting**
14. **booking**
15. **asap**

Only messages containing these keywords will be processed.

## Components

### 1. Gmail Watcher (`watchers/gmail_watcher_browser.py`)
- **Fixed Issues:**
  - Inbox loading properly with wait states
  - Better login detection
  - Screenshot debugging enabled
  - Proper keyword filtering

- **Features:**
  - Visible browser (headless=False)
  - Persistent session (login once)
  - Takes screenshots for debugging
  - Creates files in Needs_Action with keywords only

### 2. WhatsApp Watcher (`watchers/whatsapp_watcher_fixed.py`)
- **Status:** Already working correctly
- **Features:**
  - Monitors WhatsApp Web
  - Filters by keywords
  - Creates files in Needs_Action

### 3. LinkedIn Watcher (`watchers/linkedin_watcher_fixed.py`)
- **Fixed Issues:**
  - Enhanced "Start a post" selectors (10+ fallbacks)
  - Better post button clicking
  - Screenshot debugging for every step
  - Post publication verification

- **Features:**
  - Monitors LinkedIn notifications and messages
  - Auto-posts to LinkedIn when draft approved
  - Takes screenshots at each step

### 4. Gold Orchestrator (`gold/tools/gold_orchestrator.py`)
- **Fixed Issues:**
  - Files ONLY move to Done AFTER draft creation
  - Robust error logging for Claude CLI
  - Validates AI response has required fields
  - Returns boolean from `_handle_ai_response()`

- **Features:**
  - Watches Needs_Action folder
  - Calls Claude AI to generate reply drafts
  - Creates drafts in Pending_Approval
  - Moves original to Done only after successful draft creation

### 5. Action Dispatcher (`silver/tools/action_dispatcher.py`)
- **Status:** Working correctly
- **Features:**
  - Monitors Pending_Approval/Approved folder
  - Executes LinkedIn posts, emails, WhatsApp messages
  - Moves completed actions to Done

## How to Use

### Quick Start

1. **Run the fixed startup script:**
   ```batch
   start_fixed_ai_employee.bat
   ```

2. **All components will start:**
   - Gmail Watcher (green window)
   - WhatsApp Watcher (cyan window)
   - LinkedIn Watcher (red window)
   - Gold Orchestrator (yellow window)
   - Action Dispatcher (purple window)

3. **Login to accounts:**
   - Gmail: Login when browser opens
   - WhatsApp: Scan QR code if first time
   - LinkedIn: Login if not already logged in

4. **Monitor logs:**
   - Check `Logs/` folder for detailed logs
   - Check `debug_gmail/` and `debug_linkedin/` for screenshots

### Testing the Workflow

1. **Run the test script:**
   ```batch
   python test_complete_workflow.py
   ```

2. **What it does:**
   - Creates test files in Needs_Action with keywords
   - Waits for Gold Orchestrator to process
   - Verifies drafts are created in Pending_Approval
   - Verifies files move to Done

## Debugging

### Screenshot Locations

- **Gmail:** `debug_gmail/` folder
  - `initial_navigation_*.png` - First page load
  - `login_step_*.png` - Login process
  - `inbox_loaded_success_*.png` - Inbox loaded
  - `important_email_found_*.png` - Email with keywords found

- **LinkedIn:** `debug_linkedin/` folder
  - `01_initial_navigation_*.png` - Feed loaded
  - `05_logged_in_feed_*.png` - After login
  - `06_post_button_clicked_*.png` - Start a post clicked
  - `08_compose_modal_opened_*.png` - Compose box open
  - `10_content_typed_*.png` - Content typed
  - `12_post_button_clicked_*.png` - Post button clicked
  - `13_final_result_*.png` - Final result

### Log Files

- `Logs/gold_orchestrator_*.log` - Gold Orchestrator logs
- `Logs/action_dispatcher_*.log` - Action Dispatcher logs
- `Logs/watcher.log` - WhatsApp watcher logs
- `Logs/linkedin.log` - LinkedIn watcher logs

### Common Issues

#### 1. Files going directly to Done without drafts
**Cause:** Gold Orchestrator not running or Claude not available
**Fix:** 
- Make sure Gold Orchestrator is running
- Check `claude.cmd` is available
- Check Logs for errors

#### 2. Gmail inbox not loading
**Cause:** Login issue or slow connection
**Fix:**
- Check screenshots in `debug_gmail/`
- Manually login in the browser
- Restart Gmail watcher

#### 3. LinkedIn post not publishing
**Cause:** Selector issue or network problem
**Fix:**
- Check screenshots in `debug_linkedin/`
- Verify you're logged into LinkedIn
- Check if post button is visible

#### 4. No files in Needs_Action
**Cause:** Messages don't have keywords
**Fix:**
- Send test messages with keywords (urgent, payment, etc.)
- Check watcher logs to see what's being detected

## File Structure

```
heckathon 0/
├── Needs_Action/          # Watchers create files here
├── Pending_Approval/      # Gold Orchestrator creates drafts here
│   └── Approved/          # Human moves approved drafts here
├── Done/                  # Completed files
├── Plans/                 # Action plans created by AI
├── Logs/                  # Log files
├── debug_gmail/           # Gmail screenshots
├── debug_linkedin/        # LinkedIn screenshots
├── watchers/              # Watcher scripts
├── gold/tools/            # Gold Orchestrator
├── silver/tools/          # Action Dispatcher
├── start_fixed_ai_employee.bat
└── test_complete_workflow.py
```

## What Was Fixed

### Bug 1: Workflow Violation
**Problem:** Files disappearing from Needs_Action to Done without drafts
**Fix:** 
- `_handle_ai_response()` now returns boolean
- Files only move to Done if draft creation succeeds
- Failed files go to Failed folder instead

### Bug 2: LinkedIn Crash Loop
**Problem:** "Start a post" button not found, browser restarting
**Fix:**
- 10+ fallback selectors
- Better error handling
- Screenshot debugging
- Post publication verification

### Bug 3: Gmail Inbox Not Loading
**Problem:** Inbox not fully loaded error
**Fix:**
- `wait_for_inbox_load()` function
- Better wait states
- Screenshot debugging
- Multiple selector attempts

### Bug 4: Keyword Enforcement
**Problem:** Not all watchers using full keyword list
**Fix:**
- All watchers now use same 15 keywords
- Consistent filtering across platforms

## Next Steps

1. **Run the startup script:** `start_fixed_ai_employee.bat`
2. **Login to all accounts** when browsers open
3. **Send test messages** with keywords to test platforms
4. **Monitor logs and screenshots** for debugging
5. **Review drafts** in Pending_Approval folder
6. **Move approved drafts** to Pending_Approval/Approved
7. **Action Dispatcher** will execute automatically

## Support

If issues persist:
1. Check all log files in `Logs/` folder
2. Review screenshots in `debug_gmail/` and `debug_linkedin/`
3. Run `test_complete_workflow.py` to isolate issues
4. Verify Python and dependencies are installed:
   ```bash
   pip install playwright watchdog
   playwright install chromium
   ```
