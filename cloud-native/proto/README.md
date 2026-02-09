# Protocol Buffer Definitions

This directory contains Protocol Buffer (proto3) definitions for all microservices in the Metlab.edu cloud-native architecture.

## Directory Structure

```
proto/
├── auth/               # Authentication service
├── video/              # Video management service
├── homework/           # Homework submission and grading service
├── analytics/          # Analytics and tracking service
├── collaboration/      # Study groups and chat service
└── pdf/                # PDF document management service
```

## Services Overview

### Auth Service (`auth/auth.proto`)
Handles user authentication and authorization:
- Teacher signup and login
- Student signin with codes
- JWT token validation
- Signin code generation

### Video Service (`video/video.proto`)
Manages video content:
- Video upload and storage
- Video streaming URL generation
- View tracking
- Video analytics for teachers

### Homework Service (`homework/homework.proto`)
Manages homework assignments:
- Assignment creation
- Homework submission
- Grading and feedback
- Submission file retrieval

### Analytics Service (`analytics/analytics.proto`)
Tracks user activity:
- Login tracking
- Student engagement metrics
- Class-wide statistics
- PDF download tracking

### Collaboration Service (`collaboration/collaboration.proto`)
Enables student collaboration:
- Study group creation and management
- Chat room creation
- Real-time messaging
- Message history retrieval

### PDF Service (`pdf/pdf.proto`)
Manages PDF documents:
- PDF upload and storage
- PDF listing
- Secure download URL generation

## Prerequisites

### Install Protocol Buffer Compiler

**Windows:**
```powershell
# Using Chocolatey
choco install protoc

# Or download from:
# https://github.com/protocolbuffers/protobuf/releases
```

**macOS:**
```bash
brew install protobuf
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install protobuf-compiler
```

### Install Language Plugins

**Go plugins:**
```bash
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
```

**TypeScript plugin:**
```bash
npm install -g ts-proto
```

## Quick Start

### Automated Installation (Recommended)

**Windows:**
```powershell
cd cloud-native
.\scripts\install-proto-tools.ps1
```

**macOS/Linux:**
```bash
cd cloud-native
chmod +x scripts/install-proto-tools.sh
./scripts/install-proto-tools.sh
```

### Generate Code

**Windows:**
```powershell
cd cloud-native
.\scripts\generate-proto.ps1
```

**macOS/Linux:**
```bash
cd cloud-native
chmod +x scripts/generate-proto.sh
./scripts/generate-proto.sh
```

**Using Make:**
```bash
cd cloud-native
make proto-gen
```

## Generated Code

Generated code will be placed in:
- **Go:** `shared/proto-gen/go/`
- **TypeScript:** `frontend/src/proto-gen/`

## Usage Examples

### Go Service Implementation

```go
package main

import (
    pb "metlab/proto/auth"
    "google.golang.org/grpc"
)

type authServer struct {
    pb.UnimplementedAuthServiceServer
}

func (s *authServer) TeacherLogin(ctx context.Context, req *pb.LoginRequest) (*pb.AuthResponse, error) {
    // Implementation
    return &pb.AuthResponse{
        Token: "jwt-token",
        UserId: "user-id",
        Role: "teacher",
    }, nil
}
```

### TypeScript Client Usage

```typescript
import { AuthServiceClient } from './proto-gen/auth/auth';

const client = new AuthServiceClient('http://localhost:8080');

const response = await client.TeacherLogin({
  email: 'teacher@example.com',
  password: 'password123'
});

console.log('Token:', response.token);
```

## Modifying Proto Files

When modifying proto files:

1. Edit the `.proto` file in the appropriate service directory
2. Regenerate code: `make proto-gen` or run the generation script
3. Update service implementations to match new definitions
4. Update client code if interfaces changed

## Best Practices

1. **Versioning:** Use semantic versioning for breaking changes
2. **Backward Compatibility:** Add new fields instead of modifying existing ones
3. **Field Numbers:** Never reuse field numbers
4. **Comments:** Document all messages and fields
5. **Naming:** Use snake_case for field names (converted to camelCase in generated code)

## Troubleshooting

### protoc not found
Ensure protoc is installed and in your PATH:
```bash
protoc --version
```

### Plugin not found
Ensure Go/TypeScript plugins are installed:
```bash
# Go plugins
which protoc-gen-go
which protoc-gen-go-grpc

# TypeScript plugin
which protoc-gen-ts_proto
```

### Generation fails
1. Check that all proto files have valid syntax
2. Ensure output directories exist
3. Verify plugin versions are compatible

## References

- [Protocol Buffers Documentation](https://protobuf.dev/)
- [gRPC Documentation](https://grpc.io/docs/)
- [proto3 Language Guide](https://protobuf.dev/programming-guides/proto3/)
- [ts-proto Documentation](https://github.com/stephenh/ts-proto)
