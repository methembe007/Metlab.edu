# Video Chat System Diagnostic and Fix Guide

## Issues Identified

### 1. **Corrupted Routing File**
The `video_chat/routing.py` file appears to be incomplete or corrupted. The WebSocket URL pattern is cut off mid-line.

### 2. **Potential WebSocket Connection Issues**
The JavaScript is trying to connect to `/ws/video/{sessionId}/` but the routing might not match.

### 3. **Missing Error Handling**
Need to verify all components are properly connected.

## Quick Diagnostic Steps

Run these commands to diagnose the issues:

```bash
# 1. Check if Redis is running (required for Channels)
redis-cli ping

# 2. Check if channels is installed
python -c "import channels; print(channels.__version__)"

# 3. Check if channels_redis is installed
python -c "import channels_redis; print(channels_redis.__version__)"

# 4. Test WebSocket routing
python manage.py shell
>>> from video_chat.routing import websocket_urlpatterns
>>> print(websocket_urlpatterns)

# 5. Check for any import errors
python manage.py check

# 6. Test ASGI application
python manage.py runserver --noreload
```

## Common Issues and Fixes

### Issue 1: Redis Not Running
**Symptoms:** WebSocket connections fail immediately
**Fix:**
```bash
# Windows (if using WSL or Docker)
docker run -d -p 6379:6379 redis

# Or install Redis for Windows
# Download from: https://github.com/microsoftarchive/redis/releases
```

### Issue 2: Channels Not Installed
**Symptoms:** Import errors, ASGI application fails
**Fix:**
```bash
pip install channels channels-redis
```

### Issue 3: WebSocket URL Mismatch
**Symptoms:** 404 errors on WebSocket connection
**Current JavaScript:** `/ws/video/{sessionId}/`
**Current Routing:** `/ws/video-session/{sessionId}/`

**These don't match!**

### Issue 4: CORS/Security Settings
**Symptoms:** WebSocket connections blocked by browser
**Check:** `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in settings.py

## Immediate Fixes Needed

### Fix 1: Repair routing.py
The file needs to be fixed - it's currently broken.

### Fix 2: Match WebSocket URLs
Either update JavaScript or routing to use the same path.

### Fix 3: Verify Channel Layer Configuration
Check that Redis connection string is correct in settings.py.

### Fix 4: Check Installed Apps
Ensure 'channels' is in INSTALLED_APPS before 'django.contrib.staticfiles'.

## Testing the Video Chat

After fixes, test with:

1. **Create a test session:**
   - Go to `/video/quick-start/`
   - Create a session
   - Try to join

2. **Check browser console:**
   - Open Developer Tools (F12)
   - Look for WebSocket connection errors
   - Check for JavaScript errors

3. **Check Django logs:**
   - Look for WebSocket connection attempts
   - Check for any Python errors

## What to Check Right Now

1. **Is Redis running?**
   ```bash
   redis-cli ping
   ```
   Should return: `PONG`

2. **Can you access video chat URLs?**
   - Try: `http://localhost:8000/video/sessions/`
   - Should show session list page

3. **Check browser console when joining:**
   - Look for WebSocket connection errors
   - Note the exact error message

## Next Steps

Please provide:
1. The exact error message you're seeing
2. Where the error occurs (browser console, Django logs, etc.)
3. Output of `redis-cli ping`
4. Whether you can access `/video/sessions/` page

This will help me provide a more specific fix.
