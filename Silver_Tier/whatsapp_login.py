"""
WhatsApp Quick Login Script
Run this once to log in via QR code. Session will be saved.
"""

import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

SESSION_PATH = os.path.join(os.path.dirname(__file__), 'sessions', 'whatsapp_session')

def login():
    """Log in to WhatsApp Web and save session."""
    print("=" * 50)
    print("WhatsApp Login - Silver Tier")
    print("=" * 50)
    
    os.makedirs(SESSION_PATH, exist_ok=True)
    
    options = Options()
    options.add_argument("--user-data-dir=" + SESSION_PATH)
    options.add_argument("--profile-directory=Default")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--remote-debugging-port=9223")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://web.whatsapp.com")
    
    print("\n[INFO] Scan the QR code with your phone:")
    print("  1. Open WhatsApp on phone")
    print("  2. Settings → Linked Devices → Link a Device")
    print("  3. Scan the QR code on screen")
    print("\nWaiting 120 seconds for login...")
    
    try:
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='main']"))
        )
        print("\n✓ Login successful! Session saved to:")
        print(f"  {SESSION_PATH}")
        print("\nKeep browser open or close it - session is saved.")
        input("\nPress Enter to exit...")
    except Exception as e:
        print(f"\n[WARN] Login timeout: {e}")
        print("Session may still have been partially saved. Try again.")
    finally:
        driver.quit()

if __name__ == '__main__':
    login()
