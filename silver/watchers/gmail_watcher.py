"""
Gmail Watcher - Gold Tier (Fixed)
==================================
Monitors Gmail inbox for unread important emails.
Creates files in gold/needs_action/ folder first.

Install: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
Setup:
  1. Download credentials.json to project root
  2. Run once to authorize
Run: python silver/watchers/gmail_watcher.py
"""

import os
import re
import sys
import time
import base64
import logging
from datetime import datetime
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError as e:
    print(f"[ERROR] Missing: {e}")
    print("Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# =============================================================================
# CONFIGURATION - GOLD TIER FOLDERS
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GOLD_DIR = PROJECT_ROOT / "gold"

# CRITICAL: Gold Tier folder structure
NEEDS_ACTION_FOLDER = GOLD_DIR / "needs_action"
LOGS_FOLDER = GOLD_DIR / "logs"

# Credentials
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Ensure folders exist
NEEDS_ACTION_FOLDER.mkdir(parents=True, exist_ok=True)
LOGS_FOLDER.mkdir(parents=True, exist_ok=True)

# Settings
CHECK_INTERVAL = 60  # seconds
IMPORTANT_KEYWORDS = [
    "urgent", "sales", "payment", "invoice", "deal", "order",
    "client", "customer", "quotation", "proposal", "overdue",
    "follow up", "meeting", "booking", "asap", "test"
]

# Track processed
processed_emails = set()
PROCESSED_FILE = LOGS_FOLDER / "gmail_processed.txt"

# =============================================================================
# LOGGING
# =============================================================================

def setup_logging():
    log_file = LOGS_FOLDER / f"gmail_{datetime.now().strftime('%Y%m%d')}.log"
    
    logger = logging.getLogger("GmailWatcher")
    logger.setLevel(logging.INFO)
    logger.handlers = []
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# =============================================================================
# MESSAGE PROCESSING
# =============================================================================

def load_processed():
    global processed_emails
    if PROCESSED_FILE.exists():
        try:
            with open(PROCESSED_FILE, 'r', encoding='utf-8') as f:
                processed_emails = set(line.strip() for line in f)
            logger.info(f"Loaded {len(processed_emails)} processed emails")
        except:
            pass

def save_processed(email_id: str):
    processed_emails.add(email_id)
    try:
        with open(PROCESSED_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{email_id}\n")
    except:
        pass

def get_priority(subject: str, snippet: str) -> str:
    text = f"{subject} {snippet}".lower()
    if "urgent" in text or "asap" in text:
        return "high"
    if "invoice" in text or "payment" in text or "order" in text:
        return "medium"
    return "normal"

def create_needs_action_file(email_data: dict, logger) -> Path:
    """CRITICAL: Create file in gold/needs_action/ folder"""
    priority = get_priority(email_data['subject'], email_data['snippet'])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    safe_sender = re.sub(r"[^a-zA-Z0-9]", "_", email_data['from'][:20]) or "Unknown"
    filename = f"GMAIL_{safe_sender}_{timestamp}.md"
    filepath = NEEDS_ACTION_FOLDER / filename
    
    content = f"""---
type: email
from: {email_data['from']}
to: 
subject: {email_data['subject']}
priority: {priority}
status: pending
created_at: {datetime.now().isoformat()}
message_id: {email_data['id']}
---

## Email Content

{email_data['body']}

## Metadata

- **From:** {email_data['from']}
- **Subject:** {email_data['subject']}
- **Priority:** {priority}
- **Received:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---
*Gmail Watcher - Gold Tier*
"""
    
    with open(filepath, "w", encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"✓ CREATED: {filename} in needs_action/")
    return filepath

# =============================================================================
# GMAIL API
# =============================================================================

def get_gmail_service():
    """Get Gmail API service."""
    creds = None
    
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            logger.error(f"Token error: {e}")
            creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Token refreshed")
            except Exception as e:
                logger.error(f"Refresh failed: {e}")
                creds = None
        
        if not creds:
            if not CREDENTIALS_FILE.exists():
                logger.error("credentials.json not found!")
                return None
            
            logger.info("Starting OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)
                
            with open(str(TOKEN_FILE), 'w') as token:
                    token.write(creds.to_json())
                
                logger.info("✓ OAuth completed")
            except Exception as e:
                logger.error(f"OAuth failed: {e}")
                return None
    
    return build('gmail', 'v1', credentials=creds)

def check_emails(service, logger):
    """Check Gmail for unread emails with keywords."""
    try:
        # Get unread messages
        results = service.users().messages().list(
            userId='me',
            q='is:unread',
            maxResults=10
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            logger.debug("No unread emails")
            return 0
        
        new_tasks = 0
        
        for msg in messages:
            try:
                # Get message details
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Snippet']
                ).execute()
                
                # Extract data
                headers = message['payload']['headers']
                subject = ""
                sender = ""
                snippet = message.get('snippet', '')
                
                for header in headers:
                    if header['name'] == 'Subject':
                        subject = header['value']
                    elif header['name'] == 'From':
                        sender = header['value']
                
                # Check if processed
                if msg['id'] in processed_emails:
                    continue
                
                # Check keywords
                text_to_check = f"{subject} {snippet}".lower()
                if any(kw in text_to_check for kw in IMPORTANT_KEYWORDS):
                    # Get full body
                    try:
                        full_msg = service.users().messages().get(
                            userId='me',
                            id=msg['id'],
                            format='full'
                        ).execute()
                        
                        body = ""
                        if 'parts' in full_msg['payload']:
                            for part in full_msg['payload']['parts']:
                                if part['mimeType'] == 'text/plain':
                                    if 'data' in part['body']:
                                        body = base64.urlsafe_b64decode(
                                            part['body']['data'] + "==="
                                        ).decode('utf-8', errors='ignore')
                                        break
                        elif 'body' in full_msg['payload']:
                            if 'data' in full_msg['payload']['body']:
                                body = base64.urlsafe_b64decode(
                                    full_msg['payload']['body']['data'] + "==="
                                ).decode('utf-8', errors='ignore')
                        
                        if not body:
                            body = snippet
                    
                    except Exception as e:
                        body = snippet
                    
                    # Create task file
                    email_data = {
                        'id': msg['id'],
                        'from': sender,
                        'subject': subject,
                        'snippet': snippet,
                        'body': body
                    }
                    
                    create_needs_action_file(email_data, logger)
                    save_processed(msg['id'])
                    new_tasks += 1
                    logger.info(f"📧 Found: {subject[:50]}...")
                    
            except Exception as e:
                logger.debug(f"Error processing message: {e}")
                continue
        
        return new_tasks
        
    except Exception as e:
        logger.error(f"Error checking emails: {e}")
        return 0

# =============================================================================
# MAIN
# =============================================================================

def main():
    logger.info("=" * 70)
    logger.info("GMAIL WATCHER - GOLD TIER")
    logger.info("=" * 70)
    logger.info(f"Tasks folder: {NEEDS_ACTION_FOLDER}")
    logger.info(f"Check interval: {CHECK_INTERVAL}s")
    logger.info("=" * 70)
    
    load_processed()
    
    logger.info("Connecting to Gmail API...")
    service = get_gmail_service()
    
    if not service:
        logger.error("Failed to connect to Gmail API")
        logger.info("Please ensure credentials.json exists and OAuth is completed")
        return
    
    logger.info("✓ Gmail API connected")
    logger.info("Starting monitoring loop...")
    
    consecutive_errors = 0
    
    while True:
        try:
            new_tasks = check_emails(service, logger)
            
            if new_tasks > 0:
                logger.info(f"✓ Created {new_tasks} new task(s) in needs_action/")
                consecutive_errors = 0
            else:
                consecutive_errors += 1
                if consecutive_errors > 10:
                    logger.info("Still monitoring...")
                    consecutive_errors = 0
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("\n👋 Stopping...")
            break
        except Exception as e:
            logger.error(f"Loop error: {e}")
            consecutive_errors += 1
            if consecutive_errors > 10:
                # Reconnect service
                logger.info("Reconnecting to Gmail API...")
                service = get_gmail_service()
                consecutive_errors = 0
            time.sleep(CHECK_INTERVAL)
    
    logger.info("Gmail Watcher stopped")

if __name__ == "__main__":
    main()
