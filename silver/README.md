# Silver Tier - AI Employee Implementation

Complete implementation of the Silver Tier with autonomous task processing, human-in-the-loop approval, and multi-platform execution.

## Overview

The Silver Tier extends the Bronze Tier with external integrations (Gmail, WhatsApp, LinkedIn) and introduces the complete autonomy loop:

```
Watcher (Inbox) → AI Agent (Needs_Action) → Draft (Pending_Approval) 
→ Human Moves to 'Approved' → System Executes Action → Done
```

## Architecture

### The Eyes (Watchers)
- **Gmail Watcher** - Monitors Gmail for important emails (keywords: urgent, invoice, payment, sales)
- **WhatsApp Watcher** - Monitors WhatsApp Web for important messages
- **LinkedIn Watcher** - Monitors LinkedIn for messages and notifications

### The Brain (Ralph Wiggum Loop)
- **Ralph Loop Runner** - Analyzes tasks, creates plans, routes to approval
- Runs continuously in daemon mode (60-second check interval)
- Triggers Action Dispatcher for approved files

### The Hands (Action Dispatcher)
- **Action Dispatcher** - Executes approved actions
- LinkedIn posts → Calls `li_post.py`
- Email drafts → Uses Gmail API to send
- Tweets → Uses Twitter MCP
- Facebook/Instagram → Uses Meta Graph API
- Runs continuously in daemon mode (10-second check interval)

### The Memory (File System)
- **Inbox/** - New incoming files/tasks
- **Needs_Action/** - Items requiring AI processing
- **Plans/** - Draft plans and posts
- **Pending_Approval/** - Awaiting human review
- **Pending_Approval/Approved/** - Ready for execution
- **Done/** - Completed actions

## Quick Start

### Option 1: Master Startup Script (Recommended)

Start all components with one command:

```batch
start_ai_employee.bat
```

This launches:
1. Gmail Watcher
2. WhatsApp Watcher
3. Odoo Docker Container
4. Ralph Loop (daemon mode)
5. Action Dispatcher (daemon mode)

### Option 2: Manual Component Startup

Start each component individually:

```bash
# Terminal 1: Gmail Watcher
python watchers/gmail_watcher.py

# Terminal 2: WhatsApp Watcher
python watchers/whatsapp_watcher_simple.py

# Terminal 3: Ralph Loop (daemon mode)
python silver/tools/ralph_loop_runner.py --daemon --interval 60

# Terminal 4: Action Dispatcher (daemon mode)
python silver/tools/action_dispatcher.py --daemon --interval 10
```

### Option 3: PM2 Process Manager

For production deployment:

```bash
# Install PM2
npm install -g pm2

# Start watchers
pm2 start ecosystem.config.js

# View status
pm2 status

# View logs
pm2 logs

# Stop all
pm2 stop all
```

## Component Details

### 1. Gmail Watcher

**File:** `watchers/gmail_watcher.py`

**Purpose:** Monitors Gmail inbox for important emails using Gmail API.

**Setup:**
1. Enable Gmail API in Google Cloud Console
2. Download `credentials.json` to project root
3. Run once to authorize (creates `token.json`)

**Run:**
```bash
python watchers/gmail_watcher.py
```

**Output:** Creates `.md` files in `Needs_Action/` with YAML frontmatter:
```yaml
---
type: email
from: sender@example.com
subject: Email Subject
received: 2026-03-16 10:00:00
priority: high
status: pending
---
```

### 2. WhatsApp Watcher

**File:** `watchers/whatsapp_watcher_simple.py`

**Purpose:** Monitors WhatsApp messages (file-based alternative to Playwright version).

**Run:**
```bash
python watchers/whatsapp_watcher_simple.py
```

**Usage:** Create files in `Inbox/`, watcher moves them to `Needs_Action/` with metadata.

### 3. Ralph Loop Runner (The Brain)

**File:** `silver/tools/ralph_loop_runner.py`

**Purpose:** Analyzes tasks in `Needs_Action/`, creates plans, routes to approval.

**Modes:**
- **Daemon mode** (continuous): `python silver/tools/ralph_loop_runner.py --daemon --interval 60`
- **Single run:** `python silver/tools/ralph_loop_runner.py "Process Needs_Action"`

**Features:**
- Task type detection (sales, payment, file_drop, action_item, review)
- Priority assignment (high, medium, normal, low)
- Plan generation with action steps
- LinkedIn post draft creation for sales leads
- Automatic routing to `Pending_Approval/`

**Task Type Keywords:**
| Type | Keywords |
|------|----------|
| sales | sales, client, project, lead, opportunity |
| payment | payment, invoice, bill, price, cost |
| file_drop | file, document, attachment |
| action_item | action, task, todo, urgent |
| review | review, approve, check, verify |

### 4. Action Dispatcher (The Hands)

**File:** `silver/tools/action_dispatcher.py`

**Purpose:** Monitors `Pending_Approval/Approved/` and executes approved actions.

**Run:**
```bash
# Daemon mode (continuous)
python silver/tools/action_dispatcher.py --daemon --interval 10

# Single check
python silver/tools/action_dispatcher.py --once
```

**Supported Actions:**
| Type | Handler |
|------|---------|
| `linkedin_post_draft` | Calls `tools/li_post.py` |
| `email_draft` | Uses Gmail API to send |
| `tweet_draft` | Uses Twitter MCP |
| `facebook_post_draft` | Uses Facebook/Instagram MCP |
| `instagram_post_draft` | Uses Facebook/Instagram MCP |

**After Successful Execution:**
1. Moves file to `Done/`
2. Updates `Dashboard.md` with activity log

## Complete Workflow Example

### Sales Lead Processing

1. **Email arrives** → Gmail Watcher detects keyword "sales"
2. **File created** → `Needs_Action/GMAIL_sales_inquiry_20260316_100000.md`
3. **Ralph Loop processes** → Detects "sales" type
4. **Plan created** → `Plans/Plan_GMAIL_sales_inquiry_...md`
5. **LinkedIn post draft** → `Pending_Approval/linkedin_post_draft_...md`
6. **Human reviews** → Moves file to `Pending_Approval/Approved/`
7. **Action Dispatcher executes** → Calls `li_post.py` to post
8. **Confirmation** → File moved to `Done/`, Dashboard updated

### Email Sending

1. **Task created** → `Needs_Action/email_to_client.md`
2. **Ralph Loop processes** → Creates email draft
3. **Draft created** → `Plans/email_draft_...md`
4. **Human approves** → Moves to `Pending_Approval/Approved/`
5. **Action Dispatcher sends** → Gmail API sends email
6. **Confirmation** → File moved to `Done/`

## File Format Examples

### Approved LinkedIn Post
```markdown
---
type: linkedin_post_draft
source: GMAIL_sales_inquiry_20260316_100000.md
created: 2026-03-16 10:05:00
status: approved
---

## Content

🚀 Excited to offer our professional services for your business success!

#Business #Professional #Services

---
```

### Approved Email Draft
```markdown
---
type: email_draft
to: client@example.com
subject: Re: Project Inquiry
cc: manager@example.com
created: 2026-03-16 10:05:00
status: approved
---

## Content

Hello,

Thank you for your inquiry. We would be happy to help with your project.

Best regards

---
```

## Configuration

### Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `credentials.json` to project root
6. Run `python watchers/gmail_watcher.py` to authorize

### Odoo Setup

```bash
# Start Odoo
docker-compose up -d

# Access at http://localhost:8069
# Username: admin
# Password: admin
```

### MCP Servers Setup

Edit `mcp.json` with your API credentials:

```json
{
  "mcpServers": {
    "twitter": {
      "env": {
        "TWITTER_API_KEY": "your_key",
        "TWITTER_API_SECRET": "your_secret",
        "TWITTER_ACCESS_TOKEN": "your_token",
        "TWITTER_USER_ID": "your_user_id"
      }
    },
    "facebook-instagram": {
      "env": {
        "FB_APP_ID": "your_app_id",
        "FB_ACCESS_TOKEN": "your_token",
        "INSTAGRAM_ACCOUNT_ID": "your_ig_account"
      }
    }
  }
}
```

## Logs

All logs are stored in `Logs/`:

| Log File | Component |
|----------|-----------|
| `watcher.log` | Gmail/WhatsApp watchers |
| `action_dispatcher_YYYYMMDD.log` | Action Dispatcher |
| `ralph_loop_YYYYMMDD.log` | Ralph Loop |
| `li_YYYYMMDD.log` | LinkedIn poster |
| `pm2/` | PM2 managed processes |

## Troubleshooting

### Gmail Watcher not starting
- Check `credentials.json` exists in project root
- Run manually first to authorize: `python watchers/gmail_watcher.py`
- Check logs: `tail -f Logs/watcher.log`

### Action Dispatcher not executing
- Ensure file is in `Pending_Approval/Approved/` (not just `Pending_Approval/`)
- Check file has correct `type` in YAML frontmatter
- View logs: `tail -f Logs/action_dispatcher_*.log`

### Ralph Loop not processing
- Check `Needs_Action/` folder has files
- Run manually: `python silver/tools/ralph_loop_runner.py`
- View output for errors

### LinkedIn post not publishing
- Ensure you're logged in to LinkedIn
- Check session folder: `session/linkedin/`
- Run `li_post.py` manually: `python tools/li_post.py`

### Python 3.14 compatibility issues
- Playwright-based watchers require Python 3.11/3.12
- Use `whatsapp_watcher_simple.py` as alternative
- See `watchers/PYTHON314_FIX.md` for details

## Testing

### Test Gmail Watcher
```bash
# Send yourself an email with subject "URGENT: Sales Inquiry"
python watchers/gmail_watcher.py
# Check Needs_Action/ for new file
```

### Test Ralph Loop
```bash
# Create test file
echo "Sales lead: New client project opportunity" > Needs_Action/test_sales.md

# Run Ralph Loop
python silver/tools/ralph_loop_runner.py

# Check Plans/ and Pending_Approval/ for created files
```

### Test Action Dispatcher
```bash
# Create approved file
cat > Pending_Approval/Approved/test_post.md << EOF
---
type: linkedin_post_draft
---

## Content

Test post content

---
EOF

# Run dispatcher
python silver/tools/action_dispatcher.py --once

# Check Done/ for moved file
```

## Production Deployment

### Using PM2 (Recommended)

```bash
# Install PM2
npm install -g pm2

# Start all watchers
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
```

### Using Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: At logon
4. Action: Start a program
5. Program: `start_ai_employee.bat`
6. Start in: `F:\heckathon\heckathon 0`

## Security Notes

- **NEVER** commit `credentials.json` or `token.json` to git
- **CHANGE** Odoo default password before production
- **REVIEW** all posts/emails before approval (HITL)
- **MONITOR** logs regularly for errors

## Next Steps

1. ✅ Start all components: `start_ai_employee.bat`
2. ✅ Verify watchers are running: Check `Needs_Action/` for new files
3. ✅ Test approval workflow: Move a draft to `Approved/`
4. ✅ Monitor Dashboard: `Dashboard.md`
5. ✅ Configure MCP servers with API credentials

---

*Silver Tier Implementation - Personal AI Employee*
*Version: 1.0 - 2026-03-24*
