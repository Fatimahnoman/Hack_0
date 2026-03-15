# LinkedIn Watcher & Auto Poster - Silver Tier

## Quick Start

### Install Dependencies
```bash
pip install playwright
playwright install chromium
```

### Run LinkedIn Watcher (Monitors LinkedIn for messages/notifications)
```bash
cd "F:\heckathon\heckathon 0"
python watchers\linkedin_watcher_fixed.py
```

### Run Auto LinkedIn Poster (Creates drafts from sales leads)
```bash
cd "F:\heckathon\heckathon 0"
python tools\auto_linkedin_poster.py --scan
```

---

## LinkedIn Watcher - Features

| Feature | Description |
|---------|-------------|
| **Persistent Session** | Session saved to `/session/linkedin` |
| **Keywords** | urgent, invoice, payment, sales |
| **Check Interval** | Every 60 seconds |
| **Online Status** | Shown every 30 seconds |
| **Logging** | Logs to `/Logs/watcher.log` |
| **Output** | Creates `.md` files in `/Needs_Action` |
| **Error Handling** | Retry mechanism (3 attempts) |

### Watcher Output Format
Files created in `/Needs_Action`:
```markdown
---
type: linkedin_message
from: John Doe
subject: LinkedIn Message from John Doe
received: 2026-03-07 09:00:00
priority: high
status: pending
watcher: linkedin_watcher
---

# LinkedIn Message

## Sender
**From:** John Doe

## Content
[Message content here...]

---
*Imported by LinkedIn Watcher (Silver Tier)*
```

---

## Auto LinkedIn Poster - Features

| Feature | Description |
|---------|-------------|
| **Scan** | Scans `/Needs_Action` for sales keywords |
| **Keywords** | sales, client, project, lead, opportunity, business |
| **Draft Location** | `/Plans/linkedin_post_[timestamp].md` |
| **Approval** | Moves to `/Pending_Approval` for HITL |
| **Posting** | Via Playwright after approval |
| **Company Rules** | Polite language per `Company_Handbook.md` |

### Commands

```bash
# Scan and create drafts from sales leads
python tools\auto_linkedin_poster.py --scan

# Check pending approvals
python tools\auto_linkedin_poster.py --status

# Post approved draft (after manual approval)
python tools\auto_linkedin_poster.py --post linkedin_post_20260307_090000.md
```

---

## Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Complete LinkedIn Workflow                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. LINKEDIN WATCHER (Continuous Monitoring)                    │
│     └─→ Monitors LinkedIn messages & notifications              │
│     └─→ Detects keywords: urgent, invoice, payment, sales       │
│     └─→ Creates files in /Needs_Action                          │
│                                                                  │
│  2. AUTO LINKEDIN POSTER (Scan & Draft)                         │
│     └─→ Scans /Needs_Action for sales leads                     │
│     └─→ Keywords: sales, client, project, lead, etc.            │
│     └─→ Creates draft post with polite language                 │
│     └─→ Saves to /Plans                                         │
│     └─→ Moves to /Pending_Approval                              │
│                                                                  │
│  3. HITL APPROVAL (Manual Review)                               │
│     └─→ User reviews draft in /Pending_Approval                 │
│     └─→ Edits if needed                                         │
│     └─→ Approves (ready to post)                                │
│                                                                  │
│  4. POST TO LINKEDIN (Automated)                                │
│     └─→ Run: python auto_linkedin_poster.py --post FILE         │
│     └─→ Launches browser with session                           │
│     └─→ Posts to LinkedIn                                       │
│     └─→ Saves confirmation to /Done                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
F:\heckathon\heckathon 0\
├── watchers/
│   └── linkedin_watcher_fixed.py    # Fixed LinkedIn watcher
├── tools/
│   └── auto_linkedin_poster.py      # Auto poster script
├── .claude/skills/
│   └── auto_linkedin_poster.md      # Skill documentation
├── Needs_Action/                    # Incoming files from watcher
├── Plans/                           # Draft posts (initial)
├── Pending_Approval/                # Drafts awaiting HITL
├── Done/                            # Posted confirmations
├── Rejected/                        # Rejected drafts
├── session/
│   └── linkedin/                    # Persistent browser session
├── Logs/
│   ├── watcher.log                  # Watcher activity log
│   └── linkedin_YYYY-MM-DD.log      # Daily poster logs
└── Dashboard.md                     # Updated with pending count
```

---

## Testing

### Test with Sample File
```bash
cd "F:\heckathon\heckathon 0"

# Create test sales lead
echo "---
type: sales_inquiry
---
# Test Sales Lead

We are interested in your professional services for our business project.
Please contact us for more details.
" > Needs_Action\test_lead.md

# Run auto poster
python tools\auto_linkedin_poster.py --scan

# Check pending
python tools\auto_linkedin_poster.py --status

# View created draft
type Pending_Approval\linkedin_post_*.md
```

### Test Watcher (Manual)
1. Run watcher: `python watchers\linkedin_watcher_fixed.py`
2. Login to LinkedIn (first run only)
3. Watcher monitors for 60 seconds
4. Check `Needs_Action` for new files
5. Check `Logs\watcher.log` for activity

---

## Troubleshooting

### Issue: Playwright not installed
```bash
pip install playwright
playwright install chromium
```

### Issue: Session expired
- Delete `session\linkedin` folder
- Re-run watcher/poster
- Login to LinkedIn again

### Issue: Post not publishing
- Ensure you're logged in to LinkedIn
- Check browser is not headless (first run)
- Verify session folder exists

### Issue: Unicode errors on Windows
- Files use UTF-8 encoding
- Console may need: `chcp 65001`

---

## Company Handbook Compliance

Per `Company_Handbook.md`:
- ✅ All posts use polite language
- ✅ All posts require HITL approval
- ✅ Professional tone maintained

---

## Logs

### Watcher Log Location
`F:\heckathon\heckathon 0\Logs\watcher.log`

### Poster Log Location
`F:\heckathon\heckathon 0\Logs\linkedin_YYYY-MM-DD.log`

### Log Format
```
2026-03-07 06:51:39 - INFO - [FOUND] test_sales_lead.md - Keywords: sales, client
2026-03-07 06:51:39 - INFO - [DRAFT] Created: linkedin_post_20260307_065139.md
2026-03-07 06:51:39 - INFO - [MOVED] Draft moved to Pending_Approval
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start watcher | `python watchers\linkedin_watcher_fixed.py` |
| Scan for leads | `python tools\auto_linkedin_poster.py --scan` |
| Check pending | `python tools\auto_linkedin_poster.py --status` |
| Post approved | `python tools\auto_linkedin_poster.py --post FILENAME` |
| View logs | `type Logs\watcher.log` |

---

*LinkedIn Watcher & Auto Poster - Silver Tier - Hackathon 0*
*Version: 1.0 - 2026-03-07*
