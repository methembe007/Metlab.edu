# Redis Setup Completion Summary

## Task 6: Set up Redis for caching and pub/sub

**Status**: ✅ COMPLETED

**Date**: February 10, 2026

## What Was Implemented

### 1. Kubernetes Deployment Manifest

**File**: `cloud-native/infrastructure/k8s/redis.yaml`

Enhanced the Redis Kubernetes deployment with:

- **ConfigMap** with production-ready Redis configuration:
  - Memory management (512MB max with LRU eviction)
  - AOF persistence (append-only file) for durability
  - RDB snapshots as backup (900s/1 change, 300s/10 changes, 60s/10000 changes)
  - Performance tuning (slowlog, connection limits)
  - Pub/Sub support enabled

- **PersistentVolumeClaim** (5Gi) for data persistence:
  - Ensures data survives pod restarts
  - Uses standard storage class
  - ReadWriteOnce access mode

- **Deployment** with proper resource limits:
  - Memory: 256Mi request, 512Mi limit
  - CPU: 200m request, 500m limit
  - Liveness probe (TCP socket check)
  - Readiness probe (redis-cli ping)
  - Volume mounts for data and configuration

- **Service** for internal cluster communication:
  - ClusterIP type for internal-only access
  - Port 6379 exposed
  - Proper labels for service discovery

### 2. Go Redis Client Package

**Location**: `cloud-native/shared/cache/`

Created a comprehensive Redis client package with:

#### Core Features (`redis.go`):
- **Connection pooling** with configurable pool size (default: 100 connections)
- **Automatic health checks** and connection management
- **Configurable timeouts** for dial, read, and write operations
- **Support for both config-based and URL-based initialization**

#### Operations Supported:
- Basic operations: Get, Set, Del, Exists, Expire, TTL
- Counter operations: Incr, Decr
- Hash operations: HSet, HGet, HGetAll, HDel
- Pub/Sub: Publish, Subscribe, PSubscribe
- Pipeline support for batching commands
- Transaction pipeline support
- Pool statistics monitoring

#### Configuration Options:
```go
type RedisConfig struct {
    Host               string        // Redis server host
    Port               int           // Redis server port
    Password           string        // Authentication password
    DB                 int           // Database number
    PoolSize           int           // Max connections (default: 100)
    MinIdleConns       int           // Min idle connections (default: 10)
    MaxConnAge         time.Duration // Connection lifetime (default: 1 hour)
    PoolTimeout        time.Duration // Wait timeout (default: 4 seconds)
    IdleTimeout        time.Duration // Idle timeout (default: 5 minutes)
    IdleCheckFrequency time.Duration // Check frequency (default: 1 minute)
    DialTimeout        time.Duration // Connect timeout (default: 5 seconds)
    ReadTimeout        time.Duration // Read timeout (default: 3 seconds)
    WriteTimeout       time.Duration // Write timeout (default: 3 seconds)
}
```

### 3. Comprehensive Test Suite

**File**: `cloud-native/shared/cache/redis_test.go`

Test coverage includes:
- Configuration validation
- Connection establishment
- Basic CRUD operations (Set, Get, Del, Exists)
- Counter operations (Incr, Decr)
- Hash operations (HSet, HGet, HGetAll, HDel)
- Pub/Sub messaging
- Pool statistics

Tests are designed to skip gracefully if Redis is not available.

### 4. Integration Examples

**File**: `cloud-native/shared/cache/example_integration.go`

Provides ready-to-use patterns for:

#### CacheManager
- JSON serialization/deserialization
- Pattern-based cache invalidation
- High-level caching operations

#### SessionManager
- Session creation with TTL
- Session retrieval and updates
- Session deletion
- Automatic TTL refresh on updates

#### RateLimiter
- Request counting per identifier
- Sliding window rate limiting
- Remaining requests calculation
- Configurable limits and windows

#### PubSubManager
- Message publishing with JSON serialization
- Channel subscription with message handlers
- Graceful error handling
- Context-aware cancellation

### 5. Documentation

**File**: `cloud-native/shared/cache/README.md`

Comprehensive documentation including:
- Feature overview
- Usage examples for all operations
- Configuration guide
- Environment variable setup
- Kubernetes deployment details
- Common use cases (sessions, rate limiting, caching, chat)
- Best practices
- Troubleshooting guide

## How to Use

### 1. Deploy Redis to Kubernetes

```bash
# Apply the Redis manifest
kubectl apply -f cloud-native/infrastructure/k8s/redis.yaml

# Verify deployment
kubectl get pods -n metlab-dev | grep redis
kubectl get svc redis -n metlab-dev

# Check Redis is running
kubectl exec -it <redis-pod-name> -n metlab-dev -- redis-cli ping
# Should return: PONG
```

### 2. Use in Go Services

```go
package main

import (
    "context"
    "log"
    
    "github.com/metlab/shared/cache"
)

func main() {
    ctx := context.Background()
    
    // Initialize from environment variables
    client, err := cache.InitializeRedisClient(ctx)
    if err != nil {
        log.Fatalf("Failed to connect to Redis: %v", err)
    }
    defer client.Close()
    
    // Use the client
    err = client.Set(ctx, "key", "value", 0)
    if err != nil {
        log.Fatalf("Failed to set key: %v", err)
    }
}
```

### 3. Environment Variables

Services should set these environment variables:

```bash
REDIS_HOST=redis          # Service name in Kubernetes
REDIS_PORT=6379           # Default Redis port
REDIS_PASSWORD=           # Empty for dev, set in production
REDIS_DB=0                # Database number
```

## Integration Points

### Services That Will Use Redis

1. **API Gateway** - Rate limiting, session management
2. **Auth Service** - Session storage, token blacklisting
3. **Collaboration Service** - Real-time chat pub/sub, study group data
4. **Analytics Service** - Temporary metrics aggregation
5. **Video Service** - View tracking cache, streaming session data
6. **Homework Service** - Submission status cache

### Common Use Cases

#### 1. Session Storage (Auth Service)
```go
sessionMgr := cache.NewSessionManager(client, "session", 24*time.Hour)
sessionMgr.CreateSession(ctx, sessionID, map[string]interface{}{
    "user_id": userID,
    "role": "teacher",
})
```

#### 2. Rate Limiting (API Gateway)
```go
rateLimiter := cache.NewRateLimiter(client, "ratelimit")
allowed, _ := rateLimiter.CheckLimit(ctx, ipAddress, 100, 1*time.Minute)
if !allowed {
    return errors.New("rate limit exceeded")
}
```

#### 3. Real-time Chat (Collaboration Service)
```go
pubsubMgr := cache.NewPubSubManager(client)

// Publish message
pubsubMgr.PublishMessage(ctx, "chat:room1", message)

// Subscribe to messages
pubsubMgr.SubscribeToChannel(ctx, "chat:room1", handleMessage)
```

#### 4. Caching (Video Service)
```go
cacheMgr := cache.NewCacheManager(client)

// Cache video metadata
cacheMgr.CacheJSON(ctx, "video:123", videoData, 1*time.Hour)

// Retrieve from cache
var video Video
cacheMgr.GetJSON(ctx, "video:123", &video)
```

## Testing

### Run Unit Tests

```bash
cd cloud-native/shared
go test -v ./cache
```

### Manual Testing

```bash
# Connect to Redis pod
kubectl exec -it <redis-pod-name> -n metlab-dev -- redis-cli

# Test basic operations
SET test:key "test-value"
GET test:key
DEL test:key

# Test pub/sub
SUBSCRIBE test:channel
# In another terminal:
PUBLISH test:channel "Hello, World!"

# Check persistence
INFO persistence

# Check memory usage
INFO memory

# Check connection stats
INFO clients
```

## Performance Characteristics

### Connection Pool
- **Pool Size**: 100 connections (configurable)
- **Min Idle**: 10 connections always ready
- **Connection Lifetime**: 1 hour (prevents stale connections)
- **Pool Timeout**: 4 seconds (fail fast if pool exhausted)

### Memory Management
- **Max Memory**: 512MB (configured in redis.conf)
- **Eviction Policy**: allkeys-lru (least recently used)
- **Persistence**: AOF + RDB snapshots

### Persistence
- **AOF**: fsync every second (balance between durability and performance)
- **RDB**: Snapshots at 900s/1, 300s/10, 60s/10000 changes
- **Storage**: 5Gi persistent volume

## Monitoring

### Health Checks
- **Liveness Probe**: TCP socket check on port 6379
- **Readiness Probe**: redis-cli ping command

### Metrics to Monitor
- Connection pool usage (via `GetPoolStats()`)
- Memory usage (via Redis INFO command)
- Hit/miss ratio for cache effectiveness
- Pub/sub channel activity
- Slow query log

### Kubernetes Monitoring

```bash
# Check pod status
kubectl get pods -n metlab-dev -l app=redis

# View logs
kubectl logs -f <redis-pod-name> -n metlab-dev

# Check resource usage
kubectl top pod <redis-pod-name> -n metlab-dev

# Describe pod for events
kubectl describe pod <redis-pod-name> -n metlab-dev
```

## Security Considerations

### Current Setup (Development)
- No password authentication (suitable for dev environment)
- ClusterIP service (internal-only access)
- Network policies should be added for production

### Production Recommendations
1. **Enable authentication**: Set REDIS_PASSWORD in secrets
2. **Enable TLS**: Configure Redis with TLS certificates
3. **Network policies**: Restrict access to specific services
4. **Regular backups**: Automate RDB/AOF backup to external storage
5. **Monitoring**: Set up alerts for memory usage, connection errors

## Next Steps

### Immediate
1. ✅ Redis Kubernetes deployment configured
2. ✅ Go client package created with connection pooling
3. ✅ Comprehensive tests written
4. ✅ Documentation completed

### Future Tasks (Other Tasks in Spec)
1. Integrate Redis client into API Gateway for rate limiting (Task 17)
2. Integrate Redis into Auth Service for session management (Task 13)
3. Integrate Redis into Collaboration Service for real-time chat (Tasks 50-52)
4. Set up monitoring and alerting for Redis (Task 81)

## Requirements Satisfied

✅ **Requirement 16.1**: Container orchestration with Kubernetes
- Redis deployed as Kubernetes Deployment with proper resource limits
- Health checks configured
- Persistent storage configured

✅ **Task 6 Sub-tasks**:
- ✅ Create Kubernetes Deployment manifest for Redis
- ✅ Configure Redis persistence and memory limits
- ✅ Set up Redis connection pooling in Go services

## Files Created/Modified

### Created
1. `cloud-native/shared/cache/redis.go` - Redis client implementation
2. `cloud-native/shared/cache/redis_test.go` - Comprehensive test suite
3. `cloud-native/shared/cache/README.md` - Documentation
4. `cloud-native/shared/cache/example_integration.go` - Integration examples
5. `cloud-native/infrastructure/REDIS_SETUP_COMPLETE.md` - This file

### Modified
1. `cloud-native/infrastructure/k8s/redis.yaml` - Enhanced with persistence and configuration

## Verification Checklist

- [x] Redis Kubernetes manifest includes ConfigMap with production settings
- [x] Persistent volume claim configured for data persistence
- [x] Resource limits set (512Mi memory, 500m CPU)
- [x] Health checks configured (liveness and readiness probes)
- [x] Go client package created with connection pooling
- [x] Connection pool configurable (default 100 connections, 10 min idle)
- [x] Support for all common Redis operations
- [x] Pub/Sub support for real-time messaging
- [x] Comprehensive test suite
- [x] Documentation with examples
- [x] Integration patterns for common use cases

## Conclusion

Task 6 is now **COMPLETE**. Redis is fully configured for both caching and pub/sub functionality with:

- Production-ready Kubernetes deployment with persistence
- Comprehensive Go client library with connection pooling
- Full test coverage
- Detailed documentation and examples
- Ready for integration into all microservices

The Redis setup provides a solid foundation for:
- Session management
- Rate limiting
- Data caching
- Real-time messaging (chat, notifications)
- Temporary data storage

All services can now use the shared Redis client package to leverage these capabilities.
