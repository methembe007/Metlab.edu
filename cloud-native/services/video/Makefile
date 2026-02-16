.PHONY: build test clean run proto build-worker docker-build-worker

# Build the service
build:
	go build -o bin/video-service cmd/server/main.go

# Build the worker
build-worker:
	go build -o bin/video-worker cmd/worker/main.go

# Build both service and worker
build-all: build build-worker

# Run tests
test:
	go test -v ./...

# Run tests with coverage
test-coverage:
	go test -cover -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

# Clean build artifacts
clean:
	rm -rf bin/
	rm -f coverage.out coverage.html

# Run the service locally
run:
	go run cmd/server/main.go

# Run the worker locally
run-worker:
	go run cmd/worker/main.go

# Download dependencies
deps:
	go mod download
	go mod tidy

# Format code
fmt:
	go fmt ./...

# Lint code
lint:
	golangci-lint run

# Build Docker image for service
docker-build:
	docker build -t metlab/video-service:latest .

# Build Docker image for worker
docker-build-worker:
	docker build -f Dockerfile.worker -t metlab/video-worker:latest .

# Build both Docker images
docker-build-all: docker-build docker-build-worker

# Run Docker container for service
docker-run:
	docker run -p 50052:50052 --env-file .env metlab/video-service:latest

# Run Docker container for worker
docker-run-worker:
	docker run --env-file .env metlab/video-worker:latest
