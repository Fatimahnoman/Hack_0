"""
Workflow Processor Agent - Auto File Mover
===========================================
Monitors Inbox folder and automatically moves files through workflow:

Inbox → Needs_Action → Plans → Pending_Approval

When user approves (moves to Approved/), Orchestrator sends reply.

Run: python workflow_processor.py
Or via PM2: pm2 start workflow_processor.py
"""

import os
import shutil
import time
import re
import logging
from datetime import datetime
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent
INBOX_FOLDER = PROJECT_ROOT / "Bronze_Tier" / "Inbox"
NEEDS_ACTION_FOLDER = PROJECT_ROOT / "Bronze_Tier" / "Needs_Action"
PLANS_FOLDER = PROJECT_ROOT / "Bronze_Tier" / "Plans"
PENDING_APPROVAL_FOLDER = PROJECT_ROOT / "Bronze_Tier" / "Pending_Approval"
APPROVED_FOLDER = PROJECT_ROOT / "Bronze_Tier" / "Approved"  # Root level, not inside Pending_Approval
LOGS_FOLDER = PROJECT_ROOT / "logs"

CHECK_INTERVAL = 10  # seconds

# Keywords to detect (case-insensitive)
IMPORTANT_KEYWORDS = ["urgent", "invoice", "payment", "sales"]

# Setup logging
def setup_logging():
    LOGS_FOLDER.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_FOLDER / f"workflow_{datetime.now().strftime('%Y-%m-%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()


def ensure_directories():
    """Ensure all workflow directories exist."""
    for folder in [INBOX_FOLDER, NEEDS_ACTION_FOLDER, PLANS_FOLDER, PENDING_APPROVAL_FOLDER]:
        folder.mkdir(parents=True, exist_ok=True)


def extract_yaml_data(filepath: Path) -> dict:
    """Extract data from YAML frontmatter."""
    content = filepath.read_text(encoding='utf-8')
    
    data = {
        'type': '',
        'from': '',
        'subject': '',
        'priority': 'normal',
        'status': 'pending'
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


def has_important_keywords(content: str) -> bool:
    """Check if content has important keywords."""
    content_lower = content.lower()
    return any(keyword in content_lower for keyword in IMPORTANT_KEYWORDS)


def move_file(src: Path, dest_folder: Path, prefix: str = "") -> str:
    """Move file to destination folder."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}{src.name}" if prefix else src.name
    dest_path = dest_folder / filename
    
    try:
        shutil.move(str(src), str(dest_path))
        logger.info(f"Moved: {src.name} → {dest_folder.name}/")
        return filename
    except Exception as e:
        logger.error(f"Failed to move {src.name}: {e}")
        return ""


def generate_reply_draft(email_data: dict, content: str) -> str:
    """Generate a polite reply draft based on email content."""
    content_lower = content.lower()
    
    # Check for invoice/payment request
    if 'invoice' in content_lower or 'payment' in content_lower:
        reply = f"""## Reply Draft

Dear {email_data['from'].split('<')[0].strip() if '<' in email_data['from'] else email_data['from']},

Thank you for your email regarding: {email_data['subject']}

We have received your request and it is being processed. Our team will review the details and get back to you within 24-48 hours.

If you have any urgent questions, please don't hesitate to contact us.

Best regards,
AI Employee Team

---
*Draft generated automatically - Requires HITL approval before sending*
"""
    elif 'urgent' in content_lower:
        reply = f"""## Reply Draft

Dear {email_data['from'].split('<')[0].strip() if '<' in email_data['from'] else email_data['from']},

Thank you for your urgent message: {email_data['subject']}

We have received your request and are treating it as high priority. A team member will respond to you as soon as possible.

Best regards,
AI Employee Team

---
*Draft generated automatically - Requires HITL approval before sending*
"""
    else:
        reply = f"""## Reply Draft

Dear {email_data['from'].split('<')[0].strip() if '<' in email_data['from'] else email_data['from']},

Thank you for your email: {email_data['subject']}

We have received your message and will respond within 24-48 hours.

Best regards,
AI Employee Team

---
*Draft generated automatically - Requires HITL approval before sending*
"""
    
    return reply


def process_inbox_file(filepath: Path) -> bool:
    """Process a single file from Inbox - automatic workflow."""
    logger.info(f"Processing Inbox file: {filepath.name}")
    
    # Read file content
    content = filepath.read_text(encoding='utf-8')
    
    # Extract YAML data
    yaml_data = extract_yaml_data(filepath)
    
    # Check if it's an email
    if yaml_data['type'] == 'email':
        logger.info(f"  Type: Email from {yaml_data['from']}")
        logger.info(f"  Subject: {yaml_data['subject']}")
        logger.info(f"  Priority: {yaml_data['priority']}")
        
        # Check for important keywords
        if has_important_keywords(content):
            logger.info(f"  ✓ Important keywords detected!")
            
            # Step 1: Move to Needs_Action
            new_name = move_file(filepath, NEEDS_ACTION_FOLDER, "")
            
            if new_name:
                logger.info(f"  → Moved to Needs_Action: {new_name}")
                
                # Step 2: Generate reply draft
                reply_draft = generate_reply_draft(yaml_data, content)
                
                # Add reply draft to the file in Needs_Action
                needs_action_path = NEEDS_ACTION_FOLDER / new_name
                file_content = needs_action_path.read_text(encoding='utf-8')
                file_content += f"\n\n{reply_draft}"
                needs_action_path.write_text(file_content, encoding='utf-8')
                
                # Step 3: Create SEPARATE Plan.md file in Plans folder (STAYS THERE)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                plan_filename = f"PLAN_{yaml_data['subject'].replace(' ', '_')[:30]}_{timestamp}.md"
                plan_path = PLANS_FOLDER / plan_filename
                
                plan_content = f"""---
type: plan
original_file: {new_name}
from: {yaml_data['from']}
subject: {yaml_data['subject']}
priority: {yaml_data['priority']}
created_at: {datetime.now().isoformat()}
status: pending_approval
---

# Action Plan

## Email Summary
- **From:** {yaml_data['from']}
- **Subject:** {yaml_data['subject']}
- **Priority:** {yaml_data['priority']}
- **Received:** {yaml_data.get('received', 'N/A')}

## Proposed Action
{reply_draft}

## Approval Status
- Plan Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Status: Pending Approval
- Awaiting: Move to Approved/ folder

---
*Plan generated automatically by Workflow Processor*
"""
                
                with open(plan_path, 'w', encoding='utf-8') as f:
                    f.write(plan_content)
                logger.info(f"  → Plan created: {plan_filename} (stored in Plans/)")
                
                # Step 4: Move original file to Pending_Approval (with reply draft)
                pending_name = move_file(needs_action_path, PENDING_APPROVAL_FOLDER, "")
                if pending_name:
                    logger.info(f"  → File moved to Pending_Approval: {pending_name}")
                    logger.info(f"  ⏳ WAITING FOR HITL APPROVAL")
                    logger.info(f"  👤 Move to: Bronze_Tier/Approved/ to send reply")
                    return True
            
            return True
        else:
            logger.info(f"  → No important keywords, moving to Plans")
            
            # Move to Plans
            new_name = move_file(filepath, PLANS_FOLDER, "")
            
            if new_name:
                logger.info(f"  → Moved to Plans: {new_name}")
                return True
    
    return False


def check_inbox():
    """Check Inbox folder for new files."""
    if not INBOX_FOLDER.exists():
        return 0
    
    files = list(INBOX_FOLDER.glob("*.md"))
    processed_count = 0
    
    for filepath in files:
        try:
            if process_inbox_file(filepath):
                processed_count += 1
        except Exception as e:
            logger.error(f"Error processing {filepath.name}: {e}")
    
    return processed_count


def main():
    """Main function to start Workflow Processor."""
    print("=" * 60)
    print("Workflow Processor Agent - Auto File Mover")
    print("=" * 60)
    print(f"Monitoring: {INBOX_FOLDER}")
    print(f"Workflow: Inbox -> Needs_Action -> Plans -> Pending_Approval")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print("-" * 60)
    print("WORKFLOW:")
    print("1. Gmail watcher saves to Inbox/")
    print("2. This processor moves to Needs_Action/ (if important)")
    print("3. User reviews and moves to Plans/")
    print("4. User moves to Pending_Approval/")
    print("5. User approves by moving to Approved/")
    print("6. Orchestrator sends reply and moves to Done/")
    print("=" * 60)
    
    ensure_directories()
    
    logger.info("Workflow Processor started!")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Agent started!")
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            processed = check_inbox()
            
            if processed > 0:
                logger.info(f"Processed {processed} file(s)")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Processed {processed} file(s)")
            
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
        print("\n[INFO] Agent stopped.")


if __name__ == "__main__":
    main()
