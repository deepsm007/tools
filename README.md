# CI Tools Repository

A collection of tools and documentation for managing cloud infrastructure, cleaning up resources, and understanding cloud architectures. This repository contains automation scripts for AWS resource cleanup and comprehensive documentation for AWS, Azure, GCP, and OpenShift platforms.

## Repository Contents

### 🛠️ AWS Cleanup Scripts

Automation scripts for cleaning up AWS resources, managing clusters, and maintaining cloud hygiene:

- **[cleanup_aws_resources.sh](cleanup_aws_resources.sh)** - Comprehensive AWS cluster deprovisioning script
  - Deprovisions OpenShift and Hypershift clusters older than a specified cutoff time
  - Cleans up VPCs, subnets, route tables, security groups, load balancers, and other AWS resources
  - Handles IAM user cleanup for `ci-op-*` users
  - Supports multiple AWS regions and profiles
  - Usage: `./cleanup_aws_resources.sh [--profile PROFILE] [--cutoff TIME]`

- **[cleanup_iam_users.sh](cleanup_iam_users.sh)** - IAM user cleanup utility
  - Removes IAM users matching `ci-op-*` pattern older than 24 hours
  - Detaches policies, deletes access keys, and removes group memberships
  - Supports parallel processing for efficiency
  - Usage: `./cleanup_iam_users.sh <aws-profile>`

- **[cleanup_lb_sg.sh](cleanup_lb_sg.sh)** - Load balancer and security group cleanup
  - Removes unused load balancers and security groups
  - Supports safeguard lists to protect specific resources
  - Configurable age threshold and dry-run mode
  - Usage: `./cleanup_lb_sg.sh <safeguard-sgs> <age-hours> <dry-run>`

- **[cleanup_sg_rules_by_hash.sh](cleanup_sg_rules_by_hash.sh)** - Security group rules cleanup by hash
  - Removes security group rules based on hash matching
  - Useful for cleaning up duplicate or unnecessary rules

- **[cleanup_users_mac-supported.sh](cleanup_users_mac-supported.sh)** - Mac-compatible user cleanup script
  - Cross-platform version of user cleanup utilities

### 📚 Documentation

Comprehensive architecture and platform documentation organized by cloud provider:

#### OpenShift Documentation
Located in [`docs/Openshift/`](docs/Openshift/)

Comprehensive documentation for understanding OpenShift architecture, components, networking, APIs, and cluster management:

- **[Overview](docs/Openshift/OPENSHIFT_OVERVIEW.md)** - High-level overview of OpenShift
- **[Architecture](docs/Openshift/ARCHITECTURE.md)** - System architecture and component diagrams
- **[Network and API Guide](docs/Openshift/NETWORK_API_GUIDE.md)** - Networking and API architecture
- **[Component Interactions](docs/Openshift/COMPONENT_INTERACTIONS.md)** - How components interact
- **[Navigation and Debugging](docs/Openshift/NAVIGATION_DEBUGGING.md)** - How to navigate and debug clusters
- **[Setup Guide](docs/Openshift/SETUP.md)** - Setting up access and navigation
- **[Usage Guide](docs/Openshift/USAGE.md)** - Practical examples and operations
- **[FAQ](docs/Openshift/FAQ.md)** - Frequently asked questions
- **[Summaries](docs/Openshift/SUMMARIES.md)** - Technical summaries at different levels
- **[Release Notes](docs/Openshift/release.md)** - Release information

See [docs/Openshift/README.md](docs/Openshift/README.md) for the complete OpenShift documentation index.

#### Kubernetes Documentation
Located in [`docs/Kubernetes/`](docs/Kubernetes/)

Beginner-friendly architecture documentation for understanding Kubernetes:

- **[Architecture](docs/Kubernetes/architecture.md)** - Comprehensive Kubernetes architecture diagram
  - Control plane components (API Server, etcd, Scheduler, Controller Manager)
  - Worker node components (Kubelet, kube-proxy, Container Runtime)
  - Networking (Services, Ingress, CNI, DNS)
  - Storage (Volumes, PVs, PVCs, Storage Classes)
  - Security (RBAC, Secrets, Network Policies)
  - Observability (Metrics, Logs, Tracing)
  - Application deployment and scaling workflows

#### Cloud Platform Architecture Documentation

- **[AWS Architecture](docs/AWS/architecture.md)** - Amazon Web Services architecture overview
  - Compute, networking, storage, security, and operations layers
  - Service relationships and best practices

- **[Azure Architecture](docs/AZURE/architecture.md)** - Microsoft Azure architecture overview
  - Virtual machines, containers, networking, storage, and security services
  - Azure-specific patterns and configurations

- **[GCP Architecture](docs/GCP/architecture.md)** - Google Cloud Platform architecture overview
  - Compute Engine, Kubernetes, serverless, networking, and storage services
  - GCP-specific architectures and recommendations

## Quick Start

### Using AWS Cleanup Scripts

1. **Prerequisites:**
   - AWS CLI installed and configured
   - Appropriate AWS credentials and permissions
   - `jq` command-line JSON processor
   - Optional: `openshift-install` and `hypershift` for cluster management

2. **Basic Usage:**
   ```bash
   # Clean up AWS resources (default: 72 hours ago)
   ./cleanup_aws_resources.sh

   # Use specific AWS profile
   ./cleanup_aws_resources.sh --profile myprofile

   # Custom age cutoff
   ./cleanup_aws_resources.sh --cutoff "24 hours ago"

   # Combined options
   ./cleanup_aws_resources.sh --profile prod --cutoff "1 week ago"
   ```

3. **IAM User Cleanup:**
   ```bash
   ./cleanup_iam_users.sh <aws-profile>
   ```

4. **Load Balancer and Security Group Cleanup:**
   ```bash
   ./cleanup_lb_sg.sh sg-abc123,sg-def456 48 false
   ```

### Accessing Documentation

- **OpenShift**: Start with [docs/Openshift/OPENSHIFT_OVERVIEW.md](docs/Openshift/OPENSHIFT_OVERVIEW.md)
- **Kubernetes**: See [docs/Kubernetes/architecture.md](docs/Kubernetes/architecture.md)
- **AWS**: See [docs/AWS/architecture.md](docs/AWS/architecture.md)
- **Azure**: See [docs/AZURE/architecture.md](docs/AZURE/architecture.md)
- **GCP**: See [docs/GCP/architecture.md](docs/GCP/architecture.md)

## Environment Variables

The cleanup scripts support the following environment variables:

- `ARTIFACTS` - Directory for logs and metadata (default: `/tmp/artifacts`)
- `CLUSTER_TTL` - Default age cutoff for cluster cleanup (default: `72 hours ago`)
- `AWS_PROFILE` - AWS profile to use (optional)
- `AWS_SHARED_CREDENTIALS_FILE` - AWS credentials file (default: `~/.aws/credentials`)
- `HYPERSHIFT_BASE_DOMAIN` - Hypershift base domain (default: `origin-ci-int-aws.dev.rhcloud.com`)

## Requirements

### Required Tools
- `bash` (version 4.0+)
- `aws` CLI
- `jq` (JSON processor)
- `date` (GNU date or macOS gdate)

### Optional Tools
- `openshift-install` - For OpenShift cluster management
- `hypershift` - For Hypershift cluster management
- `oc` - OpenShift CLI

## Safety Features

- **Dry-run mode** - Test scripts without making changes
- **Safeguard lists** - Protect specific resources from deletion
- **Age thresholds** - Only clean resources older than specified time
- **Comprehensive logging** - All operations logged to files
- **Error handling** - Graceful failure handling and retry logic
- **Dependency checks** - Verifies required tools before execution

## External Resources

- [OpenShift Documentation](https://docs.openshift.com/) - Official OpenShift documentation
- [Kubernetes Documentation](https://kubernetes.io/docs/) - Kubernetes documentation
- [AWS CLI Documentation](https://docs.aws.amazon.com/cli/) - AWS Command Line Interface
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

## Contributing

Contributions are welcome! When contributing:

1. Test scripts thoroughly before submitting
2. Update documentation for any new features
3. Follow existing code style and patterns
4. Add appropriate error handling and logging
5. Include usage examples in script headers

## License

This repository follows the organization's standard license terms.

## Support

For issues, questions, or contributions:
- Review the documentation in the `docs/` directory
- Check script headers for usage information
- Review logs in the `ARTIFACTS` directory for troubleshooting
