# AI Employee Project - Bronze Tier

Local-first Personal AI Employee (Bronze Tier): File system monitoring with Inbox → Needs_Action → Done flow. No payment, no external APIs. Uses VS Code for editing.

## Features

### 📁 File Workflow
- **Inbox/** - New files land here
- **Needs_Action/** - Files requiring attention
- **Done/** - Completed/archived files
- **Logs/** - Activity logs
- **Plans/** - Future planning documents

### 🚀 Antigravity Auto-Processor
Automatically moves files based on content keywords. See `Antigravity_Rules.md` for configuration.

## Quick Start

### Run Antigravity Watcher
```bash
# Continuous monitoring (checks every 5 seconds)
python antigravity.py

# One-time processing
python antigravity.py --once
```

### Manual Workflow
1. Create/edit files in `Inbox/`
2. Review and move to `Needs_Action/` or `Done/`
3. Check `Dashboard.md` for status

## Project Structure
```
F:\heckathon\heckathon-0\
├── Inbox/              # New files
├── Needs_Action/       # Pending tasks
├── Done/               # Completed items
├── Pending_Approval/   # Awaiting approval
├── Logs/               # Activity logs
├── Plans/              # Future plans
├── Dashboard.md        # Status overview
├── Company_Handbook.md # Rules & guidelines
├── Antigravity_Rules.md # Auto-processing config
├── antigravity.py      # File watcher script
├── .claude/skills/     # Agent skills
└── README.md           # This file
```

## Logs
Daily logs are created in `Logs/antigravity_YYYY-MM-DD.log`
