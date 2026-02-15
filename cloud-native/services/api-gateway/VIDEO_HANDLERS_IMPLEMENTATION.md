# Video Handlers Implementation

## Overview

This document describes the implementation of HTTP handlers for video endpoints in the API Gateway service. These handlers provide REST API access to the Video Service via gRPC.

## Implementation Date

February 15, 2026

## Endpoints Implemented

### 1. GET /api/videos - List Videos

**Purpose**: List all videos for a specific class

**Authentication**: Required (JWT token)

**Query Parameters**:
- `class_id` (required): The class ID to filter videos
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Number of items per page (default: 20, max: 100)

**Request Example**:
```http
GET /api/videos?class_id=class-123&page=1&page_size=20
Authorization: Bearer <jwt-token>
```

**Response Example**:
```json
{
  "videos": [
    {
      "id": "video-123",
      "title": "Introduction to Algebra",
      "description": "Basic algebra concepts",
      "duration_seconds": 1800,
      "thumbnail_url": "https://storage.example.com/thumbnails/video-123.jpg",
      "status": "ready",
      "created_at": 1707955200
    }
  ],
  "total_count": 45
}
```

**Error Responses**:
- `400 Bad Request`: Missing or invalid class_id
- `401 Unauthorized`: Missing or invalid JWT token
- `500 Internal Server Error`: Service unavailable

---

### 2. POST /api/videos - Upload Video

**Purpose**: Upload a new video file

**Authentication**: Required (JWT token)

**Content-Type**: `multipart/form-data`

**Form Fields**:
- `teacher_id` (required): Teacher's user ID
- `class_id` (required): Class ID to associate video with
- `title` (required): Video title
- `description` (optional): Video description
- `video` (required): Video file (max 2GB, formats: MP4, WebM, MOV)

**Request Example**:
```http
POST /api/videos
Authorization: Bearer <jwt-token>
Content-Type: multipart/form-data

teacher_id=teacher-123
class_id=class-456
title=Introduction to Calculus
description=First lesson on derivatives
video=<binary-file-data>
```

**Response Example**:
```json
{
  "video_id": "video-789",
  "status": "uploading"
}
```

**Implementation Details**:
- Uses gRPC streaming for efficient large file uploads
- Sends metadata first, then streams file in 1MB chunks
- Timeout: 30 minutes to accommodate large files
- File is validated on the Video Service side

**Error Responses**:
- `400 Bad Request`: Missing required fields or invalid file
- `401 Unauthorized`: Missing or invalid JWT token
- `413 Payload Too Large`: File exceeds 2GB limit
- `500 Internal Server Error`: Upload failed

---

### 3. GET /api/videos/:id - Get Video Details

**Purpose**: Retrieve detailed information about a specific video

**Authentication**: Required (JWT token)

**URL Parameters**:
- `id` (required): Video ID

**Request Example**:
```http
GET /api/videos/video-123
Authorization: Bearer <jwt-token>
```

**Response Example**:
```json
{
  "id": "video-123",
  "title": "Introduction to Algebra",
  "description": "Basic algebra concepts",
  "duration_seconds": 1800,
  "thumbnail_url": "https://storage.example.com/thumbnails/video-123.jpg",
  "status": "ready",
  "created_at": 1707955200,
  "variants": [
    {
      "resolution": "1080p",
      "bitrate_kbps": 5000,
      "storage_path": "videos/video-123/1080p.mp4"
    },
    {
      "resolution": "720p",
      "bitrate_kbps": 2500,
      "storage_path": "videos/video-123/720p.mp4"
    }
  ]
}
```

**Error Responses**:
- `400 Bad Request`: Invalid video ID
- `401 Unauthorized`: Missing or invalid JWT token
- `404 Not Found`: Video not found
- `403 Forbidden`: User doesn't have access to this video

---

### 4. GET /api/videos/:id/stream - Get Streaming URL

**Purpose**: Generate a signed URL for video streaming

**Authentication**: Required (JWT token)

**URL Parameters**:
- `id` (required): Video ID

**Query Parameters**:
- `resolution` (optional): Preferred resolution (e.g., "1080p", "720p")

**Request Example**:
```http
GET /api/videos/video-123/stream?resolution=720p
Authorization: Bearer <jwt-token>
```

**Response Example**:
```json
{
  "url": "https://storage.example.com/videos/video-123/720p.mp4?signature=xyz&expires=1707958800",
  "expires_at": 1707958800,
  "manifest_url": "https://storage.example.com/videos/video-123/manifest.m3u8?signature=abc&expires=1707958800"
}
```

**Implementation Details**:
- URL is valid for 1 hour
- Supports HLS adaptive streaming via manifest_url
- Falls back to direct URL if resolution not available

**Error Responses**:
- `400 Bad Request`: Invalid video ID
- `401 Unauthorized`: Missing or invalid JWT token
- `404 Not Found`: Video not found or not ready
- `403 Forbidden`: User doesn't have access to this video

---

### 5. POST /api/videos/:id/view - Record Video View

**Purpose**: Track student video viewing progress

**Authentication**: Required (JWT token)

**URL Parameters**:
- `id` (required): Video ID

**Request Body**:
```json
{
  "position_seconds": 450,
  "watch_duration_seconds": 120,
  "completed": false
}
```

**Request Fields**:
- `position_seconds` (required): Current playback position in seconds
- `watch_duration_seconds` (required): Duration watched in this session
- `completed` (optional): Whether the video was completed (default: false)

**Request Example**:
```http
POST /api/videos/video-123/view
Authorization: Bearer <jwt-token>
Content-Type: application/json

{
  "position_seconds": 450,
  "watch_duration_seconds": 120,
  "completed": false
}
```

**Response Example**:
```json
{
  "success": true
}
```

**Implementation Details**:
- Updates or creates video_views record
- Tracks total watch time and last position for resume
- Used for analytics and progress tracking

**Error Responses**:
- `400 Bad Request`: Invalid request body or negative values
- `401 Unauthorized`: Missing or invalid JWT token
- `404 Not Found`: Video not found

---

### 6. GET /api/videos/:id/analytics - Get Video Analytics

**Purpose**: Retrieve viewing analytics for a video (teacher only)

**Authentication**: Required (JWT token, teacher role)

**URL Parameters**:
- `id` (required): Video ID

**Request Example**:
```http
GET /api/videos/video-123/analytics
Authorization: Bearer <jwt-token>
```

**Response Example**:
```json
{
  "video_id": "video-123",
  "total_views": 28,
  "student_views": [
    {
      "student_id": "student-456",
      "student_name": "John Doe",
      "percentage_watched": 85,
      "total_watch_seconds": 1530,
      "completed": false,
      "last_viewed_at": 1707955200
    },
    {
      "student_id": "student-789",
      "student_name": "Jane Smith",
      "percentage_watched": 100,
      "total_watch_seconds": 1800,
      "completed": true,
      "last_viewed_at": 1707958800
    }
  ]
}
```

**Implementation Details**:
- Only accessible by teachers
- Shows per-student viewing statistics
- Includes completion status and watch percentage
- Helps teachers identify students who haven't watched videos

**Error Responses**:
- `400 Bad Request`: Invalid video ID
- `401 Unauthorized`: Missing or invalid JWT token
- `403 Forbidden`: User is not a teacher or doesn't own this video
- `404 Not Found`: Video not found

---

## Technical Implementation Details

### File Structure

```
cloud-native/services/api-gateway/internal/handlers/
├── video.go          # Video handlers implementation
├── auth.go           # Authentication handlers
└── handlers.go       # Handler struct and constructor
```

### Dependencies

- **Chi Router**: URL routing and parameter extraction
- **gRPC Video Client**: Communication with Video Service
- **Transformers Package**: JSON encoding/decoding and error handling
- **Context**: User authentication and request timeouts

### Request Flow

1. **Authentication**: Middleware validates JWT token and adds user_id to context
2. **Rate Limiting**: Middleware enforces 100 requests/minute per IP
3. **Handler**: Extracts parameters, validates input
4. **gRPC Call**: Transforms HTTP request to gRPC and calls Video Service
5. **Response**: Transforms gRPC response to HTTP JSON response

### Error Handling

All handlers use consistent error handling:
- Input validation errors return 400 Bad Request
- Authentication errors return 401 Unauthorized
- Authorization errors return 403 Forbidden
- Not found errors return 404 Not Found
- gRPC errors are mapped to appropriate HTTP status codes
- Internal errors return 500 Internal Server Error

### Validation

**ListVideos**:
- class_id is required
- page must be positive integer
- page_size must be between 1 and 100

**UploadVideo**:
- teacher_id, class_id, title are required
- video file is required
- file size validated by Video Service

**RecordView**:
- position_seconds must be non-negative
- watch_duration_seconds must be non-negative

### Timeouts

- Standard operations: 10 seconds
- Video upload: 30 minutes (large file support)

### Streaming Implementation

The UploadVideo handler uses gRPC bidirectional streaming:
1. Sends metadata message first
2. Streams file in 1MB chunks
3. Closes stream and receives response
4. Returns video_id and status to client

## Testing

### Manual Testing

Use curl or Postman to test endpoints:

```bash
# List videos
curl -X GET "http://localhost:8080/api/videos?class_id=class-123" \
  -H "Authorization: Bearer <token>"

# Get video details
curl -X GET "http://localhost:8080/api/videos/video-123" \
  -H "Authorization: Bearer <token>"

# Get streaming URL
curl -X GET "http://localhost:8080/api/videos/video-123/stream" \
  -H "Authorization: Bearer <token>"

# Record view
curl -X POST "http://localhost:8080/api/videos/video-123/view" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"position_seconds": 450, "watch_duration_seconds": 120}'

# Get analytics
curl -X GET "http://localhost:8080/api/videos/video-123/analytics" \
  -H "Authorization: Bearer <token>"

# Upload video
curl -X POST "http://localhost:8080/api/videos" \
  -H "Authorization: Bearer <token>" \
  -F "teacher_id=teacher-123" \
  -F "class_id=class-456" \
  -F "title=Test Video" \
  -F "description=Test Description" \
  -F "video=@/path/to/video.mp4"
```

### Integration Testing

Integration tests should verify:
- Authentication middleware integration
- gRPC client communication
- Error handling and status codes
- Request/response transformation
- File upload streaming

## Requirements Mapping

This implementation satisfies the following requirements from the specification:

- **Requirement 4.1**: Video upload endpoint with format validation
- **Requirement 4.2**: Video storage and processing trigger
- **Requirement 4.3**: Video metadata and thumbnail support
- **Requirement 4.4**: Video listing and retrieval
- **Requirement 4.5**: Video view tracking
- **Requirement 7.1**: Student viewing status tracking
- **Requirement 7.2**: View duration tracking with 10-second granularity
- **Requirement 7.3**: Percentage watched calculation
- **Requirement 7.4**: Identification of students who haven't started videos
- **Requirement 7.5**: Real-time viewing statistics updates

## Future Enhancements

1. **Batch Operations**: Support uploading multiple videos at once
2. **Video Transcoding Status**: WebSocket updates for processing status
3. **Thumbnail Selection**: Allow teachers to choose custom thumbnails
4. **Video Chapters**: Support for chapter markers and navigation
5. **Subtitles/Captions**: Upload and manage subtitle files
6. **Video Sharing**: Generate shareable links with expiration
7. **Download Support**: Allow offline video downloads for students
8. **Quality Selection**: Let students manually select video quality
9. **Playback Speed**: Support for variable playback speeds
10. **Video Comments**: Allow students to comment at specific timestamps

## Related Files

- `cloud-native/services/api-gateway/internal/router/router.go` - Route definitions
- `cloud-native/proto/video/video.proto` - gRPC service definition
- `cloud-native/services/video/` - Video Service implementation
- `.kiro/specs/cloud-native-architecture/requirements.md` - Requirements document
- `.kiro/specs/cloud-native-architecture/design.md` - Design document

## Completion Status

✅ All 6 video endpoints implemented
✅ Request validation added
✅ Error handling implemented
✅ gRPC streaming support for uploads
✅ Authentication integration
✅ Documentation complete

## Task Reference

This implementation completes Task 19 from the cloud-native architecture implementation plan:
- Task: "Implement HTTP handlers for Video endpoints"
- Status: Complete
- Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 7.1, 7.2, 7.3, 7.4, 7.5
