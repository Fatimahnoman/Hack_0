#!/bin/bash
set -e

echo "Waiting for database to be ready..."
until pg_isready -h db -p 5432 -U odoo; do
  sleep 1
done

echo "Database is ready!"

# Check if database is empty (no ir_module_module table)
if ! docker exec heckathon0-db-1 psql -U odoo -d odoo -c "SELECT 1 FROM ir_module_module LIMIT 1;" 2>/dev/null; then
  echo "Database is empty. Initializing Odoo..."
  # Initialize the database by running odoo with --init base
  exec odoo --init base --without-demo=all
else
  echo "Database already initialized. Starting Odoo..."
  exec odoo
fi
