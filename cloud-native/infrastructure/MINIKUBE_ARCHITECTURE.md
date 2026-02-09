# Minikube Local Development Architecture

This document provides a visual overview of the Minikube-based local development environment for Metlab.edu.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Developer Machine                         │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Docker Desktop                           │ │
│  │                                                              │ │
│  │  ┌────────────────────────────────────────────────────────┐│ │
│  │  │              Minikube Cluster (metlab-dev)             ││ │
│  │  │                                                          ││ │
│  │  │  ┌──────────────────────────────────────────────────┐  ││ │
│  │  │  │           Kubernetes Control Plane               │  ││ │
│  │  │  │  • API Server                                    │  ││ │
│  │  │  │  • Scheduler                                     │  ││ │
│  │  │  │  • Controller Manager                            │  ││ │
│  │  │  │  • etcd                                          │  ││ │
│  │  │  └──────────────────────────────────────────────────┘  ││ │
│  │  │                                                          ││ │
│  │  │  ┌──────────────────────────────────────────────────┐  ││ │
│  │  │  │              Namespaces                          │  ││ │
│  │  │  │                                                    │  ││ │
│  │  │  │  ┌─────────────────────────────────────────────┐ │  ││ │
│  │  │  │  │  metlab-dev (Development)                   │ │  ││ │
│  │  │  │  │  • Frontend Service                         │ │  ││ │
│  │  │  │  │  • API Gateway Service                      │ │  ││ │
│  │  │  │  │  • Auth Service                             │ │  ││ │
│  │  │  │  │  • Video Service                            │ │  ││ │
│  │  │  │  │  • Homework Service                         │ │  ││ │
│  │  │  │  │  • Analytics Service                        │ │  ││ │
│  │  │  │  │  • Collaboration Service                    │ │  ││ │
│  │  │  │  │  • PDF Service                              │ │  ││ │
│  │  │  │  │  • PostgreSQL StatefulSet                   │ │  ││ │
│  │  │  │  │  • Redis Deployment                         │ │  ││ │
│  │  │  │  └─────────────────────────────────────────────┘ │  ││ │
│  │  │  │                                                    │  ││ │
│  │  │  │  ┌─────────────────────────────────────────────┐ │  ││ │
│  │  │  │  │  metlab-staging (Future)                    │ │  ││ │
│  │  │  │  └─────────────────────────────────────────────┘ │  ││ │
│  │  │  │                                                    │  ││ │
│  │  │  │  ┌─────────────────────────────────────────────┐ │  ││ │
│  │  │  │  │  metlab-production (Future)                 │ │  ││ │
│  │  │  │  └─────────────────────────────────────────────┘ │  ││ │
│  │  │  └──────────────────────────────────────────────────┘  ││ │
│  │  │                                                          ││ │
│  │  │  ┌──────────────────────────────────────────────────┐  ││ │
│  │  │  │              Enabled Addons                      │  ││ │
│  │  │  │  • Ingress Controller (nginx)                   │  ││ │
│  │  │  │  • Metrics Server                               │  ││ │
│  │  │  │  • Kubernetes Dashboard                         │  ││ │
│  │  │  │  • Storage Provisioner                          │  ││ │
│  │  │  │  • Default StorageClass                         │  ││ │
│  │  │  └──────────────────────────────────────────────────┘  ││ │
│  │  └────────────────────────────────────────────────────────┘│ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Development Tools                        │ │
│  │  • kubectl (Kubernetes CLI)                                │ │
│  │  • Tilt (Development orchestration)                        │ │
│  │  • Docker CLI                                              │ │
│  │  • Minikube CLI                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### Minikube Cluster Configuration

| Component | Configuration |
|-----------|---------------|
| **Profile Name** | `metlab-dev` |
| **CPUs** | 4 cores |
| **Memory** | 8192 MB (8 GB) |
| **Driver** | Docker |
| **Kubernetes Version** | Stable (latest) |

### Namespaces

#### metlab-dev (Active)
- **Purpose**: Local development and testing
- **Services**: All microservices, database, cache
- **Access**: Default namespace for development

#### metlab-staging (Reserved)
- **Purpose**: Pre-production testing
- **Status**: Created but not actively used
- **Future Use**: Staging environment testing

#### metlab-production (Reserved)
- **Purpose**: Production deployment reference
- **Status**: Created but not actively used
- **Future Use**: Production deployment (cloud)

### Enabled Addons

#### Ingress Controller
- **Type**: nginx
- **Purpose**: Routes external HTTP/HTTPS traffic to services
- **Ports**: 80 (HTTP), 443 (HTTPS)

#### Metrics Server
- **Purpose**: Collects resource metrics (CPU, memory)
- **Used By**: Horizontal Pod Autoscaler (HPA)
- **Commands**: `kubectl top nodes`, `kubectl top pods`

#### Kubernetes Dashboard
- **Purpose**: Web-based UI for cluster management
- **Access**: `minikube dashboard -p metlab-dev`
- **Features**: View resources, logs, events

#### Storage Provisioner
- **Purpose**: Dynamic provisioning of persistent volumes
- **Type**: hostPath (local development)
- **Used By**: PostgreSQL StatefulSet

#### Default StorageClass
- **Purpose**: Automatic PVC provisioning
- **Type**: standard (hostPath)

## Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    External Access                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Ingress Controller                          │
│                    (nginx)                                   │
│  • Routes: /api/* → API Gateway                             │
│  • Routes: /* → Frontend                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│   Frontend Service        │   │   API Gateway Service     │
│   (TanStack Start)        │   │   (Go)                    │
│   Port: 3000              │   │   Port: 8080              │
└───────────────────────────┘   └───────────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
        ┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
        │  Auth Service     │   │  Video Service    │   │  Homework Service │
        │  (gRPC)           │   │  (gRPC)           │   │  (gRPC)           │
        │  Port: 50051      │   │  Port: 50052      │   │  Port: 50053      │
        └───────────────────┘   └───────────────────┘   └───────────────────┘
                    │                       │                       │
                    └───────────────────────┼───────────────────────┘
                                            ▼
                            ┌───────────────────────────┐
                            │   PostgreSQL              │
                            │   (StatefulSet)           │
                            │   Port: 5432              │
                            └───────────────────────────┘
```

## Storage Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Persistent Storage                        │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  PostgreSQL Data                                       │ │
│  │  • PersistentVolumeClaim: postgres-pvc                │ │
│  │  • Size: 10Gi                                         │ │
│  │  • StorageClass: standard                             │ │
│  │  • Access Mode: ReadWriteOnce                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Object Storage (MinIO - Future)                      │ │
│  │  • Videos, PDFs, Images                               │ │
│  │  • S3-compatible API                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Development Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    Developer Workflow                        │
│                                                               │
│  1. Code Change                                              │
│     └─> Edit source files                                   │
│                                                               │
│  2. Tilt Detects Change                                      │
│     └─> Watches file system                                 │
│                                                               │
│  3. Build & Deploy                                           │
│     ├─> Build Docker image                                  │
│     ├─> Push to Minikube registry                           │
│     └─> Update Kubernetes deployment                        │
│                                                               │
│  4. Live Reload                                              │
│     └─> Service restarts with new code                      │
│                                                               │
│  5. Test & Verify                                            │
│     ├─> Access via localhost                                │
│     ├─> View logs in Tilt UI                                │
│     └─> Debug if needed                                     │
└─────────────────────────────────────────────────────────────┘
```

## Access Points

### Services

| Service | Local Access | Port Forward Command |
|---------|--------------|----------------------|
| Frontend | http://localhost:3000 | `kubectl port-forward svc/frontend 3000:3000` |
| API Gateway | http://localhost:8080 | `kubectl port-forward svc/api-gateway 8080:8080` |
| PostgreSQL | localhost:5432 | `kubectl port-forward svc/postgres 5432:5432` |
| Redis | localhost:6379 | `kubectl port-forward svc/redis 6379:6379` |

### Management Tools

| Tool | Access Command |
|------|----------------|
| Kubernetes Dashboard | `minikube dashboard -p metlab-dev` |
| Tilt UI | `tilt up` (opens browser automatically) |
| Minikube SSH | `minikube ssh -p metlab-dev` |

## Resource Allocation

### Default Pod Resources

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---------|-------------|-----------|----------------|--------------|
| Frontend | 200m | 500m | 256Mi | 512Mi |
| API Gateway | 500m | 1000m | 512Mi | 1Gi |
| Auth Service | 200m | 500m | 256Mi | 512Mi |
| Video Service | 500m | 1000m | 512Mi | 1Gi |
| Homework Service | 200m | 500m | 256Mi | 512Mi |
| Analytics Service | 200m | 500m | 256Mi | 512Mi |
| Collaboration Service | 200m | 500m | 256Mi | 512Mi |
| PDF Service | 200m | 500m | 256Mi | 512Mi |
| PostgreSQL | 1000m | 2000m | 2Gi | 4Gi |
| Redis | 200m | 500m | 256Mi | 512Mi |

### Cluster Capacity

- **Total CPU**: 4 cores
- **Total Memory**: 8192 MB
- **Available for Pods**: ~3.5 cores, ~6 GB (after system overhead)

## Monitoring and Observability

### Metrics Collection

```
┌─────────────────────────────────────────────────────────────┐
│                    Metrics Server                            │
│  • Collects CPU and memory metrics                          │
│  • Updates every 15 seconds                                 │
│  • Used by HPA for autoscaling                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    kubectl top                               │
│  • View node metrics: kubectl top nodes                     │
│  • View pod metrics: kubectl top pods                       │
└─────────────────────────────────────────────────────────────┘
```

### Logging

```
┌─────────────────────────────────────────────────────────────┐
│                    Container Logs                            │
│  • Stdout/stderr from containers                            │
│  • Accessible via kubectl logs                              │
│  • Aggregated in Tilt UI                                    │
└─────────────────────────────────────────────────────────────┘
```

## Advantages of This Setup

1. **Isolated Environment**: Separate from production, safe for experimentation
2. **Fast Iteration**: Tilt provides hot reload for rapid development
3. **Production-Like**: Mimics production Kubernetes environment
4. **Resource Efficient**: Runs on a single machine with reasonable resources
5. **Easy Reset**: Can delete and recreate cluster quickly
6. **Multi-Service**: All microservices run simultaneously
7. **Networking**: Services communicate via Kubernetes DNS
8. **Storage**: Persistent volumes for stateful services
9. **Monitoring**: Built-in metrics and dashboard
10. **Debugging**: Easy access to logs and shell access to pods

## Limitations

1. **Single Node**: No multi-node features (node affinity, etc.)
2. **Resource Constraints**: Limited by host machine resources
3. **Storage**: Uses hostPath, not production-grade storage
4. **Networking**: Simplified networking compared to cloud
5. **Load Balancing**: Single ingress controller, no real load balancing
6. **High Availability**: No HA features (single replica for most services)

## Next Steps

After setting up Minikube, proceed with:

1. **Task 4**: Create base Docker images and configurations
2. **Task 5**: Set up PostgreSQL database infrastructure
3. **Task 6**: Set up Redis for caching and pub/sub
4. **Deploy Services**: Apply Kubernetes manifests
5. **Start Development**: Use Tilt for hot-reload development

---

**Last Updated**: 2026-02-09
**Minikube Version**: 1.30+
**Kubernetes Version**: 1.27+
