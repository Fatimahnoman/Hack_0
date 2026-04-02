# Gold Tier LinkedIn Auto Poster - Quick Reference

## Overview
This is the **production-ready** LinkedIn auto poster for Gold Tier, based on the working Silver Tier code.

## Features
✓ **Persistent Session**: `F:\heckathon\heckathon-0\session\linkedin`
✓ **Slow Typing**: 100ms per character (anti-bot detection)
✓ **Stable Selectors**: Multiple fallback selectors for reliability
✓ **Comprehensive Logging**: All actions logged to `gold/logs/`
✓ **Action Dispatcher Integration**: Auto-posts when files move to Approved folder
✓ **Retry Logic**: 3 retry attempts with increasing delays
✓ **Screenshot Debugging**: Screenshots saved to `debug_linkedin/`

## Installation

```bash
pip install playwright
playwright install chromium
```

## Usage

### 1. Manual Post (Command Line)
```bash
python gold/watchers/linkedin_auto_poster.py --content "Your post text here"
```

### 2. Post from File
```bash
python gold/watchers/linkedin_auto_poster.py --file "path/to/approved_file.md"
```

### 3. Watcher Mode (Monitor LinkedIn)
```bash
python gold/watchers/linkedin_auto_poster.py --watch
```

### 4. Action Dispatcher (Automatic)
```bash
python silver/tools/action_dispatcher.py --daemon --interval 10
```

## File Flow

1. **Create Draft**: File created in `gold/pending_approval/`
2. **Approval**: File moved to `gold/pending_approval/approved/`
3. **Auto Post**: Action Dispatcher detects file and calls LinkedIn poster
4. **Completion**: File moved to `gold/done/` (or `gold/failed/` on error)

## File Format

```markdown
---
type: linkedin_post
status: approved
---

## LinkedIn Post Draft

Your post content goes here...

```

## Directories

| Directory | Purpose |
|-----------|---------|
| `session/linkedin/` | Persistent browser session |
| `gold/pending_approval/approved/` | Files waiting to be posted |
| `gold/done/` | Successfully posted files |
| `gold/failed/` | Failed posts with reason |
| `gold/logs/` | Execution logs |
| `debug_linkedin/` | Screenshots for debugging |

## Troubleshooting

### Browser doesn't launch
```bash
pip install --upgrade playwright
playwright install chromium
```

### Login required every time
- Check `session/linkedin/` folder exists
- Don't clear browser cookies
- First run requires manual login

### Post button not found
- Check screenshots in `debug_linkedin/`
- Review logs in `gold/logs/`
- LinkedIn may have updated UI

### Session locked errors
- Wait 10 seconds for automatic retry
- Check no other process is using LinkedIn
- Delete `session/whatsapp.lock` if stale

## Testing

### Test Connection
```bash
python gold/watchers/linkedin_auto_poster.py --content "Test post - ignore"
```

### Test with Debug
```bash
python gold/watchers/linkedin_auto_poster.py --file "test_file.md"
```

### Full Workflow Test
1. Create file in `gold/pending_approval/`
2. Move to `gold/pending_approval/approved/`
3. Start Action Dispatcher
4. Check `gold/done/` for completed file

## Logs

All activity is logged to:
- `gold/logs/linkedin_gold_YYYYMMDD_HHMMSS.log`
- `gold/logs/action_dispatcher_YYYYMMDD.log`

Check logs for:
- ✓ Success messages
- ⚠ Warnings
- ✗ Errors
- Screenshot locations

## Action Dispatcher Integration

The Action Dispatcher automatically calls this script when:
1. File appears in `gold/pending_approval/approved/`
2. File type contains "linkedin" or "linkedin_post"
3. No session lock is active

**Script Priority:**
1. `gold/watchers/linkedin_auto_poster.py` (Primary)
2. `watchers/linkedin_auto_poster_production.py` (Fallback)
3. `watchers/linkedin_auto_poster_fixed.py` (Legacy)

## Session Management

**Persistent Session Path:**
```
F:\heckathon\heckathon-0\session\linkedin
```

**First Run:**
- Browser launches in visible mode
- Manual login required
- Session saved for future runs

**Subsequent Runs:**
- Uses saved session
- Should auto-login
- Faster execution

## Performance

| Metric | Value |
|--------|-------|
| Typing Speed | 100ms/char |
| Max Retries | 3 |
| Retry Delay | 10-20s |
| Post Timeout | 12 minutes |
| Check Interval (Daemon) | 10 seconds |

## Author & Version

- **Based on:** Silver Tier `linkedin_watcher.py`
- **Version:** 2.0 (Gold Tier)
- **Date:** 2026-03-31
- **Integration:** Action Dispatcher compatible

---

## Quick Start

```bash
# 1. Install dependencies
pip install playwright
playwright install chromium

# 2. Test manual post
python gold/watchers/linkedin_auto_poster.py --content "Hello from Gold Tier!"

# 3. Start auto-posting daemon
python silver/tools/action_dispatcher.py --daemon --interval 10
```

**That's it!** Files moved to `approved/` will auto-post to LinkedIn.
