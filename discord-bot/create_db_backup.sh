#!/bin/bash

set -e

if [ -z "$PG_DUMP_URI" ]; then
    echo "❌ PG_DUMP_URI not set in .env"
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d%H%M%S)
BACKUP_DIR="db_backups"
FILENAME="afc_db_backup_${TIMESTAMP}.sql"

mkdir -p "$BACKUP_DIR"

echo "🧹 Cleaning up old backups in $BACKUP_DIR..."
rm -f "$BACKUP_DIR"/*.sql

echo "📤 Creating backup from $PG_DUMP_URI ..."
pg_dump "$PG_DUMP_URI" > "${BACKUP_DIR}/${FILENAME}"

echo "✅ Backup saved to ${BACKUP_DIR}/${FILENAME}"

