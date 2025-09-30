aws --profile $1 iam list-users --query "Users[?starts_with(UserName, 'ci-op-') && CreateDate < '$(date -d '24 hours ago' --iso-8601=seconds)'].UserName" --output text | tr '\t' '\n' | while read -r user; do

  if [[ -n "$user" && "$user" =~ ^[a-zA-Z0-9+=,.@_-]+$ ]]; then

    echo "Processing user: $user"

    # Clean up user dependencies first
    echo "  Detaching managed policies..."
    aws --profile $1 iam list-attached-user-policies --user-name "$user" --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null | tr '\t' '\n' | while read -r policy; do 
      if [[ -n "$policy" ]]; then
        aws --profile $1 iam detach-user-policy --user-name "$user" --policy-arn "$policy" 2>/dev/null
        echo "    Detached policy: $policy"
      fi
    done

    echo "  Deleting inline policies..."
    aws --profile $1 iam list-user-policies --user-name "$user" --query 'PolicyNames[]' --output text 2>/dev/null | tr '\t' '\n' | while read -r policy; do 
      if [[ -n "$policy" ]]; then
        aws --profile $1 iam delete-user-policy --user-name "$user" --policy-name "$policy" 2>/dev/null
        echo "    Deleted inline policy: $policy"
      fi
    done

    echo "  Deleting access keys..."
    aws --profile $1 iam list-access-keys --user-name "$user" --query 'AccessKeyMetadata[].AccessKeyId' --output text 2>/dev/null | tr '\t' '\n' | while read -r key; do 
      if [[ -n "$key" ]]; then
        aws --profile $1 iam delete-access-key --user-name "$user" --access-key-id "$key" 2>/dev/null
        echo "    Deleted access key: $key"
      fi
    done

    echo "  Removing from groups..."
    aws --profile $1 iam list-groups-for-user --user-name "$user" --query 'Groups[].GroupName' --output text 2>/dev/null | tr '\t' '\n' | while read -r group; do 
      if [[ -n "$group" ]]; then
        aws --profile $1 iam remove-user-from-group --user-name "$user" --group-name "$group" 2>/dev/null
        echo "    Removed from group: $group"
      fi
    done

    # Wait a moment for all operations to complete
    sleep 2

    # Delete the user
    echo "  Deleting user..."
    if aws --profile $1 iam delete-user --user-name "$user" 2>/dev/null; then
      echo "✓ Deleted: $user"
    else
      echo "✗ Failed to delete: $user (may still have dependencies)"
    fi

  else

    echo "Skipping invalid username: '$user'"

  fi

done
