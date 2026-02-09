# Infrastructure

This directory contains infrastructure configuration for the Metlab.edu cloud-native platform.

## Structure

```
infrastructure/
├── k8s/            # Kubernetes manifests
├── docker/         # Dockerfiles for all services
├── tilt/           # Tilt configuration (see root Tiltfile)
└── migrations/     # Database migration files
```

## Getting Started

For detailed instructions on setting up your local Kubernetes development environment, see:

**[MINIKUBE_SETUP.md](MINIKUBE_SETUP.md)** - Complete guide for Minikube setup, configuration, and troubleshooting

Quick setup:
```bash
# Automated setup
make minikube-setup

# Or run the script directly
cd ../scripts
./setup-minikube.sh  # Linux/macOS
.\setup-minikube.ps1  # Windows
```

## Kubernetes Manifests

All Kubernetes manifests are in the `k8s/` directory:

- `namespace.yaml` - Development namespace
- `postgres.yaml` - PostgreSQL StatefulSet
- `redis.yaml` - Redis Deployment
- `api-gateway.yaml` - API Gateway Deployment and Service
- `auth.yaml` - Auth Service Deployment and Service
- `video.yaml` - Video Service Deployment and Service
- `homework.yaml` - Homework Service Deployment and Service
- `analytics.yaml` - Analytics Service Deployment and Service
- `collaboration.yaml` - Collaboration Service Deployment and Service
- `pdf.yaml` - PDF Service Deployment and Service
- `frontend.yaml` - Frontend Deployment and Service

## Docker Images

All services use multi-stage Docker builds for optimal image size:

- Go services: Built with `golang:1.21-alpine` and run on `alpine:latest`
- Frontend: Built with `node:20-alpine`

## Local Development

For local development, use Tilt which provides:

- Automatic rebuilds on code changes
- Live updates without full rebuilds
- Unified dashboard for all services
- Log streaming

See the root `Tiltfile` for configuration.
