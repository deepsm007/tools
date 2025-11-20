# OpenShift Setup and Navigation Guide

This guide helps you set up access to OpenShift clusters and navigate them effectively.

## Prerequisites

### Required Tools

1. **oc (OpenShift CLI)**
   ```bash
   # Download from https://mirror.openshift.com/pub/openshift-v4/clients/ocp/
   # Or install via package manager
   
   # Verify installation
   oc version
   ```

2. **kubectl** (optional, oc includes kubectl functionality)
   ```bash
   kubectl version --client
   ```

3. **Git**
   ```bash
   git --version
   ```

### Optional but Recommended

- **jq** - For JSON processing
- **yq** - For YAML processing
- **curl** - For API testing
- **tcpdump/wireshark** - For network debugging

## Setting Up Cluster Access

### 1. Get Cluster Credentials

```bash
# Download kubeconfig from cluster admin
# Or use oc login for web-based authentication

# Login via web browser
oc login <cluster-url>

# Login with token
oc login <cluster-url> --token=<token>

# Login with username/password
oc login <cluster-url> -u <username> -p <password>
```

### 2. Verify Access

```bash
# Check current user
oc whoami

# Check cluster info
oc cluster-info

# List projects you can access
oc projects

# Check permissions
oc auth can-i <verb> <resource> -n <namespace>
```

### 3. Set Default Project

```bash
# Switch to a project
oc project <project-name>

# Check current project
oc project

# List all projects
oc get projects
```

## Environment Requirements

### For Development

- **Operating System**: Linux, macOS, or Windows with WSL2
- **Network Access**: Access to OpenShift cluster
- **Permissions**: Appropriate RBAC permissions for your tasks

### For Administration

- **Cluster Admin Access**: For cluster-level operations
- **Project Admin Access**: For project-level operations
- **Network Access**: Access to cluster API and nodes

## How to Navigate OpenShift

### Basic Navigation Commands

```bash
# Get current context
oc config current-context

# List all contexts
oc config get-contexts

# Switch context
oc config use-context <context-name>

# Get current project
oc project

# Switch project
oc project <project-name>

# List all resources
oc get all

# Get specific resource type
oc get pods
oc get services
oc get routes
oc get deployments
```

### Resource Navigation

```bash
# Get resource details
oc get <resource> <name> -o yaml
oc describe <resource> <name>

# Follow resource relationships
oc get <resource> <name> -o jsonpath='{.spec}'
oc get <resource> <name> -o jsonpath='{.status}'

# Watch resources
oc get <resource> -w

# Get resources across namespaces
oc get <resource> --all-namespaces
```

### Namespace Navigation

```bash
# List namespaces
oc get namespaces

# Get namespace details
oc describe namespace <namespace>

# List all resources in namespace
oc get all -n <namespace>

# Check namespace quotas
oc describe quota -n <namespace>
```

## How to Debug Issues

### Debugging Pods

```bash
# Check pod status
oc get pods -n <namespace>

# Get pod details
oc describe pod <pod-name> -n <namespace>

# Check pod logs
oc logs <pod-name> -n <namespace>

# Check previous container logs
oc logs <pod-name> -n <namespace> --previous

# Check specific container logs
oc logs <pod-name> -c <container-name> -n <namespace>

# Execute commands in pod
oc exec <pod-name> -n <namespace> -- <command>

# Debug pod (create debug container)
oc debug <pod-name> -n <namespace>
```

### Debugging Services

```bash
# Check service
oc get service <service-name> -n <namespace>
oc describe service <service-name> -n <namespace>

# Check endpoints
oc get endpoints <service-name> -n <namespace>

# Test service from pod
oc run test-pod --image=busybox -it --rm -- sh
# Inside pod: wget -O- <service>:<port>
```

### Debugging Routes

```bash
# Check route
oc get route <route-name> -n <namespace>
oc describe route <route-name> -n <namespace>

# Test route
curl -v http://<route-host>

# Check router pods
oc get pods -n openshift-ingress
oc logs -n openshift-ingress <router-pod>
```

### Debugging Network

```bash
# Check pod network
oc exec <pod-name> -n <namespace> -- ip addr
oc exec <pod-name> -n <namespace> -- ip route

# Check DNS
oc exec <pod-name> -n <namespace> -- nslookup <service>
oc exec <pod-name> -n <namespace> -- dig <service>

# Check network policies
oc get networkpolicies -n <namespace>
oc describe networkpolicy <policy-name> -n <namespace>
```

### Debugging API

```bash
# Check API access
oc auth can-i <verb> <resource> -n <namespace>

# Check API resources
oc api-resources
oc api-versions

# Test API directly
curl -k -H "Authorization: Bearer $(oc whoami -t)" \
  https://<api-server>/api/v1/namespaces

# Check API server status
oc get clusteroperators
```

## Common Errors and Solutions

### Error: "Unable to connect to the server"

**Solution:**
```bash
# Check cluster URL
oc cluster-info

# Verify network connectivity
ping <cluster-url>

# Check kubeconfig
oc config view

# Re-login
oc login <cluster-url>
```

### Error: "User cannot list resource"

**Solution:**
```bash
# Check permissions
oc auth can-i list <resource> -n <namespace>

# Check current user
oc whoami

# Check role bindings
oc get rolebindings -n <namespace>
oc get clusterrolebindings

# Request access from admin
```

### Error: "Project not found"

**Solution:**
```bash
# List available projects
oc projects

# Check if project exists
oc get project <project-name>

# Create project (if you have permissions)
oc new-project <project-name>
```

### Error: "Image pull failed"

**Solution:**
```bash
# Check image pull secret
oc get secrets -n <namespace>
oc describe secret <pull-secret> -n <namespace>

# Check image stream
oc get imagestream <image-name> -n <namespace>

# Check registry access
oc get route -n openshift-image-registry
```

## Navigation Best Practices

1. **Use oc project** to set context
2. **Use oc get all** to see overview
3. **Use oc describe** for detailed information
4. **Use oc logs** for troubleshooting
5. **Use oc exec** for debugging inside pods
6. **Use oc debug** for advanced debugging
7. **Check events** for resource issues
8. **Use -o yaml** to see full resource definition

## Getting Help

- Check OpenShift documentation
- Use `oc --help` for command help
- Check cluster logs
- Ask cluster administrators
- Review [Navigation and Debugging Guide](NAVIGATION_DEBUGGING.md)

