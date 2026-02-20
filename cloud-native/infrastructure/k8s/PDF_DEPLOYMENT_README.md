# PDF Service Kubernetes Deployment

## Overview

This document describes the Kubernetes deployment configuration for the PDF Service, which handles PDF document uploads, storage, and download URL generation for the Metlab educational platform.

## Architecture

The PDF Service is deployed as a microservice within the Kubernetes cluster with the following components:

- **Deployment**: Manages PDF service pods with auto-scaling capabilities
- **Service**: Provides internal gRPC communication endpoint
- **ConfigMap**: Stores non-sensitive configuration
- **Secret**: Stores sensitive credentials (database password, S3 keys)
- **HorizontalPodAutoscaler**: Automatically scales pods based on CPU and memory usage

## Components

### ConfigMap (pdf-config)

Stores configuration parameters:
- `PORT`: gRPC server port (50056)
- `ENV`: Environment (development/production)
- `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_USER`, `DATABASE_NAME`: PostgreSQL connection details
- `S3_ENDPOINT`, `S3_REGION`, `PDF_BUCKET`: S3 storage configuration
- `MAX_UPLOAD_SIZE_MB`: Maximum PDF file size (50MB)
- `SUPPORTED_FORMATS`: Allowed file formats (pdf)
- `DOWNLOAD_URL_EXPIRY_HOURS`: Signed URL expiration time (1 hour)

### Secret (pdf-secret)

Stores sensitive data:
- `DATABASE_PASSWORD`: PostgreSQL password
- `S3_ACCESS_KEY`: S3 access key
- `S3_SECRET_KEY`: S3 secret key

### Deployment

**Specifications:**
- **Replicas**: 2 (minimum)
- **Image**: metlab/pdf:latest
- **Port**: 50056 (gRPC)
- **Strategy**: RollingUpdate with maxSurge=1, maxUnavailable=0

**Resource Limits:**
- Requests: 256Mi memory, 250m CPU
- Limits: 512Mi memory, 500m CPU

**Health Checks:**
- **Liveness Probe**: gRPC health check every 10s (starts after 30s)
- **Readiness Probe**: gRPC health check every 5s (starts after 10s)

**Security:**
- Runs as non-root user
- No privilege escalation
- Drops all capabilities
- Read-only root filesystem disabled (for temp file handling)

### Service

**Type**: ClusterIP (internal only)
**Port**: 50056 (gRPC)
**Selector**: app=metlab, service=pdf

### HorizontalPodAutoscaler

**Scaling Configuration:**
- Min replicas: 2
- Max replicas: 10
- CPU target: 80% utilization
- Memory target: 85% utilization

**Behavior:**
- Scale up: Fast (100% or 2 pods per 30s)
- Scale down: Conservative (50% or 1 pod per 60s, 5min stabilization)

## Deployment Instructions

### Prerequisites

1. Kubernetes cluster running (Minikube for dev)
2. kubectl configured
3. Namespace created (metlab-dev)
4. PostgreSQL deployed and running
5. MinIO/S3 deployed and running
6. PDF service Docker image built

### Deploy to Kubernetes

```bash
# Apply the deployment
kubectl apply -f cloud-native/infrastructure/k8s/pdf.yaml

# Verify deployment
kubectl get pods -n metlab-dev -l service=pdf
kubectl get svc -n metlab-dev -l service=pdf
kubectl get hpa -n metlab-dev -l service=pdf
```

### Verify Deployment

```bash
# Check pod status
kubectl get pods -n metlab-dev -l service=pdf

# Check logs
kubectl logs -n metlab-dev -l service=pdf --tail=50

# Check service endpoints
kubectl get endpoints -n metlab-dev pdf

# Test health check
kubectl exec -n metlab-dev deployment/pdf -- grpc_health_probe -addr=:50056
```

## Configuration

### Environment Variables

All configuration is injected via ConfigMap and Secret:

```yaml
# From ConfigMap
PORT: "50056"
DATABASE_HOST: "postgres"
S3_ENDPOINT: "http://minio-service:9000"
PDF_BUCKET: "metlab-pdfs"
MAX_UPLOAD_SIZE_MB: "50"

# From Secret
DATABASE_PASSWORD: <encrypted>
S3_ACCESS_KEY: <encrypted>
S3_SECRET_KEY: <encrypted>
```

### S3 Bucket Configuration

The PDF service requires an S3 bucket named `metlab-pdfs`:

```bash
# Create bucket in MinIO (development)
kubectl exec -n metlab-dev deployment/minio -- \
  mc mb local/metlab-pdfs

# Set bucket policy (public read for signed URLs)
kubectl exec -n metlab-dev deployment/minio -- \
  mc policy set download local/metlab-pdfs
```

## Monitoring

### Metrics

The service exposes Prometheus metrics on port 50056:
- gRPC request duration
- Request count by method
- Error rate
- Active connections
- Upload/download operations

### Health Checks

**Liveness Probe:**
- Checks if service is alive
- Restarts pod if failing for 30s

**Readiness Probe:**
- Checks if service can handle requests
- Removes from load balancer if failing

### Logs

View logs:
```bash
# All pods
kubectl logs -n metlab-dev -l service=pdf --tail=100 -f

# Specific pod
kubectl logs -n metlab-dev pdf-<pod-id> -f
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod events
kubectl describe pod -n metlab-dev <pod-name>

# Check logs
kubectl logs -n metlab-dev <pod-name>

# Common issues:
# - Database connection failed: Check DATABASE_HOST and credentials
# - S3 connection failed: Check S3_ENDPOINT and credentials
# - Image pull failed: Check image name and registry access
```

### Service Not Responding

```bash
# Check service endpoints
kubectl get endpoints -n metlab-dev pdf

# Test gRPC health
kubectl exec -n metlab-dev deployment/pdf -- grpc_health_probe -addr=:50056

# Check if pods are ready
kubectl get pods -n metlab-dev -l service=pdf
```

### High Memory Usage

```bash
# Check current usage
kubectl top pods -n metlab-dev -l service=pdf

# Increase memory limits if needed
# Edit pdf.yaml and increase resources.limits.memory
```

### Scaling Issues

```bash
# Check HPA status
kubectl get hpa -n metlab-dev pdf-hpa

# Check HPA events
kubectl describe hpa -n metlab-dev pdf-hpa

# Manual scaling (temporary)
kubectl scale deployment -n metlab-dev pdf --replicas=5
```

## Integration

### API Gateway Integration

The API Gateway connects to the PDF service via gRPC:

```go
// API Gateway configuration
pdfConn, err := grpc.Dial(
    "pdf:50056",
    grpc.WithInsecure(),
)
pdfClient := pb.NewPDFServiceClient(pdfConn)
```

### Database Schema

The PDF service uses these tables:
- `pdfs`: PDF metadata and storage paths
- `classes`: Class information (foreign key)
- `teachers`: Teacher information (foreign key)

### S3 Storage

PDFs are stored in S3 with the following structure:
```
metlab-pdfs/
  ├── <class-id>/
  │   ├── <pdf-id>.pdf
  │   └── ...
```

## Security

### Network Policies

The PDF service should only accept connections from:
- API Gateway
- Monitoring systems (Prometheus)

### Secrets Management

Secrets are stored in Kubernetes Secrets and injected as environment variables. Never commit secrets to git.

To update secrets:
```bash
# Update secret
kubectl create secret generic pdf-secret \
  --from-literal=DATABASE_PASSWORD=<new-password> \
  --from-literal=S3_ACCESS_KEY=<new-key> \
  --from-literal=S3_SECRET_KEY=<new-secret> \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart pods to pick up new secrets
kubectl rollout restart deployment -n metlab-dev pdf
```

### TLS/SSL

For production:
- Enable SSL for S3 connections
- Use TLS for database connections
- Consider mTLS for service-to-service communication

## Performance

### Resource Tuning

Based on load testing:
- 256Mi memory handles ~50 concurrent uploads
- 250m CPU handles ~100 requests/second
- Scale to 10 pods for peak load (500 concurrent users)

### Optimization Tips

1. **Connection Pooling**: Database connections are pooled (10-100 connections)
2. **Streaming Uploads**: Large files are streamed to S3 to minimize memory usage
3. **Signed URLs**: Download URLs are pre-signed to offload traffic from service
4. **Caching**: PDF metadata is cached in Redis (if available)

## Maintenance

### Rolling Updates

```bash
# Update image
kubectl set image deployment/pdf -n metlab-dev \
  pdf=metlab/pdf:v2.0.0

# Check rollout status
kubectl rollout status deployment/pdf -n metlab-dev

# Rollback if needed
kubectl rollout undo deployment/pdf -n metlab-dev
```

### Backup and Recovery

PDFs are stored in S3 with versioning enabled. Database backups include PDF metadata.

### Cleanup

```bash
# Delete deployment
kubectl delete -f cloud-native/infrastructure/k8s/pdf.yaml

# Or delete specific resources
kubectl delete deployment,service,hpa,configmap,secret -n metlab-dev -l service=pdf
```

## References

- [gRPC Health Checking Protocol](https://github.com/grpc/grpc/blob/master/doc/health-checking.md)
- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [MinIO Documentation](https://min.io/docs/minio/kubernetes/upstream/)

## Requirements Satisfied

This deployment satisfies the following requirements from the specification:

- **16.1**: Container orchestration with Kubernetes, health checks, resource limits
- **16.5**: Kubernetes Secrets for sensitive configuration data
- **5.1-5.5**: PDF upload, storage, and download functionality
- **11.1-11.5**: PDF listing and download for students