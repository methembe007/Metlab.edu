# kubectl Quick Reference for Metlab.edu

A quick reference guide for common kubectl commands used in the Metlab.edu development environment.

## Context and Namespace

```bash
# View current context
kubectl config current-context

# Switch to metlab-dev context
kubectl config use-context metlab-dev

# Set default namespace
kubectl config set-context --current --namespace=metlab-dev

# View all contexts
kubectl config get-contexts

# View current namespace
kubectl config view --minify | grep namespace:
```

## Viewing Resources

```bash
# View all resources in current namespace
kubectl get all

# View all resources in all namespaces
kubectl get all -A

# View pods
kubectl get pods
kubectl get pods -o wide  # More details
kubectl get pods -w       # Watch mode

# View services
kubectl get services
kubectl get svc           # Short form

# View deployments
kubectl get deployments
kubectl get deploy        # Short form

# View namespaces
kubectl get namespaces
kubectl get ns            # Short form

# View persistent volumes
kubectl get pv
kubectl get pvc           # Persistent volume claims

# View config maps and secrets
kubectl get configmaps
kubectl get secrets
```

## Describing Resources

```bash
# Describe a pod (shows events and details)
kubectl describe pod <pod-name>

# Describe a service
kubectl describe service <service-name>

# Describe a deployment
kubectl describe deployment <deployment-name>

# Describe a node
kubectl describe node <node-name>
```

## Logs

```bash
# View pod logs
kubectl logs <pod-name>

# Follow logs (tail -f)
kubectl logs -f <pod-name>

# View logs from previous container instance
kubectl logs <pod-name> --previous

# View logs from specific container in pod
kubectl logs <pod-name> -c <container-name>

# View logs from all containers in pod
kubectl logs <pod-name> --all-containers=true

# View last 100 lines
kubectl logs <pod-name> --tail=100

# View logs since 1 hour ago
kubectl logs <pod-name> --since=1h
```

## Executing Commands

```bash
# Execute command in pod
kubectl exec <pod-name> -- <command>

# Interactive shell in pod
kubectl exec -it <pod-name> -- /bin/sh
kubectl exec -it <pod-name> -- /bin/bash

# Execute in specific container
kubectl exec -it <pod-name> -c <container-name> -- /bin/sh
```

## Port Forwarding

```bash
# Forward local port to pod
kubectl port-forward <pod-name> <local-port>:<pod-port>

# Forward to service
kubectl port-forward svc/<service-name> <local-port>:<service-port>

# Forward to deployment
kubectl port-forward deployment/<deployment-name> <local-port>:<pod-port>

# Examples for Metlab services
kubectl port-forward svc/api-gateway 8080:8080
kubectl port-forward svc/frontend 3000:3000
kubectl port-forward svc/postgres 5432:5432
```

## Applying and Deleting Resources

```bash
# Apply a manifest file
kubectl apply -f <file.yaml>

# Apply all manifests in directory
kubectl apply -f <directory>/

# Apply all k8s manifests
kubectl apply -f infrastructure/k8s/

# Delete resource from file
kubectl delete -f <file.yaml>

# Delete all resources in namespace
kubectl delete all --all -n <namespace>

# Delete specific resource
kubectl delete pod <pod-name>
kubectl delete service <service-name>
kubectl delete deployment <deployment-name>
```

## Scaling

```bash
# Scale deployment
kubectl scale deployment <deployment-name> --replicas=3

# Autoscale deployment
kubectl autoscale deployment <deployment-name> --min=2 --max=10 --cpu-percent=80
```

## Rolling Updates and Rollbacks

```bash
# Update image
kubectl set image deployment/<deployment-name> <container-name>=<new-image>

# View rollout status
kubectl rollout status deployment/<deployment-name>

# View rollout history
kubectl rollout history deployment/<deployment-name>

# Rollback to previous version
kubectl rollout undo deployment/<deployment-name>

# Rollback to specific revision
kubectl rollout undo deployment/<deployment-name> --to-revision=2

# Restart deployment (rolling restart)
kubectl rollout restart deployment/<deployment-name>
```

## Events and Troubleshooting

```bash
# View events in current namespace
kubectl get events

# View events sorted by time
kubectl get events --sort-by=.metadata.creationTimestamp

# View events for specific resource
kubectl get events --field-selector involvedObject.name=<pod-name>

# View cluster info
kubectl cluster-info

# View node status
kubectl get nodes
kubectl top nodes  # Resource usage

# View pod resource usage
kubectl top pods
kubectl top pods -n <namespace>
```

## Labels and Selectors

```bash
# View pods with labels
kubectl get pods --show-labels

# Filter by label
kubectl get pods -l app=api-gateway
kubectl get pods -l environment=production

# Add label to resource
kubectl label pod <pod-name> environment=dev

# Remove label
kubectl label pod <pod-name> environment-
```

## Copying Files

```bash
# Copy file from pod to local
kubectl cp <pod-name>:<path-in-pod> <local-path>

# Copy file from local to pod
kubectl cp <local-path> <pod-name>:<path-in-pod>

# Copy from specific container
kubectl cp <pod-name>:<path> <local-path> -c <container-name>
```

## Resource Management

```bash
# View resource quotas
kubectl get resourcequota

# View limit ranges
kubectl get limitrange

# View pod resource requests and limits
kubectl describe pod <pod-name> | grep -A 5 "Limits\|Requests"
```

## Debugging

```bash
# Run temporary debug pod
kubectl run debug --rm -it --image=alpine -- /bin/sh

# Run debug pod with network tools
kubectl run debug --rm -it --image=nicolaka/netshoot -- /bin/bash

# Check DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup <service-name>

# Test connectivity to service
kubectl run -it --rm debug --image=busybox --restart=Never -- wget -O- http://<service-name>:<port>
```

## Metlab-Specific Commands

### Service Access

```bash
# API Gateway
kubectl port-forward svc/api-gateway 8080:8080 -n metlab-dev

# Frontend
kubectl port-forward svc/frontend 3000:3000 -n metlab-dev

# PostgreSQL
kubectl port-forward svc/postgres 5432:5432 -n metlab-dev

# Redis
kubectl port-forward svc/redis 6379:6379 -n metlab-dev
```

### View Service Logs

```bash
# API Gateway logs
kubectl logs -f -l app=api-gateway -n metlab-dev

# Auth Service logs
kubectl logs -f -l app=auth -n metlab-dev

# Video Service logs
kubectl logs -f -l app=video -n metlab-dev

# All service logs
kubectl logs -f -l app=metlab --all-containers=true -n metlab-dev
```

### Check Service Status

```bash
# All Metlab services
kubectl get pods -l app=metlab -n metlab-dev

# Specific service
kubectl get pods -l app=api-gateway -n metlab-dev

# Service endpoints
kubectl get endpoints -n metlab-dev
```

### Database Operations

```bash
# Connect to PostgreSQL
kubectl exec -it <postgres-pod-name> -n metlab-dev -- psql -U postgres

# Run SQL query
kubectl exec -it <postgres-pod-name> -n metlab-dev -- psql -U postgres -c "SELECT * FROM users LIMIT 10;"

# Backup database
kubectl exec <postgres-pod-name> -n metlab-dev -- pg_dump -U postgres metlab > backup.sql

# Restore database
kubectl exec -i <postgres-pod-name> -n metlab-dev -- psql -U postgres metlab < backup.sql
```

### Redis Operations

```bash
# Connect to Redis CLI
kubectl exec -it <redis-pod-name> -n metlab-dev -- redis-cli

# Check Redis keys
kubectl exec <redis-pod-name> -n metlab-dev -- redis-cli KEYS '*'

# Get Redis info
kubectl exec <redis-pod-name> -n metlab-dev -- redis-cli INFO
```

## Useful Aliases

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
# kubectl aliases
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get services'
alias kgd='kubectl get deployments'
alias kga='kubectl get all'
alias kl='kubectl logs'
alias klf='kubectl logs -f'
alias kd='kubectl describe'
alias kx='kubectl exec -it'
alias kpf='kubectl port-forward'

# Namespace shortcuts
alias kdev='kubectl config set-context --current --namespace=metlab-dev'
alias kstaging='kubectl config set-context --current --namespace=metlab-staging'
alias kprod='kubectl config set-context --current --namespace=metlab-production'

# Common operations
alias kwatch='kubectl get pods -w'
alias kevents='kubectl get events --sort-by=.metadata.creationTimestamp'
alias ktop='kubectl top pods'
```

## Output Formats

```bash
# JSON output
kubectl get pods -o json

# YAML output
kubectl get pods -o yaml

# Wide output (more columns)
kubectl get pods -o wide

# Custom columns
kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase

# JSONPath
kubectl get pods -o jsonpath='{.items[*].metadata.name}'

# Template
kubectl get pods -o go-template='{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}'
```

## Tips and Tricks

1. **Use tab completion**: Enable kubectl autocompletion for faster typing
   ```bash
   source <(kubectl completion bash)  # For bash
   source <(kubectl completion zsh)   # For zsh
   ```

2. **Use short names**: Most resources have short names (po, svc, deploy, etc.)

3. **Use labels**: Label resources for easier filtering and management

4. **Watch mode**: Use `-w` flag to watch resources in real-time

5. **Dry run**: Use `--dry-run=client -o yaml` to preview changes without applying

6. **Explain resources**: Use `kubectl explain <resource>` to see resource documentation

7. **Use contexts**: Switch between different clusters easily with contexts

8. **Resource limits**: Always set resource requests and limits for production

9. **Health checks**: Configure liveness and readiness probes for all services

10. **Use namespaces**: Isolate resources using namespaces for different environments

## Additional Resources

- [Official kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [kubectl Command Reference](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Minikube Setup Guide](MINIKUBE_SETUP.md)

---

**Last Updated**: 2026-02-09
