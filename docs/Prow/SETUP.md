# Prow Setup Guide

This guide provides step-by-step instructions for setting up Prow in your environment.

## Prerequisites

### Required Components

- **Kubernetes Cluster**: Version 1.19+ (for ProwJob CRD support)
- **kubectl**: Configured to access your Kubernetes cluster
- **GitHub/GitLab Account**: With appropriate permissions
- **Cloud Storage**: GCS bucket or S3 bucket for artifacts
- **Domain Name**: (Optional) For Deck web UI access

### Required Knowledge

- Basic Kubernetes concepts (pods, services, configmaps, secrets)
- YAML configuration
- Git and GitHub/GitLab workflows
- Basic understanding of CI/CD concepts

## Installation Methods

### Method 1: Using Prow Operator (Recommended)

The Prow Operator simplifies Prow installation and management.

```bash
# Install Prow Operator
kubectl apply -f https://raw.githubusercontent.com/kubernetes/test-infra/master/prow/cluster/prow_operator_deploy.yaml

# Wait for operator to be ready
kubectl wait --for=condition=ready pod -l app=prow-operator -n prow-system --timeout=300s
```

### Method 2: Manual Installation

Manual installation provides more control over the setup.

```bash
# Clone the test-infra repository
git clone https://github.com/kubernetes/test-infra.git
cd test-infra/prow/cluster

# Apply base components
kubectl apply -f starter.yaml
```

## Initial Configuration

### 1. Create Namespace

```bash
kubectl create namespace prow
```

### 2. Create GitHub Token Secret

```bash
# Create GitHub token
kubectl create secret generic github-token \
  --from-literal=oauth=YOUR_GITHUB_TOKEN \
  --namespace=prow
```

**Getting a GitHub Token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a token with `repo`, `admin:repo_hook`, and `admin:org_hook` permissions
3. Use the token in the secret above

### 3. Create HMAC Token Secret

```bash
# Generate HMAC token
openssl rand -hex 20

# Create secret
kubectl create secret generic hmac-token \
  --from-literal=hmac=GENERATED_HMAC_TOKEN \
  --namespace=prow
```

**Important**: Use the same HMAC token when configuring GitHub webhooks.

### 4. Configure GitHub Webhook

1. Go to your GitHub repository → Settings → Webhooks
2. Click "Add webhook"
3. Set Payload URL: `https://your-prow-hook-domain/hook`
4. Content type: `application/json`
5. Secret: Use the HMAC token from step 3
6. Events: Select "Let me select individual events"
   - Check: Pull requests, Issue comments, Pull request reviews, Pushes
7. Click "Add webhook"

### 5. Create Job Config

Create a basic job configuration file:

```yaml
# config/jobs/my-org/my-repo/jobs.yaml
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

### 6. Create Plugin Config

Create a plugin configuration file:

```yaml
# config/plugins.yaml
plugins:
  my-org/my-repo:
    - approve
    - lgtm
    - trigger
    - welcome
    - help
    - hold
    - wip
    - lifecycle
```

### 7. Create ConfigMaps

```bash
# Create job config ConfigMap
kubectl create configmap config \
  --from-file=config.yaml=path/to/config.yaml \
  --from-file=jobs=path/to/jobs \
  --namespace=prow

# Create plugin config ConfigMap
kubectl create configmap plugins \
  --from-file=plugins.yaml=path/to/plugins.yaml \
  --namespace=prow
```

## Component Deployment

### Deploy Hook

```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hook
  namespace: prow
spec:
  replicas: 2
  selector:
    matchLabels:
      app: hook
  template:
    metadata:
      labels:
        app: hook
    spec:
      containers:
      - name: hook
        image: gcr.io/k8s-prow/hook:v20231119-abc123
        args:
        - --dry-run=false
        - --github-token-path=/etc/github/oauth
        - --hmac-secret-file=/etc/hmac/hmac
        - --config-path=/etc/config/config.yaml
        - --plugin-config=/etc/plugins/plugins.yaml
        volumeMounts:
        - name: hmac
          mountPath: /etc/hmac
        - name: oauth
          mountPath: /etc/github
        - name: config
          mountPath: /etc/config
        - name: plugins
          mountPath: /etc/plugins
      volumes:
      - name: hmac
        secret:
          secretName: hmac-token
      - name: oauth
        secret:
          secretName: github-token
      - name: config
        configMap:
          name: config
      - name: plugins
        configMap:
          name: plugins
---
apiVersion: v1
kind: Service
metadata:
  name: hook
  namespace: prow
spec:
  selector:
    app: hook
  ports:
  - port: 8888
    targetPort: 8888
EOF
```

### Deploy Controller Manager

```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prow-controller-manager
  namespace: prow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prow-controller-manager
  template:
    metadata:
      labels:
        app: prow-controller-manager
    spec:
      serviceAccountName: prow-controller-manager
      containers:
      - name: prow-controller-manager
        image: gcr.io/k8s-prow/prow-controller-manager:v20231119-abc123
        args:
        - --config-path=/etc/config/config.yaml
        - --job-config-path=/etc/job-config
        volumeMounts:
        - name: config
          mountPath: /etc/config
        - name: job-config
          mountPath: /etc/job-config
      volumes:
      - name: config
        configMap:
          name: config
      - name: job-config
        configMap:
          name: config
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prow-controller-manager
  namespace: prow
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prow-controller-manager
rules:
- apiGroups:
  - prow.k8s.io
  resources:
  - prowjobs
  verbs:
  - get
  - list
  - watch
  - create
  - update
  - patch
  - delete
- apiGroups:
  - ""
  resources:
  - pods
  verbs:
  - get
  - list
  - watch
  - create
  - update
  - patch
  - delete
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prow-controller-manager
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prow-controller-manager
subjects:
- kind: ServiceAccount
  name: prow-controller-manager
  namespace: prow
EOF
```

### Deploy Plank

```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: plank
  namespace: prow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: plank
  template:
    metadata:
      labels:
        app: plank
    spec:
      serviceAccountName: plank
      containers:
      - name: plank
        image: gcr.io/k8s-prow/plank:v20231119-abc123
        args:
        - --config-path=/etc/config/config.yaml
        - --job-config-path=/etc/job-config
        volumeMounts:
        - name: config
          mountPath: /etc/config
        - name: job-config
          mountPath: /etc/job-config
      volumes:
      - name: config
        configMap:
          name: config
      - name: job-config
        configMap:
          name: config
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: plank
  namespace: prow
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: plank
rules:
- apiGroups:
  - prow.k8s.io
  resources:
  - prowjobs
  verbs:
  - get
  - list
  - watch
  - update
  - patch
- apiGroups:
  - ""
  resources:
  - pods
  verbs:
  - get
  - list
  - watch
  - create
  - update
  - patch
  - delete
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: plank
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: plank
subjects:
- kind: ServiceAccount
  name: plank
  namespace: prow
EOF
```

### Deploy Crier

```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crier
  namespace: prow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: crier
  template:
    metadata:
      labels:
        app: crier
    spec:
      containers:
      - name: crier
        image: gcr.io/k8s-prow/crier:v20231119-abc123
        args:
        - --github-token-path=/etc/github/oauth
        - --config-path=/etc/config/config.yaml
        - --job-config-path=/etc/job-config
        volumeMounts:
        - name: oauth
          mountPath: /etc/github
        - name: config
          mountPath: /etc/config
        - name: job-config
          mountPath: /etc/job-config
      volumes:
      - name: oauth
        secret:
          secretName: github-token
      - name: config
        configMap:
          name: config
      - name: job-config
        configMap:
          name: config
EOF
```

### Deploy Sinker

```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sinker
  namespace: prow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sinker
  template:
    metadata:
      labels:
        app: sinker
    spec:
      serviceAccountName: sinker
      containers:
      - name: sinker
        image: gcr.io/k8s-prow/sinker:v20231119-abc123
        args:
        - --config-path=/etc/config/config.yaml
        - --job-config-path=/etc/job-config
        volumeMounts:
        - name: config
          mountPath: /etc/config
        - name: job-config
          mountPath: /etc/job-config
      volumes:
      - name: config
        configMap:
          name: config
      - name: job-config
        configMap:
          name: config
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sinker
  namespace: prow
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: sinker
rules:
- apiGroups:
  - prow.k8s.io
  resources:
  - prowjobs
  verbs:
  - get
  - list
  - watch
  - delete
- apiGroups:
  - ""
  resources:
  - pods
  verbs:
  - get
  - list
  - watch
  - delete
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: sinker
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: sinker
subjects:
- kind: ServiceAccount
  name: sinker
  namespace: prow
EOF
```

### Deploy Deck (Web UI)

```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deck
  namespace: prow
spec:
  replicas: 2
  selector:
    matchLabels:
      app: deck
  template:
    metadata:
      labels:
        app: deck
    spec:
      containers:
      - name: deck
        image: gcr.io/k8s-prow/deck:v20231119-abc123
        args:
        - --config-path=/etc/config/config.yaml
        - --job-config-path=/etc/job-config
        - --spyglass=true
        volumeMounts:
        - name: config
          mountPath: /etc/config
        - name: job-config
          mountPath: /etc/job-config
      volumes:
      - name: config
        configMap:
          name: config
      - name: job-config
        configMap:
          name: config
---
apiVersion: v1
kind: Service
metadata:
  name: deck
  namespace: prow
spec:
  selector:
    app: deck
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
EOF
```

## Verify Installation

### Check Component Status

```bash
# Check all pods are running
kubectl get pods -n prow

# Check services
kubectl get services -n prow

# Check ProwJob CRD
kubectl get crd prowjobs.prow.k8s.io
```

### Test Webhook

```bash
# Port-forward to hook service
kubectl port-forward -n prow svc/hook 8888:8888

# In another terminal, test webhook
curl -X POST http://localhost:8888/hook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -d '{"zen":"Keep it logically awesome."}'
```

### Test Job Execution

Create a test ProwJob:

```bash
kubectl apply -f - <<EOF
apiVersion: prow.k8s.io/v1
kind: ProwJob
metadata:
  name: test-job
  namespace: prow
spec:
  type: presubmit
  job: test-job
  refs:
    org: my-org
    repo: my-repo
    base_ref: main
  agent: kubernetes
  pod_spec:
    containers:
    - image: alpine:latest
      command:
      - /bin/sh
      args:
      - -c
      - echo "Hello from Prow!"
EOF
```

Check job status:

```bash
kubectl get prowjob -n prow
kubectl get pods -n prow
```

## Configuration

### Main Config File

Create `config.yaml`:

```yaml
prow:
  job_namespace: default
  pod_namespace: default
  log_level: info

github:
  org: my-org
  repo: my-repo

deck:
  spyglass:
    lenses:
    - lens:
        name: buildlog
      required_files:
      - started.json|finished.json
```

### Cluster Configuration

```yaml
# config/cluster.yaml
default:
  cluster: default
  service_account: default
```

## Troubleshooting

### Common Issues

1. **Webhook not received**
   - Check webhook URL is correct
   - Verify HMAC token matches
   - Check hook pod logs: `kubectl logs -n prow -l app=hook`

2. **Jobs not running**
   - Check ProwJob CRD exists
   - Verify Plank is running: `kubectl get pods -n prow -l app=plank`
   - Check Plank logs: `kubectl logs -n prow -l app=plank`

3. **Status not reported**
   - Verify Crier is running
   - Check GitHub token is valid
   - Review Crier logs: `kubectl logs -n prow -l app=crier`

### Debug Commands

```bash
# View all ProwJobs
kubectl get prowjobs -n prow

# Describe a ProwJob
kubectl describe prowjob <job-name> -n prow

# View job pod logs
kubectl logs <pod-name> -n prow

# Check component logs
kubectl logs -n prow -l app=hook --tail=100
kubectl logs -n prow -l app=plank --tail=100
kubectl logs -n prow -l app=crier --tail=100
```

## Next Steps

1. **Configure Jobs**: See [Job Configuration Guide](JOB_CONFIGURATION.md)
2. **Set Up Plugins**: Configure plugins in `plugins.yaml`
3. **Configure Tide**: Set up automatic merging
4. **Set Up Deck**: Configure web UI access
5. **Monitor**: Set up monitoring and alerting

## Additional Resources

- [Prow Official Documentation](https://docs.prow.k8s.io/)
- [Example Configurations](https://github.com/kubernetes/test-infra/tree/master/config)
- [Prow GitHub Repository](https://github.com/kubernetes/test-infra/tree/master/prow)

