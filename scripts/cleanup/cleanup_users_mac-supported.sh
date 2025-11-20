iso_date_hours_ago() {

  local hours=${1:-12}   # default = 12 hours ago

  local os=$(uname)



  if [[ "$os" == "Linux" ]]; then

    date -d "$hours hours ago" --iso-8601=seconds

  elif [[ "$os" == "Darwin" ]]; then

    date -u -v -"${hours}"H +"%Y-%m-%dT%H:%M:%S%z" \

      | sed -E 's/([0-9]{2})([0-9]{2})$/\1:\2/'

  else

    echo "Unsupported OS: $os" >&2

    return 1

  fi

}



aws iam list-users --query "Users[?starts_with(UserName, 'ci-op-') && CreateDate < '$(iso_date_hours_ago)'].UserName" --output text | tr '\t' '\n' | while read -r user; do

  if [[ -n "$user" && "$user" =~ ^[a-zA-Z0-9+=,.@_-]+$ ]]; then

    echo "Processing: $user"

    aws iam list-attached-user-policies --user-name "$user" --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null | tr '\t' '\n' | while read -r policy; do [[ -n "$policy" ]] && aws iam detach-user-policy --user-name "$user" --policy-arn "$policy" 2>/dev/null; done

    aws iam list-user-policies --user-name "$user" --query 'PolicyNames[]' --output text 2>/dev/null | tr '\t' '\n' | while read -r policy; do [[ -n "$policy" ]] && aws iam delete-user-policy --user-name "$user" --policy-name "$policy" 2>/dev/null; done

    aws iam list-access-keys --user-name "$user" --query 'AccessKeyMetadata[].AccessKeyId' --output text 2>/dev/null | tr '\t' '\n' | while read -r key; do [[ -n "$key" ]] && aws iam delete-access-key --user-name "$user" --access-key-id "$key" 2>/dev/null; done

    aws iam get-groups-for-user --user-name "$user" --query 'Groups[].GroupName' --output text 2>/dev/null | tr '\t' '\n' | while read -r group; do [[ -n "$group" ]] && aws iam remove-user-from-group --user-name "$user" --group-name "$group" 2>/dev/null; done

    aws iam delete-user --user-name "$user" && echo "Deleted: $user"

  else

    echo "Skip invalid username: '$user'"

  fi
