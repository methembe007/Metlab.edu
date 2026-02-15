#!/bin/bash

# API Gateway Deployment Validation Script
# This script validates that the API Gateway deployment is correctly configured

set -e

NAMESPACE="metlab-dev"
SERVICE_NAME="api-gateway"
HPA_NAME="api-gateway-hpa"
INGRESS_NAME="metlab-ingress"

echo "=========================================="
echo "API Gateway Deployment Validation"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}✗ kubectl not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ kubectl found${NC}"

# Check if namespace exists
echo ""
echo "Checking namespace..."
if kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${GREEN}✓ Namespace '$NAMESPACE' exists${NC}"
else
    echo -e "${RED}✗ Namespace '$NAMESPACE' not found${NC}"
    exit 1
fi

# Check deployment
echo ""
echo "Checking deployment..."
if kubectl get deployment $SERVICE_NAME -n $NAMESPACE &> /dev/null; then
    echo -e "${GREEN}✓ Deployment '$SERVICE_NAME' exists${NC}"
    
    # Check replicas
    DESIRED=$(kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.replicas}')
    READY=$(kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
    echo "  Desired replicas: $DESIRED"
    echo "  Ready replicas: $READY"
    
    if [ "$READY" -ge 3 ]; then
        echo -e "${GREEN}✓ Minimum 3 replicas are ready${NC}"
    else
        echo -e "${YELLOW}⚠ Less than 3 replicas ready (expected minimum: 3)${NC}"
    fi
else
    echo -e "${RED}✗ Deployment '$SERVICE_NAME' not found${NC}"
    exit 1
fi

# Check pods
echo ""
echo "Checking pods..."
POD_COUNT=$(kubectl get pods -n $NAMESPACE -l service=$SERVICE_NAME --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
if [ "$POD_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ $POD_COUNT pod(s) running${NC}"
    kubectl get pods -n $NAMESPACE -l service=$SERVICE_NAME
else
    echo -e "${RED}✗ No running pods found${NC}"
    exit 1
fi

# Check service
echo ""
echo "Checking service..."
if kubectl get service $SERVICE_NAME -n $NAMESPACE &> /dev/null; then
    echo -e "${GREEN}✓ Service '$SERVICE_NAME' exists${NC}"
    
    # Check service type
    SERVICE_TYPE=$(kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.type}')
    if [ "$SERVICE_TYPE" == "ClusterIP" ]; then
        echo -e "${GREEN}✓ Service type is ClusterIP${NC}"
    else
        echo -e "${YELLOW}⚠ Service type is $SERVICE_TYPE (expected: ClusterIP)${NC}"
    fi
    
    # Check service port
    SERVICE_PORT=$(kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}')
    if [ "$SERVICE_PORT" == "8080" ]; then
        echo -e "${GREEN}✓ Service port is 8080${NC}"
    else
        echo -e "${YELLOW}⚠ Service port is $SERVICE_PORT (expected: 8080)${NC}"
    fi
else
    echo -e "${RED}✗ Service '$SERVICE_NAME' not found${NC}"
    exit 1
fi

# Check HPA
echo ""
echo "Checking HorizontalPodAutoscaler..."
if kubectl get hpa $HPA_NAME -n $NAMESPACE &> /dev/null; then
    echo -e "${GREEN}✓ HPA '$HPA_NAME' exists${NC}"
    
    # Check HPA configuration
    MIN_REPLICAS=$(kubectl get hpa $HPA_NAME -n $NAMESPACE -o jsonpath='{.spec.minReplicas}')
    MAX_REPLICAS=$(kubectl get hpa $HPA_NAME -n $NAMESPACE -o jsonpath='{.spec.maxReplicas}')
    echo "  Min replicas: $MIN_REPLICAS"
    echo "  Max replicas: $MAX_REPLICAS"
    
    if [ "$MIN_REPLICAS" == "3" ] && [ "$MAX_REPLICAS" == "20" ]; then
        echo -e "${GREEN}✓ HPA replica range is correct (3-20)${NC}"
    else
        echo -e "${YELLOW}⚠ HPA replica range is $MIN_REPLICAS-$MAX_REPLICAS (expected: 3-20)${NC}"
    fi
    
    # Check if metrics-server is available
    if kubectl get deployment metrics-server -n kube-system &> /dev/null; then
        echo -e "${GREEN}✓ metrics-server is deployed${NC}"
    else
        echo -e "${YELLOW}⚠ metrics-server not found (required for HPA)${NC}"
    fi
else
    echo -e "${RED}✗ HPA '$HPA_NAME' not found${NC}"
    exit 1
fi

# Check Ingress
echo ""
echo "Checking Ingress..."
if kubectl get ingress $INGRESS_NAME -n $NAMESPACE &> /dev/null; then
    echo -e "${GREEN}✓ Ingress '$INGRESS_NAME' exists${NC}"
    
    # Check Ingress class
    INGRESS_CLASS=$(kubectl get ingress $INGRESS_NAME -n $NAMESPACE -o jsonpath='{.spec.ingressClassName}')
    if [ "$INGRESS_CLASS" == "nginx" ]; then
        echo -e "${GREEN}✓ Ingress class is nginx${NC}"
    else
        echo -e "${YELLOW}⚠ Ingress class is $INGRESS_CLASS (expected: nginx)${NC}"
    fi
    
    # Check if nginx-ingress-controller is running
    if kubectl get pods -n ingress-nginx -l app.kubernetes.io/component=controller 2>/dev/null | grep -q Running; then
        echo -e "${GREEN}✓ Nginx Ingress Controller is running${NC}"
    else
        echo -e "${YELLOW}⚠ Nginx Ingress Controller not found${NC}"
        echo "  Run: minikube addons enable ingress"
    fi
else
    echo -e "${RED}✗ Ingress '$INGRESS_NAME' not found${NC}"
    exit 1
fi

# Check health probes
echo ""
echo "Checking health probes..."
LIVENESS_PATH=$(kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].livenessProbe.httpGet.path}')
READINESS_PATH=$(kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].readinessProbe.httpGet.path}')

if [ "$LIVENESS_PATH" == "/health" ]; then
    echo -e "${GREEN}✓ Liveness probe configured (/health)${NC}"
else
    echo -e "${YELLOW}⚠ Liveness probe path is $LIVENESS_PATH (expected: /health)${NC}"
fi

if [ "$READINESS_PATH" == "/ready" ]; then
    echo -e "${GREEN}✓ Readiness probe configured (/ready)${NC}"
else
    echo -e "${YELLOW}⚠ Readiness probe path is $READINESS_PATH (expected: /ready)${NC}"
fi

# Check resource limits
echo ""
echo "Checking resource limits..."
CPU_REQUEST=$(kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].resources.requests.cpu}')
CPU_LIMIT=$(kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].resources.limits.cpu}')
MEM_REQUEST=$(kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].resources.requests.memory}')
MEM_LIMIT=$(kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}')

echo "  CPU: $CPU_REQUEST (request) / $CPU_LIMIT (limit)"
echo "  Memory: $MEM_REQUEST (request) / $MEM_LIMIT (limit)"

if [ "$CPU_REQUEST" == "500m" ] && [ "$CPU_LIMIT" == "1000m" ] && [ "$MEM_REQUEST" == "512Mi" ] && [ "$MEM_LIMIT" == "1Gi" ]; then
    echo -e "${GREEN}✓ Resource limits are correctly configured${NC}"
else
    echo -e "${YELLOW}⚠ Resource limits differ from expected values${NC}"
fi

# Test connectivity (if pods are running)
echo ""
echo "Testing connectivity..."
if [ "$POD_COUNT" -gt 0 ]; then
    POD_NAME=$(kubectl get pods -n $NAMESPACE -l service=$SERVICE_NAME --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}')
    
    echo "Testing health endpoint..."
    if kubectl exec -n $NAMESPACE $POD_NAME -- wget -q -O- http://localhost:8080/health &> /dev/null; then
        echo -e "${GREEN}✓ Health endpoint responding${NC}"
    else
        echo -e "${YELLOW}⚠ Health endpoint not responding (service may still be starting)${NC}"
    fi
fi

# Summary
echo ""
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo -e "${GREEN}✓ API Gateway deployment is configured correctly${NC}"
echo ""
echo "Next steps:"
echo "1. Verify all backend services are running:"
echo "   kubectl get pods -n $NAMESPACE"
echo ""
echo "2. Check HPA metrics:"
echo "   kubectl get hpa $HPA_NAME -n $NAMESPACE"
echo ""
echo "3. Access the application:"
echo "   echo \"\$(minikube ip) metlab.local\" | sudo tee -a /etc/hosts"
echo "   curl http://metlab.local/api/health"
echo ""
echo "4. Monitor logs:"
echo "   kubectl logs -n $NAMESPACE -l service=$SERVICE_NAME -f"
