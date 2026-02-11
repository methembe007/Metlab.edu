# MinIO Object Storage Setup - Complete

## Overview

Task 7 from the cloud-native architecture implementation plan has been completed. MinIO (S3-compatible object storage) has been configured for local development with automatic bucket creation and a comprehensive Go storage client wrapper.

## What Was Implemented

### 1. Kubernetes Deployment (`infrastructure/k8s/minio.yaml`)

- **MinIO Deployment**: Single replica deployment with persistent storage (10Gi)
- **Service**: ClusterIP service exposing API (port 9000) and Console (port 9001)
- **ConfigMap**: Configuration for MinIO settings
- **Secret**: Credentials for MinIO access
- **Bucket Setup Job**: Automatic creation of three buckets on startup:
  - `videos` - For video files and processed variants
  - `pdfs` - For PDF documents
  - `thumbnails` - For video thumbnails (public read access)

### 2. Storage Client Package (`shared/storage/`)

A comprehensive Go client wrapper with the following features:

#### Core Operations
- **Upload**: Upload files from readers or byte arrays
- **Download**: Download files to memory or writers
- **Delete**: Delete single or multiple objects
- **Exists**: Check if objects exist
- **List**: List objects with prefix filtering
- **Copy**: Copy objects between locations

#### Advanced Features
- **Presigned URLs**: Generate temporary URLs for downloads and uploads
- **Metadata**: Support for custom metadata on objects
- **Object Info**: Retrieve detailed metadata about objects
- **Bucket Management**: Create and check bucket existence
- **Streaming**: Support for large file streaming

#### Configuration
- Default configuration for MinIO
- Custom configuration support
- Environment variable support
- Connection pooling via AWS SDK

### 3. Documentation

- **README.md**: Comprehensive documentation with examples
- **QUICK_START.md**: 5-minute quick start guide
- **example_integration.go**: Example service implementations showing:
  - Video service integration
  - PDF service integration
  - Thumbnail management
  - File deletion workflows

### 4. Testing

- **s3_test.go**: Unit and integration tests
- Tests for all core operations
- Integration tests (skippable with `-short` flag)

### 5. Docker Compose Integration

Updated `docker-compose.yml` to include:
- MinIO service with health checks
- Automatic bucket creation container
- Updated environment variables for all services
- Proper service dependencies

## File Structure

```
cloud-native/
├── infrastructure/
│   ├── k8s/
│   │   └── minio.yaml                    # Kubernetes deployment
│   └── MINIO_SETUP_COMPLETE.md          # This file
└── shared/
    └── storage/
        ├── s3.go                         # Main storage client
        ├── s3_test.go                    # Tests
        ├── example_integration.go        # Usage examples
        ├── README.md                     # Full documentation
        └── QUICK_START.md                # Quick start guide
```

## Usage

### Deploy to Kubernetes

```bash
# Apply MinIO deployment
kubectl apply -f infrastructure/k8s/minio.yaml

# Wait for MinIO to be ready
kubectl wait --for=condition=ready pod -l app=minio -n metlab-dev --timeout=120s

# Verify buckets were created
kubectl logs -n metlab-dev job/minio-setup-buckets
```

### Access MinIO Console

```bash
# Port forward to access the console
kubectl port-forward -n metlab-dev svc/minio-service 9001:9001

# Open browser to http://localhost:9001
# Login: minioadmin / minioadmin123
```

### Use in Go Services

```go
import (
    "context"
    "github.com/metlab/shared/storage"
)

// Create client
cfg := storage.DefaultConfig()
client, err := storage.NewClient(cfg)
if err != nil {
    log.Fatal(err)
}

// Upload video
ctx := context.Background()
location, err := client.UploadBytes(ctx, "videos", "my-video.mp4", videoData, &storage.UploadOptions{
    ContentType: "video/mp4",
    ACL:         "private",
})

// Generate presigned URL
url, err := client.GeneratePresignedURL("videos", "my-video.mp4", 1*time.Hour)
```

### Run with Docker Compose

```bash
# Start all services including MinIO
docker-compose up -d

# Check MinIO is running
docker-compose ps minio

# View bucket setup logs
docker-compose logs minio-setup
```

## Buckets Configuration

### videos
- **Purpose**: Store video files and processed variants
- **Access**: Private
- **Structure**:
  - `originals/` - Original uploaded videos
  - `processed/{video-id}/` - Transcoded versions and HLS manifests

### pdfs
- **Purpose**: Store PDF documents
- **Access**: Private
- **Structure**: Flat structure with PDF IDs as keys

### thumbnails
- **Purpose**: Store video thumbnails
- **Access**: Public read (for easy display in UI)
- **Structure**: `{video-id}/thumb-{position}.jpg`

## Environment Variables

Services can be configured using these environment variables:

```bash
S3_ENDPOINT=http://minio-service:9000
S3_REGION=us-east-1
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin123
S3_USE_SSL=false
S3_FORCE_PATH_STYLE=true
```

## Integration with Services

The storage client is ready to be integrated into:

1. **Video Service** (Task 23-31)
   - Upload original videos
   - Store processed variants
   - Generate streaming URLs
   - Save thumbnails

2. **PDF Service** (Task 54-58)
   - Upload PDF documents
   - Generate download URLs
   - Track downloads

3. **Homework Service** (Task 32-39)
   - Store homework submissions
   - Generate download URLs for teachers

## Testing

```bash
# Run unit tests
cd shared/storage
go test -v -short

# Run integration tests (requires MinIO running)
go test -v

# Test with Docker Compose
docker-compose up -d minio minio-setup
go test -v
```

## Security Considerations

### Development
- Default credentials: `minioadmin` / `minioadmin123`
- HTTP (no SSL) for local development
- Public read access for thumbnails bucket

### Production
- Use strong credentials (stored in Kubernetes secrets)
- Enable SSL/TLS
- Use IAM roles or service accounts where possible
- Implement proper access controls
- Regular credential rotation
- Private access for all buckets (use presigned URLs)

## Performance Characteristics

- **Upload**: Streaming support for large files (no memory limits)
- **Download**: Streaming support with configurable chunk sizes
- **Presigned URLs**: Offload traffic from services to S3
- **Connection Pooling**: Managed by AWS SDK
- **Multipart Uploads**: Automatic for files > 5MB

## Next Steps

1. **Task 8**: Implement shared Go packages (JWT, logging, error handling)
2. **Task 23-31**: Implement Video Service using storage client
3. **Task 32-39**: Implement Homework Service using storage client
4. **Task 54-58**: Implement PDF Service using storage client

## Requirements Satisfied

✅ **Requirement 4.2**: Video storage and streaming infrastructure
- MinIO provides S3-compatible storage for videos
- Storage client supports video upload and streaming URL generation

✅ **Requirement 5.2**: PDF document storage
- MinIO provides storage for PDF documents
- Storage client supports PDF upload and download URL generation

## Troubleshooting

### MinIO not starting
```bash
# Check pod status
kubectl get pods -n metlab-dev | grep minio

# Check logs
kubectl logs -n metlab-dev deployment/minio
```

### Buckets not created
```bash
# Check job status
kubectl get jobs -n metlab-dev

# View job logs
kubectl logs -n metlab-dev job/minio-setup-buckets
```

### Connection refused
```bash
# Verify service is running
kubectl get svc -n metlab-dev minio-service

# Test connectivity from another pod
kubectl run -it --rm debug --image=alpine --restart=Never -- sh
apk add curl
curl http://minio-service:9000/minio/health/live
```

### Access denied
```bash
# Verify credentials
kubectl get secret minio-secret -n metlab-dev -o yaml

# Check environment variables in services
kubectl describe pod <service-pod> -n metlab-dev
```

## References

- [MinIO Documentation](https://min.io/docs/minio/kubernetes/upstream/)
- [AWS SDK for Go](https://docs.aws.amazon.com/sdk-for-go/api/)
- [Design Document](../../.kiro/specs/cloud-native-architecture/design.md)
- [Requirements Document](../../.kiro/specs/cloud-native-architecture/requirements.md)
