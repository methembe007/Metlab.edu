# PDF Service Deployment Validation Script (PowerShell)
# This script validates that the PDF service is properly deployed and functioning

$ErrorActionPreference = "Stop"

$NAMESPACE = "metlab-dev"
$SERVICE_NAME = "pdf"
$DEPLOYMENT_NAME = "pdf"
$PORT = "50056"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "PDF Service Deployment Validation" -ForegroundColor Cyan
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
    $null = kubectl get configmap pdf-config -n $NAMESPACE 2>$null
    Write-Success "ConfigMap 'pdf-config' exists"
    
    # Validate required keys
    $REQUIRED_KEYS = @("PORT", "DATABASE_HOST", "S3_ENDPOINT", "PDF_BUCKET", "MAX_UPLOAD_SIZE_MB")
    foreach ($key in $REQUIRED_KEYS) {
        try {
            $null = kubectl get configmap pdf-config -n $NAMESPACE -o jsonpath="{.data.$key}" 2>$null
            Write-Success "  ConfigMap has key '$key'"
        } catch {
            Write-Error-Custom "  ConfigMap missing key '$key'"
        }
    }
} catch {
    Write-Error-Custom "ConfigMap 'pdf-config' does not exist"
    exit 1
}

# Check if Secret exists
Write-Host ""
Write-Info "Checking Secret..."
try {
    $null = kubectl get secret pdf-secret -n $NAMESPACE 2>$null
    Write-Success "Secret 'pdf-secret' exists"
    
    # Validate required keys
    $REQUIRED_SECRET_KEYS = @("DATABASE_PASSWORD", "S3_ACCESS_KEY", "S3_SECRET_KEY")
    foreach ($key in $REQUIRED_SECRET_KEYS) {
        try {
            $null = kubectl get secret pdf-secret -n $NAMESPACE -o jsonpath="{.data.$key}" 2>$null
            Write-Success "  Secret has key '$key'"
        } catch {
            Write-Error-Custom "  Secret missing key '$key'"
        }
    }
} catch {
    Write-Error-Custom "Secret 'pdf-secret' does not exist"
    exit 1
}

# Check if Deployment exists
Write-Host ""
Write-Info "Checking Deployment..."
try {
    $null = kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE 2>$null
    Write-Success "Deployment '$DEPLOYMENT_NAME' exists"
    
    # Check replicas
    $DESIRED_REPLICAS = kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.spec.replicas}'
    $READY_REPLICAS = kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.status.readyReplicas}'
    
    Write-Info "  Desired replicas: $DESIRED_REPLICAS"
    Write-Info "  Ready replicas: $READY_REPLICAS"
    
    if ($DESIRED_REPLICAS -eq $READY_REPLICAS) {
        Write-Success "  All replicas are ready"
    } else {
        Write-Warning-Custom "  Not all replicas are ready ($READY_REPLICAS/$DESIRED_REPLICAS)"
    }
    
    # Check deployment conditions
    $AVAILABLE = kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Available")].status}'
    if ($AVAILABLE -eq "True") {
        Write-Success "  Deployment is available"
    } else {
        Write-Error-Custom "  Deployment is not available"
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
    $SERVICE_PORT = kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}'
    Write-Info "  Service port: $SERVICE_PORT"
    
    if ($SERVICE_PORT -eq $PORT) {
        Write-Success "  Service port matches expected port ($PORT)"
    } else {
        Write-Warning-Custom "  Service port ($SERVICE_PORT) does not match expected port ($PORT)"
    }
    
    # Check endpoints
    $ENDPOINTS_OUTPUT = kubectl get endpoints $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.subsets[*].addresses[*].ip}'
    $ENDPOINTS = ($ENDPOINTS_OUTPUT -split ' ').Count
    Write-Info "  Endpoints: $ENDPOINTS"
    
    if ($ENDPOINTS -gt 0) {
        Write-Success "  Service has $ENDPOINTS endpoint(s)"
    } else {
        Write-Error-Custom "  Service has no endpoints"
    }
} catch {
    Write-Error-Custom "Service '$SERVICE_NAME' does not exist"
    exit 1
}

# Check if HPA exists
Write-Host ""
Write-Info "Checking HorizontalPodAutoscaler..."
try {
    $null = kubectl get hpa pdf-hpa -n $NAMESPACE 2>$null
    Write-Success "HPA 'pdf-hpa' exists"
    
    # Check HPA status
    $MIN_REPLICAS = kubectl get hpa pdf-hpa -n $NAMESPACE -o jsonpath='{.spec.minReplicas}'
    $MAX_REPLICAS = kubectl get hpa pdf-hpa -n $NAMESPACE -o jsonpath='{.spec.maxReplicas}'
    $CURRENT_REPLICAS = kubectl get hpa pdf-hpa -n $NAMESPACE -o jsonpath='{.status.currentReplicas}'
    
    Write-Info "  Min replicas: $MIN_REPLICAS"
    Write-Info "  Max replicas: $MAX_REPLICAS"
    Write-Info "  Current replicas: $CURRENT_REPLICAS"
    
    if (($CURRENT_REPLICAS -ge $MIN_REPLICAS) -and ($CURRENT_REPLICAS -le $MAX_REPLICAS)) {
        Write-Success "  HPA is within configured bounds"
    } else {
        Write-Warning-Custom "  HPA replicas outside configured bounds"
    }
} catch {
    Write-Warning-Custom "HPA 'pdf-hpa' does not exist (optional)"
}

# Check pod status
Write-Host ""
Write-Info "Checking Pods..."
$PODS_OUTPUT = kubectl get pods -n $NAMESPACE -l app=metlab,service=pdf -o jsonpath='{.items[*].metadata.name}'
$PODS = $PODS_OUTPUT -split ' '

if ($PODS.Count -eq 0 -or [string]::IsNullOrWhiteSpace($PODS_OUTPUT)) {
    Write-Error-Custom "No pods found for service '$SERVICE_NAME'"
    exit 1
}

foreach ($POD in $PODS) {
    if ([string]::IsNullOrWhiteSpace($POD)) { continue }
    
    Write-Info "  Checking pod: $POD"
    
    # Check pod phase
    $PHASE = kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.status.phase}'
    if ($PHASE -eq "Running") {
        Write-Success "    Pod is running"
    } else {
        Write-Error-Custom "    Pod is not running (phase: $PHASE)"
    }
    
    # Check container status
    $READY = kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.status.containerStatuses[0].ready}'
    if ($READY -eq "true") {
        Write-Success "    Container is ready"
    } else {
        Write-Error-Custom "    Container is not ready"
    }
    
    # Check restart count
    $RESTARTS = kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.status.containerStatuses[0].restartCount}'
    Write-Info "    Restart count: $RESTARTS"
    if ([int]$RESTARTS -gt 5) {
        Write-Warning-Custom "    High restart count detected"
    }
}

# Test gRPC health check
Write-Host ""
Write-Info "Testing gRPC health check..."
$FIRST_POD = $PODS[0]

try {
    $null = kubectl exec -n $NAMESPACE $FIRST_POD -- sh -c "command -v grpc_health_probe" 2>$null
    try {
        $null = kubectl exec -n $NAMESPACE $FIRST_POD -- grpc_health_probe -addr=:$PORT 2>$null
        Write-Success "gRPC health check passed"
    } catch {
        Write-Error-Custom "gRPC health check failed"
    }
} catch {
    Write-Warning-Custom "grpc_health_probe not found in container (health checks may use fallback)"
}

# Check resource usage
Write-Host ""
Write-Info "Checking resource usage..."
try {
    $null = kubectl top pods -n $NAMESPACE -l app=metlab,service=pdf 2>$null
    Write-Host ""
    kubectl top pods -n $NAMESPACE -l app=metlab,service=pdf
    Write-Host ""
    Write-Success "Resource usage retrieved"
} catch {
    Write-Warning-Custom "Unable to retrieve resource usage (metrics-server may not be installed)"
}

# Check recent logs for errors
Write-Host ""
Write-Info "Checking recent logs for errors..."
try {
    $LOGS = kubectl logs -n $NAMESPACE -l app=metlab,service=pdf --tail=100 --since=5m 2>$null
    $ERROR_COUNT = ($LOGS | Select-String -Pattern "error|fatal|panic" -CaseSensitive:$false).Count
    
    if ($ERROR_COUNT -eq 0) {
        Write-Success "No errors found in recent logs"
    } else {
        Write-Warning-Custom "Found $ERROR_COUNT error(s) in recent logs"
        Write-Info "  Run 'kubectl logs -n $NAMESPACE -l app=metlab,service=pdf --tail=100' to view"
    }
} catch {
    Write-Warning-Custom "Unable to check logs"
}

# Check database connectivity
Write-Host ""
Write-Info "Checking database connectivity..."
$DB_HOST = kubectl get configmap pdf-config -n $NAMESPACE -o jsonpath='{.data.DATABASE_HOST}'
try {
    $null = kubectl get service $DB_HOST -n $NAMESPACE 2>$null
    Write-Success "Database service '$DB_HOST' is accessible"
} catch {
    Write-Warning-Custom "Database service '$DB_HOST' not found in namespace"
}

# Check S3/MinIO connectivity
Write-Host ""
Write-Info "Checking S3/MinIO connectivity..."
$S3_ENDPOINT = kubectl get configmap pdf-config -n $NAMESPACE -o jsonpath='{.data.S3_ENDPOINT}'
$S3_SERVICE = ($S3_ENDPOINT -replace 'http://', '' -replace 'https://', '') -split ':' | Select-Object -First 1

try {
    $null = kubectl get service $S3_SERVICE -n $NAMESPACE 2>$null
    Write-Success "S3 service '$S3_SERVICE' is accessible"
} catch {
    Write-Warning-Custom "S3 service '$S3_SERVICE' not found in namespace"
}

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Validation Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check final status
$AVAILABLE = kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Available")].status}'

if ($AVAILABLE -eq "True") {
    Write-Success "PDF Service is deployed and healthy"
    Write-Host ""
    Write-Info "Service endpoint: $SERVICE_NAME.$NAMESPACE.svc.cluster.local:$PORT"
    Write-Info "gRPC port: $PORT"
    Write-Host ""
    Write-Info "Next steps:"
    Write-Host "  - Test PDF upload: Use API Gateway to upload a PDF"
    Write-Host "  - Test PDF download: Generate and use a download URL"
    Write-Host "  - Monitor logs: kubectl logs -n $NAMESPACE -l service=pdf -f"
    Write-Host "  - Check metrics: kubectl top pods -n $NAMESPACE -l service=pdf"
    Write-Host ""
    exit 0
} else {
    Write-Error-Custom "PDF Service deployment has issues"
    Write-Host ""
    Write-Info "Troubleshooting steps:"
    Write-Host "  - Check pod logs: kubectl logs -n $NAMESPACE -l service=pdf"
    Write-Host "  - Describe pods: kubectl describe pods -n $NAMESPACE -l service=pdf"
    Write-Host "  - Check events: kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'"
    Write-Host ""
    exit 1
}
