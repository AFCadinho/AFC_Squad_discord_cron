#!/bin/bash

set -e


# Load variables from .env
set -a
source .env
set +a

# --- Config ---
BACKUP_DIR="db_backups"
TARGET_URI="$PG_DUMP_URI"

# --- Check for URI argument ---
if [ -z "$TARGET_URI" ]; then
    echo "Usage: $0 \"postgresql://user:password@host:port/database\""
    exit 1
fi

# --- Find the .sql file ---
DUMP_FILE=$(find "$BACKUP_DIR" -maxdepth 1 -type f -name "*.sql" | head -n 1)

echo "📄 Found backup file: $DUMP_FILE"

# --- Clean up owner references ---
echo "🧹 Cleaning dump file..."
sed -i '/OWNER TO/d' "$DUMP_FILE"
sed -i '/^-- Name: .*; Owner: /d' "$DUMP_FILE"

psql "$TARGET_URI" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# --- Import the dump ---
echo "📥 Importing into target database..."
psql "$TARGET_URI" -f "$DUMP_FILE"

echo "✅ Import completed successfully."
