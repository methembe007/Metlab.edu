# Video Service

The Video Service handles video uploads, processing, storage, and streaming for the Metlab.edu platform.

## Features

- **Video Upload**: Streaming upload of video files up to 2GB
- **Video Processing**: Automatic transcoding to multiple resolutions (1080p, 720p, 480p, 360p)
- **Thumbnail Generation**: Automatic generation of thumbnails at 0%, 25%, 50%, 75% timestamps
- **HLS Streaming**: Adaptive bitrate streaming using HLS
- **View Tracking**: Track student video viewing progress and analytics
- **Analytics**: Provide viewing statistics for teachers

## Architecture

### Components

- **gRPC Server**: Handles all video-related operations
- **Repository Layer**: Database operations for videos, variants, thumbnails, and views
- **FFmpeg Processor**: Video processing, transcoding, and thumbnail generation
- **Storage Client**: S3-compatible storage for video files

### Database Schema

- `videos`: Main video records
- `video_variants`: Processed video variants at different resolutions
- `video_thumbnails`: Generated thumbnails
- `video_views`: Student viewing records

## Configuration

Environment variables:

- `PORT`: gRPC server port (default: 50052)
- `DB_HOST`: PostgreSQL host (default: postgres-service)
- `DB_PORT`: PostgreSQL port (default: 5432)
- `DB_USER`: Database user (default: postgres)
- `DB_PASSWORD`: Database password (default: postgres)
- `DB_NAME`: Database name (default: metlab)
- `REDIS_HOST`: Redis host (default: redis-service)
- `REDIS_PORT`: Redis port (default: 6379)
- `REDIS_PASSWORD`: Redis password (optional)
- `S3_ENDPOINT`: S3 endpoint URL (default: http://minio-service:9000)
- `S3_ACCESS_KEY`: S3 access key (default: minioadmin)
- `S3_SECRET_KEY`: S3 secret key (default: minioadmin123)
- `VIDEO_BUCKET`: S3 bucket for videos (default: metlab-videos)
- `TEMP_DIR`: Temporary directory for processing (default: /tmp/video-processing)

## Development

### Prerequisites

- Go 1.21+
- PostgreSQL 15+
- Redis 7+
- MinIO or S3-compatible storage
- FFmpeg and FFprobe

### Running Locally

```bash
# Install dependencies
go mod download

# Run database migrations
# (migrations are in ./migrations directory)

# Run the service
go run cmd/server/main.go
```

### Building

```bash
# Build binary
go build -o video-service cmd/server/main.go

# Build Docker image
docker build -t metlab/video-service:latest .
```

## API

The service implements the VideoService gRPC interface defined in `proto/video/video.proto`:

- `UploadVideo`: Stream upload a video file
- `ListVideos`: List videos for a class
- `GetVideo`: Get video details
- `GetStreamingURL`: Get HLS streaming URL
- `RecordView`: Record video viewing progress
- `GetVideoAnalytics`: Get viewing analytics

## Video Processing Pipeline

1. **Upload**: Video is uploaded via streaming gRPC
2. **Validation**: File format (MP4, WebM, MOV) and size (max 2GB) validation
3. **Storage**: Original video stored in S3
4. **Queue**: Processing job enqueued to Redis
5. **Processing** (implemented in task 25):
   - Extract metadata (duration, resolution, codec)
   - Generate multiple resolution variants
   - Create HLS manifest for adaptive streaming
   - Generate thumbnails
6. **Ready**: Video marked as ready for streaming

## Storage Structure

```
videos/
  {video_id}/
    original/
      {filename}
    variants/
      1080p.mp4
      720p.mp4
      480p.mp4
      360p.mp4
    hls/
      playlist.m3u8
      segment_001.ts
      segment_002.ts
      ...
    thumbnails/
      thumb_0.jpg
      thumb_25.jpg
      thumb_50.jpg
      thumb_75.jpg
```

## Testing

```bash
# Run tests
go test ./...

# Run tests with coverage
go test -cover ./...
```

## Deployment

The service is deployed as a Kubernetes Deployment with:

- Resource limits for FFmpeg processing
- Persistent volume for temporary processing
- Health and readiness probes
- Horizontal pod autoscaling

See `infrastructure/k8s/video-service.yaml` for Kubernetes manifests.
