.PHONY: build run test clean docker-build docker-run migrate-up migrate-down

# Build the application
build:
	go build -o bin/analytics-service ./cmd/server

# Run the application
run:
	go run ./cmd/server/main.go

# Run tests
test:
	go test -v ./...

# Clean build artifacts
clean:
	rm -rf bin/

# Build Docker image
docker-build:
	docker build -t metlab/analytics-service:latest .

# Run Docker container
docker-run:
	docker run -p 50054:50054 --env-file .env metlab/analytics-service:latest

# Run database migrations up
migrate-up:
	migrate -path migrations -database "${DATABASE_URL}" up

# Run database migrations down
migrate-down:
	migrate -path migrations -database "${DATABASE_URL}" down

# Install dependencies
deps:
	go mod download
	go mod tidy

# Format code
fmt:
	go fmt ./...

# Lint code
lint:
	golangci-lint run

# Generate proto files (when proto is ready)
proto:
	@echo "Proto generation will be handled by the root-level proto generation script"
