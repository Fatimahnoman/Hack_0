"""
Gmail OAuth - Manual Authorization Flow
Run this script to generate an authorization URL, then paste the URL from your browser back.
"""

import os
import json
from google_auth_oauthlib.flow import Flow

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")

def main():
    print("=" * 70)
    print("Gmail OAuth - Manual Authorization")
    print("=" * 70)
    
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"ERROR: credentials.json not found at {CREDENTIALS_FILE}")
        return
    
    flow = Flow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    
    # Use a redirect URI that matches your credentials.json
    flow.redirect_uri = "http://localhost"
    
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    
    print("\n1. Copy and paste this URL into your browser:")
    print("-" * 70)
    print(authorization_url)
    print("-" * 70)
    
    print("\n2. Sign in with your Google account")
    print("3. Grant the requested permissions")
    print("4. After authorization, you'll see a page like 'localhost says'")
    print("5. Copy the ENTIRE URL from your browser's address bar")
    print("   (It will look like: http://localhost/?code=4/0A...&state=...)")
    print("\n6. Paste the full URL below:")
    
    redirect_url = input("\nEnter the full redirect URL: ").strip()
    
    try:
        flow.fetch_token(authorization_response=redirect_url)
        creds = flow.credentials
        
        # Save token
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        
        print("\n" + "=" * 70)
        print("SUCCESS! Token saved to token.json")
        print("=" * 70)
        print(f"\nToken expires: {creds.expiry}")
        print(f"Scopes: {creds.scopes}")
        print("\nYou can now run: python watchers/gmail_watcher.py")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nMake sure you copied the FULL URL including the 'code=' parameter")

if __name__ == "__main__":
    main()
