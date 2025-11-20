# OpenShift Usage Guide

This guide provides practical examples for using OpenShift effectively.

## Basic Operations

### Working with Projects

```bash
# Create a project
oc new-project my-project

# Switch to project
oc project my-project

# List projects
oc get projects

# Delete project
oc delete project my-project
```

### Working with Pods

```bash
# Create pod from image
oc run my-pod --image=nginx:latest

# Get pod status
oc get pods

# Describe pod
oc describe pod my-pod

# Get pod logs
oc logs my-pod

# Execute command in pod
oc exec my-pod -- ls -la

# Delete pod
oc delete pod my-pod
```

### Working with Deployments

```bash
# Create deployment
oc create deployment my-app --image=nginx:latest

# Scale deployment
oc scale deployment my-app --replicas=3

# Update deployment
oc set image deployment/my-app nginx=nginx:1.21

# Rollback deployment
oc rollout undo deployment/my-app

# Check rollout status
oc rollout status deployment/my-app
```

### Working with Services

```bash
# Expose deployment as service
oc expose deployment my-app --port=80

# Get service
oc get service my-app

# Describe service
oc describe service my-app

# Test service
oc run test-pod --image=busybox -it --rm -- wget -O- my-app:80
```

### Working with Routes

```bash
# Create route
oc expose service my-app

# Create route with custom hostname
oc expose service my-app --hostname=my-app.example.com

# Get routes
oc get routes

# Describe route
oc describe route my-app

# Test route
curl http://my-app-<namespace>.apps.<cluster-domain>
```

## Advanced Operations

### Working with ImageStreams

```bash
# Create ImageStream
oc create imagestream my-image

# Import image
oc import-image my-image:latest --from=docker.io/library/nginx:latest

# Get ImageStream
oc get imagestream my-image

# Tag image
oc tag my-image:latest my-image:v1.0
```

### Working with Builds

```bash
# Create BuildConfig
oc new-build --name=my-build --dockerfile="FROM nginx:latest"

# Start build
oc start-build my-build

# Watch build
oc logs -f bc/my-build

# Get build status
oc get builds
```

### Working with ConfigMaps and Secrets

```bash
# Create ConfigMap
oc create configmap my-config --from-literal=key=value

# Create Secret
oc create secret generic my-secret --from-literal=username=admin

# Use in deployment
oc set env deployment/my-app --from=configmap/my-config
oc set env deployment/my-app --from=secret/my-secret
```

### Working with Persistent Volumes

```bash
# Create PVC
oc create -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
EOF

# Use in pod
oc set volume deployment/my-app --add --name=data --type=pvc --claim-name=my-pvc
```

## Network Operations

### Network Policies

```bash
# Create network policy
oc create -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-same-namespace
spec:
  podSelector: {}
  ingress:
  - from:
    - podSelector: {}
EOF

# Get network policies
oc get networkpolicies

# Describe network policy
oc describe networkpolicy allow-same-namespace
```

### Service Discovery

```bash
# Test DNS resolution
oc run test-pod --image=busybox -it --rm -- nslookup my-service

# Test service connectivity
oc run test-pod --image=busybox -it --rm -- wget -O- my-service:80
```

## Monitoring and Observability

### Viewing Metrics

```bash
# Get pod metrics
oc top pods

# Get node metrics
oc top nodes

# Get resource usage
oc adm top pods
oc adm top nodes
```

### Viewing Logs

```bash
# Pod logs
oc logs <pod-name>

# Follow logs
oc logs -f <pod-name>

# Previous container logs
oc logs <pod-name> --previous

# All containers in pod
oc logs <pod-name> --all-containers
```

### Viewing Events

```bash
# Get events
oc get events

# Get events for resource
oc get events --field-selector involvedObject.name=<resource-name>

# Watch events
oc get events -w
```

## Best Practices

1. **Use projects** to organize resources
2. **Use deployments** instead of pods directly
3. **Use services** for internal communication
4. **Use routes** for external access
5. **Use ConfigMaps and Secrets** for configuration
6. **Use resource quotas** to limit resource usage
7. **Use network policies** for security
8. **Monitor resources** regularly

