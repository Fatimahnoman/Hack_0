"""
WhatsApp Chat Structure Debug - Inspect actual row content
"""

import os
import time
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_PATH = os.path.join(PROJECT_ROOT, "session", "whatsapp")

def debug_chat_structure():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_PATH,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0]
        page.goto("https://web.whatsapp.com")
        
        print("=" * 60)
        print("CHAT STRUCTURE DEBUG")
        print("Wait for WhatsApp to load, then check for UNREAD messages")
        print("=" * 60)
        
        input("\nPress Enter after WhatsApp has loaded...")
        
        # Get all chat rows
        rows = page.query_selector_all('#pane-side [role="row"]')
        print(f"\nFound {len(rows)} chat rows")
        
        for i, row in enumerate(rows[:10]):  # First 10 rows
            try:
                # Get all gridcells in this row
                gridcells = row.query_selector_all('[role="gridcell"]')
                print(f"\n--- Row {i+1} ---")
                print(f"Gridcells: {len(gridcells)}")
                
                # Get class names
                row_class = row.get_attribute('class')
                print(f"Row class: {row_class[:100] if row_class else 'None'}")
                
                for j, cell in enumerate(gridcells):
                    try:
                        cell_text = cell.inner_text()
                        cell_class = cell.get_attribute('class')
                        cell_html = cell.evaluate('el => el.innerHTML')[:150]
                        print(f"  Cell {j}: '{cell_text}' | class: {cell_class[:50] if cell_class else 'None'}")
                        print(f"    HTML: {cell_html}...")
                    except Exception as e:
                        print(f"  Cell {j}: Error - {e}")
                
                # Get contact name
                name_elem = row.query_selector('span[dir="auto"], span[title]')
                if name_elem:
                    print(f"Contact: {name_elem.inner_text() or name_elem.get_attribute('title')}")
                
                # Check for any unread-like elements
                all_spans = row.query_selector_all('span, div')
                for span in all_spans:
                    try:
                        span_class = span.get_attribute('class') or ''
                        if any(x in span_class.lower() for x in ['badge', 'unread', 'dot', 'icon', '_']):
                            span_text = span.inner_text()
                            print(f"  Potential unread element: class='{span_class[:50]}', text='{span_text}'")
                    except:
                        pass
                        
            except Exception as e:
                print(f"Row {i+1}: Error - {e}")
        
        print("\n" + "=" * 60)
        print("Keeping browser open for manual inspection...")
        print("Press Ctrl+C to exit")
        
        while True:
            time.sleep(10)

if __name__ == "__main__":
    debug_chat_structure()
