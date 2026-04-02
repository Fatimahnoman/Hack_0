"""
Ralph Wiggum Loop - Bronze Tier Processor
==========================================
Claude Code integration for processing files in Needs_Action folder.

Workflow:
1. Watch Needs_Action/ folder for new .md files
2. Process file content with Claude Code (simulated)
3. Update Dashboard.md with status
4. Create/Update Plans in Plans/ folder
5. Move processed files to Done/ folder

Run: python bronze_tier_processor.py
"""

import os
import shutil
import time
import re
from datetime import datetime
from pathlib import Path

# Configuration
BRONZE_TIER = Path(__file__).resolve().parent
INBOX_FOLDER = BRONZE_TIER / "Inbox"
NEEDS_ACTION_FOLDER = BRONZE_TIER / "Needs_Action"
PLANS_FOLDER = BRONZE_TIER / "Plans"
DONE_FOLDER = BRONZE_TIER / "Done"
DASHBOARD_FILE = BRONZE_TIER / "Dashboard.md"
CHECK_INTERVAL = 10  # seconds

# Import dashboard updater
try:
    from dashboard_updater import update_dashboard, file_created, plan_created
except ImportError:
    update_dashboard = None
    file_created = None
    plan_created = None


def ensure_directories():
    """Ensure all Bronze Tier directories exist."""
    for folder in [INBOX_FOLDER, NEEDS_ACTION_FOLDER, PLANS_FOLDER, DONE_FOLDER]:
        folder.mkdir(parents=True, exist_ok=True)
    print(f"✓ All directories verified")


def read_file(filepath: Path) -> str:
    """Read file content."""
    try:
        return filepath.read_text(encoding='utf-8')
    except Exception as e:
        print(f"[ERROR] Reading {filepath.name}: {e}")
        return ""


def write_file(filepath: Path, content: str):
    """Write content to file."""
    try:
        filepath.write_text(content, encoding='utf-8')
        print(f"✓ Written: {filepath.name}")
    except Exception as e:
        print(f"[ERROR] Writing {filepath.name}: {e}")


def extract_yaml_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown file."""
    data = {
        'type': 'unknown',
        'from': '',
        'subject': '',
        'priority': 'normal',
        'status': 'pending',
        'original_name': ''
    }
    
    if '---' in content:
        parts = content.split('---')
        if len(parts) >= 2:
            yaml_content = parts[1]
            for line in yaml_content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if key in data:
                        data[key] = value
    
    return data


def claude_code_processing(content: str, metadata: dict) -> dict:
    """
    Simulate Claude Code (Ralph Wiggum Loop) processing.
    In real scenario, this would call Claude API or Claude Code CLI.
    
    Returns analysis and action plan.
    """
    content_lower = content.lower()
    
    # Analyze content
    analysis = {
        'is_urgent': 'urgent' in content_lower,
        'is_invoice': 'invoice' in content_lower or 'payment' in content_lower,
        'is_sales': 'sales' in content_lower,
        'requires_action': False,
        'action_type': '',
        'summary': ''
    }
    
    # Determine action type
    if analysis['is_invoice']:
        analysis['requires_action'] = True
        analysis['action_type'] = 'invoice_processing'
        analysis['summary'] = 'Invoice/Payment request detected'
    elif analysis['is_urgent']:
        analysis['requires_action'] = True
        analysis['action_type'] = 'urgent_response'
        analysis['summary'] = 'Urgent matter requiring attention'
    elif analysis['is_sales']:
        analysis['requires_action'] = True
        analysis['action_type'] = 'sales_inquiry'
        analysis['summary'] = 'Sales inquiry detected'
    else:
        analysis['summary'] = 'General message - no immediate action required'
    
    # Generate plan
    if analysis['requires_action']:
        analysis['plan'] = f"""
## Action Plan

**Priority:** {metadata.get('priority', 'normal').upper()}
**Type:** {analysis['action_type']}
**Summary:** {analysis['summary']}

### Steps:
1. Review the content carefully
2. Determine appropriate response
3. Take necessary action
4. Document in Done folder

### Status: Pending Review
"""
    else:
        analysis['plan'] = f"""
## Action Plan

**Priority:** {metadata.get('priority', 'normal').upper()}
**Summary:** {analysis['summary']}

### Recommendation:
- Archive for future reference
- No immediate action required

### Status: Information Only
"""
    
    return analysis


def update_dashboard(processed_count: int, pending_count: int, last_processed: str):
    """Update Dashboard.md with current status."""
    dashboard_content = f"""# Bronze Tier Dashboard

## 📊 Status Overview

| Metric | Value |
|--------|-------|
| **Pending Items** | {pending_count} |
| **Processed Today** | {processed_count} |
| **Last Processed** | {last_processed} |
| **Status** | {'🟢 Active' if processed_count > 0 else '🟡 Idle'} |

## 📁 Folder Status

| Folder | Purpose |
|--------|---------|
| **Inbox/** | New files land here |
| **Needs_Action/** | Files requiring attention |
| **Plans/** | Action plans and drafts |
| **Done/** | Completed items |

## 🔄 Workflow

```
Watcher → Needs_Action → [Ralph Wiggum Loop] → Dashboard + Plans → Done
```

## ⚡ Quick Stats

- **Active Tasks:** {pending_count}
- **Completed:** {processed_count}
- **System Status:** ONLINE

---
*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Bronze Tier - Ralph Wiggum Loop Processor*
"""
    
    write_file(DASHBOARD_FILE, dashboard_content)


def create_plan_file(original_file: Path, metadata: dict, analysis: dict) -> Path:
    """Create a plan file in Plans/ folder."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    subject = metadata.get('subject', 'Unknown')[:30].replace(' ', '_')
    plan_filename = f"PLAN_{subject}_{timestamp}.md"
    plan_path = PLANS_FOLDER / plan_filename
    
    plan_content = f"""---
type: plan
original_file: {original_file.name}
from: {metadata.get('from', 'Unknown')}
subject: {metadata.get('subject', 'No Subject')}
priority: {metadata.get('priority', 'normal')}
created_at: {datetime.now().isoformat()}
status: created
---

# Action Plan

## Original File Information

- **File:** {original_file.name}
- **From:** {metadata.get('from', 'Unknown')}
- **Subject:** {metadata.get('subject', 'No Subject')}
- **Priority:** {metadata.get('priority', 'normal')}
- **Received:** {metadata.get('received', 'N/A')}

## Claude Code Analysis (Ralph Wiggum Loop)

{analysis['summary']}

### Detected Keywords:
- Urgent: {'✓' if analysis['is_urgent'] else '✗'}
- Invoice/Payment: {'✓' if analysis['is_invoice'] else '✗'}
- Sales: {'✓' if analysis['is_sales'] else '✗'}

{analysis['plan']}

## Processing Log

- **Plan Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Processed by:** Ralph Wiggum Loop (Claude Code)
- **Status:** Plan Generated

---
*Automatically generated by Bronze Tier Processor*
"""
    
    write_file(plan_path, plan_content)
    return plan_path


def move_to_done(original_file: Path, analysis: dict) -> Path:
    """Move processed file to Done/ folder with completion metadata."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    done_filename = f"{original_file.stem}_COMPLETED_{timestamp}.md"
    done_path = DONE_FOLDER / done_filename

    # Read original content
    content = read_file(original_file)

    # Add completion metadata
    completion_info = f"""
---
## Completion Info
- Processed by: Ralph Wiggum Loop (Claude Code)
- Analysis: {analysis['summary']}
- Action Required: {'Yes' if analysis['requires_action'] else 'No'}
- Action Type: {analysis['action_type']}
- Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Status: COMPLETED
"""

    new_content = content + completion_info
    write_file(done_path, new_content)

    # Delete original from Needs_Action
    try:
        original_file.unlink()
        print(f"✓ Moved to Done: {done_filename}")
        
        # Update dashboard - moved to done
        if update_dashboard:
            update_dashboard(
                event="✅ Moved to Done",
                folder="Done/",
                details=done_filename
            )
    except Exception as e:
        print(f"[ERROR] Deleting original file: {e}")

    return done_path


def process_needs_action_file(filepath: Path) -> bool:
    """Process a single file from Needs_Action folder."""
    print(f"\n{'='*60}")
    print(f"Processing: {filepath.name}")
    print(f"{'='*60}")
    
    # Read file content
    content = read_file(filepath)
    if not content:
        return False
    
    # Extract metadata
    metadata = extract_yaml_frontmatter(content)
    print(f"  Type: {metadata['type']}")
    print(f"  From: {metadata['from']}")
    print(f"  Subject: {metadata['subject']}")
    print(f"  Priority: {metadata['priority']}")
    
    # Claude Code Processing (Ralph Wiggum Loop)
    print(f"\n🤖 Ralph Wiggum Loop (Claude Code) processing...")
    analysis = claude_code_processing(content, metadata)
    print(f"  Summary: {analysis['summary']}")
    print(f"  Requires Action: {'✓ Yes' if analysis['requires_action'] else '✗ No'}")
    if analysis['requires_action']:
        print(f"  Action Type: {analysis['action_type']}")
    
    # Create Plan file
    print(f"\n📋 Creating Plan...")
    plan_path = create_plan_file(filepath, metadata, analysis)
    print(f"  Plan created: {plan_path.name}")
    
    # Update dashboard - plan created
    if update_dashboard:
        update_dashboard(event="📋 Plan Created", folder="Plans/", details=plan_path.name)
    
    # Move to Done
    print(f"\n📁 Moving to Done folder...")
    done_path = move_to_done(filepath, analysis)
    
    # Update Dashboard
    print(f"\n📊 Updating Dashboard...")
    pending_count = len(list(NEEDS_ACTION_FOLDER.glob("*.md")))
    if update_dashboard:
        update_dashboard(
            event="🔄 File Processed",
            folder="Done/",
            details=f"Moved {filepath.name} to Done/"
        )
    
    print(f"\n✓ Processing complete!")
    return True


def check_needs_action() -> int:
    """Check Needs_Action folder for new files to process."""
    if not NEEDS_ACTION_FOLDER.exists():
        return 0
    
    files = list(NEEDS_ACTION_FOLDER.glob("*.md"))
    processed_count = 0
    
    for filepath in files:
        # Skip already processed files
        if 'COMPLETED' in filepath.name or 'PLAN' in filepath.name:
            continue
        
        try:
            if process_needs_action_file(filepath):
                processed_count += 1
        except Exception as e:
            print(f"[ERROR] Processing {filepath.name}: {e}")
    
    return processed_count


def main():
    """Main function to start Bronze Tier Processor (Ralph Wiggum Loop)."""
    print("=" * 60)
    print("🤖 Ralph Wiggum Loop - Bronze Tier Processor")
    print("=" * 60)
    print(f"Bronze Tier: {BRONZE_TIER}")
    print(f"Monitoring: {NEEDS_ACTION_FOLDER}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print("-" * 60)
    print("WORKFLOW:")
    print("1. Watcher (Gmail/File) → Needs_Action/")
    print("2. Ralph Wiggum Loop (Claude Code) processes files")
    print("3. Dashboard.md + Plans/ updated")
    print("4. Files moved to Done/")
    print("=" * 60)
    
    # Ensure directories exist
    ensure_directories()
    
    # Initialize Dashboard
    update_dashboard(
        processed_count=len(list(DONE_FOLDER.glob("*.md"))),
        pending_count=len(list(NEEDS_ACTION_FOLDER.glob("*.md"))),
        last_processed="Starting up..."
    )
    
    print(f"\n[✓] Ralph Wiggum Loop started!")
    print(f"Press Ctrl+C to stop...")
    
    try:
        while True:
            processed = check_needs_action()
            
            if processed > 0:
                print(f"\n🎉 Processed {processed} file(s)")
            
            time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n\n[INFO] Processor stopped by user")
    
    print("[INFO] Ralph Wiggum Loop stopped.")


if __name__ == "__main__":
    main()
