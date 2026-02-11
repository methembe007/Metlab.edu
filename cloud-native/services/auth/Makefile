.PHONY: help build run test clean migrate-up migrate-down docker-build docker-run

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build the service
	go build -o bin/auth-service ./cmd/server

run: ## Run the service locally
	go run ./cmd/server/main.go

test: ## Run tests
	go test -v -race -coverprofile=coverage.out ./...

test-coverage: test ## Run tests and show coverage
	go tool cover -html=coverage.out

clean: ## Clean build artifacts
	rm -rf bin/
	rm -f coverage.out

deps: ## Download dependencies
	go mod download
	go mod tidy

migrate-up: ## Run database migrations up
	migrate -path migrations -database "postgres://postgres:postgres@localhost:5432/metlab?sslmode=disable" up

migrate-down: ## Run database migrations down
	migrate -path migrations -database "postgres://postgres:postgres@localhost:5432/metlab?sslmode=disable" down

migrate-create: ## Create a new migration (usage: make migrate-create NAME=migration_name)
	migrate create -ext sql -dir migrations -seq $(NAME)

docker-build: ## Build Docker image
	docker build -t metlab/auth:latest .

docker-run: ## Run Docker container
	docker run -p 50051:50051 \
		-e DATABASE_HOST=host.docker.internal \
		-e DATABASE_PASSWORD=postgres \
		-e JWT_SECRET=dev-secret \
		metlab/auth:latest

lint: ## Run linter
	golangci-lint run

fmt: ## Format code
	go fmt ./...

vet: ## Run go vet
	go vet ./...

proto-gen: ## Generate code from proto files
	protoc --go_out=. --go_opt=paths=source_relative \
		--go-grpc_out=. --go-grpc_opt=paths=source_relative \
		../../proto/auth/auth.proto
