#!/usr/bin/env bash
set -e

DB_NAME="revisor"
SETUP_FILE="schema.sql"

chmod +x "$SETUP_FILE"
echo "🌱 Seeding database: $DB_NAME"

psql -d "$DB_NAME" -f "$SETUP_FILE"

echo "Database setup successfully"
