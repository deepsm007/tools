# Prow Job Configuration Guide

This guide explains how to configure Prow jobs effectively.

## Job Types Overview

### Presubmit Jobs
Run when pull requests are created or updated. Used for validation before merging.

### Postsubmit Jobs
Run after code is merged to the main branch. Used for building artifacts and deployment.

### Periodic Jobs
Run on a schedule (cron). Used for maintenance, long-running tests, or regular builds.

## Basic Job Structure

### Minimal Presubmit Job

```yaml
presubmits:
  my-org/my-repo:
    - name: simple-test
      spec:
        containers:
        - image: alpine:latest
          command: ["echo", "Hello Prow"]
```

### Job with All Common Fields

```yaml
presubmits:
  my-org/my-repo:
    - name: comprehensive-job
      always_run: true
      optional: false
      skip_report: false
      max_concurrency: 5
      run_if_changed: '^src/.*'
      skip_if_only_changed: '^docs/.*'
      branches:
      - main
      - release-*
      labels:
        preset-service-account: "true"
      spec:
        containers:
        - image: my-image:latest
          command: ["./run-tests.sh"]
```

## Job Fields Explained

### always_run
Whether job runs on every PR, even if files don't match `run_if_changed`.

```yaml
always_run: true  # Run on every PR
always_run: false # Only run if conditions match
```

### optional
Whether job failure blocks PR merge.

```yaml
optional: false  # Failure blocks merge (default)
optional: true   # Failure doesn't block merge
```

### skip_report
Whether to report status back to GitHub.

```yaml
skip_report: false  # Report status (default)
skip_report: true   # Don't report status
```

### max_concurrency
Maximum number of instances of this job that can run simultaneously.

```yaml
max_concurrency: 1   # Run one at a time
max_concurrency: 10  # Allow up to 10 concurrent runs
```

### run_if_changed
Only run if files matching the regex pattern changed.

```yaml
run_if_changed: '^src/.*'        # Only if files in src/ changed
run_if_changed: '\.(go|java)$'   # Only if Go or Java files changed
```

### skip_if_only_changed
Skip job if only files matching pattern changed.

```yaml
skip_if_only_changed: '^docs/.*'  # Skip if only docs changed
```

### branches
Only run on PRs targeting these branches.

```yaml
branches:
- main
- release-*
- 'release-v\d+\.\d+'
```

### labels
Labels to apply to the ProwJob.

```yaml
labels:
  preset-service-account: "true"
  preset-dind-enabled: "true"
```

## Container Specification

### Basic Container

```yaml
spec:
  containers:
  - image: my-image:latest
    command: ["./script.sh"]
```

### Container with Arguments

```yaml
spec:
  containers:
  - image: my-image:latest
    command: ["/bin/bash"]
    args:
    - -c
    - |
      echo "Running tests"
      ./test.sh
```

### Container with Environment Variables

```yaml
spec:
  containers:
  - image: my-image:latest
    env:
    - name: ENV_VAR
      value: "value"
    - name: SECRET_VAR
      valueFrom:
        secretKeyRef:
          name: my-secret
          key: secret-key
```

### Container with Resource Limits

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

### Container with Volume Mounts

```yaml
spec:
  containers:
  - image: my-image:latest
    volumeMounts:
    - name: shared-data
      mountPath: /data
  volumes:
  - name: shared-data
    emptyDir: {}
```

## Advanced Job Patterns

### Multi-Container Job

```yaml
presubmits:
  my-org/my-repo:
    - name: integration-test
      spec:
        containers:
        - name: test-runner
          image: test-runner:latest
          command: ["./run-tests.sh"]
        - name: database
          image: postgres:13
          env:
          - name: POSTGRES_PASSWORD
            value: "test"
```

### Job with Service Account

```yaml
presubmits:
  my-org/my-repo:
    - name: gcp-deploy
      labels:
        preset-service-account: "true"
      spec:
        serviceAccountName: deployer
        containers:
        - image: gcr.io/cloud-builders/gcloud
          command: ["gcloud", "deploy"]
```

### Job with Timeout

```yaml
presubmits:
  my-org/my-repo:
    - name: long-test
      timeout: 2h
      spec:
        containers:
        - image: test-image:latest
          command: ["./long-test.sh"]
```

### Job with Retries

```yaml
presubmits:
  my-org/my-repo:
    - name: flaky-test
      max_concurrency: 1
      spec:
        containers:
        - image: test-image:latest
          command: ["./test.sh"]
      rerun_command: "/test flaky-test"
      rerun_auth_config:
        github_team_ids:
        - 123456
```

## Postsubmit Jobs

### Build and Push Image

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

### Deploy to Staging

```yaml
postsubmits:
  my-org/my-repo:
    - name: deploy-staging
      branches:
      - main
      spec:
        containers:
        - image: deployer:latest
          command: ["./deploy.sh", "staging"]
```

## Periodic Jobs

### Daily Job

```yaml
periodics:
  - name: daily-cleanup
    interval: 24h
    spec:
      containers:
      - image: cleanup:latest
        command: ["./cleanup.sh"]
```

### Cron-Based Job

```yaml
periodics:
  - name: weekly-report
    cron: "0 0 * * 0"  # Every Sunday at midnight
    spec:
      containers:
      - image: report-generator:latest
        command: ["./generate-report.sh"]
```

### Periodic with Branch Context

```yaml
periodics:
  - name: nightly-tests
    interval: 24h
    extra_refs:
    - org: my-org
      repo: my-repo
      base_ref: main
    spec:
      containers:
      - image: test-image:latest
        command: ["./run-tests.sh"]
```

## Job Presets

### Using Presets

```yaml
presets:
- labels:
    preset-service-account: "true"
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

### Applying Presets to Jobs

```yaml
presubmits:
  my-org/my-repo:
    - name: gcp-job
      labels:
        preset-service-account: "true"
      spec:
        containers:
        - image: my-image:latest
```

## Decoration (Artifacts and Logs)

### Enable Decoration

```yaml
presubmits:
  my-org/my-repo:
    - name: decorated-job
      decorate: true
      spec:
        containers:
        - image: my-image:latest
          command: ["./test.sh"]
```

### Custom Decoration

```yaml
presubmits:
  my-org/my-repo:
    - name: custom-decorated
      decorate: true
      decoration_config:
        timeout: 1h
        grace_period: 10m
        utility_images:
          clonerefs: gcr.io/k8s-prow/clonerefs:latest
          initupload: gcr.io/k8s-prow/initupload:latest
          entrypoint: gcr.io/k8s-prow/entrypoint:latest
          sidecar: gcr.io/k8s-prow/sidecar:latest
      spec:
        containers:
        - image: my-image:latest
```

## Job Dependencies

### Sequential Jobs

```yaml
presubmits:
  my-org/my-repo:
    - name: build
      always_run: true
      spec:
        containers:
        - image: builder:latest
          command: ["./build.sh"]
    - name: test
      run_after_success:
      - build
      spec:
        containers:
        - image: tester:latest
          command: ["./test.sh"]
```

## Cluster Selection

### Multi-Cluster Configuration

```yaml
# config.yaml
cluster_config:
  default: default-cluster
  build-cluster: build-cluster
  test-cluster: test-cluster
```

### Job-Specific Cluster

```yaml
presubmits:
  my-org/my-repo:
    - name: gpu-test
      cluster: gpu-cluster
      spec:
        containers:
        - image: gpu-test:latest
```

## Best Practices

### 1. Use Descriptive Names

```yaml
# Good
- name: unit-tests
- name: integration-tests
- name: build-docker-image

# Bad
- name: test1
- name: job
- name: run
```

### 2. Set Appropriate Concurrency

```yaml
# For resource-intensive jobs
max_concurrency: 1

# For lightweight jobs
max_concurrency: 10
```

### 3. Use run_if_changed Wisely

```yaml
# Only run when relevant files change
run_if_changed: '^src/.*\.(go|java)$'
```

### 4. Set Resource Limits

```yaml
resources:
  requests:
    cpu: "1"
    memory: "2Gi"
  limits:
    cpu: "2"
    memory: "4Gi"
```

### 5. Use Presets for Common Configurations

```yaml
# Define once, reuse many times
labels:
  preset-service-account: "true"
  preset-dind-enabled: "true"
```

## Configuration File Structure

```
config/
├── config.yaml          # Main config
├── plugins.yaml         # Plugin config
├── jobs/
│   ├── my-org/
│   │   └── my-repo/
│   │       └── jobs.yaml
└── cluster.yaml         # Cluster config
```

## Validation

### Validate Configuration

```bash
# Using checkconfig tool
go run ./prow/cmd/checkconfig \
  --config-path=config.yaml \
  --job-config-path=jobs/
```

### Common Validation Errors

1. **Invalid YAML syntax**
2. **Missing required fields**
3. **Invalid image references**
4. **Circular job dependencies**
5. **Invalid regex patterns**

## Additional Resources

- [Prow Job Documentation](https://docs.prow.k8s.io/docs/jobs/)
- [Example Configurations](https://github.com/kubernetes/test-infra/tree/master/config)
- [Job Presets](https://docs.prow.k8s.io/docs/jobs/#job-presets)

