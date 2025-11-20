# Kubernetes Component Interactions Guide

This guide explains how Kubernetes components interact with each other and how to understand these interactions.

## Core Component Interactions

### API Server Interactions

```mermaid
graph TB
    subgraph "API Server Clients"
        CLI[kubectl CLI]
        Dashboard[Web Dashboard]
        Controllers[Controllers]
        Operators[Operators]
        Kubelet[Kubelet]
        Apps[Applications]
    end
    
    subgraph "API Server"
        Auth[Authentication]
        Authz[Authorization]
        Admission[Admission Control]
        API[API Handler]
    end
    
    subgraph "Backend Storage"
        etcd[etcd]
    end
    
    subgraph "Controllers"
        Replication[Replication Controller]
        Deployment[Deployment Controller]
        Service[Service Controller]
        Node[Node Controller]
    end
    
    CLI --> Auth
    Dashboard --> Auth
    Controllers --> Auth
    Operators --> Auth
    Kubelet --> Auth
    Apps --> Auth
    
    Auth --> Authz
    Authz --> Admission
    Admission --> API
    API --> etcd
    
    etcd --> Replication
    etcd --> Deployment
    etcd --> Service
    etcd --> Node
```

### Controller Interactions

```mermaid
sequenceDiagram
    participant API as API Server
    participant etcd as etcd
    participant Controller as Controller
    participant Resource as Resource
    participant Kubelet as Kubelet
    
    API->>etcd: Store Resource
    etcd->>Controller: Watch Event
    Controller->>Controller: Reconcile Logic
    Controller->>API: Create/Update Resource
    API->>etcd: Store Change
    etcd->>Kubelet: Resource Assignment
    Kubelet->>Resource: Create/Update
    Resource->>Kubelet: Status Update
    Kubelet->>API: Update Status
    API->>etcd: Store Status
    etcd->>Controller: Status Event
```

## Pod Lifecycle Interactions

### Pod Creation Flow

```mermaid
sequenceDiagram
    participant User as User/kubectl
    participant API as API Server
    participant etcd as etcd
    participant Scheduler as Scheduler
    participant Kubelet as Kubelet
    participant Runtime as Container Runtime
    participant Pod as Pod
    
    User->>API: Create Pod
    API->>etcd: Store Pod Spec
    etcd->>Scheduler: Pod Pending Event
    Scheduler->>Scheduler: Select Node
    Scheduler->>API: Bind Pod to Node
    API->>etcd: Update Pod Status
    etcd->>Kubelet: Pod Assignment
    Kubelet->>Runtime: Create Container
    Runtime->>Pod: Start Container
    Pod->>Kubelet: Status Update
    Kubelet->>API: Update Pod Status
    API->>etcd: Store Status
```

### Pod Deletion Flow

```mermaid
sequenceDiagram
    participant User as User
    participant API as API Server
    participant etcd as etcd
    participant Kubelet as Kubelet
    participant Pod as Pod
    
    User->>API: Delete Pod
    API->>etcd: Mark Pod for Deletion
    etcd->>Kubelet: Deletion Event
    Kubelet->>Pod: Send SIGTERM
    Pod->>Pod: Graceful Shutdown
    Kubelet->>Pod: Force Delete (if needed)
    Pod->>Kubelet: Terminated
    Kubelet->>API: Update Status
    API->>etcd: Remove Pod
```

## Deployment Interactions

### Deployment Update Flow

```mermaid
sequenceDiagram
    participant User as User
    participant API as API Server
    participant Deployment as Deployment Controller
    participant ReplicaSet as ReplicaSet
    participant OldPod as Old Pods
    participant NewPod as New Pods
    
    User->>API: Update Deployment
    API->>Deployment: Deployment Changed
    Deployment->>Deployment: Calculate Desired State
    Deployment->>API: Create New ReplicaSet
    API->>ReplicaSet: New ReplicaSet Created
    ReplicaSet->>API: Create New Pods
    API->>NewPod: Create Pods
    NewPod->>NewPod: Start Containers
    NewPod->>API: Pod Ready
    Deployment->>API: Scale Down Old ReplicaSet
    API->>OldPod: Delete Old Pods
    OldPod->>OldPod: Graceful Termination
```

## Service Discovery Interactions

### Service and Endpoints

```mermaid
graph TB
    subgraph "Service Discovery"
        Service[Service<br/>Virtual IP]
        Endpoints[Endpoints<br/>Pod IPs]
        DNS[CoreDNS<br/>DNS Resolution]
    end
    
    subgraph "Pods"
        Pod1[Pod 1]
        Pod2[Pod 2]
        Pod3[Pod 3]
    end
    
    subgraph "kube-proxy"
        Proxy[kube-proxy<br/>Load Balancing]
    end
    
    Service --> Endpoints
    Endpoints --> Pod1
    Endpoints --> Pod2
    Endpoints --> Pod3
    Service --> DNS
    Service --> Proxy
    Proxy --> Pod1
    Proxy --> Pod2
    Proxy --> Pod3
```

### DNS Resolution Flow

```mermaid
sequenceDiagram
    participant Pod as Pod
    participant DNS as CoreDNS
    participant Service as Service
    participant Endpoints as Endpoints
    participant TargetPod as Target Pod
    
    Pod->>DNS: Query service-name.namespace.svc.cluster.local
    DNS->>DNS: Resolve Service
    DNS->>Service: Get Service IP
    Service->>Endpoints: Get Pod IPs
    Endpoints->>TargetPod: Select Pod
    DNS-->>Pod: Return Pod IP
    Pod->>TargetPod: Connect
```

## Networking Interactions

### Pod-to-Pod Communication

```mermaid
graph TB
    subgraph "Source Pod"
        SourcePod[Pod A<br/>10.244.1.5]
    end
    
    subgraph "CNI Plugin"
        CNI[CNI Plugin<br/>Network Configuration]
    end
    
    subgraph "Network"
        Bridge[Network Bridge]
        Routes[Routing Rules]
    end
    
    subgraph "Destination Pod"
        DestPod[Pod B<br/>10.244.2.3]
    end
    
    SourcePod --> CNI
    CNI --> Bridge
    Bridge --> Routes
    Routes --> DestPod
```

### Ingress Flow

```mermaid
sequenceDiagram
    participant User as User
    participant Ingress as Ingress Controller
    participant IngressRule as Ingress Resource
    participant Service as Service
    participant Pod as Pod
    
    User->>Ingress: HTTP Request
    Ingress->>IngressRule: Match Rule
    IngressRule->>Service: Route to Service
    Service->>Pod: Load Balance
    Pod->>Service: Response
    Service->>Ingress: Response
    Ingress->>User: HTTP Response
```

## Storage Interactions

### Persistent Volume Flow

```mermaid
sequenceDiagram
    participant Pod as Pod
    participant PVC as PVC
    participant PV as PV
    participant StorageClass as StorageClass
    participant Provisioner as Provisioner
    participant Storage as Storage Backend
    
    Pod->>PVC: Request Storage
    PVC->>StorageClass: Get Storage Class
    StorageClass->>Provisioner: Provision Volume
    Provisioner->>Storage: Create Volume
    Storage-->>Provisioner: Volume Created
    Provisioner->>PV: Create PV
    PV->>PVC: Bind to PVC
    PVC->>Pod: Mount Volume
    Pod->>PV: Access Storage
    PV->>Storage: Read/Write
```

## Scheduler Interactions

### Pod Scheduling Flow

```mermaid
sequenceDiagram
    participant API as API Server
    participant etcd as etcd
    participant Scheduler as Scheduler
    participant Node1 as Node 1
    participant Node2 as Node 2
    participant Node3 as Node 3
    
    API->>etcd: Store Pod (Pending)
    etcd->>Scheduler: Pod Pending Event
    Scheduler->>Scheduler: Filter Nodes
    Scheduler->>Node1: Check Resources
    Node1-->>Scheduler: Available
    Scheduler->>Node2: Check Resources
    Node2-->>Scheduler: Available
    Scheduler->>Node3: Check Resources
    Node3-->>Scheduler: Insufficient
    Scheduler->>Scheduler: Score Nodes
    Scheduler->>API: Bind to Node 2
    API->>etcd: Update Pod
    etcd->>Node2: Pod Assignment
```

## Health Check Interactions

### Liveness and Readiness Probes

```mermaid
sequenceDiagram
    participant Kubelet as Kubelet
    participant Probe as Health Probe
    participant Container as Container
    participant API as API Server
    
    loop Liveness Probe
        Kubelet->>Probe: Execute Liveness
        Probe->>Container: Check Health
        Container-->>Probe: Response
        alt Unhealthy
            Probe-->>Kubelet: Failure
            Kubelet->>Container: Restart Container
            Kubelet->>API: Update Status
        end
    end
    
    loop Readiness Probe
        Kubelet->>Probe: Execute Readiness
        Probe->>Container: Check Ready
        Container-->>Probe: Response
        alt Not Ready
            Probe-->>Kubelet: Not Ready
            Kubelet->>API: Remove from Endpoints
        else Ready
            Probe-->>Kubelet: Ready
            Kubelet->>API: Add to Endpoints
        end
    end
```

## Autoscaling Interactions

### Horizontal Pod Autoscaler

```mermaid
sequenceDiagram
    participant HPA as HPA Controller
    participant Metrics as Metrics Server
    participant Deployment as Deployment
    participant ReplicaSet as ReplicaSet
    participant Pods as Pods
    
    loop Every Poll Interval
        HPA->>Metrics: Get Current Metrics
        Metrics-->>HPA: CPU/Memory Usage
        HPA->>HPA: Calculate Desired Replicas
        alt Scale Up
            HPA->>Deployment: Scale Up
            Deployment->>ReplicaSet: Increase Replicas
            ReplicaSet->>Pods: Create New Pods
        else Scale Down
            HPA->>Deployment: Scale Down
            Deployment->>ReplicaSet: Decrease Replicas
            ReplicaSet->>Pods: Delete Pods
        end
    end
```

## Security Interactions

### RBAC Flow

```mermaid
sequenceDiagram
    participant User as User
    participant API as API Server
    participant Auth as Authentication
    participant RBAC as RBAC Authorizer
    participant Role as Role/RoleBinding
    participant Resource as Resource
    
    User->>API: API Request
    API->>Auth: Authenticate
    Auth-->>API: User Identity
    API->>RBAC: Authorize Request
    RBAC->>Role: Check Permissions
    Role-->>RBAC: Allowed/Denied
    alt Allowed
        RBAC-->>API: Allow
        API->>Resource: Execute Request
    else Denied
        RBAC-->>API: Deny
        API-->>User: 403 Forbidden
    end
```

## Summary

Kubernetes components interact through well-defined patterns:

1. **Event-Driven**: Components react to changes in etcd
2. **Watch Loops**: Controllers watch resources and reconcile state
3. **API-Centric**: All interactions go through the API Server
4. **Declarative**: Desired state is declared, actual state is reconciled
5. **Asynchronous**: Many operations are asynchronous with status updates
6. **Layered**: Clear separation between control plane and data plane

Understanding these interaction patterns helps with:
- **Debugging**: Knowing which component to check when issues occur
- **Troubleshooting**: Tracing issues through the component flow
- **Architecture**: Designing applications that work well with Kubernetes
- **Operations**: Understanding how to monitor and maintain clusters

