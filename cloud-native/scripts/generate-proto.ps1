# PowerShell script to generate Go and TypeScript code from Protocol Buffer definitions
# This script should be run from the cloud-native directory

$ErrorActionPreference = "Stop"

Write-Host "=== Protocol Buffer Code Generation ===" -ForegroundColor Cyan
Write-Host ""

# Check if protoc is installed
try {
    $protocVersion = & protoc --version 2>&1
    Write-Host "Found protoc version:" -ForegroundColor Blue
    Write-Host $protocVersion
    Write-Host ""
} catch {
    Write-Host "Error: protoc compiler not found" -ForegroundColor Red
    Write-Host "Please install protoc:"
    Write-Host "  - Windows: Download from https://github.com/protocolbuffers/protobuf/releases"
    Write-Host "  - Or use: choco install protoc"
    exit 1
}

# Check if Go plugins are installed
try {
    & protoc-gen-go --version 2>&1 | Out-Null
} catch {
    Write-Host "Error: protoc-gen-go not found" -ForegroundColor Red
    Write-Host "Installing Go protobuf plugins..." -ForegroundColor Yellow
    go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
}

# Check if TypeScript plugin is installed
try {
    & protoc-gen-ts_proto --version 2>&1 | Out-Null
    $tsProtoAvailable = $true
} catch {
    Write-Host "Note: protoc-gen-ts not found" -ForegroundColor Yellow
    Write-Host "To generate TypeScript code, install:"
    Write-Host "  npm install -g ts-proto"
    Write-Host ""
    $tsProtoAvailable = $false
}

# Create output directories
Write-Host "Creating output directories..." -ForegroundColor Blue
New-Item -ItemType Directory -Force -Path "shared/proto-gen/go" | Out-Null
New-Item -ItemType Directory -Force -Path "frontend/src/proto-gen" | Out-Null

# Array of proto files
$protoServices = @(
    "auth",
    "video",
    "homework",
    "analytics",
    "collaboration",
    "pdf"
)

# Generate Go code
Write-Host "Generating Go code..." -ForegroundColor Green
foreach ($service in $protoServices) {
    Write-Host "  - Generating $service..."
    & protoc `
        --proto_path=proto `
        --go_out=shared/proto-gen/go `
        --go_opt=paths=source_relative `
        --go-grpc_out=shared/proto-gen/go `
        --go-grpc_opt=paths=source_relative `
        "proto/$service/$service.proto"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error generating Go code for $service" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✓ Go code generation complete" -ForegroundColor Green
Write-Host ""

# Generate TypeScript code (if ts-proto is available)
if ($tsProtoAvailable -or (Test-Path "node_modules/.bin/protoc-gen-ts_proto.cmd")) {
    Write-Host "Generating TypeScript code..." -ForegroundColor Green
    foreach ($service in $protoServices) {
        Write-Host "  - Generating $service..."
        
        if (Test-Path "node_modules/.bin/protoc-gen-ts_proto.cmd") {
            $plugin = "node_modules/.bin/protoc-gen-ts_proto.cmd"
        } else {
            $plugin = "protoc-gen-ts_proto"
        }
        
        & protoc `
            --plugin=$plugin `
            --proto_path=proto `
            --ts_proto_out=frontend/src/proto-gen `
            --ts_proto_opt=esModuleInterop=true `
            --ts_proto_opt=outputClientImpl=grpc-web `
            "proto/$service/$service.proto"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error generating TypeScript code for $service" -ForegroundColor Red
            exit 1
        }
    }
    Write-Host "✓ TypeScript code generation complete" -ForegroundColor Green
} else {
    Write-Host "Skipping TypeScript generation (ts-proto not installed)" -ForegroundColor Yellow
    Write-Host "To generate TypeScript code, run:"
    Write-Host "  cd frontend && npm install ts-proto"
}

Write-Host ""
Write-Host "=== Code generation complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Generated files:"
Write-Host "  - Go: shared/proto-gen/go/"
Write-Host "  - TypeScript: frontend/src/proto-gen/"
