# Errors Package

This package provides error handling utilities with gRPC status code integration for the Metlab.edu platform.

## Features

- Structured error types with gRPC status codes
- Error wrapping with additional context
- Error details and metadata
- Conversion between application errors and gRPC errors
- Helper functions for common error types
- Error type checking utilities

## Usage

### Basic Usage

```go
package main

import (
    "github.com/metlab/shared/errors"
)

func main() {
    // Create a simple error
    err := errors.NotFound("user not found")
    
    // Create an error with formatting
    err := errors.NotFoundf("user with id %s not found", userID)
    
    // Create an error with details
    err := errors.InvalidArgument("invalid email").
        WithDetail("field", "email").
        WithDetail("reason", "invalid format")
}
```

### Error Types

The package provides helper functions for common error types:

```go
// NOT_FOUND
err := errors.NotFound("resource not found")

// ALREADY_EXISTS
err := errors.AlreadyExists("user already exists")

// INVALID_ARGUMENT
err := errors.InvalidArgument("invalid input")

// UNAUTHENTICATED
err := errors.Unauthenticated("missing authentication token")

// PERMISSION_DENIED
err := errors.PermissionDenied("insufficient permissions")

// INTERNAL
err := errors.Internal("database connection failed")

// UNAVAILABLE
err := errors.Unavailable("service temporarily unavailable")

// DEADLINE_EXCEEDED
err := errors.DeadlineExceeded("request timeout")

// RESOURCE_EXHAUSTED
err := errors.ResourceExhausted("rate limit exceeded")

// ABORTED
err := errors.Aborted("transaction aborted")

// OUT_OF_RANGE
err := errors.OutOfRange("page number out of range")

// UNIMPLEMENTED
err := errors.Unimplemented("feature not implemented")

// DATA_LOSS
err := errors.DataLoss("data corruption detected")
```

### Wrapping Errors

```go
// Wrap an existing error with additional context
err := someOperation()
if err != nil {
    return errors.Wrap(err, codes.Internal, "failed to process user data")
}
```

### Adding Details

```go
// Add multiple details
err := errors.InvalidArgument("validation failed").
    WithDetails(map[string]string{
        "field": "email",
        "reason": "invalid format",
        "expected": "user@example.com",
    })

// Add a single detail
err := errors.NotFound("user not found").
    WithDetail("user_id", userID)
```

### Converting to gRPC Errors

```go
// Convert AppError to gRPC error
appErr := errors.NotFound("user not found")
grpcErr := appErr.ToGRPCStatus().Err()
return grpcErr

// Or use the helper function
err := someOperation()
if err != nil {
    return errors.ToGRPCError(err)
}
```

### Converting from gRPC Errors

```go
// Convert gRPC error to AppError
grpcErr := someGRPCCall()
appErr := errors.FromGRPCError(grpcErr)

fmt.Printf("Code: %v\nMessage: %s\n", appErr.Code, appErr.Message)
```

### Error Type Checking

```go
err := someOperation()

// Check if error is a specific type
if errors.IsNotFound(err) {
    // Handle not found error
}

if errors.IsInvalidArgument(err) {
    // Handle invalid argument error
}

if errors.IsUnauthenticated(err) {
    // Handle authentication error
}

if errors.IsPermissionDenied(err) {
    // Handle permission error
}
```

## Error Structure

The `AppError` type contains:

- `Code`: gRPC status code
- `Message`: Error message
- `Details`: Map of additional error details
- `Err`: Underlying error (if wrapped)

## gRPC Status Codes

The package uses the following gRPC status codes:

- `OK`: Success (not an error)
- `CANCELLED`: Operation was cancelled
- `UNKNOWN`: Unknown error
- `INVALID_ARGUMENT`: Invalid argument provided
- `DEADLINE_EXCEEDED`: Deadline expired before operation completed
- `NOT_FOUND`: Resource not found
- `ALREADY_EXISTS`: Resource already exists
- `PERMISSION_DENIED`: Caller doesn't have permission
- `RESOURCE_EXHAUSTED`: Resource has been exhausted (e.g., rate limit)
- `FAILED_PRECONDITION`: Operation rejected due to system state
- `ABORTED`: Operation was aborted
- `OUT_OF_RANGE`: Operation attempted past valid range
- `UNIMPLEMENTED`: Operation not implemented
- `INTERNAL`: Internal server error
- `UNAVAILABLE`: Service unavailable
- `DATA_LOSS`: Unrecoverable data loss or corruption
- `UNAUTHENTICATED`: Request lacks valid authentication

## Best Practices

1. **Use Specific Error Types**: Use the most specific error type for the situation
2. **Add Context**: Include relevant details to help with debugging
3. **Wrap Errors**: Wrap underlying errors to preserve the error chain
4. **Don't Expose Internal Details**: Be careful not to expose sensitive information in error messages
5. **Consistent Error Handling**: Use the same error handling patterns across services

## Integration with gRPC Services

### Server-Side Error Handling

```go
func (s *UserService) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.User, error) {
    user, err := s.repo.FindByID(ctx, req.UserId)
    if err != nil {
        if errors.IsNotFound(err) {
            return nil, errors.NotFoundf("user with id %s not found", req.UserId).
                WithDetail("user_id", req.UserId).
                ToGRPCStatus().Err()
        }
        return nil, errors.Wrap(err, codes.Internal, "failed to fetch user").
            ToGRPCStatus().Err()
    }
    
    return user, nil
}
```

### Client-Side Error Handling

```go
func (c *UserClient) GetUser(ctx context.Context, userID string) (*User, error) {
    resp, err := c.grpcClient.GetUser(ctx, &pb.GetUserRequest{
        UserId: userID,
    })
    if err != nil {
        appErr := errors.FromGRPCError(err)
        
        if appErr.Code == codes.NotFound {
            return nil, fmt.Errorf("user not found")
        }
        
        return nil, fmt.Errorf("failed to get user: %w", appErr)
    }
    
    return resp, nil
}
```

### HTTP API Error Responses

```go
func handleError(w http.ResponseWriter, err error) {
    appErr := errors.FromGRPCError(err)
    
    var statusCode int
    switch appErr.Code {
    case codes.NotFound:
        statusCode = http.StatusNotFound
    case codes.InvalidArgument:
        statusCode = http.StatusBadRequest
    case codes.Unauthenticated:
        statusCode = http.StatusUnauthorized
    case codes.PermissionDenied:
        statusCode = http.StatusForbidden
    case codes.AlreadyExists:
        statusCode = http.StatusConflict
    case codes.ResourceExhausted:
        statusCode = http.StatusTooManyRequests
    default:
        statusCode = http.StatusInternalServerError
    }
    
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(statusCode)
    
    json.NewEncoder(w).Encode(map[string]interface{}{
        "error": map[string]interface{}{
            "code":    appErr.Code.String(),
            "message": appErr.Message,
            "details": appErr.Details,
        },
    })
}
```

## Common Error Patterns

### Validation Errors

```go
func validateEmail(email string) error {
    if !isValidEmail(email) {
        return errors.InvalidArgument("invalid email format").
            WithDetail("field", "email").
            WithDetail("value", email)
    }
    return nil
}
```

### Database Errors

```go
func (r *UserRepository) Create(ctx context.Context, user *User) error {
    err := r.db.Insert(ctx, user)
    if err != nil {
        if isDuplicateKeyError(err) {
            return errors.AlreadyExists("user with this email already exists").
                WithDetail("email", user.Email)
        }
        return errors.Wrap(err, codes.Internal, "failed to create user")
    }
    return nil
}
```

### Authentication Errors

```go
func (s *AuthService) ValidateToken(token string) (*Claims, error) {
    claims, err := s.tokenManager.ValidateToken(token)
    if err != nil {
        if errors.Is(err, jwt.ErrExpiredToken) {
            return nil, errors.Unauthenticated("token has expired")
        }
        return nil, errors.Unauthenticated("invalid token")
    }
    return claims, nil
}
```

### Authorization Errors

```go
func (s *VideoService) DeleteVideo(ctx context.Context, videoID, userID string) error {
    video, err := s.repo.FindByID(ctx, videoID)
    if err != nil {
        return err
    }
    
    if video.TeacherID != userID {
        return errors.PermissionDenied("you don't have permission to delete this video").
            WithDetail("video_id", videoID).
            WithDetail("user_id", userID)
    }
    
    return s.repo.Delete(ctx, videoID)
}
```
