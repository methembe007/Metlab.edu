# PDF Service - Quick Reference Guide

## Service Overview

**Service Name**: PDF Service  
**Port**: 50056 (gRPC)  
**Namespace**: metlab-dev  
**Purpose**: Handle PDF document uploads, storage, and download URL generation

## Quick Commands

### Deployment

```bash
# Deploy PDF service
kubectl apply -f cloud-native/infrastructure/k8s/pdf.yaml

# Validate deployment
./cloud-native/infrastructure/k8s/validate-pdf-deployment.sh
# Or on Windows:
.\cloud-native\infrastructure\k8s\validate-pdf-deployment.ps1

# Check status
kubectl get all -n metlab-dev -l service=pdf
```

### Monitoring

```bash
# View logs (all pods)
kubectl logs -n metlab-dev -l service=pdf -f

# View logs (specific pod)
kubectl logs -n metlab-dev pdf-<pod-id> -f

# Check resource usage
kubectl top pods -n metlab-dev -l service=pdf

# Check HPA status
kubectl get hpa -n metlab-dev pdf-hpa
```

### Debugging

```bash
# Describe deployment
kubectl describe deployment pdf -n metlab-dev

# Describe pods
kubectl describe pods -n metlab-dev -l service=pdf

# Check events
kubectl get events -n metlab-dev --sort-by='.lastTimestamp' | grep pdf

# Test gRPC health
kubectl exec -n metlab-dev deployment/pdf -- grpc_health_probe -addr=:50056

# Shell into pod
kubectl exec -it -n metlab-dev deployment/pdf -- sh
```

### Configuration

```bash
# View ConfigMap
kubectl get configmap pdf-config -n metlab-dev -o yaml

# View Secret (base64 encoded)
kubectl get secret pdf-secret -n metlab-dev -o yaml

# Update ConfigMap
kubectl edit configmap pdf-config -n metlab-dev

# Update Secret
kubectl create secret generic pdf-secret \
  --from-literal=DATABASE_PASSWORD=<password> \
  --from-literal=S3_ACCESS_KEY=<key> \
  --from-literal=S3_SECRET_KEY=<secret> \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart pods to pick up config changes
kubectl rollout restart deployment pdf -n metlab-dev
```

### Scaling

```bash
# Manual scale
kubectl scale deployment pdf -n metlab-dev --replicas=5

# Check HPA
kubectl get hpa pdf-hpa -n metlab-dev

# Describe HPA
kubectl describe hpa pdf-hpa -n metlab-dev

# Edit HPA
kubectl edit hpa pdf-hpa -n metlab-dev
```

### Updates

```bash
# Update image
kubectl set image deployment/pdf -n metlab-dev \
  pdf=metlab/pdf:v2.0.0

# Check rollout status
kubectl rollout status deployment/pdf -n metlab-dev

# View rollout history
kubectl rollout history deployment/pdf -n metlab-dev

# Rollback to previous version
kubectl rollout undo deployment/pdf -n metlab-dev

# Rollback to specific revision
kubectl rollout undo deployment/pdf -n metlab-dev --to-revision=2
```

### Cleanup

```bash
# Delete all PDF service resources
kubectl delete -f cloud-native/infrastructure/k8s/pdf.yaml

# Or delete individually
kubectl delete deployment,service,hpa,configmap,secret -n metlab-dev -l service=pdf
```

## Configuration Reference

### Environment Variables

| Variable | Source | Description |
|----------|--------|-------------|
| PORT | ConfigMap | gRPC server port (50056) |
| ENV | ConfigMap | Environment (development/production) |
| DATABASE_HOST | ConfigMap | PostgreSQL host |
| DATABASE_PORT | ConfigMap | PostgreSQL port |
| DATABASE_USER | ConfigMap | PostgreSQL user |
| DATABASE_NAME | ConfigMap | PostgreSQL database name |
| DATABASE_PASSWORD | Secret | PostgreSQL password |
| S3_ENDPOINT | ConfigMap | S3/MinIO endpoint URL |
| S3_REGION | ConfigMap | S3 region |
| PDF_BUCKET | ConfigMap | S3 bucket for PDFs |
| S3_ACCESS_KEY | Secret | S3 access key |
| S3_SECRET_KEY | Secret | S3 secret key |
| MAX_UPLOAD_SIZE_MB | ConfigMap | Max PDF size (50MB) |
| SUPPORTED_FORMATS | ConfigMap | Allowed formats (pdf) |
| DOWNLOAD_URL_EXPIRY_HOURS | ConfigMap | URL expiration (1 hour) |

### Resource Limits

| Resource | Request | Limit |
|----------|---------|-------|
| Memory | 256Mi | 512Mi |
| CPU | 250m | 500m |

### Scaling Configuration

| Parameter | Value |
|-----------|-------|
| Min Replicas | 2 |
| Max Replicas | 10 |
| CPU Target | 80% |
| Memory Target | 85% |

## Health Checks

### Liveness Probe
- **Type**: gRPC health check
- **Initial Delay**: 30 seconds
- **Period**: 10 seconds
- **Timeout**: 5 seconds
- **Failure Threshold**: 3

### Readiness Probe
- **Type**: gRPC health check
- **Initial Delay**: 10 seconds
- **Period**: 5 seconds
- **Timeout**: 3 seconds
- **Failure Threshold**: 3

## Service Endpoints

### Internal (within cluster)
```
pdf.metlab-dev.svc.cluster.local:50056
```

### From API Gateway
```go
conn, err := grpc.Dial("pdf:50056", grpc.WithInsecure())
```

## gRPC Methods

| Method | Description |
|--------|-------------|
| UploadPDF | Stream PDF file upload |
| ListPDFs | List PDFs for a class |
| GetDownloadURL | Generate signed download URL |

## Common Issues

### Pod Not Starting

**Symptoms**: Pod stuck in Pending or CrashLoopBackOff

**Solutions**:
```bash
# Check pod events
kubectl describe pod -n metlab-dev <pod-name>

# Check logs
kubectl logs -n metlab-dev <pod-name>

# Common causes:
# - Database connection failed: Check DATABASE_HOST and credentials
# - S3 connection failed: Check S3_ENDPOINT and credentials
# - Image pull failed: Check image name and registry
```

### Service Not Responding

**Symptoms**: API Gateway cannot connect to PDF service

**Solutions**:
```bash
# Check service endpoints
kubectl get endpoints -n metlab-dev pdf

# Test from another pod
kubectl run -it --rm debug --image=alpine --restart=Never -n metlab-dev -- sh
# Inside pod:
apk add curl
curl -v telnet://pdf:50056

# Check if pods are ready
kubectl get pods -n metlab-dev -l service=pdf
```

### High Memory Usage

**Symptoms**: Pods being OOMKilled

**Solutions**:
```bash
# Check current usage
kubectl top pods -n metlab-dev -l service=pdf

# Increase memory limits
# Edit pdf.yaml and increase resources.limits.memory
kubectl apply -f cloud-native/infrastructure/k8s/pdf.yaml
```

### Upload Failures

**Symptoms**: PDF uploads failing

**Solutions**:
```bash
# Check S3 connectivity
kubectl exec -n metlab-dev deployment/pdf -- sh -c "nc -zv minio-service 9000"

# Check S3 bucket exists
kubectl exec -n metlab-dev deployment/minio -- mc ls local/metlab-pdfs

# Check upload size limit
kubectl get configmap pdf-config -n metlab-dev -o jsonpath='{.data.MAX_UPLOAD_SIZE_MB}'
```

## Performance Tuning

### For High Load

```bash
# Increase replicas
kubectl scale deployment pdf -n metlab-dev --replicas=8

# Or adjust HPA
kubectl patch hpa pdf-hpa -n metlab-dev -p '{"spec":{"maxReplicas":15}}'
```

### For Low Load

```bash
# Decrease replicas
kubectl scale deployment pdf -n metlab-dev --replicas=2

# Or adjust HPA
kubectl patch hpa pdf-hpa -n metlab-dev -p '{"spec":{"minReplicas":1}}'
```

## Monitoring Metrics

### Prometheus Metrics

The service exposes metrics on port 50056:
- `grpc_server_handled_total` - Total gRPC requests
- `grpc_server_handling_seconds` - Request duration
- `pdf_uploads_total` - Total PDF uploads
- `pdf_downloads_total` - Total download URL generations
- `pdf_upload_bytes` - Upload size distribution

### Grafana Dashboard

Import the PDF service dashboard:
```bash
# Dashboard ID: TBD
# Metrics include:
# - Request rate
# - Error rate
# - Response time (p50, p95, p99)
# - Upload/download counts
# - Resource usage
```

## Integration Testing

### Test PDF Upload

```bash
# Port-forward API Gateway
kubectl port-forward -n metlab-dev svc/api-gateway 8080:8080

# Upload PDF (using curl)
curl -X POST http://localhost:8080/api/pdfs \
  -H "Authorization: Bearer <token>" \
  -F "file=@test.pdf" \
  -F "title=Test PDF" \
  -F "class_id=<class-id>"
```

### Test PDF Download

```bash
# Get download URL
curl http://localhost:8080/api/pdfs/<pdf-id>/download \
  -H "Authorization: Bearer <token>"

# Download PDF
curl -o downloaded.pdf "<signed-url>"
```

## Security Checklist

- [ ] Secrets are not committed to git
- [ ] Database password is strong and rotated
- [ ] S3 credentials have minimal required permissions
- [ ] TLS is enabled for production
- [ ] Network policies restrict access to PDF service
- [ ] Resource limits prevent resource exhaustion
- [ ] Health checks are properly configured

## Related Documentation

- [Full Deployment README](./PDF_DEPLOYMENT_README.md)
- [PDF Service Implementation](../../services/pdf/README.md)
- [API Gateway Integration](./API_GATEWAY_QUICK_REFERENCE.md)
- [Kubernetes Best Practices](./README.md)

## Support

For issues or questions:
1. Check logs: `kubectl logs -n metlab-dev -l service=pdf`
2. Run validation: `./validate-pdf-deployment.sh`
3. Review events: `kubectl get events -n metlab-dev`
4. Consult full documentation: `PDF_DEPLOYMENT_README.md`
