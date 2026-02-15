# API Gateway Middleware

This directory contains middleware components for the API Gateway service.

## Authentication Middleware

The authentication middleware (`auth.go`) validates JWT tokens and adds user context to requests.

### Features

- Extracts JWT token from `Authorization` header (Bearer token format)
- Validates token by calling the Auth service's `ValidateToken` gRPC method
- Adds user information to request context for downstream handlers
- Returns 401 Unauthorized for missing or invalid tokens

### Usage

The middleware is automatically applied to protected routes in the router:

```go
r.Group(func(r chi.Router) {
    // Add authentication middleware
    if handler.GetAuthClient() != nil {
        r.Use(custommw.Authenticate(handler.GetAuthClient()))
    }
    
    // Protected endpoints
    r.Get("/videos", handler.ListVideos)
})
```

### Accessing User Context

Handlers can access authenticated user information from the request context:

```go
func (h *Handler) ListVideos(w http.ResponseWriter, r *http.Request) {
    userID := middleware.GetUserID(r.Context())
    role := middleware.GetUserRole(r.Context())
    classIDs := middleware.GetClassIDs(r.Context())
    teacherID := middleware.GetTeacherID(r.Context())
    
    // Use user information for authorization and filtering
}
```

### Error Responses

The middleware returns JSON error responses with appropriate HTTP status codes:

- **401 Unauthorized**: Missing, invalid, or expired token
  ```json
  {"error": "missing authorization header"}
  {"error": "invalid authorization header format"}
  {"error": "invalid or expired token"}
  ```

### Token Format

Requests must include the JWT token in the Authorization header:

```
Authorization: Bearer <jwt-token>
```

### Context Keys

The middleware adds the following values to the request context:

- `UserIDKey`: User's unique identifier
- `UserRoleKey`: User's role (teacher or student)
- `ClassIDsKey`: Array of class IDs the user has access to
- `TeacherIDKey`: Teacher ID (for teacher users or students linked to a teacher)

### Testing

The middleware includes comprehensive unit tests in `auth_test.go`:

- Missing Authorization header
- Invalid Authorization header format
- Empty token
- Invalid token
- Valid token with context population
- Context getter functions

Run tests with:
```bash
go test ./internal/middleware -v -run TestAuthenticate
```

## Rate Limiting Middleware

The rate limiting middleware (`rate_limiter.go`) implements request rate limiting with both in-memory and Redis-backed storage.

### Features

- **100 requests per minute per IP** (configurable)
- In-memory rate limiting with automatic cleanup
- Redis-backed distributed rate limiting for multi-instance deployments
- Hybrid mode with Redis primary and in-memory fallback
- Standard rate limit headers in responses
- 429 Too Many Requests status code when limit exceeded

### Configuration

Rate limiting is configured via environment variables:

```bash
REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_PER_MINUTE=100
```

### Usage

The middleware is automatically applied globally in the router:

```go
rateLimitConfig := &custommw.RateLimitConfig{
    Limit:  100,
    Window: time.Minute,
    KeyFunc: func(r *http.Request) string {
        // Use X-Forwarded-For if behind proxy
        if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
            return xff
        }
        return r.RemoteAddr
    },
    RedisClient: redisClient, // Optional
}

r.Use(custommw.RateLimit(rateLimitConfig))
```

### Response Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1709654400
```

When rate limit is exceeded:

```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1709654400
Retry-After: 45

{
  "error": "rate limit exceeded",
  "message": "Too many requests. Please try again in 45 seconds.",
  "retry_after": 45
}
```

### Rate Limiting Strategies

#### In-Memory Rate Limiter

- Fast and simple
- Suitable for single-instance deployments
- Automatic cleanup of expired entries
- No external dependencies

#### Redis Rate Limiter

- Distributed rate limiting across multiple instances
- Atomic operations using Redis pipelines
- Persistent across service restarts
- Suitable for production deployments

#### Hybrid Rate Limiter

- Uses Redis as primary storage
- Falls back to in-memory if Redis is unavailable
- Best of both worlds for reliability

### Key Extraction

By default, the rate limit key is extracted from:

1. `X-Forwarded-For` header (if present, for proxy/load balancer scenarios)
2. `X-Real-IP` header (if present)
3. `RemoteAddr` (direct connection IP)

This ensures accurate rate limiting even behind proxies or load balancers.

### Testing

The middleware includes comprehensive unit tests in `rate_limiter_test.go`:

- In-memory rate limiter functionality
- Redis rate limiter functionality
- Middleware integration tests
- Rate limit header validation
- 429 response validation
- Different IP addresses have separate limits
- Window reset behavior

Run tests with:
```bash
go test ./internal/middleware -v -run TestRateLimit
```

## Other Middleware

- **CORS** (`cors.go`): Handles Cross-Origin Resource Sharing
- **Logging** (`logging.go`): Logs HTTP requests and responses
- **Request ID** (`request_id.go`): Adds unique request IDs for tracing
