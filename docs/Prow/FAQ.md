# Prow FAQ

Frequently asked questions about Prow, its components, and how to work with them.

## General Questions

### What is Prow?

Prow is a Kubernetes-based CI/CD system that automates testing, code review, and deployment workflows. It integrates with GitHub and GitLab to provide automated testing, status reporting, and merge management.

### How does Prow differ from other CI/CD systems?

Prow is:
- **Kubernetes-native**: Built specifically for Kubernetes, uses Kubernetes APIs and CRDs
- **GitHub/GitLab focused**: Deep integration with code hosting platforms
- **Scalable**: Leverages Kubernetes for automatic scaling
- **Flexible**: Highly configurable through YAML files
- **Open source**: Part of the Kubernetes project

### What are the main components of Prow?

- **Hook**: Receives webhooks from GitHub/GitLab
- **Controller Manager**: Orchestrates ProwJobs
- **Plank**: Executes jobs by creating Kubernetes pods
- **Crier**: Reports job status back to GitHub/GitLab
- **Sinker**: Cleans up old completed jobs
- **Tide**: Automatically merges PRs when ready
- **Deck**: Web UI for viewing jobs and logs

## Job Questions

### What types of jobs does Prow support?

1. **Presubmit**: Run on pull requests before merging
2. **Postsubmit**: Run after code is merged
3. **Periodic**: Run on a schedule (cron)

### How do I trigger a job manually?

Comment on a PR:
- `/test job-name` - Run a specific job
- `/retest` - Retry all failed jobs
- `/test all` - Run all jobs

### Why isn't my job running?

Check:
1. Is the job configured correctly in job config?
2. Is Plank running? (`kubectl get pods -n prow -l app=plank`)
3. Was a ProwJob created? (`kubectl get prowjobs -n prow`)
4. Check Plank logs for errors

### How do I view job logs?

1. **Via Deck UI**: Navigate to job and click "View Logs"
2. **Via kubectl**: `kubectl logs <pod-name> -n prow`
3. **Via Spyglass**: In Deck, click job → Spyglass view

### How do I configure a job to run only when certain files change?

Use `run_if_changed`:

```yaml
presubmits:
  my-org/my-repo:
    - name: my-job
      run_if_changed: '^src/.*\.go$'
      spec:
        containers:
        - image: my-image:latest
```

### How do I set resource limits for a job?

```yaml
spec:
  containers:
  - image: my-image:latest
    resources:
      requests:
        cpu: "1"
        memory: "2Gi"
      limits:
        cpu: "2"
        memory: "4Gi"
```

## Configuration Questions

### Where are Prow configuration files stored?

Typically in a Git repository:
```
config/
├── config.yaml      # Main config
├── plugins.yaml     # Plugin config
└── jobs/            # Job definitions
```

### How do I update job configuration?

1. Edit YAML files in the config repository
2. Commit and push changes
3. Update ConfigMaps in Kubernetes:
   ```bash
   kubectl create configmap config \
     --from-file=config.yaml \
     --from-file=jobs \
     --namespace=prow \
     --dry-run=client -o yaml | kubectl apply -f -
   ```

### How do I add a new job?

1. Add job definition to appropriate file in `jobs/` directory
2. Follow the job configuration format
3. Update ConfigMap (see above)
4. Jobs will be available immediately

## Plugin Questions

### What plugins are available?

Common plugins:
- `approve` - Handle `/approve` command
- `lgtm` - Handle `/lgtm` command
- `trigger` - Handle `/test`, `/retest` commands
- `welcome` - Welcome new contributors
- `help` - Provide help information
- `hold` - Prevent merging with `/hold`
- `wip` - Mark PR as work in progress

### How do I enable a plugin?

Add to `plugins.yaml`:

```yaml
plugins:
  my-org/my-repo:
    - approve
    - lgtm
    - trigger
```

### How do I restrict who can use a plugin?

Configure in `plugins.yaml`:

```yaml
plugins:
  my-org/my-repo:
    - approve
      lgtm_acts_as_approve: true
      require_self_approval: false
      issue_required: false
      # Restrict to specific teams
      owners_aliases:
        approvers:
        - my-team
```

## Tide Questions

### What is Tide?

Tide is Prow's merge bot that automatically merges pull requests when all conditions are met (tests pass, approvals, labels, etc.).

### How do I configure Tide?

In `config.yaml`:

```yaml
tide:
  queries:
  - repos:
    - my-org/my-repo
    labels:
    - lgtm
    - approved
    missingLabels:
    - do-not-merge
    - work-in-progress
```

### Why isn't my PR being merged by Tide?

Check:
1. Are all required status checks passing?
2. Are required labels present?
3. Are there merge conflicts?
4. Is PR blocked by `/hold`?
5. Check Tide logs: `kubectl logs -n prow -l app=tide`

## Webhook Questions

### How do I set up a webhook?

1. Go to GitHub repository → Settings → Webhooks
2. Add webhook with:
   - URL: `https://your-prow-hook-domain/hook`
   - Secret: HMAC token from Prow config
   - Events: Pull requests, Issue comments, etc.

### How do I test if webhooks are working?

```bash
# Port-forward to hook
kubectl port-forward -n prow svc/hook 8888:8888

# Test webhook
curl -X POST http://localhost:8888/hook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -d '{"zen":"test"}'
```

### Why aren't webhooks being received?

Check:
1. Webhook URL is correct
2. HMAC token matches
3. Hook pod is running: `kubectl get pods -n prow -l app=hook`
4. Hook logs: `kubectl logs -n prow -l app=hook`

## Status Reporting Questions

### Why isn't job status showing in GitHub?

Check:
1. Is Crier running? (`kubectl get pods -n prow -l app=crier`)
2. Is GitHub token valid?
3. Check Crier logs: `kubectl logs -n prow -l app=crier`
4. Verify job has `skip_report: false`

### How do I disable status reporting for a job?

```yaml
presubmits:
  my-org/my-repo:
    - name: my-job
      skip_report: true
      spec:
        containers:
        - image: my-image:latest
```

## Troubleshooting Questions

### How do I debug a failed job?

1. Check ProwJob status: `kubectl get prowjob <name> -n prow`
2. Check pod status: `kubectl get pods -n prow`
3. View pod logs: `kubectl logs <pod-name> -n prow`
4. Describe pod: `kubectl describe pod <pod-name> -n prow`

### How do I check if Prow components are healthy?

```bash
# Check all pods
kubectl get pods -n prow

# Check component logs
kubectl logs -n prow -l app=hook
kubectl logs -n prow -l app=plank
kubectl logs -n prow -l app=crier
kubectl logs -n prow -l app=tide
```

### Why are jobs stuck in pending?

Check:
1. Is Plank running?
2. Are there available resources in the cluster?
3. Check Plank logs for errors
4. Verify ProwJob was created correctly

## Security Questions

### How do I restrict who can trigger jobs?

Configure RBAC and plugin permissions:

```yaml
plugins:
  my-org/my-repo:
    trigger:
      trusted_org: my-org
      # Or specify teams
      owners_aliases:
        approvers:
        - my-team
```

### How do I use secrets in jobs?

Use Kubernetes secrets:

```yaml
spec:
  containers:
  - image: my-image:latest
    env:
    - name: SECRET_VAR
      valueFrom:
        secretKeyRef:
          name: my-secret
          key: secret-key
```

## Performance Questions

### How do I limit concurrent jobs?

Use `max_concurrency`:

```yaml
presubmits:
  my-org/my-repo:
    - name: my-job
      max_concurrency: 5
      spec:
        containers:
        - image: my-image:latest
```

### How do I clean up old jobs?

Sinker automatically cleans up old jobs. Configure TTL in job config or Sinker settings.

## Additional Resources

- [Prow Documentation](https://docs.prow.k8s.io/)
- [Prow GitHub Repository](https://github.com/kubernetes/test-infra/tree/master/prow)
- [Example Configurations](https://github.com/kubernetes/test-infra/tree/master/config)

