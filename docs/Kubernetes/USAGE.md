# Kubernetes Usage Guide

This guide provides practical examples for using Kubernetes effectively.

## Basic Operations

### Working with Pods

```bash
# Create pod from image
kubectl run my-pod --image=nginx:latest

# Create pod from YAML
kubectl create -f pod.yaml

# Get pod status
kubectl get pods

# Describe pod
kubectl describe pod my-pod

# Get pod logs
kubectl logs my-pod

# Execute command in pod
kubectl exec my-pod -- ls -la

# Interactive shell
kubectl exec -it my-pod -- /bin/bash

# Delete pod
kubectl delete pod my-pod
```

### Working with Deployments

```bash
# Create deployment
kubectl create deployment my-app --image=nginx:latest

# Create from YAML
kubectl apply -f deployment.yaml

# Get deployments
kubectl get deployments

# Scale deployment
kubectl scale deployment my-app --replicas=3

# Update deployment image
kubectl set image deployment/my-app nginx=nginx:1.21

# Rollout status
kubectl rollout status deployment/my-app

# Rollback deployment
kubectl rollout undo deployment/my-app

# Rollback to specific revision
kubectl rollout undo deployment/my-app --to-revision=2

# View rollout history
kubectl rollout history deployment/my-app
```

### Working with Services

```bash
# Expose deployment as service
kubectl expose deployment my-app --port=80 --type=ClusterIP

# Create service from YAML
kubectl apply -f service.yaml

# Get services
kubectl get services

# Describe service
kubectl describe service my-service

# Get service endpoints
kubectl get endpoints my-service

# Port forward to service
kubectl port-forward service/my-service 8080:80

# Delete service
kubectl delete service my-service
```

### Working with ConfigMaps

```bash
# Create ConfigMap from literal
kubectl create configmap my-config --from-literal=key1=value1 --from-literal=key2=value2

# Create ConfigMap from file
kubectl create configmap my-config --from-file=config.properties

# Create ConfigMap from YAML
kubectl apply -f configmap.yaml

# Get ConfigMap
kubectl get configmap my-config

# View ConfigMap
kubectl get configmap my-config -o yaml

# Use in pod
kubectl create deployment my-app --image=nginx --dry-run=client -o yaml | \
  kubectl set env --from=configmap/my-config -f - | kubectl apply -f -
```

### Working with Secrets

```bash
# Create secret from literal
kubectl create secret generic my-secret --from-literal=username=admin --from-literal=password=secret

# Create secret from file
kubectl create secret generic my-secret --from-file=./username.txt --from-file=./password.txt

# Create secret from YAML
kubectl apply -f secret.yaml

# Get secret
kubectl get secret my-secret

# View secret (base64 encoded)
kubectl get secret my-secret -o yaml

# Decode secret
kubectl get secret my-secret -o jsonpath='{.data.password}' | base64 -d
```

## Advanced Operations

### Working with Namespaces

```bash
# Create namespace
kubectl create namespace my-namespace

# Get namespaces
kubectl get namespaces

# Set default namespace
kubectl config set-context --current --namespace=my-namespace

# Get resources in namespace
kubectl get all -n my-namespace

# Delete namespace
kubectl delete namespace my-namespace
```

### Working with Jobs

```bash
# Create job
kubectl create job my-job --image=busybox -- echo "Hello"

# Create from YAML
kubectl apply -f job.yaml

# Get jobs
kubectl get jobs

# View job logs
kubectl logs job/my-job

# Delete job
kubectl delete job my-job
```

### Working with CronJobs

```bash
# Create CronJob
kubectl create cronjob my-cronjob --image=busybox --schedule="*/1 * * * *" -- echo "Hello"

# Get CronJobs
kubectl get cronjobs

# Suspend CronJob
kubectl patch cronjob my-cronjob -p '{"spec":{"suspend":true}}'

# Resume CronJob
kubectl patch cronjob my-cronjob -p '{"spec":{"suspend":false}}'

# Delete CronJob
kubectl delete cronjob my-cronjob
```

### Working with StatefulSets

```bash
# Create StatefulSet
kubectl apply -f statefulset.yaml

# Get StatefulSets
kubectl get statefulsets

# Scale StatefulSet
kubectl scale statefulset my-statefulset --replicas=3

# Delete StatefulSet
kubectl delete statefulset my-statefulset
```

### Working with DaemonSets

```bash
# Create DaemonSet
kubectl apply -f daemonset.yaml

# Get DaemonSets
kubectl get daemonsets

# Delete DaemonSet
kubectl delete daemonset my-daemonset
```

## Resource Management

### Resource Quotas

```bash
# Create resource quota
kubectl create quota my-quota --hard=cpu=1,memory=1Gi,pods=10

# Get quotas
kubectl get quota

# Describe quota
kubectl describe quota my-quota
```

### Limit Ranges

```bash
# Create limit range
kubectl create limitrange my-limits --max=cpu=2 --max=memory=2Gi --min=cpu=100m --min=memory=128Mi

# Get limit ranges
kubectl get limitranges

# Describe limit range
kubectl describe limitrange my-limits
```

### Resource Requests and Limits

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  containers:
  - name: my-container
    image: nginx
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "500m"
        memory: "512Mi"
```

## Networking

### Ingress

```bash
# Create Ingress
kubectl apply -f ingress.yaml

# Get Ingress
kubectl get ingress

# Describe Ingress
kubectl describe ingress my-ingress
```

### Network Policies

```bash
# Create NetworkPolicy
kubectl apply -f networkpolicy.yaml

# Get NetworkPolicies
kubectl get networkpolicies

# Describe NetworkPolicy
kubectl describe networkpolicy my-policy
```

## Storage

### Persistent Volumes

```bash
# Get persistent volumes
kubectl get pv

# Describe persistent volume
kubectl describe pv my-pv
```

### Persistent Volume Claims

```bash
# Create PVC
kubectl apply -f pvc.yaml

# Get PVCs
kubectl get pvc

# Describe PVC
kubectl describe pvc my-pvc

# Delete PVC
kubectl delete pvc my-pvc
```

### Storage Classes

```bash
# Get storage classes
kubectl get storageclass

# Describe storage class
kubectl describe storageclass my-storageclass
```

## Monitoring and Debugging

### Viewing Metrics

```bash
# Node metrics
kubectl top nodes

# Pod metrics
kubectl top pods

# Pod metrics in namespace
kubectl top pods -n my-namespace
```

### Viewing Events

```bash
# Get events
kubectl get events

# Watch events
kubectl get events --watch

# Events for specific resource
kubectl get events --field-selector involvedObject.name=my-pod
```

### Port Forwarding

```bash
# Forward to pod
kubectl port-forward my-pod 8080:80

# Forward to service
kubectl port-forward service/my-service 8080:80

# Forward to deployment
kubectl port-forward deployment/my-deployment 8080:80
```

## Common Patterns

### Multi-Container Pods

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-pod
spec:
  containers:
  - name: app
    image: nginx
  - name: sidecar
    image: busybox
    command: ['sh', '-c', 'while true; do echo hello; sleep 10; done']
```

### Init Containers

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-container-pod
spec:
  initContainers:
  - name: init
    image: busybox
    command: ['sh', '-c', 'echo Initializing...']
  containers:
  - name: app
    image: nginx
```

### Health Checks

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: health-check-pod
spec:
  containers:
  - name: app
    image: nginx
    livenessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
```

## Best Practices

1. **Use Deployments**: Use Deployments instead of directly creating pods
2. **Resource Limits**: Always set resource requests and limits
3. **Health Checks**: Configure liveness and readiness probes
4. **Labels**: Use consistent labeling strategy
5. **Namespaces**: Organize resources using namespaces
6. **ConfigMaps/Secrets**: Externalize configuration
7. **Rolling Updates**: Use rolling update strategy for zero downtime

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Kubernetes Examples](https://github.com/kubernetes/examples)

