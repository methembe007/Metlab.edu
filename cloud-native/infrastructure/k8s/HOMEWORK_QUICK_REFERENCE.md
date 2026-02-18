# Homework Service - Quick Reference

## Quick Commands

### Deploy
```bash
kubectl apply -f cloud-native/infrastructure/k8s/homework.yaml
```

### Status Check
```bash
# Check deployment
kubectl get deployment homework -n metlab-dev

# Check pods
kubectl get pods -n metlab-dev -l service=homework

# Check service
kubectl get svc homework -n metlab-dev

# Check HPA
kubectl get hpa homework-hpa -n metlab-dev
```

### Logs
```bash
# Tail logs
kubectl logs -n metlab-dev -l service=homework --tail=50 -f

# All logs
kubectl logs -n metlab-dev -l service=homework --all-containers=true
```

### Port Forward
```bash
# Forward gRPC port
kubectl port-forward -n metlab-dev svc/homework 50053:50053
```

### Scale
```bash
# Manual scale
kubectl scale deployment homework -n metlab-dev --replicas=5

# Check autoscaling
kubectl get hpa homework-hpa -n metlab-dev -w
```

### Update
```bash
# Update image
kubectl set image deployment/homework homework=metlab/homework:v1.2.0 -n metlab-dev

# Rollout status
kubectl rollout status deployment/homework -n metlab-dev

# Rollback
kubectl rollout undo deployment/homework -n metlab-dev
```

### Configuration
```bash
# Edit ConfigMap
kubectl edit configmap homework-config -n metlab-dev

# Edit Secret
kubectl edit secret homework-secret -n metlab-dev

# Restart to apply changes
kubectl rollout restart deployment homework -n metlab-dev
```

### Debug
```bash
# Describe pod
kubectl describe pod -n metlab-dev -l service=homework

# Exec into pod
kubectl exec -it -n metlab-dev <pod-name> -- /bin/sh

# Check events
kubectl get events -n metlab-dev --sort-by='.lastTimestamp' | grep homework
```

### Health Check
```bash
# Port forward first
kubectl port-forward -n metlab-dev svc/homework 50053:50053

# Test with grpcurl
grpcurl -plaintext localhost:50053 grpc.health.v1.Health/Check

# Test with grpc_health_probe
grpc_health_probe -addr=localhost:50053
```

### Delete
```bash
# Delete all homework resources
kubectl delete -f cloud-native/infrastructure/k8s/homework.yaml

# Or delete individually
kubectl delete deployment homework -n metlab-dev
kubectl delete service homework -n metlab-dev
kubectl delete hpa homework-hpa -n metlab-dev
kubectl delete configmap homework-config -n metlab-dev
kubectl delete secret homework-secret -n metlab-dev
```

## Configuration Values

### ConfigMap (homework-config)
- `PORT`: 50053
- `ENV`: development
- `DATABASE_HOST`: postgres
- `DATABASE_PORT`: 5432
- `DATABASE_USER`: postgres
- `DATABASE_NAME`: metlab
- `S3_ENDPOINT`: http://minio-service:9000
- `S3_REGION`: us-east-1
- `HOMEWORK_BUCKET`: metlab-homework
- `MAX_UPLOAD_SIZE_MB`: 25
- `SUPPORTED_FORMATS`: pdf,docx,txt,jpg,jpeg,png

### Secret (homework-secret)
- `DATABASE_PASSWORD`: postgres (change in production!)
- `S3_ACCESS_KEY`: minioadmin (change in production!)
- `S3_SECRET_KEY`: minioadmin (change in production!)

## Resource Limits

### Requests
- Memory: 512Mi
- CPU: 500m

### Limits
- Memory: 1Gi
- CPU: 1000m

## Auto-scaling

### HPA Settings
- Min Replicas: 2
- Max Replicas: 10
- CPU Target: 80%
- Memory Target: 85%

## Health Checks

### Liveness Probe
- Initial Delay: 30s
- Period: 10s
- Timeout: 5s
- Failure Threshold: 3

### Readiness Probe
- Initial Delay: 10s
- Period: 5s
- Timeout: 3s
- Failure Threshold: 3

## Service Endpoints

### Internal gRPC
- Service Name: `homework.metlab-dev.svc.cluster.local`
- Port: 50053
- Protocol: TCP

## Common Issues

### Pod CrashLoopBackOff
```bash
# Check logs
kubectl logs -n metlab-dev -l service=homework --previous

# Check events
kubectl describe pod -n metlab-dev -l service=homework
```

### Database Connection Failed
```bash
# Check if postgres is running
kubectl get pods -n metlab-dev -l app=postgres

# Test connection
kubectl exec -it -n metlab-dev <homework-pod> -- nc -zv postgres 5432
```

### S3/MinIO Connection Failed
```bash
# Check if MinIO is running
kubectl get pods -n metlab-dev -l app=minio

# Test connection
kubectl exec -it -n metlab-dev <homework-pod> -- nc -zv minio-service 9000
```

### Health Check Failing
```bash
# Check if grpc_health_probe is in the image
kubectl exec -it -n metlab-dev <homework-pod> -- which grpc_health_probe

# Test manually
kubectl exec -it -n metlab-dev <homework-pod> -- grpc_health_probe -addr=:50053
```

## Monitoring

### Prometheus Metrics
- Endpoint: `:50053/metrics`
- Scrape: Enabled via annotations

### Key Metrics to Monitor
- Request rate
- Error rate
- Response latency
- Upload/download rates
- Storage usage
- Pod restarts
- CPU/Memory usage

## Dependencies

### Required Services
- PostgreSQL (postgres:5432)
- MinIO/S3 (minio-service:9000)

### Optional Services
- Redis (for caching)
- Prometheus (for metrics)

## Testing

### Test gRPC Endpoints
```bash
# Port forward
kubectl port-forward -n metlab-dev svc/homework 50053:50053

# List methods
grpcurl -plaintext localhost:50053 list

# Call CreateAssignment
grpcurl -plaintext -d '{"teacher_id":"test","class_id":"test","title":"Test"}' \
  localhost:50053 homework.HomeworkService/CreateAssignment
```

## Production Checklist

- [ ] Update DATABASE_PASSWORD in secret
- [ ] Update S3_ACCESS_KEY and S3_SECRET_KEY in secret
- [ ] Configure proper S3 endpoint (not MinIO)
- [ ] Enable TLS for database connections
- [ ] Set up network policies
- [ ] Configure pod disruption budget
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Test backup and restore procedures
- [ ] Document runbooks
- [ ] Load test the service
- [ ] Security scan the container image

</content>
