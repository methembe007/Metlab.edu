# JWT Package

This package provides JWT token generation and validation for the Metlab.edu platform.

## Features

- Generate JWT tokens for teachers and students with different expiration times
- Validate JWT tokens and extract claims
- Refresh expired tokens
- Extract user information without full validation
- Support for custom claims

## Usage

### Basic Usage

```go
package main

import (
    "fmt"
    "github.com/metlab/shared/jwt"
)

func main() {
    // Create a token manager
    config := &jwt.Config{
        SecretKey:            "your-secret-key",
        Issuer:               "metlab.edu",
        TeacherTokenDuration: 24 * time.Hour,
        StudentTokenDuration: 7 * 24 * time.Hour,
    }
    tm := jwt.NewTokenManager(config)

    // Generate a teacher token
    token, expiresAt, err := tm.GenerateTeacherToken("teacher-123", []string{"class-1", "class-2"})
    if err != nil {
        panic(err)
    }
    fmt.Printf("Token: %s\nExpires at: %d\n", token, expiresAt)

    // Validate the token
    claims, err := tm.ValidateToken(token)
    if err != nil {
        panic(err)
    }
    fmt.Printf("User ID: %s\nRole: %s\n", claims.UserID, claims.Role)
}
```

### Generate Student Token

```go
// Generate a student token
token, expiresAt, err := tm.GenerateStudentToken(
    "student-456",
    "teacher-123",
    []string{"class-1"},
)
```

### Refresh Token

```go
// Refresh an expired token
newToken, expiresAt, err := tm.RefreshToken(oldToken)
if err != nil {
    panic(err)
}
```

### Extract Information Without Validation

```go
// Extract user ID without full validation (useful for logging)
userID, err := tm.ExtractUserID(token)

// Extract role without full validation
role, err := tm.ExtractRole(token)
```

## Token Claims

The JWT tokens include the following claims:

- `user_id`: Unique identifier for the user
- `role`: User role ("teacher" or "student")
- `teacher_id`: Teacher ID (only for students)
- `class_ids`: Array of class IDs the user has access to
- `exp`: Expiration time
- `iat`: Issued at time
- `iss`: Issuer
- `sub`: Subject (same as user_id)

## Configuration

### Config Fields

- `SecretKey`: Secret key for signing tokens (required)
- `Issuer`: Token issuer (default: "metlab.edu")
- `TeacherTokenDuration`: Token duration for teachers (default: 24 hours)
- `StudentTokenDuration`: Token duration for students (default: 7 days)

## Error Handling

The package defines the following errors:

- `ErrInvalidToken`: Token is invalid or malformed
- `ErrExpiredToken`: Token has expired
- `ErrInvalidClaims`: Token claims are invalid

## Security Considerations

1. **Secret Key**: Use a strong, randomly generated secret key in production
2. **Token Storage**: Store tokens securely (httpOnly cookies for web, secure storage for mobile)
3. **Token Expiration**: Use appropriate expiration times based on security requirements
4. **Token Refresh**: Implement token refresh to avoid forcing users to re-authenticate frequently
5. **HTTPS**: Always transmit tokens over HTTPS in production
