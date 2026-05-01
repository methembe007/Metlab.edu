# Video Chat System - Quick Fix Guide

## The Problem
The video chat system is not working. This is likely due to one or more of these issues:
1. Redis not running
2. Missing Python packages
3. Corrupted routing file (FIXED)
4. Database migrations not applied

## The Solution - 3 Simple Steps

### Step 1: Run the Diagnostic
```bash
python test_video_chat.py
```

This will tell you exactly what's wrong.

### Step 2: Run the Auto-Fix
```bash
python fix_video_chat.py
```

This will automatically fix most common issues.

### Step 3: Start Redis (if needed)
```bash
# If you have Docker (RECOMMENDED):
docker run -d -p 6379:6379 redis

# Or if you have Redis installed:
redis-server

# Verify it's running:
redis-cli ping
# Should return: PONG
```

### Step 4: Start the Server
```bash
python manage.py runserver
```

### Step 5: Test It
Open your browser to: `http://localhost:8000/video/sessions/`

Try creating a quick session and joining it.

## What I Fixed

1. **Fixed `video_chat/routing.py`** - The file was corrupted/incomplete
2. **Created diagnostic tools** - `test_video_chat.py` to identify issues
3. **Created auto-fix script** - `fix_video_chat.py` to fix common problems
4. **Created troubleshooting guide** - Comprehensive help document

## Most Likely Issue: Redis

The #1 reason video chat doesn't work is **Redis not running**.

Video chat uses WebSockets, which require Redis for message passing between server instances.

**Quick Redis Setup:**
```bash
# Using Docker (easiest):
docker run -d -p 6379:6379 redis

# Test it:
redis-cli ping
```

If you see `PONG`, Redis is working!

## If It Still Doesn't Work

1. **Check the browser console** (F12 → Console tab)
   - Look for WebSocket connection errors
   - Look for JavaScript errors

2. **Check Django terminal output**
   - Look for Python exceptions
   - Look for WebSocket connection attempts

3. **Run the diagnostic again:**
   ```bash
   python test_video_chat.py
   ```

4. **Check specific issues:**
   - Can you access `/video/sessions/`? (Should show a page)
   - Do you see WebSocket errors in console?
   - Is Redis running? (`redis-cli ping`)

## Common Error Messages

### "WebSocket connection failed"
→ Redis is not running. Start Redis.

### "Module 'channels' not found"
→ Run: `pip install channels channels-redis redis`

### "no such table: video_chat_videosession"
→ Run: `python manage.py migrate`

### "Connection refused [Errno 111]"
→ Redis is not running. Start Redis.

### "Permission denied" when joining session
→ Make sure you're logged in and have the right role.

## Testing with Multiple Users

To test video chat with multiple participants:

1. Open the session in one browser window
2. Copy the session URL
3. Open an incognito/private window
4. Log in as a different user
5. Paste the session URL
6. Both users should see each other

## Production Notes

For production deployment, you'll also need:
- HTTPS (WebRTC requires it)
- A TURN server (for NAT traversal)
- Production Redis instance
- ASGI server (Daphne or Uvicorn)

But for development/testing, the steps above should work!

## Need More Help?

Run the diagnostic and share the output:
```bash
python test_video_chat.py > diagnostic_output.txt
```

Then share `diagnostic_output.txt` along with:
- The exact error message you see
- Where you see it (browser console, Django logs, etc.)
- What you were trying to do when it failed
