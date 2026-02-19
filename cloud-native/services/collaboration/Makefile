.PHONY: build run test clean docker-build docker-run migrate-up migrate-down

# Build the application
build:
	go build -o collaboration ./cmd/server

# Run the application
run:
	go run ./cmd/server/main.go

# Run tests
test:
	go test -v ./...

# Clean build artifacts
clean:
	rm -f collaboration
	go clean

# Build Docker image
docker-build:
	docker build -t metlab/collaboration:latest .

# Run Docker container
docker-run:
	docker run -p 50055:50055 --env-file .env metlab/collaboration:latest

# Install golang-migrate if not already installed
install-migrate:
	@which migrate > /dev/null || (echo "Installing golang-migrate..." && \
		go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest)

# Run database migrations up
migrate-up: install-migrate
	@echo "Running migrations..."
	@migrate -path migrations -database "${DATABASE_URL}" up

# Run database migrations down
migrate-down: install-migrate
	@echo "Rolling back migrations..."
	@migrate -path migrations -database "${DATABASE_URL}" down

# Create a new migration
migrate-create: install-migrate
	@read -p "Enter migration name: " name; \
	migrate create -ext sql -dir migrations -seq $$name

# Format code
fmt:
	go fmt ./...

# Run linter
lint:
	golangci-lint run

# Download dependencies
deps:
	go mod download
	go mod tidy

# Generate proto files (run from project root)
proto:
	cd ../../proto && make generate
