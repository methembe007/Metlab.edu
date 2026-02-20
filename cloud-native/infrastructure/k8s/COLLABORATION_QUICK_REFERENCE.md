# Collaboration Service - Quick Reference

## Quick Commands

### Deployment

```bash
# Deploy
kubectl apply -f cloud-native/infrastructure/k8s/collaboration.yaml

# Validate
./cloud-native/infrastructure/k8s/validate-collaboration-deployment.sh

# Check status
kubectl get all -n metlab-dev -l service=collaboration
```

### Monitoring

```bash
# View logs
kubectl logs -n metlab-dev -l service=collaboration --tail=50 -f

# Check pod status
kubectl get pods -n metlab-dev -l service=collaboration

# Check resource usage
kubectl top pods -n metlab-dev -l service=collaboration

# View events
kubectl get events -n metlab-dev --field-selector involvedObject.name=collaboration
```

### Debugging

```bash
# Port forward
kubectl port-forward -n metlab-dev svc/collaboration 50055:50055

# Test health
grpc_health_probe -addr=localhost:50055

# Shell into pod
kubectl exec -n metlab-dev -it <pod-name> -- /bin/sh

# Test database connection
kubectl exec -n metlab-dev <pod-name> -- nc -zv postgres 5432

# Test Redis connection
kubectl exec -n metlab-dev <pod-name> -- nc -zv redis 6379

# Test Redis pub/sub
kubectl exec -n metlab-dev <pod-name> -- redis-cli -h redis PING
```

### Scaling

```bash
# Manual scale
kubectl scale deployment collaboration --replicas=5 -n metlab-dev

# Check HPA status
kubectl get hpa collaboration-hpa -n metlab-dev

# Describe HPA
kubectl describe hpa collaboration-hpa -n metlab-dev
```

### Updates

```bash
# Update image
kubectl set image deployment/collaboration \
  collaboration=metlab/collaboration:v2.0.0 -n metlab-dev

# Check rollout status
kubectl rollout status deployment/collaboration -n metlab-dev

# Rollback
kubectl rollout undo deployment/collaboration -n metlab-dev

# Restart
kubectl rollout restart deployment/collaboration -n metlab-dev
```

### Configuration

```bash
# View ConfigMap
kubectl get configmap collaboration-config -n metlab-dev -o yaml

# Edit ConfigMap
kubectl edit configmap collaboration-config -n metlab-dev

# View Secret (base64 encoded)
kubectl get secret collaboration-secret -n metlab-dev -o yaml

# Decode secret value
kubectl get secret collaboration-secret -n metlab-dev -o jsonpath='{.data.DATABASE_PASSWORD}' | base64 -d
```

## Service Endpoints

| Endpoint | Port | Protocol | Purpose |
|----------|------|----------|---------|
| collaboration | 50055 | gRPC | Internal service communication |

## gRPC Methods

| Method | Description |
|--------|-------------|
| CreateStudyGroup | Create a new study group |
| JoinStudyGroup | Join an existing study group |
| ListStudyGroups | List available study groups |
| CreateChatRoom | Create a new chat room |
| SendMessage | Send a chat message |
| GetMessages | Retrieve message history |
| StreamMessages | Stream real-time messages |

## Configuration Keys

### ConfigMap (collaboration-config)

| Key | Default | Description |
|-----|---------|-------------|
| PORT | 50055 | gRPC port |
| DATABASE_HOST | postgres | Database host |
| DATABASE_PORT | 5432 | Database port |
| REDIS_HOST | redis | Redis host |
| REDIS_PORT | 6379 | Redis port |
| MAX_STUDY_GROUPS_PER_STUDENT | 5 | Max groups per student |
| MAX_STUDY_GROUP_MEMBERS | 10 | Max members per group |
| MAX_MESSAGE_LENGTH | 1000 | Max message characters |
| MAX_IMAGE_SIZE_MB | 5 | Max image size |
| MESSAGE_RETENTION_DAYS | 7 | Message retention period |
| CHAT_RATE_LIMIT_PER_MINUTE | 60 | Rate limit per user |

### Secret (collaboration-secret)

| Key | Description |
|-----|-------------|
| DATABASE_PASSWORD | PostgreSQL password |
| REDIS_PASSWORD | Redis password |

## Resource Limits

| Resource | Request | Limit |
|----------|---------|-------|
| Memory | 512Mi | 1Gi |
| CPU | 500m | 1000m |

## Auto-scaling

| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU | > 80% | Scale up |
| Memory | > 85% | Scale up |
| Min Replicas | 2 | - |
| Max Replicas | 10 | - |

## Health Checks

| Probe | Initial Delay | Period | Timeout | Failure Threshold |
|-------|---------------|--------|---------|-------------------|
| Liveness | 30s | 10s | 5s | 3 |
| Readiness | 10s | 5s | 3s | 3 |

## Dependencies

| Service | Port | Purpose |
|---------|------|---------|
| postgres | 5432 | Data persistence |
| redis | 6379 | Pub/sub messaging |
| api-gateway | 8080 | HTTP to gRPC translation |

## Common Issues

| Issue | Solution |
|-------|----------|
| Pods not starting | Check database/Redis connectivity |
| Messages not delivered | Verify Redis pub/sub channels |
| High memory usage | Check for connection leaks |
| Slow response | Check database query performance |
| Connection refused | Verify service is running and port is correct |

## Testing with grpcurl

```bash
# List services
grpcurl -plaintext localhost:50055 list

# List methods
grpcurl -plaintext localhost:50055 list collaboration.CollaborationService

# Create study group
grpcurl -plaintext \
  -d '{"class_id":"class-123","name":"Math Study","description":"Algebra help"}' \
  localhost:50055 collaboration.CollaborationService/CreateStudyGroup

# Send message
grpcurl -plaintext \
  -d '{"chat_room_id":"room-123","sender_id":"student-456","message_text":"Hello!"}' \
  localhost:50055 collaboration.CollaborationService/SendMessage

# Stream messages
grpcurl -plaintext \
  -d '{"chat_room_id":"room-123"}' \
  localhost:50055 collaboration.CollaborationService/StreamMessages
```

## Redis Pub/Sub Testing

```bash
# Connect to Redis
kubectl exec -n metlab-dev -it <redis-pod> -- redis-cli

# Subscribe to channel
SUBSCRIBE chat:room:room-123

# Publish message (from another terminal)
kubectl exec -n metlab-dev -it <redis-pod> -- redis-cli
PUBLISH chat:room:room-123 '{"message":"test"}'

# List active channels
PUBSUB CHANNELS chat:*

# Count subscribers
PUBSUB NUMSUB chat:room:room-123
```

## Logs Analysis

```bash
# Filter by level
kubectl logs -n metlab-dev -l service=collaboration | grep ERROR

# Filter by user
kubectl logs -n metlab-dev -l service=collaboration | grep "user_id:student-123"

# Filter by trace
kubectl logs -n metlab-dev -l service=collaboration | grep "trace_id:abc123"

# Count errors
kubectl logs -n metlab-dev -l service=collaboration | grep ERROR | wc -l

# Recent errors
kubectl logs -n metlab-dev -l service=collaboration --since=1h | grep ERROR
```

## Performance Metrics

```bash
# Check HPA metrics
kubectl get hpa collaboration-hpa -n metlab-dev -w

# Resource usage
kubectl top pods -n metlab-dev -l service=collaboration

# Connection count (from pod)
kubectl exec -n metlab-dev <pod-name> -- netstat -an | grep ESTABLISHED | wc -l
```

## Backup & Recovery

```bash
# Database backup (handled by PostgreSQL)
# See postgres deployment for backup configuration

# Export ConfigMap
kubectl get configmap collaboration-config -n metlab-dev -o yaml > collaboration-config-backup.yaml

# Export Secret
kubectl get secret collaboration-secret -n metlab-dev -o yaml > collaboration-secret-backup.yaml

# Restore ConfigMap
kubectl apply -f collaboration-config-backup.yaml

# Restore Secret
kubectl apply -f collaboration-secret-backup.yaml
```

## Network Testing

```bash
# Test from another pod
kubectl run -n metlab-dev test-pod --image=busybox --rm -it -- sh
nc -zv collaboration 50055

# Test DNS resolution
kubectl run -n metlab-dev test-pod --image=busybox --rm -it -- sh
nslookup collaboration

# Test from outside cluster (with port-forward)
kubectl port-forward -n metlab-dev svc/collaboration 50055:50055
grpc_health_probe -addr=localhost:50055
```

## Useful Aliases

```bash
# Add to ~/.bashrc or ~/.zshrc
alias k='kubectl'
alias kgp='kubectl get pods -n metlab-dev'
alias kgd='kubectl get deployments -n metlab-dev'
alias kgs='kubectl get services -n metlab-dev'
alias klogs='kubectl logs -n metlab-dev'
alias kexec='kubectl exec -n metlab-dev -it'
alias kcol='kubectl get all -n metlab-dev -l service=collaboration'
```

## Emergency Procedures

### Service Down

```bash
# 1. Check pod status
kubectl get pods -n metlab-dev -l service=collaboration

# 2. Check recent events
kubectl get events -n metlab-dev --sort-by='.lastTimestamp' | grep collaboration

# 3. Check logs
kubectl logs -n metlab-dev -l service=collaboration --tail=100

# 4. Restart if needed
kubectl rollout restart deployment/collaboration -n metlab-dev

# 5. Scale up if needed
kubectl scale deployment collaboration --replicas=5 -n metlab-dev
```

### High Load

```bash
# 1. Check current load
kubectl top pods -n metlab-dev -l service=collaboration

# 2. Check HPA status
kubectl get hpa collaboration-hpa -n metlab-dev

# 3. Manual scale if needed
kubectl scale deployment collaboration --replicas=10 -n metlab-dev

# 4. Check for slow queries
kubectl logs -n metlab-dev -l service=collaboration | grep "slow query"
```

### Database Connection Issues

```bash
# 1. Test connectivity
kubectl exec -n metlab-dev <pod-name> -- nc -zv postgres 5432

# 2. Check database status
kubectl get pods -n metlab-dev -l app=postgres

# 3. Check connection pool
kubectl logs -n metlab-dev -l service=collaboration | grep "connection pool"

# 4. Restart service
kubectl rollout restart deployment/collaboration -n metlab-dev
```

## Documentation Links

- [Full Deployment Guide](./COLLABORATION_DEPLOYMENT_README.md)
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [gRPC Health Check](https://github.com/grpc/grpc/blob/master/doc/health-checking.md)
- [Redis Pub/Sub](https://redis.io/topics/pubsub)
