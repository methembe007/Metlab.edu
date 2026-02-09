.PHONY: help install-go install-node install-tools build test clean dev minikube-start minikube-stop proto-gen

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Metlab.edu Cloud-Native - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# Installation targets
check-prerequisites: ## Check if all required tools are installed
	@echo "$(BLUE)Checking prerequisites...$(NC)"
ifeq ($(OS),Windows_NT)
	@powershell -ExecutionPolicy Bypass -File scripts/check-prerequisites.ps1
else
	@chmod +x scripts/check-prerequisites.sh
	@./scripts/check-prerequisites.sh
endif

install-go: ## Install Go dependencies for all services
	@echo "$(BLUE)Installing Go dependencies...$(NC)"
	@cd services/api-gateway && go mod download
	@cd services/auth && go mod download
	@cd services/video && go mod download
	@cd services/homework && go mod download
	@cd services/analytics && go mod download
	@cd services/collaboration && go mod download
	@cd services/pdf && go mod download
	@cd shared && go mod download
	@echo "$(GREEN)✓ Go dependencies installed$(NC)"

install-node: ## Install Node.js dependencies for frontend
	@echo "$(BLUE)Installing Node.js dependencies...$(NC)"
	@cd frontend && npm install
	@echo "$(GREEN)✓ Node.js dependencies installed$(NC)"

install-tools: ## Install development tools (protoc, tilt, etc.)
	@echo "$(BLUE)Installing development tools...$(NC)"
	@echo "$(YELLOW)Please ensure the following are installed:$(NC)"
	@echo "  - protoc (Protocol Buffers compiler)"
	@echo "  - protoc-gen-go and protoc-gen-go-grpc"
	@echo "  - protoc-gen-ts"
	@echo "  - Tilt (https://tilt.dev)"
	@echo "  - Minikube (https://minikube.sigs.k8s.io)"
	@echo "  - kubectl"
	@echo ""
	@echo "Run the following to install Go protoc plugins:"
	@echo "  go install google.golang.org/protobuf/cmd/protoc-gen-go@latest"
	@echo "  go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest"

# Build targets
build: build-services build-frontend ## Build all services and frontend

build-services: ## Build all Go services
	@echo "$(BLUE)Building Go services...$(NC)"
	@cd services/api-gateway && go build -o ../../bin/api-gateway ./cmd/server
	@cd services/auth && go build -o ../../bin/auth ./cmd/server
	@cd services/video && go build -o ../../bin/video ./cmd/server
	@cd services/homework && go build -o ../../bin/homework ./cmd/server
	@cd services/analytics && go build -o ../../bin/analytics ./cmd/server
	@cd services/collaboration && go build -o ../../bin/collaboration ./cmd/server
	@cd services/pdf && go build -o ../../bin/pdf ./cmd/server
	@echo "$(GREEN)✓ Services built$(NC)"

build-frontend: ## Build frontend application
	@echo "$(BLUE)Building frontend...$(NC)"
	@cd frontend && npm run build
	@echo "$(GREEN)✓ Frontend built$(NC)"

build-auth: ## Build auth service
	@cd services/auth && go build -o ../../bin/auth ./cmd/server

build-video: ## Build video service
	@cd services/video && go build -o ../../bin/video ./cmd/server

build-homework: ## Build homework service
	@cd services/homework && go build -o ../../bin/homework ./cmd/server

# Test targets
test: test-go test-frontend ## Run all tests

test-go: ## Run Go tests for all services
	@echo "$(BLUE)Running Go tests...$(NC)"
	@cd services/api-gateway && go test ./... -v
	@cd services/auth && go test ./... -v
	@cd services/video && go test ./... -v
	@cd services/homework && go test ./... -v
	@cd services/analytics && go test ./... -v
	@cd services/collaboration && go test ./... -v
	@cd services/pdf && go test ./... -v
	@cd shared && go test ./... -v
	@echo "$(GREEN)✓ Go tests passed$(NC)"

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(NC)"
	@cd frontend && npm test -- --run
	@echo "$(GREEN)✓ Frontend tests passed$(NC)"

# Linting targets
lint: lint-go lint-frontend ## Run linters for all code

lint-go: ## Run Go linter
	@echo "$(BLUE)Running Go linter...$(NC)"
	@golangci-lint run ./services/... ./shared/...
	@echo "$(GREEN)✓ Go linting passed$(NC)"

lint-frontend: ## Run frontend linter
	@echo "$(BLUE)Running frontend linter...$(NC)"
	@cd frontend && npm run lint
	@echo "$(GREEN)✓ Frontend linting passed$(NC)"

# Protocol Buffers
proto-gen: ## Generate code from Protocol Buffer definitions
	@echo "$(BLUE)Generating code from proto files...$(NC)"
ifeq ($(OS),Windows_NT)
	@powershell -ExecutionPolicy Bypass -File scripts/generate-proto.ps1
else
	@chmod +x scripts/generate-proto.sh
	@./scripts/generate-proto.sh
endif
	@echo "$(GREEN)✓ Proto code generated$(NC)"

proto-install: ## Install Protocol Buffer tools
	@echo "$(BLUE)Installing Protocol Buffer tools...$(NC)"
ifeq ($(OS),Windows_NT)
	@powershell -ExecutionPolicy Bypass -File scripts/install-proto-tools.ps1
else
	@chmod +x scripts/install-proto-tools.sh
	@./scripts/install-proto-tools.sh
endif
	@echo "$(GREEN)✓ Proto tools installed$(NC)"

# Development environment
minikube-setup: ## Complete Minikube setup with all configurations
	@echo "$(BLUE)Setting up Minikube environment...$(NC)"
ifeq ($(OS),Windows_NT)
	@powershell -ExecutionPolicy Bypass -File scripts/setup-minikube.ps1
else
	@chmod +x scripts/setup-minikube.sh
	@./scripts/setup-minikube.sh
endif
	@echo "$(GREEN)✓ Minikube setup complete$(NC)"

minikube-start: ## Start Minikube cluster
	@echo "$(BLUE)Starting Minikube...$(NC)"
	@minikube start --profile metlab-dev --cpus=4 --memory=8192 --driver=docker
	@minikube addons enable ingress -p metlab-dev
	@minikube addons enable metrics-server -p metlab-dev
	@echo "$(GREEN)✓ Minikube started$(NC)"

minikube-stop: ## Stop Minikube cluster
	@echo "$(BLUE)Stopping Minikube...$(NC)"
	@minikube stop -p metlab-dev
	@echo "$(GREEN)✓ Minikube stopped$(NC)"

minikube-delete: ## Delete Minikube cluster
	@echo "$(YELLOW)Deleting Minikube cluster...$(NC)"
	@minikube delete -p metlab-dev
	@echo "$(GREEN)✓ Minikube deleted$(NC)"

minikube-status: ## Show Minikube cluster status
	@echo "$(BLUE)Minikube Status:$(NC)"
	@minikube status -p metlab-dev

minikube-dashboard: ## Open Kubernetes dashboard
	@echo "$(BLUE)Opening Kubernetes dashboard...$(NC)"
	@minikube dashboard -p metlab-dev

minikube-ip: ## Get Minikube cluster IP
	@minikube ip -p metlab-dev

dev: ## Start development environment with Tilt
	@echo "$(BLUE)Starting development environment...$(NC)"
	@tilt up

dev-down: ## Stop development environment
	@echo "$(BLUE)Stopping development environment...$(NC)"
	@tilt down

# Database migrations
migrate-up: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	@./scripts/migrate.sh up
	@echo "$(GREEN)✓ Migrations applied$(NC)"

migrate-down: ## Rollback database migrations
	@echo "$(YELLOW)Rolling back database migrations...$(NC)"
	@./scripts/migrate.sh down
	@echo "$(GREEN)✓ Migrations rolled back$(NC)"

migrate-create: ## Create new migration (usage: make migrate-create NAME=migration_name)
	@./scripts/migrate.sh create $(NAME)

# Docker targets
docker-build: ## Build all Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	@docker build -t metlab/api-gateway:latest -f infrastructure/docker/api-gateway.Dockerfile .
	@docker build -t metlab/auth:latest -f infrastructure/docker/auth.Dockerfile .
	@docker build -t metlab/video:latest -f infrastructure/docker/video.Dockerfile .
	@docker build -t metlab/homework:latest -f infrastructure/docker/homework.Dockerfile .
	@docker build -t metlab/analytics:latest -f infrastructure/docker/analytics.Dockerfile .
	@docker build -t metlab/collaboration:latest -f infrastructure/docker/collaboration.Dockerfile .
	@docker build -t metlab/pdf:latest -f infrastructure/docker/pdf.Dockerfile .
	@docker build -t metlab/frontend:latest -f infrastructure/docker/frontend.Dockerfile .
	@echo "$(GREEN)✓ Docker images built$(NC)"

# Kubernetes targets
k8s-apply: ## Apply Kubernetes manifests
	@echo "$(BLUE)Applying Kubernetes manifests...$(NC)"
	@kubectl apply -f infrastructure/k8s/
	@echo "$(GREEN)✓ Kubernetes manifests applied$(NC)"

k8s-delete: ## Delete Kubernetes resources
	@echo "$(YELLOW)Deleting Kubernetes resources...$(NC)"
	@kubectl delete -f infrastructure/k8s/
	@echo "$(GREEN)✓ Kubernetes resources deleted$(NC)"

# Cleanup
clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@rm -rf bin/
	@rm -rf frontend/dist/
	@rm -rf frontend/.vinxi/
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-all: clean ## Clean everything including dependencies
	@echo "$(BLUE)Cleaning all dependencies...$(NC)"
	@rm -rf frontend/node_modules/
	@find services -name "vendor" -type d -exec rm -rf {} +
	@echo "$(GREEN)✓ All cleaned$(NC)"

# Utility targets
logs: ## Show logs from all services (requires kubectl)
	@kubectl logs -f -l app=metlab --all-containers=true

status: ## Show status of all services
	@echo "$(BLUE)Service Status:$(NC)"
	@kubectl get pods -l app=metlab

port-forward-api: ## Port forward API Gateway to localhost:8080
	@kubectl port-forward svc/api-gateway 8080:8080

port-forward-frontend: ## Port forward Frontend to localhost:3000
	@kubectl port-forward svc/frontend 3000:3000
