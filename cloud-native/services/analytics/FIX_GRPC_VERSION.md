# Fix gRPC Version Mismatch

## Problem

The analytics service fails to compile with the following errors:
```
undefined: grpc.SupportPackageIsVersion9
undefined: grpc.StaticMethod
```

## Root Cause

The proto files in `shared/proto-gen/go/analytics/` were generated with a newer version of `protoc-gen-go-grpc` that expects gRPC v1.65+, but the analytics service's `go.mod` was using gRPC v1.60.1.

## Solution

I've updated the `go.mod` files to use gRPC v1.79.1 (matching the video and homework services). Now you need to update the dependencies.

## Steps to Fix

### Option 1: Update Dependencies (Recommended)

Since you're working from Windows accessing WSL files, you'll need to run the go commands from within WSL:

```bash
# Open WSL terminal
wsl

# Navigate to the project
cd /home/metrix/git/Metlab.edu/cloud-native/shared/proto-gen
go mod tidy

cd /home/metrix/git/Metlab.edu/cloud-native/services/analytics
go mod tidy

# Try building
go build -o analytics ./cmd/server
```

### Option 2: Regenerate Proto Files

If Option 1 doesn't work, regenerate the proto files with the correct version:

```bash
# In WSL
cd /home/metrix/git/Metlab.edu/cloud-native

# Install/update proto tools
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# Regenerate proto files
./scripts/generate-proto.sh

# Update dependencies
cd services/analytics
go mod tidy

# Build
go build -o analytics ./cmd/server
```

### Option 3: Quick Fix (If above don't work)

If you just need to verify the implementation without building, you can:

1. Review the code logic (which is correct)
2. Test using an already-built binary from another service
3. Deploy using Docker (which will build in a Linux environment)

## Changes Made

### Updated Files

1. **cloud-native/services/analytics/go.mod**
   - Changed `google.golang.org/grpc v1.60.1` → `v1.79.1`

2. **cloud-native/shared/proto-gen/go.mod**
   - Changed `google.golang.org/grpc v1.60.1` → `v1.79.1`
   - Changed `google.golang.org/protobuf v1.32.0` → `v1.36.11`

## Verification

After fixing, verify the build works:

```bash
cd /home/metrix/git/Metlab.edu/cloud-native/services/analytics
go build -o analytics ./cmd/server
./analytics
```

Expected output:
```
Successfully connected to database
Analytics service starting on port 50053
```

## Why This Happened

The proto files were likely generated on a different machine or at a different time with a newer version of the protoc-gen-go-grpc plugin. The generated code uses features from gRPC v1.65+ (like `grpc.StaticMethod` and `SupportPackageIsVersion9`) that aren't available in v1.60.1.

## Prevention

To prevent this in the future:
1. Keep all services on the same gRPC version
2. Regenerate proto files when updating gRPC versions
3. Document the protoc-gen-go-grpc version used
4. Consider adding a version check in the generation script
