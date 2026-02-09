# Metlab.edu - Minikube Setup Script (PowerShell)
# This script sets up a local Kubernetes environment with Minikube

$ErrorActionPreference = "Stop"

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
Write-ColorOutput Blue "Metlab.edu - Minikube Setup"
Write-ColorOutput Blue "========================================"
Write-Output ""

# Check if Minikube is installed
if (-not (Get-Command minikube -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "Error: Minikube is not installed"
    Write-Output "Please install Minikube from: https://minikube.sigs.k8s.io/docs/start/"
    exit 1
}

# Check if kubectl is installed
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "Error: kubectl is not installed"
    Write-Output "Please install kubectl from: https://kubernetes.io/docs/tasks/tools/"
    exit 1
}

# Check if Docker is installed and running
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "Error: Docker is not installed"
    Write-Output "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
}

try {
    docker info | Out-Null
} catch {
    Write-ColorOutput Red "Error: Docker is not running"
    Write-Output "Please start Docker and try again"
    exit 1
}

Write-ColorOutput Green "✓ Prerequisites check passed"
Write-Output ""

# Configuration
$CLUSTER_NAME = "metlab-dev"
$CPUS = 4
$MEMORY = 8192
$DRIVER = "docker"

# Check if Minikube cluster already exists
$clusterExists = $false
try {
    minikube status -p $CLUSTER_NAME 2>&1 | Out-Null
    $clusterExists = $true
} catch {
    $clusterExists = $false
}

if ($clusterExists) {
    Write-ColorOutput Yellow "Minikube cluster '$CLUSTER_NAME' already exists"
    $response = Read-Host "Do you want to delete and recreate it? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-ColorOutput Yellow "Deleting existing cluster..."
        minikube delete -p $CLUSTER_NAME
    } else {
        Write-ColorOutput Blue "Using existing cluster"
        minikube start -p $CLUSTER_NAME
    }
} else {
    Write-ColorOutput Blue "Creating new Minikube cluster..."
}

# Start Minikube with appropriate resources
Write-ColorOutput Blue "Starting Minikube cluster '$CLUSTER_NAME'..."
minikube start `
    -p $CLUSTER_NAME `
    --cpus=$CPUS `
    --memory=$MEMORY `
    --driver=$DRIVER `
    --kubernetes-version=stable

Write-ColorOutput Green "✓ Minikube cluster started"
Write-Output ""

# Enable required addons
Write-ColorOutput Blue "Enabling Minikube addons..."

Write-Output "  - Enabling ingress addon..."
minikube addons enable ingress -p $CLUSTER_NAME

Write-Output "  - Enabling metrics-server addon..."
minikube addons enable metrics-server -p $CLUSTER_NAME

Write-Output "  - Enabling dashboard addon..."
minikube addons enable dashboard -p $CLUSTER_NAME

Write-Output "  - Enabling storage-provisioner addon..."
minikube addons enable storage-provisioner -p $CLUSTER_NAME

Write-Output "  - Enabling default-storageclass addon..."
minikube addons enable default-storageclass -p $CLUSTER_NAME

Write-ColorOutput Green "✓ Addons enabled"
Write-Output ""

# Configure kubectl context
Write-ColorOutput Blue "Configuring kubectl context..."
kubectl config use-context $CLUSTER_NAME

# Verify context
$CURRENT_CONTEXT = kubectl config current-context
if ($CURRENT_CONTEXT -eq $CLUSTER_NAME) {
    Write-ColorOutput Green "✓ kubectl context set to '$CLUSTER_NAME'"
} else {
    Write-ColorOutput Red "Error: Failed to set kubectl context"
    exit 1
}
Write-Output ""

# Create namespaces
Write-ColorOutput Blue "Creating Kubernetes namespaces..."
kubectl apply -f ..\infrastructure\k8s\namespace.yaml

# Create additional namespaces for staging and production (for future use)
$namespaceYaml = @"
apiVersion: v1
kind: Namespace
metadata:
  name: metlab-staging
  labels:
    name: metlab-staging
    environment: staging
---
apiVersion: v1
kind: Namespace
metadata:
  name: metlab-production
  labels:
    name: metlab-production
    environment: production
"@

$namespaceYaml | kubectl apply -f -

Write-ColorOutput Green "✓ Namespaces created"
Write-Output ""

# Display cluster information
Write-ColorOutput Blue "========================================"
Write-ColorOutput Blue "Cluster Information"
Write-ColorOutput Blue "========================================"
Write-Output ""
Write-ColorOutput Green "Cluster Name: $CLUSTER_NAME"
$k8sVersion = kubectl version --short 2>$null | Select-String "Server" | ForEach-Object { $_.ToString().Split()[2] }
Write-ColorOutput Green "Kubernetes Version: $k8sVersion"
Write-ColorOutput Green "CPUs: $CPUS"
Write-ColorOutput Green "Memory: ${MEMORY}MB"
Write-ColorOutput Green "Driver: $DRIVER"
Write-Output ""

Write-ColorOutput Green "Namespaces:"
kubectl get namespaces | Select-String "metlab"
Write-Output ""

Write-ColorOutput Green "Enabled Addons:"
minikube addons list -p $CLUSTER_NAME | Select-String "enabled"
Write-Output ""

# Display useful commands
Write-ColorOutput Blue "========================================"
Write-ColorOutput Blue "Useful Commands"
Write-ColorOutput Blue "========================================"
Write-Output ""
Write-ColorOutput Green "View cluster status:"
Write-Output "  minikube status -p $CLUSTER_NAME"
Write-Output ""
Write-ColorOutput Green "Access Kubernetes dashboard:"
Write-Output "  minikube dashboard -p $CLUSTER_NAME"
Write-Output ""
Write-ColorOutput Green "View cluster IP:"
Write-Output "  minikube ip -p $CLUSTER_NAME"
Write-Output ""
Write-ColorOutput Green "SSH into cluster:"
Write-Output "  minikube ssh -p $CLUSTER_NAME"
Write-Output ""
Write-ColorOutput Green "Stop cluster:"
Write-Output "  minikube stop -p $CLUSTER_NAME"
Write-Output ""
Write-ColorOutput Green "Delete cluster:"
Write-Output "  minikube delete -p $CLUSTER_NAME"
Write-Output ""
Write-ColorOutput Green "Deploy services:"
Write-Output "  kubectl apply -f infrastructure\k8s\"
Write-Output ""
Write-ColorOutput Green "Start development with Tilt:"
Write-Output "  tilt up"
Write-Output ""

Write-ColorOutput Green "========================================"
Write-ColorOutput Green "✓ Minikube setup complete!"
Write-ColorOutput Green "========================================"
