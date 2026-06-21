#!/usr/bin/env bash
# 計算 round id：給定 PR number，計算該 PR 上「非 bot 作者」的發言次數（含 PR body 算第 1 次）。
# 回傳格式：R<N>，例如 R1, R2
# 用法：calc-round.sh <pr-number>
# 依賴環境變數 GH_TOKEN / GITHUB_TOKEN 或 gh 已登入
set -euo pipefail
pr_number="${1:?missing pr-number}"
repo="${GH_REPO:-${GITHUB_REPOSITORY:?missing GITHUB_REPOSITORY}}"

# 取 PR body author + comments authors（按時間順序）
json=$(gh pr view "$pr_number" --repo "$repo" --json author,comments,body)

# PR body 算 user 第 1 次發言 → 起始 user_count=1
user_count=1

# 處理 comments
comment_count=$(echo "$json" | jq '.comments | length')
for ((i=0; i<comment_count; i++)); do
  author=$(echo "$json" | jq -r ".comments[$i].author.login")
  # bot 作者（含 [bot] 後綴或 github-actions[bot]）不算 user 發言
  if [[ "$author" == *"bot"* ]] || [[ "$author" == "github-actions[bot]" ]]; then
    continue
  fi
  user_count=$((user_count + 1))
done

echo "R${user_count}"