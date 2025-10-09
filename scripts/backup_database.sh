#!/bin/bash

# Database backup script for Metlab.edu
# This script creates compressed backups of the PostgreSQL database

set -e

# Configuration
BACKUP_DIR="/backups"
DB_NAME="${DB_NAME:-metlab_edu_prod}"
DB_USER="${DB_USER:-metlab_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/metlab_edu_backup_$TIMESTAMP.sql.gz"

echo "Starting database backup..."
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "User: $DB_USER"
echo "Backup file: $BACKUP_FILE"

# Create database backup
PGPASSWORD="$DB_PASSWORD" pg_dump \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --verbose \
    --clean \
    --no-owner \
    --no-privileges \
    --format=custom \
    | gzip > "$BACKUP_FILE"

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "✓ Database backup completed successfully"
    echo "Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"
else
    echo "✗ Database backup failed"
    exit 1
fi

# Create a plain SQL backup for easier restoration
PLAIN_BACKUP_FILE="$BACKUP_DIR/metlab_edu_backup_$TIMESTAMP.sql"
PGPASSWORD="$DB_PASSWORD" pg_dump \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --verbose \
    --clean \
    --no-owner \
    --no-privileges \
    --format=plain > "$PLAIN_BACKUP_FILE"

gzip "$PLAIN_BACKUP_FILE"

echo "✓ Plain SQL backup created: ${PLAIN_BACKUP_FILE}.gz"

# Clean up old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "metlab_edu_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

# List remaining backups
echo "Current backups:"
ls -lh "$BACKUP_DIR"/metlab_edu_backup_*.sql.gz | tail -10

# Create backup metadata
cat > "$BACKUP_DIR/backup_$TIMESTAMP.info" << EOF
Backup Information
==================
Database: $DB_NAME
Host: $DB_HOST:$DB_PORT
User: $DB_USER
Timestamp: $TIMESTAMP
Date: $(date)
Backup Files:
  - Custom format: metlab_edu_backup_$TIMESTAMP.sql.gz
  - Plain SQL: metlab_edu_backup_$TIMESTAMP.sql.gz
Size: $(du -h "$BACKUP_FILE" | cut -f1)
EOF

echo "✓ Backup process completed successfully"