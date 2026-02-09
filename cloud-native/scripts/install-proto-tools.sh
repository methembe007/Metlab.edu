#!/bin/bash

# Script to install Protocol Buffer compiler and plugins
# Supports macOS, Linux, and provides instructions for Windows

set -e

echo "=== Installing Protocol Buffer Tools ==="
echo ""

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Windows;;
    MINGW*)     MACHINE=Windows;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "Detected OS: $MACHINE"
echo ""

# Install protoc compiler
if command -v protoc &> /dev/null; then
    echo "✓ protoc already installed:"
    protoc --version
else
    echo "Installing protoc compiler..."
    
    if [ "$MACHINE" = "Mac" ]; then
        if command -v brew &> /dev/null; then
            brew install protobuf
        else
            echo "Error: Homebrew not found. Please install Homebrew first:"
            echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
    elif [ "$MACHINE" = "Linux" ]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y protobuf-compiler
        elif command -v yum &> /dev/null; then
            sudo yum install -y protobuf-compiler
        else
            echo "Error: Package manager not found. Please install protoc manually:"
            echo "  https://github.com/protocolbuffers/protobuf/releases"
            exit 1
        fi
    elif [ "$MACHINE" = "Windows" ]; then
        echo "For Windows, please install protoc manually:"
        echo "  1. Download from: https://github.com/protocolbuffers/protobuf/releases"
        echo "  2. Or use Chocolatey: choco install protoc"
        exit 1
    fi
    
    echo "✓ protoc installed successfully"
fi

echo ""

# Install Go plugins
if command -v go &> /dev/null; then
    echo "Installing Go protobuf plugins..."
    go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
    echo "✓ Go plugins installed"
else
    echo "⚠ Go not found. Skipping Go plugin installation."
    echo "  Install Go from: https://golang.org/dl/"
fi

echo ""

# Install TypeScript plugin
if command -v npm &> /dev/null; then
    echo "Installing TypeScript protobuf plugin..."
    npm install -g ts-proto
    echo "✓ TypeScript plugin installed"
else
    echo "⚠ npm not found. Skipping TypeScript plugin installation."
    echo "  Install Node.js from: https://nodejs.org/"
fi

echo ""
echo "=== Installation complete ==="
echo ""
echo "Installed tools:"
command -v protoc &> /dev/null && echo "  ✓ protoc: $(protoc --version)"
command -v protoc-gen-go &> /dev/null && echo "  ✓ protoc-gen-go"
command -v protoc-gen-go-grpc &> /dev/null && echo "  ✓ protoc-gen-go-grpc"
command -v protoc-gen-ts_proto &> /dev/null && echo "  ✓ ts-proto"

echo ""
echo "You can now run: ./scripts/generate-proto.sh"
