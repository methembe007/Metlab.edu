# Homework Service Kubernetes Deployment

This document describes the Kubernetes deployment configuration for the Homework Service.

## Overview

The Homework Service deployment includes:
- **ConfigMap**: Non-sensitive configuration values
- **Secret**: Sensitive data (database password, S3 credentials)
- **Deployment**: Pod specification with resource limits and health checks
- **Service**: Internal gRPC communication endpoint
- **HorizontalPodAutoscaler**: Auto-scaling based on CPU and memory usage

## Components

### 1. ConfigMap (homework-config)

Contains non-sensitive configuration:
- `PORT`: gRPC server port (50053)
- `ENV`: Environment (development/staging/production)
- `DATABASE_HOST`: PostgreSQL host
- `DATABASE_PORT`: PostgreSQL port
- `DATABASE_USER`: Database username
- `DATABASE_NAME`: Database name
- `S3_ENDPOINT`: S3-compatible storage endpoint (MinIO for dev)
- `S3_REGION`: S3 region
- `HOMEWORK_BUCKET`: S3 bucket for homework submissions
- `MAX_UPLOAD_SIZE_MB`: Maximum file upload size (25MB)
- `SUPPORTED_FORMATS`: Allowed file formats (pdf,docx,txt,jpg,jpeg,png)

### 2. Secret (homework-secret)

Contains sensitive data:
- `DATABASE_PASSWORD`: PostgreSQL password
- `S3_ACCESS_KEY`: S3 access key
- `S3_SECRET_KEY`: S3 secret key

**Security Note**: In production, use strong random values and manage secrets securely (e.g., using sealed-secrets, external secret managers like Vault, or cloud provider secret management).

### 3. Deployment

**Replicas**: 2 (minimum for high availability)

**Resource Limits**:
- Requests: 512Mi memory, 500m CPU
- Limits: 1Gi memory, 1000m CPU

**Rolling Update Strategy**:
- MaxSurge: 1 (one extra pod during updates)
- MaxUnavailable: 0 (zero downtime deployments)

**Health Checks**:

**Liveness Probe**:
- Uses `grpc_health_probe` to check if service is alive
- Initial delay: 30 seconds
- Period: 10 seconds
- Timeout: 5 seconds
- Failure threshold: 3 (restart after 3 failures)

**Readiness Probe**:
- Uses `grpc_health_probe` to check if service is ready
- Initial delay: 10 seconds
- Period: 5 seconds
- Timeout: 3 seconds
- Failure threshold: 3 (remove from service after 3 failures)

**Security Context**:
- Drop all capabilities
- No privilege escalation
- Read-only root filesystem disabled (for now, can be enabled with proper volume mounts)

### 4. Service

**Type**: ClusterIP (internal only)
**Port**: 50053 (gRPC)
**Protocol**: TCP

The service provides a stable endpoint for other services to communicate with the Homework Service via gRPC.

### 5. HorizontalPodAutoscaler (HPA)

**Scaling Range**: 2-10 replicas

**Metrics**:
- CPU: Scale when average utilization > 80%
- Memory: Scale when average utilization > 85%

**Behavior**:
- **Scale Up**: Fast (100% increase or 2 pods every 30 seconds)
- **Scale Down**: Slow (50% decrease or 1 pod every 60 seconds, with 5-minute stabilization)

This ensures the service can handle traffic spikes quickly while avoiding flapping during scale-down.

## Deployment Instructions

### Prerequisites

1. Kubernetes cluster running (Minikube for local development)
2. kubectl configured to access the cluster
3. `metlab-dev` namespace created
4. PostgreSQL deployed and accessible
5. MinIO (or S3) deployed and accessible
6. Homework bucket created in S3/MinIO

### Deploy Homework Service

```bash
# Apply the deployment
kubectl apply -f cloud-native/infrastructure/k8s/homework.yaml

# Verify deployment
kubectl get deployment homework -n metlab-dev
kubectl get pods -n metlab-dev -l service=homework
kubectl get svc homework -n metlab-dev
kubectl get hpa homework-hpa -n metlab-dev

# Check pod logs
kubectl logs -n metlab-dev -l service=homework --tail=50

# Check pod status
kubectl describe pod -n metlab-dev -l service=homework
```

### Verify Health Checks

```bash
# Port forward to test locally
kubectl port-forward -n metlab-dev svc/homework 50053:50053

# In another terminal, test with grpc_health_probe (if installed)
grpc_health_probe -addr=localhost:50053

# Or use grpcurl
grpcurl -plaintext localhost:50053 grpc.health.v1.Health/Check
```

### Update Configuration

To update configuration values:

```bash
# Edit ConfigMap
kubectl edit configmap homework-config -n metlab-dev

# Edit Secret
kubectl edit secret homework-secret -n metlab-dev

# Restart pods to pick up changes
kubectl rollout restart deployment homework -n metlab-dev
```

### Scaling

Manual scaling:
```bash
# Scale to 5 replicas
kubectl scale deployment homework -n metlab-dev --replicas=5

# Check HPA status
kubectl get hpa homework-hpa -n metlab-dev
```

The HPA will automatically adjust replicas based on CPU/memory usage.

### Troubleshooting

**Pods not starting**:
```bash
# Check pod events
kubectl describe pod -n metlab-dev -l service=homework

# Check logs
kubectl logs -n metlab-dev -l service=homework --tail=100
```

**Health checks failing**:
```bash
# Exec into pod
kubectl exec -it -n metlab-dev <pod-name> -- /bin/sh

# Check if grpc_health_probe is available
which grpc_health_probe

# Test health check manually
grpc_health_probe -addr=:50053
```

**Database connection issues**:
```bash
# Check if PostgreSQL is accessible
kubectl get svc postgres -n metlab-dev

# Test connection from homework pod
kubectl exec -it -n metlab-dev <homework-pod-name> -- /bin/sh
# Inside pod:
# nc -zv postgres 5432
```

**S3/MinIO connection issues**:
```bash
# Check if MinIO is accessible
kubectl get svc minio-service -n metlab-dev

# Test connection from homework pod
kubectl exec -it -n metlab-dev <homework-pod-name> -- /bin/sh
# Inside pod:
# nc -zv minio-service 9000
```

**Secret/ConfigMap not found**:
```bash
# List all ConfigMaps
kubectl get configmap -n metlab-dev

# List all Secrets
kubectl get secret -n metlab-dev

# Verify homework-config and homework-secret exist
kubectl get configmap homework-config -n metlab-dev -o yaml
kubectl get secret homework-secret -n metlab-dev -o yaml
```

## Production Considerations

### Security

1. **Secrets Management**:
   - Use external secret management (Vault, AWS Secrets Manager, etc.)
   - Rotate secrets regularly
   - Never commit secrets to version control

2. **Network Policies**:
   - Implement NetworkPolicy to restrict traffic
   - Only allow necessary ingress/egress
   - Restrict access to S3/MinIO

3. **RBAC**:
   - Use service accounts with minimal permissions
   - Implement pod security policies

4. **File Upload Security**:
   - Validate file types and sizes
   - Scan uploaded files for malware
   - Implement rate limiting for uploads

### Monitoring

1. **Metrics**:
   - Enable Prometheus scraping (annotations already added)
   - Monitor request rate, latency, error rate
   - Track resource usage
   - Monitor upload/download rates
   - Track storage usage

2. **Logging**:
   - Centralize logs (ELK, Loki, cloud provider)
   - Structured logging with trace IDs
   - Log retention policies
   - Log file upload/download events

3. **Alerting**:
   - Alert on pod restarts
   - Alert on high error rates
   - Alert on resource exhaustion
   - Alert on storage quota issues
   - Alert on failed uploads/downloads

### High Availability

1. **Pod Disruption Budget**:
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: homework-pdb
  namespace: metlab-dev
spec:
  minAvailable: 1
  selector:
    matchLabels:
      service: homework
```

2. **Anti-Affinity**:
   - Spread pods across nodes
   - Avoid single point of failure

3. **Resource Quotas**:
   - Set namespace resource limits
   - Prevent resource exhaustion

4. **Storage Redundancy**:
   - Use S3 with replication
   - Regular backups of homework submissions
   - Disaster recovery plan

## Environment-Specific Configurations

### Development (metlab-dev)
- 2 replicas minimum
- Relaxed resource limits
- Debug logging enabled
- Development database
- MinIO for object storage

### Staging (metlab-staging)
- 3 replicas minimum
- Production-like resources
- Info logging
- Staging database
- S3 or MinIO with replication

### Production (metlab-production)
- 5 replicas minimum
- Strict resource limits
- Error/warn logging only
- Production database with replicas
- S3 with versioning and replication
- TLS enabled
- Network policies enforced
- File scanning enabled

## API Endpoints

The Homework Service exposes the following gRPC methods:

1. **CreateAssignment**: Create a new homework assignment
2. **ListAssignments**: List assignments for a class
3. **SubmitHomework**: Submit homework (streaming for file upload)
4. **ListSubmissions**: List submissions for an assignment
5. **GradeSubmission**: Grade a student's submission
6. **GetSubmissionFile**: Download a submission file (streaming)

## Database Schema

The service manages the following tables:
- `homework_assignments`: Assignment metadata
- `homework_submissions`: Student submissions
- `homework_grades`: Grades and feedback

## Storage Structure

Homework files are stored in S3/MinIO with the following structure:
```
metlab-homework/
├── assignments/
│   └── {assignment_id}/
│       └── {student_id}/
│           └── {submission_id}.{ext}
```

## References

- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Kubernetes Services](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [gRPC Health Checking Protocol](https://github.com/grpc/grpc/blob/master/doc/health-checking.md)
- [grpc_health_probe](https://github.com/grpc-ecosystem/grpc-health-probe)
- [MinIO Documentation](https://min.io/docs/minio/kubernetes/upstream/)

</content>
