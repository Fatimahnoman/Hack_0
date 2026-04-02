"""
Dashboard Updater - Bronze Tier
================================
Updates Dashboard.md at every workflow step.

Usage:
    from dashboard_updater import update_dashboard
    update_dashboard(event="email_received", folder="Inbox")
"""

from pathlib import Path
from datetime import datetime
import os

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRONZE_TIER = PROJECT_ROOT / "Bronze_Tier"
INBOX_FOLDER = BRONZE_TIER / "Inbox"
NEEDS_ACTION_FOLDER = BRONZE_TIER / "Needs_Action"
PLANS_FOLDER = BRONZE_TIER / "Plans"
PENDING_APPROVAL_FOLDER = BRONZE_TIER / "Pending_Approval"
APPROVED_FOLDER = BRONZE_TIER / "Approved"
DONE_FOLDER = BRONZE_TIER / "Done"
DASHBOARD_FILE = BRONZE_TIER / "Dashboard.md"


def count_files(folder: Path) -> int:
    """Count .md files in folder."""
    if not folder.exists():
        return 0
    return len(list(folder.glob("*.md")))


def update_dashboard(event: str = "", folder: str = "", details: str = ""):
    """Update Dashboard.md with current status."""
    
    # Count files in each folder
    inbox_count = count_files(INBOX_FOLDER)
    needs_action_count = count_files(NEEDS_ACTION_FOLDER)
    plans_count = count_files(PLANS_FOLDER)
    pending_count = count_files(PENDING_APPROVAL_FOLDER)
    approved_count = count_files(APPROVED_FOLDER)
    done_count = count_files(DONE_FOLDER)
    
    # Calculate totals
    total_pending = inbox_count + needs_action_count + plans_count + pending_count
    total_completed = done_count
    
    # Determine status
    if total_pending > 0:
        status = "Active"
    else:
        status = "Idle"
    
    # Get current time
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Build event log
    event_log = ""
    if event:
        event_log = f"""
## Latest Activity

| Time | Event | Folder | Details |
|------|-------|--------|---------|
| {now} | {event} | {folder} | {details} |

"""
    
    # Build dashboard content
    dashboard_content = f"""# 🥉 Bronze Tier Dashboard

## 📊 Status Overview

| Metric | Value |
|--------|-------|
| **Pending Items** | {total_pending} |
| **Processed Today** | {total_completed} |
| **Last Updated** | {now} |
| **Status** | {status} |

## 📁 Folder Status

| Folder | Files | Purpose |
|--------|-------|---------|
| **Inbox/** | {inbox_count} | New emails/messages land here |
| **Needs_Action/** | {needs_action_count} | Important items requiring attention |
| **Plans/** | {plans_count} | Action plans and drafts |
| **Pending_Approval/** | {pending_count} | Awaiting HITL approval |
| **Approved/** | {approved_count} | Approved for processing |
| **Done/** | {done_count} | Completed items |

{event_log}
## Workflow

```
Gmail/WhatsApp -> Inbox/ -> Needs_Action/ -> Plans/ -> Pending_Approval/ -> Approved/ -> Done/
```

## Quick Stats

- **Total Pending:** {total_pending}
- **Total Completed:** {total_completed}
- **System Status:** {status}

---
*Last Updated: {now}*
*Bronze Tier - AI Employee Dashboard*
"""
    
    # Write dashboard
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(dashboard_content)
    
    print(f"📊 Dashboard updated: {event if event else 'Status refresh'}")


# Event shortcuts
def email_received(subject: str = ""):
    update_dashboard(event="Email Received", folder="Inbox/", details=subject)


def file_created(filename: str = ""):
    update_dashboard(event="File Created", folder="Needs_Action/", details=filename)


def plan_created(filename: str = ""):
    update_dashboard(event="Plan Created", folder="Plans/", details=filename)


def moved_to_pending(filename: str = ""):
    update_dashboard(event="Moved to Pending", folder="Pending_Approval/", details=filename)


def moved_to_approved(filename: str = ""):
    update_dashboard(event="Moved to Approved", folder="Approved/", details=filename)


def reply_sent(filename: str = ""):
    update_dashboard(event="Reply Sent", folder="Done/", details=filename)


if __name__ == "__main__":
    # Test update
    update_dashboard(event="Test Update", folder="Dashboard/", details="Dashboard updater working")
    print("Dashboard updater ready!")
