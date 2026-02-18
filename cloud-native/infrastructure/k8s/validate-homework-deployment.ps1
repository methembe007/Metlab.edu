# Homework Service Deployment Validation Script (PowerShell)
# This script validates that the Homework Service is properly deployed and healthy

$ErrorActionPreference = "Stop"

$NAMESPACE = "metlab-dev"
$SERVICE_NAME = "homework"
$DEPLOYMENT_NAME = "homework"
$SERVICE_PORT = "50053"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Homework Service Deployment Validation" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Function to print success message
function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

# Function to print error message
function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

# Function to print warning message
function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

# Function to print info message
function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor White
}

# Check if kubectl is installed
try {
    $null = kubectl version --client 2>$null
    Write-Success "kubectl is installed"
} catch {
    Write-Error-Custom "kubectl is not installed"
    exit 1
}

# Check if namespace exists
try {
    $null = kubectl get namespace $NAMESPACE 2>$null
    Write-Success "Namespace '$NAMESPACE' exists"
} catch {
    Write-Error-Custom "Namespace '$NAMESPACE' does not exist"
    exit 1
}

# Check if ConfigMap exists
Write-Host ""
Write-Info "Checking ConfigMap..."
try {
    $null = kubectl get configmap homework-config -n $NAMESPACE 2>$null
    Write-Success "ConfigMap 'homework-config' exists"
    
    # Validate ConfigMap keys
    $REQUIRED_KEYS = @("PORT", "ENV", "DATABASE_HOST", "DATABASE_PORT", "DATABASE_USER", "DATABASE_NAME", "S3_ENDPOINT", "S3_REGION", "HOMEWORK_BUCKET", "MAX_UPLOAD_SIZE_MB", "SUPPORTED_FORMATS")
    foreach ($key in $REQUIRED_KEYS) {
        try {
            $null = kubectl get configmap homework-config -n $NAMESPACE -o jsonpath="{.data.$key}" 2>$null
            Write-Success "  ConfigMap key '$key' exists"
        } catch {
            Write-Error-Custom "  ConfigMap key '$key' is missing"
        }
    }
} catch {
    Write-Error-Custom "ConfigMap 'homework-config' does not exist"
}

# Check if Secret exists
Write-Host ""
Write-Info "Checking Secret..."
try {
    $null = kubectl get secret homework-secret -n $NAMESPACE 2>$null
    Write-Success "Secret 'homework-secret' exists"
    
    # Validate Secret keys
    $REQUIRED_SECRET_KEYS = @("DATABASE_PASSWORD", "S3_ACCESS_KEY", "S3_SECRET_KEY")
    foreach ($key in $REQUIRED_SECRET_KEYS) {
        try {
            $null = kubectl get secret homework-secret -n $NAMESPACE -o jsonpath="{.data.$key}" 2>$null
            Write-Success "  Secret key '$key' exists"
        } catch {
            Write-Error-Custom "  Secret key '$key' is missing"
        }
    }
} catch {
    Write-Error-Custom "Secret 'homework-secret' does not exist"
}

# Check if Deployment exists
Write-Host ""
Write-Info "Checking Deployment..."
try {
    $null = kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE 2>$null
    Write-Success "Deployment '$DEPLOYMENT_NAME' exists"
    
    # Check deployment status
    $DESIRED = kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.spec.replicas}'
    $READY = kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.status.readyReplicas}'
    
    Write-Info "  Desired replicas: $DESIRED"
    Write-Info "  Ready replicas: $READY"
    
    if ($DESIRED -eq $READY) {
        Write-Success "  All replicas are ready"
    } else {
        Write-Warning-Custom "  Not all replicas are ready ($READY/$DESIRED)"
    }
} catch {
    Write-Error-Custom "Deployment '$DEPLOYMENT_NAME' does not exist"
    exit 1
}

# Check if Service exists
Write-Host ""
Write-Info "Checking Service..."
try {
    $null = kubectl get service $SERVICE_NAME -n $NAMESPACE 2>$null
    Write-Success "Service '$SERVICE_NAME' exists"
    
    # Check service type
    $SERVICE_TYPE = kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.type}'
    Write-Info "  Service type: $SERVICE_TYPE"
    
    # Check service port
    $PORT = kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}'
    Write-Info "  Service port: $PORT"
    
    if ($PORT -eq $SERVICE_PORT) {
        Write-Success "  Service port is correct ($SERVICE_PORT)"
    } else {
        Write-Error-Custom "  Service port is incorrect (expected $SERVICE_PORT, got $PORT)"
    }
} catch {
    Write-Error-Custom "Service '$SERVICE_NAME' does not exist"
}

# Check if HPA exists
Write-Host ""
Write-Info "Checking HorizontalPodAutoscaler..."
try {
    $null = kubectl get hpa homework-hpa -n $NAMESPACE 2>$null
    Write-Success "HPA 'homework-hpa' exists"
    
    # Check HPA status
    $MIN_REPLICAS = kubectl get hpa homework-hpa -n $NAMESPACE -o jsonpath='{.spec.minReplicas}'
    $MAX_REPLICAS = kubectl get hpa homework-hpa -n $NAMESPACE -o jsonpath='{.spec.maxReplicas}'
    $CURRENT_REPLICAS = kubectl get hpa homework-hpa -n $NAMESPACE -o jsonpath='{.status.currentReplicas}'
    
    Write-Info "  Min replicas: $MIN_REPLICAS"
    Write-Info "  Max replicas: $MAX_REPLICAS"
    Write-Info "  Current replicas: $CURRENT_REPLICAS"
} catch {
    Write-Warning-Custom "HPA 'homework-hpa' does not exist (optional)"
}

# Check pod status
Write-Host ""
Write-Info "Checking Pods..."
$PODS = kubectl get pods -n $NAMESPACE -l service=$SERVICE_NAME -o jsonpath='{.items[*].metadata.name}'

if ([string]::IsNullOrWhiteSpace($PODS)) {
    Write-Error-Custom "No pods found for service '$SERVICE_NAME'"
    exit 1
}

$POD_ARRAY = $PODS -split ' '
foreach ($POD in $POD_ARRAY) {
    Write-Info "  Checking pod: $POD"
    
    # Check pod status
    $POD_STATUS = kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.status.phase}'
    if ($POD_STATUS -eq "Running") {
        Write-Success "    Pod is Running"
    } else {
        Write-Error-Custom "    Pod status: $POD_STATUS"
    }
    
    # Check container status
    $CONTAINER_READY = kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.status.containerStatuses[0].ready}'
    if ($CONTAINER_READY -eq "true") {
        Write-Success "    Container is ready"
    } else {
        Write-Error-Custom "    Container is not ready"
    }
    
    # Check restart count
    $RESTART_COUNT = kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.status.containerStatuses[0].restartCount}'
    if ($RESTART_COUNT -eq "0") {
        Write-Success "    No restarts"
    } else {
        Write-Warning-Custom "    Restart count: $RESTART_COUNT"
    }
}

# Check dependencies
Write-Host ""
Write-Info "Checking Dependencies..."

# Check PostgreSQL
try {
    $null = kubectl get service postgres -n $NAMESPACE 2>$null
    Write-Success "PostgreSQL service exists"
} catch {
    Write-Warning-Custom "PostgreSQL service not found (required dependency)"
}

# Check MinIO
try {
    $null = kubectl get service minio-service -n $NAMESPACE 2>$null
    Write-Success "MinIO service exists"
} catch {
    Write-Warning-Custom "MinIO service not found (required dependency)"
}

# Test connectivity (if pods are running)
Write-Host ""
Write-Info "Testing Connectivity..."

$FIRST_POD = $POD_ARRAY[0]

if (![string]::IsNullOrWhiteSpace($FIRST_POD)) {
    # Test database connectivity
    Write-Info "  Testing database connectivity from pod..."
    try {
        $null = kubectl exec -n $NAMESPACE $FIRST_POD -- nc -zv postgres 5432 2>$null
        Write-Success "    Database is reachable"
    } catch {
        Write-Warning-Custom "    Database connectivity test failed"
    }
    
    # Test MinIO connectivity
    Write-Info "  Testing MinIO connectivity from pod..."
    try {
        $null = kubectl exec -n $NAMESPACE $FIRST_POD -- nc -zv minio-service 9000 2>$null
        Write-Success "    MinIO is reachable"
    } catch {
        Write-Warning-Custom "    MinIO connectivity test failed"
    }
}

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Validation Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Write-Info "Deployment validation completed"
Write-Info "Review the output above for any errors or warnings"

Write-Host ""
Write-Info "To view logs, run:"
Write-Host "  kubectl logs -n $NAMESPACE -l service=$SERVICE_NAME --tail=50" -ForegroundColor Gray
Write-Host ""
Write-Info "To port-forward for testing, run:"
Write-Host "  kubectl port-forward -n $NAMESPACE svc/$SERVICE_NAME ${SERVICE_PORT}:${SERVICE_PORT}" -ForegroundColor Gray
Write-Host ""
Write-Info "To test health check, run:"
Write-Host "  grpc_health_probe -addr=localhost:$SERVICE_PORT" -ForegroundColor Gray

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
