# Storage Package

This package provides a Go client wrapper for S3-compatible object storage (AWS S3, MinIO, etc.) with helper methods for common operations.

## Features

- Upload and download files
- Generate presigned URLs for temporary access
- List, copy, and delete objects
- Bucket management
- Metadata support
- Streaming support for large files

## Configuration

### Default Configuration (MinIO)

```go
import "github.com/metlab/shared/storage"

cfg := storage.DefaultConfig()
// Uses MinIO defaults:
// - Endpoint: http://minio-service:9000
// - Region: us-east-1
// - AccessKeyID: minioadmin
// - SecretAccessKey: minioadmin123
// - UseSSL: false
// - ForcePathStyle: true
```

### Custom Configuration

```go
cfg := &storage.Config{
    Endpoint:        "https://s3.amazonaws.com",
    Region:          "us-west-2",
    AccessKeyID:     "your-access-key",
    SecretAccessKey: "your-secret-key",
    UseSSL:          true,
    ForcePathStyle:  false,
}
```

### Environment Variables

You can also configure using environment variables:

```go
import "os"

cfg := &storage.Config{
    Endpoint:        os.Getenv("S3_ENDPOINT"),
    Region:          os.Getenv("S3_REGION"),
    AccessKeyID:     os.Getenv("S3_ACCESS_KEY"),
    SecretAccessKey: os.Getenv("S3_SECRET_KEY"),
    UseSSL:          os.Getenv("S3_USE_SSL") == "true",
    ForcePathStyle:  os.Getenv("S3_FORCE_PATH_STYLE") == "true",
}
```

## Usage Examples

### Creating a Client

```go
import (
    "context"
    "github.com/metlab/shared/storage"
)

func main() {
    cfg := storage.DefaultConfig()
    client, err := storage.NewClient(cfg)
    if err != nil {
        panic(err)
    }
    
    ctx := context.Background()
    // Use client...
}
```

### Uploading Files

```go
// Upload from bytes
data := []byte("Hello, World!")
location, err := client.UploadBytes(ctx, "videos", "hello.txt", data, &storage.UploadOptions{
    ContentType: "text/plain",
    ACL:         "private",
    Metadata: map[string]string{
        "uploaded-by": "user-123",
    },
})

// Upload from reader
file, _ := os.Open("video.mp4")
defer file.Close()

location, err := client.Upload(ctx, "videos", "my-video.mp4", file, &storage.UploadOptions{
    ContentType: "video/mp4",
    ACL:         "private",
})
```

### Downloading Files

```go
// Download to memory
data, err := client.Download(ctx, "videos", "my-video.mp4")

// Download to file
file, _ := os.Create("downloaded-video.mp4")
defer file.Close()

n, err := client.DownloadToWriter(ctx, "videos", "my-video.mp4", file)
fmt.Printf("Downloaded %d bytes\n", n)
```

### Generating Presigned URLs

```go
import "time"

// Generate download URL (valid for 1 hour)
url, err := client.GeneratePresignedURL("videos", "my-video.mp4", 1*time.Hour)
// Share this URL with users for temporary access

// Generate upload URL (valid for 15 minutes)
uploadURL, err := client.GeneratePresignedUploadURL("videos", "new-video.mp4", 15*time.Minute)
// Share this URL with users to upload directly to S3
```

### Checking Object Existence

```go
exists, err := client.Exists(ctx, "videos", "my-video.mp4")
if exists {
    fmt.Println("Video exists!")
}
```

### Getting Object Metadata

```go
info, err := client.GetObjectInfo(ctx, "videos", "my-video.mp4")
fmt.Printf("Size: %d bytes\n", info.Size)
fmt.Printf("Last Modified: %s\n", info.LastModified)
fmt.Printf("Content Type: %s\n", info.ContentType)
fmt.Printf("Custom Metadata: %v\n", info.Metadata)
```

### Listing Objects

```go
// List all objects with prefix "2024/"
objects, err := client.ListObjects(ctx, "videos", "2024/")
for _, obj := range objects {
    fmt.Printf("%s - %d bytes\n", obj.Key, obj.Size)
}
```

### Deleting Objects

```go
// Delete single object
err := client.Delete(ctx, "videos", "old-video.mp4")

// Delete multiple objects
keys := []string{"video1.mp4", "video2.mp4", "video3.mp4"}
err := client.DeleteMultiple(ctx, "videos", keys)
```

### Copying Objects

```go
err := client.CopyObject(ctx, 
    "videos", "original.mp4",  // source
    "backups", "original.mp4", // destination
)
```

### Bucket Operations

```go
// Check if bucket exists
exists, err := client.BucketExists(ctx, "videos")

// Create bucket
err := client.CreateBucket(ctx, "new-bucket")
```

## Buckets in Metlab System

The system uses three main buckets:

1. **videos** - Stores video files and processed variants
   - Original uploads
   - Transcoded versions (1080p, 720p, 480p, 360p)
   - HLS manifests

2. **pdfs** - Stores PDF documents
   - Course materials
   - Homework assignments

3. **thumbnails** - Stores video thumbnails
   - Generated at 0%, 25%, 50%, 75% timestamps
   - Public read access for easy display

## Integration with Services

### Video Service Example

```go
import (
    "github.com/metlab/shared/storage"
    "io"
)

type VideoService struct {
    storage *storage.Client
}

func (s *VideoService) UploadVideo(ctx context.Context, videoID string, reader io.Reader) error {
    key := fmt.Sprintf("originals/%s.mp4", videoID)
    
    _, err := s.storage.Upload(ctx, "videos", key, reader, &storage.UploadOptions{
        ContentType: "video/mp4",
        ACL:         "private",
        Metadata: map[string]string{
            "video-id": videoID,
            "status":   "uploaded",
        },
    })
    
    return err
}

func (s *VideoService) GetStreamingURL(ctx context.Context, videoID string) (string, error) {
    key := fmt.Sprintf("processed/%s/playlist.m3u8", videoID)
    return s.storage.GeneratePresignedURL("videos", key, 1*time.Hour)
}
```

### PDF Service Example

```go
func (s *PDFService) UploadPDF(ctx context.Context, pdfID string, reader io.Reader) error {
    key := fmt.Sprintf("%s.pdf", pdfID)
    
    _, err := s.storage.Upload(ctx, "pdfs", key, reader, &storage.UploadOptions{
        ContentType: "application/pdf",
        ACL:         "private",
    })
    
    return err
}

func (s *PDFService) GetDownloadURL(ctx context.Context, pdfID string) (string, error) {
    key := fmt.Sprintf("%s.pdf", pdfID)
    return s.storage.GeneratePresignedURL("pdfs", key, 1*time.Hour)
}
```

## Testing

Run unit tests:
```bash
go test ./storage
```

Run integration tests (requires MinIO running):
```bash
go test ./storage -v
```

Skip integration tests:
```bash
go test ./storage -short
```

## Error Handling

The client returns descriptive errors for common scenarios:

```go
data, err := client.Download(ctx, "videos", "nonexistent.mp4")
if err != nil {
    // Check for specific error types
    if storage.IsNotFoundError(err) {
        fmt.Println("Object not found")
    } else {
        fmt.Printf("Download error: %v\n", err)
    }
}
```

## Performance Considerations

- Use streaming for large files to avoid loading entire files into memory
- Use presigned URLs for direct client-to-S3 uploads/downloads to reduce server load
- Use `DeleteMultiple` for batch deletions (more efficient than individual deletes)
- Consider using multipart uploads for files larger than 100MB (handled automatically by the uploader)

## Security Best Practices

1. Never expose access keys in code - use environment variables or secrets management
2. Use private ACL for sensitive content
3. Set appropriate expiration times for presigned URLs
4. Implement proper authentication before generating presigned URLs
5. Use HTTPS in production (set `UseSSL: true`)
6. Regularly rotate access keys

## MinIO Setup

The MinIO deployment is configured in `infrastructure/k8s/minio.yaml` and includes:

- Persistent storage (10Gi)
- Health checks
- Automatic bucket creation (videos, pdfs, thumbnails)
- Console UI on port 9001

Access MinIO console:
```bash
kubectl port-forward -n metlab-dev svc/minio-service 9001:9001
# Open http://localhost:9001
# Login: minioadmin / minioadmin123
```

## Troubleshooting

### Connection Refused

Ensure MinIO is running:
```bash
kubectl get pods -n metlab-dev | grep minio
```

### Access Denied

Check credentials in the secret:
```bash
kubectl get secret minio-secret -n metlab-dev -o yaml
```

### Bucket Not Found

Verify buckets were created:
```bash
kubectl logs -n metlab-dev job/minio-setup-buckets
```
