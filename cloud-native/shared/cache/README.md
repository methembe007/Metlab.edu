# Cache Package

This package provides Redis client functionality with connection pooling for the Metlab microservices.

## Features

- Connection pooling with configurable pool size
- Automatic connection health checks
- Support for common Redis operations (Get, Set, Del, etc.)
- Hash operations (HSet, HGet, HGetAll, HDel)
- Pub/Sub support for real-time messaging
- Pipeline support for batching commands
- Connection pool statistics

## Usage

### Basic Usage

```go
package main

import (
    "context"
    "time"
    
    "github.com/metlab/shared/cache"
)

func main() {
    ctx := context.Background()
    
    // Create client with default configuration
    cfg := cache.DefaultRedisConfig()
    cfg.Host = "redis"
    cfg.Port = 6379
    
    client, err := cache.NewRedisClient(ctx, cfg)
    if err != nil {
        panic(err)
    }
    defer client.Close()
    
    // Set a value with expiration
    err = client.Set(ctx, "user:123", "John Doe", 1*time.Hour)
    if err != nil {
        panic(err)
    }
    
    // Get a value
    value, err := client.Get(ctx, "user:123")
    if err != nil {
        panic(err)
    }
    
    println(value) // Output: John Doe
}
```

### Using Connection URL

```go
client, err := cache.NewRedisClientFromURL(ctx, "redis://localhost:6379/0")
if err != nil {
    panic(err)
}
defer client.Close()
```

### Hash Operations

```go
// Store user data in a hash
err = client.HSet(ctx, "user:123", 
    "name", "John Doe",
    "email", "john@example.com",
    "age", "30")

// Get a specific field
name, err := client.HGet(ctx, "user:123", "name")

// Get all fields
userData, err := client.HGetAll(ctx, "user:123")
```

### Pub/Sub for Real-time Messaging

```go
// Publisher
err = client.Publish(ctx, "chat:room1", "Hello, World!")

// Subscriber
pubsub := client.Subscribe(ctx, "chat:room1")
defer pubsub.Close()

for {
    msg, err := pubsub.ReceiveMessage(ctx)
    if err != nil {
        break
    }
    println("Received:", msg.Payload)
}
```

### Pipeline for Batching

```go
pipe := client.Pipeline()

pipe.Set(ctx, "key1", "value1", 0)
pipe.Set(ctx, "key2", "value2", 0)
pipe.Set(ctx, "key3", "value3", 0)

_, err := pipe.Exec(ctx)
if err != nil {
    panic(err)
}
```

### Connection Pool Statistics

```go
stats := client.GetPoolStats()
fmt.Printf("Total Connections: %d\n", stats.TotalConns)
fmt.Printf("Idle Connections: %d\n", stats.IdleConns)
fmt.Printf("Hits: %d\n", stats.Hits)
fmt.Printf("Misses: %d\n", stats.Misses)
```

## Configuration

### RedisConfig Options

- `Host`: Redis server hostname (default: "localhost")
- `Port`: Redis server port (default: 6379)
- `Password`: Redis password (default: "")
- `DB`: Redis database number (default: 0)
- `PoolSize`: Maximum number of socket connections (default: 100)
- `MinIdleConns`: Minimum number of idle connections (default: 10)
- `MaxConnAge`: Connection age at which client retires the connection (default: 1 hour)
- `PoolTimeout`: Amount of time client waits for connection if all are busy (default: 4 seconds)
- `IdleTimeout`: Amount of time after which client closes idle connections (default: 5 minutes)
- `IdleCheckFrequency`: Frequency of idle checks (default: 1 minute)
- `DialTimeout`: Timeout for establishing new connections (default: 5 seconds)
- `ReadTimeout`: Timeout for socket reads (default: 3 seconds)
- `WriteTimeout`: Timeout for socket writes (default: 3 seconds)

## Environment Variables

Services can use environment variables to configure Redis:

```bash
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=secret
REDIS_DB=0
```

## Kubernetes Configuration

The Redis deployment is configured in `infrastructure/k8s/redis.yaml` with:

- Persistent storage (5Gi)
- Memory limit: 512Mi
- CPU limit: 500m
- AOF persistence enabled
- RDB snapshots enabled
- Health checks (liveness and readiness probes)

## Testing

Run tests with:

```bash
go test -v ./cache
```

Note: Tests require a running Redis instance on localhost:6379. Tests will be skipped if Redis is not available.

## Common Use Cases

### Session Storage

```go
// Store user session
sessionData := map[string]interface{}{
    "user_id": "123",
    "role": "teacher",
    "expires_at": time.Now().Add(24 * time.Hour).Unix(),
}

err = client.HSet(ctx, "session:abc123", sessionData)
err = client.Expire(ctx, "session:abc123", 24*time.Hour)
```

### Rate Limiting

```go
// Increment request count for IP
key := fmt.Sprintf("ratelimit:%s", ipAddress)
count, err := client.Incr(ctx, key)

if count == 1 {
    // First request, set expiration
    client.Expire(ctx, key, 1*time.Minute)
}

if count > 100 {
    // Rate limit exceeded
    return errors.New("rate limit exceeded")
}
```

### Caching

```go
// Try to get from cache
cacheKey := "video:metadata:123"
cached, err := client.Get(ctx, cacheKey)

if err == redis.Nil {
    // Cache miss, fetch from database
    data := fetchFromDatabase()
    
    // Store in cache for 1 hour
    client.Set(ctx, cacheKey, data, 1*time.Hour)
    return data
}

return cached
```

### Real-time Chat

```go
// Chat service publishes messages
func SendMessage(roomID, message string) error {
    channel := fmt.Sprintf("chat:room:%s", roomID)
    return client.Publish(ctx, channel, message)
}

// Chat service subscribes to messages
func SubscribeToRoom(roomID string) *redis.PubSub {
    channel := fmt.Sprintf("chat:room:%s", roomID)
    return client.Subscribe(ctx, channel)
}
```

## Best Practices

1. **Always close connections**: Use `defer client.Close()` to ensure connections are properly closed
2. **Use context for timeouts**: Pass context with timeout for operations that might hang
3. **Handle redis.Nil errors**: Check for `redis.Nil` error when a key doesn't exist
4. **Set appropriate expiration**: Always set TTL on cached data to prevent memory bloat
5. **Use pipelines for bulk operations**: Batch multiple commands to reduce round trips
6. **Monitor pool stats**: Regularly check pool statistics to optimize pool size
7. **Use pub/sub for real-time features**: Leverage Redis pub/sub for chat and notifications

## Troubleshooting

### Connection Refused

If you see "connection refused" errors:
- Verify Redis is running: `kubectl get pods -n metlab-dev | grep redis`
- Check Redis service: `kubectl get svc redis -n metlab-dev`
- Verify network connectivity: `kubectl exec -it <pod> -- redis-cli -h redis ping`

### High Memory Usage

If Redis memory usage is high:
- Check maxmemory policy in redis.conf
- Review TTL settings on cached data
- Monitor eviction stats: `INFO stats` in redis-cli
- Consider increasing memory limits in Kubernetes

### Connection Pool Exhausted

If you see "connection pool timeout" errors:
- Increase `PoolSize` in configuration
- Check for connection leaks (not closing connections)
- Review `PoolStats` to see connection usage patterns
- Consider increasing `PoolTimeout`

## References

- [go-redis Documentation](https://redis.uptrace.dev/)
- [Redis Commands](https://redis.io/commands)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
