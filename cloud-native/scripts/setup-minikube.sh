#!/bin/bash

# Metlab.edu - Minikube Setup Script
# This script sets up a local Kubernetes environment with Minikube

set -e

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Metlab.edu - Minikube Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Minikube is installed
if ! command -v minikube &> /dev/null; then
    echo -e "${RED}Error: Minikube is not installed${NC}"
    echo "Please install Minikube from: https://minikube.sigs.k8s.io/docs/start/"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    echo "Please install kubectl from: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Configuration
CLUSTER_NAME="metlab-dev"
CPUS=4
MEMORY=3072
DRIVER="docker"

# Check if Minikube cluster already exists
if minikube status -p $CLUSTER_NAME &> /dev/null; then
    echo -e "${YELLOW}Minikube cluster '$CLUSTER_NAME' already exists${NC}"
    read -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Deleting existing cluster...${NC}"
        minikube delete -p $CLUSTER_NAME
    else
        echo -e "${BLUE}Using existing cluster${NC}"
        minikube start -p $CLUSTER_NAME
    fi
else
    echo -e "${BLUE}Creating new Minikube cluster...${NC}"
fi

# Start Minikube with appropriate resources
echo -e "${BLUE}Starting Minikube cluster '$CLUSTER_NAME'...${NC}"
minikube start \
    -p $CLUSTER_NAME \
    --cpus=$CPUS \
    --memory=$MEMORY \
    --driver=$DRIVER \
    --kubernetes-version=stable

echo -e "${GREEN}✓ Minikube cluster started${NC}"
echo ""

# Enable required addons
echo -e "${BLUE}Enabling Minikube addons...${NC}"

echo "  - Enabling ingress addon..."
minikube addons enable ingress -p $CLUSTER_NAME

echo "  - Enabling metrics-server addon..."
minikube addons enable metrics-server -p $CLUSTER_NAME

echo "  - Enabling dashboard addon..."
minikube addons enable dashboard -p $CLUSTER_NAME

echo "  - Enabling storage-provisioner addon..."
minikube addons enable storage-provisioner -p $CLUSTER_NAME

echo "  - Enabling default-storageclass addon..."
minikube addons enable default-storageclass -p $CLUSTER_NAME

echo -e "${GREEN}✓ Addons enabled${NC}"
echo ""

# Configure kubectl context
echo -e "${BLUE}Configuring kubectl context...${NC}"
kubectl config use-context $CLUSTER_NAME

# Verify context
CURRENT_CONTEXT=$(kubectl config current-context)
if [ "$CURRENT_CONTEXT" = "$CLUSTER_NAME" ]; then
    echo -e "${GREEN}✓ kubectl context set to '$CLUSTER_NAME'${NC}"
else
    echo -e "${RED}Error: Failed to set kubectl context${NC}"
    exit 1
fi
echo ""

# Create namespaces
echo -e "${BLUE}Creating Kubernetes namespaces...${NC}"
kubectl apply -f ../infrastructure/k8s/namespace.yaml

# Create additional namespaces for staging and production (for future use)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: metlab-staging
  labels:
    name: metlab-staging
    environment: staging
---
apiVersion: v1
kind: Namespace
metadata:
  name: metlab-production
  labels:
    name: metlab-production
    environment: production
EOF

echo -e "${GREEN}✓ Namespaces created${NC}"
echo ""

# Display cluster information
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Cluster Information${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Cluster Name:${NC} $CLUSTER_NAME"
echo -e "${GREEN}Kubernetes Version:${NC} $(kubectl version --short 2>/dev/null | grep Server | awk '{print $3}')"
echo -e "${GREEN}CPUs:${NC} $CPUS"
echo -e "${GREEN}Memory:${NC} ${MEMORY}MB"
echo -e "${GREEN}Driver:${NC} $DRIVER"
echo ""

echo -e "${GREEN}Namespaces:${NC}"
kubectl get namespaces | grep metlab
echo ""

echo -e "${GREEN}Enabled Addons:${NC}"
minikube addons list -p $CLUSTER_NAME | grep enabled
echo ""

# Display useful commands
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Useful Commands${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}View cluster status:${NC}"
echo "  minikube status -p $CLUSTER_NAME"
echo ""
echo -e "${GREEN}Access Kubernetes dashboard:${NC}"
echo "  minikube dashboard -p $CLUSTER_NAME"
echo ""
echo -e "${GREEN}View cluster IP:${NC}"
echo "  minikube ip -p $CLUSTER_NAME"
echo ""
echo -e "${GREEN}SSH into cluster:${NC}"
echo "  minikube ssh -p $CLUSTER_NAME"
echo ""
echo -e "${GREEN}Stop cluster:${NC}"
echo "  minikube stop -p $CLUSTER_NAME"
echo ""
echo -e "${GREEN}Delete cluster:${NC}"
echo "  minikube delete -p $CLUSTER_NAME"
echo ""
echo -e "${GREEN}Deploy services:${NC}"
echo "  kubectl apply -f infrastructure/k8s/"
echo ""
echo -e "${GREEN}Start development with Tilt:${NC}"
echo "  tilt up"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Minikube setup complete!${NC}"
echo -e "${GREEN}========================================${NC}"
