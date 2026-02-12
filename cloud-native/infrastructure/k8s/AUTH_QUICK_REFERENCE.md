# Auth Service - Quick Reference

## Quick Deploy

```bash
# Deploy everything
kubectl apply -f cloud-native/infrastructure/k8s/auth.yaml

# Verify
kubectl get all -n metlab-dev -l service=auth
```

## Quick Commands

### Status Check
```bash
# Get all auth resources
kubectl get all -n metlab-dev -l service=auth

# Get pods
kubectl get pods -n metlab-dev -l service=auth

# Get deployment
kubectl get deployment auth -n metlab-dev

# Get service
kubectl get svc auth -n metlab-dev

# Get HPA
kubectl get hpa auth-hpa -n metlab-dev
```

### Logs
```bash
# Tail logs
kubectl logs -n metlab-dev -l service=auth --tail=50 -f

# Get logs from specific pod
kubectl logs -n metlab-dev <pod-name>

# Get previous logs (if pod restarted)
kubectl logs -n metlab-dev <pod-name> --previous
```

### Debugging
```bash
# Describe deployment
kubectl describe deployment auth -n metlab-dev

# Describe pod
kubectl describe pod -n metlab-dev <pod-name>

# Exec into pod
kubectl exec -it -n metlab-dev <pod-name> -- /bin/sh

# Port forward for local testing
kubectl port-forward -n metlab-dev svc/auth 50051:50051
```

### Configuration
```bash
# View ConfigMap
kubectl get configmap auth-config -n metlab-dev -o yaml

# Edit ConfigMap
kubectl edit configmap auth-config -n metlab-dev

# View Secret (base64 encoded)
kubectl get secret auth-secret -n metlab-dev -o yaml

# Decode secret value
kubectl get secret auth-secret -n metlab-dev -o jsonpath='{.data.JWT_SECRET}' | base64 -d
```

### Scaling
```bash
# Manual scale
kubectl scale deployment auth -n metlab-dev --replicas=5

# Check HPA status
kubectl get hpa auth-hpa -n metlab-dev

# Describe HPA
kubectl describe hpa auth-hpa -n metlab-dev
```

### Updates
```bash
# Update image
kubectl set image deployment/auth auth=metlab/auth:v2 -n metlab-dev

# Rollout status
kubectl rollout status deployment/auth -n metlab-dev

# Rollout history
kubectl rollout history deployment/auth -n metlab-dev

# Rollback
kubectl rollout undo deployment/auth -n metlab-dev

# Restart deployment
kubectl rollout restart deployment/auth -n metlab-dev
```

### Cleanup
```bash
# Delete all auth resources
kubectl delete -f cloud-native/infrastructure/k8s/auth.yaml

# Or delete individually
kubectl delete deployment auth -n metlab-dev
kubectl delete service auth -n metlab-dev
kubectl delete hpa auth-hpa -n metlab-dev
kubectl delete configmap auth-config -n metlab-dev
kubectl delete secret auth-secret -n metlab-dev
```

## Health Check

```bash
# Port forward
kubectl port-forward -n metlab-dev svc/auth 50051:50051

# Test with grpcurl (in another terminal)
grpcurl -plaintext localhost:50051 grpc.health.v1.Health/Check

# Expected response:
# {
#   "status": "SERVING"
# }
```

## Common Issues

### Pods not starting
```bash
# Check events
kubectl describe pod -n metlab-dev <pod-name>

# Check logs
kubectl logs -n metlab-dev <pod-name>

# Common causes:
# - Image pull errors
# - ConfigMap/Secret not found
# - Database connection issues
```

### Health checks failing
```bash
# Check if grpc_health_probe is in image
kubectl exec -it -n metlab-dev <pod-name> -- which grpc_health_probe

# Test health check manually
kubectl exec -it -n metlab-dev <pod-name> -- grpc_health_probe -addr=:50051
```

### Database connection issues
```bash
# Check if PostgreSQL is running
kubectl get pods -n metlab-dev -l app=postgres

# Test connection from auth pod
kubectl exec -it -n metlab-dev <auth-pod-name> -- /bin/sh
# nc -zv postgres 5432
```

## Resource URLs

- **Service DNS**: `auth.metlab-dev.svc.cluster.local:50051`
- **Service Short**: `auth:50051` (within same namespace)
- **ConfigMap**: `auth-config`
- **Secret**: `auth-secret`

## Monitoring

```bash
# Watch pods
kubectl get pods -n metlab-dev -l service=auth -w

# Watch HPA
kubectl get hpa auth-hpa -n metlab-dev -w

# Top pods (resource usage)
kubectl top pods -n metlab-dev -l service=auth
```

## Environment Variables

Available in pods:
- `PORT`: 50051
- `ENV`: development
- `DATABASE_HOST`: postgres
- `DATABASE_PORT`: 5432
- `DATABASE_USER`: postgres
- `DATABASE_NAME`: metlab
- `DATABASE_PASSWORD`: (from secret)
- `JWT_SECRET`: (from secret)
- `JWT_EXPIRY_HOURS`: 24
- `STUDENT_EXPIRY_DAYS`: 7
- `MAX_LOGIN_ATTEMPTS`: 5
- `LOCKOUT_MINUTES`: 30
- `DATABASE_URL`: (computed)
