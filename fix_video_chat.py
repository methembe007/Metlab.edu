"""
Quick fix script for common video chat issues
Run with: python fix_video_chat.py
"""

import os
import sys
import subprocess

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description} completed")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"✗ {description} failed")
            if result.stderr:
                print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    print("=" * 60)
    print("VIDEO CHAT SYSTEM AUTO-FIX")
    print("=" * 60)
    
    fixes = []
    
    # Fix 1: Install required packages
    print("\n[1/5] Installing required packages...")
    result = run_command(
        "pip install channels channels-redis redis",
        "Package installation"
    )
    fixes.append(("Install packages", result))
    
    # Fix 2: Run migrations
    print("\n[2/5] Running database migrations...")
    result = run_command(
        "python manage.py migrate",
        "Database migrations"
    )
    fixes.append(("Run migrations", result))
    
    # Fix 3: Collect static files
    print("\n[3/5] Collecting static files...")
    result = run_command(
        "python manage.py collectstatic --noinput",
        "Static files collection"
    )
    fixes.append(("Collect static", result))
    
    # Fix 4: Check Django configuration
    print("\n[4/5] Checking Django configuration...")
    result = run_command(
        "python manage.py check",
        "Django configuration check"
    )
    fixes.append(("Django check", result))
    
    # Fix 5: Test Redis connection
    print("\n[5/5] Testing Redis connection...")
    result = run_command(
        "redis-cli ping",
        "Redis connection test"
    )
    fixes.append(("Redis test", result))
    
    # Summary
    print("\n" + "=" * 60)
    print("FIX SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in fixes if result)
    total = len(fixes)
    
    for fix_name, result in fixes:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {fix_name}")
    
    print(f"\nCompleted: {passed}/{total}")
    
    if not fixes[-1][1]:  # Redis test failed
        print("\n⚠ Redis is not running!")
        print("\nTo start Redis:")
        print("  Option 1 (Docker): docker run -d -p 6379:6379 redis")
        print("  Option 2 (Windows): Download from https://github.com/microsoftarchive/redis/releases")
        print("  Option 3 (WSL): sudo service redis-server start")
    
    if passed >= total - 1:  # All except maybe Redis
        print("\n✓ Most fixes applied successfully!")
        print("\nNext steps:")
        print("1. Make sure Redis is running")
        print("2. Run: python test_video_chat.py")
        print("3. Start server: python manage.py runserver")
        print("4. Test at: http://localhost:8000/video/sessions/")
    else:
        print("\n✗ Some fixes failed. Please review errors above.")
    
    return passed >= total - 1


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nFix interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
