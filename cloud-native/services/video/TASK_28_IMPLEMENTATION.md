# Task 28: Video Streaming URL Generation Implementation

## Overview

This document describes the implementation of Task 28: "Implement video streaming URL generation" from the cloud-native architecture migration plan.

## Requirements

Based on the requirements document (10.2, 10.3):
- Generate signed S3 URLs for HLS manifest
- Set URL expiration to 1 hour
- Support adaptive bitrate selection
- Enable video streaming with adaptive bitrate based on connection speed

## Implementation Details

### Enhanced GetStreamingURL Method

The `GetStreamingURL` gRPC handler has been enhanced with the following capabilities:

#### 1. Video Validation
- Validates that `video_id` is provided
- Retrieves video from database
- Verifies video status is "ready" before generating streaming URLs
- Returns appropriate error codes for invalid states

#### 2. Signed URL Generation
- Generates presigned S3 URLs with exactly 1 hour expiration (as per requirements)
- Uses the shared storage client's `GeneratePresignedURL` method
- Returns both the URL and expiration timestamp in Unix format

#### 3. Adaptive Bitrate Support

The implementation supports two streaming modes:

**Mode 1: Adaptive Bitrate (Default)**
- When no specific resolution is requested
- Generates URL for the master HLS playlist (`master.m3u8`)
- Master playlist contains references to all available resolution variants
- Client video player automatically selects optimal resolution based on:
  - Network bandwidth
  - Device capabilities
  - Buffer status
- Falls back to single playlist if master playlist doesn't exist

**Mode 2: Specific Resolution**
- When `resolution` parameter is provided (e.g., "1080p", "720p", "480p", "360p")
- Validates that the requested resolution exists in the database
- Generates URL for resolution-specific HLS playlist
- Returns error if requested resolution is not available
- Useful for:
  - Manual quality selection by users
  - Bandwidth-constrained scenarios
  - Testing specific resolutions

#### 4. HLS Manifest Structure

The implementation assumes the following storage structure:

```
videos/{video_id}/
├── original/
│   └── {filename}
├── hls/
│   ├── master.m3u8          # Master playlist (adaptive bitrate)
│   ├── playlist.m3u8        # Default/fallback playlist
│   ├── 1080p/
│   │   ├── playlist.m3u8    # 1080p variant playlist
│   │   └── segment*.ts      # 1080p video segments
│   ├── 720p/
│   │   ├── playlist.m3u8
│   │   └── segment*.ts
│   ├── 480p/
│   │   ├── playlist.m3u8
│   │   └── segment*.ts
│   └── 360p/
│       ├── playlist.m3u8
│       └── segment*.ts
└── thumbnails/
    └── ...
```

#### 5. Error Handling

Comprehensive error handling with appropriate gRPC status codes:
- `INVALID_ARGUMENT`: Missing video_id or invalid resolution
- `NOT_FOUND`: Video doesn't exist
- `FAILED_PRECONDITION`: Video not ready for streaming
- `INTERNAL`: Storage or database errors

### Interface Updates

Updated the `StorageClient` interface to include the `Exists` method:

```go
type StorageClient interface {
    Upload(ctx context.Context, bucket, key string, data io.Reader, opts *storage.UploadOptions) (string, error)
    GeneratePresignedURL(bucket, key string, expiration time.Duration) (string, error)
    Delete(ctx context.Context, bucket, key string) error
    Exists(ctx context.Context, bucket, key string) (bool, error)
}
```

This allows checking if the master playlist exists before attempting to generate URLs.

## API Usage Examples

### Example 1: Adaptive Bitrate Streaming (Recommended)

```go
// Request streaming URL without specifying resolution
req := &pb.GetStreamingURLRequest{
    VideoId: "video-uuid-123",
    UserId:  "student-uuid-456",
}

resp, err := videoService.GetStreamingURL(ctx, req)
// Returns URL to master.m3u8 with all resolution variants
// Player automatically adapts based on network conditions
```

### Example 2: Specific Resolution

```go
// Request specific resolution
req := &pb.GetStreamingURLRequest{
    VideoId:    "video-uuid-123",
    UserId:     "student-uuid-456",
    Resolution: "720p",
}

resp, err := videoService.GetStreamingURL(ctx, req)
// Returns URL to 720p/playlist.m3u8
// Player streams only 720p variant
```

### Example 3: Response Structure

```protobuf
message StreamingURLResponse {
  string url = 1;           // Presigned S3 URL (valid for 1 hour)
  int64 expires_at = 2;     // Unix timestamp when URL expires
  string manifest_url = 3;  // Same as url (for clarity)
}
```

## Security Considerations

1. **URL Expiration**: All URLs expire after exactly 1 hour to prevent unauthorized long-term access
2. **Signed URLs**: Uses AWS S3 presigned URLs with cryptographic signatures
3. **Video Status Check**: Only generates URLs for videos with "ready" status
4. **User Context**: Accepts user_id for potential future authorization checks

## Performance Considerations

1. **Database Queries**: Single query to fetch video metadata
2. **Variant Lookup**: Only queries variants when specific resolution is requested
3. **Storage Check**: Minimal overhead for checking master playlist existence
4. **URL Generation**: Fast cryptographic signing operation (< 1ms)

## Integration with Video Processing Pipeline

This implementation works seamlessly with the video processing pipeline (Task 25):
1. Video processing creates multiple resolution variants
2. FFmpeg generates HLS playlists for each variant
3. Master playlist references all variants
4. GetStreamingURL provides access to the appropriate playlist
5. Client player handles adaptive streaming

## Testing Recommendations

1. **Unit Tests**:
   - Test with valid video ID
   - Test with non-existent video ID
   - Test with video in "processing" status
   - Test with specific resolution request
   - Test with invalid resolution request
   - Test URL expiration timestamp calculation

2. **Integration Tests**:
   - Test with actual S3/MinIO storage
   - Verify presigned URLs are valid
   - Test URL expiration behavior
   - Test with real HLS playlists

3. **End-to-End Tests**:
   - Upload video → process → generate URL → stream in player
   - Test adaptive bitrate switching in player
   - Test manual resolution selection

## Compliance with Requirements

✅ **Requirement 10.2**: "WHEN a student selects a video, THE VideoService SHALL stream the video with adaptive bitrate based on connection speed"
- Implemented via master playlist with multiple resolution variants
- Client player automatically selects optimal bitrate

✅ **Requirement 10.3**: "THE VideoService SHALL support playback controls including play, pause, seek, and playback speed adjustment"
- HLS format inherently supports all standard playback controls
- Presigned URLs enable full HLS functionality

✅ **Task Requirements**:
- ✅ Implement GetStreamingURL gRPC handler
- ✅ Generate signed S3 URLs for HLS manifest
- ✅ Set URL expiration to 1 hour
- ✅ Support adaptive bitrate selection

## Future Enhancements

1. **Authorization**: Add permission checks based on user_id and class enrollment
2. **Analytics**: Track which resolutions are most commonly used
3. **CDN Integration**: Add Cloudflare CDN URLs for better performance
4. **DRM Support**: Add digital rights management for protected content
5. **Bandwidth Detection**: Server-side bandwidth estimation for initial quality selection
6. **Subtitle Support**: Add support for subtitle/caption tracks in HLS

## Conclusion

The video streaming URL generation feature is now fully implemented with support for adaptive bitrate streaming, signed URLs with 1-hour expiration, and flexible resolution selection. The implementation follows best practices for HLS streaming and integrates seamlessly with the existing video processing pipeline.
