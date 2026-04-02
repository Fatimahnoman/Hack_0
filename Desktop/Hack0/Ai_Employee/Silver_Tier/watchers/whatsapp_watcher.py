"""
WhatsApp Watcher - ULTIMATE VERSION
Uses JavaScript to extract ALL text from WhatsApp Web
"""

import os
import re
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

# Config
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SESSION_PATH = PROJECT_ROOT / "Silver_Tier" / "sessions" / "whatsapp_session"
NEEDS_ACTION_FOLDER = PROJECT_ROOT / "Bronze_Tier" / "Needs_Action"
LOGS_FOLDER = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_FOLDER / "whatsapp_ultimate.log"
CHECK_INTERVAL = 30

KEYWORDS = ["urgent", "asap", "invoice", "payment", "help", "meeting", "due", "bill", "quote", "contract", "reply", "now", "important", "kindly", "please"]

# Setup
LOGS_FOLDER.mkdir(parents=True, exist_ok=True)
NEEDS_ACTION_FOLDER.mkdir(parents=True, exist_ok=True)
SESSION_PATH.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

processed = set()

def create_file(chat_name, message, keywords_list):
    """Create .md file in Bronze_Tier/Needs_Action"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r"[^a-zA-Z0-9]", "_", chat_name[:30])
    filename = f"WHATSAPP_{safe_name}_{ts}.md"
    filepath = NEEDS_ACTION_FOLDER / filename

    content = f"""---
type: whatsapp
from: {chat_name}
chat_name: {chat_name}
latest_message: {message}
received: {datetime.now().isoformat()}
priority: high
status: pending
keywords_matched: {', '.join(keywords_list)}
---

## WhatsApp Message from {chat_name}

{message}

## Suggested Actions
- [ ] Reply to sender
- [ ] Process request
- [ ] Mark as processed

---
*Imported: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"✓ CREATED: {filename}")
    print(f">>> CREATED: {filename}")
    return filename

def extract_messages_js(page):
    """Use JavaScript to extract ALL messages from WhatsApp Web"""

    result = page.evaluate('''() => {
        const messages = [];

        // Get ALL text content from the page
        const allText = document.body.innerText;
        const lines = allText.split('\\n').filter(l => l.trim().length > 0);

        console.log('Total lines:', lines.length);

        // Look for lines containing keywords
        const keywords = ["urgent", "asap", "invoice", "payment", "help", "meeting", "due", "bill", "quote", "contract", "reply", "now", "important", "kindly", "please"];

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();

            // Skip short lines, timestamps, system messages
            if (line.length < 5 || line.length > 200) continue;
            if (/^\\d+:\\d+/.test(line)) continue;
            if (line.startsWith('Yesterday') || line.startsWith('Today')) continue;
            if (line === 'WhatsApp Web') continue;

            // Check for keywords
            const lower = line.toLowerCase();
            const matched = [];

            for (const kw of keywords) {
                if (lower.includes(kw)) {
                    matched.push(kw);
                }
            }

            if (matched.length > 0) {
                // Try to find sender (usually on previous lines)
                let sender = 'Unknown';
                for (let j = Math.max(0, i-10); j < i; j++) {
                    const prevLine = lines[j].trim();
                    if (prevLine.length >= 2 && prevLine.length <= 40 &&
                        !/^\\d+:\\d+/.test(prevLine) &&
                        prevLine !== 'WhatsApp Web' &&
                        !keywords.some(k => prevLine.toLowerCase().includes(k))) {
                        sender = prevLine;
                        break;
                    }
                }

                messages.push({
                    sender: sender,
                    message: line,
                    keywords: matched,
                    lineNum: i
                });

                console.log('FOUND:', sender, '-', line.substring(0, 50), matched);
            }
        }

        return messages;
    }''')

    return result

def main():
    print("=" * 70)
    print("WhatsApp Watcher - ULTIMATE VERSION")
    print("=" * 70)
    print(f"Keywords: {', '.join(KEYWORDS)}")
    print("=" * 70)

    logger.info("=" * 70)
    logger.info("WhatsApp Ultimate Watcher Started")
    logger.info("=" * 70)

    playwright = sync_playwright().start()

    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(SESSION_PATH),
        headless=False,
        channel="chrome",
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
    )

    page = context.pages[0] if context.pages else context.new_page()

    print("\nOpening WhatsApp Web...")
    page.goto("https://web.whatsapp.com", timeout=60000)

    print("Waiting for WhatsApp to load...")
    print("(Scan QR code if shown)")

    try:
        page.wait_for_selector('span[dir="auto"]', timeout=120000)
        time.sleep(5)
        print("✓ Loaded!")
    except Exception as e:
        print(f"✗ Error: {e}")
        context.close()
        playwright.stop()
        return

    print("\nMonitoring for keywords...\n")
    logger.info("Monitoring started")

    try:
        while True:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking...")

            try:
                messages = extract_messages_js(page)

                logger.info(f"Found {len(messages)} lines with keywords")

                for msg in messages:
                    sender = msg.get('sender', 'Unknown')
                    message = msg.get('message', '')
                    keywords = msg.get('keywords', [])

                    msg_id = f"{sender}:{message[:40]}"

                    if msg_id not in processed:
                        logger.info(f"MATCH: {sender} | {message[:50]} | {keywords}")
                        print(f"  *** {sender}: {message[:50]}... {keywords}")
                        create_file(sender, message, keywords)
                        processed.add(msg_id)

                if not messages:
                    logger.info("No new messages with keywords")
                    print("  No new messages")

            except Exception as e:
                logger.error(f"Error: {e}")

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        context.close()
        playwright.stop()

if __name__ == "__main__":
    main()
