"""
Enable testing mode for video chat (no Redis required)
This allows you to test the video chat system without installing Redis.

⚠️ WARNING: Only use for testing! Not for production!

Run with: python enable_testing_mode.py
"""

import os
import re

def enable_testing_mode():
    """Switch to in-memory channel layer for testing"""
    
    settings_file = 'metlab_edu/settings.py'
    
    if not os.path.exists(settings_file):
        print("❌ Error: settings.py not found")
        return False
    
    # Read the settings file
    with open(settings_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already in testing mode
    if 'InMemoryChannelLayer' in content:
        print("✓ Already in testing mode")
        return True
    
    # Find and replace CHANNEL_LAYERS configuration
    pattern = r"CHANNEL_LAYERS\s*=\s*\{[^}]*'default'\s*:\s*\{[^}]*\}[^}]*\}"
    
    replacement = """CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# ⚠️ WARNING: Using in-memory channel layer for testing
# This only works with a single server instance
# For production, use Redis:
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             'hosts': [('127.0.0.1', 6379)],
#         },
#     },
# }"""
    
    # Replace the configuration
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content == content:
        print("❌ Error: Could not find CHANNEL_LAYERS configuration")
        return False
    
    # Backup original settings
    backup_file = 'metlab_edu/settings.py.backup'
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Backed up original settings to: {backup_file}")
    
    # Write new settings
    with open(settings_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✓ Enabled testing mode (in-memory channel layer)")
    print("\n⚠️  WARNING: This is for testing only!")
    print("   - Only works with single server instance")
    print("   - Don't use in production")
    print("   - Install Redis for production use")
    
    return True


def disable_testing_mode():
    """Restore original settings"""
    
    backup_file = 'metlab_edu/settings.py.backup'
    settings_file = 'metlab_edu/settings.py'
    
    if not os.path.exists(backup_file):
        print("❌ Error: No backup file found")
        return False
    
    # Restore from backup
    with open(backup_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(settings_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Restored original settings from backup")
    print("✓ Testing mode disabled")
    
    return True


def main():
    print("=" * 60)
    print("VIDEO CHAT TESTING MODE")
    print("=" * 60)
    print()
    print("This will enable testing mode for video chat.")
    print("You can test the video chat without installing Redis.")
    print()
    print("⚠️  WARNING: Only use for testing, not production!")
    print()
    
    choice = input("Enable testing mode? (y/n): ").lower().strip()
    
    if choice == 'y':
        if enable_testing_mode():
            print("\n" + "=" * 60)
            print("TESTING MODE ENABLED")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Run: python manage.py runserver")
            print("2. Go to: http://localhost:8000/video/sessions/")
            print("3. Test the video chat")
            print()
            print("To disable testing mode later:")
            print("  python enable_testing_mode.py --disable")
            print()
            print("For production, install Redis:")
            print("  See: INSTALL_REDIS_WINDOWS.md")
        else:
            print("\n❌ Failed to enable testing mode")
    else:
        print("\nCancelled")


if __name__ == '__main__':
    import sys
    
    if '--disable' in sys.argv:
        disable_testing_mode()
    else:
        main()
