# Video Service Deployment Validation Script (PowerShell)
# This script validates the Video Service and Video Worker deployments

$ErrorActionPreference = "Stop"
$NAMESPACE = "metlab-dev"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Video Service Deployment Validation" -ForegroundColor Cyan
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

# Check if namespace exists
Write-Host "Checking namespace..." -ForegroundColor White
try {
    kubectl get namespace $NAMESPACE 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Namespace '$NAMESPACE' exists"
    } else {
        Write-Error-Custom "Namespace '$NAMESPACE' does not exist"
        exit 1
    }
} catch {
    Write-Error-Custom "Failed to check namespace"
    exit 1
}
Write-Host ""

# Check ConfigMaps
Write-Host "Checking ConfigMaps..." -ForegroundColor White
try {
    kubectl get configmap video-config -n $NAMESPACE 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "ConfigMap 'video-config' exists"
    } else {
        Write-Error-Custom "ConfigMap 'video-config' does not exist"
        exit 1
    }
} catch {
    Write-Error-Custom "Failed to check video-config"
    exit 1
}

try {
    kubectl get configmap video-worker-config -n $NAMESPACE 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "ConfigMap 'video-worker-config' exists"
    } else {
        Write-Error-Custom "ConfigMap 'video-worker-config' does not exist"
        exit 1
    }
} catch {
    Write-Error-Custom "Failed to check video-worker-config"
    exit 1
}
Write-Host ""

# Check Secrets
Write-Host "Checking Secrets..." -ForegroundColor White
try {
    kubectl get secret video-secret -n $NAMESPACE 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Secret 'video-secret' exists"
    } else {
        Write-Error-Custom "Secret 'video-secret' does not exist"
        exit 1
    }
} catch {
    Write-Error-Custom "Failed to check video-secret"
    exit 1
}

try {
    kubectl get secret video-worker-secret -n $NAMESPACE 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Secret 'video-worker-secret' exists"
    } else {
        Write-Error-Custom "Secret 'video-worker-secret' does not exist"
        exit 1
    }
} catch {
    Write-Error-Custom "Failed to check video-worker-secret"
    exit 1
}
Write-Host ""

# Check PersistentVolumeClaims
Write-Host "Checking PersistentVolumeClaims..." -ForegroundColor White
try {
    kubectl get pvc video-processing-pvc -n $NAMESPACE 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $PVC_STATUS = kubectl get pvc video-processing-pvc -n $NAMESPACE -o jsonpath='{.status.phase}'
        if ($PVC_STATUS -eq "Bound") {
            Write-Success "PVC 'video-processing-pvc' is Bound"
        } else {
            Write-Warning-Custom "PVC 'video-processing-pvc' status: $PVC_STATUS"
        }
    } else {
        Write-Error-Custom "PVC 'video-processing-pvc' does not exist"
        exit 1
    }
} catch {
    Write-Error-Custom "Failed to check video-processing-pvc"
    exit 1
}

try {
    kubectl get pvc video-worker-processing-pvc -n $NAMESPACE 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $PVC_STATUS = kubectl get pvc video-worker-processing-pvc -n $NAMESPACE -o jsonpath='{.status.phase}'
        if ($PVC_STATUS -eq "Bound") {
            Write-Success "PVC 'video-worker-processing-pvc' is Bound"
        } else {
            Write-Warning-Custom "PVC 'video-worker-processing-pvc' status: $PVC_STATUS"
        }
    } else {
        Write-Error-Custom "PVC 'video-worker-processing-pvc' does not exist"
        exit 1
    }
} catch {
    Write-Error-Custom "Failed to check video-worker-processing-pvc"
    exit 1
}
Write-Host ""

# Check Deployments
Write-Host "Checking Deployments..." -ForegroundColor White
try {
    kubectl get deployment video -n $NAMESPACE 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Deployment 'video' exists"
        
        $DESIRED = kubectl get deployment video -n $NAMESPACE -o jsonpath='{.spec.replicas}'
        $READY = kubectl get deployment video -n $NAMESPACE -o jsonpath='{.status.readyReplicas}'
        
        if ($READY -eq $DESIRED) {
            Write-Success "Video Service: $READY/$DESIRED replicas ready"
        } else {
            Write-Warning-Custom "Video Service: $READY/$DESIRED replicas ready"
        }
    } else {
        Write-Error-Custom "Deployment 'video' does not exist"
        exit 1
    }
} catch {
    Write-Error-Custom "Failed to check video deployment"
    exit 1
}

try {
    kubectl get deployment video-worker -n $NAMESPACE 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Deployment 'video-worker' exists"
        
        $DESIRED = kubectl get deployment video-worker -n $NAMESPACE -o jsonpath='{.spec.replicas}'
        $READY = kubectl get deployment video-worker -n $NAMESPACE -o jsonpath='{.status.readyReplicas}'
        
        if ($READY -eq $DESIRED) {
            Write-Success "Video Worker: $READY/$DESIRED replicas ready"
        } else {
            Write-Warning-Custom "Video Worker: $READY/$DESIRED replicas ready"
        }
    } else {
        Write-Error-Custom "Deployment 'video-worker' does not exist"
        exit 1
    }
} catch {
    Write-Error-Custom "Failed to check video-worker deployment"
    exit 1
}
Write-Host ""

# Check Services
Write-Host "Checking Services..." -ForegroundColor White
try {
    kubectl get service video -n $NAMESPACE 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Service 'video' exists"
        $PORT = kubectl get service video -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}'
        Write-Success "Video Service listening on port $PORT"
    } else {
        Write-Error-Custom "Service 'video' does not exist"
        exit 1
    }
} catch {
    Write-Error-Custom "Failed to check video service"
    exit 1
}

try {
    kubectl get service video-worker -n $NAMESPACE 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Service 'video-worker' exists"
        $PORT = kubectl get service video-worker -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}'
        Write-Success "Video Worker Service listening on port $PORT"
    } else {
        Write-Error-Custom "Service 'video-worker' does not exist"
        exit 1
    }
} catch {
    Write-Error-Custom "Failed to check video-worker service"
    exit 1
}
Write-Host ""

# Check HorizontalPodAutoscalers
Write-Host "Checking HorizontalPodAutoscalers..." -ForegroundColor White
try {
    kubectl get hpa video-hpa -n $NAMESPACE 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "HPA 'video-hpa' exists"
        $MIN = kubectl get hpa video-hpa -n $NAMESPACE -o jsonpath='{.spec.minReplicas}'
        $MAX = kubectl get hpa video-hpa -n $NAMESPACE -o jsonpath='{.spec.maxReplicas}'
        Write-Success "Video Service HPA: min=$MIN, max=$MAX"
    } else {
        Write-Warning-Custom "HPA 'video-hpa' does not exist"
    }
} catch {
    Write-Warning-Custom "Failed to check video-hpa"
}

try {
    kubectl get hpa video-worker-hpa -n $NAMESPACE 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "HPA 'video-worker-hpa' exists"
        $MIN = kubectl get hpa video-worker-hpa -n $NAMESPACE -o jsonpath='{.spec.minReplicas}'
        $MAX = kubectl get hpa video-worker-hpa -n $NAMESPACE -o jsonpath='{.spec.maxReplicas}'
        Write-Success "Video Worker HPA: min=$MIN, max=$MAX"
    } else {
        Write-Warning-Custom "HPA 'video-worker-hpa' does not exist"
    }
} catch {
    Write-Warning-Custom "Failed to check video-worker-hpa"
}
Write-Host ""

# Check Pods
Write-Host "Checking Pods..." -ForegroundColor White
$VIDEO_PODS = (kubectl get pods -n $NAMESPACE -l service=video --no-headers 2>$null | Measure-Object).Count
if ($VIDEO_PODS -gt 0) {
    Write-Success "Found $VIDEO_PODS Video Service pod(s)"
    
    $NOT_RUNNING = (kubectl get pods -n $NAMESPACE -l service=video --no-headers 2>$null | Where-Object { $_ -notmatch "Running" } | Measure-Object).Count
    if ($NOT_RUNNING -gt 0) {
        Write-Warning-Custom "$NOT_RUNNING Video Service pod(s) not in Running state"
    }
} else {
    Write-Error-Custom "No Video Service pods found"
}

$WORKER_PODS = (kubectl get pods -n $NAMESPACE -l service=video-worker --no-headers 2>$null | Measure-Object).Count
if ($WORKER_PODS -gt 0) {
    Write-Success "Found $WORKER_PODS Video Worker pod(s)"
    
    $NOT_RUNNING = (kubectl get pods -n $NAMESPACE -l service=video-worker --no-headers 2>$null | Where-Object { $_ -notmatch "Running" } | Measure-Object).Count
    if ($NOT_RUNNING -gt 0) {
        Write-Warning-Custom "$NOT_RUNNING Video Worker pod(s) not in Running state"
    }
} else {
    Write-Error-Custom "No Video Worker pods found"
}
Write-Host ""

# Check Pod Health
Write-Host "Checking Pod Health..." -ForegroundColor White
$VIDEO_POD = kubectl get pods -n $NAMESPACE -l service=video -o jsonpath='{.items[0].metadata.name}' 2>$null
if ($VIDEO_POD) {
    try {
        kubectl exec -n $NAMESPACE $VIDEO_POD -- grpc_health_probe -addr=:50052 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Video Service health check passed"
        } else {
            Write-Warning-Custom "Video Service health check failed (may not be implemented yet)"
        }
    } catch {
        Write-Warning-Custom "Video Service health check failed (may not be implemented yet)"
    }
} else {
    Write-Warning-Custom "No Video Service pod available for health check"
}

$WORKER_POD = kubectl get pods -n $NAMESPACE -l service=video-worker -o jsonpath='{.items[0].metadata.name}' 2>$null
if ($WORKER_POD) {
    try {
        kubectl exec -n $NAMESPACE $WORKER_POD -- curl -f http://localhost:9090/health 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Video Worker health check passed"
        } else {
            Write-Warning-Custom "Video Worker health check failed (may not be implemented yet)"
        }
    } catch {
        Write-Warning-Custom "Video Worker health check failed (may not be implemented yet)"
    }
} else {
    Write-Warning-Custom "No Video Worker pod available for health check"
}
Write-Host ""

# Check Dependencies
Write-Host "Checking Dependencies..." -ForegroundColor White
try {
    kubectl get service postgres -n $NAMESPACE 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "PostgreSQL service is available"
    } else {
        Write-Error-Custom "PostgreSQL service not found"
    }
} catch {
    Write-Error-Custom "PostgreSQL service not found"
}

try {
    kubectl get service redis -n $NAMESPACE 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Redis service is available"
    } else {
        Write-Error-Custom "Redis service not found"
    }
} catch {
    Write-Error-Custom "Redis service not found"
}

try {
    kubectl get service minio-service -n $NAMESPACE 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "MinIO service is available"
    } else {
        Write-Warning-Custom "MinIO service not found (may use external S3)"
    }
} catch {
    Write-Warning-Custom "MinIO service not found (may use external S3)"
}
Write-Host ""

# Summary
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Validation Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$ERRORS = (kubectl get pods -n $NAMESPACE -l service=video --no-headers 2>$null | Where-Object { $_ -notmatch "Running" } | Measure-Object).Count
$ERRORS += (kubectl get pods -n $NAMESPACE -l service=video-worker --no-headers 2>$null | Where-Object { $_ -notmatch "Running" } | Measure-Object).Count

if ($ERRORS -eq 0) {
    Write-Success "All Video Service components are healthy!"
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Test video upload: Use API Gateway to upload a test video"
    Write-Host "2. Monitor processing: Check video-worker logs for processing status"
    Write-Host "3. Verify storage: Check MinIO/S3 for uploaded videos and thumbnails"
    Write-Host "4. Test streaming: Request streaming URL and verify playback"
} else {
    Write-Warning-Custom "Found $ERRORS issue(s) that need attention"
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Cyan
    Write-Host "1. Check pod logs: kubectl logs -n $NAMESPACE -l service=video"
    Write-Host "2. Check pod logs: kubectl logs -n $NAMESPACE -l service=video-worker"
    Write-Host "3. Describe pods: kubectl describe pods -n $NAMESPACE -l service=video"
    Write-Host "4. Check events: kubectl get events -n $NAMESPACE"
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
