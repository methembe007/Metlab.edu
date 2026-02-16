# Video Processing Pipeline

This document describes the video processing pipeline implementation for the Metlab video service.

## Overview

The video processing pipeline is a background worker system that processes uploaded videos to generate multiple resolution variants, HLS manifests for adaptive streaming, and thumbnails.

## Architecture

```
┌─────────────────┐
│  Video Upload   │
│   (gRPC API)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Upload to S3   │
│  (Original)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Queue Job      │
│  (Redis)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Video Worker   │
│  (Background)   │
└────────┬────────┘
         │
         ├─────────────────────┐
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│  Extract        │   │  Generate       │
│  Metadata       │   │  Thumbnails     │
└────────┬────────┘   └────────┬────────┘
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│  Transcode      │   │  Upload to S3   │
│  Variants       │   │                 │
│  (1080p, 720p,  │   └─────────────────┘
│   480p, 360p)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Generate HLS   │
│  Manifest       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Upload to S3   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Update Status  │
│  to 'ready'     │
└─────────────────┘
```

## Components

### 1. Video Service (gRPC API)

The video service handles video uploads and queues processing jobs:

- Receives video upload via streaming gRPC
- Validates video format and size
- Uploads original video to S3
- Creates video record in database with status 'processing'
- Enqueues processing job to Redis queue

### 2. Video Worker (Background Processor)

The video worker is a separate process that:

- Polls Redis queue for processing jobs
- Downloads original video from S3
- Extracts metadata (duration, resolution, codec)
- Generates multiple resolution variants
- Creates HLS manifest for adaptive streaming
- Generates thumbnails at 0%, 25%, 50%, 75%
- Uploads all processed files to S3
- Updates video status to 'ready'

### 3. FFmpeg Processor

The FFmpeg processor provides video processing capabilities:

- **GetMetadata**: Extracts video metadata using ffprobe
- **Transcode**: Converts video to different resolutions and bitrates
- **GenerateThumbnail**: Creates thumbnail images at specific timestamps
- **GenerateHLSManifest**: Creates HLS playlist and segments
- **ValidateVideoFile**: Checks if file is a valid video

## Processing Steps

### Step 1: Extract Metadata

```go
metadata, err := ffmpeg.GetMetadata(ctx, videoPath)
// Returns: duration, width, height, bitrate, codec, format
```

### Step 2: Generate Resolution Variants

The worker generates up to 4 resolution variants:

| Resolution | Target Size | Bitrate | Notes |
|-----------|-------------|---------|-------|
| 1080p | 1920x1080 | 5 Mbps | Only if original ≥ 1080p |
| 720p | 1280x720 | 2.5 Mbps | Only if original ≥ 720p |
| 480p | 854x480 | 1 Mbps | Only if original ≥ 480p |
| 360p | 640x360 | 500 Kbps | Always generated |

Each variant is:
- Transcoded using H.264 codec
- Audio encoded with AAC at 128 Kbps
- Optimized for web playback with faststart flag
- Uploaded to S3 at `videos/{video_id}/variants/{resolution}.mp4`

### Step 3: Generate HLS Manifest

HLS (HTTP Live Streaming) enables adaptive bitrate streaming:

- Creates 10-second video segments
- Generates playlist.m3u8 manifest file
- Uploads all segments and manifest to S3
- Path: `videos/{video_id}/hls/`

### Step 4: Generate Thumbnails

Four thumbnails are generated at different timestamps:

- 0% (start)
- 25% (quarter)
- 50% (middle)
- 75% (three-quarters)

Each thumbnail is:
- Scaled to 320px width (maintaining aspect ratio)
- Saved as JPEG
- Uploaded to S3 at `videos/{video_id}/thumbnails/thumb_{percent}.jpg`

## Storage Structure

```
metlab-videos/
└── videos/
    └── {video_id}/
        ├── original/
        │   └── {filename}
        ├── variants/
        │   ├── 1080p.mp4
        │   ├── 720p.mp4
        │   ├── 480p.mp4
        │   └── 360p.mp4
        ├── hls/
        │   ├── playlist.m3u8
        │   ├── segment_000.ts
        │   ├── segment_001.ts
        │   └── ...
        └── thumbnails/
            ├── thumb_0.jpg
            ├── thumb_25.jpg
            ├── thumb_50.jpg
            └── thumb_75.jpg
```

## Database Schema

### videos table

```sql
CREATE TABLE videos (
    id UUID PRIMARY KEY,
    teacher_id UUID,
    class_id UUID,
    title VARCHAR(255),
    description TEXT,
    original_filename VARCHAR(255),
    storage_path VARCHAR(500),
    duration_seconds INT,
    file_size_bytes BIGINT,
    status VARCHAR(20), -- 'uploading', 'processing', 'ready', 'failed'
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### video_variants table

```sql
CREATE TABLE video_variants (
    id UUID PRIMARY KEY,
    video_id UUID REFERENCES videos(id),
    resolution VARCHAR(20), -- '1080p', '720p', '480p', '360p'
    bitrate_kbps INT,
    storage_path VARCHAR(500),
    file_size_bytes BIGINT
);
```

### video_thumbnails table

```sql
CREATE TABLE video_thumbnails (
    id UUID PRIMARY KEY,
    video_id UUID REFERENCES videos(id),
    timestamp_percent INT, -- 0, 25, 50, 75
    storage_path VARCHAR(500)
);
```

## Queue System

The processing queue uses Redis for job management:

### Job Structure

```json
{
  "id": "video-uuid",
  "type": "process_video",
  "payload": {
    "video_id": "video-uuid",
    "path": "videos/video-uuid/original/filename.mp4"
  },
  "created_at": "2024-02-16T10:30:00Z",
  "attempts": 0
}
```

### Queue Operations

- **Enqueue**: Add job to Redis list (RPUSH)
- **Dequeue**: Remove job from Redis list with blocking (BLPOP)
- **Size**: Get queue length (LLEN)

## Deployment

### Video Worker Deployment

The worker is deployed as a separate Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: video-worker
spec:
  replicas: 2  # Scale based on processing load
  template:
    spec:
      containers:
      - name: video-worker
        image: metlab/video-worker:latest
        resources:
          requests:
            memory: "1Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

### Scaling Considerations

- **Horizontal Scaling**: Add more worker replicas for higher throughput
- **Vertical Scaling**: Increase CPU/memory for faster processing
- **Queue Monitoring**: Monitor queue size to detect backlogs
- **Resource Limits**: FFmpeg is CPU-intensive, allocate accordingly

## Error Handling

### Upload Failures

- Video status set to 'failed'
- Original file remains in S3
- Error logged for investigation

### Processing Failures

- Individual variant/thumbnail failures don't fail entire job
- Errors logged but processing continues
- Video marked 'ready' if at least one variant succeeds

### Retry Logic

Currently, failed jobs are not automatically retried. Future enhancements:

- Add retry count to job payload
- Re-queue failed jobs with exponential backoff
- Dead letter queue for permanently failed jobs

## Monitoring

### Metrics to Track

- Queue size (jobs pending)
- Processing time per video
- Success/failure rate
- Storage usage
- Worker CPU/memory usage

### Logging

All operations are logged with structured logging:

```go
log.Info("processing video", map[string]interface{}{
    "video_id": videoID,
    "job_id": job.ID,
})
```

## Performance Optimization

### Current Optimizations

1. **Parallel Processing**: Multiple workers process videos concurrently
2. **Conditional Variants**: Skip variants if original resolution is lower
3. **Streaming Upload**: Stream files to S3 without loading into memory
4. **Temporary Storage**: Use local disk for processing, clean up after

### Future Optimizations

1. **GPU Acceleration**: Use hardware encoding for faster transcoding
2. **Distributed Processing**: Split variant generation across workers
3. **Caching**: Cache frequently accessed metadata
4. **Compression**: Use more efficient codecs (H.265, AV1)

## Testing

### Unit Tests

Test individual components:

```bash
go test ./internal/ffmpeg
go test ./internal/worker
```

### Integration Tests

Test end-to-end processing:

1. Upload test video
2. Wait for processing to complete
3. Verify all variants and thumbnails exist
4. Verify video status is 'ready'

### Load Tests

Test system under load:

- Upload multiple videos simultaneously
- Monitor queue size and processing time
- Verify no jobs are lost or stuck

## Troubleshooting

### Video Stuck in 'processing' Status

1. Check worker logs for errors
2. Verify Redis queue has the job
3. Check worker is running and healthy
4. Verify S3 connectivity

### FFmpeg Errors

1. Check video format is supported
2. Verify FFmpeg is installed in worker container
3. Check temp directory has sufficient space
4. Review FFmpeg command output in logs

### High Queue Backlog

1. Scale up worker replicas
2. Increase worker resources (CPU/memory)
3. Check for slow S3 uploads
4. Verify database connectivity

## Requirements Satisfied

This implementation satisfies the following requirements:

- **4.2**: Video processing with multiple resolutions
- **4.3**: Thumbnail generation and HLS manifest creation

## Related Documentation

- [Video Service README](./README.md)
- [FFmpeg Processor](./internal/ffmpeg/processor.go)
- [Video Worker](./internal/worker/processor.go)
- [Shared Queue Package](../../shared/queue/README.md)
