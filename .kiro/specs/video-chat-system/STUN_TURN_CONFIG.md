# STUN/TURN Server Configuration

This document describes the STUN/TURN server configuration for the MetLab Education video chat system.

## Overview

The video chat system uses WebRTC for peer-to-peer video/audio communication. STUN and TURN servers are essential for establishing connections through firewalls and NAT devices.

- **STUN (Session Traversal Utilities for NAT)**: Helps discover public IP addresses
- **TURN (Traversal Using Relays around NAT)**: Relays media traffic when direct connections fail

## Configuration Files

### Development Configuration

File: `metlab_edu/settings.py`

```python
WEBRTC_ICE_SERVERS = [
    {'urls': 'stun:stun.l.google.com:19302'},
    {'urls': 'stun:stun1.l.google.com:19302'},
    {'urls': 'stun:stun2.l.google.com:19302'},
    {'urls': 'stun:stun3.l.google.com:19302'},
    {'urls': 'stun:stun4.l.google.com:19302'},
]

VIDEO_CHAT_MAX_PARTICIPANTS = 30
VIDEO_CHAT_SESSION_TIMEOUT = 3600  # 1 hour
VIDEO_CHAT_RECORDING_ENABLED = True
VIDEO_CHAT_SCREEN_SHARE_ENABLED = True
```

For development, we use public STUN servers which are sufficient for most testing scenarios.

### Production Configuration

File: `metlab_edu/settings_production.py`

The production configuration includes both STUN and TURN servers. TURN servers are configured via environment variables:

```python
WEBRTC_ICE_SERVERS = [
    # Public STUN servers for fallback
    {'urls': 'stun:stun.l.google.com:19302'},
    {'urls': 'stun:stun1.l.google.com:19302'},
    
    # Production TURN server
    {
        'urls': os.environ.get('TURN_SERVER_URL', 'turn:turn.example.com:3478'),
        'username': os.environ.get('TURN_USERNAME', ''),
        'credential': os.environ.get('TURN_PASSWORD', ''),
    },
]
```

### Environment Variables

File: `.env.production.template`

```bash
# WebRTC TURN Server Configuration
TURN_SERVER_URL=turn:turn.yourdomain.com:3478
TURN_USERNAME=your-turn-username
TURN_PASSWORD=your-turn-password

# Optional: Secondary TURN server for redundancy
# TURN_SERVER_URL_2=turn:turn2.yourdomain.com:3478
# TURN_USERNAME_2=your-turn-username-2
# TURN_PASSWORD_2=your-turn-password-2

# Video Chat Settings
VIDEO_CHAT_MAX_PARTICIPANTS=30
VIDEO_CHAT_SESSION_TIMEOUT=3600
VIDEO_CHAT_RECORDING_ENABLED=True
VIDEO_CHAT_SCREEN_SHARE_ENABLED=True
```

## API Endpoint

The ICE server configuration is exposed to authenticated users via an API endpoint:

**Endpoint**: `/video-chat/api/ice-servers/`  
**Method**: GET  
**Authentication**: Required (login_required)

**Response**:
```json
{
  "iceServers": [
    {"urls": "stun:stun.l.google.com:19302"},
    {"urls": "stun:stun1.l.google.com:19302"},
    {
      "urls": "turn:turn.yourdomain.com:3478",
      "username": "metlab_turn_user",
      "credential": "your_secure_password"
    }
  ],
  "maxParticipants": 30,
  "sessionTimeout": 3600,
  "recordingEnabled": true,
  "screenShareEnabled": true
}
```

## Frontend Integration

The frontend JavaScript (`static/js/video_call.js`) automatically fetches the ICE server configuration on initialization:

```javascript
async loadICEServerConfiguration() {
    const response = await fetch('/video-chat/api/ice-servers/');
    const data = await response.json();
    this.iceServers = data.iceServers;
    this.videoSettings = {
        maxParticipants: data.maxParticipants,
        sessionTimeout: data.sessionTimeout,
        recordingEnabled: data.recordingEnabled,
        screenShareEnabled: data.screenShareEnabled
    };
}
```

## Usage in WebRTC

The ICE servers are used when creating RTCPeerConnection objects:

```javascript
const peerConnection = new RTCPeerConnection({
    iceServers: this.iceServers
});
```

## Testing

### Verify Configuration

```bash
# Check Django settings
python manage.py shell -c "from django.conf import settings; print(settings.WEBRTC_ICE_SERVERS)"

# Test ICE servers utility
python manage.py shell -c "from video_chat.ice_servers import get_video_chat_settings; import json; print(json.dumps(get_video_chat_settings(), indent=2))"
```

### Test TURN Server

Use the Trickle ICE test tool: https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/

1. Enter your TURN server URL
2. Enter username and password
3. Click "Gather candidates"
4. Look for "relay" type candidates

## Requirements Satisfied

This configuration satisfies the following requirements:

- **Requirement 1.3**: WebRTC connection establishment within 5 seconds
- **Requirement 4.3**: Reliable connection establishment for students
- **Requirement 9.1**: Network quality handling and connection reliability

## Next Steps

For production deployment:

1. Set up a TURN server (see `TURN_SERVER_SETUP.md`)
2. Configure environment variables in `.env.production`
3. Test the configuration with the Trickle ICE tool
4. Monitor connection success rates and adjust as needed

## References

- [WebRTC ICE Documentation](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Protocols)
- [TURN Server Setup Guide](./TURN_SERVER_SETUP.md)
- [Coturn Documentation](https://github.com/coturn/coturn)
