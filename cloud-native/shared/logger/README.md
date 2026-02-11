# Logger Package

This package provides structured logging for the Metlab.edu platform with JSON output format.

## Features

- Structured JSON logging
- Multiple log levels (DEBUG, INFO, WARN, ERROR, FATAL)
- Automatic caller information (file and line number)
- Context-aware logging (trace ID, user ID)
- Default fields for all log entries
- Service name identification

## Usage

### Basic Usage

```go
package main

import (
    "github.com/metlab/shared/logger"
)

func main() {
    // Use the default logger
    logger.Info("Application started")
    logger.Debug("Debug information")
    logger.Warn("Warning message")
    logger.Error("Error occurred", err)
}
```

### Create Custom Logger

```go
// Create a custom logger
config := &logger.Config{
    Level:       logger.InfoLevel,
    ServiceName: "auth-service",
    AddCaller:   true,
    Fields: map[string]string{
        "environment": "production",
        "version":     "1.0.0",
    },
}
log := logger.New(config)

log.Info("Service started")
```

### Logging with Fields

```go
// Log with additional fields
logger.Info("User logged in", map[string]interface{}{
    "user_id": "user-123",
    "ip_address": "192.168.1.1",
    "duration_ms": 45,
})
```

### Context-Aware Logging

```go
// Create a logger with trace ID
log := logger.WithTraceID("trace-abc-123")
log.Info("Processing request")

// Create a logger with user ID
log := logger.WithUserID("user-456")
log.Info("User action performed")

// Create a logger from context
log := logger.WithContext(ctx)
log.Info("Request processed")
```

### Logger with Default Fields

```go
// Create a logger with default fields
log := logger.WithFields(map[string]string{
    "component": "database",
    "operation": "query",
})

log.Info("Query executed")
log.Error("Query failed", err)
```

### Error Logging

```go
// Log errors with context
err := someOperation()
if err != nil {
    logger.Error("Operation failed", err, map[string]interface{}{
        "operation": "user_creation",
        "user_id": "user-123",
    })
}
```

## Log Levels

The package supports the following log levels:

- `DebugLevel`: Detailed information for debugging
- `InfoLevel`: General informational messages
- `WarnLevel`: Warning messages for potentially harmful situations
- `ErrorLevel`: Error messages for error events
- `FatalLevel`: Critical errors that cause the application to exit

## Log Output Format

Logs are output in JSON format:

```json
{
  "timestamp": "2026-02-09T10:30:00.123456Z",
  "level": "INFO",
  "service": "auth-service",
  "message": "User logged in",
  "fields": {
    "user_id": "user-123",
    "ip_address": "192.168.1.1",
    "duration_ms": 45
  },
  "caller": "/app/handlers/auth.go:45",
  "trace_id": "trace-abc-123"
}
```

## Configuration

### Config Fields

- `Level`: Minimum log level to output (default: InfoLevel)
- `ServiceName`: Name of the service (default: "metlab-service")
- `Output`: Output writer (default: os.Stdout)
- `AddCaller`: Add caller information (default: true)
- `Fields`: Default fields to include in all logs (default: empty map)

## Best Practices

1. **Use Appropriate Log Levels**: Use DEBUG for development, INFO for normal operations, WARN for potential issues, ERROR for errors
2. **Include Context**: Always include relevant context (user ID, trace ID, operation) in log messages
3. **Structured Fields**: Use structured fields instead of string formatting for better searchability
4. **Avoid Sensitive Data**: Never log passwords, tokens, or other sensitive information
5. **Performance**: Be mindful of logging in hot paths; use DEBUG level for verbose logging
6. **Trace IDs**: Use trace IDs to correlate logs across services for distributed tracing

## Integration with Services

### gRPC Interceptor

```go
func LoggingInterceptor(log *logger.Logger) grpc.UnaryServerInterceptor {
    return func(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
        start := time.Now()
        
        // Extract trace ID from metadata
        traceID := extractTraceID(ctx)
        log := log.WithTraceID(traceID)
        
        log.Info("gRPC request started", map[string]interface{}{
            "method": info.FullMethod,
        })
        
        resp, err := handler(ctx, req)
        
        duration := time.Since(start)
        if err != nil {
            log.Error("gRPC request failed", err, map[string]interface{}{
                "method": info.FullMethod,
                "duration_ms": duration.Milliseconds(),
            })
        } else {
            log.Info("gRPC request completed", map[string]interface{}{
                "method": info.FullMethod,
                "duration_ms": duration.Milliseconds(),
            })
        }
        
        return resp, err
    }
}
```

### HTTP Middleware

```go
func LoggingMiddleware(log *logger.Logger) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            start := time.Now()
            
            log := log.WithTraceID(r.Header.Get("X-Trace-ID"))
            
            log.Info("HTTP request started", map[string]interface{}{
                "method": r.Method,
                "path": r.URL.Path,
                "remote_addr": r.RemoteAddr,
            })
            
            next.ServeHTTP(w, r)
            
            duration := time.Since(start)
            log.Info("HTTP request completed", map[string]interface{}{
                "method": r.Method,
                "path": r.URL.Path,
                "duration_ms": duration.Milliseconds(),
            })
        })
    }
}
```
