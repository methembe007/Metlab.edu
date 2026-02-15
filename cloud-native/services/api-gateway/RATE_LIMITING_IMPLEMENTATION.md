# Rate Limiting Implementation

## Overview

This document describes the implementation of rate limiting middleware for the API Gateway service, as specified in task 17 of the cloud-native architecture migration.

## Implementation Details

### Components

1. **Rate Limiter Interface** (`rate_limiter.go`)
   - Defines a common interface for different rate limiting strategies
   - Provides `RateLimitInfo` structure with limit, remaining, reset time, and retry-after information

2. **In-Memory Rate Limiter**
   - Fast, local rate limiting using Go maps and mutexes
   - Automatic cleanup of expired entries
   - Suitable for single-instance deployments or development

3. **Redis Rate Limiter**
   - Distributed rate limiting using Redis
   - Atomic operations with Redis pipelines
   - Suitable for multi-instance production deployments

4. **Hybrid Rate Limiter**
   - Uses Redis as primary storage
   - Falls back to in-memory if Redis is unavailable
   - Provides best reliability for production

### Configuration

Rate limiting is configured via environment variables:

```bash
# Redis connection URL
REDIS_URL=redis://localhost:6379/0

# Maximum requests per minute per IP
RATE_LIMIT_PER_MINUTE=100
```

### Features Implemented

✅ **In-memory rate limiter with automatic cleanup**
- Tracks requests per IP address in memory
- Automatically removes expired entries every minute
- Thread-safe with mutex protection

✅ **Redis-backed distributed rate limiting**
- Uses Redis INCR and TTL commands for atomic operations
- Supports multiple API Gateway instances
- Persistent across service restarts

✅ **100 requests per minute per IP limit (configurable)**
- Default limit: 100 requests per minute
- Configurable via `RATE_LIMIT_PER_MINUTE` environment variable
- Per-IP tracking using X-Forwarded-For, X-Real-IP, or RemoteAddr

✅ **429 status code when limit exceeded**
- Returns HTTP 429 Too Many Requests
- Includes descriptive error message
- Provides retry-after information

✅ **Rate limit headers in responses**
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets
- `Retry-After`: Seconds to wait before retrying (when limited)

### Middleware Integration

The rate limiting middleware is applied globally in the router:

```go
// Apply rate limiting middleware
if config != nil {
    rateLimitConfig := &custommw.RateLimitConfig{
        Limit:  config.RateLimitPerMinute,
        Window: time.Minute,
        KeyFunc: func(r *http.Request) string {
            // Use X-Forwarded-For if behind proxy
            if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
                return xff
            }
            if xri := r.Header.Get("X-Real-IP"); xri != "" {
                return xri
            }
            return r.RemoteAddr
        },
    }
    
    if config.RedisClient != nil {
        rateLimitConfig.RedisClient = config.RedisClient.Client()
    }
    
    r.Use(custommw.RateLimit(rateLimitConfig))
}
```

### Response Examples

#### Successful Request (Within Limit)

```
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1709654400
Content-Type: application/json

{"message": "Success"}
```

#### Rate Limited Request

```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1709654400
Retry-After: 45
Content-Type: application/json

{
  "error": "rate limit exceeded",
  "message": "Too many requests. Please try again in 45 seconds.",
  "retry_after": 45
}
```

### Testing

Comprehensive unit tests are provided in `rate_limiter_test.go`:

- ✅ In-memory rate limiter allows requests within limit
- ✅ In-memory rate limiter blocks requests exceeding limit
- ✅ Different keys have separate limits
- ✅ Rate limit resets after window expires
- ✅ Redis rate limiter functionality
- ✅ Middleware integration with proper headers
- ✅ 429 status code on limit exceeded
- ✅ X-Forwarded-For header support

Run tests with:
```bash
go test ./internal/middleware -v -run TestRateLimit
```

### Architecture Decisions

1. **Hybrid Approach**: Implemented both in-memory and Redis-backed rate limiting to support different deployment scenarios
   - Development: In-memory only (no Redis required)
   - Production: Redis-backed with in-memory fallback

2. **IP-Based Rate Limiting**: Uses client IP address as the rate limit key
   - Supports proxy headers (X-Forwarded-For, X-Real-IP)
   - Falls back to RemoteAddr for direct connections

3. **Graceful Degradation**: If Redis is unavailable, the system falls back to in-memory rate limiting
   - Ensures service availability even if Redis fails
   - Logs warnings when fallback occurs

4. **Standard Headers**: Implements standard rate limit headers
   - Compatible with common rate limiting conventions
   - Provides clear feedback to clients

### Requirements Satisfied

This implementation satisfies the following requirements from the specification:

- **Requirement 1.3**: API Gateway with rate limiting
- **Requirement 20.3**: Rate limiting of 100 requests per minute per IP address

### Files Modified/Created

1. **Created**: `internal/middleware/rate_limiter.go`
   - Core rate limiting implementation
   - In-memory, Redis, and hybrid rate limiters
   - Middleware function

2. **Created**: `internal/middleware/rate_limiter_test.go`
   - Comprehensive unit tests
   - Tests for all rate limiter types
   - Middleware integration tests

3. **Modified**: `internal/config/config.go`
   - Added `RedisURL` configuration field
   - Added `RateLimitPerMinute` configuration field
   - Updated `Load()` function to parse new fields

4. **Modified**: `cmd/server/main.go`
   - Added Redis client initialization
   - Passes Redis client to router
   - Graceful handling of Redis connection failures

5. **Modified**: `internal/router/router.go`
   - Added `RouterConfig` structure
   - Applied rate limiting middleware globally
   - Configured key extraction function

6. **Modified**: `.env.example`
   - Added `REDIS_URL` configuration
   - Added `RATE_LIMIT_PER_MINUTE` configuration

7. **Updated**: `internal/middleware/README.md`
   - Added comprehensive rate limiting documentation
   - Usage examples
   - Configuration details

### Usage Instructions

1. **Start Redis** (optional, for distributed rate limiting):
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   ```

2. **Configure Environment Variables**:
   ```bash
   export REDIS_URL=redis://localhost:6379/0
   export RATE_LIMIT_PER_MINUTE=100
   ```

3. **Start API Gateway**:
   ```bash
   cd cloud-native/services/api-gateway
   go run cmd/server/main.go
   ```

4. **Test Rate Limiting**:
   ```bash
   # Make multiple requests quickly
   for i in {1..105}; do
     curl -i http://localhost:8080/api/
   done
   ```

   After 100 requests, you should see:
   ```
   HTTP/1.1 429 Too Many Requests
   X-RateLimit-Limit: 100
   X-RateLimit-Remaining: 0
   Retry-After: 45
   ```

### Performance Considerations

- **In-Memory**: Very fast, no network overhead, but not distributed
- **Redis**: Slight network overhead, but supports multiple instances
- **Hybrid**: Best of both worlds with fallback capability

### Future Enhancements

Potential improvements for future iterations:

1. **Per-User Rate Limiting**: Different limits for authenticated users
2. **Endpoint-Specific Limits**: Different limits for different API endpoints
3. **Burst Allowance**: Allow short bursts above the limit
4. **Rate Limit Tiers**: Different limits based on user subscription level
5. **Metrics**: Export rate limiting metrics to Prometheus

## Conclusion

The rate limiting middleware has been successfully implemented with all required features:
- ✅ In-memory rate limiter with Redis backing
- ✅ 100 requests per minute per IP limit (configurable)
- ✅ 429 status code when limit exceeded
- ✅ Rate limit headers in all responses

The implementation is production-ready, well-tested, and follows best practices for distributed systems.
