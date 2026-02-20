# Collaboration Service Deployment Guide

This document provides comprehensive information about deploying and managing the Collaboration Service in the Metlab cloud-native architecture.

## Overview

The Collaboration Service manages study groups and real-time chat functionality for students. It enables:
- Study group creation and management
- Student collaboration within class boundaries
- Real-time chat messaging with Redis pub/sub
- Image attachments in chat messages
- Message history retention

## Architecture

### Components

1. **Deployment**: Manages Collaboration Service pods with rolling updates
2. **Service**: Exposes gRPC endpoints for internal communication
3. **ConfigMap**: Stores non-sensitive configuration
4. **Secret**: Stores sensitive credentials
5. **HorizontalPodAutoscaler**: Auto-scales based on CPU and memory usage

### Dependencies

- **PostgreSQL**: Stores study groups, members, chat rooms, and messages
- **Redis**: Provides pub/sub for real-time message distribution
- **API Gateway**: Routes HTTP requests to this service

### Port Configuration

- **gRPC Port**: 50055
- **Protocol**: gRPC over HTTP/2

## Configuration

### ConfigMap (collaboration-config)

| Key | Default Value | Description |
|-----|---------------|-------------|
| PORT | 50055 | gRPC server port |
| ENV | development | Environment (development/staging/production) |
| DATABASE_HOST | postgres | PostgreSQL host |
| DATABASE_PORT | 5432 | PostgreSQL port |
| DATABASE_USER | postgres | Database user |
| DATABASE_NAME | metlab | Database name |
| REDIS_HOST | redis | Redis host |
| REDIS_PORT | 6379 | Redis port |
| REDIS_DB | 0 | Redis database number |
| REDIS_POOL_SIZE | 10 | Redis connection pool size |
| MAX_STUDY_GROUPS_PER_STUDENT | 5 | Maximum study groups per student |
| MAX_STUDY_GROUP_MEMBERS | 10 | Maximum members per study group |
| MAX_MESSAGE_LENGTH | 1000 | Maximum characters per message |
| MAX_IMAGE_SIZE_MB | 5 | Maximum image attachment size |
| MESSAGE_RETENTION_DAYS | 7 | Days to retain chat messages |
| CHAT_RATE_LIMIT_PER_MINUTE | 60 | Messages per minute per user |

### Secret (collaboration-secret)

| Key | Description |
|-----|-------------|
| DATABASE_PASSWORD | PostgreSQL password |
| REDIS_PASSWORD | Redis password (empty for no auth) |

## Deployment

### Prerequisites

1. Kubernetes cluster running (Minikube for local development)
2. `kubectl` configured to access the cluster
3. Namespace `metlab-dev` created
4. PostgreSQL deployed and accessible
5. Redis deployed and accessible

### Deploy the Service

```bash
# Apply the deployment manifest
kubectl apply -f cloud-native/infrastructure/k8s/collaboration.yaml

# Verify deployment
kubectl get deployment collaboration -n metlab-dev

# Check pod status
kubectl get pods -n metlab-dev -l service=collaboration

# View logs
kubectl logs -n metlab-dev -l service=collaboration --tail=50
```

### Validation

Run the validation script to verify the deployment:

**Linux/Mac:**
```bash
chmod +x cloud-native/infrastructure/k8s/validate-collaboration-deployment.sh
./cloud-native/infrastructure/k8s/validate-collaboration-deployment.sh
```

**Windows (PowerShell):**
```powershell
.\cloud-native\infrastructure\k8s\validate-collaboration-deployment.ps1
```

## Resource Allocation

### Pod Resources

- **Requests**: 512Mi memory, 500m CPU
- **Limits**: 1Gi memory, 1000m CPU

### Scaling Configuration

- **Min Replicas**: 2
- **Max Replicas**: 10
- **Scale Up Trigger**: CPU > 80% or Memory > 85%
- **Scale Down Trigger**: CPU < 80% and Memory < 85%

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

## Redis Pub/Sub Configuration

The Collaboration Service uses Redis pub/sub for real-time message distribution:

### Channel Naming Convention

- Chat room messages: `chat:room:{room_id}`
- Study group notifications: `studygroup:{group_id}`

### Connection Pool

- Pool size: 10 connections
- Idle timeout: 5 minutes
- Max retries: 3

### Message Format

```json
{
  "id": "message-uuid",
  "room_id": "room-uuid",
  "sender_id": "user-uuid",
  "sender_name": "Student Name",
  "message_text": "Hello, world!",
  "image_url": "https://...",
  "sent_at": 1234567890
}
```

## Database Schema

### Tables

1. **study_groups**: Study group information
2. **study_group_members**: Group membership
3. **chat_rooms**: Chat room information
4. **chat_messages**: Message history

### Indexes

- `idx_chat_messages_room_time`: Fast message retrieval by room and time
- `idx_study_groups_class`: Fast group lookup by class
- `idx_study_group_members_student`: Fast membership lookup

## Monitoring

### Metrics

The service exposes Prometheus metrics on the gRPC port:

- `grpc_server_handled_total`: Total gRPC requests
- `grpc_server_handling_seconds`: Request duration
- `redis_pool_active_connections`: Active Redis connections
- `chat_messages_sent_total`: Total messages sent
- `study_groups_created_total`: Total study groups created

### Logs

Structured JSON logs include:

- Timestamp
- Log level
- Service name
- Trace ID
- User ID
- Message
- Additional context

### Alerts

Recommended alerts:

- Pod restart count > 3 in 10 minutes
- Error rate > 5%
- Redis connection failures
- Message delivery latency > 2 seconds

## Troubleshooting

### Common Issues

#### Pods Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n metlab-dev

# Check logs
kubectl logs <pod-name> -n metlab-dev

# Common causes:
# - Database connection failure
# - Redis connection failure
# - Missing ConfigMap or Secret
```

#### Database Connection Issues

```bash
# Test database connectivity from pod
kubectl exec -n metlab-dev <pod-name> -- nc -zv postgres 5432

# Check database credentials
kubectl get secret collaboration-secret -n metlab-dev -o yaml

# Verify database is running
kubectl get pods -n metlab-dev -l app=postgres
```

#### Redis Connection Issues

```bash
# Test Redis connectivity from pod
kubectl exec -n metlab-dev <pod-name> -- nc -zv redis 6379

# Test Redis with redis-cli
kubectl exec -n metlab-dev <pod-name> -- redis-cli -h redis PING

# Check Redis pod status
kubectl get pods -n metlab-dev -l app=redis
```

#### Real-time Messages Not Delivered

```bash
# Check Redis pub/sub
kubectl exec -n metlab-dev -it <redis-pod> -- redis-cli
> PUBSUB CHANNELS chat:*
> PUBSUB NUMSUB chat:room:<room-id>

# Check service logs for pub/sub errors
kubectl logs -n metlab-dev -l service=collaboration | grep "pub/sub"

# Verify multiple pods can communicate via Redis
kubectl exec -n metlab-dev <pod-1> -- redis-cli -h redis PUBLISH test "hello"
kubectl exec -n metlab-dev <pod-2> -- redis-cli -h redis SUBSCRIBE test
```

#### High Memory Usage

```bash
# Check memory usage
kubectl top pods -n metlab-dev -l service=collaboration

# Check for memory leaks in logs
kubectl logs -n metlab-dev <pod-name> | grep -i "memory\|oom"

# Increase memory limits if needed
kubectl edit deployment collaboration -n metlab-dev
```

### Debug Commands

```bash
# Port forward for local testing
kubectl port-forward -n metlab-dev svc/collaboration 50055:50055

# Test gRPC health
grpc_health_probe -addr=localhost:50055

# Execute shell in pod
kubectl exec -n metlab-dev -it <pod-name> -- /bin/sh

# View all resources
kubectl get all -n metlab-dev -l service=collaboration

# Restart deployment
kubectl rollout restart deployment/collaboration -n metlab-dev

# View rollout status
kubectl rollout status deployment/collaboration -n metlab-dev

# View rollout history
kubectl rollout history deployment/collaboration -n metlab-dev
```

## Security

### Network Policies

Consider implementing network policies to restrict traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: collaboration-network-policy
  namespace: metlab-dev
spec:
  podSelector:
    matchLabels:
      service: collaboration
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          service: api-gateway
    ports:
    - protocol: TCP
      port: 50055
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

### Secret Management

- Rotate database password quarterly
- Use Kubernetes Secrets for sensitive data
- Never commit secrets to version control
- Consider using external secret management (Vault, AWS Secrets Manager)

## Performance Tuning

### Database Connection Pool

Adjust based on load:

```go
// In service code
config.MinConns = 10
config.MaxConns = 100
config.MaxConnLifetime = time.Hour
config.MaxConnIdleTime = 30 * time.Minute
```

### Redis Connection Pool

Tune for real-time performance:

```go
// In service code
RedisPoolSize = 20  // Increase for high message volume
IdleTimeout = 5 * time.Minute
MaxRetries = 3
```

### Message Batching

For high-volume chat rooms, consider batching messages:

```go
// Batch messages every 100ms
BatchInterval = 100 * time.Millisecond
MaxBatchSize = 50
```

## Maintenance

### Backup

Database tables are backed up with PostgreSQL:
- Frequency: Every 6 hours
- Retention: 30 days

### Updates

Rolling update strategy ensures zero downtime:

```bash
# Update image
kubectl set image deployment/collaboration \
  collaboration=metlab/collaboration:v2.0.0 \
  -n metlab-dev

# Monitor rollout
kubectl rollout status deployment/collaboration -n metlab-dev

# Rollback if needed
kubectl rollout undo deployment/collaboration -n metlab-dev
```

### Scaling

Manual scaling:

```bash
# Scale to 5 replicas
kubectl scale deployment collaboration --replicas=5 -n metlab-dev

# Verify
kubectl get deployment collaboration -n metlab-dev
```

## Integration Testing

### Test Study Group Creation

```bash
# Port forward
kubectl port-forward -n metlab-dev svc/collaboration 50055:50055

# Use grpcurl to test
grpcurl -plaintext \
  -d '{"class_id":"class-123","name":"Math Study Group","description":"Help with algebra"}' \
  localhost:50055 collaboration.CollaborationService/CreateStudyGroup
```

### Test Chat Messaging

```bash
# Send a message
grpcurl -plaintext \
  -d '{"chat_room_id":"room-123","sender_id":"student-456","message_text":"Hello!"}' \
  localhost:50055 collaboration.CollaborationService/SendMessage

# Stream messages
grpcurl -plaintext \
  -d '{"chat_room_id":"room-123"}' \
  localhost:50055 collaboration.CollaborationService/StreamMessages
```

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [gRPC Health Checking Protocol](https://github.com/grpc/grpc/blob/master/doc/health-checking.md)
- [Redis Pub/Sub](https://redis.io/topics/pubsub)
- [Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

## Support

For issues or questions:
1. Check logs: `kubectl logs -n metlab-dev -l service=collaboration`
2. Run validation script
3. Review this documentation
4. Contact the DevOps team
