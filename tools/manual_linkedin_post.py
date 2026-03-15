"""
LinkedIn Manual Poster
======================
Opens LinkedIn and lets you manually click to post.

Run:
    python tools\manual_linkedin_post.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("[ERROR] Playwright not installed!")
    sys.exit(1)

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_PATH = os.path.join(PROJECT_ROOT, "session", "linkedin")
PENDING_APPROVAL = os.path.join(PROJECT_ROOT, "Pending_Approval")

def get_draft_content(filename):
    """Read draft content from file."""
    filepath = os.path.join(PENDING_APPROVAL, filename)
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract content after "## Content"
    if '## Content' in content:
        parts = content.split('## Content')
        if len(parts) > 1:
            # Get content between ## Content and next ---
            post_content = parts[1].strip()
            if '---' in post_content:
                post_content = post_content.split('---')[0].strip()
            return post_content
    
    return None

def main():
    """Main function."""
    print("=" * 60)
    print("LinkedIn Manual Poster")
    print("=" * 60)
    print()
    
    # List drafts
    if not os.path.exists(PENDING_APPROVAL):
        print("[ERROR] Pending_Approval folder not found!")
        return
    
    drafts = [f for f in os.listdir(PENDING_APPROVAL)
              if f.startswith('linkedin_post_') and f.endswith('.md')]
    
    if not drafts:
        print("[INFO] No drafts found!")
        return
    
    print("Available drafts:")
    print("-" * 60)
    for i, d in enumerate(sorted(drafts), 1):
        print(f"  {i}. {d}")
    print()
    
    # Select draft
    try:
        choice = input(f"Select (1-{len(drafts)}) or 'q': ").strip()
        if choice.lower() == 'q':
            return
        selected = drafts[int(choice) - 1]
    except:
        print("[ERROR] Invalid selection")
        return
    
    # Get content
    content = get_draft_content(selected)
    if not content:
        print("[ERROR] Could not read draft content")
        return
    
    print()
    print("-" * 60)
    print(f"Selected: {selected}")
    print("-" * 60)
    print()
    print("Content preview:")
    print(content[:200] + "..." if len(content) > 200 else content)
    print()
    
    # Copy to clipboard
    import subprocess
    subprocess.run(['clip'], input=content.encode('utf-8'))
    print("[INFO] Content copied to clipboard!")
    print()
    
    # Open LinkedIn
    print("Opening LinkedIn...")
    print("Please:")
    print("  1. Click 'Start a post' box")
    print("  2. Paste content (Ctrl+V)")
    print("  3. Click 'Post' button")
    print()
    print("Browser will stay open for 2 minutes...")
    print()
    
    os.makedirs(SESSION_PATH, exist_ok=True)
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_PATH,
            headless=False,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        
        page = context.pages[0]
        page.goto("https://www.linkedin.com/feed/")
        
        print()
        print("[INFO] LinkedIn opened!")
        print("[INFO] Paste the content and post manually")
        print("[INFO] Browser will auto-close in 2 minutes...")
        
        time.sleep(120)  # Keep open for 2 minutes
        
        context.close()
        print("[INFO] Browser closed.")

if __name__ == "__main__":
    main()
