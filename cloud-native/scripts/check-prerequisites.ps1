# Metlab.edu - Prerequisites Check Script (PowerShell)
# This script checks if all required tools are installed

$ErrorActionPreference = "Continue"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Blue "========================================"
Write-ColorOutput Blue "Metlab.edu - Prerequisites Check"
Write-ColorOutput Blue "========================================"
Write-Output ""

# Track if all prerequisites are met
$ALL_GOOD = $true

# Check Docker
Write-Host "Checking Docker... " -NoNewline
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $dockerVersion = (docker --version).Split()[2].TrimEnd(',')
    Write-ColorOutput Green "✓ Installed ($dockerVersion)"
    
    # Check if Docker is running
    try {
        docker info 2>&1 | Out-Null
        Write-ColorOutput Green "  ✓ Docker daemon is running"
    } catch {
        Write-ColorOutput Red "  ✗ Docker daemon is not running"
        $ALL_GOOD = $false
    }
} else {
    Write-ColorOutput Red "✗ Not installed"
    Write-Output "  Install from: https://docs.docker.com/get-docker/"
    $ALL_GOOD = $false
}
Write-Output ""

# Check Minikube
Write-Host "Checking Minikube... " -NoNewline
if (Get-Command minikube -ErrorAction SilentlyContinue) {
    $minikubeVersion = (minikube version --short 2>$null)
    Write-ColorOutput Green "✓ Installed ($minikubeVersion)"
} else {
    Write-ColorOutput Red "✗ Not installed"
    Write-Output "  Install from: https://minikube.sigs.k8s.io/docs/start/"
    $ALL_GOOD = $false
}
Write-Output ""

# Check kubectl
Write-Host "Checking kubectl... " -NoNewline
if (Get-Command kubectl -ErrorAction SilentlyContinue) {
    $kubectlVersion = (kubectl version --client --short 2>$null).Split()[2]
    Write-ColorOutput Green "✓ Installed ($kubectlVersion)"
} else {
    Write-ColorOutput Red "✗ Not installed"
    Write-Output "  Install from: https://kubernetes.io/docs/tasks/tools/"
    $ALL_GOOD = $false
}
Write-Output ""

# Check Go
Write-Host "Checking Go... " -NoNewline
if (Get-Command go -ErrorAction SilentlyContinue) {
    $goVersion = (go version).Split()[2]
    Write-ColorOutput Green "✓ Installed ($goVersion)"
} else {
    Write-ColorOutput Yellow "⚠ Not installed (required for backend development)"
    Write-Output "  Install from: https://go.dev/dl/"
}
Write-Output ""

# Check Node.js
Write-Host "Checking Node.js... " -NoNewline
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Write-ColorOutput Green "✓ Installed ($nodeVersion)"
} else {
    Write-ColorOutput Yellow "⚠ Not installed (required for frontend development)"
    Write-Output "  Install from: https://nodejs.org/"
}
Write-Output ""

# Check npm
Write-Host "Checking npm... " -NoNewline
if (Get-Command npm -ErrorAction SilentlyContinue) {
    $npmVersion = npm --version
    Write-ColorOutput Green "✓ Installed (v$npmVersion)"
} else {
    Write-ColorOutput Yellow "⚠ Not installed (comes with Node.js)"
}
Write-Output ""

# Check protoc
Write-Host "Checking protoc... " -NoNewline
if (Get-Command protoc -ErrorAction SilentlyContinue) {
    $protocVersion = (protoc --version).Split()[1]
    Write-ColorOutput Green "✓ Installed ($protocVersion)"
} else {
    Write-ColorOutput Yellow "⚠ Not installed (required for proto generation)"
    Write-Output "  Install from: https://grpc.io/docs/protoc-installation/"
}
Write-Output ""

# Check Tilt (optional)
Write-Host "Checking Tilt... " -NoNewline
if (Get-Command tilt -ErrorAction SilentlyContinue) {
    $tiltVersion = (tilt version 2>$null | Select-Object -First 1).Split()[1]
    Write-ColorOutput Green "✓ Installed ($tiltVersion)"
} else {
    Write-ColorOutput Yellow "⚠ Not installed (optional, but recommended)"
    Write-Output "  Install from: https://docs.tilt.dev/install.html"
}
Write-Output ""

# Check make (optional on Windows)
Write-Host "Checking make... " -NoNewline
if (Get-Command make -ErrorAction SilentlyContinue) {
    $makeVersion = (make --version 2>$null | Select-Object -First 1).Split()[2]
    Write-ColorOutput Green "✓ Installed ($makeVersion)"
} else {
    Write-ColorOutput Yellow "⚠ Not installed (optional on Windows)"
    Write-Output "  You can use PowerShell scripts instead of Makefile"
}
Write-Output ""

# Summary
Write-ColorOutput Blue "========================================"
if ($ALL_GOOD) {
    Write-ColorOutput Green "✓ All required prerequisites are met!"
    Write-Output ""
    Write-Output "You can now run:"
    Write-Output "  make minikube-setup    # Set up Minikube cluster"
    Write-Output "  make dev               # Start development environment"
    Write-Output ""
    Write-Output "Or use PowerShell scripts directly:"
    Write-Output "  .\scripts\setup-minikube.ps1"
} else {
    Write-ColorOutput Red "✗ Some required prerequisites are missing"
    Write-Output ""
    Write-Output "Please install the missing tools and run this script again."
}
Write-ColorOutput Blue "========================================"
