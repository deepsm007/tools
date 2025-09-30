#!/bin/bash
# AWS Cluster Deprovision Script
# Usage: 
#   ./aws.sh                    # Uses default AWS profile/credentials
#   ./aws.sh --profile myprofile # Uses specified AWS profile
#   AWS_PROFILE=myprofile ./aws.sh # Uses profile from environment variable
#
# Environment variables (with defaults):
#   ARTIFACTS=/tmp/artifacts                    # Directory for logs and metadata
#   CLUSTER_TTL="72 hours ago"                  # Age cutoff for cluster cleanup
#   AWS_PROFILE=""                              # AWS profile to use (optional)
#   AWS_SHARED_CREDENTIALS_FILE=~/.aws/credentials # AWS credentials file
#   HYPERSHIFT_BASE_DOMAIN=origin-ci-int-aws.dev.rhcloud.com # Hypershift domain

set -o errexit
set -o nounset
set -o pipefail

# AWS Profile handling
AWS_PROFILE="${AWS_PROFILE:-}"
if [[ $# -gt 0 && "$1" == "--profile" ]]; then
    AWS_PROFILE="$2"
    shift 2
fi

# Helper function to run AWS CLI commands with profile support
function aws_cmd() {
    if [[ -n "${AWS_PROFILE}" ]]; then
        aws --profile "${AWS_PROFILE}" "$@"
    else
        aws "$@"
    fi
}

trap finish TERM QUIT

function finish {
    CHILDREN=$(jobs -p)
    if test -n "${CHILDREN}"; then
        kill ${CHILDREN} && wait
    fi
    exit
}

function queue() {
    local LIVE="$(jobs | wc -l)"
    while [[ "${LIVE}" -ge 2 ]]; do
        sleep 1
        LIVE="$(jobs | wc -l)"
    done
    echo "${@}"
    "${@}" &
}

function retry() {
    local retries=5
    local wait=5
    local n=0
    until "$@"; do
        n=$((n+1))
        if [[ $n -ge $retries ]]; then
            echo "Command failed after $n attempts: $*" >&2
            return 1
        fi
        echo "Retry $n/$retries for: $*" >&2
        sleep $((wait**n))
    done
}

function force_cleanup_vpc() {
    local region="$1"
    local cluster="$2"

    echo "Force-cleaning VPCs for cluster $cluster in region $region"

    vpcs=$(aws_cmd ec2 describe-vpcs --region "$region" \
        --filters "Name=tag:kubernetes.io/cluster/${cluster},Values=owned" \
        --query 'Vpcs[].VpcId' --output text || true)

    for vpc in $vpcs; do
        echo "Cleaning VPC $vpc"

        # Delete NAT gateways
        for nat in $(aws_cmd ec2 describe-nat-gateways --region "$region" --filter Name=vpc-id,Values=$vpc --query 'NatGateways[].NatGatewayId' --output text || true); do
            retry aws_cmd ec2 delete-nat-gateway --region "$region" --nat-gateway-id "$nat" || true
        done

        # Detach and delete IGWs
        for igw in $(aws_cmd ec2 describe-internet-gateways --region "$region" --filter Name=attachment.vpc-id,Values=$vpc --query 'InternetGateways[].InternetGatewayId' --output text || true); do
            retry aws_cmd ec2 detach-internet-gateway --region "$region" --internet-gateway-id "$igw" --vpc-id "$vpc" || true
            retry aws_cmd ec2 delete-internet-gateway --region "$region" --internet-gateway-id "$igw" || true
        done

        # Delete subnets
        for subnet in $(aws_cmd ec2 describe-subnets --region "$region" --filter Name=vpc-id,Values=$vpc --query 'Subnets[].SubnetId' --output text || true); do
            retry aws_cmd ec2 delete-subnet --region "$region" --subnet-id "$subnet" || true
        done

        # Delete route tables (except main)
        for rtb in $(aws_cmd ec2 describe-route-tables --region "$region" --filter Name=vpc-id,Values=$vpc --query 'RouteTables[].RouteTableId' --output text || true); do
            retry aws_cmd ec2 delete-route-table --region "$region" --route-table-id "$rtb" || true
        done

        # Delete security groups (except default)
        for sg in $(aws_cmd ec2 describe-security-groups --region "$region" --filter Name=vpc-id,Values=$vpc --query 'SecurityGroups[?GroupName!=`default`].GroupId' --output text || true); do
            retry aws_cmd ec2 delete-security-group --region "$region" --group-id "$sg" || true
        done

        # Finally delete the VPC
        retry aws_cmd ec2 delete-vpc --region "$region" --vpc-id "$vpc" || true
    done
}

function force_cleanup_route53() {
    local cluster="$1"

    zones=$(aws_cmd route53 list-hosted-zones --query "HostedZones[?Name == '${cluster}.${HYPERSHIFT_BASE_DOMAIN}.'].Id" --output text || true)
    for zone in $zones; do
        records=$(aws_cmd route53 list-resource-record-sets --hosted-zone-id "$zone" --query "ResourceRecordSets[?Type != 'NS' && Type != 'SOA']" --output json || true)
        for record in $(echo "$records" | jq -r '.[] | @base64'); do
            rname=$(echo "$record" | base64 --decode | jq -r .Name)
            rtype=$(echo "$record" | base64 --decode | jq -r .Type)
            aws_cmd route53 change-resource-record-sets \
                --hosted-zone-id "$zone" \
                --change-batch "{\"Changes\":[{\"Action\":\"DELETE\",\"ResourceRecordSet\":$(echo "$record" | base64 --decode)}]}" || true
        done
        retry aws_cmd route53 delete-hosted-zone --id "$zone" || true
    done
}

function deprovision() {
    WORKDIR="${1}"
    REGION="$(cat ${WORKDIR}/metadata.json|jq .aws.region -r)"
    INFRA_ID="$(cat ${WORKDIR}/metadata.json|jq '.aws.identifier[0]|keys[0]' -r|cut -d '/' -f3|tr -d '\n')"

    if [[ -n ${HYPERSHIFT_PRUNER:-} ]]; then
        HYPERSHIFT_BASE_DOMAIN="${HYPERSHIFT_BASE_DOMAIN:-origin-ci-int-aws.dev.rhcloud.com}"
        timeout --signal=SIGQUIT 30m hypershift destroy infra aws --aws-creds "${AWS_SHARED_CREDENTIALS_FILE}" --infra-id "${INFRA_ID}" --base-domain "${HYPERSHIFT_BASE_DOMAIN}" --region "${REGION}" || touch "${WORKDIR}/failure"
        timeout --signal=SIGQUIT 30m hypershift destroy iam aws --aws-creds "${AWS_SHARED_CREDENTIALS_FILE}" --infra-id "${INFRA_ID}" --region "${REGION}" || touch "${WORKDIR}/failure"
    else
        if command -v openshift-install >/dev/null 2>&1; then
            timeout --signal=SIGQUIT 60m openshift-install --dir "${WORKDIR}" --log-level error destroy cluster && touch "${WORKDIR}/success" || touch "${WORKDIR}/failure"
        else
            echo "Warning: openshift-install not found, skipping standard cluster destroy for ${WORKDIR##*/}"
            touch "${WORKDIR}/failure"
        fi
    fi

    # Failsafe: if cluster destroy failed, clean VPCs and Route53
    if [[ -f "${WORKDIR}/failure" ]]; then
        cluster="${WORKDIR##*/}"
        force_cleanup_vpc "${REGION}" "${cluster}"
        force_cleanup_route53 "${cluster}"
    fi
}

# HYPERSHIFT CLUSTER CLEANUP (72h cutoff)
had_failure=0
# Check if hostedcluster resource type exists before attempting cleanup
if oc api-resources | grep -q "hostedclusters"; then
    echo "Hypershift hostedcluster resource found, checking for old clusters..."
    hostedclusters="$(oc get hostedcluster -n clusters -o json 2>/dev/null | jq -r --argjson timestamp 259200 '.items[] | select (.metadata.creationTimestamp | sub("\\..*";"Z") | sub("\\s";"T") | fromdate < now - $timestamp).metadata.name' 2>/dev/null || true)"
    for hostedcluster in $hostedclusters; do
        if [[ -n "$hostedcluster" ]]; then
            echo "Destroying hostedcluster: $hostedcluster"
            hypershift destroy cluster aws --aws-creds "${AWS_SHARED_CREDENTIALS_FILE}" --namespace clusters --name "${hostedcluster}" || had_failure=$((had_failure+1))
        fi
    done
else
    echo "Hypershift hostedcluster resource not found, skipping hypershift cleanup..."
fi
if [[ $had_failure -ne 0 ]]; then exit $had_failure; fi

# DEPENDENCY CHECKS
echo "Checking required dependencies..."
missing_deps=0

# Check for required commands
for cmd in aws jq date find; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: Required command '$cmd' not found in PATH" >&2
        missing_deps=$((missing_deps + 1))
    fi
done

# Check for optional commands  
for cmd in openshift-install hypershift oc; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "WARNING: Optional command '$cmd' not found in PATH" >&2
    fi
done

if [[ $missing_deps -gt 0 ]]; then
    echo "ERROR: $missing_deps required dependencies missing. Exiting." >&2
    exit 1
fi

echo "Dependency check complete."

# MAIN CLUSTER DEPROVISION LOGIC
# Set default values for environment variables if not already set
ARTIFACTS="${ARTIFACTS:-/tmp/artifacts}"
CLUSTER_TTL="${CLUSTER_TTL:-72 hours ago}"
AWS_SHARED_CREDENTIALS_FILE="${AWS_SHARED_CREDENTIALS_FILE:-${HOME}/.aws/credentials}"
HYPERSHIFT_BASE_DOMAIN="${HYPERSHIFT_BASE_DOMAIN:-origin-ci-int-aws.dev.rhcloud.com}"

logdir="${ARTIFACTS}/deprovision"
mkdir -p "${logdir}"

# Set up logging to file
LOGFILE="${ARTIFACTS}/aws-deprovision-$(date +%Y%m%d-%H%M%S).log"
echo "AWS Deprovision Script started at $(date)" >&2
echo "Logging to: ${LOGFILE}" >&2
echo "Use 'tail -f ${LOGFILE}' to follow progress" >&2
echo "=======================================" >&2

# Redirect stdout to log file, keep stderr for important messages
exec 1> >(tee -a "${LOGFILE}")
exec 2> >(tee -a "${LOGFILE}" >&2)

aws_cluster_age_cutoff="$(TZ=":Africa/Abidjan" date --date="${CLUSTER_TTL}" '+%Y-%m-%dT%H:%M+0000')"
echo "deprovisioning clusters with an expirationDate before ${aws_cluster_age_cutoff} in AWS ..."

for region in $( aws_cmd ec2 describe-regions --region us-east-1 --query "Regions[].{Name:RegionName}" --output text ); do
    echo "deprovisioning in AWS region ${region} ..."
    aws_cmd ec2 describe-vpcs --output json --region ${region} | jq --arg date "${aws_cluster_age_cutoff}" -r '.Vpcs[] | select(.Tags[]? | select(.Key == "expirationDate" and .Value < $date)) | .Tags[]? | select((.Key | startswith("kubernetes.io/cluster/")) and (.Value == "owned")) | .Key' > /tmp/clusters
    while read cluster; do
        workdir="${logdir}/${cluster:22}"
        mkdir -p "${workdir}"
        cat <<-EOF >"${workdir}/metadata.json"
        {
            "aws":{
                "region":"${region}",
                "identifier":[
                    {"${cluster}": "owned"}
                ]
            }
        }
EOF
        echo "will deprovision AWS cluster ${cluster} in region ${region}"
    done < /tmp/clusters
done

# Check if openshift-install is available
if command -v openshift-install >/dev/null 2>&1; then
    echo "Using openshift-install version:"
    openshift-install version
else
    echo "Warning: openshift-install not found in PATH. Cluster destruction will use force cleanup methods."
fi

clusters=$( find "${logdir}" -mindepth 1 -type d )
for workdir in $(shuf <<< ${clusters}); do
    queue deprovision "${workdir}"
done

wait

# IAM USER CLEANUP (ci-op-* users older than 72h) - run after all cluster deprovisions complete
echo "Cleaning up old IAM users..."
cutoff="$(date -u -d '72 hours ago' --iso-8601=seconds)"
aws_cmd iam list-users --query "Users[?starts_with(UserName, 'ci-op-') && CreateDate < '${cutoff}'].UserName" --output text | tr '\t' '\n' | while read -r user; do
    if [[ -n "$user" ]]; then
        echo "Cleaning IAM user: $user"
        aws_cmd iam list-attached-user-policies --user-name "$user" --query 'AttachedPolicies[].PolicyArn' --output text | tr '\t' '\n' | while read -r policy; do
            [[ -n "$policy" ]] && aws_cmd iam detach-user-policy --user-name "$user" --policy-arn "$policy" || true
        done
        aws_cmd iam list-user-policies --user-name "$user" --query 'PolicyNames[]' --output text | tr '\t' '\n' | while read -r policy; do
            [[ -n "$policy" ]] && aws_cmd iam delete-user-policy --user-name "$user" --policy-name "$policy" || true
        done
        aws_cmd iam list-access-keys --user-name "$user" --query 'AccessKeyMetadata[].AccessKeyId' --output text | tr '\t' '\n' | while read -r key; do
            [[ -n "$key" ]] && aws_cmd iam delete-access-key --user-name "$user" --access-key-id "$key" || true
        done
        aws_cmd iam list-groups-for-user --user-name "$user" --query 'Groups[].GroupName' --output text | tr '\t' '\n' | while read -r group; do
            [[ -n "$group" ]] && aws_cmd iam remove-user-from-group --user-name "$user" --group-name "$group" || true
        done
        aws_cmd iam delete-user --user-name "$user" && echo "✓ Deleted: $user"
    fi
done

# CHECK DEPROVISION RESULTS
FAILED="$(find ${clusters} -name failure -printf '%H\n' | sort || true)"
if [[ -n "${FAILED}" ]]; then
    echo "Deprovision failed on the following clusters:"
    xargs --max-args 1 basename <<< $FAILED
    exit 1
fi

echo "Deprovision finished successfully"
