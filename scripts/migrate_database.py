#!/usr/bin/env python
"""
Database migration script for production deployment.
This script handles Django migrations safely in production.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, description, check=True):
    """Run a command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description} completed successfully")
            return result.stdout
        else:
            print(f"⚠ {description} completed with warnings: {result.stderr}")
            return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e.stderr}")
        if check:
            sys.exit(1)
        return None

def check_database_connection():
    """Check if database is accessible."""
    print("Checking database connection...")
    result = run_command(
        'python manage.py dbshell --command="SELECT 1;" 2>/dev/null',
        'Testing database connection',
        check=False
    )
    return result is not None

def backup_before_migration():
    """Create a backup before running migrations."""
    print("Creating pre-migration backup...")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_file = f"pre_migration_backup_{timestamp}.sql.gz"
    
    # Use the backup script if available
    backup_script = Path(__file__).parent / 'backup_database.sh'
    if backup_script.exists():
        run_command(
            f'bash {backup_script}',
            'Creating database backup'
        )
    else:
        print("⚠ Backup script not found, skipping backup")

def main():
    """Main function to handle database migrations."""
    print("Starting database migration process...")
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Set production settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings_production')
    
    # Check database connection
    if not check_database_connection():
        print("✗ Cannot connect to database. Please check your database configuration.")
        sys.exit(1)
    
    # Create backup before migration (optional but recommended)
    backup_choice = input("Create backup before migration? (y/N): ").lower()
    if backup_choice in ['y', 'yes']:
        backup_before_migration()
    
    # Check for pending migrations
    print("Checking for pending migrations...")
    result = run_command(
        'python manage.py showmigrations --plan',
        'Checking migration status'
    )
    
    if '[ ]' not in result:
        print("✓ No pending migrations found")
        return
    
    print("Pending migrations found:")
    print(result)
    
    # Confirm migration
    confirm = input("Proceed with migrations? (y/N): ").lower()
    if confirm not in ['y', 'yes']:
        print("Migration cancelled")
        return
    
    # Run migrations
    run_command(
        'python manage.py migrate --verbosity=2',
        'Running database migrations'
    )
    
    # Collect static files after migration
    run_command(
        'python manage.py collectstatic --noinput --clear',
        'Collecting static files'
    )
    
    # Create superuser if none exists (interactive)
    print("Checking for superuser accounts...")
    result = run_command(
        'python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).exists())"',
        'Checking for superuser',
        check=False
    )
    
    if result and 'False' in result:
        create_superuser = input("No superuser found. Create one now? (y/N): ").lower()
        if create_superuser in ['y', 'yes']:
            run_command(
                'python manage.py createsuperuser',
                'Creating superuser account'
            )
    
    # Initialize data if needed
    print("Initializing application data...")
    
    # Run initialization commands
    init_commands = [
        ('python manage.py initialize_gamification', 'Initializing gamification data'),
        ('python manage.py initialize_privacy_policies', 'Initializing privacy policies'),
        ('python manage.py initialize_tutoring', 'Initializing tutoring data'),
    ]
    
    for command, description in init_commands:
        run_command(command, description, check=False)
    
    # Update search indexes if using full-text search
    run_command(
        'python manage.py update_index',
        'Updating search indexes',
        check=False
    )
    
    print("\n✓ Database migration process completed successfully!")
    print("\nNext steps:")
    print("1. Restart application services")
    print("2. Test critical functionality")
    print("3. Monitor application logs")
    print("4. Verify data integrity")

if __name__ == '__main__':
    main()