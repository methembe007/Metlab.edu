# Docker Quick Start Guide

This guide helps you get the Metlab cloud-native architecture running locally using Docker Compose.

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+
- At least 8GB RAM allocated to Docker
- At least 20GB free disk space

## Quick Start

### 1. Navigate to the cloud-native directory
```bash
cd cloud-native
```

### 2. Start all services
```bash
docker-compose up -d
```

This will:
- Pull required base images
- Build all service images
- Start PostgreSQL, Redis, and MinIO
- Start all microservices
- Start the frontend application

### 3. Wait for services to be healthy
```bash
docker-compose ps
```

All services should show "healthy" status after 30-60 seconds.

### 4. Access the application

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8080
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## Development Mode

For hot-reload during development:

### 1. Copy the override file
```bash
cp docker-compose.override.yml.example docker-compose.override.yml
```

### 2. Start services
```bash
docker-compose up -d
```

### 3. Access development tools

- **pgAdmin**: http://localhost:5050 (admin@metlab.local/admin)
- **Redis Commander**: http://localhost:8081

## Common Commands

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f auth-service
docker-compose logs -f frontend
```

### Restart a service
```bash
docker-compose restart auth-service
```

### Rebuild a service
```bash
docker-compose build auth-service
docker-compose up -d auth-service
```

### Stop all services
```bash
docker-compose down
```

### Stop and remove volumes (clean slate)
```bash
docker-compose down -v
```

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Web application |
| API Gateway | 8080 | HTTP API |
| Auth Service | 50051 | gRPC |
| Video Service | 50052 | gRPC |
| Homework Service | 50053 | gRPC |
| Analytics Service | 50054 | gRPC |
| Collaboration Service | 50055 | gRPC |
| PDF Service | 50056 | gRPC |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache/Pub-Sub |
| MinIO API | 9000 | Object Storage |
| MinIO Console | 9001 | Web UI |
| pgAdmin | 5050 | Database UI (dev) |
| Redis Commander | 8081 | Redis UI (dev) |

## Initial Setup

### Create MinIO Buckets

1. Open MinIO Console: http://localhost:9001
2. Login with minioadmin/minioadmin
3. Create buckets:
   - `metlab-videos`
   - `metlab-pdfs`
   - `metlab-homework`

Or use the MinIO CLI:
```bash
docker exec metlab-minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker exec metlab-minio mc mb local/metlab-videos
docker exec metlab-minio mc mb local/metlab-pdfs
docker exec metlab-minio mc mb local/metlab-homework
```

### Run Database Migrations

```bash
# Once migration tools are implemented
docker-compose exec auth-service ./auth -migrate
```

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Check Docker resources
docker system df

# Restart Docker Desktop
```

### Port conflicts
If ports are already in use, edit `docker-compose.yml` to change port mappings:
```yaml
ports:
  - "3001:3000"  # Change 3000 to 3001
```

### Database connection errors
```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Out of disk space
```bash
# Remove unused images and containers
docker system prune -a

# Remove unused volumes
docker volume prune
```

### Build failures
```bash
# Clean build
docker-compose build --no-cache service-name

# Check Docker logs
docker-compose logs service-name
```

## Performance Tips

### Allocate more resources to Docker
- **RAM**: At least 8GB recommended
- **CPU**: At least 4 cores recommended
- **Disk**: Use SSD for better performance

### Enable BuildKit
Add to your environment or Docker config:
```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

### Use volume mounts carefully
In development mode, avoid mounting large directories like `node_modules`.

## Next Steps

1. **Run tests**: See testing documentation
2. **Deploy to Kubernetes**: See Kubernetes setup guide
3. **Configure Tilt**: For faster development iteration
4. **Set up CI/CD**: See deployment documentation

## Getting Help

- Check service logs: `docker-compose logs service-name`
- View service status: `docker-compose ps`
- Inspect service: `docker-compose exec service-name sh`
- Read full documentation: `infrastructure/docker/README.md`

## Stopping Development

### Keep data
```bash
docker-compose down
```

### Remove all data (fresh start)
```bash
docker-compose down -v
```

### Remove images too
```bash
docker-compose down -v --rmi all
```
