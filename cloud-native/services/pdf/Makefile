.PHONY: build run test clean proto docker-build docker-run

# Build the service
build:
	go build -o pdf-service ./cmd/server

# Run the service locally
run:
	go run ./cmd/server/main.go

# Run tests
test:
	go test -v ./...

# Clean build artifacts
clean:
	rm -f pdf-service
	rm -f pdf-service.exe

# Generate proto files (if needed)
proto:
	cd ../../proto && ./generate.sh

# Build Docker image
docker-build:
	docker build -t metlab/pdf-service:latest .

# Run Docker container
docker-run:
	docker run -p 50056:50056 \
		-e DATABASE_HOST=host.docker.internal \
		-e S3_ENDPOINT=host.docker.internal:9000 \
		metlab/pdf-service:latest

# Run with hot reload (requires air)
dev:
	air

# Format code
fmt:
	go fmt ./...

# Lint code
lint:
	golangci-lint run

# Tidy dependencies
tidy:
	go mod tidy
