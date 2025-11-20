# OpenShift FAQ Section

Frequently asked questions about OpenShift, its components, and how to work with them.

## General Questions

### What is OpenShift?

OpenShift is a Kubernetes-based container platform that provides a complete application development and deployment environment with enterprise features.

### How does OpenShift differ from Kubernetes?

OpenShift extends Kubernetes with:
- Additional APIs (ImageStreams, Builds, Routes)
- Enhanced security (SCCs, network policies)
- Developer tools (Web console, Source-to-Image)
- Built-in CI/CD capabilities
- Enterprise features (multi-tenancy, quotas)

### What are the main components of OpenShift?

- **Control Plane**: API Server, etcd, Controller Manager, Scheduler
- **Compute Nodes**: Kubelet, CRI-O, Kube-proxy, SDN
- **Infrastructure**: Router, Registry, Build System, Web Console

## Component Questions

### How do pods communicate with each other?

Pods communicate through:
- **Direct Pod IP**: Pods can reach each other by IP
- **Services**: Virtual IPs for service discovery
- **DNS**: Service names resolve to service IPs
- **Network Policies**: Control allowed traffic

### How does service discovery work?

1. Services get virtual IPs
2. CoreDNS resolves service names
3. Kube-proxy routes traffic to pods
4. Endpoints track pod IPs

### How do routes work?

Routes provide external access:
1. Router pods watch Route resources
2. Router configures HAProxy
3. External traffic hits router
4. Router forwards to service
5. Service load balances to pods

### How does the API server work?

The API server:
1. Validates and authenticates requests
2. Authorizes based on RBAC
3. Applies admission control
4. Stores state in etcd
5. Notifies controllers of changes

## Network Questions

### How does pod networking work?

Each pod gets its own IP address:
1. CNI plugin assigns IP to pod
2. SDN manages pod network
3. Open vSwitch handles switching
4. Network policies control traffic

### What is a Service?

A Service is a virtual IP that:
- Provides stable endpoint for pods
- Load balances across pod endpoints
- Enables service discovery via DNS
- Abstracts pod IP changes

### What is a Route?

A Route provides external HTTP/HTTPS access:
- Maps external hostname to service
- Handles TLS termination
- Provides load balancing
- Integrates with router pods

### How do network policies work?

Network policies control traffic:
- Define ingress/egress rules
- Select pods by labels
- Enforced by SDN plugin
- Applied at pod level

## API Questions

### What APIs does OpenShift provide?

OpenShift provides:
- **Kubernetes APIs**: All standard Kubernetes APIs
- **OpenShift APIs**: ImageStreams, Builds, Routes, Projects, Templates
- **Custom APIs**: Operator-defined APIs via CRDs

### How do I discover available APIs?

```bash
# List all API resources
oc api-resources

# List API versions
oc api-versions

# Describe specific API
oc explain <resource>
```

### How does authentication work?

OpenShift supports:
- **OAuth**: Web-based authentication
- **LDAP/AD**: Directory integration
- **Certificates**: Client certificates
- **Service Accounts**: For applications

### How does authorization work?

Authorization uses RBAC:
- **Roles**: Define permissions
- **RoleBindings**: Bind roles to users
- **ClusterRoles**: Cluster-wide permissions
- **ClusterRoleBindings**: Cluster-wide bindings

## Debugging Questions

### How do I debug a pod that won't start?

1. Check pod status: `oc get pod <name>`
2. Check events: `oc describe pod <name>`
3. Check logs: `oc logs <pod-name> --previous`
4. Check node resources: `oc describe node`
5. Check image pull: `oc get events | grep <pod-name>`

### How do I debug network connectivity?

1. Check pod network: `oc exec <pod> -- ip addr`
2. Check DNS: `oc exec <pod> -- nslookup <service>`
3. Check service: `oc get service <name>`
4. Check endpoints: `oc get endpoints <name>`
5. Check network policies: `oc get networkpolicies`

### How do I debug API access issues?

1. Check authentication: `oc whoami`
2. Check authorization: `oc auth can-i <verb> <resource>`
3. Check API server: `oc get clusteroperators`
4. Check logs: `oc logs -n openshift-kube-apiserver <pod>`
5. Test API: `curl -k -H "Authorization: Bearer $(oc whoami -t)" <api-url>`

### How do I trace a request through the system?

1. **External Request**: Check route → service → pod
2. **Internal Request**: Check service → endpoints → pod
3. **API Request**: Check authentication → authorization → API → etcd
4. **Resource Creation**: Check API → controller → resource → kubelet

## Navigation Questions

### How do I find what I'm looking for?

1. **Start broad**: `oc get all` to see everything
2. **Narrow down**: `oc get <resource-type>` for specific type
3. **Get details**: `oc describe <resource>` for information
4. **Follow relationships**: Check `ownerReferences` and labels
5. **Check events**: `oc get events` for recent activity

### How do I understand component relationships?

1. Use `oc describe` to see relationships
2. Check `ownerReferences` in resource YAML
3. Follow labels and selectors
4. Check events for interactions
5. Review [Component Interactions Guide](COMPONENT_INTERACTIONS.md)

### How do I navigate between related resources?

```bash
# Find pods for a service
oc get pods -l app=<label> -n <namespace>

# Find services for a route
oc get route <route-name> -o jsonpath='{.spec.to.name}'

# Find deployments for a pod
oc get pod <pod-name> -o jsonpath='{.metadata.ownerReferences}'
```

## Still Have Questions?

- Check the [documentation index](README.md)
- Review [Navigation and Debugging Guide](NAVIGATION_DEBUGGING.md)
- Review [Component Interactions Guide](COMPONENT_INTERACTIONS.md)
- Check OpenShift official documentation
- Ask cluster administrators

