"""
Gmail Watcher for Bronze Tier
Checks for unread important emails every 300 seconds
Creates .md files in Vault/Needs_Action/ for each new email
"""

import os
import time
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configuration
CHECK_INTERVAL = 300  # seconds
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'token.json')
VAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Vault')
NEEDS_ACTION_PATH = os.path.join(VAULT_PATH, 'Needs_Action')


def get_gmail_service():
    """Authenticate and build Gmail service."""
    creds = None
    
    # Note: For now this is placeholder - credentials not set up yet
    # This will work once credentials.json is properly configured
    print(f"[LOG] Checking credentials at: {CREDENTIALS_FILE}")
    
    if not os.path.exists(CREDENTIALS_FILE):
        print("[LOG] credentials.json not found - running in demo mode")
        return None
    
    try:
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print("[LOG] No valid token - authentication required")
                return None
        
        service = build('gmail', 'v1', credentials=creds)
        print("[LOG] Gmail service connected")
        return service
    except Exception as e:
        print(f"[LOG] Auth error: {e}")
        return None


def create_email_file(message_id, from_addr, subject, received_time, snippet):
    """Create .md file in Vault/Needs_Action/ for the email."""
    filename = f"EMAIL_{message_id}.md"
    filepath = os.path.join(NEEDS_ACTION_PATH, filename)
    
    content = f"""From: {from_addr}
Subject: {subject}
Received: {received_time}
Priority: high

{snippet}
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[LOG] Created: {filename}")
    return filepath


def check_unread_emails(service):
    """Check for unread important emails."""
    if service is None:
        print("[LOG] Service not available - skipping email check")
        return 0
    
    try:
        # Query for unread important emails
        results = service.users().messages().list(
            userId='me',
            q='is:unread is:important',
            maxResults=10
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print("[LOG] No unread important emails")
            return 0
        
        count = 0
        for message in messages:
            msg_id = message['id']
            msg = service.users().messages().get(
                userId='me',
                id=msg_id,
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = msg['payload']['headers']
            from_addr = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            received_time = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            
            # Get snippet
            snippet = msg.get('snippet', '')
            
            # Create file in Needs_Action
            create_email_file(msg_id, from_addr, subject, received_time, snippet)
            count += 1
        
        print(f"[LOG] Processed {count} new email(s)")
        return count
    
    except Exception as e:
        print(f"[LOG] Error checking emails: {e}")
        return 0


def main():
    """Main watcher loop."""
    print("=" * 50)
    print("Gmail Watcher - Bronze Tier")
    print(f"Checking every {CHECK_INTERVAL} seconds")
    print(f"Output: {NEEDS_ACTION_PATH}")
    print("=" * 50)
    
    # Ensure Needs_Action folder exists
    os.makedirs(NEEDS_ACTION_PATH, exist_ok=True)
    
    # Get Gmail service
    service = get_gmail_service()
    
    while True:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{timestamp}] Checking for new emails...")
            
            check_unread_emails(service)
            
            print(f"[LOG] Sleeping for {CHECK_INTERVAL} seconds...")
            time.sleep(CHECK_INTERVAL)
        
        except KeyboardInterrupt:
            print("\n[LOG] Watcher stopped by user")
            break
        except Exception as e:
            print(f"[LOG] Error in main loop: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
