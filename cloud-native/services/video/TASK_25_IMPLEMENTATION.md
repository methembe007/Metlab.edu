# Task 25: Video Processing Pipeline Implementation

## Summary

Implemented a complete background video processing pipeline that handles video transcoding, thumbnail generation, and HLS manifest creation for adaptive streaming.

## Implementation Details

### 1. Video Processor Worker (`internal/worker/processor.go`)

Created a background worker that:

- **Polls Redis Queue**: Continuously dequeues video processing jobs
- **Downloads Original Video**: Retrieves uploaded video from S3 storage
- **Extracts Metadata**: Uses FFmpeg to get duration, resolution, codec information
- **Generates Resolution Variants**: Creates multiple quality versions (1080p, 720p, 480p, 360p)
  - Only generates variants if original resolution is high enough
  - Uses recommended bitrates for each resolution
  - Transcodes with H.264 video and AAC audio
- **Creates HLS Manifest**: Generates adaptive streaming playlist and segments
  - 10-second segments for smooth playback
  - Uploads all segments and manifest to S3
- **Generates Thumbnails**: Creates 4 thumbnails at 0%, 25%, 50%, 75% timestamps
  - Scaled to 320px width
  - Saved as JPEG format
- **Updates Database**: Records all variants and thumbnails in database
- **Updates Status**: Marks video as 'ready' when processing completes

### 2. Worker Command (`cmd/worker/main.go`)

Created a standalone worker process that:

- Initializes database, Redis, and S3 connections
- Creates video processor instance
- Handles graceful shutdown on SIGTERM/SIGINT
- Runs processing loop in background
- Logs all operations with structured logging

### 3. Storage Client Enhancement (`shared/storage/s3.go`)

Added `GetObject` method to support streaming downloads:

```go
func (c *Client) GetObject(ctx context.Context, bucket, key string) (io.ReadCloser, error)
```

This enables efficient downloading of large video files without loading entire file into memory.

### 4. Video Service Updates (`internal/service/video_service.go`)

Updated video upload to properly enqueue processing jobs:

- Creates `queue.Job` struct with video metadata
- Enqueues job to Redis queue after successful upload
- Sets video status to 'processing'

### 5. Deployment Configuration

Created Kubernetes deployment manifest (`infrastructure/k8s/video-worker-deployment.yaml`):

- 2 replicas for redundancy and throughput
- Resource limits: 4Gi memory, 2 CPU cores
- Temporary storage volume for video processing
- Environment variables for all service connections
- Secrets for sensitive credentials

### 6. Docker Configuration

Created `Dockerfile.worker` with:

- Multi-stage build for smaller image size
- FFmpeg installation for video processing
- Non-root user for security
- Temporary directory for processing

### 7. Build System Updates

Updated `Makefile` with worker-specific commands:

- `make build-worker`: Build worker binary
- `make run-worker`: Run worker locally
- `make docker-build-worker`: Build worker Docker image
- `make build-all`: Build both service and worker
- `make docker-build-all`: Build both Docker images

## Processing Pipeline Flow

```
1. Video Upload (gRPC) → Upload to S3 → Queue Job
                                           ↓
2. Worker Dequeues Job → Download from S3 → Extract Metadata
                                           ↓
3. Generate Variants (1080p, 720p, 480p, 360p) → Upload to S3
                                           ↓
4. Generate HLS Manifest & Segments → Upload to S3
                                           ↓
5. Generate Thumbnails (0%, 25%, 50%, 75%) → Upload to S3
                                           ↓
6. Update Database Records → Set Status to 'ready'
```

## Storage Structure

```
metlab-videos/
└── videos/
    └── {video_id}/
        ├── original/{filename}
        ├── variants/
        │   ├── 1080p.mp4
        │   ├── 720p.mp4
        │   ├── 480p.mp4
        │   └── 360p.mp4
        ├── hls/
        │   ├── playlist.m3u8
        │   └── segment_*.ts
        └── thumbnails/
            ├── thumb_0.jpg
            ├── thumb_25.jpg
            ├── thumb_50.jpg
            └── thumb_75.jpg
```

## Key Features

### Intelligent Variant Generation

- Skips generating variants higher than original resolution
- Prevents upscaling which would waste storage and bandwidth
- Logs skipped variants for transparency

### Error Resilience

- Individual variant/thumbnail failures don't fail entire job
- Errors logged but processing continues
- Video marked 'ready' if core processing succeeds

### Resource Efficiency

- Streams files to/from S3 without loading into memory
- Uses temporary local storage for processing
- Cleans up temporary files after processing
- Configurable temp directory location

### Scalability

- Multiple worker instances can run concurrently
- Each worker processes jobs independently
- Redis queue ensures no duplicate processing
- Horizontal scaling by adding more replicas

### Monitoring & Observability

- Structured logging for all operations
- Logs include video_id, job_id, and operation details
- Processing time and file sizes logged
- Error details captured for troubleshooting

## Configuration

### Environment Variables

- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`: Database connection
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`: Redis connection
- `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`: S3 storage connection
- `VIDEO_BUCKET`: S3 bucket name for videos
- `TEMP_DIR`: Local directory for temporary processing files

### Resource Requirements

- **Memory**: 1-4 Gi (depends on video size and concurrent processing)
- **CPU**: 1-2 cores (FFmpeg is CPU-intensive)
- **Storage**: 10 Gi temporary storage per worker
- **Network**: High bandwidth for S3 uploads/downloads

## Testing

### Manual Testing

1. Upload a video via gRPC API
2. Check video status is 'processing'
3. Monitor worker logs for processing progress
4. Verify variants, thumbnails, and HLS files in S3
5. Check video status changes to 'ready'
6. Verify database records for variants and thumbnails

### Load Testing

1. Upload multiple videos simultaneously
2. Monitor queue size in Redis
3. Check worker CPU/memory usage
4. Verify all videos process successfully
5. Measure average processing time

## Requirements Satisfied

✅ **Requirement 4.2**: Video processing with storage and streaming-optimized versions
- Generates multiple resolution variants
- Creates HLS manifest for adaptive streaming
- Uploads all processed files to S3

✅ **Requirement 4.3**: Video thumbnails and metadata
- Generates 4 thumbnails at different timestamps
- Extracts and stores video metadata (duration, resolution, codec)
- Creates database records for all variants and thumbnails

## Files Created/Modified

### Created Files

1. `cloud-native/services/video/internal/worker/processor.go` - Video processing worker
2. `cloud-native/services/video/cmd/worker/main.go` - Worker entry point
3. `cloud-native/services/video/Dockerfile.worker` - Worker Docker image
4. `cloud-native/infrastructure/k8s/video-worker-deployment.yaml` - K8s deployment
5. `cloud-native/services/video/VIDEO_PROCESSING_PIPELINE.md` - Documentation
6. `cloud-native/services/video/TASK_25_IMPLEMENTATION.md` - This file

### Modified Files

1. `cloud-native/shared/storage/s3.go` - Added GetObject method
2. `cloud-native/services/video/internal/service/video_service.go` - Updated job enqueuing
3. `cloud-native/services/video/Makefile` - Added worker build commands

## Next Steps

1. Deploy worker to Kubernetes cluster
2. Test with real video uploads
3. Monitor queue size and processing times
4. Tune worker resources based on load
5. Implement retry logic for failed jobs
6. Add metrics endpoint for monitoring
7. Consider GPU acceleration for faster processing

## Notes

- FFmpeg must be installed in worker container
- Temporary directory must have sufficient space for video processing
- S3 credentials must have read/write permissions
- Redis must be accessible from worker pods
- Database must be accessible from worker pods
