package logger

import (
	"context"
	"errors"
	"os"
)

// ExampleUsage demonstrates how to use the logger package
func ExampleUsage() {
	// Create a custom logger
	config := &Config{
		Level:       InfoLevel,
		ServiceName: "auth-service",
		Output:      os.Stdout,
		AddCaller:   true,
		Fields: map[string]string{
			"environment": "production",
			"version":     "1.0.0",
		},
	}
	log := New(config)

	// Basic logging
	log.Info("Service started")
	log.Debug("Debug information")
	log.Warn("Warning message")

	// Logging with fields
	log.Info("User logged in", map[string]interface{}{
		"user_id":    "user-123",
		"ip_address": "192.168.1.1",
		"duration_ms": 45,
	})

	// Error logging
	err := errors.New("database connection failed")
	log.Error("Failed to connect to database", err, map[string]interface{}{
		"host": "localhost",
		"port": 5432,
	})

	// Logger with trace ID
	traceLog := log.WithTraceID("trace-abc-123")
	traceLog.Info("Processing request")

	// Logger with user ID
	userLog := log.WithUserID("user-456")
	userLog.Info("User action performed")

	// Logger with multiple fields
	componentLog := log.WithFields(map[string]string{
		"component": "database",
		"operation": "query",
	})
	componentLog.Info("Query executed")

	// Context-aware logging
	ctx := context.Background()
	ctx = context.WithValue(ctx, "trace_id", "trace-xyz-789")
	ctx = context.WithValue(ctx, "user_id", "user-999")
	
	ctxLog := log.WithContext(ctx)
	ctxLog.Info("Request processed with context")

	// Using the default logger
	Info("Application initialized")
	Debug("Debug message")
	Warn("Warning message")
	
	// Error with default logger
	Error("Operation failed", err, map[string]interface{}{
		"operation": "user_creation",
	})
}

// ExampleGRPCInterceptor demonstrates how to use the logger in a gRPC interceptor
func ExampleGRPCInterceptor() {
	// This is a conceptual example showing how to integrate with gRPC
	// In actual implementation, you would use this in your gRPC server setup
	
	log := New(&Config{
		Level:       InfoLevel,
		ServiceName: "grpc-service",
	})

	// Example of logging in a gRPC handler
	traceID := "trace-123"
	method := "/auth.AuthService/Login"
	
	requestLog := log.WithTraceID(traceID)
	requestLog.Info("gRPC request started", map[string]interface{}{
		"method": method,
	})

	// Simulate processing
	// ...

	requestLog.Info("gRPC request completed", map[string]interface{}{
		"method":      method,
		"duration_ms": 150,
		"status":      "success",
	})
}

// ExampleHTTPMiddleware demonstrates how to use the logger in HTTP middleware
func ExampleHTTPMiddleware() {
	// This is a conceptual example showing how to integrate with HTTP
	
	log := New(&Config{
		Level:       InfoLevel,
		ServiceName: "api-gateway",
	})

	// Example of logging in an HTTP handler
	traceID := "trace-456"
	method := "POST"
	path := "/api/auth/login"
	remoteAddr := "192.168.1.100"
	
	requestLog := log.WithTraceID(traceID)
	requestLog.Info("HTTP request started", map[string]interface{}{
		"method":      method,
		"path":        path,
		"remote_addr": remoteAddr,
	})

	// Simulate processing
	// ...

	requestLog.Info("HTTP request completed", map[string]interface{}{
		"method":      method,
		"path":        path,
		"duration_ms": 75,
		"status_code": 200,
	})
}
