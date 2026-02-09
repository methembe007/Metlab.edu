#!/bin/bash

# Metlab.edu - kubectl Configuration Script
# This script configures kubectl for the Metlab.edu development environment

set -e

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}kubectl Configuration for Metlab.edu${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    echo "Please install kubectl from: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Configuration
CLUSTER_NAME="metlab-dev"
DEFAULT_NAMESPACE="metlab-dev"

# Check if Minikube cluster exists
if ! minikube status -p $CLUSTER_NAME &> /dev/null; then
    echo -e "${RED}Error: Minikube cluster '$CLUSTER_NAME' is not running${NC}"
    echo "Please start the cluster first:"
    echo "  make minikube-setup"
    echo "  or"
    echo "  make minikube-start"
    exit 1
fi

echo -e "${GREEN}✓ Minikube cluster '$CLUSTER_NAME' is running${NC}"
echo ""

# Set kubectl context
echo -e "${BLUE}Setting kubectl context to '$CLUSTER_NAME'...${NC}"
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

# Set default namespace
echo -e "${BLUE}Setting default namespace to '$DEFAULT_NAMESPACE'...${NC}"
kubectl config set-context --current --namespace=$DEFAULT_NAMESPACE
echo -e "${GREEN}✓ Default namespace set to '$DEFAULT_NAMESPACE'${NC}"
echo ""

# Display current configuration
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Current kubectl Configuration${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${GREEN}Context:${NC} $(kubectl config current-context)"
echo -e "${GREEN}Cluster:${NC} $(kubectl config view --minify -o jsonpath='{.clusters[0].name}')"
echo -e "${GREEN}User:${NC} $(kubectl config view --minify -o jsonpath='{.users[0].name}')"
echo -e "${GREEN}Namespace:${NC} $(kubectl config view --minify -o jsonpath='{.contexts[0].context.namespace}')"
echo ""

# Display cluster information
echo -e "${BLUE}Cluster Information:${NC}"
kubectl cluster-info
echo ""

# Display available namespaces
echo -e "${BLUE}Available Namespaces:${NC}"
kubectl get namespaces | grep metlab || echo "No metlab namespaces found"
echo ""

# Create kubectl aliases (optional)
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Recommended kubectl Aliases${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Add these aliases to your ~/.bashrc or ~/.zshrc:"
echo ""
echo "# Metlab.edu kubectl aliases"
echo "alias k='kubectl'"
echo "alias kgp='kubectl get pods'"
echo "alias kgs='kubectl get services'"
echo "alias kgd='kubectl get deployments'"
echo "alias kl='kubectl logs'"
echo "alias kd='kubectl describe'"
echo "alias kx='kubectl exec -it'"
echo "alias kdev='kubectl config set-context --current --namespace=metlab-dev'"
echo "alias kstaging='kubectl config set-context --current --namespace=metlab-staging'"
echo "alias kprod='kubectl config set-context --current --namespace=metlab-production'"
echo ""

# Display useful commands
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Useful kubectl Commands${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}View all resources in current namespace:${NC}"
echo "  kubectl get all"
echo ""
echo -e "${GREEN}View pods with more details:${NC}"
echo "  kubectl get pods -o wide"
echo ""
echo -e "${GREEN}View pod logs:${NC}"
echo "  kubectl logs <pod-name>"
echo ""
echo -e "${GREEN}Follow pod logs:${NC}"
echo "  kubectl logs -f <pod-name>"
echo ""
echo -e "${GREEN}Describe a resource:${NC}"
echo "  kubectl describe pod <pod-name>"
echo ""
echo -e "${GREEN}Execute command in pod:${NC}"
echo "  kubectl exec -it <pod-name> -- /bin/sh"
echo ""
echo -e "${GREEN}Port forward to a service:${NC}"
echo "  kubectl port-forward svc/<service-name> <local-port>:<service-port>"
echo ""
echo -e "${GREEN}Switch namespace:${NC}"
echo "  kubectl config set-context --current --namespace=<namespace>"
echo ""
echo -e "${GREEN}View cluster events:${NC}"
echo "  kubectl get events --sort-by=.metadata.creationTimestamp"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ kubectl configuration complete!${NC}"
echo -e "${GREEN}========================================${NC}"
