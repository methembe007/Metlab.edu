#!/bin/bash

# Collaboration Service Deployment Validation Script
# This script validates that the Collaboration Service is properly deployed and healthy

set -e

NAMESPACE="metlab-dev"
SERVICE_NAME="collaboration"
DEPLOYMENT_NAME="collaboration"
SERVICE_PORT="50055"

echo "=========================================="
echo "Collaboration Service Deployment Validation"
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
    echo -e "ℹ $1"
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
if kubectl get configmap collaboration-config -n $NAMESPACE &> /dev/null; then
    success "ConfigMap 'collaboration-config' exists"
    
    # Validate ConfigMap keys
    REQUIRED_KEYS=("PORT" "ENV" "DATABASE_HOST" "DATABASE_PORT" "DATABASE_USER" "DATABASE_NAME" "REDIS_HOST" "REDIS_PORT" "REDIS_DB" "REDIS_POOL_SIZE" "MAX_STUDY_GROUPS_PER_STUDENT" "MAX_STUDY_GROUP_MEMBERS" "MAX_MESSAGE_LENGTH" "MAX_IMAGE_SIZE_MB" "MESSAGE_RETENTION_DAYS" "CHAT_RATE_LIMIT_PER_MINUTE")
    for key in "${REQUIRED_KEYS[@]}"; do
        if kubectl get configmap collaboration-config -n $NAMESPACE -o jsonpath="{.data.$key}" &> /dev/null; then
            success "  ConfigMap key '$key' exists"
        else
            error "  ConfigMap key '$key' is missing"
        fi
    done
else
    error "ConfigMap 'collaboration-config' does not exist"
fi

# Check if Secret exists
echo ""
info "Checking Secret..."
if kubectl get secret collaboration-secret -n $NAMESPACE &> /dev/null; then
    success "Secret 'collaboration-secret' exists"
    
    # Validate Secret keys
    REQUIRED_SECRET_KEYS=("DATABASE_PASSWORD" "REDIS_PASSWORD")
    for key in "${REQUIRED_SECRET_KEYS[@]}"; do
        if kubectl get secret collaboration-secret -n $NAMESPACE -o jsonpath="{.data.$key}" &> /dev/null; then
            success "  Secret key '$key' exists"
        else
            error "  Secret key '$key' is missing"
        fi
    done
else
    error "Secret 'collaboration-secret' does not exist"
fi

# Check if Deployment exists
echo ""
info "Checking Deployment..."
if kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE &> /dev/null; then
    success "Deployment '$DEPLOYMENT_NAME' exists"
    
    # Check deployment status
    DESIRED=$(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.spec.replicas}')
    READY=$(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
    
    info "  Desired replicas: $DESIRED"
    info "  Ready replicas: $READY"
    
    if [ "$DESIRED" == "$READY" ]; then
        success "  All replicas are ready"
    else
        warning "  Not all replicas are ready ($READY/$DESIRED)"
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
    PORT=$(kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}')
    info "  Service port: $PORT"
    
    if [ "$PORT" == "$SERVICE_PORT" ]; then
        success "  Service port is correct ($SERVICE_PORT)"
    else
        error "  Service port is incorrect (expected $SERVICE_PORT, got $PORT)"
    fi
else
    error "Service '$SERVICE_NAME' does not exist"
fi

# Check if HPA exists
echo ""
info "Checking HorizontalPodAutoscaler..."
if kubectl get hpa collaboration-hpa -n $NAMESPACE &> /dev/null; then
    success "HPA 'collaboration-hpa' exists"
    
    # Check HPA status
    MIN_REPLICAS=$(kubectl get hpa collaboration-hpa -n $NAMESPACE -o jsonpath='{.spec.minReplicas}')
    MAX_REPLICAS=$(kubectl get hpa collaboration-hpa -n $NAMESPACE -o jsonpath='{.spec.maxReplicas}')
    CURRENT_REPLICAS=$(kubectl get hpa collaboration-hpa -n $NAMESPACE -o jsonpath='{.status.currentReplicas}')
    
    info "  Min replicas: $MIN_REPLICAS"
    info "  Max replicas: $MAX_REPLICAS"
    info "  Current replicas: $CURRENT_REPLICAS"
else
    warning "HPA 'collaboration-hpa' does not exist (optional)"
fi

# Check pod status
echo ""
info "Checking Pods..."
PODS=$(kubectl get pods -n $NAMESPACE -l service=$SERVICE_NAME -o jsonpath='{.items[*].metadata.name}')

if [ -z "$PODS" ]; then
    error "No pods found for service '$SERVICE_NAME'"
    exit 1
fi

for POD in $PODS; do
    info "  Checking pod: $POD"
    
    # Check pod status
    POD_STATUS=$(kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.status.phase}')
    if [ "$POD_STATUS" == "Running" ]; then
        success "    Pod is Running"
    else
        error "    Pod status: $POD_STATUS"
    fi
    
    # Check container status
    CONTAINER_READY=$(kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.status.containerStatuses[0].ready}')
    if [ "$CONTAINER_READY" == "true" ]; then
        success "    Container is ready"
    else
        error "    Container is not ready"
    fi
    
    # Check restart count
    RESTART_COUNT=$(kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.status.containerStatuses[0].restartCount}')
    if [ "$RESTART_COUNT" == "0" ]; then
        success "    No restarts"
    else
        warning "    Restart count: $RESTART_COUNT"
    fi
done

# Check dependencies
echo ""
info "Checking Dependencies..."

# Check PostgreSQL
if kubectl get service postgres -n $NAMESPACE &> /dev/null; then
    success "PostgreSQL service exists"
else
    warning "PostgreSQL service not found (required dependency)"
fi

# Check Redis
if kubectl get service redis -n $NAMESPACE &> /dev/null; then
    success "Redis service exists"
else
    warning "Redis service not found (required dependency for pub/sub)"
fi

# Test connectivity (if pods are running)
echo ""
info "Testing Connectivity..."

FIRST_POD=$(echo $PODS | awk '{print $1}')

if [ ! -z "$FIRST_POD" ]; then
    # Test database connectivity
    info "  Testing database connectivity from pod..."
    if kubectl exec -n $NAMESPACE $FIRST_POD -- nc -zv postgres 5432 &> /dev/null; then
        success "    Database is reachable"
    else
        warning "    Database connectivity test failed"
    fi
    
    # Test Redis connectivity
    info "  Testing Redis connectivity from pod..."
    if kubectl exec -n $NAMESPACE $FIRST_POD -- nc -zv redis 6379 &> /dev/null; then
        success "    Redis is reachable"
    else
        warning "    Redis connectivity test failed"
    fi
fi

# Summary
echo ""
echo "=========================================="
echo "Validation Summary"
echo "=========================================="

# Count checks
TOTAL_CHECKS=0
PASSED_CHECKS=0

# This is a simplified summary - in a real script, you'd track each check
info "Deployment validation completed"
info "Review the output above for any errors or warnings"

echo ""
info "To view logs, run:"
echo "  kubectl logs -n $NAMESPACE -l service=$SERVICE_NAME --tail=50"
echo ""
info "To port-forward for testing, run:"
echo "  kubectl port-forward -n $NAMESPACE svc/$SERVICE_NAME $SERVICE_PORT:$SERVICE_PORT"
echo ""
info "To test health check, run:"
echo "  grpc_health_probe -addr=localhost:$SERVICE_PORT"
echo ""
info "To test Redis pub/sub functionality:"
echo "  kubectl exec -n $NAMESPACE -it $FIRST_POD -- redis-cli -h redis PING"

echo ""
echo "=========================================="
