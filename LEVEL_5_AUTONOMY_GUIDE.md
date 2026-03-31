# Level 5 Autonomy - Complete Implementation Guide

## Overview

This document describes the complete "Level 5 Autonomy" implementation for the Personal AI Employee system.

## Architecture: Eyes → Brain → Hands

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LEVEL 5 AUTONOMY FLOW                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  THE EYES (Watchers)                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Gmail        │  │ WhatsApp     │  │ LinkedIn     │                  │
│  │ Watcher      │  │ Watcher      │  │ Watcher      │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         │                 │                 │                           │
│         └─────────────────┴─────────────────┘                           │
│                           │                                             │
│                           ▼                                             │
│                    Inbox / Needs_Action                                 │
│                           │                                             │
│                           ▼                                             │
│  THE BRAIN (Ralph Wiggum Loop)                                          │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │  • Analyze task type (sales, payment, action, review)   │          │
│  │  • Assign priority (high, medium, normal, low)          │          │
│  │  • Generate action plan                                  │          │
│  │  • Create drafts (LinkedIn posts, emails)               │          │
│  │  • Route to Pending_Approval                            │          │
│  └──────────────────────────────────────────────────────────┘          │
│                           │                                             │
│                           ▼                                             │
│                  Pending_Approval /                                     │
│                  Pending_Approval/Approved                              │
│                           │                                             │
│                           │  ◄── HUMAN-IN-THE-LOOP (Manual Approval)   │
│                           │      Human moves file to "Approved"         │
│                           ▼                                             │
│  THE HANDS (Action Dispatcher)                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │ LinkedIn     │  │ Email        │  │ Social Media │                 │
│  │ Poster       │  │ Sender       │  │ (FB, IG, TW) │                 │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                 │
│         │                 │                 │                          │
│         └─────────────────┴─────────────────┘                          │
│                           │                                            │
│                           ▼                                            │
│                        Done /                                           │
│                  Dashboard Updated                                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components Summary

| Component | File | Purpose | Mode |
|-----------|------|---------|------|
| **Gmail Watcher** | `watchers/gmail_watcher.py` | Monitor Gmail for important emails | Daemon (120s) |
| **WhatsApp Watcher** | `watchers/whatsapp_watcher_simple.py` | Monitor WhatsApp messages | Daemon (30s) |
| **Ralph Loop** | `silver/tools/ralph_loop_runner.py` | Task analysis & planning | Daemon (60s) |
| **Action Dispatcher** | `silver/tools/action_dispatcher.py` | Execute approved actions | Daemon (10s) |
| **LinkedIn Poster** | `tools/li_post.py` | Post to LinkedIn | On-demand |
| **Email MCP** | `mcp_servers/email-mcp/index.js` | Send emails via Gmail | On-demand |
| **Twitter MCP** | `mcp_servers/twitter/index.js` | Post tweets | On-demand |
| **Facebook/Instagram MCP** | `mcp_servers/facebook-instagram/index.js` | Social posting | On-demand |

## Startup Commands

### Quick Start (All Components)
```batch
start_ai_employee.bat
```

### Manual Start (Individual Components)
```bash
# Terminal 1: Gmail Watcher
python watchers/gmail_watcher.py

# Terminal 2: WhatsApp Watcher
python watchers/whatsapp_watcher_simple.py

# Terminal 3: Ralph Loop (Brain)
python silver/tools/ralph_loop_runner.py --daemon --interval 60

# Terminal 4: Action Dispatcher (Hands)
python silver/tools/action_dispatcher.py --daemon --interval 10
```

### Production (PM2)
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## Workflow Examples

### Example 1: Sales Lead → LinkedIn Post

1. **Email arrives**: "Interested in your services for our project"
2. **Gmail Watcher** detects keyword "services" → Creates `Needs_Action/GMAIL_services_20260324.md`
3. **Ralph Loop** (every 60s):
   - Detects "sales" type (keywords: services, project)
   - Priority: normal
   - Creates LinkedIn post draft
   - Moves to `Pending_Approval/linkedin_post_draft_20260324.md`
4. **Human reviews** draft → Moves to `Pending_Approval/Approved/`
5. **Action Dispatcher** (every 10s):
   - Detects approved file
   - Calls `li_post.py` to publish
   - Moves to `Done/`
   - Updates Dashboard

### Example 2: Payment Request → Approval

1. **Email arrives**: "Invoice #1234 - Payment due $750"
2. **Gmail Watcher** detects keywords "invoice", "payment" → Creates `Needs_Action/GMAIL_invoice_20260324.md`
3. **Ralph Loop**:
   - Detects "payment" type
   - Priority: medium
   - Flags for approval (amount > $500 per Company Handbook)
   - Moves to `Pending_Approval/`
4. **Human reviews** → Approves or rejects
5. **Action Dispatcher** processes approved payment

### Example 3: Client Message → Email Response

1. **WhatsApp message**: "Can you send me the proposal?"
2. **WhatsApp Watcher** → Creates `Needs_Action/WHATSAPP_proposal_20260324.md`
3. **Ralph Loop**:
   - Detects "action_item" type
   - Creates email draft response
   - Moves to `Plans/email_draft_20260324.md`
4. **Human edits** draft → Moves to `Pending_Approval/Approved/`
5. **Action Dispatcher**:
   - Uses Gmail API to send
   - Moves to `Done/`

## File Format Standards

### Needs_Action File
```markdown
---
type: email
from: client@example.com
subject: Project Inquiry
received: 2026-03-24 10:00:00
priority: normal
status: pending
watcher: gmail_watcher
---

# Email Content

[Paste email content here]
```

### Approved LinkedIn Post
```markdown
---
type: linkedin_post_draft
source: GMAIL_Project_Inquiry_20260324.md
created: 2026-03-24 10:05:00
status: approved
---

## Content

🚀 Excited to announce our new project partnership!

#Business #Partnership #Success

---
```

### Approved Email Draft
```markdown
---
type: email_draft
to: client@example.com
subject: Re: Project Inquiry
cc: manager@example.com
created: 2026-03-24 10:05:00
status: approved
---

## Content

Hello,

Thank you for your inquiry. We would be delighted to help.

Best regards

---
```

## Task Type Detection

| Type | Keywords | Action |
|------|----------|--------|
| **sales** | sales, client, project, lead, opportunity | Create LinkedIn post |
| **payment** | payment, invoice, bill, price, cost | Flag for approval |
| **file_drop** | file, document, attachment | Process and route |
| **action_item** | action, task, todo, urgent | Execute or delegate |
| **review** | review, approve, check, verify | Manual review |

## Priority Assignment

| Priority | Trigger |
|----------|---------|
| **high** | "urgent" in content |
| **medium** | "invoice" or "payment" in content |
| **normal** | "sales" in content |
| **low** | Default |

## Human-in-the-Loop (HITL) Approval

All actions require human approval before execution:

1. **Draft created** → `Plans/` or `Pending_Approval/`
2. **Human reviews** → Edits if needed
3. **Human approves** → Moves file to `Pending_Approval/Approved/`
4. **Action Dispatcher executes** → Posts/sends/moves to Done

### Approval Workflow
```
Pending_Approval/
├── linkedin_post_draft_20260324.md  ← Waiting for approval
├── email_draft_20260324.md          ← Waiting for approval
└── Approved/
    ├── linkedin_post_draft_20260323.md  ← Approved, will be posted
    └── email_draft_20260323.md          ← Approved, will be sent
```

## Monitoring & Debugging

### Check Component Status
```bash
# PM2 status
pm2 status

# Docker status
docker-compose ps

# View logs
tail -f Logs/watcher.log
tail -f Logs/action_dispatcher_*.log
tail -f Logs/ralph_loop_*.log
```

### Test Individual Components
```bash
# Test Gmail Watcher
python watchers/gmail_watcher.py

# Test Ralph Loop (single run)
python silver/tools/ralph_loop_runner.py "Test processing"

# Test Action Dispatcher (single check)
python silver/tools/action_dispatcher.py --once
```

### Dashboard
Check `Dashboard.md` for:
- Bank balance
- Pending messages
- Active tasks
- LinkedIn posts pending
- Recent activity log

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Gmail Watcher not starting | Check `credentials.json` exists, run manual auth |
| Action Dispatcher not executing | Ensure file is in `Approved/` subfolder |
| Ralph Loop not processing | Check `Needs_Action/` has files, run manually |
| LinkedIn post fails | Check session folder, re-login if needed |
| Python 3.14 errors | Use simple watchers, see `PYTHON314_FIX.md` |

## Production Checklist

- [ ] All watchers running (PM2 or separate terminals)
- [ ] Odoo Docker container running
- [ ] `credentials.json` configured for Gmail
- [ ] MCP servers configured with API keys
- [ ] Odoo password changed from default
- [ ] Logs monitored regularly
- [ ] Dashboard reviewed daily
- [ ] Approved folder checked before execution

## Next Steps

1. ✅ Start system: `start_ai_employee.bat`
2. ✅ Verify all components running
3. ✅ Test with sample file in `Inbox/`
4. ✅ Monitor `Needs_Action/` for processed files
5. ✅ Review and approve drafts in `Pending_Approval/`
6. ✅ Check `Done/` for completed actions
7. ✅ Review `Dashboard.md` for status

---

*Level 5 Autonomy Implementation - Personal AI Employee*
*Version: 1.0 - 2026-03-24*
