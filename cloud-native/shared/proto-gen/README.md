# Generated Protocol Buffer Code (Go)

This directory contains Go code generated from Protocol Buffer definitions.

## ⚠️ Do Not Edit

Files in this directory are automatically generated. Do not edit them manually.

## Regenerating Code

To regenerate the code after modifying proto files:

```bash
# From cloud-native directory
make proto-gen

# Or run the script directly
./scripts/generate-proto.sh    # macOS/Linux
.\scripts\generate-proto.ps1   # Windows
```

## Structure

```
go/
├── auth/
│   ├── auth.pb.go              # Message definitions
│   └── auth_grpc.pb.go         # gRPC service stubs
├── video/
│   ├── video.pb.go
│   └── video_grpc.pb.go
├── homework/
│   ├── homework.pb.go
│   └── homework_grpc.pb.go
├── analytics/
│   ├── analytics.pb.go
│   └── analytics_grpc.pb.go
├── collaboration/
│   ├── collaboration.pb.go
│   └── collaboration_grpc.pb.go
└── pdf/
    ├── pdf.pb.go
    └── pdf_grpc.pb.go
```

## Usage in Go Services

```go
import (
    pb "metlab/proto/auth"
)

// Use the generated types
req := &pb.LoginRequest{
    Email:    "user@example.com",
    Password: "password",
}
```

## Source Files

The source proto files are located in: `../proto/`
