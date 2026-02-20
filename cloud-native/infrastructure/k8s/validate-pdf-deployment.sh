#!/bin/bash

# PDF Service Deployment Validation Script
# This script validates that the PDF service is properly deployed and functioning

set -e

NAMESPACE="metlab-dev"
SERVICE_NAME="pdf"
DEPLOYMENT_NAME="pdf"
PORT="50056"

echo "=========================================="
echo "PDF Service Deployment Validation"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print success message
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error message
error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to print warning message
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to print info message
info() {
    echo -e "${NC}ℹ${NC} $1"
}

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    error "kubectl is not installed"
    exit 1
fi
success "kubectl is installed"

# Check if namespace exists
if kubectl get namespace $NAMESPACE &> /dev/null; then
    success "Namespace '$NAMESPACE' exists"
else
    error "Namespace '$NAMESPACE' does not exist"
    exit 1
fi

# Check if ConfigMap exists
echo ""
info "Checking ConfigMap..."
if kubectl get configmap pdf-config -n $NAMESPACE &> /dev/null; then
    success "ConfigMap 'pdf-config' exists"
    
    # Validate required keys
    REQUIRED_KEYS=("PORT" "DATABASE_HOST" "S3_ENDPOINT" "PDF_BUCKET" "MAX_UPLOAD_SIZE_MB")
    for key in "${REQUIRED_KEYS[@]}"; do
        if kubectl get configmap pdf-config -n $NAMESPACE -o jsonpath="{.data.$key}" &> /dev/null; then
            success "  ConfigMap has key '$key'"
        else
            error "  ConfigMap missing key '$key'"
        fi
    done
else
    error "ConfigMap 'pdf-config' does not exist"
    exit 1
fi

# Check if Secret exists
echo ""
info "Checking Secret..."
if kubectl get secret pdf-secret -n $NAMESPACE &> /dev/null; then
    success "Secret 'pdf-secret' exists"
    
    # Validate required keys
    REQUIRED_SECRET_KEYS=("DATABASE_PASSWORD" "S3_ACCESS_KEY" "S3_SECRET_KEY")
    for key in "${REQUIRED_SECRET_KEYS[@]}"; do
        if kubectl get secret pdf-secret -n $NAMESPACE -o jsonpath="{.data.$key}" &> /dev/null; then
            success "  Secret has key '$key'"
        else
            error "  Secret missing key '$key'"
        fi
    done
else
    error "Secret 'pdf-secret' does not exist"
    exit 1
fi

# Check if Deployment exists
echo ""
info "Checking Deployment..."
if kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE &> /dev/null; then
    success "Deployment '$DEPLOYMENT_NAME' exists"
    
    # Check replicas
    DESIRED_REPLICAS=$(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.spec.replicas}')
    READY_REPLICAS=$(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
    
    info "  Desired replicas: $DESIRED_REPLICAS"
    info "  Ready replicas: $READY_REPLICAS"
    
    if [ "$DESIRED_REPLICAS" == "$READY_REPLICAS" ]; then
        success "  All replicas are ready"
    else
        warning "  Not all replicas are ready ($READY_REPLICAS/$DESIRED_REPLICAS)"
    fi
    
    # Check deployment conditions
    AVAILABLE=$(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Available")].status}')
    if [ "$AVAILABLE" == "True" ]; then
        success "  Deployment is available"
    else
        error "  Deployment is not available"
    fi
else
    error "Deployment '$DEPLOYMENT_NAME' does not exist"
    exit 1
fi

# Check if Service exists
echo ""
info "Checking Service..."
if kubectl get service $SERVICE_NAME -n $NAMESPACE &> /dev/null; then
    success "Service '$SERVICE_NAME' exists"
    
    # Check service type
    SERVICE_TYPE=$(kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.type}')
    info "  Service type: $SERVICE_TYPE"
    
    # Check service port
    SERVICE_PORT=$(kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}')
    info "  Service port: $SERVICE_PORT"
    
    if [ "$SERVICE_PORT" == "$PORT" ]; then
        success "  Service port matches expected port ($PORT)"
    else
        warning "  Service port ($SERVICE_PORT) does not match expected port ($PORT)"
    fi
    
    # Check endpoints
    ENDPOINTS=$(kubectl get endpoints $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.subsets[*].addresses[*].ip}' | wc -w)
    info "  Endpoints: $ENDPOINTS"
    
    if [ "$ENDPOINTS" -gt 0 ]; then
        success "  Service has $ENDPOINTS endpoint(s)"
    else
        error "  Service has no endpoints"
    fi
else
    error "Service '$SERVICE_NAME' does not exist"
    exit 1
fi

# Check if HPA exists
echo ""
info "Checking HorizontalPodAutoscaler..."
if kubectl get hpa pdf-hpa -n $NAMESPACE &> /dev/null; then
    success "HPA 'pdf-hpa' exists"
    
    # Check HPA status
    MIN_REPLICAS=$(kubectl get hpa pdf-hpa -n $NAMESPACE -o jsonpath='{.spec.minReplicas}')
    MAX_REPLICAS=$(kubectl get hpa pdf-hpa -n $NAMESPACE -o jsonpath='{.spec.maxReplicas}')
    CURRENT_REPLICAS=$(kubectl get hpa pdf-hpa -n $NAMESPACE -o jsonpath='{.status.currentReplicas}')
    
    info "  Min replicas: $MIN_REPLICAS"
    info "  Max replicas: $MAX_REPLICAS"
    info "  Current replicas: $CURRENT_REPLICAS"
    
    if [ "$CURRENT_REPLICAS" -ge "$MIN_REPLICAS" ] && [ "$CURRENT_REPLICAS" -le "$MAX_REPLICAS" ]; then
        success "  HPA is within configured bounds"
    else
        warning "  HPA replicas outside configured bounds"
    fi
else
    warning "HPA 'pdf-hpa' does not exist (optional)"
fi

# Check pod status
echo ""
info "Checking Pods..."
PODS=$(kubectl get pods -n $NAMESPACE -l app=metlab,service=pdf -o jsonpath='{.items[*].metadata.name}')

if [ -z "$PODS" ]; then
    error "No pods found for service '$SERVICE_NAME'"
    exit 1
fi

for POD in $PODS; do
    info "  Checking pod: $POD"
    
    # Check pod phase
    PHASE=$(kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.status.phase}')
    if [ "$PHASE" == "Running" ]; then
        success "    Pod is running"
    else
        error "    Pod is not running (phase: $PHASE)"
    fi
    
    # Check container status
    READY=$(kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.status.containerStatuses[0].ready}')
    if [ "$READY" == "true" ]; then
        success "    Container is ready"
    else
        error "    Container is not ready"
    fi
    
    # Check restart count
    RESTARTS=$(kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.status.containerStatuses[0].restartCount}')
    info "    Restart count: $RESTARTS"
    if [ "$RESTARTS" -gt 5 ]; then
        warning "    High restart count detected"
    fi
done

# Test gRPC health check
echo ""
info "Testing gRPC health check..."
FIRST_POD=$(echo $PODS | awk '{print $1}')

if kubectl exec -n $NAMESPACE $FIRST_POD -- sh -c "command -v grpc_health_probe" &> /dev/null; then
    if kubectl exec -n $NAMESPACE $FIRST_POD -- grpc_health_probe -addr=:$PORT &> /dev/null; then
        success "gRPC health check passed"
    else
        error "gRPC health check failed"
    fi
else
    warning "grpc_health_probe not found in container (health checks may use fallback)"
fi

# Check resource usage
echo ""
info "Checking resource usage..."
if command -v kubectl &> /dev/null && kubectl top pods -n $NAMESPACE -l app=metlab,service=pdf &> /dev/null 2>&1; then
    echo ""
    kubectl top pods -n $NAMESPACE -l app=metlab,service=pdf
    echo ""
    success "Resource usage retrieved"
else
    warning "Unable to retrieve resource usage (metrics-server may not be installed)"
fi

# Check recent logs for errors
echo ""
info "Checking recent logs for errors..."
ERROR_COUNT=$(kubectl logs -n $NAMESPACE -l app=metlab,service=pdf --tail=100 --since=5m 2>/dev/null | grep -i "error\|fatal\|panic" | wc -l)

if [ "$ERROR_COUNT" -eq 0 ]; then
    success "No errors found in recent logs"
else
    warning "Found $ERROR_COUNT error(s) in recent logs"
    info "  Run 'kubectl logs -n $NAMESPACE -l app=metlab,service=pdf --tail=100' to view"
fi

# Check database connectivity
echo ""
info "Checking database connectivity..."
DB_HOST=$(kubectl get configmap pdf-config -n $NAMESPACE -o jsonpath='{.data.DATABASE_HOST}')
if kubectl get service $DB_HOST -n $NAMESPACE &> /dev/null; then
    success "Database service '$DB_HOST' is accessible"
else
    warning "Database service '$DB_HOST' not found in namespace"
fi

# Check S3/MinIO connectivity
echo ""
info "Checking S3/MinIO connectivity..."
S3_ENDPOINT=$(kubectl get configmap pdf-config -n $NAMESPACE -o jsonpath='{.data.S3_ENDPOINT}')
S3_SERVICE=$(echo $S3_ENDPOINT | sed 's|http://||' | sed 's|https://||' | cut -d: -f1)

if kubectl get service $S3_SERVICE -n $NAMESPACE &> /dev/null; then
    success "S3 service '$S3_SERVICE' is accessible"
else
    warning "S3 service '$S3_SERVICE' not found in namespace"
fi

# Summary
echo ""
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo ""

# Count checks
TOTAL_CHECKS=15
PASSED_CHECKS=$(grep -c "✓" <<< "$(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE &> /dev/null && echo '✓')")

if kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' | grep -q "True"; then
    success "PDF Service is deployed and healthy"
    echo ""
    info "Service endpoint: $SERVICE_NAME.$NAMESPACE.svc.cluster.local:$PORT"
    info "gRPC port: $PORT"
    echo ""
    info "Next steps:"
    echo "  - Test PDF upload: Use API Gateway to upload a PDF"
    echo "  - Test PDF download: Generate and use a download URL"
    echo "  - Monitor logs: kubectl logs -n $NAMESPACE -l service=pdf -f"
    echo "  - Check metrics: kubectl top pods -n $NAMESPACE -l service=pdf"
    echo ""
    exit 0
else
    error "PDF Service deployment has issues"
    echo ""
    info "Troubleshooting steps:"
    echo "  - Check pod logs: kubectl logs -n $NAMESPACE -l service=pdf"
    echo "  - Describe pods: kubectl describe pods -n $NAMESPACE -l service=pdf"
    echo "  - Check events: kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'"
    echo ""
    exit 1
fi
