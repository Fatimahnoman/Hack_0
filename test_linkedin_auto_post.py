"""
LinkedIn Auto-Post Test - Direct Test
======================================
This directly tests LinkedIn auto-posting without waiting for notifications.

Run: python test_linkedin_auto_post.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from watchers.linkedin_watcher_fixed import post_to_linkedin

def main():
    print("=" * 70)
    print("LINKEDIN AUTO-POST TEST")
    print("=" * 70)
    
    # Test content
    test_content = """🚀 Excited to share our latest business update!

We're offering special deals on our services this month. 
Perfect for clients looking for urgent solutions.

#Business #Sales #Professional #Deal
"""
    
    print("\nTest Content:")
    print("-" * 70)
    print(test_content)
    print("-" * 70)
    
    print("\nStarting LinkedIn auto-post...")
    print("Browser will open - make sure you're logged in!")
    print("\nPress Ctrl+C to cancel\n")
    
    try:
        input("Press ENTER to start posting...")
        
        success = post_to_linkedin(test_content)
        
        print("\n" + "=" * 70)
        if success:
            print("✓✓✓ LINKEDIN POST SUCCESSFUL! ✓✓✓")
        else:
            print("✗✗✗ LINKEDIN POST FAILED! ✗✗✗")
        print("=" * 70)
        
        print("\nCheck screenshots in: debug_linkedin/")
        print("Check logs in: Logs/linkedin.log")
        
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")

if __name__ == "__main__":
    main()
