# Prow Usage Guide

This guide provides practical examples for using Prow effectively.

## Basic Operations

### Triggering Jobs via Comments

```bash
# Trigger a specific job
/test job-name

# Retest all failed jobs
/retest

# Retest a specific job
/retest job-name

# Test all jobs
/test all
```

### Checking Job Status

```bash
# View job status in GitHub PR
# Status checks appear automatically in the PR

# View jobs in Deck (Web UI)
# Navigate to: https://your-prow-deck-url/job-history?repo=my-org%2Fmy-repo
```

### Viewing Job Logs

```bash
# Via Deck UI
# Click on job name → View logs

# Via kubectl
kubectl get pods -n prow
kubectl logs <pod-name> -n prow

# Via Spyglass (in Deck)
# Click on job → View in Spyglass
```

## Job Configuration Examples

### Simple Presubmit Job

```yaml
presubmits:
  my-org/my-repo:
    - name: unit-tests
      always_run: true
      skip_report: false
      spec:
        containers:
        - image: golang:1.19
          command:
          - /bin/bash
          args:
          - -c
          - |
            go test ./...
```

### Postsubmit Job

```yaml
postsubmits:
  my-org/my-repo:
    - name: build-image
      spec:
        containers:
        - image: gcr.io/cloud-builders/docker
          command:
          - /bin/bash
          args:
          - -c
          - |
            docker build -t my-image:$PULL_BASE_SHA .
            docker push my-image:$PULL_BASE_SHA
```

### Periodic Job

```yaml
periodics:
  - name: nightly-tests
    interval: 24h
    spec:
      containers:
      - image: my-test-image:latest
        command:
        - /bin/bash
        args:
        - -c
        - |
          ./run-e2e-tests.sh
```

### Job with Multiple Containers

```yaml
presubmits:
  my-org/my-repo:
    - name: integration-tests
      spec:
        containers:
        - name: test-runner
          image: test-runner:latest
          command: ["/bin/sh", "-c"]
          args: ["./run-tests.sh"]
        - name: database
          image: postgres:13
          env:
          - name: POSTGRES_PASSWORD
            value: "test"
```

### Job with Secrets

```yaml
presubmits:
  my-org/my-repo:
    - name: deploy-staging
      spec:
        containers:
        - image: deployer:latest
          env:
          - name: API_KEY
            valueFrom:
              secretKeyRef:
                name: api-key-secret
                key: api-key
```

## Plugin Usage

### Approval Workflow

```bash
# Approve a PR
/approve

# Cancel approval
/approve cancel
```

### LGTM (Looks Good To Me)

```bash
# Mark PR as LGTM
/lgtm

# Remove LGTM
/lgtm cancel
```

### Hold and WIP

```bash
# Put PR on hold (prevents merging)
/hold

# Remove hold
/hold cancel

# Mark as work in progress
/wip

# Remove WIP
/wip cancel
```

### Help Command

```bash
# Get help with available commands
/help
```

## Advanced Usage

### Conditional Job Execution

```yaml
presubmits:
  my-org/my-repo:
    - name: e2e-tests
      run_if_changed: '^test/.*'
      spec:
        containers:
        - image: test-runner:latest
          command: ["./run-e2e.sh"]
```

### Job with Resource Limits

```yaml
presubmits:
  my-org/my-repo:
    - name: resource-intensive-test
      spec:
        containers:
        - image: test-image:latest
          resources:
            requests:
              cpu: "2"
              memory: "4Gi"
            limits:
              cpu: "4"
              memory: "8Gi"
```

### Job with Timeout

```yaml
presubmits:
  my-org/my-repo:
    - name: long-running-test
      max_concurrency: 1
      timeout: 2h
      spec:
        containers:
        - image: test-image:latest
          command: ["./long-test.sh"]
```

### Job with Environment Variables

```yaml
presubmits:
  my-org/my-repo:
    - name: test-with-env
      spec:
        containers:
        - image: test-image:latest
          env:
          - name: TEST_ENV
            value: "staging"
          - name: LOG_LEVEL
            value: "debug"
          command: ["./test.sh"]
```

### Job with Artifact Upload

```yaml
presubmits:
  my-org/my-repo:
    - name: build-and-upload
      spec:
        containers:
        - image: builder:latest
          command:
          - /bin/bash
          args:
          - -c
          - |
            make build
            gsutil cp artifacts/* gs://my-bucket/artifacts/
          env:
          - name: GOOGLE_APPLICATION_CREDENTIALS
            value: /etc/service-account/service-account.json
          volumeMounts:
          - name: service-account
            mountPath: /etc/service-account
        volumes:
        - name: service-account
          secret:
            secretName: gcp-service-account
```

## Tide Configuration

### Basic Tide Config

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

### Merge Requirements

```yaml
tide:
  merge_method:
    my-org/my-repo: squash
  required_status_checks:
    my-org/my-repo:
      contexts:
      - unit-tests
      - integration-tests
```

## Deck (Web UI) Usage

### Viewing Job History

1. Navigate to Deck URL
2. Select repository from dropdown
3. View job history and status
4. Click on job to see details

### Viewing Logs in Spyglass

1. Click on a job in Deck
2. Select "Spyglass" view
3. Browse logs, artifacts, and metadata
4. Use filters to find specific information

### Searching Jobs

1. Use search bar in Deck
2. Filter by:
   - Repository
   - Job name
   - Status
   - Time range

## Common Workflows

### Standard PR Workflow

1. Developer creates PR
2. Presubmit jobs run automatically
3. Developer reviews status checks
4. If tests fail, fix and push
5. Use `/retest` to rerun tests
6. Get approvals (`/lgtm`, `/approve`)
7. Tide automatically merges when ready

### Manual Job Triggering

```bash
# Trigger specific job
/test integration-tests

# Check status
# View in GitHub PR or Deck UI

# View logs if needed
kubectl logs <pod-name> -n prow
```

### Debugging Failed Jobs

```bash
# 1. Check job status
kubectl get prowjob <job-name> -n prow

# 2. Check pod status
kubectl get pods -n prow | grep <job-name>

# 3. View pod logs
kubectl logs <pod-name> -n prow

# 4. Describe pod for events
kubectl describe pod <pod-name> -n prow

# 5. Check job configuration
kubectl get configmap config -n prow -o yaml
```

### Monitoring Job Performance

```bash
# View all running jobs
kubectl get prowjobs -n prow

# View job metrics (if Prometheus configured)
# Query: prow_job_state{state="pending"}
# Query: prow_job_state{state="running"}
# Query: prow_job_state{state="success"}
# Query: prow_job_state{state="failure"}
```

## Best Practices

### Job Naming

- Use descriptive names: `unit-tests`, `integration-tests`, `build-image`
- Include component name if needed: `frontend-tests`, `backend-tests`
- Use consistent naming across repos

### Job Organization

- Group related jobs together
- Use `always_run` for critical jobs
- Use `run_if_changed` for optional jobs
- Set appropriate `max_concurrency`

### Resource Management

- Set resource requests and limits
- Use appropriate timeouts
- Clean up artifacts after jobs
- Monitor resource usage

### Error Handling

- Make jobs idempotent when possible
- Include proper error messages
- Upload logs and artifacts
- Set up alerts for failures

## Troubleshooting

### Job Not Running

```bash
# Check ProwJob was created
kubectl get prowjob -n prow

# Check Plank is running
kubectl get pods -n prow -l app=plank

# Check Plank logs
kubectl logs -n prow -l app=plank --tail=100
```

### Status Not Reported

```bash
# Check Crier is running
kubectl get pods -n prow -l app=crier

# Check Crier logs
kubectl logs -n prow -l app=crier --tail=100

# Verify GitHub token
kubectl get secret github-token -n prow
```

### Webhook Not Received

```bash
# Check Hook is running
kubectl get pods -n prow -l app=hook

# Check Hook logs
kubectl logs -n prow -l app=hook --tail=100

# Test webhook manually
curl -X POST http://hook-url/hook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -d '{"zen":"test"}'
```

## Additional Resources

- [Prow Job Configuration](https://docs.prow.k8s.io/docs/jobs/)
- [Prow Plugins](https://docs.prow.k8s.io/docs/plugins/)
- [Tide Configuration](https://docs.prow.k8s.io/docs/components/core/tide/)

