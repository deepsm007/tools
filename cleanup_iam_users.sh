aws --profile $1 iam list-users --query "Users[?starts_with(UserName, 'ci-op-') && CreateDate < '$(date -d '12 hours ago' --iso-8601=seconds)'].UserName" --output text | tr '\t' '\n' | while read -r user; do
  if [[ -n "$user" && "$user" =~ ^[a-zA-Z0-9+=,.@_-]+$ ]]; then
    echo "Processing user: $user"
    # Clean up user dependencies first
    aws --profile $1 iam list-attached-user-policies --user-name "$user" --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null | tr '\t' '\n' | while read -r policy; do [[ -n "$policy" ]] && aws --profile $1 iam detach-user-policy --user-name "$user" --policy-arn "$policy" 2>/dev/null; done
    aws --profile $1 iam list-user-policies --user-name "$user" --query 'PolicyNames[]' --output text 2>/dev/null | tr '\t' '\n' | while read -r policy; do [[ -n "$policy" ]] && aws --profile $1 iam delete-user-policy --user-name "$user" --policy-name "$policy" 2>/dev/null; done
    aws --profile $1 iam list-access-keys --user-name "$user" --query 'AccessKeyMetadata[].AccessKeyId' --output text 2>/dev/null | tr '\t' '\n' | while read -r key; do [[ -n "$key" ]] && aws --profile $1 iam delete-access-key --user-name "$user" --access-key-id "$key" 2>/dev/null; done
    aws --profile $1 iam list-groups-for-user --user-name "$user" --query 'Groups[].GroupName' --output text 2>/dev/null | tr '\t' '\n' | while read -r group; do [[ -n "$group" ]] && aws --profile $1 iam remove-user-from-group --user-name "$user" --group-name "$group" 2>/dev/null; done
    # Delete the user
    aws --profile $1 iam delete-user --user-name "$user" && echo "✓ Deleted: $user"
  else
    echo "Skipping invalid username: '$user'"
  fi
done
