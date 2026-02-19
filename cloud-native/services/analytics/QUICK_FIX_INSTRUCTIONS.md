# Quick Fix Instructions for Analytics Service Build

## Problem
The analytics service fails to build due to gRPC version mismatch between generated proto files and the go.mod dependencies.

## Solution
Run the automated fix script in WSL.

## Steps

### 1. Open WSL Terminal
```bash
wsl
```

### 2. Navigate to the analytics service directory
```bash
cd /home/metrix/git/Metlab.edu/cloud-native/services/analytics
```

### 3. Make the fix script executable
```bash
chmod +x fix-build.sh
```

### 4. Run the fix script
```bash
./fix-build.sh
```

The script will:
1. Update proto-gen dependencies
2. Update analytics service dependencies
3. Regenerate the analytics proto files with the correct gRPC version
4. Update dependencies again
5. Build the analytics service

## Expected Output

```
=== Fixing Analytics Service Build ===

Step 1: Update proto-gen dependencies...
✓ proto-gen dependencies updated

Step 2: Update analytics service dependencies...
✓ analytics dependencies updated

Step 3: Regenerate proto files...
Regenerating analytics proto files...
✓ Proto files regenerated

Step 4: Update dependencies again after proto regeneration...
✓ Dependencies updated

Step 5: Build analytics service...

=== SUCCESS ===
✓ Analytics service built successfully!

You can now run the service with:
  cd /home/metrix/git/Metlab.edu/cloud-native/services/analytics
  ./analytics
```

## Manual Alternative

If you prefer to run the commands manually:

```bash
# In WSL
cd /home/metrix/git/Metlab.edu/cloud-native

# Update dependencies
cd shared/proto-gen
go mod tidy

cd ../services/analytics
go mod tidy

# Install proto tools if needed
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# Regenerate analytics proto
cd /home/metrix/git/Metlab.edu/cloud-native
protoc \
    --proto_path=proto \
    --go_out=shared/proto-gen/go \
    --go_opt=paths=source_relative \
    --go-grpc_out=shared/proto-gen/go \
    --go-grpc_opt=paths=source_relative \
    proto/analytics/analytics.proto

# Update dependencies again
cd shared/proto-gen
go mod tidy

cd ../services/analytics
go mod tidy

# Build
go build -o analytics ./cmd/server
```

## Verification

After the build succeeds, verify the service works:

```bash
# Start the service (requires database to be running)
./analytics

# In another terminal, test with grpcurl
grpcurl -plaintext localhost:50053 list
```

Expected output:
```
analytics.AnalyticsService
grpc.health.v1.Health
grpc.reflection.v1alpha.ServerReflection
```

## Troubleshooting

### If protoc-gen-go-grpc is not found
```bash
export PATH=$PATH:$(go env GOPATH)/bin
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
```

### If build still fails
Check the error message and ensure:
1. Go version is 1.21 or higher: `go version`
2. Protoc is installed: `protoc --version`
3. All dependencies are downloaded: `go mod download`

### If you get "permission denied"
```bash
chmod +x fix-build.sh
```

## What Changed

The fix updates:
- `go.mod` files to use gRPC v1.79.1 (from v1.60.1)
- Regenerates proto files with the newer gRPC version
- Updates all transitive dependencies

This aligns the analytics service with the video and homework services which already use gRPC v1.79.1.
