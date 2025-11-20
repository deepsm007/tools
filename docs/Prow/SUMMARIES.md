# Prow Technical Summaries

Summaries of Prow at different technical levels.

## Non-Technical Summary

**What is Prow?**
Prow is an automated testing and code review system used by software development teams. When a developer submits code changes, Prow automatically runs tests to make sure the code works correctly. It also helps manage the code review process and can automatically merge code when everything is approved and tested.

**How does it help?**
- Automatically tests code changes before they're merged
- Provides clear feedback to developers about test results
- Helps maintain code quality by ensuring all changes are tested
- Reduces manual work in the code review process

**Who uses it?**
Primarily used by large open-source projects (like Kubernetes) and organizations that need to test many code changes efficiently.

## Intermediate Technical Summary

**What is Prow?**
Prow is a Kubernetes-based CI/CD system that automates testing, code review, and deployment workflows. It integrates with GitHub and GitLab to provide automated testing on pull requests, status reporting, and automated merge management.

**Key Components:**
- **Hook**: Receives webhooks from GitHub/GitLab when events occur (PR created, comment added, etc.)
- **Controller Manager**: Orchestrates jobs by creating ProwJob resources
- **Plank**: Executes jobs by creating Kubernetes pods
- **Crier**: Reports job status back to GitHub/GitLab
- **Tide**: Automatically merges PRs when all conditions are met
- **Deck**: Web UI for viewing jobs and logs

**Job Types:**
- **Presubmit**: Run on pull requests before merging (validation)
- **Postsubmit**: Run after code is merged (build artifacts, deploy)
- **Periodic**: Run on a schedule (maintenance, long tests)

**How it works:**
1. Developer creates PR → GitHub sends webhook to Prow
2. Hook processes event and triggers appropriate jobs
3. Controller creates ProwJob resources
4. Plank creates Kubernetes pods to run jobs
5. Jobs execute and produce results
6. Crier reports status back to GitHub
7. Tide evaluates PR and merges when ready

**Configuration:**
- Jobs defined in YAML files
- Configuration stored in Git repository
- Updates via ConfigMaps in Kubernetes

## Advanced Technical Summary

**Architecture:**
Prow is a distributed, event-driven CI/CD system built on Kubernetes. It uses Kubernetes Custom Resource Definitions (ProwJob CRD) to represent jobs and leverages Kubernetes for job execution and resource management.

**Component Architecture:**

1. **Hook (Webhook Receiver)**
   - Receives GitHub/GitLab webhooks
   - Validates HMAC signatures
   - Processes events through plugin system
   - Creates ProwJob resources via Controller Manager

2. **Controller Manager**
   - Watches for ProwJob resources
   - Manages ProwJob lifecycle
   - Coordinates with Plank for execution
   - Handles job state transitions

3. **Plank**
   - Watches for ProwJob resources in "triggered" state
   - Creates Kubernetes pods for job execution
   - Monitors pod status
   - Updates ProwJob status based on pod results

4. **Crier**
   - Watches for ProwJob status changes
   - Reports status to GitHub/GitLab via API
   - Supports multiple reporters (GitHub, GitLab, Slack)
   - Handles retries and error cases

5. **Sinker**
   - Periodically scans for completed ProwJobs
   - Deletes ProwJobs and pods older than TTL
   - Prevents resource accumulation
   - Configurable retention policies

6. **Tide**
   - Periodically queries GitHub for open PRs
   - Evaluates PRs against merge criteria
   - Checks status checks, labels, conflicts
   - Performs batch merges when possible

7. **Deck (Web UI)**
   - Provides web interface for job viewing
   - Integrates with Spyglass for log viewing
   - Shows job history and status
   - Allows searching and filtering

**Job Execution Flow:**

```
GitHub Webhook → Hook → Plugin System → Controller Manager
    ↓
ProwJob CRD Created
    ↓
Plank Watches ProwJob
    ↓
Kubernetes Pod Created
    ↓
Job Executes
    ↓
Results Uploaded to GCS/S3
    ↓
Crier Reports Status
    ↓
GitHub Status Updated
```

**Configuration Management:**

- **config.yaml**: Main configuration (GitHub orgs, clusters, deck settings)
- **plugins.yaml**: Plugin configuration (which plugins enabled, permissions)
- **jobs/**: Job definitions organized by org/repo
- **cluster.yaml**: Kubernetes cluster configurations

Configuration is stored in Git and loaded via ConfigMaps. Components watch ConfigMaps for changes and reload configuration dynamically.

**Plugin System:**

Plugins extend Prow functionality:
- Process PR comments (`/test`, `/approve`, `/lgtm`)
- Manage labels automatically
- Trigger jobs based on events
- Enforce policies

Plugins are configured per repository and can have permission restrictions.

**Multi-Cluster Support:**

Prow can execute jobs across multiple Kubernetes clusters:
- Different clusters for different job types
- Cluster selection based on job configuration
- Resource isolation and optimization

**Security:**

- OAuth integration for GitHub authentication
- RBAC for Kubernetes resource access
- HMAC validation for webhooks
- Secret management via Kubernetes secrets
- Audit logging for all actions

**Scalability:**

- Horizontal scaling of components (Hook, Deck)
- Kubernetes-native job execution
- Efficient resource cleanup (Sinker)
- Configurable concurrency limits
- Support for large numbers of concurrent jobs

**Monitoring:**

- Prometheus metrics for all components
- Centralized logging
- Distributed tracing support
- Alerting for failures

**Best Practices:**

1. Use `run_if_changed` to optimize job execution
2. Set appropriate `max_concurrency` limits
3. Use resource requests and limits
4. Configure Sinker TTL appropriately
5. Use presets for common configurations
6. Monitor job performance and resource usage
7. Set up alerts for failures

**Integration Points:**

- **GitHub/GitLab**: Webhooks, status checks, PR management
- **Kubernetes**: Job execution, resource management
- **Cloud Storage**: Artifact storage (GCS, S3)
- **Monitoring**: Prometheus, logging systems
- **Notifications**: Slack, email

**Extension Points:**

- Custom plugins for repository-specific logic
- Custom job types via ProwJob CRD
- Integration with external systems via webhooks
- Custom reporters for status reporting

**Performance Considerations:**

- Job execution time depends on cluster resources
- Webhook processing is asynchronous
- Status reporting has retry logic
- Sinker prevents resource leaks
- Deck UI performance scales with job volume

**Common Patterns:**

1. **Validation Pipeline**: Presubmit jobs for quick feedback
2. **Build Pipeline**: Postsubmit jobs for artifact creation
3. **Maintenance Tasks**: Periodic jobs for cleanup and testing
4. **Multi-Stage Workflows**: Jobs that depend on other jobs
5. **Conditional Execution**: Jobs that run based on file changes

This architecture makes Prow highly scalable, flexible, and suitable for large-scale CI/CD needs while maintaining simplicity for common use cases.

