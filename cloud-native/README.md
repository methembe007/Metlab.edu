# Metlab.edu Cloud-Native Architecture

This is the cloud-native microservices implementation of Metlab.edu, migrating from Django monolith to a scalable, containerized architecture.

## Architecture Overview

- **Frontend**: TanStack Start (React SSR)
- **Backend**: Go microservices with gRPC
- **Database**: PostgreSQL
- **Cache**: Redis
- **Storage**: S3-compatible object storage
- **Orchestration**: Kubernetes
- **Development**: Minikube + Tilt

## Project Structure

```
cloud-native/
├── frontend/           # TanStack Start application
├── services/           # Go microservices
│   ├── api-gateway/    # HTTP to gRPC gateway
│   ├── auth/           # Authentication service
│   ├── video/          # Video management service
│   ├── homework/       # Homework service
│   ├── analytics/      # Analytics service
│   ├── collaboration/  # Study groups & chat
│   └── pdf/            # PDF management service
├── proto/              # Protocol Buffer definitions
├── infrastructure/     # Kubernetes manifests & configs
│   ├── k8s/            # Kubernetes YAML files
│   ├── docker/         # Dockerfiles
│   └── tilt/           # Tilt configuration
├── shared/             # Shared Go packages
└── scripts/            # Build and deployment scripts
```

## Prerequisites

- Go 1.21+
- Node.js 20+
- Docker
- Minikube
- Tilt
- kubectl
- protoc (Protocol Buffers compiler)

## Quick Start

### 1. Install Dependencies

Before starting, ensure you have the following installed:
- Go 1.21+
- Node.js 20+
- Docker
- Minikube
- kubectl
- Tilt (optional but recommended)
- protoc (Protocol Buffers compiler)

See [infrastructure/MINIKUBE_SETUP.md](infrastructure/MINIKUBE_SETUP.md) for detailed installation instructions.

### 2. Set Up Local Kubernetes Environment

Run the automated Minikube setup script:

**Linux/macOS:**
```bash
cd scripts
chmod +x setup-minikube.sh
./setup-minikube.sh
```

**Windows (PowerShell):**
```powershell
cd scripts
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\setup-minikube.ps1
```

Or use the Makefile:
```bash
make minikube-setup
```

This will:
- Create a Minikube cluster with 4 CPUs and 8GB RAM
- Enable required addons (ingress, metrics-server, dashboard)
- Configure kubectl context
- Create development, staging, and production namespaces

### 3. Install Project Dependencies

```bash
# Install Go dependencies
make install-go

# Install Node dependencies
make install-node

# Install Protocol Buffer tools
make proto-install
```

### 4. Start Local Development Environment

```bash
# Start all services with Tilt
make dev
```

This will:
- Build all Docker images
- Deploy services to Kubernetes
- Enable hot reload for code changes
- Open Tilt UI in browser

### 3. Access Services

- Frontend: http://localhost:3000
- API Gateway: http://localhost:8080
- Tilt UI: http://localhost:10350

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run Go tests
make test-go

# Run frontend tests
make test-frontend
```

### Building Services

```bash
# Build all services
make build

# Build specific service
make build-auth
make build-video
```

### Database Migrations

```bash
# Run migrations
make migrate-up

# Rollback migrations
make migrate-down
```

### Generate Protocol Buffers

```bash
# Generate Go and TypeScript code from proto files
make proto-gen
```

## Available Make Commands

Run `make help` to see all available commands.

## Documentation

- [Architecture Design](../.kiro/specs/cloud-native-architecture/design.md)
- [Requirements](../.kiro/specs/cloud-native-architecture/requirements.md)
- [Implementation Tasks](../.kiro/specs/cloud-native-architecture/tasks.md)

## Contributing

1. Create feature branch from `main`
2. Make changes and write tests
3. Run `make test` and `make lint`
4. Submit pull request

## License

Proprietary - Metlab.edu
