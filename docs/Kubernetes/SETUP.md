# Kubernetes Setup Guide

This guide provides instructions for setting up and accessing Kubernetes clusters.

## Prerequisites

### Required Tools

- **kubectl**: Kubernetes command-line tool
- **kubeconfig**: Cluster access configuration
- **Container Runtime**: Docker, containerd, or CRI-O (for local clusters)

### Installation

#### Install kubectl

**Linux:**
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

**macOS:**
```bash
brew install kubectl
```

**Windows:**
```powershell
choco install kubernetes-cli
```

#### Verify Installation

```bash
kubectl version --client
```

## Cluster Access

### Getting kubeconfig

**Cloud Providers:**
```bash
# AWS EKS
aws eks update-kubeconfig --name my-cluster --region us-west-2

# Azure AKS
az aks get-credentials --resource-group my-resource-group --name my-cluster

# Google GKE
gcloud container clusters get-credentials my-cluster --zone us-central1-a
```

**Local Cluster (minikube):**
```bash
minikube start
kubectl config view
```

### Configure kubectl

**Set Context:**
```bash
kubectl config use-context my-context
```

**View Current Context:**
```bash
kubectl config current-context
```

**List Contexts:**
```bash
kubectl config get-contexts
```

**View Config:**
```bash
kubectl config view
```

## Local Development Setup

### minikube

**Install:**
```bash
# Linux
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# macOS
brew install minikube
```

**Start Cluster:**
```bash
minikube start
```

**Stop Cluster:**
```bash
minikube stop
```

**Delete Cluster:**
```bash
minikube delete
```

### kind (Kubernetes in Docker)

**Install:**
```bash
# Linux/macOS
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

**Create Cluster:**
```bash
kind create cluster --name my-cluster
```

**Delete Cluster:**
```bash
kind delete cluster --name my-cluster
```

### Docker Desktop

**Enable Kubernetes:**
1. Open Docker Desktop
2. Go to Settings → Kubernetes
3. Enable Kubernetes
4. Click Apply & Restart

## Verify Cluster Access

### Basic Checks

```bash
# Check cluster connection
kubectl cluster-info

# Check nodes
kubectl get nodes

# Check all resources
kubectl get all --all-namespaces
```

### Test Deployment

```bash
# Create test pod
kubectl run test-pod --image=nginx:latest

# Check pod status
kubectl get pods

# Delete test pod
kubectl delete pod test-pod
```

## Namespace Setup

### Create Namespace

```bash
kubectl create namespace my-namespace
```

### Set Default Namespace

```bash
kubectl config set-context --current --namespace=my-namespace
```

### List Namespaces

```bash
kubectl get namespaces
```

## Authentication Setup

### Service Account

```bash
# Create service account
kubectl create serviceaccount my-sa

# Use in pod
kubectl run my-pod --image=nginx --serviceaccount=my-sa
```

### RBAC Setup

```bash
# Create role
kubectl create role pod-reader --verb=get,list,watch --resource=pods

# Create role binding
kubectl create rolebinding read-pods --role=pod-reader --user=my-user
```

## Storage Setup

### Storage Class

```bash
# List storage classes
kubectl get storageclass

# Set default storage class
kubectl patch storageclass my-storageclass -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

## Network Setup

### Check CNI

```bash
# Check CNI pods
kubectl get pods -n kube-system | grep -i cni

# Check network policies
kubectl get networkpolicies
```

## Monitoring Setup

### Metrics Server

```bash
# Deploy metrics server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### Verify Metrics

```bash
# Check node metrics
kubectl top nodes

# Check pod metrics
kubectl top pods
```

## Common Setup Tasks

### Enable Features

```bash
# Check API versions
kubectl api-versions

# Check feature gates (if accessible)
kubectl get --raw /metrics | grep feature
```

### Configure kubectl Aliases

**Add to ~/.bashrc or ~/.zshrc:**
```bash
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get services'
alias kgd='kubectl get deployments'
alias kd='kubectl describe'
alias kl='kubectl logs'
alias ke='kubectl exec -it'
```

### kubectl Autocomplete

**Bash:**
```bash
echo 'source <(kubectl completion bash)' >> ~/.bashrc
kubectl completion bash > /etc/bash_completion.d/kubectl
```

**Zsh:**
```bash
echo 'source <(kubectl completion zsh)' >> ~/.zshrc
```

## Troubleshooting Setup

### Connection Issues

```bash
# Check kubeconfig
kubectl config view

# Test connection
kubectl cluster-info

# Check authentication
kubectl auth can-i get pods
```

### Certificate Issues

```bash
# Verify certificates
kubectl config view --raw

# Update certificates (cloud providers)
# AWS: aws eks update-kubeconfig
# Azure: az aks get-credentials
# GCP: gcloud container clusters get-credentials
```

## Additional Resources

- [kubectl Installation](https://kubernetes.io/docs/tasks/tools/)
- [minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [kind Documentation](https://kind.sigs.k8s.io/)
- [Kubernetes Setup](https://kubernetes.io/docs/setup/)

