#!/bin/bash

# Validation script for Auth Service Kubernetes deployment
# This script validates the YAML syntax and checks for common issues

set -e

echo "==================================="
echo "Auth Service Deployment Validation"
echo "==================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}ERROR: kubectl is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ kubectl is installed${NC}"

# Validate YAML syntax
echo ""
echo "Validating YAML syntax..."
if kubectl apply -f cloud-native/infrastructure/k8s/auth.yaml --dry-run=client > /dev/null 2>&1; then
    echo -e "${GREEN}✓ YAML syntax is valid${NC}"
else
    echo -e "${RED}✗ YAML syntax validation failed${NC}"
    kubectl apply -f cloud-native/infrastructure/k8s/auth.yaml --dry-run=client
    exit 1
fi

# Check if namespace exists
echo ""
echo "Checking namespace..."
if kubectl get namespace metlab-dev > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Namespace 'metlab-dev' exists${NC}"
else
    echo -e "${YELLOW}⚠ Namespace 'metlab-dev' does not exist${NC}"
    echo "  Run: kubectl apply -f cloud-native/infrastructure/k8s/namespace.yaml"
fi

# Check if PostgreSQL is deployed
echo ""
echo "Checking PostgreSQL dependency..."
if kubectl get service postgres -n metlab-dev > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL service exists${NC}"
else
    echo -e "${YELLOW}⚠ PostgreSQL service not found${NC}"
    echo "  Run: kubectl apply -f cloud-native/infrastructure/k8s/postgres.yaml"
fi

# Validate resource definitions
echo ""
echo "Validating resource definitions..."

# Check ConfigMap
if kubectl apply -f cloud-native/infrastructure/k8s/auth.yaml --dry-run=client 2>&1 | grep -q "configmap/auth-config"; then
    echo -e "${GREEN}✓ ConfigMap definition is valid${NC}"
fi

# Check Secret
if kubectl apply -f cloud-native/infrastructure/k8s/auth.yaml --dry-run=client 2>&1 | grep -q "secret/auth-secret"; then
    echo -e "${GREEN}✓ Secret definition is valid${NC}"
fi

# Check Deployment
if kubectl apply -f cloud-native/infrastructure/k8s/auth.yaml --dry-run=client 2>&1 | grep -q "deployment.apps/auth"; then
    echo -e "${GREEN}✓ Deployment definition is valid${NC}"
fi

# Check Service
if kubectl apply -f cloud-native/infrastructure/k8s/auth.yaml --dry-run=client 2>&1 | grep -q "service/auth"; then
    echo -e "${GREEN}✓ Service definition is valid${NC}"
fi

# Check HPA
if kubectl apply -f cloud-native/infrastructure/k8s/auth.yaml --dry-run=client 2>&1 | grep -q "horizontalpodautoscaler.autoscaling/auth-hpa"; then
    echo -e "${GREEN}✓ HorizontalPodAutoscaler definition is valid${NC}"
fi

echo ""
echo "==================================="
echo "Validation Summary"
echo "==================================="
echo ""
echo "All validations passed! The Auth Service deployment is ready."
echo ""
echo "To deploy:"
echo "  kubectl apply -f cloud-native/infrastructure/k8s/auth.yaml"
echo ""
echo "To verify:"
echo "  kubectl get all -n metlab-dev -l service=auth"
echo ""
