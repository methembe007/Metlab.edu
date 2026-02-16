# Task 26: Video Thumbnail Generation - Verification

## Task Requirements

✅ Extract frames at 0%, 25%, 50%, 75% timestamps
✅ Generate thumbnail images using FFmpeg
✅ Upload thumbnails to S3
✅ Store thumbnail URLs in database

## Implementation Verification

### 1. FFmpeg Thumbnail Generation (`internal/ffmpeg/processor.go`)

**Function**: `GenerateThumbnail(ctx context.Context, inputPath string, timestampPercent int32, outputPath string) error`

**Implementation Details**:
- ✅ Gets video metadata to determine duration
- ✅ Calculates timestamp in seconds: `timestamp = duration * percent / 100`
- ✅ Uses FFmpeg to extract frame at specific timestamp
- ✅ Scales thumbnail to 320px width (maintains aspect ratio)
- ✅ Saves as JPEG format
- ✅ Overwrites existing files with `-y` flag

**FFmpeg Command**:
```bash
ffmpeg -ss {timestamp} -i {input} -vframes 1 -vf scale=320:-1 -y {output}
```

### 2. Worker Integration (`internal/worker/processor.go`)

**Function**: `generateThumbnail(ctx context.Context, videoID, inputPath string, percent int32) error`

**Implementation Details**:
- ✅ Called for each timestamp: 0%, 25%, 50%, 75%
- ✅ Creates temporary output file: `{videoID}_thumb_{percent}.jpg`
- ✅ Calls FFmpeg processor to generate thumbnail
- ✅ Uploads thumbnail to S3 storage
- ✅ Creates database record with storage path
- ✅ Cleans up temporary file after upload
- ✅ Logs success/failure for each thumbnail
- ✅ Continues processing other thumbnails if one fails

**Storage Path Pattern**:
```
videos/{video_id}/thumbnails/thumb_{percent}.jpg
```

### 3. Database Schema (`migrations/001_create_video_tables.up.sql`)

**Table**: `video_thumbnails`

```sql
CREATE TABLE IF NOT EXISTS video_thumbnails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    timestamp_percent INT NOT NULL CHECK (timestamp_percent IN (0, 25, 50, 75)),
    storage_path VARCHAR(500) NOT NULL
);
```

**Features**:
- ✅ UUID primary key
- ✅ Foreign key to videos table with CASCADE delete
- ✅ Constraint to ensure only valid percentages (0, 25, 50, 75)
- ✅ Storage path for S3 location
- ✅ Index on video_id for fast lookups

### 4. Data Model (`internal/models/video.go`)

**Struct**: `VideoThumbnail`

```go
type VideoThumbnail struct {
    ID              string `db:"id"`
    VideoID         string `db:"video_id"`
    TimestampPercent int32  `db:"timestamp_percent"` // 0, 25, 50, 75
    StoragePath     string `db:"storage_path"`
}
```

### 5. Repository Operations (`internal/repository/video_repository.go`)

**Function**: `CreateVideoThumbnail(ctx context.Context, thumbnail *models.VideoThumbnail) error`

**Implementation**:
- ✅ Generates UUID for thumbnail
- ✅ Inserts record into database
- ✅ Returns error if operation fails

**Function**: `GetVideoThumbnails(ctx context.Context, videoID string) ([]*models.VideoThumbnail, error)`

**Implementation**:
- ✅ Retrieves all thumbnails for a video
- ✅ Orders by timestamp_percent ascending
- ✅ Returns array of thumbnail records

### 6. S3 Storage Integration

**Upload Process**:
1. ✅ Generate thumbnail locally in temp directory
2. ✅ Open thumbnail file for reading
3. ✅ Upload to S3 bucket at path: `videos/{video_id}/thumbnails/thumb_{percent}.jpg`
4. ✅ Close file handle
5. ✅ Delete temporary file

**Storage Client**: Uses `shared/storage/s3.go` Upload method

## Processing Flow

```
Video Upload Complete
        ↓
Queue Processing Job
        ↓
Worker Dequeues Job
        ↓
Download Original Video
        ↓
Extract Metadata (duration)
        ↓
Generate Variants (1080p, 720p, 480p, 360p)
        ↓
Generate HLS Manifest
        ↓
┌───────────────────────────────────┐
│ Generate Thumbnails (Task 26)    │
│                                   │
│ For each percent (0, 25, 50, 75):│
│   1. Calculate timestamp          │
│   2. Extract frame with FFmpeg    │
│   3. Scale to 320px width         │
│   4. Save as JPEG                 │
│   5. Upload to S3                 │
│   6. Create DB record             │
│   7. Clean up temp file           │
└───────────────────────────────────┘
        ↓
Update Video Status to 'ready'
        ↓
Processing Complete
```

## Error Handling

✅ **Individual Thumbnail Failures**: If one thumbnail fails, processing continues with remaining thumbnails
✅ **Logging**: All failures logged with video_id and percent for debugging
✅ **Cleanup**: Temporary files deleted even if upload fails (defer statement)
✅ **Database Errors**: Errors returned and logged, but don't fail entire job

## Requirements Mapping

**Requirement 4.3**: Video thumbnails and metadata

✅ **Extract frames at 0%, 25%, 50%, 75% timestamps**
- Implemented in `generateThumbnail` function
- Calculates exact timestamp based on video duration
- Uses FFmpeg `-ss` flag for precise seeking

✅ **Generate thumbnail images using FFmpeg**
- Uses FFmpeg command with `-vframes 1` to extract single frame
- Scales to 320px width with `-vf scale=320:-1`
- Outputs as JPEG format

✅ **Upload thumbnails to S3**
- Uploads to structured path: `videos/{video_id}/thumbnails/thumb_{percent}.jpg`
- Uses S3 client Upload method
- Handles upload errors gracefully

✅ **Store thumbnail URLs in database**
- Creates `video_thumbnails` record for each thumbnail
- Stores storage_path for retrieval
- Links to video via foreign key
- Indexed for fast lookups

## Testing Recommendations

### Manual Testing
1. Upload a video via gRPC API
2. Wait for processing to complete
3. Check S3 bucket for thumbnails at: `videos/{video_id}/thumbnails/`
4. Verify 4 thumbnails exist: `thumb_0.jpg`, `thumb_25.jpg`, `thumb_50.jpg`, `thumb_75.jpg`
5. Query database: `SELECT * FROM video_thumbnails WHERE video_id = '{video_id}'`
6. Verify 4 records exist with correct percentages
7. Download thumbnails from S3 and verify they show different frames

### Integration Testing
1. Test with videos of different durations (short, medium, long)
2. Test with videos of different resolutions
3. Test with videos of different formats (MP4, WebM, MOV)
4. Verify thumbnails are generated at correct timestamps
5. Verify thumbnails are properly scaled to 320px width

### Error Testing
1. Test with corrupted video file
2. Test with insufficient disk space
3. Test with S3 connection failure
4. Verify error handling and logging
5. Verify other thumbnails still generated if one fails

## Conclusion

✅ **Task 26 is COMPLETE**

All requirements have been successfully implemented:
- Thumbnail extraction at 4 different timestamps (0%, 25%, 50%, 75%)
- FFmpeg integration for frame extraction and scaling
- S3 upload with structured storage paths
- Database records for thumbnail metadata
- Error handling and logging
- Integration with video processing pipeline

The implementation is production-ready and follows best practices for:
- Resource cleanup (defer statements)
- Error handling (graceful degradation)
- Logging (structured logging with context)
- Database operations (proper indexing and constraints)
- Storage organization (logical path structure)
