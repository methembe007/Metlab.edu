#!/bin/bash

# Script to generate Go and TypeScript code from Protocol Buffer definitions
# This script should be run from the cloud-native directory

set -e

echo "=== Protocol Buffer Code Generation ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if protoc is installed
if ! command -v protoc &> /dev/null; then
    echo -e "${RED}Error: protoc compiler not found${NC}"
    echo "Please install protoc:"
    echo "  - macOS: brew install protobuf"
    echo "  - Ubuntu/Debian: apt-get install protobuf-compiler"
    echo "  - Windows: Download from https://github.com/protocolbuffers/protobuf/releases"
    exit 1
fi

echo -e "${BLUE}Found protoc version:${NC}"
protoc --version
echo ""

# Check if Go plugins are installed
if ! command -v protoc-gen-go &> /dev/null; then
    echo -e "${RED}Error: protoc-gen-go not found${NC}"
    echo "Installing Go protobuf plugins..."
    go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
fi

# Check if TypeScript plugin is installed
if ! command -v protoc-gen-ts &> /dev/null; then
    echo -e "${BLUE}Note: protoc-gen-ts not found${NC}"
    echo "To generate TypeScript code, install:"
    echo "  npm install -g ts-proto"
    echo ""
fi

# Create output directories
echo -e "${BLUE}Creating output directories...${NC}"
mkdir -p shared/proto-gen/go
mkdir -p frontend/src/proto-gen

# Array of proto files
PROTO_SERVICES=(
    "auth"
    "video"
    "homework"
    "analytics"
    "collaboration"
    "pdf"
)

# Generate Go code
echo -e "${GREEN}Generating Go code...${NC}"
for service in "${PROTO_SERVICES[@]}"; do
    echo "  - Generating $service..."
    protoc \
        --proto_path=proto \
        --go_out=shared/proto-gen/go \
        --go_opt=paths=source_relative \
        --go-grpc_out=shared/proto-gen/go \
        --go-grpc_opt=paths=source_relative \
        proto/$service/$service.proto
done

echo -e "${GREEN}✓ Go code generation complete${NC}"
echo ""

# Generate TypeScript code (if ts-proto is available)
if command -v protoc-gen-ts_proto &> /dev/null || [ -f "node_modules/.bin/protoc-gen-ts_proto" ]; then
    echo -e "${GREEN}Generating TypeScript code...${NC}"
    for service in "${PROTO_SERVICES[@]}"; do
        echo "  - Generating $service..."
        protoc \
            --plugin=./node_modules/.bin/protoc-gen-ts_proto \
            --proto_path=proto \
            --ts_proto_out=frontend/src/proto-gen \
            --ts_proto_opt=esModuleInterop=true \
            --ts_proto_opt=outputClientImpl=grpc-web \
            proto/$service/$service.proto
    done
    echo -e "${GREEN}✓ TypeScript code generation complete${NC}"
else
    echo -e "${BLUE}Skipping TypeScript generation (ts-proto not installed)${NC}"
    echo "To generate TypeScript code, run:"
    echo "  cd frontend && npm install ts-proto"
fi

echo ""
echo -e "${GREEN}=== Code generation complete ===${NC}"
echo ""
echo "Generated files:"
echo "  - Go: shared/proto-gen/go/"
echo "  - TypeScript: frontend/src/proto-gen/"
