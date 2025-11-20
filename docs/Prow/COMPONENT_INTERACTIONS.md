# Prow Component Interactions Guide

This guide explains how Prow components interact with each other and how to understand these interactions.

## Core Component Interactions

### Webhook Processing Flow

```mermaid
sequenceDiagram
    participant GitHub as GitHub/GitLab
    participant Hook as Hook
    participant Plugin as Plugin System
    participant Controller as Controller Manager
    participant Plank as Plank
    participant K8s as Kubernetes
    participant Crier as Crier
    
    GitHub->>Hook: Webhook Event (PR created/updated)
    Hook->>Hook: Validate Webhook
    Hook->>Plugin: Process Event
    Plugin->>Plugin: Check Plugin Config
    Plugin->>Controller: Create ProwJob (if needed)
    Controller->>Controller: Create ProwJob CRD
    Controller->>Plank: ProwJob Created Event
    Plank->>K8s: Create Pod for Job
    K8s->>K8s: Execute Job
    K8s->>Plank: Job Status Update
    Plank->>Controller: Update ProwJob Status
    Controller->>Crier: Job Completed Event
    Crier->>GitHub: Update Status Check
```

### Job Execution Flow

```mermaid
graph TB
    subgraph "Event Source"
        PR[Pull Request Event]
        Comment[PR Comment]
        Schedule[Cron Schedule]
    end
    
    subgraph "Prow Entry Point"
        Hook[Hook<br/>Webhook Receiver]
    end
    
    subgraph "Job Orchestration"
        Controller[Controller Manager<br/>Creates ProwJobs]
        Plank[Plank<br/>Executes Jobs]
    end
    
    subgraph "Kubernetes"
        ProwJob[ProwJob CRD]
        Pod[Job Pod]
    end
    
    subgraph "Status Reporting"
        Crier[Crier<br/>Status Reporter]
        GitHub[GitHub Status]
    end
    
    PR --> Hook
    Comment --> Hook
    Schedule --> Controller
    
    Hook --> Controller
    Controller --> ProwJob
    ProwJob --> Plank
    Plank --> Pod
    Pod --> Plank
    Plank --> Crier
    Crier --> GitHub
```

### Tide Merge Flow

```mermaid
sequenceDiagram
    participant Tide as Tide
    participant GitHub as GitHub API
    participant Controller as Controller Manager
    participant Crier as Crier
    
    loop Every Poll Interval
        Tide->>GitHub: Query Open PRs
        GitHub-->>Tide: List of PRs
        Tide->>Tide: Evaluate Each PR
        
        alt PR Meets Merge Criteria
            Tide->>Tide: Check Status Checks
            Tide->>Tide: Check Labels
            Tide->>Tide: Check Conflicts
            Tide->>GitHub: Merge PR
            GitHub-->>Tide: Merge Success
            Tide->>Controller: Trigger Postsubmit Jobs
        else PR Not Ready
            Tide->>Tide: Log Reason
        end
    end
```

## Component Communication Patterns

### Hook to Controller Communication

```mermaid
graph LR
    subgraph "Hook Component"
        HookWebhook[Webhook Handler]
        HookPlugin[Plugin Handler]
    end
    
    subgraph "Controller Manager"
        ControllerAPI[API Server]
        ControllerReconcile[Reconciler]
    end
    
    subgraph "Kubernetes API"
        K8sAPI[Kubernetes API]
        ProwJobCRD[ProwJob CRD]
    end
    
    HookWebhook --> HookPlugin
    HookPlugin --> ControllerAPI
    ControllerAPI --> K8sAPI
    K8sAPI --> ProwJobCRD
    ProwJobCRD --> ControllerReconcile
```

### Plank Job Execution

```mermaid
graph TB
    subgraph "Plank Component"
        PlankWatch[Watch ProwJobs]
        PlankCreate[Create Pods]
        PlankUpdate[Update Status]
    end
    
    subgraph "Kubernetes Cluster"
        ProwJob[ProwJob Resource]
        JobPod[Job Pod]
        PodStatus[Pod Status]
    end
    
    subgraph "Storage"
        GCS[GCS/S3<br/>Artifacts]
        Logs[Log Storage]
    end
    
    PlankWatch --> ProwJob
    ProwJob --> PlankCreate
    PlankCreate --> JobPod
    JobPod --> PodStatus
    PodStatus --> PlankUpdate
    JobPod --> GCS
    JobPod --> Logs
```

### Crier Status Reporting

```mermaid
sequenceDiagram
    participant Controller as Controller Manager
    participant Crier as Crier
    participant GitHub as GitHub API
    participant GitLab as GitLab API
    participant Slack as Slack API
    
    Controller->>Crier: ProwJob Status Change
    Crier->>Crier: Determine Reporters
    
    alt GitHub Job
        Crier->>GitHub: Update Status Check
        Crier->>GitHub: Post Comment (optional)
    else GitLab Job
        Crier->>GitLab: Update Pipeline Status
    end
    
    alt Slack Notification Enabled
        Crier->>Slack: Send Notification
    end
```

## Plugin System Interactions

### Plugin Command Processing

```mermaid
graph TB
    subgraph "GitHub Event"
        Comment[PR Comment<br/>/test job-name]
    end
    
    subgraph "Hook Component"
        HookReceive[Receive Webhook]
        HookParse[Parse Comment]
        HookPlugin[Plugin Handler]
    end
    
    subgraph "Plugin System"
        PluginConfig[Plugin Config<br/>Check Permissions]
        PluginAction[Execute Action]
    end
    
    subgraph "Actions"
        TriggerJob[Trigger Job]
        AddLabel[Add Label]
        ApprovePR[Approve PR]
    end
    
    Comment --> HookReceive
    HookReceive --> HookParse
    HookParse --> HookPlugin
    HookPlugin --> PluginConfig
    PluginConfig --> PluginAction
    PluginAction --> TriggerJob
    PluginAction --> AddLabel
    PluginAction --> ApprovePR
```

### Common Plugin Commands Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant GitHub as GitHub
    participant Hook as Hook
    participant Plugin as Plugin System
    participant Controller as Controller Manager
    
    Dev->>GitHub: Comment "/test unit-tests"
    GitHub->>Hook: Webhook (issue_comment)
    Hook->>Hook: Validate Comment
    Hook->>Plugin: Process Command
    Plugin->>Plugin: Check User Permissions
    Plugin->>Plugin: Validate Job Name
    Plugin->>Controller: Create ProwJob
    Controller->>Controller: Schedule Job
    Note over Controller: Job executes...
    Controller->>GitHub: Update Status Check
    GitHub->>Dev: Show Status in PR
```

## Sinker Cleanup Flow

```mermaid
graph TB
    subgraph "Sinker Component"
        SinkerWatch[Watch ProwJobs]
        SinkerCheck[Check Age]
        SinkerDelete[Delete Old Jobs]
    end
    
    subgraph "Kubernetes"
        OldProwJob[Old ProwJob<br/>Completed > TTL]
        OldPod[Old Pod<br/>Completed]
    end
    
    subgraph "Storage"
        Artifacts[Artifacts<br/>Retained]
    end
    
    SinkerWatch --> OldProwJob
    SinkerCheck --> OldProwJob
    alt Job Older Than TTL
        SinkerDelete --> OldProwJob
        SinkerDelete --> OldPod
    end
    OldProwJob -.-> Artifacts
```

## Deck (Web UI) Interactions

```mermaid
graph TB
    subgraph "User Browser"
        User[User]
    end
    
    subgraph "Deck Component"
        DeckUI[Web UI]
        DeckAPI[API Handler]
    end
    
    subgraph "Backend Services"
        K8sAPI[Kubernetes API<br/>ProwJob Status]
        GCS[GCS/S3<br/>Logs & Artifacts]
        GitHubAPI[GitHub API<br/>PR Info]
    end
    
    User --> DeckUI
    DeckUI --> DeckAPI
    DeckAPI --> K8sAPI
    DeckAPI --> GCS
    DeckAPI --> GitHubAPI
    K8sAPI --> DeckAPI
    GCS --> DeckAPI
    GitHubAPI --> DeckAPI
    DeckAPI --> DeckUI
    DeckUI --> User
```

## Configuration Flow

```mermaid
graph TB
    subgraph "Configuration Source"
        GitRepo[Git Repository<br/>Config Files]
    end
    
    subgraph "Prow Components"
        ConfigMap[ConfigMap<br/>Job Config]
        PluginConfigMap[ConfigMap<br/>Plugin Config]
    end
    
    subgraph "Component Usage"
        Hook[Hook<br/>Reads Plugin Config]
        Controller[Controller<br/>Reads Job Config]
        Tide[Tide<br/>Reads Job Config]
    end
    
    GitRepo --> ConfigMap
    GitRepo --> PluginConfigMap
    ConfigMap --> Controller
    ConfigMap --> Tide
    PluginConfigMap --> Hook
```

## Error Handling and Retry Logic

### Job Failure Flow

```mermaid
sequenceDiagram
    participant Pod as Job Pod
    participant Plank as Plank
    participant Controller as Controller Manager
    participant Crier as Crier
    participant GitHub as GitHub
    
    Pod->>Pod: Job Fails
    Pod->>Plank: Status: Failed
    Plank->>Controller: Update ProwJob Status
    Controller->>Crier: Job Failed Event
    Crier->>GitHub: Update Status: Failure
    Crier->>GitHub: Post Failure Comment (optional)
    GitHub->>GitHub: Update PR Status
```

### Retry Logic

```mermaid
graph TB
    subgraph "Job Execution"
        JobRun[Job Runs]
        JobResult{Job Result}
    end
    
    subgraph "Retry Logic"
        CheckRetry{Retry<br/>Configured?}
        CheckAttempts{Attempts<br/>< Max?}
        IncrementAttempt[Increment Attempt]
    end
    
    subgraph "Final State"
        Success[Mark Success]
        Failure[Mark Failure]
    end
    
    JobRun --> JobResult
    JobResult -->|Success| Success
    JobResult -->|Failure| CheckRetry
    CheckRetry -->|Yes| CheckAttempts
    CheckAttempts -->|Yes| IncrementAttempt
    IncrementAttempt --> JobRun
    CheckAttempts -->|No| Failure
    CheckRetry -->|No| Failure
```

## Multi-Cluster Interactions

```mermaid
graph TB
    subgraph "Prow Control Plane"
        Hook[Hook]
        Controller[Controller Manager]
    end
    
    subgraph "Cluster Configuration"
        ClusterConfig[Cluster Config<br/>Multiple Clusters]
    end
    
    subgraph "Execution Clusters"
        Cluster1[Cluster 1<br/>Presubmit Jobs]
        Cluster2[Cluster 2<br/>Postsubmit Jobs]
        Cluster3[Cluster 3<br/>Periodic Jobs]
    end
    
    Hook --> Controller
    Controller --> ClusterConfig
    ClusterConfig --> Cluster1
    ClusterConfig --> Cluster2
    ClusterConfig --> Cluster3
```

## Security and Authentication Flow

```mermaid
sequenceDiagram
    participant User as User/Developer
    participant GitHub as GitHub
    participant Hook as Hook
    participant OAuth as OAuth System
    participant RBAC as RBAC
    participant Plugin as Plugin System
    
    User->>GitHub: Comment "/test job-name"
    GitHub->>Hook: Webhook (authenticated)
    Hook->>OAuth: Verify GitHub Token
    OAuth-->>Hook: Token Valid
    Hook->>RBAC: Check User Permissions
    RBAC-->>Hook: Permission Granted
    Hook->>Plugin: Process Command
    Plugin->>Plugin: Execute Action
```

## Summary

Prow components interact through well-defined patterns:

1. **Event-Driven**: Components react to events (webhooks, Kubernetes events, schedules)
2. **Kubernetes-Native**: Uses Kubernetes APIs and CRDs for job management
3. **Stateless Components**: Most components are stateless and can scale horizontally
4. **Configuration-Driven**: Behavior controlled through YAML configuration files
5. **Async Processing**: Jobs execute asynchronously with status reporting
6. **Clean Separation**: Clear separation between orchestration (Controller), execution (Plank), and reporting (Crier)

Understanding these interaction patterns helps with:
- **Debugging**: Knowing which component to check when issues occur
- **Configuration**: Understanding how configuration affects component behavior
- **Troubleshooting**: Tracing issues through the component flow
- **Extension**: Adding custom components or modifying behavior

