# Kubernetes FAQ

Frequently asked questions about Kubernetes, its components, and how to work with them.

## General Questions

### What is Kubernetes?

Kubernetes is an open-source container orchestration platform that automates the deployment, scaling, and management of containerized applications.

### How does Kubernetes differ from Docker?

Docker is a container runtime that runs containers. Kubernetes is an orchestration platform that manages containers across multiple hosts, providing features like scaling, load balancing, and self-healing.

### What are the main components of Kubernetes?

**Control Plane:**
- API Server
- etcd
- Scheduler
- Controller Manager

**Worker Nodes:**
- Kubelet
- kube-proxy
- Container Runtime

## Pod Questions

### What is a Pod?

A Pod is the smallest deployable unit in Kubernetes. It contains one or more containers that share storage and network resources.

### How do pods communicate with each other?

Pods can communicate using:
- Direct pod IP addresses
- Service names (DNS-based)
- Environment variables (for service discovery)

### Why is my pod not starting?

Common reasons:
- Image pull errors
- Resource constraints
- Configuration errors
- Health check failures

Check with: `kubectl describe pod my-pod`

### How do I view pod logs?

```bash
kubectl logs my-pod
kubectl logs my-pod --previous  # Previous container instance
kubectl logs -f my-pod          # Follow logs
```

## Deployment Questions

### How do I update a deployment?

```bash
# Update image
kubectl set image deployment/my-app nginx=nginx:1.21

# Or edit deployment
kubectl edit deployment my-app
```

### How do I rollback a deployment?

```bash
# Rollback to previous version
kubectl rollout undo deployment/my-app

# Rollback to specific revision
kubectl rollout undo deployment/my-app --to-revision=2
```

### How do I scale a deployment?

```bash
# Scale to specific number of replicas
kubectl scale deployment my-app --replicas=3

# Or edit deployment
kubectl edit deployment my-app
```

## Service Questions

### What is a Service?

A Service provides a stable network endpoint for accessing pods. It load balances traffic across pod instances.

### What are the different service types?

- **ClusterIP**: Internal cluster IP (default)
- **NodePort**: Exposes service on each node's IP
- **LoadBalancer**: Cloud provider load balancer
- **ExternalName**: Maps to external DNS name

### How does service discovery work?

Services are discoverable via DNS:
- Format: `<service-name>.<namespace>.svc.cluster.local`
- Short form: `<service-name>` (same namespace)

### Why isn't my service routing traffic?

Check:
1. Service selector matches pod labels
2. Pods are running and ready
3. Service endpoints exist: `kubectl get endpoints my-service`
4. Ports are correct

## Networking Questions

### How do pods get IP addresses?

Pods get IP addresses from the CNI (Container Network Interface) plugin, which configures networking for each pod.

### How do I expose my application externally?

Options:
1. **NodePort**: Expose on node IP
2. **LoadBalancer**: Cloud provider load balancer
3. **Ingress**: HTTP/HTTPS routing

### What is Ingress?

Ingress provides HTTP/HTTPS routing to services. It requires an Ingress Controller (like NGINX, Traefik, or Istio).

## Storage Questions

### How do I add persistent storage?

1. Create a PersistentVolumeClaim (PVC)
2. Mount it in your pod/deployment
3. Kubernetes provisions storage based on StorageClass

### What is the difference between PV and PVC?

- **PV (PersistentVolume)**: Cluster resource representing storage
- **PVC (PersistentVolumeClaim)**: Request for storage by a user/pod

### How do I backup persistent volumes?

Backup methods depend on storage backend:
- Snapshot capabilities (if supported)
- Application-level backups
- Volume cloning

## Configuration Questions

### How do I manage configuration?

Use ConfigMaps for non-sensitive configuration:
```bash
kubectl create configmap my-config --from-literal=key=value
```

Use Secrets for sensitive data:
```bash
kubectl create secret generic my-secret --from-literal=password=secret
```

### How do I update a ConfigMap?

```bash
# Edit ConfigMap
kubectl edit configmap my-config

# Or apply new YAML
kubectl apply -f configmap.yaml
```

Note: Pods need to be restarted to pick up ConfigMap changes (unless using volume mounts with refresh).

## Security Questions

### How does RBAC work?

RBAC (Role-Based Access Control) defines:
- **Roles**: Permissions in a namespace
- **RoleBindings**: Bind roles to users/service accounts
- **ClusterRoles**: Cluster-wide permissions
- **ClusterRoleBindings**: Bind cluster roles

### How do I create a service account?

```bash
kubectl create serviceaccount my-sa
```

### How do I restrict pod security?

Use Pod Security Standards or Pod Security Policies:
- **Privileged**: Unrestricted
- **Baseline**: Minimally restrictive
- **Restricted**: Highly restrictive

## Troubleshooting Questions

### How do I debug a failing pod?

1. Check pod status: `kubectl get pod my-pod`
2. Describe pod: `kubectl describe pod my-pod`
3. View logs: `kubectl logs my-pod`
4. Check events: `kubectl get events`

### How do I check cluster health?

```bash
# Check nodes
kubectl get nodes

# Check cluster info
kubectl cluster-info

# Check component status
kubectl get componentstatuses
```

### How do I check resource usage?

```bash
# Node resources
kubectl top nodes

# Pod resources
kubectl top pods
```

## Performance Questions

### How do I limit resource usage?

Set resource requests and limits in pod spec:
```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
```

### How does auto-scaling work?

**Horizontal Pod Autoscaler (HPA)** scales pods based on metrics:
```bash
kubectl autoscale deployment my-app --cpu-percent=80 --min=1 --max=10
```

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kubernetes API Reference](https://kubernetes.io/docs/reference/kubernetes-api/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)

