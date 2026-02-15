# API Gateway Quick Reference

Quick commands for managing the API Gateway deployment.

## Deploy

```bash
# Apply the deployment
kubectl apply -f cloud-native/infrastructure/k8s/api-gateway.yaml

# Verify deployment
kubectl get all -n metlab-dev -l service=api-gateway
```

## Validate

```bash
# Run validation script (Linux/Mac)
bash cloud-native/infrastructure/k8s/validate-api-gateway-deployment.sh

# Run validation script (Windows)
powershell -ExecutionPolicy Bypass -File cloud-native/infrastructure/k8s/validate-api-gateway-deployment.ps1
```

## Monitor

```bash
# Watch pods
kubectl get pods -n metlab-dev -l service=api-gateway -w

# View logs
kubectl logs -n metlab-dev -l service=api-gateway -f

# Check HPA status
kubectl get hpa api-gateway-hpa -n metlab-dev -w

# View metrics
kubectl top pods -n metlab-dev -l service=api-gateway
```

## Test

```bash
# Test health endpoint (from within cluster)
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n metlab-dev -- \
  curl http://api-gateway:8080/health

# Test via Ingress (after adding metlab.local to /etc/hosts)
curl http://metlab.local/api/health
```

## Scale

```bash
# Manual scaling (overrides HPA temporarily)
kubectl scale deployment api-gateway -n metlab-dev --replicas=5

# View HPA metrics
kubectl describe hpa api-gateway-hpa -n metlab-dev
```

## Troubleshoot

```bash
# Describe deployment
kubectl describe deployment api-gateway -n metlab-dev

# Describe pods
kubectl describe pods -n metlab-dev -l service=api-gateway

# Check events
kubectl get events -n metlab-dev --sort-by='.lastTimestamp'

# Check Ingress
kubectl describe ingress metlab-ingress -n metlab-dev

# Test service connectivity
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n metlab-dev -- \
  curl -v http://api-gateway:8080/health
```

## Update

```bash
# Update image
kubectl set image deployment/api-gateway api-gateway=metlab/api-gateway:v1.2.3 -n metlab-dev

# Rollout status
kubectl rollout status deployment/api-gateway -n metlab-dev

# Rollback
kubectl rollout undo deployment/api-gateway -n metlab-dev
```

## Delete

```bash
# Delete all resources
kubectl delete -f cloud-native/infrastructure/k8s/api-gateway.yaml

# Or delete individually
kubectl delete deployment api-gateway -n metlab-dev
kubectl delete service api-gateway -n metlab-dev
kubectl delete hpa api-gateway-hpa -n metlab-dev
kubectl delete ingress metlab-ingress -n metlab-dev
```

## Access Application

```bash
# Get Minikube IP
minikube ip

# Add to hosts file (Linux/Mac)
echo "$(minikube ip) metlab.local" | sudo tee -a /etc/hosts

# Add to hosts file (Windows - run as Administrator)
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "$(minikube ip) metlab.local"

# Access frontend
curl http://metlab.local

# Access API
curl http://metlab.local/api/health
```

## Load Testing

```bash
# Install hey (if not already installed)
# https://github.com/rakyll/hey

# Generate load to test auto-scaling
hey -z 5m -c 50 -q 10 http://metlab.local/api/health

# Watch HPA scale up
kubectl get hpa api-gateway-hpa -n metlab-dev --watch
```

## Configuration

### Environment Variables

The API Gateway uses the following environment variables:

- `PORT`: HTTP server port (default: 8080)
- `AUTH_SERVICE_ADDR`: Auth service gRPC endpoint
- `VIDEO_SERVICE_ADDR`: Video service gRPC endpoint
- `HOMEWORK_SERVICE_ADDR`: Homework service gRPC endpoint
- `ANALYTICS_SERVICE_ADDR`: Analytics service gRPC endpoint
- `COLLABORATION_SERVICE_ADDR`: Collaboration service gRPC endpoint
- `PDF_SERVICE_ADDR`: PDF service gRPC endpoint
- `REDIS_ADDR`: Redis connection for rate limiting

### Resource Limits

- **Requests:** 512Mi memory, 500m CPU
- **Limits:** 1Gi memory, 1000m CPU

### Auto-scaling

- **Min Replicas:** 3
- **Max Replicas:** 20
- **CPU Target:** 80%
- **Memory Target:** 85%

### Health Checks

- **Liveness:** `/health` (30s initial delay, 10s period)
- **Readiness:** `/ready` (5s initial delay, 5s period)

## Common Issues

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n metlab-dev -l service=api-gateway

# View pod events
kubectl describe pod <pod-name> -n metlab-dev

# Check logs
kubectl logs <pod-name> -n metlab-dev
```

### HPA Not Scaling

```bash
# Verify metrics-server is running
kubectl get deployment metrics-server -n kube-system

# Enable metrics-server addon (Minikube)
minikube addons enable metrics-server

# Check HPA status
kubectl describe hpa api-gateway-hpa -n metlab-dev
```

### Ingress Not Working

```bash
# Enable Ingress addon (Minikube)
minikube addons enable ingress

# Check Ingress Controller
kubectl get pods -n ingress-nginx

# View Ingress details
kubectl describe ingress metlab-ingress -n metlab-dev

# Check Ingress Controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

### Service Connection Issues

```bash
# Check service endpoints
kubectl get endpoints api-gateway -n metlab-dev

# Test from debug pod
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n metlab-dev -- \
  curl -v http://api-gateway:8080/health
```
