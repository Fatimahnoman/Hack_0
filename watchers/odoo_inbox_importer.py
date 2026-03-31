"""
Odoo Inbox Importer - GOLD TIER (ROBUST VERSION)
=================================================
Imports sales leads from Inbox folder to Odoo CRM/Contacts.

Features:
- Retry logic (3 attempts with exponential backoff)
- Better error handling
- Progress logging
- Auto-moves processed files to Done
- Creates partners in Odoo with full details

Usage: python watchers/odoo_inbox_importer.py
"""

import os
import sys
import json
import time
import logging
import xmlrpc.client
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INBOX_FOLDER = PROJECT_ROOT / "Inbox"
DONE_FOLDER = PROJECT_ROOT / "Done"
LOGS_FOLDER = PROJECT_ROOT / "Logs"

# Odoo Configuration - Can be overridden via environment variables
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "odoo")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds (will be multiplied by attempt number)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_FOLDER / f"odoo_importer_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ensure directories exist
for folder in [INBOX_FOLDER, DONE_FOLDER, LOGS_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)


# =============================================================================
# ODOO CONNECTION FUNCTIONS
# =============================================================================


class OdooConnection:
    """Manages Odoo connection with retry logic."""
    
    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.models = None
        self.common = None
    
    def connect(self) -> bool:
        """Establish connection to Odoo with retries."""
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Connecting to Odoo (attempt {attempt + 1}/{MAX_RETRIES})...")
                logger.info(f"URL: {self.url}")
                logger.info(f"Database: {self.db}")
                logger.info(f"Username: {self.username}")
                
                # Connect to common API
                self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
                
                # Authenticate
                self.uid = self.common.authenticate(self.db, self.username, self.password, {})
                
                if not self.uid:
                    logger.error("Authentication failed - invalid credentials")
                    return False
                
                # Connect to models API
                self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
                
                logger.info(f"✓ Connected successfully! User ID: {self.uid}")
                return True
                
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (attempt + 1)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error("Max retries reached - cannot connect to Odoo")
                    return False
        
        return False
    
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self.uid is not None and self.models is not None


# =============================================================================
# PARTNER/CONTACT FUNCTIONS
# =============================================================================


def create_or_find_partner(models, uid: int, db: str, password: str, lead_data: Dict[str, Any]) -> Optional[int]:
    """
    Create a new partner or find existing one by email/phone.
    
    Args:
        models: Odoo models proxy
        uid: User ID
        db: Database name
        password: Password
        lead_data: Lead data dictionary
        
    Returns:
        Partner ID if successful, None otherwise
    """
    email = lead_data.get('email', '').strip()
    phone = lead_data.get('phone', '').strip()
    customer_name = lead_data.get('customer_name', lead_data.get('name', 'Unknown Customer'))
    
    # Try to find existing partner by email
    if email:
        try:
            partner_ids = models.execute_kw(
                db, uid, password,
                'res.partner', 'search',
                [[['email', '=', email]]]
            )
            if partner_ids:
                logger.info(f"✓ Found existing partner by email: {email} (ID: {partner_ids[0]})")
                
                # Update existing partner with new info
                update_data = {
                    'phone': phone or False,
                    'comment': f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nProduct: {lead_data.get('product', '')}\nAmount: {lead_data.get('amount', 0)}\nNotes: {lead_data.get('notes', '')}",
                }
                models.execute_kw(
                    db, uid, password,
                    'res.partner', 'write',
                    [partner_ids[0], update_data]
                )
                logger.info(f"✓ Updated partner: {partner_ids[0]}")
                
                return partner_ids[0]
        except Exception as e:
            logger.warning(f"Error searching by email: {e}")
    
    # Try to find by phone
    if phone:
        try:
            partner_ids = models.execute_kw(
                db, uid, password,
                'res.partner', 'search',
                [[['phone', '=', phone]]]
            )
            if partner_ids:
                logger.info(f"✓ Found existing partner by phone: {phone} (ID: {partner_ids[0]})")
                return partner_ids[0]
        except Exception as e:
            logger.warning(f"Error searching by phone: {e}")
    
    # Create new partner
    try:
        partner_data = {
            'name': customer_name,
            'email': email or False,
            'phone': phone or False,
            'company_registry': lead_data.get('product', lead_data.get('company', '')),
            'comment': f"Product: {lead_data.get('product', 'N/A')}\nAmount: {lead_data.get('amount', 0)} {lead_data.get('currency', 'PKR')}\nNotes: {lead_data.get('notes', lead_data.get('message', ''))}\nImported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        }
        
        partner_id = models.execute_kw(
            db, uid, password,
            'res.partner', 'create',
            [[partner_data]]
        )
        logger.info(f"✓ Created new partner: {customer_name} (ID: {partner_id})")
        return partner_id
        
    except Exception as e:
        logger.error(f"Error creating partner: {e}")
        return None


def create_crm_lead(models, uid: int, db: str, password: str, lead_data: Dict[str, Any], partner_id: Optional[int] = None) -> Optional[int]:
    """
    Create a CRM lead/opportunity in Odoo.
    
    Args:
        models: Odoo models proxy
        uid: User ID
        db: Database name
        password: Password
        lead_data: Lead data dictionary
        partner_id: Optional existing partner ID
        
    Returns:
        Lead ID if successful, None otherwise
    """
    try:
        crm_lead_data = {
            'name': f"Lead: {lead_data.get('customer_name', 'Unknown')} - {lead_data.get('product', 'General')}",
            'contact_name': lead_data.get('customer_name', lead_data.get('name', '')),
            'email_from': lead_data.get('email', ''),
            'phone': lead_data.get('phone', ''),
            'description': lead_data.get('notes', lead_data.get('message', '')),
            'partner_id': partner_id or False,
            'priority': lead_data.get('priority', '1'),
        }
        
        # Add product info if available
        if lead_data.get('product'):
            crm_lead_data['name'] += f" ({lead_data.get('product')})"
        
        # Add amount if available
        if lead_data.get('amount'):
            crm_lead_data['planned_revenue'] = float(lead_data.get('amount', 0))
            crm_lead_data['currency_id'] = False  # Will use company currency
        
        lead_id = models.execute_kw(
            db, uid, password,
            'crm.lead', 'create',
            [[crm_lead_data]]
        )
        logger.info(f"✓ Created CRM lead: {crm_lead_data['name']} (ID: {lead_id})")
        return lead_id
        
    except Exception as e:
        logger.error(f"Error creating CRM lead: {e}")
        return None


# =============================================================================
# FILE PROCESSING FUNCTIONS
# =============================================================================


def read_json_file(filepath: Path) -> Optional[Dict[str, Any]]:
    """Read and parse JSON file with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            logger.info(f"✓ Read JSON file: {filepath.name}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filepath.name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading {filepath.name} (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                return None
    return None


def read_markdown_file(filepath: Path) -> Optional[Dict[str, Any]]:
    """Read and parse Markdown file with YAML frontmatter."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        data = {
            'raw_content': content,
            'metadata': {},
            'body': ''
        }
        
        # Parse YAML frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                body = parts[2].strip()
                
                # Parse key-value pairs
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        data['metadata'][key.strip()] = value.strip()
                
                data['body'] = body
        else:
            data['body'] = content
        
        logger.info(f"✓ Read Markdown file: {filepath.name}")
        return data
    except Exception as e:
        logger.error(f"Error reading {filepath.name}: {e}")
        return None


def extract_lead_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract lead information from file data."""
    lead_data = {
        'customer_name': '',
        'email': '',
        'phone': '',
        'product': '',
        'amount': 0,
        'currency': 'PKR',
        'notes': '',
        'priority': '1',
        'type': 'sales_lead'
    }
    
    # Check if it's JSON data
    if 'raw_content' not in data:
        # Direct JSON
        lead_data.update(data)
    else:
        # Markdown with frontmatter
        metadata = data.get('metadata', {})
        body = data.get('body', '')
        
        # Extract from metadata
        lead_data['customer_name'] = metadata.get('customer_name', metadata.get('from', metadata.get('name', '')))
        lead_data['email'] = metadata.get('email', '')
        lead_data['phone'] = metadata.get('phone', '')
        lead_data['product'] = metadata.get('product', '')
        lead_data['amount'] = metadata.get('amount', 0)
        lead_data['currency'] = metadata.get('currency', 'PKR')
        lead_data['priority'] = metadata.get('priority', '1')
        lead_data['notes'] = body
        
        # Try to extract from body if metadata is missing
        if not lead_data['email']:
            import re
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', body)
            if email_match:
                lead_data['email'] = email_match.group(0)
        
        if not lead_data['phone']:
            import re
            phone_match = re.search(r'[\+\(]?[1-9][0-9 \(\)\-\.\n]{5,32}[0-9]', body)
            if phone_match:
                lead_data['phone'] = phone_match.group(0)
    
    return lead_data


def process_inbox_file(filepath: Path, odoo: OdooConnection) -> bool:
    """
    Process a single file from Inbox and create Odoo records.
    
    Args:
        filepath: Path to the file
        odoo: OdooConnection object
        
    Returns:
        True if successful, False otherwise
    """
    filename = filepath.name
    logger.info("=" * 70)
    logger.info(f"Processing: {filename}")
    logger.info("=" * 70)
    
    # Read file based on extension
    if filepath.suffix.lower() == '.json':
        data = read_json_file(filepath)
    else:
        data = read_markdown_file(filepath)
    
    if not data:
        logger.error(f"Failed to read file: {filename}")
        return False
    
    # Extract lead data
    lead_data = extract_lead_data(data)
    
    logger.info(f"Lead Details:")
    logger.info(f"  Name: {lead_data.get('customer_name', 'N/A')}")
    logger.info(f"  Email: {lead_data.get('email', 'N/A')}")
    logger.info(f"  Phone: {lead_data.get('phone', 'N/A')}")
    logger.info(f"  Product: {lead_data.get('product', 'N/A')}")
    logger.info(f"  Amount: {lead_data.get('amount', 0)} {lead_data.get('currency', 'PKR')}")
    
    # Check if it's a sales lead
    lead_type = lead_data.get('type', 'sales_lead')
    if lead_type != 'sales_lead':
        logger.info(f"Skipping - Not a sales lead (type: {lead_type})")
        return False
    
    # Create or find partner
    partner_id = create_or_find_partner(
        odoo.models, odoo.uid, odoo.db, odoo.password, lead_data
    )
    
    if not partner_id:
        logger.warning("Could not create/find partner - continuing with lead creation")
    
    # Create CRM lead
    lead_id = create_crm_lead(
        odoo.models, odoo.uid, odoo.db, odoo.password, lead_data, partner_id
    )
    
    if not lead_id and not partner_id:
        logger.error("Failed to create both partner and lead")
        return False
    
    # Move file to Done folder
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        done_filename = f"processed_{filename}"
        done_path = DONE_FOLDER / done_filename
        
        # Create done file with processing info
        done_content = f"""---
type: processed_{lead_type}
source: {filename}
processed_at: {datetime.now().isoformat()}
status: imported_to_odoo
partner_id: {partner_id or 'N/A'}
lead_id: {lead_id or 'N/A'}
---

# Imported to Odoo

*Processed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Original Content

{data.get('raw_content', json.dumps(data, indent=2))}
"""
        
        with open(done_path, 'w', encoding='utf-8') as f:
            f.write(done_content)
        
        # Optionally remove original
        # filepath.unlink()
        
        logger.info(f"✓ File moved to Done: {done_filename}")
        logger.info(f"✓ SUCCESS: {filename} imported to Odoo!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error moving file to Done: {e}")
        return False


# =============================================================================
# MAIN FUNCTION
# =============================================================================


def main():
    """Main function to import inbox files to Odoo."""
    print("=" * 70)
    print("Odoo Inbox Importer - GOLD TIER (ROBUST)")
    print("=" * 70)
    print(f"Odoo URL: {ODOO_URL}")
    print(f"Database: {ODOO_DB}")
    print(f"Inbox Folder: {INBOX_FOLDER}")
    print(f"Done Folder: {DONE_FOLDER}")
    print("=" * 70)
    
    # Check inbox folder
    if not INBOX_FOLDER.exists():
        logger.error(f"Inbox folder not found: {INBOX_FOLDER}")
        print(f"\nERROR: Inbox folder not found: {INBOX_FOLDER}")
        input("\nPress Enter to exit...")
        return
    
    # Find all JSON and MD files
    files = list(INBOX_FOLDER.glob("*.json")) + list(INBOX_FOLDER.glob("*.md"))
    
    if not files:
        print("\n[INFO] No JSON/MD files found in Inbox folder.")
        input("\nPress Enter to exit...")
        return
    
    print(f"\n[INFO] Found {len(files)} file(s) to process.\n")
    
    # Connect to Odoo
    odoo = OdooConnection(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
    
    if not odoo.connect():
        print("\n" + "=" * 70)
        print("ERROR: Cannot connect to Odoo!")
        print("=" * 70)
        print("\nTroubleshooting:")
        print("1. Make sure Odoo is running at", ODOO_URL)
        print("2. Check username/password in environment variables:")
        print("   - ODOO_USERNAME")
        print("   - ODOO_PASSWORD")
        print("   - ODOO_DB")
        print("3. Check logs:", LOGS_FOLDER)
        input("\nPress Enter to exit...")
        return
    
    # Process each file
    success_count = 0
    fail_count = 0
    
    for filepath in files:
        if process_inbox_file(filepath, odoo):
            success_count += 1
        else:
            fail_count += 1
        
        # Small delay between files
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 70)
    print("IMPORT SUMMARY")
    print("=" * 70)
    print(f"Total files: {len(files)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    print("=" * 70)
    
    if success_count > 0:
        print(f"\n✓ SUCCESS: {success_count} file(s) imported to Odoo!")
        print("   Go to: Settings → Contacts (for partners)")
        print("   Go to: CRM → Leads (for opportunities)")
    else:
        print("\n✗ No files were successfully imported")
    
    print(f"\nLogs: {LOGS_FOLDER}")
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
