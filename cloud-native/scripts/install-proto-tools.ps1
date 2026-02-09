# PowerShell script to install Protocol Buffer compiler and plugins for Windows

$ErrorActionPreference = "Stop"

Write-Host "=== Installing Protocol Buffer Tools ===" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# Install protoc compiler
try {
    $protocVersion = & protoc --version 2>&1
    Write-Host "✓ protoc already installed:" -ForegroundColor Green
    Write-Host $protocVersion
} catch {
    Write-Host "Installing protoc compiler..." -ForegroundColor Yellow
    
    # Check if Chocolatey is available
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        if ($isAdmin) {
            choco install protoc -y
            Write-Host "✓ protoc installed successfully" -ForegroundColor Green
        } else {
            Write-Host "Error: Administrator privileges required to install via Chocolatey" -ForegroundColor Red
            Write-Host "Please run this script as Administrator, or install manually:"
            Write-Host "  1. Download from: https://github.com/protocolbuffers/protobuf/releases"
            Write-Host "  2. Extract and add to PATH"
            exit 1
        }
    } else {
        Write-Host "Chocolatey not found. Manual installation required:" -ForegroundColor Yellow
        Write-Host "  1. Download from: https://github.com/protocolbuffers/protobuf/releases"
        Write-Host "  2. Extract protoc.exe to a directory"
        Write-Host "  3. Add the directory to your PATH"
        Write-Host ""
        Write-Host "Or install Chocolatey first:"
        Write-Host "  Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
        exit 1
    }
}

Write-Host ""

# Install Go plugins
if (Get-Command go -ErrorAction SilentlyContinue) {
    Write-Host "Installing Go protobuf plugins..." -ForegroundColor Yellow
    go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
    Write-Host "✓ Go plugins installed" -ForegroundColor Green
} else {
    Write-Host "⚠ Go not found. Skipping Go plugin installation." -ForegroundColor Yellow
    Write-Host "  Install Go from: https://golang.org/dl/"
}

Write-Host ""

# Install TypeScript plugin
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "Installing TypeScript protobuf plugin..." -ForegroundColor Yellow
    npm install -g ts-proto
    Write-Host "✓ TypeScript plugin installed" -ForegroundColor Green
} else {
    Write-Host "⚠ npm not found. Skipping TypeScript plugin installation." -ForegroundColor Yellow
    Write-Host "  Install Node.js from: https://nodejs.org/"
}

Write-Host ""
Write-Host "=== Installation complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Installed tools:"

try {
    $protocVersion = & protoc --version 2>&1
    Write-Host "  ✓ protoc: $protocVersion" -ForegroundColor Green
} catch {}

try {
    & protoc-gen-go --version 2>&1 | Out-Null
    Write-Host "  ✓ protoc-gen-go" -ForegroundColor Green
} catch {}

try {
    & protoc-gen-go-grpc --version 2>&1 | Out-Null
    Write-Host "  ✓ protoc-gen-go-grpc" -ForegroundColor Green
} catch {}

try {
    & protoc-gen-ts_proto --version 2>&1 | Out-Null
    Write-Host "  ✓ ts-proto" -ForegroundColor Green
} catch {}

Write-Host ""
Write-Host "You can now run: .\scripts\generate-proto.ps1"
