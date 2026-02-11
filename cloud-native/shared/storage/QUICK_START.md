# Storage Package Quick Start

Get started with the S3-compatible storage client in 5 minutes.

## 1. Deploy MinIO (Local Development)

```bash
# Apply MinIO deployment
kubectl apply -f infrastructure/k8s/minio.yaml

# Wait for MinIO to be ready
kubectl wait --for=condition=ready pod -l app=minio -n metlab-dev --timeout=120s

# Verify buckets were created
kubectl logs -n metlab-dev job/minio-setup-buckets
```

## 2. Access MinIO Console (Optional)

```bash
# Port forward to access the console
kubectl port-forward -n metlab-dev svc/minio-service 9001:9001

# Open browser to http://localhost:9001
# Login: minioadmin / minioadmin123
```

## 3. Use in Your Service

### Import the Package

```go
import (
    "context"
    "github.com/metlab/shared/storage"
)
```

### Initialize Client

```go
// Use default config (MinIO)
cfg := storage.DefaultConfig()
client, err := storage.NewClient(cfg)
if err != nil {
    log.Fatalf("Failed to create storage client: %v", err)
}
```

### Upload a File

```go
ctx := context.Background()

// Upload video
videoData := []byte("video content here")
location, err := client.UploadBytes(ctx, "videos", "my-video.mp4", videoData, &storage.UploadOptions{
    ContentType: "video/mp4",
    ACL:         "private",
})
if err != nil {
    log.Fatalf("Upload failed: %v", err)
}
fmt.Printf("Uploaded to: %s\n", location)
```

### Download a File

```go
data, err := client.Download(ctx, "videos", "my-video.mp4")
if err != nil {
    log.Fatalf("Download failed: %v", err)
}
fmt.Printf("Downloaded %d bytes\n", len(data))
```

### Generate Presigned URL

```go
import "time"

// Generate URL valid for 1 hour
url, err := client.GeneratePresignedURL("videos", "my-video.mp4", 1*time.Hour)
if err != nil {
    log.Fatalf("Failed to generate URL: %v", err)
}
fmt.Printf("Share this URL: %s\n", url)
```

## 4. Common Patterns

### Video Upload Flow

```go
func (s *VideoService) HandleUpload(ctx context.Context, videoID string, file io.Reader) error {
    // 1. Upload original
    key := fmt.Sprintf("originals/%s.mp4", videoID)
    _, err := s.storage.Upload(ctx, "videos", key, file, &storage.UploadOptions{
        ContentType: "video/mp4",
        ACL:         "private",
    })
    if err != nil {
        return fmt.Errorf("upload failed: %w", err)
    }
    
    // 2. Queue processing job
    // ... (processing logic)
    
    return nil
}
```

### PDF Download Flow

```go
func (s *PDFService) GetDownloadURL(ctx context.Context, pdfID string) (string, error) {
    // 1. Check if PDF exists
    key := fmt.Sprintf("%s.pdf", pdfID)
    exists, err := s.storage.Exists(ctx, "pdfs", key)
    if err != nil {
        return "", err
    }
    if !exists {
        return "", fmt.Errorf("PDF not found")
    }
    
    // 2. Generate presigned URL
    url, err := s.storage.GeneratePresignedURL("pdfs", key, 1*time.Hour)
    if err != nil {
        return "", err
    }
    
    return url, nil
}
```

### Thumbnail Generation Flow

```go
func (s *VideoService) SaveThumbnail(ctx context.Context, videoID string, position int, imageData []byte) error {
    key := fmt.Sprintf("%s/thumb-%d.jpg", videoID, position)
    
    _, err := s.storage.UploadBytes(ctx, "thumbnails", key, imageData, &storage.UploadOptions{
        ContentType: "image/jpeg",
        ACL:         "public-read", // Thumbnails are public
    })
    
    return err
}
```

## 5. Environment Configuration

For production, use environment variables:

```bash
export S3_ENDPOINT="https://s3.amazonaws.com"
export S3_REGION="us-west-2"
export S3_ACCESS_KEY="your-access-key"
export S3_SECRET_KEY="your-secret-key"
export S3_USE_SSL="true"
export S3_FORCE_PATH_STYLE="false"
```

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

## 6. Testing

```bash
# Run tests
cd shared/storage
go test -v

# Run with integration tests (requires MinIO)
go test -v

# Skip integration tests
go test -v -short
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out service examples in `services/video` and `services/pdf`
- Review the [design document](../../.kiro/specs/cloud-native-architecture/design.md) for architecture details

## Troubleshooting

**Problem**: Connection refused

**Solution**: Ensure MinIO is running
```bash
kubectl get pods -n metlab-dev | grep minio
```

**Problem**: Bucket not found

**Solution**: Check if buckets were created
```bash
kubectl logs -n metlab-dev job/minio-setup-buckets
```

**Problem**: Access denied

**Solution**: Verify credentials
```bash
kubectl get secret minio-secret -n metlab-dev -o jsonpath='{.data.S3_ACCESS_KEY}' | base64 -d
```
