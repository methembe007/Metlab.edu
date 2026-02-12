# Auth Service Kubernetes Deployment

This document describes the Kubernetes deployment configuration for the Auth Service.

## Overview

The Auth Service deployment includes:
- **ConfigMap**: Non-sensitive configuration values
- **Secret**: Sensitive data (database password, JWT secret)
- **Deployment**: Pod specification with resource limits and health checks
- **Service**: Internal gRPC communication endpoint
- **HorizontalPodAutoscaler**: Auto-scaling based on CPU and memory usage

## Components

### 1. ConfigMap (auth-config)

Contains non-sensitive configuration:
- `PORT`: gRPC server port (50051)
- `ENV`: Environment (development/staging/production)
- `DATABASE_HOST`: PostgreSQL host
- `DATABASE_PORT`: PostgreSQL port
- `DATABASE_USER`: Database username
- `DATABASE_NAME`: Database name
- `JWT_EXPIRY_HOURS`: JWT token expiry for teachers (24 hours)
- `STUDENT_EXPIRY_DAYS`: JWT token expiry for students (7 days)
- `MAX_LOGIN_ATTEMPTS`: Maximum failed login attempts before lockout (5)
- `LOCKOUT_MINUTES`: Account lockout duration (30 minutes)

### 2. Secret (auth-secret)

Contains sensitive data:
- `DATABASE_PASSWORD`: PostgreSQL password
- `JWT_SECRET`: Secret key for JWT token signing

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
**Port**: 50051 (gRPC)
**Protocol**: TCP

The service provides a stable endpoint for other services to communicate with the Auth Service via gRPC.

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

### Deploy Auth Service

```bash
# Apply the deployment
kubectl apply -f cloud-native/infrastructure/k8s/auth.yaml

# Verify deployment
kubectl get deployment auth -n metlab-dev
kubectl get pods -n metlab-dev -l service=auth
kubectl get svc auth -n metlab-dev
kubectl get hpa auth-hpa -n metlab-dev

# Check pod logs
kubectl logs -n metlab-dev -l service=auth --tail=50

# Check pod status
kubectl describe pod -n metlab-dev -l service=auth
```

### Verify Health Checks

```bash
# Port forward to test locally
kubectl port-forward -n metlab-dev svc/auth 50051:50051

# In another terminal, test with grpc_health_probe (if installed)
grpc_health_probe -addr=localhost:50051

# Or use grpcurl
grpcurl -plaintext localhost:50051 grpc.health.v1.Health/Check
```

### Update Configuration

To update configuration values:

```bash
# Edit ConfigMap
kubectl edit configmap auth-config -n metlab-dev

# Edit Secret
kubectl edit secret auth-secret -n metlab-dev

# Restart pods to pick up changes
kubectl rollout restart deployment auth -n metlab-dev
```

### Scaling

Manual scaling:
```bash
# Scale to 5 replicas
kubectl scale deployment auth -n metlab-dev --replicas=5

# Check HPA status
kubectl get hpa auth-hpa -n metlab-dev
```

The HPA will automatically adjust replicas based on CPU/memory usage.

### Troubleshooting

**Pods not starting**:
```bash
# Check pod events
kubectl describe pod -n metlab-dev -l service=auth

# Check logs
kubectl logs -n metlab-dev -l service=auth --tail=100
```

**Health checks failing**:
```bash
# Exec into pod
kubectl exec -it -n metlab-dev <pod-name> -- /bin/sh

# Check if grpc_health_probe is available
which grpc_health_probe

# Test health check manually
grpc_health_probe -addr=:50051
```

**Database connection issues**:
```bash
# Check if PostgreSQL is accessible
kubectl get svc postgres -n metlab-dev

# Test connection from auth pod
kubectl exec -it -n metlab-dev <auth-pod-name> -- /bin/sh
# Inside pod:
# nc -zv postgres 5432
```

**Secret/ConfigMap not found**:
```bash
# List all ConfigMaps
kubectl get configmap -n metlab-dev

# List all Secrets
kubectl get secret -n metlab-dev

# Verify auth-config and auth-secret exist
kubectl get configmap auth-config -n metlab-dev -o yaml
kubectl get secret auth-secret -n metlab-dev -o yaml
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

3. **RBAC**:
   - Use service accounts with minimal permissions
   - Implement pod security policies

### Monitoring

1. **Metrics**:
   - Enable Prometheus scraping (annotations already added)
   - Monitor request rate, latency, error rate
   - Track resource usage

2. **Logging**:
   - Centralize logs (ELK, Loki, cloud provider)
   - Structured logging with trace IDs
   - Log retention policies

3. **Alerting**:
   - Alert on pod restarts
   - Alert on high error rates
   - Alert on resource exhaustion

### High Availability

1. **Pod Disruption Budget**:
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: auth-pdb
  namespace: metlab-dev
spec:
  minAvailable: 1
  selector:
    matchLabels:
      service: auth
```

2. **Anti-Affinity**:
   - Spread pods across nodes
   - Avoid single point of failure

3. **Resource Quotas**:
   - Set namespace resource limits
   - Prevent resource exhaustion

## Environment-Specific Configurations

### Development (metlab-dev)
- 2 replicas minimum
- Relaxed resource limits
- Debug logging enabled
- Development database

### Staging (metlab-staging)
- 3 replicas minimum
- Production-like resources
- Info logging
- Staging database

### Production (metlab-production)
- 5 replicas minimum
- Strict resource limits
- Error/warn logging only
- Production database with replicas
- TLS enabled
- Network policies enforced

## References

- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Kubernetes Services](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [gRPC Health Checking Protocol](https://github.com/grpc/grpc/blob/master/doc/health-checking.md)
- [grpc_health_probe](https://github.com/grpc-ecosystem/grpc-health-probe)
