# Video Chat System API Endpoints

This document describes all URL routing and API endpoints for the video chat system.

## HTML Views (User Interface)

### Session Management Views

| Endpoint | Method | Description | Requirements |
|----------|--------|-------------|--------------|
| `/video/schedule/` | GET, POST | Schedule a new video session | 5.1, 5.2 |
| `/video/quick-start/` | GET, POST | Start an immediate video session | 1.1, 1.2 |
| `/video/sessions/` | GET | List user's video sessions | 5.1, 8.2 |
| `/video/session/<session_id>/` | GET | View session details | 5.1, 5.2, 8.2 |
| `/video/session/<session_id>/edit/` | GET, POST | Edit a scheduled session | 5.1, 5.2 |
| `/video/session/<session_id>/cancel/` | POST | Cancel a scheduled session | 5.2 |
| `/video/session/<session_id>/join/` | GET | Join a video session | 4.1, 4.2, 5.4 |
| `/video/session/<session_id>/calendar/` | GET | Download session as .ics file | 5.2 |

## REST API Endpoints

All REST API endpoints return JSON responses and require authentication.

### Session Management API

#### List Sessions
```
GET /video/api/sessions/
```

**Query Parameters:**
- `status` (optional): Filter by status (scheduled, active, completed, cancelled)
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "sessions": [
    {
      "session_id": "uuid",
      "title": "string",
      "description": "string",
      "session_type": "one_on_one|group|class",
      "status": "scheduled|active|completed|cancelled",
      "scheduled_time": "ISO 8601 datetime",
      "started_at": "ISO 8601 datetime",
      "ended_at": "ISO 8601 datetime",
      "duration_minutes": 60,
      "is_host": true,
      "host_username": "string",
      "participant_count": 5,
      "max_participants": 30,
      "is_recorded": false,
      "recording_url": "string",
      "allow_screen_share": true,
      "created_at": "ISO 8601 datetime"
    }
  ],
  "total_count": 100,
  "limit": 50,
  "offset": 0
}
```

**Requirements:** 1.1, 5.1

---

#### Create Session
```
POST /video/api/sessions/create/
```

**Request Body:**
```json
{
  "session_type": "one_on_one|group|class",
  "title": "string (required)",
  "description": "string (optional)",
  "scheduled_time": "ISO 8601 datetime (optional)",
  "duration_minutes": 60,
  "max_participants": 30,
  "allow_screen_share": true,
  "require_approval": false,
  "participant_ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "success": true,
  "session": {
    "session_id": "uuid",
    "title": "string",
    "description": "string",
    "session_type": "one_on_one|group|class",
    "status": "scheduled",
    "scheduled_time": "ISO 8601 datetime",
    "duration_minutes": 60,
    "max_participants": 30,
    "allow_screen_share": true,
    "created_at": "ISO 8601 datetime"
  }
}
```

**Requirements:** 1.1, 5.1

---

#### Get Session Details
```
GET /video/api/sessions/<session_id>/
```

**Response:**
```json
{
  "success": true,
  "session": {
    "session_id": "uuid",
    "title": "string",
    "description": "string",
    "session_type": "one_on_one|group|class",
    "status": "scheduled|active|completed|cancelled",
    "scheduled_time": "ISO 8601 datetime",
    "started_at": "ISO 8601 datetime",
    "ended_at": "ISO 8601 datetime",
    "duration_minutes": 60,
    "host_id": 1,
    "host_username": "string",
    "is_host": true,
    "is_participant": false,
    "max_participants": 30,
    "is_recorded": false,
    "recording_url": "string",
    "allow_screen_share": true,
    "require_approval": false,
    "participants": [
      {
        "user_id": 1,
        "username": "string",
        "role": "host|participant",
        "status": "invited|joined|left|removed",
        "joined_at": "ISO 8601 datetime",
        "left_at": "ISO 8601 datetime",
        "audio_enabled": true,
        "video_enabled": true,
        "screen_sharing": false,
        "connection_quality": "excellent|good|fair|poor|unknown"
      }
    ],
    "created_at": "ISO 8601 datetime"
  }
}
```

**Requirements:** 1.1, 5.1

---

#### Start Session
```
POST /video/api/sessions/<session_id>/start/
```

**Response:**
```json
{
  "success": true,
  "session": {
    "session_id": "uuid",
    "status": "active",
    "started_at": "ISO 8601 datetime"
  }
}
```

**Requirements:** 1.1, 5.1

---

#### End Session
```
POST /video/api/sessions/<session_id>/end/
```

**Response:**
```json
{
  "success": true,
  "session": {
    "session_id": "uuid",
    "status": "completed",
    "ended_at": "ISO 8601 datetime"
  }
}
```

**Requirements:** 1.1, 5.2

---

### Participant Management API

#### Join Session
```
POST /video/api/sessions/<session_id>/join/
```

**Response:**
```json
{
  "success": true,
  "participant": {
    "user_id": 1,
    "username": "string",
    "role": "host|participant",
    "status": "joined",
    "joined_at": "ISO 8601 datetime"
  },
  "session": {
    "session_id": "uuid",
    "status": "active",
    "title": "string"
  }
}
```

**Requirements:** 4.1, 4.2

---

#### Leave Session
```
POST /video/api/sessions/<session_id>/leave/
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully left the session"
}
```

**Requirements:** 4.1

---

#### Get Session Participants
```
GET /video/api/sessions/<session_id>/participants/
```

**Response:**
```json
{
  "success": true,
  "participants": [
    {
      "user_id": 1,
      "username": "string",
      "role": "host|participant",
      "status": "invited|joined|left|removed",
      "joined_at": "ISO 8601 datetime",
      "left_at": "ISO 8601 datetime",
      "audio_enabled": true,
      "video_enabled": true,
      "screen_sharing": false,
      "connection_quality": "excellent|good|fair|poor|unknown"
    }
  ],
  "total_count": 5
}
```

**Requirements:** 1.1, 4.1

---

### Media Control API

#### Update Media State
```
POST /video/api/sessions/<session_id>/update-media/
```

**Request Body:**
```json
{
  "audio_enabled": true,
  "video_enabled": false
}
```

**Response:**
```json
{
  "success": true,
  "media_state": {
    "audio_enabled": true,
    "video_enabled": false
  }
}
```

**Requirements:** 1.5, 7.1, 7.2, 7.3

---

### Recording API

#### Start Recording
```
POST /video/api/sessions/<session_id>/recording/start/
```

**Response:**
```json
{
  "success": true,
  "message": "Recording started successfully"
}
```

**Requirements:** 6.1, 6.2

---

#### Stop Recording
```
POST /video/api/sessions/<session_id>/recording/stop/
```

**Response:**
```json
{
  "success": true,
  "message": "Recording stopped successfully",
  "recording_url": "string"
}
```

**Requirements:** 6.4, 6.5

---

### Statistics API

#### Get Session Statistics
```
GET /video/api/sessions/<session_id>/statistics/
```

**Response:**
```json
{
  "success": true,
  "statistics": {
    "total_participants": 10,
    "peak_participants": 8,
    "average_duration_minutes": 45,
    "total_events": 50,
    "connection_issues": 2
  }
}
```

**Requirements:** 8.1, 8.2, 8.3

---

### Configuration API

#### Get ICE Servers
```
GET /video/api/ice-servers/
```

**Response:**
```json
{
  "iceServers": [
    {
      "urls": "stun:stun.l.google.com:19302"
    },
    {
      "urls": "turn:turn.example.com:3478",
      "username": "string",
      "credential": "string"
    }
  ]
}
```

**Requirements:** 1.3, 4.3, 9.1

---

## WebSocket Endpoints

### Video Session Signaling

```
ws://domain/ws/video-session/<session_id>/
```

**Connection Requirements:**
- User must be authenticated
- User must have access to the session (host or invited participant)

**Message Types:**

#### Client → Server Messages

1. **Join Session**
```json
{
  "type": "join_session",
  "session_id": "uuid"
}
```

2. **Leave Session**
```json
{
  "type": "leave_session"
}
```

3. **WebRTC Offer**
```json
{
  "type": "webrtc_offer",
  "target_user_id": 123,
  "offer": {
    "type": "offer",
    "sdp": "string"
  }
}
```

4. **WebRTC Answer**
```json
{
  "type": "webrtc_answer",
  "target_user_id": 123,
  "answer": {
    "type": "answer",
    "sdp": "string"
  }
}
```

5. **ICE Candidate**
```json
{
  "type": "ice_candidate",
  "target_user_id": 123,
  "candidate": {
    "candidate": "string",
    "sdpMLineIndex": 0,
    "sdpMid": "string"
  }
}
```

6. **Media State Change**
```json
{
  "type": "media_state_change",
  "audio_enabled": true,
  "video_enabled": false
}
```

7. **Screen Share Start**
```json
{
  "type": "screen_share_start"
}
```

8. **Screen Share Stop**
```json
{
  "type": "screen_share_stop"
}
```

9. **Chat Message**
```json
{
  "type": "chat_message",
  "message": "string"
}
```

#### Server → Client Messages

1. **User Joined**
```json
{
  "type": "user_joined",
  "user_id": 123,
  "username": "string",
  "role": "host|participant"
}
```

2. **User Left**
```json
{
  "type": "user_left",
  "user_id": 123,
  "username": "string"
}
```

3. **WebRTC Offer**
```json
{
  "type": "webrtc_offer",
  "from_user_id": 123,
  "offer": {
    "type": "offer",
    "sdp": "string"
  }
}
```

4. **WebRTC Answer**
```json
{
  "type": "webrtc_answer",
  "from_user_id": 123,
  "answer": {
    "type": "answer",
    "sdp": "string"
  }
}
```

5. **ICE Candidate**
```json
{
  "type": "ice_candidate",
  "from_user_id": 123,
  "candidate": {
    "candidate": "string",
    "sdpMLineIndex": 0,
    "sdpMid": "string"
  }
}
```

6. **Media State Update**
```json
{
  "type": "media_state_update",
  "user_id": 123,
  "audio_enabled": true,
  "video_enabled": false
}
```

7. **Screen Share Started**
```json
{
  "type": "screen_share_started",
  "user_id": 123,
  "username": "string"
}
```

8. **Screen Share Stopped**
```json
{
  "type": "screen_share_stopped",
  "user_id": 123
}
```

9. **Recording Started**
```json
{
  "type": "recording_started"
}
```

10. **Recording Stopped**
```json
{
  "type": "recording_stopped",
  "recording_url": "string"
}
```

11. **Error**
```json
{
  "type": "error",
  "error": "string"
}
```

**Requirements:** 1.2, 1.3, 4.1, 4.3

---

## Error Responses

All API endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message description"
}
```

**HTTP Status Codes:**
- `400 Bad Request`: Invalid request data or validation error
- `403 Forbidden`: Permission denied or authentication required
- `404 Not Found`: Session or resource not found
- `500 Internal Server Error`: Server-side error

---

## Authentication

All endpoints require user authentication via Django's session authentication. Users must be logged in to access any video chat functionality.

For API endpoints, authentication can be provided via:
1. Session cookies (for browser-based requests)
2. Django authentication headers (for programmatic access)

---

## Rate Limiting

The following rate limits are enforced:

- **Session Creation**: Maximum 10 sessions per hour per user
- **WebSocket Messages**: Maximum 100 messages per minute per connection
- **API Requests**: Standard Django rate limiting applies

Users who exceed rate limits will receive a `429 Too Many Requests` response.

---

## URL Namespace

All video chat URLs are namespaced under `video_chat:`. To reverse URLs in Django:

```python
from django.urls import reverse

# HTML views
schedule_url = reverse('video_chat:schedule_session')
join_url = reverse('video_chat:join_session', kwargs={'session_id': session_id})

# API endpoints
api_sessions_url = reverse('video_chat:api_session_list')
api_join_url = reverse('video_chat:api_join_session', kwargs={'session_id': session_id})
```

---

## Integration Points

### Learning Module Integration

Video sessions can be linked to teacher classes:
- `/learning/class/<class_id>/video/` - Start video session for a class
- Sessions automatically invite all enrolled students
- Attendance is recorded when students join

### Community Module Integration

Video sessions can be linked to tutor bookings:
- `/community/booking/<booking_id>/video/` - Start video session for a tutoring session
- Sessions link to existing tutor-student relationships

### Parent Monitoring Integration

Parents can view their child's video session history:
- `/learning/parent/child/<child_id>/video-sessions/` - View child's video sessions
- Notifications sent when child joins/leaves sessions
