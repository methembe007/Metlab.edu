# Metlab.edu - kubectl Configuration Script (PowerShell)
# This script configures kubectl for the Metlab.edu development environment

$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Blue "========================================"
Write-ColorOutput Blue "kubectl Configuration for Metlab.edu"
Write-ColorOutput Blue "========================================"
Write-Output ""

# Check if kubectl is installed
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "Error: kubectl is not installed"
    Write-Output "Please install kubectl from: https://kubernetes.io/docs/tasks/tools/"
    exit 1
}

# Configuration
$CLUSTER_NAME = "metlab-dev"
$DEFAULT_NAMESPACE = "metlab-dev"

# Check if Minikube cluster exists
try {
    minikube status -p $CLUSTER_NAME 2>&1 | Out-Null
} catch {
    Write-ColorOutput Red "Error: Minikube cluster '$CLUSTER_NAME' is not running"
    Write-Output "Please start the cluster first:"
    Write-Output "  make minikube-setup"
    Write-Output "  or"
    Write-Output "  make minikube-start"
    exit 1
}

Write-ColorOutput Green "✓ Minikube cluster '$CLUSTER_NAME' is running"
Write-Output ""

# Set kubectl context
Write-ColorOutput Blue "Setting kubectl context to '$CLUSTER_NAME'..."
kubectl config use-context $CLUSTER_NAME

# Verify context
$CURRENT_CONTEXT = kubectl config current-context
if ($CURRENT_CONTEXT -eq $CLUSTER_NAME) {
    Write-ColorOutput Green "✓ kubectl context set to '$CLUSTER_NAME'"
} else {
    Write-ColorOutput Red "Error: Failed to set kubectl context"
    exit 1
}
Write-Output ""

# Set default namespace
Write-ColorOutput Blue "Setting default namespace to '$DEFAULT_NAMESPACE'..."
kubectl config set-context --current --namespace=$DEFAULT_NAMESPACE
Write-ColorOutput Green "✓ Default namespace set to '$DEFAULT_NAMESPACE'"
Write-Output ""

# Display current configuration
Write-ColorOutput Blue "========================================"
Write-ColorOutput Blue "Current kubectl Configuration"
Write-ColorOutput Blue "========================================"
Write-Output ""

$context = kubectl config current-context
$cluster = kubectl config view --minify -o jsonpath='{.clusters[0].name}'
$user = kubectl config view --minify -o jsonpath='{.users[0].name}'
$namespace = kubectl config view --minify -o jsonpath='{.contexts[0].context.namespace}'

Write-ColorOutput Green "Context: $context"
Write-ColorOutput Green "Cluster: $cluster"
Write-ColorOutput Green "User: $user"
Write-ColorOutput Green "Namespace: $namespace"
Write-Output ""

# Display cluster information
Write-ColorOutput Blue "Cluster Information:"
kubectl cluster-info
Write-Output ""

# Display available namespaces
Write-ColorOutput Blue "Available Namespaces:"
kubectl get namespaces | Select-String "metlab"
Write-Output ""

# Create kubectl aliases (optional)
Write-ColorOutput Blue "========================================"
Write-ColorOutput Blue "Recommended kubectl Aliases"
Write-ColorOutput Blue "========================================"
Write-Output ""
Write-Output "Add these aliases to your PowerShell profile:"
Write-Output ""
Write-Output "# Metlab.edu kubectl aliases"
Write-Output "Set-Alias -Name k -Value kubectl"
Write-Output "function kgp { kubectl get pods @args }"
Write-Output "function kgs { kubectl get services @args }"
Write-Output "function kgd { kubectl get deployments @args }"
Write-Output "function kl { kubectl logs @args }"
Write-Output "function kd { kubectl describe @args }"
Write-Output "function kx { kubectl exec -it @args }"
Write-Output "function kdev { kubectl config set-context --current --namespace=metlab-dev }"
Write-Output "function kstaging { kubectl config set-context --current --namespace=metlab-staging }"
Write-Output "function kprod { kubectl config set-context --current --namespace=metlab-production }"
Write-Output ""
Write-Output "To edit your profile, run: notepad `$PROFILE"
Write-Output ""

# Display useful commands
Write-ColorOutput Blue "========================================"
Write-ColorOutput Blue "Useful kubectl Commands"
Write-ColorOutput Blue "========================================"
Write-Output ""
Write-ColorOutput Green "View all resources in current namespace:"
Write-Output "  kubectl get all"
Write-Output ""
Write-ColorOutput Green "View pods with more details:"
Write-Output "  kubectl get pods -o wide"
Write-Output ""
Write-ColorOutput Green "View pod logs:"
Write-Output "  kubectl logs <pod-name>"
Write-Output ""
Write-ColorOutput Green "Follow pod logs:"
Write-Output "  kubectl logs -f <pod-name>"
Write-Output ""
Write-ColorOutput Green "Describe a resource:"
Write-Output "  kubectl describe pod <pod-name>"
Write-Output ""
Write-ColorOutput Green "Execute command in pod:"
Write-Output "  kubectl exec -it <pod-name> -- /bin/sh"
Write-Output ""
Write-ColorOutput Green "Port forward to a service:"
Write-Output "  kubectl port-forward svc/<service-name> <local-port>:<service-port>"
Write-Output ""
Write-ColorOutput Green "Switch namespace:"
Write-Output "  kubectl config set-context --current --namespace=<namespace>"
Write-Output ""
Write-ColorOutput Green "View cluster events:"
Write-Output "  kubectl get events --sort-by=.metadata.creationTimestamp"
Write-Output ""

Write-ColorOutput Green "========================================"
Write-ColorOutput Green "✓ kubectl configuration complete!"
Write-ColorOutput Green "========================================"
