# Protocol Buffers Setup Guide

This guide walks you through setting up Protocol Buffers for the Metlab.edu cloud-native architecture.

## Overview

Protocol Buffers (protobuf) is used for defining service interfaces and data structures across all microservices. We use proto3 syntax with gRPC for service-to-service communication.

## Quick Start

### 1. Install Tools

**Windows (PowerShell):**
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

**Using Make:**
```bash
make proto-install
```

### 2. Generate Code

**Windows (PowerShell):**
```powershell
.\scripts\generate-proto.ps1
```

**macOS/Linux:**
```bash
./scripts/generate-proto.sh
```

**Using Make:**
```bash
make proto-gen
```

## Manual Installation

If the automated scripts don't work, follow these manual installation steps:

### Install protoc Compiler

**Windows:**
1. Download the latest release from [GitHub](https://github.com/protocolbuffers/protobuf/releases)
2. Extract `protoc.exe` to a directory (e.g., `C:\protoc\bin`)
3. Add the directory to your PATH environment variable
4. Verify: `protoc --version`

**macOS:**
```bash
brew install protobuf
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y protobuf-compiler
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install -y protobuf-compiler
```

### Install Go Plugins

```bash
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
```

Add Go bin to PATH if not already:
```bash
export PATH="$PATH:$(go env GOPATH)/bin"
```

### Install TypeScript Plugin

```bash
npm install -g ts-proto
```

Or install locally in the frontend project:
```bash
cd frontend
npm install --save-dev ts-proto
```

## Proto File Structure

```
proto/
├── auth/
│   └── auth.proto              # Authentication service
├── video/
│   └── video.proto             # Video management service
├── homework/
│   └── homework.proto          # Homework service
├── analytics/
│   └── analytics.proto         # Analytics service
├── collaboration/
│   └── collaboration.proto     # Study groups and chat
└── pdf/
    └── pdf.proto               # PDF document service
```

## Generated Code Structure

After running code generation:

```
shared/proto-gen/go/
├── auth/
│   ├── auth.pb.go              # Message definitions
│   └── auth_grpc.pb.go         # gRPC service definitions
├── video/
│   ├── video.pb.go
│   └── video_grpc.pb.go
└── ...

frontend/src/proto-gen/
├── auth/
│   └── auth.ts                 # TypeScript definitions
├── video/
│   └── video.ts
└── ...
```

## Service Definitions

### Auth Service
- Teacher signup and login
- Student signin with codes
- Token validation
- Signin code generation

### Video Service
- Video upload (streaming)
- Video listing and retrieval
- Streaming URL generation
- View tracking and analytics

### Homework Service
- Assignment creation
- Homework submission (streaming)
- Submission listing
- Grading
- File download (streaming)

### Analytics Service
- Login tracking
- Student login statistics
- Class engagement metrics
- PDF download tracking

### Collaboration Service
- Study group creation and management
- Chat room creation
- Message sending and retrieval
- Real-time message streaming

### PDF Service
- PDF upload (streaming)
- PDF listing
- Download URL generation

## Usage Examples

### Go Server Implementation

```go
package main

import (
    "context"
    pb "metlab/proto/auth"
    "google.golang.org/grpc"
)

type authServer struct {
    pb.UnimplementedAuthServiceServer
}

func (s *authServer) TeacherLogin(
    ctx context.Context,
    req *pb.LoginRequest,
) (*pb.AuthResponse, error) {
    // Validate credentials
    // Generate JWT token
    
    return &pb.AuthResponse{
        Token:     "jwt-token-here",
        UserId:    "user-uuid",
        Role:      "teacher",
        ExpiresAt: time.Now().Add(24 * time.Hour).Unix(),
    }, nil
}

func main() {
    lis, _ := net.Listen("tcp", ":50051")
    grpcServer := grpc.NewServer()
    pb.RegisterAuthServiceServer(grpcServer, &authServer{})
    grpcServer.Serve(lis)
}
```

### Go Client Usage

```go
package main

import (
    "context"
    pb "metlab/proto/auth"
    "google.golang.org/grpc"
)

func main() {
    conn, _ := grpc.Dial("localhost:50051", grpc.WithInsecure())
    defer conn.Close()
    
    client := pb.NewAuthServiceClient(conn)
    
    resp, err := client.TeacherLogin(context.Background(), &pb.LoginRequest{
        Email:    "teacher@example.com",
        Password: "password123",
    })
    
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Println("Token:", resp.Token)
}
```

### TypeScript Client Usage

```typescript
import { AuthServiceClient } from './proto-gen/auth/auth';
import { LoginRequest } from './proto-gen/auth/auth';

const client = new AuthServiceClient('http://localhost:8080');

async function login() {
  const request: LoginRequest = {
    email: 'teacher@example.com',
    password: 'password123'
  };
  
  const response = await client.TeacherLogin(request);
  console.log('Token:', response.token);
  console.log('User ID:', response.userId);
}
```

## Modifying Proto Files

When you need to modify proto definitions:

1. **Edit the proto file** in the appropriate service directory
2. **Regenerate code** using `make proto-gen` or the generation script
3. **Update implementations** in both server and client code
4. **Test thoroughly** to ensure compatibility

### Best Practices

1. **Never reuse field numbers** - Once a field number is used, it's reserved forever
2. **Add new fields, don't modify existing ones** - This maintains backward compatibility
3. **Use optional for new fields** - Allows older clients to work with newer servers
4. **Document all messages and fields** - Use comments in proto files
5. **Version your APIs** - Consider using package versioning (e.g., `package auth.v1`)

### Example: Adding a New Field

```protobuf
// Before
message TeacherSignupRequest {
  string email = 1;
  string password = 2;
  string full_name = 3;
  string subject_area = 4;
}

// After - Adding a new optional field
message TeacherSignupRequest {
  string email = 1;
  string password = 2;
  string full_name = 3;
  string subject_area = 4;
  optional string phone_number = 5;  // New field
}
```

## Troubleshooting

### protoc command not found

**Solution:**
- Ensure protoc is installed
- Check that protoc is in your PATH
- On Windows, restart your terminal after adding to PATH

```bash
# Verify installation
protoc --version
```

### protoc-gen-go not found

**Solution:**
- Install the Go plugins
- Ensure Go bin directory is in PATH

```bash
# Install plugins
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$PATH:$(go env GOPATH)/bin"
```

### TypeScript generation fails

**Solution:**
- Install ts-proto globally or locally
- Ensure the plugin is accessible

```bash
# Global installation
npm install -g ts-proto

# Or local installation
cd frontend
npm install --save-dev ts-proto
```

### Import errors in generated code

**Solution:**
- Ensure all proto dependencies are generated
- Check import paths in proto files
- Regenerate all proto files

```bash
make proto-gen
```

### Permission denied on scripts

**Solution (macOS/Linux):**
```bash
chmod +x scripts/*.sh
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Generate Proto

on:
  push:
    paths:
      - 'proto/**'

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install protoc
        run: |
          sudo apt-get update
          sudo apt-get install -y protobuf-compiler
      
      - name: Install Go plugins
        run: |
          go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
          go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
      
      - name: Generate code
        run: make proto-gen
      
      - name: Commit generated code
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add shared/proto-gen frontend/src/proto-gen
          git commit -m "chore: regenerate proto code" || true
          git push
```

## Additional Resources

- [Protocol Buffers Documentation](https://protobuf.dev/)
- [gRPC Documentation](https://grpc.io/docs/)
- [proto3 Language Guide](https://protobuf.dev/programming-guides/proto3/)
- [Go gRPC Tutorial](https://grpc.io/docs/languages/go/quickstart/)
- [ts-proto Documentation](https://github.com/stephenh/ts-proto)

## Support

If you encounter issues:

1. Check this documentation
2. Review the troubleshooting section
3. Check the proto file syntax
4. Verify all tools are installed correctly
5. Try regenerating from scratch: `make clean && make proto-gen`
