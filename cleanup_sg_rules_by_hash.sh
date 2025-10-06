#!/usr/bin/env bash
# Cleanup orphaned security group rules referring to non-existent Load Balancers
# Dry Run --> ./cleanup_sg_rules_by_hash.sh sg-abc123, sg-xyz-456
#   ./cleanup_sg_rules_by_hash.sh sg-abc123, sg-xyz-456 false myprofile
#

set -euo pipefail

TARGET_SGS="${1:?Error: Please provide a comma-separated list of target security group names as the first argument.}"  # e.g. sg1,sg2  # Comma-separated SG names
DRY_RUN="${2:-true}"                                                        # Default dry run
AWS_PROFILE="${3:-default}"                                                 # AWS profile
REGIONS=("us-east-1" "us-east-2" "us-west-1" "us-west-2")

echo "=== Cleanup Orphaned SG Rules ==="
echo "Target SGs: $TARGET_SGS"
echo "Dry Run: $DRY_RUN"
echo "AWS Profile: $AWS_PROFILE"
echo "Regions: ${REGIONS[*]}"
echo "----------------------------------"

IFS=',' read -r -a SG_NAMES <<< "$TARGET_SGS"

extract_hash_from_desc() {
  local desc="$1"
  echo "$desc" | grep -oE 'client=[a-z0-9]+' | cut -d'=' -f2
}

# Check if Load Balancer exists
lb_exists() {
  local hash=$1
  local region=$2
  local exists=false

  # Search all NLB/ALBs names and ARNs for hash
  local found
  found=$(aws --profile "$AWS_PROFILE" elbv2 describe-load-balancers --region "$region" \
    --query "LoadBalancers[?contains(LoadBalancerName, \`${hash}\`) == `true`].LoadBalancerName" \
    --output text 2>/dev/null || echo "")

  if [[ -n "$found" ]]; then
    exists=true
  fi

  echo "$exists"
}

# Cleanup rules
cleanup_region() {
  local region=$1
  echo ""
  echo ">>> Checking region: $region ..."
  echo "--------------------------------"

  for sg_name in "${SG_NAMES[@]}"; do
    local sg_id
    sg_id=$(aws --profile "$AWS_PROFILE" ec2 describe-security-groups \
      --region "$region" --filters "Name=group-name,Values=$sg_name" \
      --query "SecurityGroups[0].GroupId" --output text 2>/dev/null || echo "")

    if [[ -z "$sg_id" || "$sg_id" == "None" ]]; then
      echo "⚠️  SG '$sg_name' not found in $region"
      continue
    fi

    echo "Inspecting SG: $sg_name ($sg_id)"

    # Get all ingress rules
    local ingress_json
    ingress_json=$(aws --profile "$AWS_PROFILE" ec2 describe-security-groups \
      --region "$region" --group-ids "$sg_id" --query "SecurityGroups[].IpPermissions" --output json)

    # Loop through each rule
    echo "$ingress_json" | jq -c '.[]' | while read -r rule; do
      local descs
      descs=$(echo "$rule" | jq -r '.IpRanges[].Description? // empty')

      for desc in $descs; do
        if [[ "$desc" == *"kubernetes.io/rule/nlb/client="* ]]; then
          local hash
          hash=$(extract_hash_from_desc "$desc")
          if [[ -n "$hash" ]]; then
            local exists
            exists=$(lb_exists "$hash" "$region")
            if [[ "$exists" == "false" ]]; then
              echo "→ Orphaned rule found in $sg_name (hash: $hash, desc: $desc)"

              if [[ "$DRY_RUN" == "false" ]]; then
                echo "Deleting rule with description: $desc"
                aws --profile "$AWS_PROFILE" ec2 revoke-security-group-ingress \
                  --region "$region" \
                  --group-id "$sg_id" \
                  --ip-permissions "[$rule]" >/dev/null 2>&1 || \
                  echo "Failed to delete rule from $sg_name"
              else
                echo "Dry run — would delete rule: $desc"
              fi
            fi
          fi
        fi
      done
    done
  done
}


for region in "${REGIONS[@]}"; do
  cleanup_region "$region"
done

echo ""
echo "=== SG Rule Cleanup Complete ✅ ==="
