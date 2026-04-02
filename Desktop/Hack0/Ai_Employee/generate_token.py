"""
Quick Token Generator with Authorization Code
"""
import os
import json
from google_auth_oauthlib.flow import Flow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly"
]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

print("=" * 70)
print("Token Generator")
print("=" * 70)

# Authorization code from user
auth_code = "4/1Aci98E8URILx0ZQxNDsqpMjZNYmkH3hDymYP9XRE6fVLmHm-BS24JNeWdi0"

print(f"\nUsing authorization code: {auth_code[:30]}...")

flow = Flow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

try:
    # Exchange code for token
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    flow.fetch_token(code=auth_code)
    creds = flow.credentials
    
    # Save token
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    
    print("\n" + "=" * 70)
    print("✅ SUCCESS! Token saved to token.json")
    print("=" * 70)
    print(f"\nToken expires: {creds.expiry}")
    print(f"Scopes: {creds.scopes}")
    print("\nNow orchestrator can send emails!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nTry again with a fresh authorization code")
