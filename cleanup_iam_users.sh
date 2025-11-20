#!/bin/bash

# Usage: ./cleanup_iam_user.sh <aws-profile>

set -euo pipefail

PROFILE="$1"
CUTOFF_DATE=$(date -d '24 hours ago' --iso-8601=seconds)

# Function to process a single user
cleanup_user() {
    local user="$1"
    
    if [[ ! "$user" =~ ^[a-zA-Z0-9+=,.@_-]+$ ]]; then
        echo "Skipping invalid username: '$user'"
        return 0
    fi

    echo "Processing user: $user"
    
    # Run all cleanup operations in parallel
    (
        # Detach managed policies
        aws --profile "$PROFILE" iam list-attached-user-policies --user-name "$user" --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null | tr '\t' '\n' | while read -r policy; do 
            [[ -n "$policy" ]] && aws --profile "$PROFILE" iam detach-user-policy --user-name "$user" --policy-arn "$policy" 2>/dev/null && echo "    Detached policy: $policy"
        done
    ) &
    
    (
        # Delete inline policies
        aws --profile "$PROFILE" iam list-user-policies --user-name "$user" --query 'PolicyNames[]' --output text 2>/dev/null | tr '\t' '\n' | while read -r policy; do 
            [[ -n "$policy" ]] && aws --profile "$PROFILE" iam delete-user-policy --user-name "$user" --policy-name "$policy" 2>/dev/null && echo "    Deleted inline policy: $policy"
        done
    ) &
    
    (
        # Delete access keys
        aws --profile "$PROFILE" iam list-access-keys --user-name "$user" --query 'AccessKeyMetadata[].AccessKeyId' --output text 2>/dev/null | tr '\t' '\n' | while read -r key; do 
            [[ -n "$key" ]] && aws --profile "$PROFILE" iam delete-access-key --user-name "$user" --access-key-id "$key" 2>/dev/null && echo "    Deleted access key: $key"
        done
    ) &
    
    (
        # Remove from groups
        aws --profile "$PROFILE" iam list-groups-for-user --user-name "$user" --query 'Groups[].GroupName' --output text 2>/dev/null | tr '\t' '\n' | while read -r group; do 
            [[ -n "$group" ]] && aws --profile "$PROFILE" iam remove-user-from-group --user-name "$user" --group-name "$group" 2>/dev/null && echo "    Removed from group: $group"
        done
    ) &
    
    # Wait for all parallel operations to complete
    wait
    
    # Delete the user
    echo "  Deleting user..."
    if aws --profile "$PROFILE" iam delete-user --user-name "$user" 2>/dev/null; then
        echo "✓ Deleted: $user"
    else
        echo "✗ Failed to delete: $user (may still have dependencies)"
    fi
}

# Export function for parallel processing
export -f cleanup_user
export PROFILE

# Get list of users and process them in parallel (limit to 10 concurrent processes)
aws --profile "$PROFILE" iam list-users --query "Users[?starts_with(UserName, 'ci-op-') && CreateDate < '$CUTOFF_DATE'].UserName" --output text | tr '\t' '\n' | \
    xargs -n 1 -P 10 -I {} bash -c 'cleanup_user "$@"' _ {}
