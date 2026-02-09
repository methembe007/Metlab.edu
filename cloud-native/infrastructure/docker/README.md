# Docker Configuration

This directory contains Docker configurations for the Metlab cloud-native architecture.

## Dockerfiles

All Dockerfiles use multi-stage builds for optimal image size and security:

### Go Services
- `auth.Dockerfile` - Authentication service
- `api-gateway.Dockerfile` - API Gateway service
- `video.Dockerfile` - Video processing service (includes FFmpeg)
- `homework.Dockerfile` - Homework management service
- `analytics.Dockerfile` - Analytics service
- `collaboration.Dockerfile` - Study groups and chat service
- `pdf.Dockerfile` - PDF management service

**Features:**
- Multi-stage builds (builder + runtime)
- Minimal runtime images (scratch or alpine)
- Non-root user execution
- Health checks included
- Optimized layer caching
- Build-time dependency verification

### Frontend
- `frontend.Dockerfile` - TanStack Start application

**Features:**
- Multi-stage build with Node.js
- Production dependency pruning
- Non-root user execution
- Dumb-init for proper signal handling
- Health check endpoint

## Building Images

### Build all services
```bash
# From cloud-native directory
docker-compose build
```

### Build specific service
```bash
docker-compose build auth-service
docker-compose build frontend
```

### Build with no cache
```bash
docker-compose build --no-cache
```

## Running Services

### Start all services
```bash
docker-compose up -d
```

### Start specific services
```bash
docker-compose up -d postgres redis minio
docker-compose up -d auth-service api-gateway
```

### View logs
```bash
docker-compose logs -f
docker-compose logs -f auth-service
```

### Stop services
```bash
docker-compose down
```

### Stop and remove volumes
```bash
docker-compose down -v
```

## Development Mode

For development with hot-reload:

1. Copy the override file:
```bash
cp docker-compose.override.yml.example docker-compose.override.yml
```

2. Start services:
```bash
docker-compose up -d
```

The override file enables:
- Hot-reload for Go services (using Air)
- Hot-reload for frontend (Vite dev server)
- pgAdmin for database management (http://localhost:5050)
- Redis Commander for Redis management (http://localhost:8081)

## Image Optimization

### Size Comparison
- Go services: ~10-15 MB (using scratch base)
- Video service: ~50 MB (includes FFmpeg)
- Frontend: ~150 MB (Node.js runtime)

### Optimization Techniques
1. **Multi-stage builds** - Separate build and runtime stages
2. **Minimal base images** - Use scratch for Go, alpine for Node
3. **Layer caching** - Copy dependencies before source code
4. **Build flags** - Strip debug symbols with `-ldflags='-w -s'`
5. **.dockerignore** - Exclude unnecessary files from build context

## Security Features

1. **Non-root users** - All services run as non-root
2. **Minimal attack surface** - Scratch images have no shell or utilities
3. **Health checks** - Built-in health monitoring
4. **No secrets in images** - Environment variables for configuration
5. **Dependency verification** - `go mod verify` during build

## Troubleshooting

### Service won't start
```bash
# Check logs
docker-compose logs service-name

# Check health status
docker-compose ps
```

### Database connection issues
```bash
# Verify postgres is healthy
docker-compose ps postgres

# Check database logs
docker-compose logs postgres
```

### Build failures
```bash
# Clean build with no cache
docker-compose build --no-cache service-name

# Check disk space
docker system df
```

### Image size issues
```bash
# View image sizes
docker images | grep metlab

# Clean up unused images
docker image prune -a
```

## Production Considerations

For production deployments:

1. Use specific image tags (not `latest`)
2. Store images in a container registry
3. Use secrets management (not environment variables)
4. Enable resource limits in Kubernetes
5. Implement proper logging and monitoring
6. Use read-only root filesystems where possible
7. Scan images for vulnerabilities (Trivy, Snyk)

## Database Initialization

The `init-db.sql` script runs when PostgreSQL starts for the first time:
- Enables UUID extension
- Creates health check function
- Can be extended with seed data

## MinIO Setup

MinIO provides S3-compatible storage for development:
- Console: http://localhost:9001
- API: http://localhost:9000
- Default credentials: minioadmin/minioadmin

Create buckets for:
- `metlab-videos` - Video files
- `metlab-pdfs` - PDF documents
- `metlab-homework` - Homework submissions

## Network Configuration

All services communicate via the `metlab-network` bridge network:
- Services can reference each other by service name
- External access via published ports
- Isolated from other Docker networks

## Volume Management

Persistent data stored in named volumes:
- `postgres_data` - Database files
- `redis_data` - Redis persistence
- `minio_data` - Object storage
- `video_temp` - Temporary video processing files

## Health Checks

All services include health checks:
- Interval: 30 seconds
- Timeout: 3 seconds
- Retries: 3
- Start period: 5-10 seconds

Health check endpoints:
- Go services: Built-in `-health-check` flag
- Frontend: HTTP GET to `/api/health`
- PostgreSQL: `pg_isready`
- Redis: `redis-cli ping`
- MinIO: HTTP GET to `/minio/health/live`
