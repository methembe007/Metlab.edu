# Shared Go Packages

This directory contains shared Go packages used across all microservices.

## Packages

- `db/` - Database connection and utilities
- `redis/` - Redis client and utilities
- `s3/` - S3-compatible storage client
- `jwt/` - JWT token generation and validation
- `logger/` - Structured logging
- `errors/` - Error handling and gRPC status codes

## Usage

Import shared packages in your service:

```go
import (
    "github.com/metlab/shared/db"
    "github.com/metlab/shared/logger"
)
```
