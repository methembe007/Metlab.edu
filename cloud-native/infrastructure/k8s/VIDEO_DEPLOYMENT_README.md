# Video Service Kubernetes Deployment

## Overview

This document describes the Kubernetes deployment configuration for the Video Service and Video Worker components of the Metlab.edu platform. The Video Service handles video uploads, streaming, and view tracking, while the Video Worker processes videos using FFmpeg to create multiple resolutions and thumbnails.

## Architecture

The Video Service deployment consists of two main components:

1. **Video Service** (`video.yaml`): gRPC service handling video uploads, streaming URLs, and view tracking
2. **Video Worker** (`video-worker-deployment.yaml`): Background worker processing videos with FFmpeg

## Components

### Video Service (video.yaml)

#### ConfigMap: video-config
Contains non-sensitive configuration:
- Port configuration (50052)
- Database connection details
- S3/MinIO endpoint and bucket names
- Redis connection details
- Upload limits and supported formats
- Processing queue name
- Temporary directory path

#### Secret: video-secret
Contains sensitive data:
- Database password
- S3 access credentials
- Redis password

#### PersistentVolumeClaim: video-processing-pvc
- **Size**: 50Gi
- **Access Mode**: ReadWriteOnce
- **Purpose**: Temporary storage for video processing operations

#### Deployment: video
- **Replicas**: 2 (minimum)
- **Image**: metlab/video:latest
- **Port**: 50052 (gRPC)
- **Resources**:
  - Requests: 1Gi memory, 1000m CPU
  - Limits: 2Gi memory, 2000m CPU
- **Health Checks**:
  - Liveness probe: gRPC health check every 10s
  - Readiness probe: gRPC health check every 5s
- **Volume Mounts**: Persistent volume for temporary processing

#### Service: video
- **Type**: ClusterIP (internal only)
- **Port**: 50052 (gRPC)
- **Purpose**: Internal service discovery for gRPC communication

#### HorizontalPodAutoscaler: video-hpa
- **Min Replicas**: 2
- **Max Replicas**: 10
- **Metrics**:
  - CPU: 80% utilization
  - Memory: 85% utilization
- **Scale Down**: Gradual (50% per minute, stabilization 5 minutes)
- **Scale Up**: Aggressive (100% per 30s, immediate)

### Video Worker (video-worker-deployment.yaml)

#### ConfigMap: video-worker-config
Contains worker-specific configuration:
- FFmpeg processing parameters
- Video resolutions to generate (1080p, 720p, 480p, 360p)
- Thumbnail timestamps (0%, 25%, 50%, 75%)
- Processing timeout (30 minutes)
- Thread count for FFmpeg

#### Secret: video-worker-secret
Contains sensitive data (same as video-secret):
- Database password
- S3 access credentials
- Redis password

#### PersistentVolumeClaim: video-worker-processing-pvc
- **Size**: 100Gi
- **Access Mode**: ReadWriteMany
- **Purpose**: Shared temporary storage for video processing (FFmpeg needs significant space)

#### Deployment: video-worker
- **Replicas**: 2 (minimum)
- **Image**: metlab/video-worker:latest
- **Port**: 9090 (metrics)
- **Resources**:
  - Requests: 2Gi memory, 1500m CPU
  - Limits: 4Gi memory, 3000m CPU (higher for FFmpeg processing)
- **Health Checks**:
  - Liveness probe: HTTP /health endpoint every 10s
  - Readiness probe: HTTP /ready endpoint every 5s
- **Volume Mounts**: Persistent volume for temporary processing
- **Termination Grace Period**: 60s (longer to allow processing to complete)

#### Service: video-worker
- **Type**: ClusterIP
- **Port**: 9090 (metrics)
- **Purpose**: Expose metrics for Prometheus scraping

#### HorizontalPodAutoscaler: video-worker-hpa
- **Min Replicas**: 2
- **Max Replicas**: 8
- **Metrics**:
  - CPU: 75% utilization (lower threshold due to FFmpeg intensity)
  - Memory: 80% utilization
- **Scale Down**: Conservative (50% per 2 minutes, stabilization 5 minutes)
- **Scale Up**: Aggressive (100% per minute)

## Resource Requirements

### Video Service
- **FFmpeg**: Not required (delegates to worker)
- **Storage**: 50Gi persistent volume
- **Memory**: 1-2Gi per pod
- **CPU**: 1-2 cores per pod

### Video Worker
- **FFmpeg**: Required in container image
- **Storage**: 100Gi persistent volume (shared)
- **Memory**: 2-4Gi per pod (FFmpeg is memory-intensive)
- **CPU**: 1.5-3 cores per pod (FFmpeg is CPU-intensive)

## Deployment Instructions

### Prerequisites

1. Kubernetes cluster running (Minikube for dev)
2. PostgreSQL deployed and accessible
3. Redis deployed and accessible
4. MinIO or S3 deployed and accessible
5. Namespace `metlab-dev` created

### Deploy Video Service

```bash
# Apply the Video Service deployment
kubectl apply -f video.yaml

# Verify deployment
kubectl get pods -n metlab-dev -l service=video
kubectl get svc -n metlab-dev -l service=video
kubectl get hpa -n metlab-dev -l service=video

# Check logs
kubectl logs -n metlab-dev -l service=video --tail=50
```

### Deploy Video Worker

```bash
# Apply the Video Worker deployment
kubectl apply -f video-worker-deployment.yaml

# Verify deployment
kubectl get pods -n metlab-dev -l service=video-worker
kubectl get svc -n metlab-dev -l service=video-worker
kubectl get hpa -n metlab-dev -l service=video-worker

# Check logs
kubectl logs -n metlab-dev -l service=video-worker --tail=50
```

### Verify Health

```bash
# Check Video Service health
kubectl exec -n metlab-dev deployment/video -- grpc_health_probe -addr=:50052

# Check Video Worker health
kubectl exec -n metlab-dev deployment/video-worker -- curl http://localhost:9090/health
```

## Configuration

### Environment Variables

#### Video Service
- `PORT`: gRPC server port (default: 50052)
- `DATABASE_URL`: PostgreSQL connection string
- `S3_ENDPOINT`: MinIO/S3 endpoint URL
- `S3_ACCESS_KEY`: S3 access key
- `S3_SECRET_KEY`: S3 secret key
- `VIDEO_BUCKET`: S3 bucket for videos
- `THUMBNAIL_BUCKET`: S3 bucket for thumbnails
- `REDIS_HOST`: Redis host
- `REDIS_PORT`: Redis port
- `MAX_UPLOAD_SIZE_MB`: Maximum upload size (default: 2048)
- `SUPPORTED_FORMATS`: Comma-separated video formats (default: mp4,webm,mov)

#### Video Worker
- `DATABASE_URL`: PostgreSQL connection string
- `S3_ENDPOINT`: MinIO/S3 endpoint URL
- `S3_ACCESS_KEY`: S3 access key
- `S3_SECRET_KEY`: S3 secret key
- `VIDEO_BUCKET`: S3 bucket for videos
- `THUMBNAIL_BUCKET`: S3 bucket for thumbnails
- `REDIS_HOST`: Redis host
- `REDIS_PORT`: Redis port
- `PROCESSING_QUEUE`: Redis queue name (default: video-processing)
- `TEMP_DIR`: Temporary directory for processing (default: /tmp/video-processing)
- `FFMPEG_THREADS`: Number of FFmpeg threads (default: 4)
- `VIDEO_RESOLUTIONS`: Comma-separated resolutions (default: 1080p,720p,480p,360p)
- `THUMBNAIL_TIMESTAMPS`: Comma-separated percentages (default: 0,25,50,75)
- `MAX_PROCESSING_TIME_MINUTES`: Processing timeout (default: 30)

## Monitoring

### Metrics

Both services expose Prometheus metrics:

- **Video Service**: Scraped via gRPC port 50052
- **Video Worker**: Scraped via HTTP port 9090

Key metrics to monitor:
- Request rate and latency
- Video upload success/failure rate
- Processing queue length
- Processing time per video
- Storage usage
- Memory and CPU utilization

### Logs

Structured JSON logs are written to stdout:

```bash
# Video Service logs
kubectl logs -n metlab-dev -l service=video -f

# Video Worker logs
kubectl logs -n metlab-dev -l service=video-worker -f

# Filter for errors
kubectl logs -n metlab-dev -l service=video | grep ERROR
```

### Alerts

Recommended alerts:
- Video Service pods not ready
- Video Worker pods not ready
- Processing queue length > 100
- Processing failure rate > 5%
- Storage usage > 80%
- Memory usage > 90%

## Troubleshooting

### Video Service Not Starting

```bash
# Check pod status
kubectl describe pod -n metlab-dev -l service=video

# Check logs
kubectl logs -n metlab-dev -l service=video --tail=100

# Common issues:
# - Database connection failure: Check DATABASE_URL
# - S3 connection failure: Check S3_ENDPOINT and credentials
# - Redis connection failure: Check REDIS_HOST
```

### Video Worker Not Processing

```bash
# Check worker logs
kubectl logs -n metlab-dev -l service=video-worker --tail=100

# Check Redis queue
kubectl exec -n metlab-dev deployment/redis -- redis-cli LLEN video-processing

# Common issues:
# - FFmpeg not installed: Check container image
# - Insufficient disk space: Check PVC usage
# - Insufficient memory: Check resource limits
# - Processing timeout: Increase MAX_PROCESSING_TIME_MINUTES
```

### Storage Issues

```bash
# Check PVC status
kubectl get pvc -n metlab-dev

# Check storage usage
kubectl exec -n metlab-dev deployment/video -- df -h /tmp/video-processing
kubectl exec -n metlab-dev deployment/video-worker -- df -h /tmp/video-processing

# Clean up old files if needed
kubectl exec -n metlab-dev deployment/video-worker -- find /tmp/video-processing -type f -mtime +1 -delete
```

### Performance Issues

```bash
# Check HPA status
kubectl get hpa -n metlab-dev

# Check resource usage
kubectl top pods -n metlab-dev -l service=video
kubectl top pods -n metlab-dev -l service=video-worker

# Scale manually if needed
kubectl scale deployment video -n metlab-dev --replicas=5
kubectl scale deployment video-worker -n metlab-dev --replicas=4
```

## Security Considerations

1. **Secrets Management**: All sensitive data stored in Kubernetes Secrets
2. **Network Policies**: Consider adding NetworkPolicy to restrict traffic
3. **RBAC**: Ensure proper service account permissions
4. **Image Security**: Scan container images for vulnerabilities
5. **Resource Limits**: Prevent resource exhaustion attacks
6. **Input Validation**: Validate video formats and sizes before processing

## Scaling Guidelines

### When to Scale Up

- CPU utilization consistently > 80%
- Memory utilization consistently > 85%
- Processing queue length > 50
- Request latency > 500ms (p95)

### When to Scale Down

- CPU utilization consistently < 40%
- Memory utilization consistently < 50%
- Processing queue empty for > 5 minutes
- Low request rate during off-hours

### Manual Scaling

```bash
# Scale Video Service
kubectl scale deployment video -n metlab-dev --replicas=5

# Scale Video Worker
kubectl scale deployment video-worker -n metlab-dev --replicas=4
```

## Backup and Recovery

### Database Backup

Video metadata is stored in PostgreSQL. Ensure regular backups:

```bash
# Backup video metadata
kubectl exec -n metlab-dev deployment/postgres -- pg_dump -U postgres -d metlab -t videos -t video_variants -t video_thumbnails -t video_views > video-backup.sql
```

### Storage Backup

Video files are stored in S3/MinIO. Enable versioning and replication:

```bash
# Enable versioning on MinIO bucket
mc version enable minio/metlab-videos
mc version enable minio/metlab-thumbnails

# Set up replication (if using multiple regions)
mc replicate add minio/metlab-videos --remote-bucket backup-videos
```

## Production Considerations

1. **Use production-grade storage**: Replace emptyDir with persistent volumes
2. **Enable TLS**: Configure TLS for gRPC communication
3. **Set resource quotas**: Prevent resource exhaustion
4. **Configure network policies**: Restrict traffic between services
5. **Enable audit logging**: Track all video operations
6. **Set up monitoring**: Prometheus + Grafana dashboards
7. **Configure alerting**: PagerDuty or similar for critical issues
8. **Regular security scans**: Trivy, OWASP ZAP
9. **Load testing**: Ensure system can handle peak load
10. **Disaster recovery plan**: Document recovery procedures

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [gRPC Health Checking](https://github.com/grpc/grpc/blob/master/doc/health-checking.md)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [MinIO Documentation](https://min.io/docs/)
