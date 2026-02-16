# Video Upload Feature - Quick Reference

## What Was Implemented

Task 24 has been completed with the following enhancements to the video upload functionality:

### 1. Enhanced Format Validation ✅
- Validates video files are MP4, WebM, or MOV format
- Uses FFprobe to detect actual video format
- Returns clear error messages for unsupported formats

### 2. Redis-Based Job Queue ✅
- Created new `queue` package in shared utilities
- Implements Redis-backed job queue for background processing
- Supports enqueue, dequeue, size, and clear operations
- Jobs are JSON-serialized with metadata

### 3. Video Upload Flow ✅
The complete upload process:
1. Client sends metadata (teacher_id, class_id, title, filename, file_size)
2. Service validates metadata and file size (max 2GB)
3. Creates video record in database with status "uploading"
4. Receives video chunks via streaming gRPC
5. Writes chunks to temporary file
6. Validates video format using FFprobe
7. Uploads video to S3 storage (videos/{id}/original/)
8. Updates video status to "processing"
9. Enqueues processing job to Redis queue
10. Returns video ID and status to client

### 4. Error Handling ✅
- Invalid metadata → INVALID_ARGUMENT
- File size > 2GB → INVALID_ARGUMENT
- Unsupported format → INVALID_ARGUMENT with format details
- Database errors → INTERNAL, video status set to "failed"
- Storage errors → INTERNAL, video status set to "failed"
- Queue errors → Logged but doesn't fail upload

## Files Modified

1. **cloud-native/shared/queue/queue.go** (NEW)
   - Redis-based job queue implementation

2. **cloud-native/shared/queue/README.md** (NEW)
   - Queue package documentation

3. **cloud-native/services/video/internal/ffmpeg/processor.go**
   - Enhanced `ValidateVideoFile` to check for MP4, WebM, MOV

4. **cloud-native/services/video/internal/service/video_service.go**
   - Added Queue interface and field
   - Updated constructor to accept queue
   - Implemented job queuing in UploadVideo

5. **cloud-native/services/video/cmd/server/main.go**
   - Added Redis client initialization
   - Added queue initialization
   - Updated service initialization

6. **cloud-native/services/video/go.mod**
   - Added redis/go-redis/v9 dependency

7. **cloud-native/services/video/.env.example**
   - Added Redis configuration variables

8. **cloud-native/services/video/README.md**
   - Updated configuration section
   - Updated prerequisites
   - Updated processing pipeline

## Configuration

New environment variables:
```bash
REDIS_HOST=redis-service
REDIS_PORT=6379
REDIS_PASSWORD=
```

## Testing the Upload

To test the video upload functionality:

```bash
# 1. Ensure Redis is running
docker run -d -p 6379:6379 redis:7-alpine

# 2. Start the video service
cd cloud-native/services/video
go run cmd/server/main.go

# 3. Use grpcurl to test upload
grpcurl -plaintext -d @ localhost:50052 video.VideoService/UploadVideo <<EOF
{
  "metadata": {
    "teacher_id": "teacher-123",
    "class_id": "class-456",
    "title": "Introduction to Physics",
    "description": "First lesson",
    "filename": "physics-intro.mp4",
    "file_size": 10485760
  }
}
EOF
```

## Queue Monitoring

Check queue size:
```bash
redis-cli LLEN video-processing
```

View queued jobs:
```bash
redis-cli LRANGE video-processing 0 -1
```

## Next Steps

Task 25 will implement the video processing worker that:
- Dequeues jobs from Redis
- Transcodes videos to multiple resolutions
- Generates HLS manifests
- Creates thumbnails
- Updates video status to "ready"

## Requirements Satisfied

✅ **Requirement 4.1**: Video upload with format validation (MP4, WebM, MOV)
✅ **Requirement 4.2**: Storage and processing pipeline setup
✅ **Task 24.1**: Implement UploadVideo gRPC streaming handler
✅ **Task 24.2**: Validate video file format and size
✅ **Task 24.3**: Stream video chunks to S3 storage
✅ **Task 24.4**: Create video record in database with 'uploading' status
✅ **Task 24.5**: Queue video processing job
