#!/bin/bash
# Script to fix the gRPC version mismatch and rebuild analytics service

set -e

echo "=== Fixing Analytics Service Build ==="
echo ""

# Get the project root
PROJECT_ROOT="/home/metrix/git/Metlab.edu/cloud-native"

echo "Step 1: Update proto-gen dependencies..."
cd "$PROJECT_ROOT/shared/proto-gen"
go mod tidy
echo "✓ proto-gen dependencies updated"
echo ""

echo "Step 2: Update analytics service dependencies..."
cd "$PROJECT_ROOT/services/analytics"
go mod tidy
echo "✓ analytics dependencies updated"
echo ""

echo "Step 3: Regenerate proto files..."
cd "$PROJECT_ROOT"

# Check if protoc-gen-go-grpc is installed
if ! command -v protoc-gen-go-grpc &> /dev/null; then
    echo "Installing protoc-gen-go-grpc..."
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
fi

# Check if protoc-gen-go is installed
if ! command -v protoc-gen-go &> /dev/null; then
    echo "Installing protoc-gen-go..."
    go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
fi

# Regenerate analytics proto
echo "Regenerating analytics proto files..."
protoc \
    --proto_path=proto \
    --go_out=shared/proto-gen/go \
    --go_opt=paths=source_relative \
    --go-grpc_out=shared/proto-gen/go \
    --go-grpc_opt=paths=source_relative \
    proto/analytics/analytics.proto

echo "✓ Proto files regenerated"
echo ""

echo "Step 4: Update dependencies again after proto regeneration..."
cd "$PROJECT_ROOT/shared/proto-gen"
go mod tidy

cd "$PROJECT_ROOT/services/analytics"
go mod tidy
echo "✓ Dependencies updated"
echo ""

echo "Step 5: Build analytics service..."
cd "$PROJECT_ROOT/services/analytics"
go build -o analytics ./cmd/server

if [ $? -eq 0 ]; then
    echo ""
    echo "=== SUCCESS ==="
    echo "✓ Analytics service built successfully!"
    echo ""
    echo "You can now run the service with:"
    echo "  cd $PROJECT_ROOT/services/analytics"
    echo "  ./analytics"
else
    echo ""
    echo "=== BUILD FAILED ==="
    echo "Please check the error messages above."
    exit 1
fi
