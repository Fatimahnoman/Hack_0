"""
Odoo Inbox Automation - Sales Lead Importer
============================================
This script monitors the Inbox folder for JSON files containing sales leads
and automatically imports them into Odoo CRM.

Usage: python watchers/odoo_inbox_automation.py
"""

import os
import json
import time
import xmlrpc.client
from datetime import datetime
from pathlib import Path

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX_FOLDER = os.path.join(PROJECT_ROOT, "Inbox")
DONE_FOLDER = os.path.join(PROJECT_ROOT, "Done")

# Odoo Configuration
ODOO_URL = "http://localhost:8069"
ODOO_DB = "odoo"
ODOO_USERNAME = "admin"
ODOO_PASSWORD = "admin"

CHECK_INTERVAL = 10  # seconds


def authenticate_odoo():
    """Authenticate with Odoo and return common and object models."""
    try:
        # Common authentication
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if not uid:
            raise Exception("Authentication failed. Check username/password.")
        
        # Object model for CRUD operations
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        print(f"[INFO] Connected to Odoo as user ID: {uid}")
        return uid, common, models
    except Exception as e:
        print(f"[ERROR] Odoo connection failed: {e}")
        raise


def create_or_find_partner(models, uid, lead_data):
    """Create a new partner or find existing one by email."""
    email = lead_data.get('email', '')
    phone = lead_data.get('phone', '')
    
    # Try to find existing partner by email
    if email:
        partner_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner', 'search',
            [[['email', '=', email]]]
        )
        if partner_ids:
            print(f"[INFO] Found existing partner: {email} (ID: {partner_ids[0]})")
            return partner_ids[0]
    
    # Try to find by phone
    if phone:
        partner_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner', 'search',
            [[['phone', '=', phone]]]
        )
        if partner_ids:
            print(f"[INFO] Found existing partner by phone: {phone} (ID: {partner_ids[0]})")
            return partner_ids[0]
    
    # Create new partner
    partner_data = {
        'name': lead_data.get('customer_name', 'Unknown Customer'),
        'email': email or False,
        'phone': phone or False,
        'company_registry': lead_data.get('product', ''),
    }
    
    partner_id = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'res.partner', 'create',
        [partner_data]
    )
    print(f"[INFO] Created new partner: {partner_data['name']} (ID: {partner_id})")
    return partner_id


def create_sales_lead(models, uid, lead_data, partner_id):
    """Create a CRM lead/opportunity in Odoo."""
    # Map product to stage (you can customize this)
    product = lead_data.get('product', '')
    amount = lead_data.get('amount', 0)
    
    # Update the partner with lead information
    models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'res.partner', 'write',
        [partner_id, {
            'comment': f"Lead Info:\nProduct: {product}\nAmount: {amount} {lead_data.get('currency', 'PKR')}\nNotes: {lead_data.get('notes', '')}",
            'company_registry': product,
        }]
    )
    
    print(f"[INFO] Created/Updated Customer in Odoo (ID: {partner_id})")
    print(f"       -> Customer: {lead_data.get('customer_name', 'Unknown')}")
    print(f"       -> Email: {lead_data.get('email', 'N/A')}")
    print(f"       -> Phone: {lead_data.get('phone', 'N/A')}")
    print(f"       -> Product: {product}")
    print(f"       -> Amount: {amount} {lead_data.get('currency', 'PKR')}")
    print(f"       -> Notes: {lead_data.get('notes', 'N/A')}")
    
    # Try to create CRM lead if CRM module is available
    try:
        # Get stage ID (default to 1)
        stage_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'crm.stage', 'search',
            [[['name', '=', 'New']]]
        )
        stage_id = stage_ids[0] if stage_ids else 1
        
        # Create lead
        lead_values = {
            'name': f"{product} - {lead_data.get('customer_name', 'Unknown')}",
            'partner_id': partner_id,
            'contact_name': lead_data.get('customer_name', ''),
            'email_from': lead_data.get('email', ''),
            'phone': lead_data.get('phone', ''),
            'description': f"Product: {product}\n\nNotes: {lead_data.get('notes', '')}",
            'planned_revenue': amount,
            'probability': 10,
            'priority': '1',
            'stage_id': stage_id,
        }
        
        lead_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'crm.lead', 'create',
            [lead_values]
        )
        
        print(f"[INFO] Also created CRM Lead (ID: {lead_id})")
        return lead_id
        
    except Exception as e:
        print(f"[INFO] CRM Lead not created (CRM module may not be installed): {e}")
        return None


def process_inbox_file(filepath: str, models, uid) -> tuple:
    """Process a JSON file from Inbox and create Odoo records."""
    filename = os.path.basename(filepath)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lead_data = json.load(f)
        
        print(f"\n[INFO] Processing: {filename}")
        print(f"       Type: {lead_data.get('type', 'unknown')}")
        
        # Check if it's a sales lead
        if lead_data.get('type') != 'sales_lead':
            print(f"[SKIP] Not a sales lead, skipping.")
            return filename, False
        
        # Create or find partner
        partner_id = create_or_find_partner(models, uid, lead_data)
        
        # Create sales lead
        lead_id = create_sales_lead(models, uid, lead_data, partner_id)
        
        # Move file to Done folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        done_filename = f"processed_{filename}"
        done_path = os.path.join(DONE_FOLDER, done_filename)
        
        # Create Done folder if it doesn't exist
        if not os.path.exists(DONE_FOLDER):
            os.makedirs(DONE_FOLDER)
        
        # Move the file
        os.rename(filepath, done_path)
        
        print(f"[SUCCESS] File moved to Done folder")
        return filename, True
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in {filename}: {e}")
        return filename, False
    except Exception as e:
        print(f"[ERROR] Processing {filename}: {e}")
        import traceback
        traceback.print_exc()
        return filename, False


def ensure_directories():
    """Ensure required directories exist."""
    for folder in [INBOX_FOLDER, DONE_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"[INFO] Created directory: {folder}")


def main():
    """Main function to start Odoo Inbox Automation."""
    print("=" * 60)
    print("Odoo Inbox Automation - Sales Lead Importer")
    print("=" * 60)
    print(f"Monitoring: {INBOX_FOLDER}")
    print(f"Odoo URL: {ODOO_URL}")
    print(f"Database: {ODOO_DB}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print("-" * 60)
    print("HOW TO USE:")
    print("1. Create a JSON file in /Inbox with sales lead data")
    print("2. This script will import it to Odoo CRM automatically")
    print("3. Processed files are moved to /Done folder")
    print("4. Press Ctrl+C to stop")
    print("=" * 60)

    ensure_directories()
    
    # Authenticate with Odoo
    print(f"\n[INFO] Connecting to Odoo at {ODOO_URL}...")
    try:
        uid, common, models = authenticate_odoo()
    except Exception as e:
        print(f"[ERROR] Cannot connect to Odoo: {e}")
        print("Make sure Odoo is running at http://localhost:8069")
        return

    processed_files = set()

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Automation started!")

    try:
        while True:
            # Check inbox folder
            if os.path.exists(INBOX_FOLDER):
                files = [f for f in os.listdir(INBOX_FOLDER)
                        if f.endswith('.json') and f not in processed_files]

                for filename in files:
                    filepath = os.path.join(INBOX_FOLDER, filename)

                    try:
                        processed_name, success = process_inbox_file(filepath, models, uid)
                        if success:
                            processed_files.add(filename)
                    except Exception as e:
                        print(f"[ERROR] Processing {filename}: {e}")

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n[INFO] Automation stopped by user.")

    print("[INFO] Automation stopped.")


if __name__ == "__main__":
    main()
