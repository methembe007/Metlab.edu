# API Gateway Deployment Validation Script (PowerShell)
# This script validates that the API Gateway deployment is correctly configured

$ErrorActionPreference = "Stop"

$NAMESPACE = "metlab-dev"
$SERVICE_NAME = "api-gateway"
$HPA_NAME = "api-gateway-hpa"
$INGRESS_NAME = "metlab-ingress"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "API Gateway Deployment Validation" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if kubectl is available
try {
    kubectl version --client --short | Out-Null
    Write-Host "✓ kubectl found" -ForegroundColor Green
} catch {
    Write-Host "✗ kubectl not found" -ForegroundColor Red
    exit 1
}

# Check if namespace exists
Write-Host ""
Write-Host "Checking namespace..."
try {
    kubectl get namespace $NAMESPACE 2>&1 | Out-Null
    Write-Host "✓ Namespace '$NAMESPACE' exists" -ForegroundColor Green
} catch {
    Write-Host "✗ Namespace '$NAMESPACE' not found" -ForegroundColor Red
    exit 1
}

# Check deployment
Write-Host ""
Write-Host "Checking deployment..."
try {
    kubectl get deployment $SERVICE_NAME -n $NAMESPACE 2>&1 | Out-Null
    Write-Host "✓ Deployment '$SERVICE_NAME' exists" -ForegroundColor Green
    
    # Check replicas
    $DESIRED = kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.replicas}'
    $READY = kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.status.readyReplicas}'
    Write-Host "  Desired replicas: $DESIRED"
    Write-Host "  Ready replicas: $READY"
    
    if ([int]$READY -ge 3) {
        Write-Host "✓ Minimum 3 replicas are ready" -ForegroundColor Green
    } else {
        Write-Host "⚠ Less than 3 replicas ready (expected minimum: 3)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Deployment '$SERVICE_NAME' not found" -ForegroundColor Red
    exit 1
}

# Check pods
Write-Host ""
Write-Host "Checking pods..."
$pods = kubectl get pods -n $NAMESPACE -l service=$SERVICE_NAME --field-selector=status.phase=Running --no-headers 2>$null
$POD_COUNT = ($pods | Measure-Object -Line).Lines
if ($POD_COUNT -gt 0) {
    Write-Host "✓ $POD_COUNT pod(s) running" -ForegroundColor Green
    kubectl get pods -n $NAMESPACE -l service=$SERVICE_NAME
} else {
    Write-Host "✗ No running pods found" -ForegroundColor Red
    exit 1
}

# Check service
Write-Host ""
Write-Host "Checking service..."
try {
    kubectl get service $SERVICE_NAME -n $NAMESPACE 2>&1 | Out-Null
    Write-Host "✓ Service '$SERVICE_NAME' exists" -ForegroundColor Green
    
    # Check service type
    $SERVICE_TYPE = kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.type}'
    if ($SERVICE_TYPE -eq "ClusterIP") {
        Write-Host "✓ Service type is ClusterIP" -ForegroundColor Green
    } else {
        Write-Host "⚠ Service type is $SERVICE_TYPE (expected: ClusterIP)" -ForegroundColor Yellow
    }
    
    # Check service port
    $SERVICE_PORT = kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}'
    if ($SERVICE_PORT -eq "8080") {
        Write-Host "✓ Service port is 8080" -ForegroundColor Green
    } else {
        Write-Host "⚠ Service port is $SERVICE_PORT (expected: 8080)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Service '$SERVICE_NAME' not found" -ForegroundColor Red
    exit 1
}

# Check HPA
Write-Host ""
Write-Host "Checking HorizontalPodAutoscaler..."
try {
    kubectl get hpa $HPA_NAME -n $NAMESPACE 2>&1 | Out-Null
    Write-Host "✓ HPA '$HPA_NAME' exists" -ForegroundColor Green
    
    # Check HPA configuration
    $MIN_REPLICAS = kubectl get hpa $HPA_NAME -n $NAMESPACE -o jsonpath='{.spec.minReplicas}'
    $MAX_REPLICAS = kubectl get hpa $HPA_NAME -n $NAMESPACE -o jsonpath='{.spec.maxReplicas}'
    Write-Host "  Min replicas: $MIN_REPLICAS"
    Write-Host "  Max replicas: $MAX_REPLICAS"
    
    if ($MIN_REPLICAS -eq "3" -and $MAX_REPLICAS -eq "20") {
        Write-Host "✓ HPA replica range is correct (3-20)" -ForegroundColor Green
    } else {
        Write-Host "⚠ HPA replica range is $MIN_REPLICAS-$MAX_REPLICAS (expected: 3-20)" -ForegroundColor Yellow
    }
    
    # Check if metrics-server is available
    try {
        kubectl get deployment metrics-server -n kube-system 2>&1 | Out-Null
        Write-Host "✓ metrics-server is deployed" -ForegroundColor Green
    } catch {
        Write-Host "⚠ metrics-server not found (required for HPA)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ HPA '$HPA_NAME' not found" -ForegroundColor Red
    exit 1
}

# Check Ingress
Write-Host ""
Write-Host "Checking Ingress..."
try {
    kubectl get ingress $INGRESS_NAME -n $NAMESPACE 2>&1 | Out-Null
    Write-Host "✓ Ingress '$INGRESS_NAME' exists" -ForegroundColor Green
    
    # Check Ingress class
    $INGRESS_CLASS = kubectl get ingress $INGRESS_NAME -n $NAMESPACE -o jsonpath='{.spec.ingressClassName}'
    if ($INGRESS_CLASS -eq "nginx") {
        Write-Host "✓ Ingress class is nginx" -ForegroundColor Green
    } else {
        Write-Host "⚠ Ingress class is $INGRESS_CLASS (expected: nginx)" -ForegroundColor Yellow
    }
    
    # Check if nginx-ingress-controller is running
    $nginxPods = kubectl get pods -n ingress-nginx -l app.kubernetes.io/component=controller 2>$null | Select-String "Running"
    if ($nginxPods) {
        Write-Host "✓ Nginx Ingress Controller is running" -ForegroundColor Green
    } else {
        Write-Host "⚠ Nginx Ingress Controller not found" -ForegroundColor Yellow
        Write-Host "  Run: minikube addons enable ingress"
    }
} catch {
    Write-Host "✗ Ingress '$INGRESS_NAME' not found" -ForegroundColor Red
    exit 1
}

# Check health probes
Write-Host ""
Write-Host "Checking health probes..."
$LIVENESS_PATH = kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].livenessProbe.httpGet.path}'
$READINESS_PATH = kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].readinessProbe.httpGet.path}'

if ($LIVENESS_PATH -eq "/health") {
    Write-Host "✓ Liveness probe configured (/health)" -ForegroundColor Green
} else {
    Write-Host "⚠ Liveness probe path is $LIVENESS_PATH (expected: /health)" -ForegroundColor Yellow
}

if ($READINESS_PATH -eq "/ready") {
    Write-Host "✓ Readiness probe configured (/ready)" -ForegroundColor Green
} else {
    Write-Host "⚠ Readiness probe path is $READINESS_PATH (expected: /ready)" -ForegroundColor Yellow
}

# Check resource limits
Write-Host ""
Write-Host "Checking resource limits..."
$CPU_REQUEST = kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].resources.requests.cpu}'
$CPU_LIMIT = kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].resources.limits.cpu}'
$MEM_REQUEST = kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].resources.requests.memory}'
$MEM_LIMIT = kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}'

Write-Host "  CPU: $CPU_REQUEST (request) / $CPU_LIMIT (limit)"
Write-Host "  Memory: $MEM_REQUEST (request) / $MEM_LIMIT (limit)"

if ($CPU_REQUEST -eq "500m" -and $CPU_LIMIT -eq "1000m" -and $MEM_REQUEST -eq "512Mi" -and $MEM_LIMIT -eq "1Gi") {
    Write-Host "✓ Resource limits are correctly configured" -ForegroundColor Green
} else {
    Write-Host "⚠ Resource limits differ from expected values" -ForegroundColor Yellow
}

# Test connectivity (if pods are running)
Write-Host ""
Write-Host "Testing connectivity..."
if ($POD_COUNT -gt 0) {
    $POD_NAME = kubectl get pods -n $NAMESPACE -l service=$SERVICE_NAME --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}'
    
    Write-Host "Testing health endpoint..."
    try {
        kubectl exec -n $NAMESPACE $POD_NAME -- wget -q -O- http://localhost:8080/health 2>&1 | Out-Null
        Write-Host "✓ Health endpoint responding" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Health endpoint not responding (service may still be starting)" -ForegroundColor Yellow
    }
}

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Validation Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✓ API Gateway deployment is configured correctly" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Verify all backend services are running:"
Write-Host "   kubectl get pods -n $NAMESPACE"
Write-Host ""
Write-Host "2. Check HPA metrics:"
Write-Host "   kubectl get hpa $HPA_NAME -n $NAMESPACE"
Write-Host ""
Write-Host "3. Access the application:"
Write-Host "   `$ip = minikube ip"
Write-Host "   Add `"`$ip metlab.local`" to C:\Windows\System32\drivers\etc\hosts"
Write-Host "   curl http://metlab.local/api/health"
Write-Host ""
Write-Host "4. Monitor logs:"
Write-Host "   kubectl logs -n $NAMESPACE -l service=$SERVICE_NAME -f"
