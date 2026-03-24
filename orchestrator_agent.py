"""
Orchestrator Agent - Auto Reply & File Mover
=============================================
Monitors Pending_Approval/Approved folder and:
1. Sends email replies automatically
2. Moves files to Done folder
3. Logs all actions

Run: python orchestrator_agent.py
Or via PM2: pm2 start orchestrator_agent.py
"""

import os
import shutil
import time
import logging
from datetime import datetime
from pathlib import Path

# Gmail API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except ImportError as e:
    print(f"[ERROR] Missing Gmail dependency: {e}")
    print("Install: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent
INBOX_FOLDER = PROJECT_ROOT / "Bronze_Tier" / "Inbox"
NEEDS_ACTION_FOLDER = PROJECT_ROOT / "Bronze_Tier" / "Needs_Action"
PLANS_FOLDER = PROJECT_ROOT / "Bronze_Tier" / "Plans"
PENDING_APPROVAL_FOLDER = PROJECT_ROOT / "Bronze_Tier" / "Pending_Approval"
APPROVED_FOLDER = PROJECT_ROOT / "Bronze_Tier" / "Approved"
DONE_FOLDER = PROJECT_ROOT / "Bronze_Tier" / "Done"
LOGS_FOLDER = PROJECT_ROOT / "logs"
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"

CHECK_INTERVAL = 10  # seconds
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Setup logging
def setup_logging():
    LOGS_FOLDER.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_FOLDER / f"orchestrator_{datetime.now().strftime('%Y-%m-%d')}.log"
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
    """Ensure required directories exist."""
    for folder in [APPROVED_FOLDER, DONE_FOLDER, LOGS_FOLDER]:
        folder.mkdir(parents=True, exist_ok=True)


def get_gmail_service():
    """Authenticate and return Gmail service."""
    creds = None
    
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing credentials...")
            creds.refresh(Request())
        else:
            logger.error("Gmail credentials not found. Run gmail_auth.py first.")
            return None
        
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    
    return build("gmail", "v1", credentials=creds)


def extract_email_data(filepath: Path) -> dict:
    """Extract email data from markdown file."""
    content = filepath.read_text(encoding='utf-8')
    
    data = {
        'type': '',
        'from': '',
        'subject': '',
        'content': '',
        'reply_draft': ''
    }
    
    # Extract YAML frontmatter
    if '---' in content:
        parts = content.split('---')
        if len(parts) >= 2:
            yaml_content = parts[1]
            
            # Parse fields
            for line in yaml_content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'from':
                        # Extract email from "Name <email>"
                        if '<' in value and '>' in value:
                            data['from'] = value.split('<')[1].split('>')[0]
                        else:
                            data['from'] = value
                    elif key == 'subject':
                        data['subject'] = value
                    elif key == 'type':
                        data['type'] = value
    
    # Extract email content
    if '## Email Content' in content:
        data['content'] = content.split('## Email Content')[1].split('---')[0].strip()
    
    # Extract reply draft
    if '## Reply Draft' in content:
        data['reply_draft'] = content.split('## Reply Draft')[1].split('---')[0].strip()
        # Remove "Draft generated automatically" line
        if '*Draft generated' in data['reply_draft']:
            data['reply_draft'] = data['reply_draft'].split('*Draft generated')[0].strip()
    
    return data


def generate_reply(data: dict) -> str:
    """Generate polite reply based on email content."""
    content_lower = data['content'].lower()
    
    # Check for invoice/payment request
    if 'invoice' in content_lower or 'payment' in content_lower:
        reply = f"""Hello,

Thank you for your email regarding: {data['subject']}

We have received your request and it is being processed. Our team will review the details and get back to you within 24-48 hours.

If you have any urgent questions, please don't hesitate to contact us.

Best regards,
AI Employee Team
"""
    elif 'urgent' in content_lower:
        reply = f"""Hello,

Thank you for your urgent message: {data['subject']}

We have received your request and are treating it as high priority. A team member will respond to you as soon as possible.

Best regards,
AI Employee Team
"""
    else:
        reply = f"""Hello,

Thank you for your email: {data['subject']}

We have received your message and will respond within 24-48 hours.

Best regards,
AI Employee Team
"""
    
    return reply


def send_email_reply(to: str, subject: str, body: str) -> bool:
    """Send email reply via Gmail API."""
    try:
        service = get_gmail_service()
        if not service:
            return False
        
        # Create MIME message
        reply_subject = f"Re: {subject}"
        mime_message = '\n'.join([
            f"To: {to}",
            f"From: me",
            f"Subject: {reply_subject}",
            'MIME-Version: 1.0',
            'Content-Type: text/plain; charset=utf-8',
            '',
            body
        ])
        
        # Encode message
        import base64
        encoded_message = base64.urlsafe_b64encode(mime_message.encode('utf-8')).decode('utf-8')
        
        # Send email
        message = service.users().messages().send(
            userId='me',
            body={'raw': encoded_message}
        ).execute()
        
        logger.info(f"Email sent! Message ID: {message['id']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def create_done_record(filepath: Path, email_data: dict, reply_sent: bool) -> str:
    """Create record in Done folder."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"DONE_{filepath.stem}_{timestamp}.md"
    dest_path = DONE_FOLDER / filename
    
    content = filepath.read_text(encoding='utf-8')
    
    done_content = f"""---
type: completed_email
original_file: {filepath.name}
from: {email_data['from']}
subject: {email_data['subject']}
reply_sent: {reply_sent}
completed_at: {datetime.now().isoformat()}
status: completed
---

# Completed

## Original Content
{content}

## Action Taken
- Reply sent: {reply_sent}
- Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
*Processed by Orchestrator Agent*
"""
    
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(done_content)
    
    return filename


def process_approved_file(filepath: Path) -> bool:
    """Process a single approved file."""
    logger.info(f"Processing: {filepath.name}")

    # Extract email data
    email_data = extract_email_data(filepath)

    if not email_data['from']:
        logger.error(f"Could not extract 'from' field from {filepath.name}")
        return False

    logger.info(f"  To: {email_data['from']}")
    logger.info(f"  Subject: {email_data['subject']}")

    # Use reply draft if available, otherwise generate
    if email_data.get('reply_draft'):
        logger.info(f"  ✓ Using reply draft from file")
        reply = email_data['reply_draft']
    else:
        logger.info(f"  → Generating reply")
        reply = generate_reply(email_data)

    # Send reply
    reply_sent = send_email_reply(email_data['from'], email_data['subject'], reply)

    if reply_sent:
        logger.info(f"  ✓ Reply sent to {email_data['from']}")
    else:
        logger.warning(f"  ✗ Reply failed (credentials issue?)")

    # Add completion info to the SAME file (don't create new file)
    file_content = filepath.read_text(encoding='utf-8')
    file_content += f"""

---
## Completion Info
- Reply sent: {reply_sent}
- Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Processed by: Orchestrator Agent
"""
    filepath.write_text(file_content, encoding='utf-8')

    # Move SAME file to Done (just rename with timestamp)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_dest = DONE_FOLDER / f"{filepath.stem}_COMPLETED_{timestamp}.md"
    shutil.move(str(filepath), str(final_dest))
    logger.info(f"  ✓ Moved to Done: {final_dest.name}")

    return True


def check_approved_folder():
    """Check Approved folder for new files."""
    if not APPROVED_FOLDER.exists():
        return 0
    
    files = list(APPROVED_FOLDER.glob("*.md"))
    processed_count = 0
    
    for filepath in files:
        try:
            if process_approved_file(filepath):
                processed_count += 1
        except Exception as e:
            logger.error(f"Error processing {filepath.name}: {e}")
    
    return processed_count


def main():
    """Main function to start Orchestrator Agent."""
    print("=" * 60)
    print("Orchestrator Agent - Auto Reply & File Mover")
    print("=" * 60)
    print(f"Monitoring: {APPROVED_FOLDER}")
    print(f"Destination: {DONE_FOLDER}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print("-" * 60)
    print("WORKFLOW:")
    print("1. Move file to Pending_Approval/Approved/")
    print("2. Agent picks it up automatically")
    print("3. Sends email reply")
    print("4. Moves file to Done/")
    print("=" * 60)
    
    ensure_directories()
    
    # Check credentials
    if not TOKEN_FILE.exists():
        logger.warning("token.json not found. Email replies will fail.")
        logger.warning("Run: python gmail_auth.py")
    
    logger.info("Orchestrator Agent started!")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Agent started!")
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            processed = check_approved_folder()
            
            if processed > 0:
                logger.info(f"Processed {processed} file(s)")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Processed {processed} file(s)")
            
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
        print("\n[INFO] Agent stopped.")


if __name__ == "__main__":
    main()
