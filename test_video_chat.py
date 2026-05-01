"""
Quick diagnostic script for video chat system
Run with: python test_video_chat.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
django.setup()

def test_imports():
    """Test if all required packages are installed"""
    print("=" * 60)
    print("Testing Imports...")
    print("=" * 60)
    
    try:
        import channels
        print(f"✓ channels installed (version: {channels.__version__})")
    except ImportError as e:
        print(f"✗ channels NOT installed: {e}")
        return False
    
    try:
        import channels_redis
        print(f"✓ channels_redis installed (version: {channels_redis.__version__})")
    except ImportError as e:
        print(f"✗ channels_redis NOT installed: {e}")
        return False
    
    try:
        import redis
        print(f"✓ redis installed (version: {redis.__version__})")
    except ImportError as e:
        print(f"✗ redis NOT installed: {e}")
        return False
    
    return True


def test_redis_connection():
    """Test Redis connection"""
    print("\n" + "=" * 60)
    print("Testing Redis Connection...")
    print("=" * 60)
    
    try:
        import redis
        from django.conf import settings
        
        # Get Redis configuration from settings
        channel_layers = settings.CHANNEL_LAYERS
        if 'default' in channel_layers:
            config = channel_layers['default'].get('CONFIG', {})
            hosts = config.get('hosts', [('127.0.0.1', 6379)])
            
            if hosts:
                host, port = hosts[0] if isinstance(hosts[0], tuple) else ('127.0.0.1', 6379)
                
                print(f"Connecting to Redis at {host}:{port}...")
                r = redis.Redis(host=host, port=port, decode_responses=True)
                
                # Test connection
                response = r.ping()
                if response:
                    print(f"✓ Redis is running and responding")
                    return True
                else:
                    print(f"✗ Redis ping failed")
                    return False
        else:
            print("✗ No Redis configuration found in settings")
            return False
            
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        print("\nTo fix:")
        print("1. Install Redis: https://redis.io/download")
        print("2. Or use Docker: docker run -d -p 6379:6379 redis")
        return False


def test_video_chat_models():
    """Test if video chat models are accessible"""
    print("\n" + "=" * 60)
    print("Testing Video Chat Models...")
    print("=" * 60)
    
    try:
        from video_chat.models import VideoSession, VideoSessionParticipant
        print("✓ VideoSession model imported")
        print("✓ VideoSessionParticipant model imported")
        
        # Check if tables exist
        count = VideoSession.objects.count()
        print(f"✓ VideoSession table exists ({count} sessions)")
        
        return True
    except Exception as e:
        print(f"✗ Model import/access failed: {e}")
        print("\nTo fix: python manage.py migrate")
        return False


def test_websocket_routing():
    """Test WebSocket routing configuration"""
    print("\n" + "=" * 60)
    print("Testing WebSocket Routing...")
    print("=" * 60)
    
    try:
        from video_chat.routing import websocket_urlpatterns
        print(f"✓ WebSocket routing imported")
        print(f"  Found {len(websocket_urlpatterns)} WebSocket route(s)")
        
        for pattern in websocket_urlpatterns:
            print(f"  - {pattern.pattern}")
        
        return True
    except Exception as e:
        print(f"✗ WebSocket routing failed: {e}")
        return False


def test_asgi_application():
    """Test ASGI application configuration"""
    print("\n" + "=" * 60)
    print("Testing ASGI Application...")
    print("=" * 60)
    
    try:
        from metlab_edu.asgi import application
        print("✓ ASGI application imported")
        
        # Check protocol router
        if hasattr(application, 'application_mapping'):
            protocols = list(application.application_mapping.keys())
            print(f"✓ Configured protocols: {protocols}")
            
            if 'websocket' in protocols:
                print("✓ WebSocket protocol configured")
            else:
                print("✗ WebSocket protocol NOT configured")
                return False
        
        return True
    except Exception as e:
        print(f"✗ ASGI application failed: {e}")
        return False


def test_video_chat_urls():
    """Test if video chat URLs are accessible"""
    print("\n" + "=" * 60)
    print("Testing Video Chat URLs...")
    print("=" * 60)
    
    try:
        from django.urls import reverse
        
        urls_to_test = [
            'video_chat:session_list',
            'video_chat:quick_start_session',
            'video_chat:schedule_session',
        ]
        
        for url_name in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"✓ {url_name}: {url}")
            except Exception as e:
                print(f"✗ {url_name}: {e}")
        
        return True
    except Exception as e:
        print(f"✗ URL testing failed: {e}")
        return False


def main():
    """Run all diagnostic tests"""
    print("\n" + "=" * 60)
    print("VIDEO CHAT SYSTEM DIAGNOSTIC")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Redis Connection", test_redis_connection()))
    results.append(("Models", test_video_chat_models()))
    results.append(("WebSocket Routing", test_websocket_routing()))
    results.append(("ASGI Application", test_asgi_application()))
    results.append(("URLs", test_video_chat_urls()))
    
    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! Video chat system should be working.")
        print("\nNext steps:")
        print("1. Start the server: python manage.py runserver")
        print("2. Go to: http://localhost:8000/video/sessions/")
        print("3. Try creating a quick session")
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("1. Install missing packages: pip install channels channels-redis redis")
        print("2. Start Redis: docker run -d -p 6379:6379 redis")
        print("3. Run migrations: python manage.py migrate")
    
    return passed == total


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nDiagnostic interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
