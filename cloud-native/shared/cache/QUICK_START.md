# Redis Client Quick Start Guide

## Installation

The Redis client is already included in the shared module. Just import it:

```go
import "github.com/metlab/shared/cache"
```

## Basic Usage (5 Minutes)

### 1. Initialize Client

```go
ctx := context.Background()

// Option A: From environment variables (recommended)
client, err := cache.InitializeRedisClient(ctx)
if err != nil {
    log.Fatal(err)
}
defer client.Close()

// Option B: Manual configuration
cfg := cache.DefaultRedisConfig()
cfg.Host = "redis"
cfg.Port = 6379
client, err := cache.NewRedisClient(ctx, cfg)
```

### 2. Basic Operations

```go
// Set a value
client.Set(ctx, "user:123", "John Doe", 1*time.Hour)

// Get a value
value, err := client.Get(ctx, "user:123")

// Delete a key
client.Del(ctx, "user:123")

// Check if key exists
exists, _ := client.Exists(ctx, "user:123")
```

### 3. Counters

```go
// Increment
count, _ := client.Incr(ctx, "page:views")

// Decrement
count, _ := client.Decr(ctx, "inventory:item123")
```

### 4. Hash Operations

```go
// Store user data
client.HSet(ctx, "user:123", 
    "name", "John Doe",
    "email", "john@example.com",
    "age", "30")

// Get specific field
name, _ := client.HGet(ctx, "user:123", "name")

// Get all fields
userData, _ := client.HGetAll(ctx, "user:123")
```

## Common Patterns

### Session Management

```go
sessionMgr := cache.NewSessionManager(client, "session", 24*time.Hour)

// Create session
sessionMgr.CreateSession(ctx, sessionID, map[string]interface{}{
    "user_id": "123",
    "role": "teacher",
})

// Get session
data, _ := sessionMgr.GetSession(ctx, sessionID)

// Delete session
sessionMgr.DeleteSession(ctx, sessionID)
```

### Rate Limiting

```go
rateLimiter := cache.NewRateLimiter(client, "ratelimit")

// Check if request is allowed (100 requests per minute)
allowed, _ := rateLimiter.CheckLimit(ctx, ipAddress, 100, 1*time.Minute)
if !allowed {
    return errors.New("rate limit exceeded")
}
```

### Caching JSON Data

```go
cacheMgr := cache.NewCacheManager(client)

// Cache an object
user := User{ID: "123", Name: "John"}
cacheMgr.CacheJSON(ctx, "user:123", user, 1*time.Hour)

// Retrieve from cache
var cachedUser User
err := cacheMgr.GetJSON(ctx, "user:123", &cachedUser)
if err == redis.Nil {
    // Cache miss - fetch from database
}
```

### Real-time Messaging (Pub/Sub)

```go
pubsubMgr := cache.NewPubSubManager(client)

// Publish a message
pubsubMgr.PublishMessage(ctx, "chat:room1", map[string]string{
    "user": "John",
    "message": "Hello!",
})

// Subscribe to messages
go pubsubMgr.SubscribeToChannel(ctx, "chat:room1", func(data []byte) error {
    var msg map[string]string
    json.Unmarshal(data, &msg)
    log.Printf("Received: %v", msg)
    return nil
})
```

## Environment Variables

Set these in your service:

```bash
REDIS_HOST=redis      # Kubernetes service name
REDIS_PORT=6379       # Default port
REDIS_PASSWORD=       # Empty for dev
REDIS_DB=0            # Database number
```

## Testing

```bash
# Run tests (requires Redis running)
go test -v ./cache

# Tests will skip if Redis is not available
```

## Troubleshooting

### Connection Refused
```bash
# Check if Redis is running
kubectl get pods -n metlab-dev | grep redis

# Test connection
kubectl exec -it <redis-pod> -n metlab-dev -- redis-cli ping
```

### Pool Exhausted
```go
// Increase pool size
cfg := cache.DefaultRedisConfig()
cfg.PoolSize = 200  // Increase from default 100
```

### Memory Issues
```bash
# Check Redis memory usage
kubectl exec -it <redis-pod> -n metlab-dev -- redis-cli INFO memory
```

## Best Practices

1. **Always set TTL** on cached data to prevent memory bloat
2. **Use context with timeout** for operations that might hang
3. **Handle redis.Nil** error when key doesn't exist
4. **Close connections** with `defer client.Close()`
5. **Use pipelines** for bulk operations to reduce round trips
6. **Monitor pool stats** to optimize pool size

## More Information

- Full documentation: `cloud-native/shared/cache/README.md`
- Integration examples: `cloud-native/shared/cache/example_integration.go`
- Test examples: `cloud-native/shared/cache/redis_test.go`

## Need Help?

Check the comprehensive README.md in this directory for:
- Detailed API documentation
- Advanced usage patterns
- Performance tuning
- Security considerations
- Monitoring and alerting
