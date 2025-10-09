#!/bin/bash

# Database restoration script for Metlab.edu
# This script restores a PostgreSQL database from backup

set -e

# Configuration
BACKUP_DIR="/backups"
DB_NAME="${DB_NAME:-metlab_edu_prod}"
DB_USER="${DB_USER:-metlab_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# Function to display usage
usage() {
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 metlab_edu_backup_20231201_120000.sql.gz"
    echo ""
    echo "Available backups:"
    ls -1 "$BACKUP_DIR"/metlab_edu_backup_*.sql.gz 2>/dev/null | head -10 || echo "No backups found"
    exit 1
}

# Check if backup file is provided
if [ $# -eq 0 ]; then
    usage
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo "Error: Backup file '$BACKUP_DIR/$BACKUP_FILE' not found"
    usage
fi

echo "WARNING: This will completely replace the current database!"
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "Backup file: $BACKUP_FILE"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restoration cancelled"
    exit 0
fi

echo "Starting database restoration..."

# Check if this is a custom format or plain SQL backup
if [[ "$BACKUP_FILE" == *".sql.gz" ]]; then
    # Plain SQL backup
    echo "Restoring from plain SQL backup..."
    
    # Drop existing connections
    PGPASSWORD="$DB_PASSWORD" psql \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --username="$DB_USER" \
        --dbname="postgres" \
        --command="SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" || true
    
    # Restore database
    gunzip -c "$BACKUP_DIR/$BACKUP_FILE" | PGPASSWORD="$DB_PASSWORD" psql \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --username="$DB_USER" \
        --dbname="$DB_NAME" \
        --verbose
else
    # Custom format backup
    echo "Restoring from custom format backup..."
    
    # Drop existing connections
    PGPASSWORD="$DB_PASSWORD" psql \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --username="$DB_USER" \
        --dbname="postgres" \
        --command="SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" || true
    
    # Restore database
    gunzip -c "$BACKUP_DIR/$BACKUP_FILE" | PGPASSWORD="$DB_PASSWORD" pg_restore \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --username="$DB_USER" \
        --dbname="$DB_NAME" \
        --verbose \
        --clean \
        --no-owner \
        --no-privileges
fi

# Check if restoration was successful
if [ $? -eq 0 ]; then
    echo "✓ Database restoration completed successfully"
    
    # Run Django migrations to ensure schema is up to date
    echo "Running Django migrations..."
    cd /app
    python manage.py migrate --settings=metlab_edu.settings_production
    
    echo "✓ Database restoration and migration completed"
else
    echo "✗ Database restoration failed"
    exit 1
fi

# Display restoration summary
echo ""
echo "Restoration Summary"
echo "==================="
echo "Database: $DB_NAME"
echo "Backup file: $BACKUP_FILE"
echo "Restored at: $(date)"
echo ""
echo "Next steps:"
echo "1. Restart the application services"
echo "2. Verify data integrity"
echo "3. Test critical functionality"