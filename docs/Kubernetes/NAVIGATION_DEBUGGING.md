# Kubernetes Navigation and Debugging Guide

This guide explains how to navigate Kubernetes clusters and debug common issues.

## Navigation Basics

### Viewing Resources

```bash
# List all pods
kubectl get pods

# List pods in specific namespace
kubectl get pods -n my-namespace

# List all resources
kubectl get all

# List resources with labels
kubectl get pods -l app=my-app

# Wide output (shows node, IP)
kubectl get pods -o wide
```

### Describing Resources

```bash
# Describe a pod
kubectl describe pod my-pod

# Describe a service
kubectl describe service my-service

# Describe a deployment
kubectl describe deployment my-deployment

# Describe events
kubectl get events --sort-by=.metadata.creationTimestamp
```

### Viewing Logs

```bash
# Pod logs
kubectl logs my-pod

# Previous container instance
kubectl logs my-pod --previous

# Follow logs
kubectl logs -f my-pod

# Logs from all pods with label
kubectl logs -l app=my-app

# Logs with timestamps
kubectl logs my-pod --timestamps

# Last N lines
kubectl logs my-pod --tail=100
```

### Executing Commands

```bash
# Execute command in pod
kubectl exec my-pod -- ls -la

# Interactive shell
kubectl exec -it my-pod -- /bin/bash

# Execute in specific container (multi-container pod)
kubectl exec -it my-pod -c my-container -- /bin/bash
```

## Debugging Strategies

### Pod Issues

#### Pod Not Starting

```bash
# Check pod status
kubectl get pod my-pod

# Describe pod for events
kubectl describe pod my-pod

# Check pod logs
kubectl logs my-pod

# Check previous container logs
kubectl logs my-pod --previous

# Check events
kubectl get events --field-selector involvedObject.name=my-pod
```

**Common Issues:**
- Image pull errors
- Resource constraints
- Configuration errors
- Health check failures

#### Pod CrashLoopBackOff

```bash
# Check current logs
kubectl logs my-pod

# Check previous container logs
kubectl logs my-pod --previous

# Describe pod
kubectl describe pod my-pod

# Check resource limits
kubectl get pod my-pod -o yaml | grep -A 5 resources
```

**Common Causes:**
- Application errors
- Out of memory
- Configuration issues
- Missing dependencies

#### Pod Pending

```bash
# Describe pod to see why
kubectl describe pod my-pod

# Check node resources
kubectl describe node

# Check resource quotas
kubectl describe quota -n my-namespace
```

**Common Causes:**
- Insufficient resources
- Node selector not matching
- Taints/tolerations
- Resource quotas

### Deployment Issues

#### Deployment Not Updating

```bash
# Check deployment status
kubectl rollout status deployment/my-deployment

# Check deployment history
kubectl rollout history deployment/my-deployment

# Describe deployment
kubectl describe deployment my-deployment

# Check replica set
kubectl get replicasets
```

#### Rolling Update Issues

```bash
# Check rollout status
kubectl rollout status deployment/my-deployment

# Pause rollout
kubectl rollout pause deployment/my-deployment

# Resume rollout
kubectl rollout resume deployment/my-deployment

# Rollback
kubectl rollout undo deployment/my-deployment

# Rollback to specific revision
kubectl rollout undo deployment/my-deployment --to-revision=2
```

### Service Issues

#### Service Not Routing Traffic

```bash
# Check service
kubectl get service my-service

# Check endpoints
kubectl get endpoints my-service

# Describe service
kubectl describe service my-service

# Check selector matches pods
kubectl get pods -l app=my-app

# Test service from pod
kubectl run -it --rm debug --image=busybox --restart=Never -- wget -O- my-service:80
```

#### DNS Resolution Issues

```bash
# Test DNS from pod
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup my-service

# Check CoreDNS
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Check CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns
```

### Network Issues

#### Pod-to-Pod Communication

```bash
# Get pod IPs
kubectl get pods -o wide

# Test connectivity
kubectl exec my-pod -- ping other-pod-ip

# Test service connectivity
kubectl exec my-pod -- curl http://my-service:80
```

#### Network Policy Issues

```bash
# List network policies
kubectl get networkpolicies

# Describe network policy
kubectl describe networkpolicy my-policy

# Check if policy is blocking traffic
kubectl get networkpolicies -o yaml
```

### Storage Issues

#### Volume Mount Issues

```bash
# Check pod volume mounts
kubectl describe pod my-pod | grep -A 10 Volumes

# Check persistent volume claims
kubectl get pvc

# Describe PVC
kubectl describe pvc my-pvc

# Check persistent volumes
kubectl get pv
```

### Resource Issues

#### Resource Quotas

```bash
# Check quotas
kubectl get quota -n my-namespace

# Describe quota
kubectl describe quota my-quota -n my-namespace

# Check resource usage
kubectl top pods -n my-namespace
kubectl top nodes
```

#### Resource Limits

```bash
# Check pod resources
kubectl get pod my-pod -o yaml | grep -A 10 resources

# Check node resources
kubectl describe node

# Check node capacity
kubectl get node -o yaml | grep -A 5 capacity
```

## Advanced Debugging

### Debugging with Ephemeral Containers

```bash
# Create debug container in pod
kubectl debug my-pod -it --image=busybox --target=my-container
```

### Port Forwarding

```bash
# Forward local port to pod
kubectl port-forward my-pod 8080:80

# Forward to service
kubectl port-forward service/my-service 8080:80

# Forward to deployment
kubectl port-forward deployment/my-deployment 8080:80
```

### API Server Debugging

```bash
# Check API server logs
kubectl logs -n kube-system -l component=kube-apiserver

# Check API server status
kubectl get --raw /healthz

# Check API versions
kubectl api-versions
```

### etcd Debugging

```bash
# Check etcd status (if accessible)
kubectl get pods -n kube-system -l component=etcd

# Check etcd logs
kubectl logs -n kube-system -l component=etcd
```

## Common Debugging Scenarios

### Application Not Responding

1. Check pod status: `kubectl get pods`
2. Check pod logs: `kubectl logs my-pod`
3. Check service endpoints: `kubectl get endpoints`
4. Test connectivity: `kubectl exec my-pod -- curl localhost:8080`
5. Check health probes: `kubectl describe pod my-pod | grep -A 5 Liveness`

### High Resource Usage

1. Check resource usage: `kubectl top pods`
2. Check resource limits: `kubectl describe pod my-pod | grep -A 5 Limits`
3. Check node resources: `kubectl top nodes`
4. Check for resource quotas: `kubectl get quota`

### Slow Performance

1. Check node resources: `kubectl describe node`
2. Check pod distribution: `kubectl get pods -o wide`
3. Check network policies: `kubectl get networkpolicies`
4. Check service load balancing: `kubectl get endpoints my-service`

### Configuration Issues

1. Check ConfigMap: `kubectl get configmap my-config -o yaml`
2. Check Secrets: `kubectl get secret my-secret -o yaml`
3. Check environment variables: `kubectl describe pod my-pod | grep -A 10 Environment`
4. Verify mounted volumes: `kubectl describe pod my-pod | grep -A 10 Mounts`

## Debugging Tools

### kubectl debug

```bash
# Debug pod with temporary container
kubectl debug my-pod -it --image=busybox
```

### kubectl get events

```bash
# Watch events
kubectl get events --watch

# Events for specific resource
kubectl get events --field-selector involvedObject.name=my-pod

# Recent events
kubectl get events --sort-by=.metadata.creationTimestamp
```

### kubectl logs

```bash
# Multiple containers
kubectl logs my-pod -c my-container

# All containers
kubectl logs my-pod --all-containers=true
```

## Best Practices

1. **Start with describe**: `kubectl describe` provides comprehensive information
2. **Check events**: Events show what happened and when
3. **Review logs**: Application logs often contain error messages
4. **Verify configuration**: Check ConfigMaps, Secrets, and resource definitions
5. **Test connectivity**: Verify network connectivity between components
6. **Check resources**: Ensure sufficient resources are available
7. **Review health checks**: Verify liveness and readiness probes

## Additional Resources

- [Kubernetes Debugging](https://kubernetes.io/docs/tasks/debug/)
- [Troubleshooting Clusters](https://kubernetes.io/docs/tasks/debug/debug-cluster/)
- [Application Debugging](https://kubernetes.io/docs/tasks/debug/debug-application/)

