# API Gateway Kubernetes Deployment

This document describes the Kubernetes deployment configuration for the API Gateway service.

## Overview

The API Gateway serves as the single entry point for all backend services, handling HTTP-to-gRPC translation, authentication, rate limiting, and request routing.

## Components

### 1. Deployment

**Configuration:**
- **Replicas:** 3 (minimum for high availability)
- **Image:** `metlab/api-gateway:latest`
- **Port:** 8080 (HTTP)

**Resource Allocation:**
- **Requests:** 512Mi memory, 500m CPU
- **Limits:** 1Gi memory, 1000m CPU

These resources are sized to handle moderate traffic while allowing room for auto-scaling.

**Environment Variables:**
- `PORT`: HTTP server port (8080)
- `AUTH_SERVICE_ADDR`: Auth service gRPC endpoint (auth:50051)
- `VIDEO_SERVICE_ADDR`: Video service gRPC endpoint (video:50052)
- `HOMEWORK_SERVICE_ADDR`: Homework service gRPC endpoint (homework:50053)
- `ANALYTICS_SERVICE_ADDR`: Analytics service gRPC endpoint (analytics:50054)
- `COLLABORATION_SERVICE_ADDR`: Collaboration service gRPC endpoint (collaboration:50055)
- `PDF_SERVICE_ADDR`: PDF service gRPC endpoint (pdf:50056)
- `REDIS_ADDR`: Redis connection for rate limiting (redis:6379)

**Health Checks:**

**Liveness Probe:**
- Endpoint: `/health`
- Initial Delay: 30 seconds
- Period: 10 seconds
- Timeout: 5 seconds
- Failure Threshold: 3

**Readiness Probe:**
- Endpoint: `/ready`
- Initial Delay: 5 seconds
- Period: 5 seconds
- Timeout: 3 seconds
- Failure Threshold: 3

### 2. Service

**Type:** ClusterIP (internal only, exposed via Ingress)

**Port Configuration:**
- Service Port: 8080
- Target Port: 8080
- Protocol: TCP

### 3. HorizontalPodAutoscaler (HPA)

The HPA automatically scales the API Gateway based on resource utilization.

**Scaling Configuration:**
- **Min Replicas:** 3
- **Max Replicas:** 20

**Metrics:**
- **CPU:** Scale when average utilization exceeds 80%
- **Memory:** Scale when average utilization exceeds 85%

**Scaling Behavior:**

**Scale Up:**
- No stabilization window (immediate scaling)
- Can scale up by 100% or add 4 pods per 30 seconds (whichever is greater)

**Scale Down:**
- Stabilization window: 300 seconds (5 minutes)
- Can scale down by 50% per 60 seconds

This configuration ensures rapid response to traffic spikes while preventing flapping during scale-down.

### 4. Ingress

The Ingress resource routes external traffic to the API Gateway and Frontend services.

**Host:** `metlab.local` (for local development)

**Annotations:**
- `nginx.ingress.kubernetes.io/ssl-redirect: "false"` - Disable SSL redirect for local dev
- `nginx.ingress.kubernetes.io/rewrite-target: /$2` - Rewrite URL paths
- `nginx.ingress.kubernetes.io/use-regex: "true"` - Enable regex path matching
- `nginx.ingress.kubernetes.io/rate-limit: "100"` - 100 requests per minute per IP
- `nginx.ingress.kubernetes.io/proxy-body-size: "50m"` - Allow large file uploads
- `nginx.ingress.kubernetes.io/proxy-*-timeout: "60"` - 60 second timeouts

**Routing Rules:**
- `/api/*` → API Gateway (port 8080)
- `/*` → Frontend (port 3000)

## Deployment

### Prerequisites

1. Minikube running with Nginx Ingress addon enabled:
   ```bash
   minikube addons enable ingress
   minikube addons enable metrics-server
   ```

2. All backend services deployed (auth, video, homework, analytics, collaboration, pdf)

3. Redis deployed for rate limiting

### Deploy

```bash
# Apply the API Gateway deployment
kubectl apply -f cloud-native/infrastructure/k8s/api-gateway.yaml

# Verify deployment
kubectl get deployment api-gateway -n metlab-dev
kubectl get pods -n metlab-dev -l service=api-gateway
kubectl get svc api-gateway -n metlab-dev
kubectl get hpa api-gateway-hpa -n metlab-dev
kubectl get ingress metlab-ingress -n metlab-dev
```

### Verify Health

```bash
# Check pod status
kubectl get pods -n metlab-dev -l service=api-gateway

# Check logs
kubectl logs -n metlab-dev -l service=api-gateway --tail=50

# Test health endpoint (from within cluster)
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://api-gateway:8080/health

# Test via Ingress
curl http://$(minikube ip)/api/health
```

### Access the Application

```bash
# Get Minikube IP
minikube ip

# Add to /etc/hosts (Linux/Mac) or C:\Windows\System32\drivers\etc\hosts (Windows)
<minikube-ip> metlab.local

# Access the application
# Frontend: http://metlab.local
# API: http://metlab.local/api
```

## Monitoring

### Check HPA Status

```bash
# View HPA metrics
kubectl get hpa api-gateway-hpa -n metlab-dev

# Watch HPA in real-time
kubectl get hpa api-gateway-hpa -n metlab-dev --watch

# Detailed HPA information
kubectl describe hpa api-gateway-hpa -n metlab-dev
```

### View Metrics

```bash
# CPU and memory usage
kubectl top pods -n metlab-dev -l service=api-gateway

# Node metrics
kubectl top nodes
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod -n metlab-dev -l service=api-gateway

# Check logs
kubectl logs -n metlab-dev -l service=api-gateway --tail=100
```

### HPA Not Scaling

```bash
# Verify metrics-server is running
kubectl get deployment metrics-server -n kube-system

# Check HPA status
kubectl describe hpa api-gateway-hpa -n metlab-dev

# Verify resource requests are set (required for HPA)
kubectl get deployment api-gateway -n metlab-dev -o yaml | grep -A 5 resources
```

### Ingress Not Working

```bash
# Check Ingress status
kubectl describe ingress metlab-ingress -n metlab-dev

# Verify Nginx Ingress Controller is running
kubectl get pods -n ingress-nginx

# Check Ingress Controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

### Service Connection Issues

```bash
# Test service connectivity from a debug pod
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n metlab-dev -- \
  curl http://api-gateway:8080/health

# Check service endpoints
kubectl get endpoints api-gateway -n metlab-dev
```

## Load Testing

To test auto-scaling behavior:

```bash
# Install hey (HTTP load generator)
# https://github.com/rakyll/hey

# Generate load
hey -z 5m -c 50 -q 10 http://metlab.local/api/health

# Watch HPA scale up
kubectl get hpa api-gateway-hpa -n metlab-dev --watch
```

## Production Considerations

For production deployment, update the following:

1. **Namespace:** Change from `metlab-dev` to `metlab-production`

2. **Ingress:**
   - Enable SSL redirect: `nginx.ingress.kubernetes.io/ssl-redirect: "true"`
   - Configure TLS certificate
   - Update host to production domain

3. **Resources:**
   - Adjust based on actual load patterns
   - Consider using node affinity for critical pods

4. **HPA:**
   - Fine-tune scaling thresholds based on production metrics
   - Consider custom metrics (e.g., request rate, latency)

5. **Security:**
   - Add network policies to restrict pod-to-pod communication
   - Use secrets for sensitive environment variables
   - Enable pod security policies

## Requirements Satisfied

This deployment satisfies the following requirements:

- **1.1:** Auto-scaling when traffic reaches 80% capacity (HPA configuration)
- **1.3:** Load balancing across backend instances (Service + Ingress)
- **16.1:** Kubernetes deployment with health checks
- **16.5:** Resource limits and health/readiness probes configured
