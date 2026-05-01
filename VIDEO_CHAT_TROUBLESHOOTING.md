# Video Chat System Troubleshooting Guide

## Quick Start - Run These Commands

```bash
# 1. Run the diagnostic script
python test_video_chat.py

# 2. If issues found, run the fix script
python fix_video_chat.py

# 3. Start Redis (if not running)
docker run -d -p 6379:6379 redis

# 4. Start the Django server
python manage.py runserver

# 5. Test the video chat
# Open browser to: http://localhost:8000/video/sessions/
```

## Common Issues and Solutions

### Issue 1: "WebSocket connection failed"

**Symptoms:**
- Browser console shows WebSocket connection errors
- Can't join video sessions
- Error: "WebSocket connection to 'ws://...' failed"

**Causes:**
1. Redis not running
2. Channels not installed
3. ASGI application not configured
4. WebSocket URL mismatch

**Solutions:**

```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not running, start Redis:
docker run -d -p 6379:6379 redis

# Install required packages
pip install channels channels-redis redis

# Run migrations
python manage.py migrate

# Restart server
python manage.py runserver
```

### Issue 2: "Session not found" or 404 errors

**Symptoms:**
- Can't access `/video/sessions/`
- 404 errors on video chat pages

**Solutions:**

```bash
# Check if video_chat URLs are included
python manage.py show_urls | grep video

# Run migrations
python manage.py migrate video_chat

# Check if app is in INSTALLED_APPS
python manage.py check
```

### Issue 3: "Permission denied" or authentication errors

**Symptoms:**
- Can't create sessions
- Can't join sessions
- "You do not have permission" errors

**Solutions:**

1. Make sure you're logged in
2. Check user role (student, teacher, parent)
3. Verify session permissions in `video_chat/permissions.py`

### Issue 4: Video/audio not working

**Symptoms:**
- Can join session but no video/audio
- Camera/microphone permissions denied
- Black screen or no video feed

**Solutions:**

1. **Check browser permissions:**
   - Click the camera icon in address bar
   - Allow camera and microphone access
   - Refresh the page

2. **Check HTTPS:**
   - WebRTC requires HTTPS in production
   - Use `localhost` for development (HTTP is allowed)

3. **Check browser console:**
   - Look for getUserMedia errors
   - Check for WebRTC errors

4. **Test camera/microphone:**
   - Go to: https://www.webrtc-experiment.com/DetectRTC/
   - Verify devices are detected

### Issue 5: "ICE connection failed"

**Symptoms:**
- Can join but can't see other participants
- Connection state shows "failed" or "disconnected"
- Network connectivity issues

**Solutions:**

1. **Check STUN/TURN servers:**
   ```python
   # In video_chat/ice_servers.py
   # Make sure ICE servers are configured
   ```

2. **Check firewall:**
   - Allow UDP ports 3478, 5349
   - Allow TCP ports 80, 443

3. **Test ICE connectivity:**
   - Go to: https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/
   - Check if ICE candidates are gathered

### Issue 6: Redis connection errors

**Symptoms:**
- "Connection refused" errors
- "Error 111 connecting to localhost:6379"
- WebSocket connections fail immediately

**Solutions:**

**Windows:**
```bash
# Option 1: Use Docker
docker run -d -p 6379:6379 redis

# Option 2: Use WSL
wsl
sudo service redis-server start

# Option 3: Install Redis for Windows
# Download from: https://github.com/microsoftarchive/redis/releases
```

**Linux/Mac:**
```bash
# Start Redis
redis-server

# Or as service
sudo systemctl start redis
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

### Issue 7: "Module not found" errors

**Symptoms:**
- ImportError: No module named 'channels'
- ImportError: No module named 'channels_redis'

**Solutions:**

```bash
# Install all required packages
pip install -r requirements.txt

# Or install individually
pip install channels channels-redis redis

# Verify installation
python -c "import channels; print(channels.__version__)"
python -c "import channels_redis; print(channels_redis.__version__)"
```

### Issue 8: Database errors

**Symptoms:**
- "no such table: video_chat_videosession"
- "relation does not exist"

**Solutions:**

```bash
# Run migrations
python manage.py migrate

# If that doesn't work, try:
python manage.py migrate video_chat --fake-initial
python manage.py migrate video_chat

# Check migration status
python manage.py showmigrations video_chat
```

## Testing Checklist

Use this checklist to verify everything is working:

- [ ] Redis is running (`redis-cli ping` returns PONG)
- [ ] Channels is installed (`python -c "import channels"` works)
- [ ] Migrations are applied (`python manage.py migrate`)
- [ ] Server starts without errors (`python manage.py runserver`)
- [ ] Can access `/video/sessions/` page
- [ ] Can create a quick session
- [ ] Can join a session
- [ ] WebSocket connects (check browser console)
- [ ] Camera/microphone permissions granted
- [ ] Can see own video feed
- [ ] Can see other participants (test with 2 browser windows)

## Debug Mode

To get more detailed error messages:

1. **Enable Django debug mode:**
   ```python
   # In settings.py
   DEBUG = True
   ```

2. **Enable WebSocket logging:**
   ```python
   # In settings.py
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'handlers': {
           'console': {
               'class': 'logging.StreamHandler',
           },
       },
       'loggers': {
           'video_chat': {
               'handlers': ['console'],
               'level': 'DEBUG',
           },
           'channels': {
               'handlers': ['console'],
               'level': 'DEBUG',
           },
       },
   }
   ```

3. **Check browser console:**
   - Open Developer Tools (F12)
   - Go to Console tab
   - Look for errors in red

4. **Check Django logs:**
   - Look at terminal where `runserver` is running
   - Check for Python exceptions

## Still Not Working?

If you've tried everything above and it's still not working:

1. **Run the diagnostic script:**
   ```bash
   python test_video_chat.py
   ```

2. **Collect information:**
   - What error message do you see?
   - Where does the error occur? (browser console, Django logs, etc.)
   - What URL are you trying to access?
   - Output of `redis-cli ping`
   - Output of `python manage.py check`

3. **Check the logs:**
   - Browser console (F12 → Console)
   - Django terminal output
   - Redis logs (if applicable)

4. **Try a clean start:**
   ```bash
   # Stop all services
   # Kill Django server (Ctrl+C)
   # Stop Redis
   
   # Start fresh
   redis-server &
   python manage.py migrate
   python manage.py runserver
   
   # Test again
   ```

## Production Deployment Notes

For production deployment, you'll need:

1. **HTTPS:** WebRTC requires HTTPS (except localhost)
2. **TURN server:** For NAT traversal (not just STUN)
3. **Redis:** Production-ready Redis instance
4. **ASGI server:** Use Daphne or Uvicorn instead of `runserver`
5. **Proper CORS settings:** Configure ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS

Example production command:
```bash
daphne -b 0.0.0.0 -p 8000 metlab_edu.asgi:application
```

## Need More Help?

Provide these details:
1. Exact error message
2. Where the error occurs
3. Output of `python test_video_chat.py`
4. Browser and version
5. Operating system
6. Django version (`python manage.py version`)
