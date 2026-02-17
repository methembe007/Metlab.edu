# Build Notes for Homework Service

## WSL File System Issue

If you encounter the error:
```
go: RLock \\wsl.localhost\Ubuntu\...\go.mod: Incorrect function.
```

This is a known issue with Go accessing files through WSL network paths from Windows PowerShell.

### Solutions:

#### Option 1: Run from WSL Terminal (Recommended)
```bash
# Open WSL terminal (Ubuntu)
cd /home/metrix/git/Metlab.edu/cloud-native/services/homework
go mod tidy
go build -o bin/homework-service ./cmd/server
```

#### Option 2: Run from Linux Environment
```bash
# SSH into Linux machine or use native Linux
cd cloud-native/services/homework
make build
```

#### Option 3: Use Docker Build
```bash
# Build using Docker (works from Windows)
cd cloud-native/services/homework
docker build -t metlab/homework-service:latest .
```

## Verification Steps

Once you can run `go mod tidy`, verify the build:

1. **Tidy dependencies**:
   ```bash
   go mod tidy
   ```

2. **Build the service**:
   ```bash
   go build -o bin/homework-service ./cmd/server
   ```

3. **Run tests** (when implemented):
   ```bash
   go test ./...
   ```

4. **Check for issues**:
   ```bash
   go vet ./...
   ```

## Import Path Fix Applied

The proto import paths have been corrected from:
- ❌ `github.com/metlab/shared/proto-gen/homework`

To:
- ✅ `github.com/metlab/shared/proto-gen/go/homework`

This matches the actual directory structure where the generated proto files are located.

## Dependencies

The service depends on:
- `github.com/metlab/shared` (via replace directive to `../../shared`)
- `github.com/jackc/pgx/v5` for PostgreSQL
- `google.golang.org/grpc` for gRPC
- `google.golang.org/protobuf` for protobuf

All transitive dependencies from the shared package are included.

## Next Steps

1. Run `go mod tidy` from WSL or Linux environment
2. Build the service: `make build`
3. Run locally: `make run` (after configuring .env)
4. Deploy to Kubernetes: `kubectl apply -f k8s/deployment.yaml`

## Status

✅ Code is syntactically correct (verified with getDiagnostics)
✅ Import paths are correct
✅ go.mod is properly configured
⚠️ Need to run `go mod tidy` from WSL/Linux environment
⚠️ Need to generate go.sum file

The implementation is complete and ready for building once the WSL file system issue is resolved.
