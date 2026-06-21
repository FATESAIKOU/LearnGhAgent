#!/usr/bin/env bash
# 把指定 log 檔案原封不動丟上 PR chat log（author 為 bot / github-actions）。
# 用法：post-log.sh <pr-number> <log-file> [step-label]
set -euo pipefail
pr_number="${1:?missing pr-number}"
log_file="${2:?missing log-file}"
label="${3:-log}"
repo="${GH_REPO:-${GITHUB_REPOSITORY:?missing GITHUB_REPOSITORY}}"

if [[ ! -f "$log_file" ]]; then
  echo "post-log: file not found $log_file, skip" >&2
  exit 0
fi

content="$(cat "$log_file")"
# GitHub comment 有長度限制（約 65536 字元），過長就分段
max=60000
if (( ${#content} <= max )); then
  gh pr comment "$pr_number" --repo "$repo" --body "$(printf '### [%s] log\n\n```markdown\n%s\n```\n' "$label" "$content")"
else
  idx=1
  while (( ${#content} > 0 )); do
    chunk="${content:0:$max}"
    content="${content:$max}"
    gh pr comment "$pr_number" --repo "$repo" --body "$(printf '### [%s part %d] log\n\n```markdown\n%s\n```\n' "$label" "$idx" "$chunk")"
    idx=$((idx+1))
  done
fi
echo "posted: $label"