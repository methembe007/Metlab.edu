.PHONY: help build run test clean proto docker-build docker-run

# Variables
SERVICE_NAME=homework-service
DOCKER_IMAGE=metlab/$(SERVICE_NAME)
PORT=50053

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build the service
	@echo "Building $(SERVICE_NAME)..."
	go build -o bin/$(SERVICE_NAME) ./cmd/server

run: ## Run the service locally
	@echo "Running $(SERVICE_NAME)..."
	go run ./cmd/server/main.go

test: ## Run tests
	@echo "Running tests..."
	go test -v -cover ./...

clean: ## Clean build artifacts
	@echo "Cleaning..."
	rm -rf bin/
	go clean

proto: ## Generate protobuf code
	@echo "Generating protobuf code..."
	cd ../../proto && make generate

docker-build: ## Build Docker image
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE):latest .

docker-run: ## Run Docker container
	@echo "Running Docker container..."
	docker run -p $(PORT):$(PORT) --env-file .env $(DOCKER_IMAGE):latest

deps: ## Download dependencies
	@echo "Downloading dependencies..."
	go mod download
	go mod tidy

migrate-up: ## Run database migrations up
	@echo "Running migrations up..."
	migrate -path ./migrations -database "$(DATABASE_URL)" up

migrate-down: ## Run database migrations down
	@echo "Running migrations down..."
	migrate -path ./migrations -database "$(DATABASE_URL)" down

migrate-create: ## Create a new migration (usage: make migrate-create NAME=migration_name)
	@echo "Creating migration $(NAME)..."
	migrate create -ext sql -dir ./migrations -seq $(NAME)

lint: ## Run linter
	@echo "Running linter..."
	golangci-lint run

fmt: ## Format code
	@echo "Formatting code..."
	go fmt ./...
	goimports -w .

dev: ## Run in development mode with hot reload
	@echo "Running in development mode..."
	air
