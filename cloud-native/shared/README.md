# Shared Go Packages

This directory contains shared Go packages used across all microservices in the Metlab.edu cloud-native architecture.

## Packages

### Infrastructure

- **`db/`** - PostgreSQL database connection pool management with pgx
  - Connection pooling with configurable limits
  - Health checks and statistics
  - Support for connection URLs and structured config

- **`cache/`** - Redis client wrapper with connection management
  - Connection pooling and health checks
  - Common operations (get, set, del, etc.)
  - Pub/Sub support for real-time messaging
  - Hash operations for structured data

- **`storage/`** - S3-compatible object storage client
  - Upload and download operations
  - Presigned URL generation
  - Bucket management
  - Support for MinIO (local) and AWS S3 (production)

### Application

- **`jwt/`** - JWT token generation and validation
  - Teacher and student token generation with different expiration times
  - Token validation and claims extraction
  - Token refresh functionality
  - Support for custom claims

- **`logger/`** - Structured JSON logging
  - Multiple log levels (DEBUG, INFO, WARN, ERROR, FATAL)
  - Context-aware logging (trace ID, user ID)
  - Automatic caller information
  - Default fields for service identification

- **`errors/`** - Error handling with gRPC status codes
  - Structured error types with gRPC codes
  - Error wrapping and context
  - Conversion between app errors and gRPC errors
  - Helper functions for common error types

## Usage

Import shared packages in your service:

```go
import (
    "github.com/metlab/shared/db"
    "github.com/metlab/shared/cache"
    "github.com/metlab/shared/storage"
    "github.com/metlab/shared/jwt"
    "github.com/metlab/shared/logger"
    "github.com/metlab/shared/errors"
)
```

## Quick Start Example

```go
package main

import (
    "context"
    "github.com/metlab/shared/db"
    "github.com/metlab/shared/cache"
    "github.com/metlab/shared/logger"
    "github.com/metlab/shared/jwt"
)

func main() {
    ctx := context.Background()
    
    // Initialize logger
    log := logger.New(&logger.Config{
        Level:       logger.InfoLevel,
        ServiceName: "my-service",
    })
    
    // Initialize database
    dbPool, err := db.NewPool(ctx, db.DefaultConfig())
    if err != nil {
        log.Fatal("Failed to connect to database", err)
    }
    defer dbPool.Close()
    
    // Initialize Redis
    redisClient, err := cache.NewRedisClient(ctx, cache.DefaultRedisConfig())
    if err != nil {
        log.Fatal("Failed to connect to Redis", err)
    }
    defer redisClient.Close()
    
    // Initialize JWT manager
    tokenManager := jwt.NewTokenManager(&jwt.Config{
        SecretKey: "your-secret-key",
    })
    
    log.Info("Service initialized successfully")
}
```

## Documentation

Each package has its own README with detailed documentation:

- [Database Package](./db/README.md)
- [Cache Package](./cache/README.md)
- [Storage Package](./storage/README.md)
- [JWT Package](./jwt/README.md)
- [Logger Package](./logger/README.md)
- [Errors Package](./errors/README.md)

## Development

### Running Tests

```bash
# Run all tests
go test ./...

# Run tests with coverage
go test -cover ./...

# Run tests for a specific package
go test ./jwt
```

### Building

The shared packages are imported as a Go module. To use them in your service:

1. Ensure your service's `go.mod` includes the shared module:
   ```
   require github.com/metlab/shared v0.0.0
   ```

2. Import the packages you need in your code

3. Run `go mod tidy` to download dependencies

## Best Practices

1. **Error Handling**: Always use the errors package for consistent error handling across services
2. **Logging**: Use structured logging with appropriate log levels and context
3. **Connection Management**: Reuse database and Redis connections; don't create new connections for each operation
4. **JWT Security**: Use strong secret keys and appropriate token expiration times
5. **Context**: Always pass context through function calls for cancellation and timeout support
