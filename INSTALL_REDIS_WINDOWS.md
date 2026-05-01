# Install Redis on Windows - Quick Guide

## Option 1: Use Memurai (Recommended for Windows)

Memurai is a Redis-compatible server for Windows that's actively maintained.

### Download and Install:
1. Go to: https://www.memurai.com/get-memurai
2. Download Memurai (free version)
3. Run the installer
4. It will install as a Windows service and start automatically

### Test it:
```bash
memurai-cli ping
```
Should return: `PONG`

## Option 2: Use Redis for Windows (Legacy)

### Download:
1. Go to: https://github.com/microsoftarchive/redis/releases
2. Download: `Redis-x64-3.0.504.msi` (or latest version)
3. Run the installer
4. Check "Add to PATH" during installation

### Start Redis:
```bash
# Redis should start automatically as a service
# To start manually:
redis-server
```

### Test it:
```bash
redis-cli ping
```
Should return: `PONG`

## Option 3: Use WSL (Windows Subsystem for Linux)

If you have WSL installed:

```bash
# Open WSL terminal
wsl

# Install Redis
sudo apt-get update
sudo apt-get install redis-server

# Start Redis
sudo service redis-server start

# Test it
redis-cli ping
```

## Option 4: Quick Python Alternative (For Testing Only)

If you just want to test the video chat quickly without installing Redis, you can use an in-memory channel layer:

### Edit `metlab_edu/settings.py`:

Find the `CHANNEL_LAYERS` section and temporarily replace it with:

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}
```

**⚠️ WARNING:** This only works for single-server testing. Don't use in production!

## After Installing Redis

Once Redis is installed and running:

```bash
# 1. Test Redis connection
redis-cli ping
# Should return: PONG

# 2. Run the diagnostic
python test_video_chat.py

# 3. Start Django server
python manage.py runserver

# 4. Test video chat
# Go to: http://localhost:8000/video/sessions/
```

## Troubleshooting

### "redis-cli not found"
- Redis isn't in your PATH
- Try: `C:\Program Files\Redis\redis-cli.exe ping`
- Or reinstall and check "Add to PATH"

### "Could not connect to Redis"
- Redis service isn't running
- Windows: Open Services (services.msc), find Redis, click Start
- Or run: `redis-server` in a terminal

### Port already in use
- Another service is using port 6379
- Stop the other service or change Redis port

## Recommended: Memurai

For Windows development, I recommend **Memurai** because:
- ✅ Native Windows application
- ✅ Actively maintained
- ✅ Redis-compatible
- ✅ Easy installation
- ✅ Runs as Windows service
- ✅ Free for development

Download: https://www.memurai.com/get-memurai
