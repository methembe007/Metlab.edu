#!/usr/bin/env python
"""
Static file collection script for production deployment.
This script ensures all static files are properly collected and optimized.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e.stderr}")
        sys.exit(1)

def main():
    """Main function to collect and optimize static files."""
    print("Starting static file collection for production...")
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Set production settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings_production')
    
    # Create staticfiles directory if it doesn't exist
    staticfiles_dir = project_root / 'staticfiles'
    staticfiles_dir.mkdir(exist_ok=True)
    
    # Clear existing static files
    if staticfiles_dir.exists() and any(staticfiles_dir.iterdir()):
        print("Clearing existing static files...")
        shutil.rmtree(staticfiles_dir)
        staticfiles_dir.mkdir()
    
    # Collect static files
    run_command(
        'python manage.py collectstatic --noinput --clear',
        'Collecting static files'
    )
    
    # Compress static files if django-compressor is available
    try:
        run_command(
            'python manage.py compress --force',
            'Compressing static files'
        )
    except:
        print("Note: django-compressor not available, skipping compression")
    
    # Set proper permissions for static files
    run_command(
        f'find {staticfiles_dir} -type f -exec chmod 644 {{}} \\;',
        'Setting file permissions for static files'
    )
    
    run_command(
        f'find {staticfiles_dir} -type d -exec chmod 755 {{}} \\;',
        'Setting directory permissions for static files'
    )
    
    # Create media directory structure
    media_root = os.environ.get('MEDIA_ROOT', project_root / 'media')
    media_path = Path(media_root)
    
    # Create media subdirectories
    media_subdirs = ['uploads', 'uploads/content', 'uploads/profiles', 'uploads/temp']
    for subdir in media_subdirs:
        (media_path / subdir).mkdir(parents=True, exist_ok=True)
    
    # Set proper permissions for media directory
    run_command(
        f'find {media_path} -type d -exec chmod 755 {{}} \\;',
        'Setting directory permissions for media files'
    )
    
    # Create log directory structure
    log_dir = Path('/var/log/metlab_edu')
    if not log_dir.exists():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            run_command(
                f'chmod 755 {log_dir}',
                'Setting permissions for log directory'
            )
        except PermissionError:
            print(f"Warning: Could not create log directory {log_dir}. Please create it manually with proper permissions.")
    
    print("\n✓ Static file collection completed successfully!")
    print(f"Static files location: {staticfiles_dir}")
    print(f"Media files location: {media_path}")
    
    # Display summary
    static_count = sum(1 for _ in staticfiles_dir.rglob('*') if _.is_file())
    print(f"Total static files collected: {static_count}")

if __name__ == '__main__':
    main()