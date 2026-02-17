# Video Service Quick Reference

## Quick Deploy

```bash
# Deploy Video Service
kubectl apply -f video.yaml

# Deploy Video Worker
kubectl apply -f video-worker-deployment.yaml

# Verify
kubectl get pods -n metlab-dev | grep video
```

## Quick Status Check

```bash
# Check all video components
kubectl get all -n metlab-dev -l app=metlab,service=video
kubectl get all -n metlab-dev -l app=metlab,service=video-worker

# Check health
kubectl exec -n metlab-dev deployment/video -- grpc_health_probe -addr=:50052
kubectl exec -n metlab-dev deployment/video-worker -- curl http://localhost:9090/health
```

## Quick Logs

```bash
# Video Service logs
kubectl logs -n metlab-dev -l service=video --tail=50 -f

# Video Worker logs
kubectl logs -n metlab-dev -l service=video-worker --tail=50 -f

# Errors only
kubectl logs -n metlab-dev -l service=video | grep ERROR
kubectl logs -n metlab-dev -l service=video-worker | grep ERROR
```

## Quick Scale

```bash
# Scale Video Service
kubectl scale deployment video -n metlab-dev --replicas=5

# Scale Video Worker
kubectl scale deployment video-worker -n metlab-dev --replicas=4

# Check HPA
kubectl get hpa -n metlab-dev | grep video
```

## Quick Debug

```bash
# Shell into Video Service
kubectl exec -it -n metlab-dev deployment/video -- /bin/sh

# Shell into Video Worker
kubectl exec -it -n metlab-dev deployment/video-worker -- /bin/sh

# Check storage
kubectl exec -n metlab-dev deployment/video -- df -h /tmp/video-processing
kubectl exec -n metlab-dev deployment/video-worker -- df -h /tmp/video-processing

# Check Redis queue
kubectl exec -n metlab-dev deployment/redis -- redis-cli LLEN video-processing
```

## Quick Restart

```bash
# Restart Video Service
kubectl rollout restart deployment/video -n metlab-dev

# Restart Video Worker
kubectl rollout restart deployment/video-worker -n metlab-dev

# Check rollout status
kubectl rollout status deployment/video -n metlab-dev
kubectl rollout status deployment/video-worker -n metlab-dev
```

## Quick Config Update

```bash
# Edit Video Service config
kubectl edit configmap video-config -n metlab-dev

# Edit Video Worker config
kubectl edit configmap video-worker-config -n metlab-dev

# Restart to apply changes
kubectl rollout restart deployment/video -n metlab-dev
kubectl rollout restart deployment/video-worker -n metlab-dev
```

## Quick Metrics

```bash
# Port forward to metrics
kubectl port-forward -n metlab-dev svc/video-worker 9090:9090

# Access metrics
curl http://localhost:9090/metrics
```

## Quick Cleanup

```bash
# Delete Video Service
kubectl delete -f video.yaml

# Delete Video Worker
kubectl delete -f video-worker-deployment.yaml

# Verify deletion
kubectl get all -n metlab-dev | grep video
```

## Common Issues

### Video Service won't start
```bash
# Check events
kubectl describe pod -n metlab-dev -l service=video

# Check database connection
kubectl exec -n metlab-dev deployment/video -- env | grep DATABASE

# Check S3 connection
kubectl exec -n metlab-dev deployment/video -- env | grep S3
```

### Video Worker not processing
```bash
# Check queue
kubectl exec -n metlab-dev deployment/redis -- redis-cli LLEN video-processing

# Check worker logs
kubectl logs -n metlab-dev -l service=video-worker --tail=100

# Check FFmpeg
kubectl exec -n metlab-dev deployment/video-worker -- ffmpeg -version
```

### Storage full
```bash
# Check PVC
kubectl get pvc -n metlab-dev | grep video

# Check usage
kubectl exec -n metlab-dev deployment/video-worker -- df -h

# Clean temp files
kubectl exec -n metlab-dev deployment/video-worker -- find /tmp/video-processing -type f -mtime +1 -delete
```

## Environment Variables

### Video Service
- `PORT=50052`
- `DATABASE_URL=postgres://...`
- `S3_ENDPOINT=http://minio-service:9000`
- `VIDEO_BUCKET=metlab-videos`
- `REDIS_HOST=redis`

### Video Worker
- `DATABASE_URL=postgres://...`
- `S3_ENDPOINT=http://minio-service:9000`
- `VIDEO_BUCKET=metlab-videos`
- `REDIS_HOST=redis`
- `PROCESSING_QUEUE=video-processing`
- `FFMPEG_THREADS=4`
- `VIDEO_RESOLUTIONS=1080p,720p,480p,360p`

## Ports

- **Video Service**: 50052 (gRPC)
- **Video Worker**: 9090 (metrics)

## Resources

- **Video Service**: 1-2Gi memory, 1-2 CPU
- **Video Worker**: 2-4Gi memory, 1.5-3 CPU

## Scaling Limits

- **Video Service**: 2-10 replicas
- **Video Worker**: 2-8 replicas

## Health Endpoints

- **Video Service**: gRPC health check on port 50052
- **Video Worker**: HTTP /health on port 9090
