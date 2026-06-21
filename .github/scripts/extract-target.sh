#!/usr/bin/env bash
# 從 PR body 抓出「技術標的」（issue 原始內容複製到 PR body 的第一行 / 標題區塊）。
# 這是暫時簡化版：直接把 PR body 全文當作「使用者意圖」回傳。
# 後續可改成結構化解析（例如讀 PR body 內特定 section）。
# 用法：extract-target.sh <pr-number>
set -euo pipefail
pr_number="${1:?missing pr-number}"
repo="${GH_REPO:-${GITHUB_REPOSITORY:?missing GITHUB_REPOSITORY}}"

body=$(gh pr view "$pr_number" --repo "$repo" --json body -q .body)
if [[ -z "$body" || "$body" == "null" ]]; then
  echo "ERROR: empty PR body" >&2
  exit 1
fi
echo "$body"