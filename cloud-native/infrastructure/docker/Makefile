.PHONY: help build build-no-cache up down logs clean restart ps health

# Default target
help:
	@echo "Metlab Docker Commands"
	@echo "======================"
	@echo "make build          - Build all Docker images"
	@echo "make build-no-cache - Build all images without cache"
	@echo "make up             - Start all services"
	@echo "make down           - Stop all services"
	@echo "make restart        - Restart all services"
	@echo "make logs           - View logs from all services"
	@echo "make ps             - Show running containers"
	@echo "make health         - Check health status of all services"
	@echo "make clean          - Stop services and remove volumes"
	@echo "make clean-all      - Remove all containers, volumes, and images"
	@echo ""
	@echo "Service-specific commands:"
	@echo "make build-auth     - Build auth service"
	@echo "make logs-auth      - View auth service logs"
	@echo "make restart-auth   - Restart auth service"

# Build all images
build:
	cd ../.. && docker-compose build

# Build without cache
build-no-cache:
	cd ../.. && docker-compose build --no-cache

# Start all services
up:
	cd ../.. && docker-compose up -d

# Stop all services
down:
	cd ../.. && docker-compose down

# Restart all services
restart: down up

# View logs
logs:
	cd ../.. && docker-compose logs -f

# Show running containers
ps:
	cd ../.. && docker-compose ps

# Check health status
health:
	@echo "Checking service health..."
	@cd ../.. && docker-compose ps --format json | jq -r '.[] | "\(.Service): \(.Health)"'

# Stop and remove volumes
clean:
	cd ../.. && docker-compose down -v

# Remove everything
clean-all:
	cd ../.. && docker-compose down -v --rmi all

# Service-specific targets
build-auth:
	cd ../.. && docker-compose build auth-service

build-api-gateway:
	cd ../.. && docker-compose build api-gateway

build-video:
	cd ../.. && docker-compose build video-service

build-homework:
	cd ../.. && docker-compose build homework-service

build-analytics:
	cd ../.. && docker-compose build analytics-service

build-collaboration:
	cd ../.. && docker-compose build collaboration-service

build-pdf:
	cd ../.. && docker-compose build pdf-service

build-frontend:
	cd ../.. && docker-compose build frontend

# Service logs
logs-auth:
	cd ../.. && docker-compose logs -f auth-service

logs-api-gateway:
	cd ../.. && docker-compose logs -f api-gateway

logs-video:
	cd ../.. && docker-compose logs -f video-service

logs-frontend:
	cd ../.. && docker-compose logs -f frontend

# Service restart
restart-auth:
	cd ../.. && docker-compose restart auth-service

restart-api-gateway:
	cd ../.. && docker-compose restart api-gateway

restart-video:
	cd ../.. && docker-compose restart video-service

restart-frontend:
	cd ../.. && docker-compose restart frontend

# Infrastructure services
up-infra:
	cd ../.. && docker-compose up -d postgres redis minio

logs-postgres:
	cd ../.. && docker-compose logs -f postgres

logs-redis:
	cd ../.. && docker-compose logs -f redis

logs-minio:
	cd ../.. && docker-compose logs -f minio
