# Actions MCP Server - Silver Tier

FastMCP-based server for AI Employee actions: **Email** + **Instagram**.

---

## 🚀 Quick Start

### Run Command

```bash
python mcp_servers/actions_mcp/server.py
```

Or from the `mcp_servers/actions_mcp` folder:

```bash
python server.py
```

---

## 📦 Installation

```bash
# Install all dependencies
pip install fastmcp google-api-python-client google-auth-httplib2 google-auth-oauthlib playwright

# Install Playwright browsers (required for Instagram)
playwright install chromium
```

---

## 🔧 Environment Requirements

### 1. Gmail API Credentials

**File:** `credentials.json` (project root)

```json
{
  "web": {
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost:8080"],
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token"
  }
}
```

**First-time OAuth:**
1. Run any Gmail function
2. Browser opens for authorization
3. `token.json` will be created automatically

---

### 2. Instagram Credentials

**File:** `.env` (project root)

```env
# Instagram (instagrapi)
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password
```

**First-time Login:**
- Server will auto-login and save session
- Session stored in `sessions/instagram_session/`
- Subsequent runs reuse the saved session

---

## 🛠️ Available Tools

### `send_email`

Send emails via Gmail API with optional attachment.

```python
await send_email(
    to="user@example.com",
    subject="Hello",
    body="This is a test email",
    attachment_path="C:/files/doc.pdf"  # Optional
)
```

**Returns:** `✓ Email sent successfully! Message ID: <id>`

---

### `post_to_instagram`

Post to Instagram using Playwright (headless browser).

```python
await post_to_instagram(
    caption="Amazing sunset! 🌅 #photography",
    image_path="C:/photos/sunset.jpg"  # Optional
)
```

**Returns:** `✓ Instagram post created successfully!`

---

### `check_approval_status`

Check if an action has human approval.

```python
await check_approval_status("WHATSAPP_20260222191008")
```

**Returns:**
- `✓ Action <id> is COMPLETED`
- `✓ Action <id> is APPROVED`
- `⏳ Action <id> is PENDING approval`
- `Action <id> not found`

---

## 📁 File Structure

```
Silver_Tier/
├── mcp_servers/
│   └── actions_mcp/
│       ├── server.py           # MCP server
│       └── README.md           # This file
│
├── credentials.json            # Gmail API credentials
├── token.json                  # OAuth token (auto-created)
├── .env                        # Instagram credentials
│
└── sessions/
    └── instagram_session/      # Persistent Instagram session
```

---

## 🔒 Security

| File | Status | Notes |
|------|--------|-------|
| `credentials.json` | ⚠️ Private | Gmail API keys |
| `token.json` | ⚠️ Private | OAuth token |
| `.env` | ⚠️ Private | Instagram password |
| `sessions/` | ⚠️ Private | Login session data |

**`.gitignore` already configured** - these files won't be committed.

---

## 🧪 Testing

### Test Email

```python
import asyncio
from mcp_servers.actions_mcp.server import send_email

async def test():
    result = await send_email(
        to="test@example.com",
        subject="Test from MCP",
        body="This is a test email from Actions MCP Server"
    )
    print(result)

asyncio.run(test())
```

### Test Instagram Post

```python
import asyncio
from mcp_servers.actions_mcp.server import post_to_instagram

async def test():
    result = await post_to_instagram(
        caption="Test post from MCP! 🤖 #automation"
    )
    print(result)

asyncio.run(test())
```

---

## 🔗 Integration

### Claude Desktop (MCP Client)

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "actions_mcp": {
      "command": "python",
      "args": ["E:/Hackathon_Zero/Silver_Tier/mcp_servers/actions_mcp/server.py"],
      "cwd": "E:/Hackathon_Zero/Silver_Tier"
    }
  }
}
```

### Python Client

```python
from mcp import ClientSession
from mcp.client.stdio import stdio_client

async with stdio_client(['python', 'mcp_servers/actions_mcp/server.py']) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # List tools
        tools = await session.list_tools()
        
        # Call tool
        result = await session.call_tool('send_email', {
            'to': 'user@example.com',
            'subject': 'Hello',
            'body': 'Test email'
        })
```

---

## 🐛 Troubleshooting

### Gmail: "Token not found"

```bash
# Delete old token and re-authenticate
del token.json
# Run send_email again - browser will open for OAuth
```

### Instagram: "Login failed"

1. Check `.env` has correct credentials
2. Try manual login at instagram.com
3. Clear session: `rmdir /s /q sessions\instagram_session`
4. Run server again

### Playwright: "Browser not found"

```bash
# Install Chromium browser
playwright install chromium
```

### MCP: "Server not responding"

```bash
# Test server directly
python mcp_servers/actions_mcp/server.py

# Should show:
# Actions MCP Server - Silver Tier
# Press Ctrl+C to stop
```

---

## 📊 Server Output

When running, you should see:

```
==================================================
Actions MCP Server - Silver Tier
==================================================
Project Root: E:\Hackathon_Zero\Silver_Tier
Vault Path: E:\Hackathon_Zero\Silver_Tier\Vault
Instagram Session: E:\Hackathon_Zero\Silver_Tier\sessions\instagram_session
==================================================

Run command: python server.py
Press Ctrl+C to stop
```

---

## ✅ Checklist

- [ ] Dependencies installed (`pip install ...`)
- [ ] Playwright browsers installed (`playwright install`)
- [ ] `credentials.json` configured
- [ ] `.env` has Instagram credentials
- [ ] Server runs without errors
- [ ] Test email sent successfully
- [ ] Test Instagram post created

---

**Server Ready! 🚀**

For issues, check console output for detailed error messages.
