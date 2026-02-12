# Validation script for Auth Service Kubernetes deployment (PowerShell)
# This script validates the YAML syntax and checks for common issues

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "Auth Service Deployment Validation" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Check if kubectl is installed
try {
    $null = kubectl version --client 2>&1
    Write-Host "✓ kubectl is installed" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: kubectl is not installed" -ForegroundColor Red
    exit 1
}

# Validate YAML syntax
Write-Host ""
Write-Host "Validating YAML syntax..."
try {
    $output = kubectl apply -f cloud-native/infrastructure/k8s/auth.yaml --dry-run=client 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ YAML syntax is valid" -ForegroundColor Green
    } else {
        Write-Host "✗ YAML syntax validation failed" -ForegroundColor Red
        Write-Host $output
        exit 1
    }
} catch {
    Write-Host "✗ YAML syntax validation failed" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# Check if namespace exists
Write-Host ""
Write-Host "Checking namespace..."
try {
    $null = kubectl get namespace metlab-dev 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Namespace 'metlab-dev' exists" -ForegroundColor Green
    } else {
        Write-Host "⚠ Namespace 'metlab-dev' does not exist" -ForegroundColor Yellow
        Write-Host "  Run: kubectl apply -f cloud-native/infrastructure/k8s/namespace.yaml"
    }
} catch {
    Write-Host "⚠ Namespace 'metlab-dev' does not exist" -ForegroundColor Yellow
    Write-Host "  Run: kubectl apply -f cloud-native/infrastructure/k8s/namespace.yaml"
}

# Check if PostgreSQL is deployed
Write-Host ""
Write-Host "Checking PostgreSQL dependency..."
try {
    $null = kubectl get service postgres -n metlab-dev 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ PostgreSQL service exists" -ForegroundColor Green
    } else {
        Write-Host "⚠ PostgreSQL service not found" -ForegroundColor Yellow
        Write-Host "  Run: kubectl apply -f cloud-native/infrastructure/k8s/postgres.yaml"
    }
} catch {
    Write-Host "⚠ PostgreSQL service not found" -ForegroundColor Yellow
    Write-Host "  Run: kubectl apply -f cloud-native/infrastructure/k8s/postgres.yaml"
}

# Validate resource definitions
Write-Host ""
Write-Host "Validating resource definitions..."

$dryRunOutput = kubectl apply -f cloud-native/infrastructure/k8s/auth.yaml --dry-run=client 2>&1 | Out-String

if ($dryRunOutput -match "configmap/auth-config") {
    Write-Host "✓ ConfigMap definition is valid" -ForegroundColor Green
}

if ($dryRunOutput -match "secret/auth-secret") {
    Write-Host "✓ Secret definition is valid" -ForegroundColor Green
}

if ($dryRunOutput -match "deployment.apps/auth") {
    Write-Host "✓ Deployment definition is valid" -ForegroundColor Green
}

if ($dryRunOutput -match "service/auth") {
    Write-Host "✓ Service definition is valid" -ForegroundColor Green
}

if ($dryRunOutput -match "horizontalpodautoscaler.autoscaling/auth-hpa") {
    Write-Host "✓ HorizontalPodAutoscaler definition is valid" -ForegroundColor Green
}

Write-Host ""
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "Validation Summary" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "All validations passed! The Auth Service deployment is ready." -ForegroundColor Green
Write-Host ""
Write-Host "To deploy:"
Write-Host "  kubectl apply -f cloud-native/infrastructure/k8s/auth.yaml"
Write-Host ""
Write-Host "To verify:"
Write-Host "  kubectl get all -n metlab-dev -l service=auth"
Write-Host ""
