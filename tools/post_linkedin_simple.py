"""
Auto LinkedIn Poster - Interactive Mode
========================================
Simple interactive script to post LinkedIn drafts.
No command-line arguments needed.

Run:
    python tools\\post_linkedin_simple.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.auto_linkedin_poster import (
    scan_and_draft_posts,
    check_pending_approvals,
    post_to_linkedin,
    ensure_directories
)

def print_header():
    """Print header."""
    print("=" * 60)
    print("Auto LinkedIn Poster - Interactive Mode")
    print("=" * 60)
    print()

def print_menu():
    """Print menu options."""
    print("Select an option:")
    print()
    print("  1. Scan Needs_Action for sales leads (create drafts)")
    print("  2. Check pending approvals")
    print("  3. Post to LinkedIn")
    print("  4. Exit")
    print()

def get_file_choice():
    """Let user select a file from Pending_Approval."""
    ensure_directories()
    
    pending_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Pending_Approval")
    
    if not os.path.exists(pending_folder):
        print("[ERROR] Pending_Approval folder not found!")
        return None
    
    files = [f for f in os.listdir(pending_folder) 
             if f.startswith('linkedin_post_') and f.endswith('.md')]
    
    if not files:
        print("[INFO] No pending drafts found.")
        return None
    
    print()
    print("Available drafts:")
    print("-" * 60)
    
    for i, filename in enumerate(sorted(files), 1):
        filepath = os.path.join(pending_folder, filename)
        print(f"  {i}. {filename}")
    
    print()
    
    while True:
        try:
            choice = input(f"Enter file number (1-{len(files)}) or 'q' to cancel: ").strip()
            
            if choice.lower() == 'q':
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(files):
                selected_file = sorted(files)[choice_num - 1]
                return selected_file
            else:
                print(f"Please enter a number between 1 and {len(files)}")
        except ValueError:
            print("Please enter a valid number or 'q'")

def main():
    """Main interactive loop."""
    print_header()
    
    while True:
        print_menu()
        
        try:
            choice = input("Your choice: ").strip()
            
            if choice == '1':
                print()
                print("-" * 60)
                print("Scanning for sales leads...")
                print("-" * 60)
                drafts = scan_and_draft_posts()
                print()
                print(f"[RESULT] Created {len(drafts)} draft(s)")
                
            elif choice == '2':
                print()
                print("-" * 60)
                print("Checking pending approvals...")
                print("-" * 60)
                pending = check_pending_approvals()
                print()
                print(f"[RESULT] {len(pending)} pending approval(s)")
                
            elif choice == '3':
                print()
                print("-" * 60)
                print("Post to LinkedIn")
                print("-" * 60)
                print()
                print("IMPORTANT: First close ALL Chrome/Edge browsers!")
                print("Press Enter when ready to continue...")
                input()
                
                selected_file = get_file_choice()
                
                if selected_file:
                    print()
                    print(f"Posting: {selected_file}")
                    print("-" * 60)
                    result = post_to_linkedin(selected_file)
                    
                    if result['success']:
                        print()
                        print("[SUCCESS] Post published to LinkedIn!")
                    else:
                        print()
                        print(f"[FAILED] {result['error']}")
                        print()
                        print("TIP: Make sure you are logged in to LinkedIn")
                        print("     The browser will open for you to login if needed.")
                else:
                    print("[CANCELLED] No file selected")
                
            elif choice == '4':
                print()
                print("Exiting...")
                print("Goodbye!")
                break
                
            else:
                print("Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print()
            print()
            print("Interrupted by user.")
            print("Exiting...")
            break
        except Exception as e:
            print()
            print(f"[ERROR] {e}")
            print("Please try again.")
        
        print()
        print("-" * 60)
        input("Press Enter to continue...")
        print()

if __name__ == "__main__":
    main()
