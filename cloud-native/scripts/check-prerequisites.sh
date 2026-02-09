#!/bin/bash

# Metlab.edu - Prerequisites Check Script
# This script checks if all required tools are installed

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Metlab.edu - Prerequisites Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Track if all prerequisites are met
ALL_GOOD=true

# Check Docker
echo -n "Checking Docker... "
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    echo -e "${GREEN}✓ Installed (${DOCKER_VERSION})${NC}"
    
    # Check if Docker is running
    if docker info &> /dev/null; then
        echo -e "  ${GREEN}✓ Docker daemon is running${NC}"
    else
        echo -e "  ${RED}✗ Docker daemon is not running${NC}"
        ALL_GOOD=false
    fi
else
    echo -e "${RED}✗ Not installed${NC}"
    echo -e "  Install from: https://docs.docker.com/get-docker/"
    ALL_GOOD=false
fi
echo ""

# Check Minikube
echo -n "Checking Minikube... "
if command -v minikube &> /dev/null; then
    MINIKUBE_VERSION=$(minikube version --short)
    echo -e "${GREEN}✓ Installed (${MINIKUBE_VERSION})${NC}"
else
    echo -e "${RED}✗ Not installed${NC}"
    echo -e "  Install from: https://minikube.sigs.k8s.io/docs/start/"
    ALL_GOOD=false
fi
echo ""

# Check kubectl
echo -n "Checking kubectl... "
if command -v kubectl &> /dev/null; then
    KUBECTL_VERSION=$(kubectl version --client --short 2>/dev/null | awk '{print $3}')
    echo -e "${GREEN}✓ Installed (${KUBECTL_VERSION})${NC}"
else
    echo -e "${RED}✗ Not installed${NC}"
    echo -e "  Install from: https://kubernetes.io/docs/tasks/tools/"
    ALL_GOOD=false
fi
echo ""

# Check Go
echo -n "Checking Go... "
if command -v go &> /dev/null; then
    GO_VERSION=$(go version | awk '{print $3}')
    echo -e "${GREEN}✓ Installed (${GO_VERSION})${NC}"
else
    echo -e "${YELLOW}⚠ Not installed (required for backend development)${NC}"
    echo -e "  Install from: https://go.dev/dl/"
fi
echo ""

# Check Node.js
echo -n "Checking Node.js... "
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Installed (${NODE_VERSION})${NC}"
else
    echo -e "${YELLOW}⚠ Not installed (required for frontend development)${NC}"
    echo -e "  Install from: https://nodejs.org/"
fi
echo ""

# Check npm
echo -n "Checking npm... "
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓ Installed (v${NPM_VERSION})${NC}"
else
    echo -e "${YELLOW}⚠ Not installed (comes with Node.js)${NC}"
fi
echo ""

# Check protoc
echo -n "Checking protoc... "
if command -v protoc &> /dev/null; then
    PROTOC_VERSION=$(protoc --version | awk '{print $2}')
    echo -e "${GREEN}✓ Installed (${PROTOC_VERSION})${NC}"
else
    echo -e "${YELLOW}⚠ Not installed (required for proto generation)${NC}"
    echo -e "  Install from: https://grpc.io/docs/protoc-installation/"
fi
echo ""

# Check Tilt (optional)
echo -n "Checking Tilt... "
if command -v tilt &> /dev/null; then
    TILT_VERSION=$(tilt version | head -n 1 | awk '{print $2}')
    echo -e "${GREEN}✓ Installed (${TILT_VERSION})${NC}"
else
    echo -e "${YELLOW}⚠ Not installed (optional, but recommended)${NC}"
    echo -e "  Install from: https://docs.tilt.dev/install.html"
fi
echo ""

# Check make
echo -n "Checking make... "
if command -v make &> /dev/null; then
    MAKE_VERSION=$(make --version | head -n 1 | awk '{print $3}')
    echo -e "${GREEN}✓ Installed (${MAKE_VERSION})${NC}"
else
    echo -e "${YELLOW}⚠ Not installed (required for Makefile commands)${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✓ All required prerequisites are met!${NC}"
    echo ""
    echo "You can now run:"
    echo "  make minikube-setup    # Set up Minikube cluster"
    echo "  make dev               # Start development environment"
else
    echo -e "${RED}✗ Some required prerequisites are missing${NC}"
    echo ""
    echo "Please install the missing tools and run this script again."
fi
echo -e "${BLUE}========================================${NC}"
