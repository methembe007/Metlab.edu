# Auth Handler Implementation

This directory contains the gRPC handler implementation for the Authentication Service.

## Current Status

The handler has been implemented with placeholder signatures. Once the Protocol Buffer files are generated, the following updates need to be made:

### Steps to Complete Integration

1. **Generate Proto Files**
   ```bash
   # From cloud-native directory
   make proto-gen
   # Or on Windows:
   powershell -ExecutionPolicy Bypass -File scripts/generate-proto.ps1
   ```

2. **Update Handler Imports**
   In `auth_handler.go`, uncomment and update the proto import:
   ```go
   pb "metlab/proto-gen/go/auth"
   ```

3. **Update Handler Struct**
   Uncomment the embedded interface:
   ```go
   type AuthHandler struct {
       pb.UnimplementedAuthServiceServer
       authService *service.AuthService
   }
   ```

4. **Update Method Signatures**
   Replace placeholder signatures with actual proto types:
   
   **TeacherSignup:**
   ```go
   func (h *AuthHandler) TeacherSignup(ctx context.Context, req *pb.TeacherSignupRequest) (*pb.AuthResponse, error) {
       email := req.Email
       password := req.Password
       fullName := req.FullName
       subjectArea := req.SubjectArea
       
       // ... rest of implementation
       
       return &pb.AuthResponse{
           Token:     token,
           UserId:    user.ID.String(),
           Role:      string(user.Role),
           ExpiresAt: expiresAt,
       }, nil
   }
   ```
   
   **TeacherLogin:**
   ```go
   func (h *AuthHandler) TeacherLogin(ctx context.Context, req *pb.LoginRequest) (*pb.AuthResponse, error) {
       email := req.Email
       password := req.Password
       
       // ... rest of implementation
       
       return &pb.AuthResponse{
           Token:     token,
           UserId:    user.ID.String(),
           Role:      string(user.Role),
           ExpiresAt: expiresAt,
       }, nil
   }
   ```

5. **Update Main Server**
   In `cmd/server/main.go`, uncomment the handler registration:
   ```go
   import pb "metlab/proto-gen/go/auth"
   
   // In main():
   pb.RegisterAuthServiceServer(grpcServer, handler.NewAuthHandler(authService))
   ```

## Implementation Details

### TeacherSignup Handler

**Functionality:**
- Validates required fields (email, password, full_name)
- Calls the service layer to create teacher account
- Maps service errors to appropriate gRPC status codes
- Returns JWT token with 24-hour expiration

**Error Handling:**
- `INVALID_ARGUMENT`: Missing required fields or invalid password format
- `ALREADY_EXISTS`: Email already registered
- `INTERNAL`: Unexpected server errors

**Password Requirements:**
- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

### TeacherLogin Handler

**Functionality:**
- Validates required fields (email, password)
- Extracts IP address from gRPC metadata for tracking
- Implements account lockout after 5 failed attempts within 15 minutes
- Calls the service layer to authenticate teacher
- Returns JWT token with 24-hour expiration

**Error Handling:**
- `INVALID_ARGUMENT`: Missing required fields
- `UNAUTHENTICATED`: Invalid credentials
- `PERMISSION_DENIED`: Account locked or inactive
- `INTERNAL`: Unexpected server errors

**Account Lockout:**
- Tracks failed login attempts in database
- Locks account for 30 minutes after 5 failed attempts
- Resets counter after successful login

### IP Address Extraction

The handler extracts the client IP address from gRPC metadata for login tracking:
- Checks `x-forwarded-for` header first (for proxied requests)
- Falls back to `x-real-ip` header
- Used for security auditing and rate limiting

## Testing

Once proto files are generated, you can test the handlers using:

```bash
# Run unit tests
cd cloud-native/services/auth
go test ./internal/handler/... -v

# Test with grpcurl (requires running server)
grpcurl -plaintext -d '{
  "email": "teacher@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "subject_area": "Mathematics"
}' localhost:50051 auth.AuthService/TeacherSignup
```

## Requirements Satisfied

This implementation satisfies the following requirements from the design document:

- **Requirement 2.1**: Teacher registration with email, password, full name, and subject area
- **Requirement 2.2**: Email verification and account creation within 5 seconds
- **Requirement 2.3**: Password requirements enforcement (12+ chars, mixed case, numbers, special chars)
- **Requirement 2.4**: JWT token generation with 24-hour validity
- **Requirement 2.5**: Account lockout after 5 failed login attempts within 15 minutes

## Next Steps

1. Generate proto files using the proto generation script
2. Update handler with actual proto types
3. Register handler in main server
4. Write unit tests for handler methods
5. Test end-to-end with gRPC client
