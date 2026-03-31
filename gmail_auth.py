"""
Gmail OAuth 2.0 - FIXED VERSION
================================
Uses InstalledAppFlow.run_local_server() for proper OAuth flow.

This fixes the "This site can't be reached" error by:
1. Starting a local server automatically
2. Opening browser automatically
3. Catching the redirect properly
4. Saving the token

Run: python gmail_auth.py
"""

import os
import sys
import json
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
except ImportError as e:
    print("=" * 70)
    print("ERROR: Missing required package!")
    print("=" * 70)
    print(f"Import error: {e}")
    print()
    print("Please install required packages:")
    print("  pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    print()
    input("Press Enter to exit...")
    sys.exit(1)

# Configuration
SCRIPT_DIR = Path(__file__).parent.resolve()
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"
TOKEN_FILE = SCRIPT_DIR / "token.json"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify"
]

# For sending emails (if needed later)
SCOPES_SEND = ["https://www.googleapis.com/auth/gmail.send"]


def check_credentials_file():
    """Verify credentials.json exists and is valid."""
    if not CREDENTIALS_FILE.exists():
        print("=" * 70)
        print("ERROR: credentials.json not found!")
        print("=" * 70)
        print(f"Expected location: {CREDENTIALS_FILE}")
        print()
        print("To get credentials.json:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create a new project or select existing")
        print("3. Enable Gmail API")
        print("4. Go to: APIs & Services → Credentials")
        print("5. Click: Create Credentials → OAuth client ID")
        print("6. Application type: Desktop app")
        print("7. Download credentials.json")
        print("8. Place it at: " + str(CREDENTIALS_FILE))
        print()
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Validate JSON
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            data = json.load(f)
        
        if 'installed' not in data:
            print("ERROR: credentials.json must have 'installed' section")
            print("Make sure you downloaded OAuth 2.0 credentials (Desktop app)")
            input("Press Enter to exit...")
            sys.exit(1)
        
        print("✓ credentials.json found and valid")
        return data
        
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in credentials.json: {e}")
        input("Press Enter to exit...")
        sys.exit(1)


def main():
    """Main OAuth flow."""
    print("=" * 70)
    print("Gmail OAuth 2.0 - Authorization")
    print("=" * 70)
    print()
    
    # Check credentials
    creds_data = check_credentials_file()
    
    # Check for existing token
    if TOKEN_FILE.exists():
        print()
        print("Found existing token.json")
        print("Do you want to:")
        print("  1. Use existing token (skip authorization)")
        print("  2. Delete and create new token (re-authorize)")
        print()
        
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            # Validate existing token
            try:
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
                
                if creds.valid:
                    print()
                    print("=" * 70)
                    print("SUCCESS! Using existing token")
                    print("=" * 70)
                    print(f"Token expires: {creds.expiry}")
                    print(f"Scopes: {creds.scopes}")
                    print()
                    print("You can now use Gmail API!")
                    print("Run: python watchers/gmail_watcher.py")
                    print()
                    input("Press Enter to exit...")
                    return
                else:
                    print("Token expired, will create new one...")
                    
            except Exception as e:
                print(f"Error loading token: {e}")
                print("Will create new token...")
        
        # Delete old token
        try:
            TOKEN_FILE.unlink()
            print("Deleted old token.json")
        except:
            pass
    
    print()
    print("=" * 70)
    print("Starting OAuth Authorization Flow")
    print("=" * 70)
    print()
    print("INSTRUCTIONS:")
    print("1. Browser will open automatically")
    print("2. Sign in with your Google account")
    print("3. Grant the requested permissions")
    print("4. After authorization, browser will show 'Success!' or redirect")
    print("5. Script will continue automatically")
    print()
    print("If browser doesn't open, copy the URL and paste in browser manually")
    print()
    print("Starting in 3 seconds...")
    
    for i in range(3, 0, -1):
        print(f"  {i}...")
        import time
        time.sleep(1)
    
    print()
    print("Opening browser...")
    
    try:
        # Create flow
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES
        )
        
        # Run local server (this handles the redirect properly)
        # It starts a server on a random available port
        creds = flow.run_local_server(
            port=0,  # Use any available port
            host='localhost',
            bind_addr=None,
            authorization_prompt_message='Opening browser... ',
            success_message='Success! You can close this browser window.',
            timeout_seconds=300,  # 5 minute timeout
            open_browser=True  # Open browser automatically
        )
        
        # Save token
        print()
        print("Saving token...")
        
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            f.write(creds.to_json())
        
        print()
        print("=" * 70)
        print("✓✓✓ SUCCESS! OAuth authorization complete! ✓✓✓")
        print("=" * 70)
        print()
        print(f"Token saved to: {TOKEN_FILE}")
        print(f"Token expires: {creds.expiry}")
        print(f"Scopes: {creds.scopes}")
        print()
        print("Next steps:")
        print("  - Run: python watchers/gmail_watcher.py")
        print("  - Or: python silver/watchers/gmail_watcher.py")
        print()
        print("=" * 70)
        
        # Keep window open
        input("Press Enter to exit...")
        
    except Exception as e:
        print()
        print("=" * 70)
        print("ERROR: Authorization failed!")
        print("=" * 70)
        print()
        print(f"Error: {e}")
        print()
        print("Common solutions:")
        print("1. Check that credentials.json is valid")
        print("2. Make sure Gmail API is enabled in Google Cloud Console")
        print("3. Try running as Administrator")
        print("4. Check if port 8080 is available (or another port)")
        print("5. Disable firewall/antivirus temporarily")
        print()
        
        # Try alternative: manual URL flow
        print()
        print("ALTERNATIVE: Manual authorization")
        print("=" * 70)
        print()
        
        try:
            # Create flow with manual redirect
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )
            
            # Use out-of-band flow
            auth_url, _ = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="consent"
            )
            
            print()
            print("Copy this URL and paste in your browser:")
            print("-" * 70)
            print(auth_url)
            print("-" * 70)
            print()
            print("After granting permission, you'll see a page with a code.")
            print("Copy the ENTIRE URL from your browser's address bar.")
            print("It will look like: http://localhost/?code=4/0A...&state=...")
            print()
            
            redirect_url = input("Paste the full redirect URL here: ").strip()
            
            # Exchange code for token
            flow.fetch_token(authorization_response=redirect_url)
            creds = flow.credentials
            
            # Save token
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                f.write(creds.to_json())
            
            print()
            print("=" * 70)
            print("✓ SUCCESS! Token saved via manual flow")
            print("=" * 70)
            input("Press Enter to exit...")
            
        except Exception as e2:
            print()
            print("=" * 70)
            print("Both automatic and manual flows failed!")
            print("=" * 70)
            print(f"Error: {e2}")
            print()
            print("Please check:")
            print("1. credentials.json is correct")
            print("2. Gmail API is enabled")
            print("3. OAuth consent screen is configured")
            print("4. You're using a supported browser")
            print()
            input("Press Enter to exit...")
            sys.exit(1)


if __name__ == "__main__":
    main()
