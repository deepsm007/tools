#!/usr/bin/env bash
# Cleanup AWS Load Balancers not attached to specific Security Groups and older than a threshold
#   ./cleanup_load_balancers.sh sg-abc123,sg-def456 48 false
#

set -euo pipefail

SAFEGUARD_SGS="${1:-sg-xxxxxx}"        # Comma-separated list of Security Groups to KEEP
AGE_HOURS="${2:-24}"                   # Default age threshold in hours
DRY_RUN="${3:-true}"                   # Default to dry run (set to false to delete)

# Regions
REGIONS=("us-east-1" "us-east-2" "us-west-1" "us-west-2")

echo "=== Cleanup AWS Load Balancers ==="
echo "Safeguard SGs: $SAFEGUARD_SGS"
echo "Age Threshold: $AGE_HOURS hours"
echo "Regions: ${REGIONS[*]}"
echo "Dry Run: $DRY_RUN"
echo "----------------------------------"

IFS=',' read -r -a SG_ARRAY <<< "$SAFEGUARD_SGS"

get_creation_time_epoch() {
  # Converts ISO8601 to epoch seconds
  date -d "$1" +%s 2>/dev/null || gdate -d "$1" +%s
}

lb_has_safe_sg() {
  local lb_sgs="$1"
  for sg in "${SG_ARRAY[@]}"; do
    if [[ "$lb_sgs" == *"$sg"* ]]; then
      return 0  # found safe SG
    fi
  done
  return 1  # none found
}

# Cleanup per region 
cleanup_region() {
  local region=$1
  echo ""
  echo ">>> Scanning region: $region ..."
  echo "--------------------------------"

  local now_epoch
  now_epoch=$(date +%s)

  local lb_list
  lb_list=$(aws elbv2 describe-load-balancers --region "$region" --query "LoadBalancers[]" --output json 2>/dev/null || echo "[]")

  if [[ "$lb_list" == "[]" ]]; then
    echo "No load balancers found in $region"
    return
  fi

  echo "$lb_list" | jq -c '.[]' | while read -r lb; do
    lb_arn=$(echo "$lb" | jq -r '.LoadBalancerArn')
    lb_name=$(echo "$lb" | jq -r '.LoadBalancerName')
    created_time=$(echo "$lb" | jq -r '.CreatedTime')
    created_epoch=$(get_creation_time_epoch "$created_time")
    age_hours_actual=$(( (now_epoch - created_epoch) / 3600 ))

    sg_attached=$(aws elbv2 describe-load-balancers --load-balancer-arns "$lb_arn" --region "$region" \
      --query "LoadBalancers[].SecurityGroups[]" --output text 2>/dev/null || echo "")

    if ! lb_has_safe_sg "$sg_attached"; then
      if (( age_hours_actual >= AGE_HOURS )); then
        echo "→ Found LB: $lb_name (Age: ${age_hours_actual}h, SGs: ${sg_attached:-None}) — NOT using safe SGs"
        if [[ "$DRY_RUN" == "false" ]]; then
          echo "Deleting $lb_name ..."
          aws elbv2 delete-load-balancer --load-balancer-arn "$lb_arn" --region "$region"
        else
          echo "Dry run — would delete $lb_name"
        fi
      fi
    fi
  done

  echo "Finished region: $region ✅"
}

for region in "${REGIONS[@]}"; do
  cleanup_region "$region"
done

echo ""
echo "=== Cleanup Complete Across All Regions ✅ ==="
