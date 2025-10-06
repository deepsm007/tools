#!/usr/bin/env bash
# Cleanup AWS Load Balancers and Security Groups not in safeguard list and older than a threshold
#    ./cleanup_lb_sg.sh sg-abc123,sg-def456 48 false
#

set -euo pipefail

SAFEGUARD_SGS="${1:-sg-xxxxxx}"     # Comma-separated list of Security Groups to KEEP
AGE_HOURS="${2:-24}"                # Default age threshold in hours
DRY_RUN="${3:-true}"                # Default to dry run (set to false to delete)

REGIONS=("us-east-1" "us-east-2" "us-west-1" "us-west-2")

echo "=== AWS Cleanup Script ==="
echo "Safeguard SGs: $SAFEGUARD_SGS"
echo "Age Threshold: $AGE_HOURS hours"
echo "Regions: ${REGIONS[*]}"
echo "Dry Run: $DRY_RUN"
echo "----------------------------------"

IFS=',' read -r -a SG_ARRAY <<< "$SAFEGUARD_SGS"

get_creation_time_epoch() {
  date -d "$1" +%s 2>/dev/null || gdate -d "$1" +%s
}

has_safe_sg() {
  local sg_list="$1"
  for sg in "${SG_ARRAY[@]}"; do
    if [[ "$sg_list" == *"$sg"* ]]; then
      return 0
    fi
  done
  return 1
}

# Cleanup Load Balancers
cleanup_load_balancers() {
  local region=$1
  echo ""
  echo ">>> Checking Load Balancers in $region ..."
  local now_epoch
  now_epoch=$(date +%s)

  local lb_list
  lb_list=$(aws elbv2 describe-load-balancers --region "$region" --query "LoadBalancers[]" --output json 2>/dev/null || echo "[]")

  if [[ "$lb_list" == "[]" ]]; then
    echo "No Load Balancers found in $region."
    return
  fi

  echo "$lb_list" | jq -c '.[]' | while read -r lb; do
    local lb_arn lb_name created_time created_epoch age_hours sg_attached
    lb_arn=$(echo "$lb" | jq -r '.LoadBalancerArn')
    lb_name=$(echo "$lb" | jq -r '.LoadBalancerName')
    created_time=$(echo "$lb" | jq -r '.CreatedTime')
    created_epoch=$(get_creation_time_epoch "$created_time")
    age_hours=$(( (now_epoch - created_epoch) / 3600 ))

    sg_attached=$(aws elbv2 describe-load-balancers --load-balancer-arns "$lb_arn" --region "$region" \
      --query "LoadBalancers[].SecurityGroups[]" --output text 2>/dev/null || echo "")

    if ! has_safe_sg "$sg_attached"; then
      if (( age_hours >= AGE_HOURS )); then
        echo "→ [LB] $lb_name (Age: ${age_hours}h, SGs: ${sg_attached:-None}) — NOT using safeguarded SGs"
        if [[ "$DRY_RUN" == "false" ]]; then
          echo "Deleting Load Balancer $lb_name ..."
          aws elbv2 delete-load-balancer --load-balancer-arn "$lb_arn" --region "$region"
        else
          echo "Dry run — would delete Load Balancer $lb_name"
        fi
      fi
    fi
  done
}

# Cleanup Security Groups
cleanup_security_groups() {
  local region=$1
  echo ""
  echo ">>> Checking Security Groups in $region ..."
  local now_epoch
  now_epoch=$(date +%s)

  local sg_list
  sg_list=$(aws ec2 describe-security-groups --region "$region" --query "SecurityGroups[]" --output json 2>/dev/null || echo "[]")

  if [[ "$sg_list" == "[]" ]]; then
    echo "No Security Groups found in $region."
    return
  fi

  echo "$sg_list" | jq -c '.[]' | while read -r sg; do
    local sg_id sg_name desc created_epoch age_hours attached
    sg_id=$(echo "$sg" | jq -r '.GroupId')
    sg_name=$(echo "$sg" | jq -r '.GroupName')

    # Skip if in safeguard list
    for safe in "${SG_ARRAY[@]}"; do
      if [[ "$sg_id" == "$safe" ]]; then
        continue 2
      fi
    done

    # Check if attached to any ENI
    attached=$(aws ec2 describe-network-interfaces --filters "Name=group-id,Values=$sg_id" --region "$region" \
      --query "NetworkInterfaces" --output text 2>/dev/null || echo "")

    # Get SG creation time from tags if available
    created_tag=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$sg_id" "Name=key,Values=CreateTime" \
      --region "$region" --query "Tags[].Value" --output text 2>/dev/null || echo "")
    if [[ -n "$created_tag" ]]; then
      created_epoch=$(get_creation_time_epoch "$created_tag")
      age_hours=$(( (now_epoch - created_epoch) / 3600 ))
    else
      age_hours=$AGE_HOURS # Assume old enough if no tag
    fi

    if [[ -z "$attached" && "$sg_name" != "default" && "$sg_id" != *"${SAFEGUARD_SGS}"* ]]; then
      if (( age_hours >= AGE_HOURS )); then
        echo "→ [SG] $sg_id ($sg_name) — unused, older than ${age_hours}h"
        if [[ "$DRY_RUN" == "false" ]]; then
          echo "Deleting Security Group $sg_id ..."
          aws ec2 delete-security-group --group-id "$sg_id" --region "$region" || echo "Failed to delete $sg_id"
        else
          echo "Dry run — would delete $sg_id"
        fi
      fi
    fi
  done
}

for region in "${REGIONS[@]}"; do
  cleanup_load_balancers "$region"
  cleanup_security_groups "$region"
done

echo ""
echo "=== Cleanup Complete Across All Regions ✅ ==="
