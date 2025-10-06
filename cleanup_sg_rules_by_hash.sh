#!/usr/bin/env bash
# Cleanup orphaned NLB rules from Security Groups
# Usage:
# ./cleanup_orphaned_sg_rules.sh sg-xxxxxx,sg-yyyyyy dry-run|delete my-aws-profile

set -euo pipefail

TARGET_SGS="${1:?Error: Please provide a comma-separated list of SG IDs as the first argument.}"
DRY_RUN="${2:-true}"        # "true" for dry-run, "false" to delete
AWS_PROFILE="${3:-default}" # AWS CLI profile

echo "=== Starting Orphaned SG Rule Cleanup ==="
echo "Target SGs: $TARGET_SGS"
echo "Dry Run: $DRY_RUN"
echo "AWS Profile: $AWS_PROFILE"
echo "----------------------------------------"

IFS=',' read -r -a SG_IDS <<< "$TARGET_SGS"

extract_hash_from_desc() {
  local desc="$1"
  echo "$desc" | grep -oE 'client=[a-z0-9]+' | cut -d'=' -f2
}

lb_exists() {
  local hash="$1"
  local region="us-east-1"
  local exists
  exists=$(aws --profile "$AWS_PROFILE" elbv2 describe-load-balancers \
    --region "$region" \
    --query "LoadBalancers[?contains(LoadBalancerName, \`${hash}\`) == \`true\`].LoadBalancerName" \
    --output text 2>/dev/null || echo "")
  [[ -n "$exists" ]]
}


for sg_id in "${SG_IDS[@]}"; do
  found_region=""

  # Auto-detect region for SG
  for region in $(aws ec2 describe-regions --query 'Regions[].RegionName' --output text --profile "$AWS_PROFILE"); do
    sg_check=$(aws --profile "$AWS_PROFILE" ec2 describe-security-groups \
      --region "$region" --group-ids "$sg_id" \
      --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "")
    if [[ "$sg_check" != "None" && -n "$sg_check" ]]; then
      found_region="$region"
      echo "✅ Found SG $sg_id in region $region"
      break
    fi
  done

  if [[ -z "$found_region" ]]; then
    echo "❌ SG $sg_id not found in any region for profile $AWS_PROFILE"
    continue
  fi

  # Get all ingress rules
  ingress_json=$(aws --profile "$AWS_PROFILE" ec2 describe-security-groups \
    --region "$found_region" --group-ids "$sg_id" \
    --query "SecurityGroups[].IpPermissions" --output json)

  # Loop through each rule
  echo "$ingress_json" | jq -c '.[]' | while read -r rule; do
    descs=$(echo "$rule" | jq -r '.IpRanges[].Description? // empty')
    for desc in $descs; do
      if [[ "$desc" == *"kubernetes.io/rule/nlb/client="* ]]; then
        hash=$(extract_hash_from_desc "$desc")
        if [[ -n "$hash" ]]; then
          if ! lb_exists "$hash" "$found_region"; then
            echo "→ Orphaned rule found in SG $sg_id (hash: $hash, desc: $desc)"
            if [[ "$DRY_RUN" == "false" ]]; then
              aws --profile "$AWS_PROFILE" ec2 revoke-security-group-ingress \
                --region "$found_region" --group-id "$sg_id" --ip-permissions "[$rule]"
              echo "Deleted orphaned rule for SG $sg_id"
            else
              echo "Dry run — would delete orphaned rule for SG $sg_id"
            fi
          fi
        fi
      fi
    done
  done
done

echo ""
echo "=== Orphaned SG Rule Cleanup Complete ✅ ==="
