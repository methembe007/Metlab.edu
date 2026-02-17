#!/bin/bash

# Video Service Deployment Validation Script
# This script validates the Video Service and Video Worker deployments

set -e

NAMESPACE="metlab-dev"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Video Service Deployment Validation"
echo "=========================================="
echo ""

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

# Check if namespace exists
echo "Checking namespace..."
if kubectl get namespace $NAMESPACE &> /dev/null; then
    success "Namespace '$NAMESPACE' exists"
else
    error "Namespace '$NAMESPACE' does not exist"
    exit 1
fi
echo ""

# Check ConfigMaps
echo "Checking ConfigMaps..."
if kubectl get configmap video-config -n $NAMESPACE &> /dev/null; then
    success "ConfigMap 'video-config' exists"
else
    error "ConfigMap 'video-config' does not exist"
    exit 1
fi

if kubectl get configmap video-worker-config -n $NAMESPACE &> /dev/null; then
    success "ConfigMap 'video-worker-config' exists"
else
    error "ConfigMap 'video-worker-config' does not exist"
    exit 1
fi
echo ""

# Check Secrets
echo "Checking Secrets..."
if kubectl get secret video-secret -n $NAMESPACE &> /dev/null; then
    success "Secret 'video-secret' exists"
else
    error "Secret 'video-secret' does not exist"
    exit 1
fi

if kubectl get secret video-worker-secret -n $NAMESPACE &> /dev/null; then
    success "Secret 'video-worker-secret' exists"
else
    error "Secret 'video-worker-secret' does not exist"
    exit 1
fi
echo ""

# Check PersistentVolumeClaims
echo "Checking PersistentVolumeClaims..."
if kubectl get pvc video-processing-pvc -n $NAMESPACE &> /dev/null; then
    PVC_STATUS=$(kubectl get pvc video-processing-pvc -n $NAMESPACE -o jsonpath='{.status.phase}')
    if [ "$PVC_STATUS" == "Bound" ]; then
        success "PVC 'video-processing-pvc' is Bound"
    else
        warning "PVC 'video-processing-pvc' status: $PVC_STATUS"
    fi
else
    error "PVC 'video-processing-pvc' does not exist"
    exit 1
fi

if kubectl get pvc video-worker-processing-pvc -n $NAMESPACE &> /dev/null; then
    PVC_STATUS=$(kubectl get pvc video-worker-processing-pvc -n $NAMESPACE -o jsonpath='{.status.phase}')
    if [ "$PVC_STATUS" == "Bound" ]; then
        success "PVC 'video-worker-processing-pvc' is Bound"
    else
        warning "PVC 'video-worker-processing-pvc' status: $PVC_STATUS"
    fi
else
    error "PVC 'video-worker-processing-pvc' does not exist"
    exit 1
fi
echo ""

# Check Deployments
echo "Checking Deployments..."
if kubectl get deployment video -n $NAMESPACE &> /dev/null; then
    success "Deployment 'video' exists"
    
    # Check replicas
    DESIRED=$(kubectl get deployment video -n $NAMESPACE -o jsonpath='{.spec.replicas}')
    READY=$(kubectl get deployment video -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
    
    if [ "$READY" == "$DESIRED" ]; then
        success "Video Service: $READY/$DESIRED replicas ready"
    else
        warning "Video Service: $READY/$DESIRED replicas ready"
    fi
else
    error "Deployment 'video' does not exist"
    exit 1
fi

if kubectl get deployment video-worker -n $NAMESPACE &> /dev/null; then
    success "Deployment 'video-worker' exists"
    
    # Check replicas
    DESIRED=$(kubectl get deployment video-worker -n $NAMESPACE -o jsonpath='{.spec.replicas}')
    READY=$(kubectl get deployment video-worker -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
    
    if [ "$READY" == "$DESIRED" ]; then
        success "Video Worker: $READY/$DESIRED replicas ready"
    else
        warning "Video Worker: $READY/$DESIRED replicas ready"
    fi
else
    error "Deployment 'video-worker' does not exist"
    exit 1
fi
echo ""

# Check Services
echo "Checking Services..."
if kubectl get service video -n $NAMESPACE &> /dev/null; then
    success "Service 'video' exists"
    PORT=$(kubectl get service video -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}')
    success "Video Service listening on port $PORT"
else
    error "Service 'video' does not exist"
    exit 1
fi

if kubectl get service video-worker -n $NAMESPACE &> /dev/null; then
    success "Service 'video-worker' exists"
    PORT=$(kubectl get service video-worker -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}')
    success "Video Worker Service listening on port $PORT"
else
    error "Service 'video-worker' does not exist"
    exit 1
fi
echo ""

# Check HorizontalPodAutoscalers
echo "Checking HorizontalPodAutoscalers..."
if kubectl get hpa video-hpa -n $NAMESPACE &> /dev/null; then
    success "HPA 'video-hpa' exists"
    MIN=$(kubectl get hpa video-hpa -n $NAMESPACE -o jsonpath='{.spec.minReplicas}')
    MAX=$(kubectl get hpa video-hpa -n $NAMESPACE -o jsonpath='{.spec.maxReplicas}')
    success "Video Service HPA: min=$MIN, max=$MAX"
else
    warning "HPA 'video-hpa' does not exist"
fi

if kubectl get hpa video-worker-hpa -n $NAMESPACE &> /dev/null; then
    success "HPA 'video-worker-hpa' exists"
    MIN=$(kubectl get hpa video-worker-hpa -n $NAMESPACE -o jsonpath='{.spec.minReplicas}')
    MAX=$(kubectl get hpa video-worker-hpa -n $NAMESPACE -o jsonpath='{.spec.maxReplicas}')
    success "Video Worker HPA: min=$MIN, max=$MAX"
else
    warning "HPA 'video-worker-hpa' does not exist"
fi
echo ""

# Check Pods
echo "Checking Pods..."
VIDEO_PODS=$(kubectl get pods -n $NAMESPACE -l service=video --no-headers 2>/dev/null | wc -l)
if [ "$VIDEO_PODS" -gt 0 ]; then
    success "Found $VIDEO_PODS Video Service pod(s)"
    
    # Check pod status
    NOT_RUNNING=$(kubectl get pods -n $NAMESPACE -l service=video --no-headers 2>/dev/null | grep -v "Running" | wc -l)
    if [ "$NOT_RUNNING" -gt 0 ]; then
        warning "$NOT_RUNNING Video Service pod(s) not in Running state"
    fi
else
    error "No Video Service pods found"
fi

WORKER_PODS=$(kubectl get pods -n $NAMESPACE -l service=video-worker --no-headers 2>/dev/null | wc -l)
if [ "$WORKER_PODS" -gt 0 ]; then
    success "Found $WORKER_PODS Video Worker pod(s)"
    
    # Check pod status
    NOT_RUNNING=$(kubectl get pods -n $NAMESPACE -l service=video-worker --no-headers 2>/dev/null | grep -v "Running" | wc -l)
    if [ "$NOT_RUNNING" -gt 0 ]; then
        warning "$NOT_RUNNING Video Worker pod(s) not in Running state"
    fi
else
    error "No Video Worker pods found"
fi
echo ""

# Check Pod Health
echo "Checking Pod Health..."
VIDEO_POD=$(kubectl get pods -n $NAMESPACE -l service=video -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$VIDEO_POD" ]; then
    if kubectl exec -n $NAMESPACE $VIDEO_POD -- grpc_health_probe -addr=:50052 &> /dev/null; then
        success "Video Service health check passed"
    else
        warning "Video Service health check failed (may not be implemented yet)"
    fi
else
    warning "No Video Service pod available for health check"
fi

WORKER_POD=$(kubectl get pods -n $NAMESPACE -l service=video-worker -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$WORKER_POD" ]; then
    if kubectl exec -n $NAMESPACE $WORKER_POD -- curl -f http://localhost:9090/health &> /dev/null; then
        success "Video Worker health check passed"
    else
        warning "Video Worker health check failed (may not be implemented yet)"
    fi
else
    warning "No Video Worker pod available for health check"
fi
echo ""

# Check Resource Usage
echo "Checking Resource Usage..."
if command -v kubectl &> /dev/null && kubectl top pods -n $NAMESPACE &> /dev/null; then
    echo "Video Service pods:"
    kubectl top pods -n $NAMESPACE -l service=video 2>/dev/null || warning "Metrics not available"
    echo ""
    echo "Video Worker pods:"
    kubectl top pods -n $NAMESPACE -l service=video-worker 2>/dev/null || warning "Metrics not available"
else
    warning "kubectl top not available or metrics-server not installed"
fi
echo ""

# Check Recent Events
echo "Checking Recent Events..."
EVENTS=$(kubectl get events -n $NAMESPACE --field-selector involvedObject.kind=Pod --sort-by='.lastTimestamp' 2>/dev/null | grep -i "video" | tail -5)
if [ -n "$EVENTS" ]; then
    echo "$EVENTS"
else
    success "No recent events for Video Service"
fi
echo ""

# Check Dependencies
echo "Checking Dependencies..."
if kubectl get service postgres -n $NAMESPACE &> /dev/null; then
    success "PostgreSQL service is available"
else
    error "PostgreSQL service not found"
fi

if kubectl get service redis -n $NAMESPACE &> /dev/null; then
    success "Redis service is available"
else
    error "Redis service not found"
fi

if kubectl get service minio-service -n $NAMESPACE &> /dev/null; then
    success "MinIO service is available"
else
    warning "MinIO service not found (may use external S3)"
fi
echo ""

# Summary
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo ""

# Count issues
ERRORS=$(kubectl get pods -n $NAMESPACE -l service=video --no-headers 2>/dev/null | grep -v "Running" | wc -l)
ERRORS=$((ERRORS + $(kubectl get pods -n $NAMESPACE -l service=video-worker --no-headers 2>/dev/null | grep -v "Running" | wc -l)))

if [ "$ERRORS" -eq 0 ]; then
    success "All Video Service components are healthy!"
    echo ""
    echo "Next steps:"
    echo "1. Test video upload: Use API Gateway to upload a test video"
    echo "2. Monitor processing: Check video-worker logs for processing status"
    echo "3. Verify storage: Check MinIO/S3 for uploaded videos and thumbnails"
    echo "4. Test streaming: Request streaming URL and verify playback"
else
    warning "Found $ERRORS issue(s) that need attention"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check pod logs: kubectl logs -n $NAMESPACE -l service=video"
    echo "2. Check pod logs: kubectl logs -n $NAMESPACE -l service=video-worker"
    echo "3. Describe pods: kubectl describe pods -n $NAMESPACE -l service=video"
    echo "4. Check events: kubectl get events -n $NAMESPACE"
fi

echo ""
echo "=========================================="
