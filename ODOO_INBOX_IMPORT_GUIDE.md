# Odoo Inbox Automation - Sales Lead Import Guide

## Overview (خلاصہ)

This system automatically imports sales leads from JSON files in the `Inbox` folder into Odoo as Customers/Partners.

## How It Works (یہ کیسے کام کرتا ہے)

1. **Create a JSON file** in the `Inbox` folder with sales lead information
2. **Run the importer** using `import_to_odoo.bat`
3. **Customer is created** in Odoo Contacts automatically
4. **File is moved** to `Done` folder after successful import

## JSON File Format

```json
{
  "type": "sales_lead",
  "customer_name": "Customer Name",
  "email": "customer@example.com",
  "phone": "+923001234567",
  "product": "Product/Service Name",
  "amount": 15000,
  "currency": "PKR",
  "notes": "Any additional notes",
  "timestamp": "2026-03-18 12:00:00"
}
```

### Required Fields
- `type`: Must be "sales_lead"
- `customer_name`: Customer's full name
- `email`: Customer's email address (used to find duplicates)
- `phone`: Customer's phone number (used to find duplicates)

### Optional Fields
- `product`: Product or service name
- `amount`: Deal amount
- `currency`: Currency code (default: PKR)
- `notes`: Additional information

## Usage (استعمال)

### Method 1: Manual Import (Recommended)
1. Create JSON file in `Inbox` folder
2. Double-click `import_to_odoo.bat`
3. Wait for confirmation message
4. Check Odoo at http://localhost:8069 → Contacts menu

### Method 2: Automatic Import (Background Service)
Run the automation script that continuously monitors the Inbox folder:
```bash
python watchers\odoo_inbox_automation.py
```

## Files Created

| File | Purpose |
|------|---------|
| `import_to_odoo.bat` | One-click import script |
| `watchers/odoo_inbox_importer.py` | Python importer script |
| `watchers/odoo_inbox_automation.py` | Background automation script |
| `run_odoo_inbox_automation.bat` | Batch file for automation |

## Where to Find Data in Odoo

After importing:

1. **Customers/Partners**: 
   - Go to http://localhost:8069
   - Click on "Contacts" menu
   - Search by customer name, email, or phone

2. **Customer Information**:
   - Name, email, phone
   - Product interest (in Company Info field)
   - Deal amount and notes (in Internal Notes field)

## Troubleshooting

### Customer not showing in Odoo
1. Check if Odoo is running: http://localhost:8069
2. Check the import script output for errors
3. Verify JSON file format is correct
4. Check if file was moved to `Done` folder

### JSON file not processing
1. Ensure file has `.json` extension
2. Check JSON syntax is valid
3. Make sure `type` field is "sales_lead"
4. Run the importer script manually to see error details

### Connection error
1. Verify Odoo is running at http://localhost:8069
2. Check Docker container: `docker ps | findstr odoo`
3. Restart Odoo if needed: `docker-compose restart`

## Example JSON Files

### Example 1: New Customer
```json
{
  "type": "sales_lead",
  "customer_name": "Ali Khan",
  "email": "ali@example.com",
  "phone": "+923001234567",
  "product": "Silver Tier Package",
  "amount": 25000,
  "currency": "PKR",
  "notes": "Interested in monthly subscription"
}
```

### Example 2: Existing Customer (Update)
If a customer with the same email or phone exists, their record will be updated:
```json
{
  "type": "sales_lead",
  "customer_name": "Ali Khan",
  "email": "ali@example.com",
  "phone": "+923001234567",
  "product": "Gold Tier Package",
  "amount": 50000,
  "currency": "PKR",
  "notes": "Upgraded to premium package"
}
```

## Duplicate Handling

The importer prevents duplicate customers:
- **First check**: Email address
- **Second check**: Phone number
- If match found: Updates existing customer
- If no match: Creates new customer

## Notes
- All JSON files must be UTF-8 encoded
- Files are moved to `Done` folder after successful import
- Failed files remain in `Inbox` folder for troubleshooting
- Customer records include all lead information in Internal Notes field

---

**Created**: 2026-03-18
**Version**: 1.0
