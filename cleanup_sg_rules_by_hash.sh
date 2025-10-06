#!/usr/bin/env bash
# Cleanup orphaned NLB rules from Security Groups (ingress + egress)
# Usage:
# ./cleanup_orphaned_sg_rules_full.sh sg-xxxxxx,sg-yyyyyy dry-run|delete my-aws-profile

set -euo pipefail

TARGET_SGS="${1:?Error: Please provide a comma-separated list of SG IDs as the first argument.}"
DRY_RUN="${2:-true}"        # "true" for dry-run, "false" to delete
AWS_PROFILE="${3:-default}" # AWS CLI profile

echo "=== Starting Orphaned SG Rule Cleanup (Ingress + Egress) ==="
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
  local region="$2"
  local exists
  exists=$(aws --profile "$AWS_PROFILE" elbv2 describe-load-balancers \
    --region "$region" \
    --query "LoadBalancers[?contains(LoadBalancerName, \`${hash}\`) == \`true\`].LoadBalancerName" \
    --output text 2>/dev/null || echo "")
  [[ -n "$exists" ]]
}

cleanup_rules() {
  local sg_id="$1"
  local region="$2"
  local permission_type="$3"   # "IpPermissions" for ingress, "IpPermissionsEgress" for egress

  rules_json=$(aws --profile "$AWS_PROFILE" ec2 describe-security-groups \
    --region "$region" --group-ids "$sg_id" \
    --query "SecurityGroups[].${permission_type}" --output json)

  echo "$rules_json" | jq -c '.[]' | while read -r rule; do
    descs=$(echo "$rule" | jq -r '.IpRanges[].Description? // empty, .Ipv6Ranges[].Description? // empty')
    for desc in $descs; do
      if [[ "$desc" == *"kubernetes.io/rule/nlb/client="* ]]; then
        hash=$(extract_hash_from_desc "$desc")
        if [[ -n "$hash" ]]; then
          if ! lb_exists "$hash" "$region"; then
            echo "→ Orphaned $permission_type rule found in SG $sg_id (hash: $hash, desc: $desc)"
            if [[ "$DRY_RUN" == "false" ]]; then
              if [[ "$permission_type" == "IpPermissions" ]]; then
                aws --profile "$AWS_PROFILE" ec2 revoke-security-group-ingress \
                  --region "$region" --group-id "$sg_id" --ip-permissions "$(echo "$rule" | jq -c '.')"
              else
                aws --profile "$AWS_PROFILE" ec2 revoke-security-group-egress \
                  --region "$region" --group-id "$sg_id" --ip-permissions "$(echo "$rule" | jq -c '.')"
              fi
              echo "Deleted orphaned $permission_type rule for SG $sg_id"
            else
              echo "Dry run — would delete orphaned $permission_type rule: $desc"
            fi
          fi
        fi
      fi
    done
  done
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

  # Cleanup ingress rules
  cleanup_rules "$sg_id" "$found_region" "IpPermissions"

  # Cleanup egress rules
  cleanup_rules "$sg_id" "$found_region" "IpPermissionsEgress"
done

echo ""
echo "=== Orphaned SG Rule Cleanup Complete ✅ ==="
