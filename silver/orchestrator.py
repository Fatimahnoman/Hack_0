"""
Silver Tier Orchestrator
========================
The "Brain" of the Silver Tier AI Employee.

Monitors silver/Needs_Action/ for new files from watchers.
Creates permanent Plan.md in silver/Plans/.
Generates AI reply draft in silver/Pending_Approval/.
Moves processed file out of Needs_Action/ (keeps it empty).

Workflow:
  Watcher → Needs_Action/ → Orchestrator → Plan.md (Plans/) + Reply Draft (Pending_Approval/)

Run:
  python silver/orchestrator.py --daemon --interval 30
  python silver/orchestrator.py --once
"""

import os
import sys
import time
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

# =============================================================================
# CONFIGURATION - SILVER TIER FOLDER ARCHITECTURE
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SILVER_DIR = PROJECT_ROOT / "silver"

# Silver Tier folders
NEEDS_ACTION_FOLDER = SILVER_DIR / "Needs_Action"
PLANS_FOLDER = SILVER_DIR / "Plans"
PENDING_APPROVAL_FOLDER = SILVER_DIR / "Pending_Approval"
APPROVED_FOLDER = SILVER_DIR / "Approved"  # Silver root level Approved folder
LOGS_FOLDER = SILVER_DIR / "Logs"

# Ensure directories exist
for folder in [NEEDS_ACTION_FOLDER, PLANS_FOLDER, PENDING_APPROVAL_FOLDER, LOGS_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)

# Settings
CHECK_INTERVAL = 30  # seconds
PROCESSED_LOG = LOGS_FOLDER / "orchestrator_processed.txt"

# Track processed files
processed_files = set()

# =============================================================================
# LOGGING
# =============================================================================

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

# =============================================================================
# PROCESSED TRACKING
# =============================================================================

def load_processed():
    global processed_files
    if PROCESSED_LOG.exists():
        try:
            with open(PROCESSED_LOG, "r", encoding="utf-8") as f:
                processed_files = set(line.strip() for line in f if line.strip())
            log(f"Loaded {len(processed_files)} processed files from log")
        except Exception as e:
            log(f"Warning: Could not load processed log: {e}")

def save_processed(filename: str):
    processed_files.add(filename)
    try:
        with open(PROCESSED_LOG, "a", encoding="utf-8") as f:
            f.write(f"{filename}\n")
    except Exception as e:
        log(f"Warning: Could not save to processed log: {e}")

# =============================================================================
# FILE ANALYSIS
# =============================================================================

def read_file_content(filepath: Path) -> str:
    """Read file content safely."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        log(f"Error reading {filepath.name}: {e}")
        return ""

def extract_yaml_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown file."""
    metadata = {}
    if not content.startswith("---"):
        return metadata

    parts = content.split("---", 2)
    if len(parts) < 2:
        return metadata

    yaml_block = parts[1].strip()
    for line in yaml_block.split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip()] = value.strip().strip('"')

    return metadata

def analyze_file(filepath: Path) -> dict:
    """Analyze a file and extract task information."""
    content = read_file_content(filepath)
    metadata = extract_yaml_frontmatter(content)

    # Determine task type
    task_type = metadata.get("type", "unknown")
    filename_lower = filepath.name.lower()
    if "gmail" in filename_lower:
        task_type = "email"
    elif "whatsapp" in filename_lower:
        task_type = "whatsapp_message"
    elif "linkedin" in filename_lower:
        task_type = "linkedin"
    elif "file" in filename_lower:
        task_type = "file_drop"

    # Determine priority
    priority = metadata.get("priority", "normal")
    content_lower = content.lower()
    if any(kw in content_lower for kw in ["urgent", "asap", "emergency"]):
        priority = "high"
    elif any(kw in content_lower for kw in ["invoice", "payment", "order"]):
        priority = "medium"

    # Extract sender/subject
    sender = metadata.get("from", metadata.get("original_name", "Unknown"))
    subject = metadata.get("subject", filepath.stem)

    # Extract body (everything after frontmatter)
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].strip()

    return {
        "filepath": filepath,
        "filename": filepath.name,
        "type": task_type,
        "priority": priority,
        "sender": sender,
        "subject": subject,
        "body": body,
        "content": content,
        "metadata": metadata
    }

# =============================================================================
# PLAN GENERATION
# =============================================================================

def create_plan(task: dict) -> Path:
    """Create permanent Plan.md in silver/Plans/ folder."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plan_filename = f"PLAN_{task['filename']}_{timestamp}.md"
    plan_filepath = PLANS_FOLDER / plan_filename

    plan_content = f"""---
type: plan
source: {task['filename']}
task_type: {task['type']}
priority: {task['priority']}
created: {datetime.now().isoformat()}
status: created
---

# Action Plan: {task['subject']}

## Source Information
- **Type:** {task['type']}
- **From:** {task['sender']}
- **Priority:** {task['priority']}
- **Received:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Original File:** {task['filename']}

## Analysis
{task['body'][:500] if task['body'] else 'No content available'}

## Recommended Actions
1. Review the incoming {task['type']} from {task['sender']}
2. Determine appropriate response
3. Generate reply draft via Ralph Loop
4. Send for human approval
5. Execute after approval

## Status
- [x] Plan created
- [ ] Reply draft generated (run Ralph Loop)
- [ ] Approved by human
- [ ] Action executed

---
*Created by Silver Orchestrator - Permanent Record*
"""

    with open(plan_filepath, "w", encoding="utf-8") as f:
        f.write(plan_content)

    log(f"✓ Plan created: {plan_filename}")
    return plan_filepath

# =============================================================================
# REPLY DRAFT GENERATION (AI-powered)
# =============================================================================

def generate_reply_draft_for_original(task: dict, original_content: str) -> str:
    """Update the ORIGINAL file with reply draft appended - keeps single file."""
    
    if task["type"] == "email":
        reply_section = generate_email_draft_inline(task)
    elif task["type"] == "whatsapp" or task["type"] == "whatsapp_message":
        reply_section = generate_whatsapp_draft_inline(task)
    elif task["type"] == "linkedin":
        reply_section = generate_linkedin_draft(task)
    else:
        reply_section = f"""
---
## AI Reply Draft

**Type:** {task['type']}
**Priority:** {task['priority']}
**Status:** Pending your review

Edit the reply below when ready, then move this file to silver/Approved/ to execute.

---
"""

    return f"""{original_content}

---
## 🤖 AI Generated Reply Draft (Edit Below Before Approving)

{reply_section}

---
*Move this file to silver/Approved/ to send | Needs_Action folder stays empty*
"""

def generate_email_draft_inline(task: dict) -> str:
    """Generate inline email reply draft."""
    sender = task['sender']
    subject = task['subject']

    # Extract clean name
    clean_sender = re.sub(r'[<>]', '', sender).split('@')[0] if '@' in sender else sender

    # Extract original sender email for reply
    sender_email = sender
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sender)
    if email_match:
        sender_email = email_match.group(0)

    return f"""### Email Reply Draft

**To:** {sender_email}
**Subject:** Re: {subject}

---

Dear {clean_sender},

Thank you for your message regarding {subject}.

We have received your request and are reviewing it carefully.
Our team will respond with a detailed answer shortly.

Best regards,
AI Employee Assistant

---
*Edit this draft as needed, then move file to silver/Approved/ to send via Gmail API*
"""

def generate_reply_draft(task: dict) -> Path:
    """Generate AI reply draft and save to silver/Pending_Approval/."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Generate draft based on task type
    if task["type"] == "email":
        # Use safe sender for filename (Windows compatible)
        sender_for_name = task.get("metadata", {}).get("from", "unknown")
        safe_sender = re.sub(r'[<>]', '', sender_for_name).split('@')[0] if '@' in sender_for_name else sender_for_name
        safe_sender = re.sub(r'[^a-zA-Z0-9_.-]', '_', safe_sender)[:30]
        draft_filename = f"email_draft_{safe_sender}_{timestamp}.md"
        draft_content = generate_email_draft(task)
    elif task["type"] == "whatsapp":
        draft_filename = f"whatsapp_draft_{timestamp}.md"
        draft_content = generate_whatsapp_draft(task)
    elif task["type"] == "linkedin":
        draft_filename = f"linkedin_draft_{timestamp}.md"
        draft_content = generate_linkedin_draft(task)
    else:
        draft_filename = f"reply_draft_{timestamp}.md"
        draft_content = f"""---
type: reply_draft
source: {task['filename']}
priority: {task['priority']}
created: {datetime.now().isoformat()}
status: pending_review
---

## Reply Required

**From:** {task['sender']}
**Type:** {task['type']}
**Priority:** {task['priority']}

{task['body']}

---
*Created by Silver Orchestrator*
"""

    draft_filepath = PENDING_APPROVAL_FOLDER / draft_filename

    with open(draft_filepath, "w", encoding="utf-8") as f:
        f.write(draft_content)

    log(f"✓ Reply draft created: {draft_filename}")
    return draft_filepath

def generate_email_draft(task: dict) -> str:
    """Generate professional email reply draft."""
    sender = task['sender']
    subject = task['subject']
    body = task['body'][:300]

    # Extract clean name from email (remove < > @ etc)
    clean_sender = re.sub(r'[<>]', '', sender).split('@')[0] if '@' in sender else sender
    # Remove spaces and special chars for filename
    safe_sender = re.sub(r'[^a-zA-Z0-9_.-]', '_', clean_sender)[:30]

    return f"""---
type: email_draft
source: {task['filename']}
from: your_email@gmail.com
to: {sender}
subject: Re: {subject}
priority: {task['priority']}
created: {datetime.now().isoformat()}
status: pending_approval
---

## Email Draft

**To:** {sender}
**Subject:** Re: {subject}

---

Dear {sender.split('@')[0] if '@' in sender else sender},

Thank you for your message.

{body}

We will review your request and respond shortly.

Best regards,
AI Employee Assistant

---
*Draft created by Silver Orchestrator - Requires HITL Approval*
*Move to silver/approved/ to send via Gmail API*
"""

def generate_whatsapp_draft(task: dict) -> str:
    """Generate WhatsApp reply draft."""
    return f"""---
type: whatsapp_draft
source: {task['filename']}
priority: {task['priority']}
created: {datetime.now().isoformat()}
status: pending_approval
---

## WhatsApp Reply Draft

Thanks for your message! I've received it and will respond shortly.

---
*Draft created by Silver Orchestrator - Requires HITL Approval*
"""

def generate_whatsapp_draft_inline(task: dict) -> str:
    """Generate inline WhatsApp reply draft for the original file."""
    sender = task['sender']
    return f"""### WhatsApp Reply Draft

**To:** {sender}

---

Hi {sender},

Thanks for your message! I've received it and will respond shortly.

Best regards,
AI Employee Assistant

---
*Move this file to silver/Approved/ to send via WhatsApp Web*
"""

def generate_linkedin_draft(task: dict) -> str:
    """Generate LinkedIn response draft."""
    return f"""---
type: linkedin_draft
source: {task['filename']}
priority: {task['priority']}
created: {datetime.now().isoformat()}
status: pending_approval
---

## LinkedIn Response Draft

Thank you for connecting! I'd love to discuss potential opportunities.

---
*Draft created by Silver Orchestrator - Requires HITL Approval*
"""

# =============================================================================
# FILE MOVEMENT
# =============================================================================

def archive_source_file(task: dict):
    """Move source file from Needs_Action to a temp archive so folder stays empty."""
    src = task["filepath"]
    if not src.exists():
        return

    # Move to Pending_Approval as reference (original source)
    dst = PENDING_APPROVAL_FOLDER / f"source_{task['filename']}"
    try:
        shutil.move(str(src), str(dst))
        log(f"✓ Source file archived: {task['filename']}")
    except Exception as e:
        log(f"Warning: Could not archive source: {e}")

# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_file(filepath: Path) -> bool:
    """Process a single file: Analyze → Plan → Update with Reply Draft → Move to Pending_Approval."""
    log(f"Processing: {filepath.name}")

    try:
        # Step 1: Check if Plan already exists for this file
        existing_plans = list(PLANS_FOLDER.glob(f"PLAN_{filepath.name}_*.md"))
        if existing_plans:
            log(f"  ⚠ Plan already exists for {filepath.name} - skipping duplicate")
            # Move original to Pending_Approval as reference
            dst = PENDING_APPROVAL_FOLDER / f"source_{filepath.name}"
            if not dst.exists():
                shutil.move(str(filepath), str(dst))
            else:
                filepath.unlink()
            save_processed(filepath.name)
            return True

        # Step 2: Analyze file
        task = analyze_file(filepath)
        log(f"  Type: {task['type']}, Priority: {task['priority']}")

        # Step 3: Create permanent Plan.md (ONE per file)
        create_plan(task)

        # Step 4: Update the ORIGINAL file with reply draft (not creating a new file)
        original_content = filepath.read_text(encoding="utf-8")

        # Extract recipient for 'to' field based on type
        if task["type"] == "email":
            sender_email = task['sender']
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', task['sender'])
            if email_match:
                sender_email = email_match.group(0)
        else:
            # WhatsApp, LinkedIn - use sender name/contact
            sender_email = task['sender']

        # Update YAML frontmatter: set 'to' field
        if original_content.startswith("---"):
            parts = original_content.split("---", 2)
            if len(parts) >= 2:
                yaml_block = parts[1].strip()
                # Add or update 'to' field
                if "to:" in yaml_block:
                    yaml_block = re.sub(r'to:.*', f'to: "{sender_email}"', yaml_block)
                else:
                    yaml_block += f'\nto: "{sender_email}"'
                original_content = f"---\n{yaml_block}\n---" + (parts[2] if len(parts) > 2 else "")

        updated_content = generate_reply_draft_for_original(task, original_content)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(updated_content)
        log(f"✓ Original file updated with reply draft")

        # Step 5: Move the SAME file to Pending_Approval (keeps filename intact)
        dst = PENDING_APPROVAL_FOLDER / filepath.name
        shutil.move(str(filepath), str(dst))
        log(f"✓ File moved to Pending_Approval: {filepath.name}")

        # Step 6: Mark as processed
        save_processed(filepath.name)

        log(f"✓ {filepath.name} processed successfully - single file in Pending_Approval")
        return True

    except Exception as e:
        log(f"✗ Error processing {filepath.name}: {e}")
        return False

def run_once():
    """Process all files in Needs_Action once."""
    log("=" * 60)
    log("Silver Orchestrator - Single Run")
    log("=" * 60)

    if not NEEDS_ACTION_FOLDER.exists():
        log(f"No Needs_Action folder found")
        return

    files = [f for f in NEEDS_ACTION_FOLDER.iterdir() if f.is_file()]

    if not files:
        log("No files to process in Needs_Action")
        return

    processed_count = 0
    for filepath in files:
        if filepath.name in processed_files:
            continue
        if process_file(filepath):
            processed_count += 1

    log(f"\nProcessed {processed_count}/{len(files)} files")

def run_daemon(check_interval: int = CHECK_INTERVAL):
    """Run orchestrator in daemon mode (continuous monitoring)."""
    log("=" * 70)
    log("Silver Orchestrator - DAEMON MODE")
    log("=" * 70)
    log(f"Monitoring: {NEEDS_ACTION_FOLDER}")
    log(f"Plans folder: {PLANS_FOLDER}")
    log(f"Drafts folder: {PENDING_APPROVAL_FOLDER}")
    log(f"Check interval: {check_interval}s")
    log("=" * 70)

    load_processed()

    try:
        while True:
            files = [f for f in NEEDS_ACTION_FOLDER.iterdir() if f.is_file()]
            unprocessed = [f for f in files if f.name not in processed_files]

            if unprocessed:
                log(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Found {len(unprocessed)} new file(s)")
                for filepath in unprocessed:
                    process_file(filepath)
            else:
                log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No new files. Waiting...")

            time.sleep(check_interval)

    except KeyboardInterrupt:
        log("\n👋 Orchestrator stopped by user")
    except Exception as e:
        log(f"💥 Orchestrator crashed: {e}")
        raise

# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Silver Tier Orchestrator")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode")
    parser.add_argument("--once", action="store_true", help="Process files once and exit")
    parser.add_argument("--interval", type=int, default=CHECK_INTERVAL, help="Check interval in seconds")

    args = parser.parse_args()

    if args.daemon:
        run_daemon(args.interval)
    elif args.once:
        run_once()
    else:
        # Default: run once
        run_once()

if __name__ == "__main__":
    main()
