# Minikube Setup Guide

This guide provides detailed instructions for setting up a local Kubernetes development environment using Minikube for the Metlab.edu cloud-native platform.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Setup](#quick-setup)
- [Manual Setup](#manual-setup)
- [Configuration Details](#configuration-details)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Useful Commands](#useful-commands)

## Prerequisites

Before setting up Minikube, ensure you have the following installed:

### Required Software

1. **Docker** (v20.10+)
   - Download: https://docs.docker.com/get-docker/
   - Verify: `docker --version`
   - Ensure Docker is running: `docker info`

2. **Minikube** (v1.30+)
   - Download: https://minikube.sigs.k8s.io/docs/start/
   - Verify: `minikube version`

3. **kubectl** (v1.27+)
   - Download: https://kubernetes.io/docs/tasks/tools/
   - Verify: `kubectl version --client`

4. **Tilt** (v0.33+) - Optional but recommended
   - Download: https://docs.tilt.dev/install.html
   - Verify: `tilt version`

### System Requirements

- **CPU**: Minimum 4 cores (8 cores recommended)
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Disk Space**: Minimum 20GB free space
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux

## Quick Setup

The fastest way to set up Minikube is using our automated setup script:

### Linux/macOS

```bash
cd cloud-native/scripts
chmod +x setup-minikube.sh
./setup-minikube.sh
```

### Windows (PowerShell)

```powershell
cd cloud-native\scripts
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\setup-minikube.ps1
```

The script will:
- ✓ Check prerequisites
- ✓ Create Minikube cluster with optimal settings
- ✓ Enable required addons
- ✓ Configure kubectl context
- ✓ Create Kubernetes namespaces
- ✓ Display cluster information

## Manual Setup

If you prefer to set up Minikube manually, follow these steps:

### Step 1: Start Minikube Cluster

```bash
minikube start \
  --profile metlab-dev \
  --cpus=4 \
  --memory=8192 \
  --driver=docker \
  --kubernetes-version=stable
```

**Configuration Explanation:**
- `--profile metlab-dev`: Creates a named cluster profile
- `--cpus=4`: Allocates 4 CPU cores
- `--memory=8192`: Allocates 8GB RAM
- `--driver=docker`: Uses Docker as the container runtime
- `--kubernetes-version=stable`: Uses the latest stable Kubernetes version

### Step 2: Enable Required Addons

```bash
# Enable Ingress for routing external traffic
minikube addons enable ingress -p metlab-dev

# Enable Metrics Server for resource monitoring
minikube addons enable metrics-server -p metlab-dev

# Enable Dashboard for web UI
minikube addons enable dashboard -p metlab-dev

# Enable Storage Provisioner for persistent volumes
minikube addons enable storage-provisioner -p metlab-dev

# Enable Default Storage Class
minikube addons enable default-storageclass -p metlab-dev
```

### Step 3: Configure kubectl Context

```bash
# Set kubectl to use the Minikube cluster
kubectl config use-context metlab-dev

# Verify the context
kubectl config current-context
```

### Step 4: Create Namespaces

```bash
# Navigate to the k8s directory
cd cloud-native/infrastructure/k8s

# Apply namespace manifests
kubectl apply -f namespace.yaml
```

This creates three namespaces:
- `metlab-dev`: Development environment
- `metlab-staging`: Staging environment (for future use)
- `metlab-production`: Production environment (for future use)

## Configuration Details

### Cluster Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| Profile Name | `metlab-dev` | Isolates this cluster from others |
| CPUs | 4 | Sufficient for running all microservices |
| Memory | 8192 MB | Adequate for services + database + cache |
| Driver | Docker | Cross-platform compatibility |
| Kubernetes Version | Stable | Latest stable release |

### Enabled Addons

| Addon | Purpose | Port |
|-------|---------|------|
| **ingress** | Routes external traffic to services | 80, 443 |
| **metrics-server** | Collects resource metrics for HPA | - |
| **dashboard** | Web-based Kubernetes UI | 30000 |
| **storage-provisioner** | Dynamic volume provisioning | - |
| **default-storageclass** | Default storage for PVCs | - |

### Namespaces

| Namespace | Environment | Purpose |
|-----------|-------------|---------|
| `metlab-dev` | Development | Local development and testing |
| `metlab-staging` | Staging | Pre-production testing |
| `metlab-production` | Production | Production deployment (future) |

## Verification

After setup, verify your Minikube cluster is working correctly:

### 1. Check Cluster Status

```bash
minikube status -p metlab-dev
```

Expected output:
```
metlab-dev
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured
```

### 2. Verify kubectl Context

```bash
kubectl config current-context
```

Expected output: `metlab-dev`

### 3. Check Namespaces

```bash
kubectl get namespaces | grep metlab
```

Expected output:
```
metlab-dev          Active   1m
metlab-staging      Active   1m
metlab-production   Active   1m
```

### 4. Verify Addons

```bash
minikube addons list -p metlab-dev | grep enabled
```

Expected output should show:
- ingress: enabled
- metrics-server: enabled
- dashboard: enabled
- storage-provisioner: enabled
- default-storageclass: enabled

### 5. Check Cluster Resources

```bash
kubectl get nodes
kubectl get pods -A
```

All system pods should be in `Running` or `Completed` state.

## Troubleshooting

### Issue: Minikube fails to start

**Symptoms:**
```
❌ Exiting due to PROVIDER_DOCKER_NOT_RUNNING
```

**Solution:**
1. Ensure Docker is running: `docker info`
2. Restart Docker Desktop
3. Try starting Minikube again

---

### Issue: Insufficient resources

**Symptoms:**
```
❌ Requested memory allocation (8192MB) is more than your system has available
```

**Solution:**
1. Reduce memory allocation: `--memory=4096`
2. Reduce CPU allocation: `--cpus=2`
3. Close other applications to free resources

---

### Issue: Addons fail to enable

**Symptoms:**
```
❌ addon ingress failed to enable
```

**Solution:**
1. Wait a few minutes for cluster to stabilize
2. Try enabling addon again: `minikube addons enable ingress -p metlab-dev`
3. Check addon status: `minikube addons list -p metlab-dev`

---

### Issue: kubectl context not set

**Symptoms:**
```
error: context "metlab-dev" does not exist
```

**Solution:**
1. List available contexts: `kubectl config get-contexts`
2. Set context manually: `kubectl config use-context metlab-dev`
3. Verify: `kubectl config current-context`

---

### Issue: Pods stuck in Pending state

**Symptoms:**
```
NAME                    READY   STATUS    RESTARTS   AGE
my-pod-xxx              0/1     Pending   0          5m
```

**Solution:**
1. Check pod events: `kubectl describe pod <pod-name>`
2. Check node resources: `kubectl top nodes`
3. Increase cluster resources if needed
4. Check for PVC issues: `kubectl get pvc`

---

### Issue: Cannot access services

**Symptoms:**
- Services not accessible via `localhost`

**Solution:**
1. Use `minikube service` command:
   ```bash
   minikube service <service-name> -p metlab-dev
   ```
2. Or use port forwarding:
   ```bash
   kubectl port-forward svc/<service-name> <local-port>:<service-port>
   ```
3. Get Minikube IP: `minikube ip -p metlab-dev`

## Useful Commands

### Cluster Management

```bash
# View cluster status
minikube status -p metlab-dev

# Stop cluster (preserves state)
minikube stop -p metlab-dev

# Start stopped cluster
minikube start -p metlab-dev

# Delete cluster (removes all data)
minikube delete -p metlab-dev

# SSH into cluster node
minikube ssh -p metlab-dev

# Get cluster IP
minikube ip -p metlab-dev
```

### Dashboard Access

```bash
# Open Kubernetes dashboard in browser
minikube dashboard -p metlab-dev

# Get dashboard URL without opening browser
minikube dashboard --url -p metlab-dev
```

### Service Access

```bash
# List all services
minikube service list -p metlab-dev

# Access a specific service
minikube service <service-name> -p metlab-dev -n metlab-dev

# Get service URL
minikube service <service-name> --url -p metlab-dev -n metlab-dev
```

### Addon Management

```bash
# List all addons
minikube addons list -p metlab-dev

# Enable an addon
minikube addons enable <addon-name> -p metlab-dev

# Disable an addon
minikube addons disable <addon-name> -p metlab-dev
```

### Resource Monitoring

```bash
# View node resources
kubectl top nodes

# View pod resources
kubectl top pods -n metlab-dev

# View all resources in namespace
kubectl get all -n metlab-dev

# Watch pod status
kubectl get pods -n metlab-dev -w
```

### Logs and Debugging

```bash
# View pod logs
kubectl logs <pod-name> -n metlab-dev

# Follow pod logs
kubectl logs -f <pod-name> -n metlab-dev

# View logs from all containers in a pod
kubectl logs <pod-name> -n metlab-dev --all-containers=true

# Describe pod (shows events)
kubectl describe pod <pod-name> -n metlab-dev

# Execute command in pod
kubectl exec -it <pod-name> -n metlab-dev -- /bin/sh
```

### Context Management

```bash
# List all contexts
kubectl config get-contexts

# Switch context
kubectl config use-context <context-name>

# View current context
kubectl config current-context

# Set default namespace
kubectl config set-context --current --namespace=metlab-dev
```

## Next Steps

After setting up Minikube, you can:

1. **Deploy Services**: Apply Kubernetes manifests
   ```bash
   kubectl apply -f infrastructure/k8s/
   ```

2. **Start Development**: Use Tilt for hot-reload development
   ```bash
   tilt up
   ```

3. **Build Docker Images**: Build all service images
   ```bash
   make docker-build
   ```

4. **Run Tests**: Execute test suite
   ```bash
   make test
   ```

## Additional Resources

- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Tilt Documentation](https://docs.tilt.dev/)
- [Metlab.edu Architecture Design](../../.kiro/specs/cloud-native-architecture/design.md)

## Support

If you encounter issues not covered in this guide:

1. Check Minikube logs: `minikube logs -p metlab-dev`
2. Check system events: `kubectl get events -n metlab-dev`
3. Consult the [Troubleshooting](#troubleshooting) section
4. Reach out to the development team

---

**Last Updated**: 2026-02-09
**Minikube Version**: 1.30+
**Kubernetes Version**: 1.27+
