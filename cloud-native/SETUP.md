# Cloud-Native Setup Guide

This guide will help you set up the Metlab.edu cloud-native development environment.

## Prerequisites

Before you begin, ensure you have the following installed:

### Required Tools

1. **Go 1.21+**
   ```bash
   go version
   ```

2. **Node.js 20+**
   ```bash
   node --version
   npm --version
   ```

3. **Docker**
   ```bash
   docker --version
   ```

4. **Minikube**
   ```bash
   minikube version
   ```

5. **kubectl**
   ```bash
   kubectl version --client
   ```

6. **Tilt**
   ```bash
   tilt version
   ```

7. **Protocol Buffers Compiler (protoc)**
   ```bash
   protoc --version
   ```

### Install Go Protocol Buffer Plugins

```bash
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
```

Add Go bin to your PATH if not already:
```bash
export PATH="$PATH:$(go env GOPATH)/bin"
```

## Setup Steps

### 1. Install Dependencies

```bash
cd cloud-native

# Install Go dependencies for all services
make install-go

# Install Node.js dependencies for frontend
make install-node
```

### 2. Start Minikube

```bash
make minikube-start
```

This will:
- Start Minikube with 4 CPUs and 8GB RAM
- Enable ingress addon
- Enable metrics-server addon

### 3. Generate Protocol Buffer Code

```bash
make proto-gen
```

This generates Go and TypeScript code from `.proto` files.

### 4. Start Development Environment

```bash
make dev
```

This will:
- Build all Docker images
- Deploy services to Kubernetes
- Start Tilt UI
- Enable hot reload for all services

The Tilt UI will open in your browser at http://localhost:10350

### 5. Access Services

Once all services are running (check Tilt UI):

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8080
- **Tilt Dashboard**: http://localhost:10350

## Development Workflow

### Making Changes

1. Edit code in any service
2. Tilt automatically detects changes
3. Service rebuilds and redeploys
4. Check Tilt UI for build status and logs

### Running Tests

```bash
# Run all tests
make test

# Run Go tests only
make test-go

# Run frontend tests only
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

### Viewing Logs

```bash
# View all service logs
make logs

# View specific service logs (in Tilt UI)
# Click on the service name in Tilt dashboard
```

### Stopping Development Environment

```bash
# Stop Tilt (Ctrl+C in terminal or)
make dev-down

# Stop Minikube
make minikube-stop
```

## Project Structure

```
cloud-native/
├── frontend/              # TanStack Start application
│   ├── app/              # Application code
│   │   ├── routes/       # Route components
│   │   ├── client.tsx    # Client entry point
│   │   └── ssr.tsx       # Server entry point
│   └── package.json
│
├── services/             # Go microservices
│   ├── api-gateway/      # HTTP to gRPC gateway
│   ├── auth/             # Authentication service
│   ├── video/            # Video management
│   ├── homework/         # Homework management
│   ├── analytics/        # Analytics service
│   ├── collaboration/    # Study groups & chat
│   └── pdf/              # PDF management
│
├── proto/                # Protocol Buffer definitions
│   ├── auth/
│   ├── video/
│   └── ...
│
├── shared/               # Shared Go packages
│   ├── db/              # Database utilities
│   ├── redis/           # Redis client
│   └── ...
│
├── infrastructure/       # Infrastructure configs
│   ├── k8s/             # Kubernetes manifests
│   ├── docker/          # Dockerfiles
│   └── migrations/      # Database migrations
│
├── Makefile             # Build commands
├── Tiltfile             # Tilt configuration
└── README.md
```

## Troubleshooting

### Minikube won't start

```bash
# Delete and recreate cluster
make minikube-delete
make minikube-start
```

### Service won't build

```bash
# Check Tilt logs in UI
# Rebuild manually
make build-<service-name>
```

### Port already in use

```bash
# Check what's using the port
lsof -i :8080  # or :3000, :50051, etc.

# Kill the process or change port in Kubernetes manifests
```

### Proto generation fails

```bash
# Ensure protoc plugins are installed
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# Ensure they're in PATH
export PATH="$PATH:$(go env GOPATH)/bin"
```

## Next Steps

1. Review the [Architecture Design](../.kiro/specs/cloud-native-architecture/design.md)
2. Check the [Implementation Tasks](../.kiro/specs/cloud-native-architecture/tasks.md)
3. Start implementing services following the task list

## Getting Help

- Check Tilt UI for service status and logs
- Review Kubernetes pod status: `kubectl get pods -n metlab-dev`
- View service logs: `kubectl logs -f <pod-name> -n metlab-dev`
- Run `make help` to see all available commands
