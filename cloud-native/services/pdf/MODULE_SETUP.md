# PDF Service Module Setup

## Module Dependencies

The PDF service depends on two local modules:

1. **github.com/metlab/shared** - Shared utilities (db, logger, storage, etc.)
2. **metlab/proto-gen** - Generated protobuf code

## Go Module Configuration

The `go.mod` file uses replace directives to reference local modules:

```go
module github.com/metlab/pdf

replace github.com/metlab/shared => ../../shared
replace metlab/proto-gen => ../../shared/proto-gen
```

## Import Paths

### Shared Utilities
```go
import (
    "github.com/metlab/shared/db"
    "github.com/metlab/shared/logger"
    "github.com/metlab/shared/storage"
)
```

### Proto-gen (Generated gRPC Code)
```go
import (
    pb "metlab/proto-gen/go/pdf"
)
```

Note: The proto-gen import uses `metlab/proto-gen` (not `github.com/metlab/shared/proto-gen`) because proto-gen is a separate Go module within the shared directory.

## Building

To build the service, ensure you're in the service directory:

```bash
cd cloud-native/services/pdf
go mod download  # Download dependencies
go build -o pdf-service ./cmd/server
```

## Common Issues

### Issue: "module github.com/metlab/shared@latest found but does not contain package"

**Solution**: Make sure the replace directives are present in go.mod:
```go
replace github.com/metlab/shared => ../../shared
replace metlab/proto-gen => ../../shared/proto-gen
```

### Issue: "cannot find package metlab/proto-gen"

**Solution**: Ensure the proto files have been generated:
```bash
cd cloud-native
make proto  # or ./scripts/generate-proto.sh
```

### Issue: WSL path errors when running go mod tidy

**Solution**: This is a known Windows/WSL interop issue. The code will still compile correctly. You can safely ignore this error or run the command from within WSL directly.

## Verification

To verify the module setup is correct:

```bash
# Check if imports resolve (should show no errors)
go list -m all

# Build the service
go build ./cmd/server

# Run tests
go test ./...
```

## Docker Build

The Dockerfile handles module dependencies automatically:

```dockerfile
COPY go.mod go.sum ./
COPY ../../shared /shared
RUN go mod download
```

This ensures both the shared module and proto-gen are available during the Docker build.
