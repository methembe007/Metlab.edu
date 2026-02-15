# Auth Handlers Implementation

## Overview

This document describes the implementation of HTTP handlers for authentication endpoints in the API Gateway service.

## Implemented Endpoints

### 1. POST /api/auth/teacher/signup

Creates a new teacher account.

**Request Body:**
```json
{
  "email": "teacher@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe",
  "subject_area": "Mathematics"
}
```

**Response (201 Created):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "uuid-here",
  "role": "teacher",
  "expires_at": 1234567890
}
```

**Validation Rules:**
- Email is required and must be valid format
- Password is required and must be at least 12 characters
- Full name is required and must be at least 2 characters
- Subject area is optional

### 2. POST /api/auth/teacher/login

Authenticates a teacher and returns a JWT token.

**Request Body:**
```json
{
  "email": "teacher@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "uuid-here",
  "role": "teacher",
  "expires_at": 1234567890
}
```

**Validation Rules:**
- Email is required and must be valid format
- Password is required

### 3. POST /api/auth/student/signin

Authenticates a student using a signin code.

**Request Body:**
```json
{
  "teacher_name": "John Doe",
  "student_name": "Jane Smith",
  "signin_code": "ABC12345"
}
```

**Response (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "uuid-here",
  "role": "student",
  "expires_at": 1234567890
}
```

**Validation Rules:**
- Teacher name is required and must be at least 2 characters
- Student name is required and must be at least 2 characters
- Signin code is required and must be exactly 8 characters

### 4. POST /api/auth/codes/generate

Generates a signin code for student registration.

**Request Body:**
```json
{
  "teacher_id": "uuid-here",
  "class_id": "uuid-here"
}
```

**Response (201 Created):**
```json
{
  "code": "ABC12345",
  "expires_at": 1234567890
}
```

**Validation Rules:**
- Teacher ID is required
- Class ID is required

## Implementation Details

### Request Validation

All endpoints perform comprehensive input validation before calling the gRPC service:

1. **Required Field Validation**: Ensures all required fields are present
2. **Format Validation**: Validates email format, string lengths, etc.
3. **Business Rule Validation**: Enforces business rules (e.g., password length, code format)

### Error Handling

The handlers use a consistent error handling approach:

1. **Validation Errors**: Return 400 Bad Request with detailed error message
2. **gRPC Errors**: Automatically converted to appropriate HTTP status codes
3. **Internal Errors**: Return 500 Internal Server Error

Error responses follow this format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "email is required"
  }
}
```

### gRPC Integration

Each handler:
1. Decodes the HTTP request body
2. Validates the input
3. Transforms HTTP request to gRPC request
4. Calls the appropriate gRPC service method with a 10-second timeout
5. Transforms gRPC response to HTTP response
6. Returns the response with appropriate status code

### Testing

Comprehensive unit tests are provided in `auth_test.go`:

- Tests for successful requests
- Tests for validation errors
- Tests for missing required fields
- Tests for invalid input formats
- Mock gRPC client for isolated testing

## Requirements Satisfied

This implementation satisfies the following requirements from the specification:

- **Requirement 2.1**: Teacher registration with email, password, full name, and subject area
- **Requirement 2.4**: JWT token generation for authentication
- **Requirement 3.1**: Signin code generation for student registration
- **Requirement 9.1**: Student authentication using signin codes

## Security Considerations

1. **Password Validation**: Enforces minimum 12-character password length
2. **Input Sanitization**: All inputs are validated before processing
3. **Timeout Protection**: All gRPC calls have 10-second timeouts
4. **Error Messages**: Error messages don't leak sensitive information

## Future Enhancements

Potential improvements for future iterations:

1. Add rate limiting per endpoint (currently handled at router level)
2. Add request logging with sanitized sensitive data
3. Add metrics collection for monitoring
4. Add more sophisticated email validation (DNS lookup, etc.)
5. Add password strength validation (uppercase, lowercase, numbers, special chars)
6. Add CAPTCHA support for signup endpoints

