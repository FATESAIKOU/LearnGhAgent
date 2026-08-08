#!/usr/bin/env bash
# 硬性驗證 sync-to-mybrain 的 execution log。
#
#     validate-step-sync.sh <log-file>
#
# 與 projects/*/judge/validate-step*.sh 同型：4 個 section + 長度上限。
# 額外多一條——最後一行必須是機器可讀的結果標記，workflow 靠它把 PR 網址
# 貼回 chat，也靠它區分「開了 PR」與「判斷不值得存」。兩者都是成功。
#
# PR 網址分支會用 gh 實查該 PR 是否真的存在——只驗字串形狀的話，模型寫
# 一個不存在的 pull/999 也會 PASS，workflow 就把假網址貼回 chat。
set -euo pipefail
file="${1:?missing file}"
if [[ ! -f "$file" ]]; then echo "FAIL: file not found: $file" >&2; exit 2; fi
content="$(cat "$file")"
if (( ${#content} > 3000 )); then echo "FAIL: $file length ${#content} > 3000" >&2; exit 1; fi
for sec in "## 狀況理解" "## 執行的動作與結果" "## 動作結束後的現狀" "## 其中的決斷點"; do
  if ! grep -qF "$sec" "$file"; then echo "FAIL: $file missing section: $sec" >&2; exit 1; fi
done

# 最後一行（忽略尾端空行）必須是 MYBRAIN_PR 標記。
last_line="$(grep -v '^[[:space:]]*$' "$file" | tail -1)"
if [[ "$last_line" =~ ^MYBRAIN_PR:\ https://github\.com/FATESAIKOU/MyBrain/pull/([0-9]+)$ ]]; then
  pr_number="${BASH_REMATCH[1]}"
  if ! gh pr view -R FATESAIKOU/MyBrain "$pr_number" --json number -q .number >/dev/null 2>&1; then
    echo "FAIL: $file 標記的 MyBrain PR #$pr_number 不存在" >&2
    exit 1
  fi
  echo "OK: sync log valid (PR #$pr_number exists)"
elif [[ "$last_line" =~ ^MYBRAIN_PR:\ SKIPPED\ -\ .+$ ]]; then
  echo "OK: sync log valid (skipped, reason recorded)"
else
  echo "FAIL: $file 最後一行必須是 'MYBRAIN_PR: <PR 網址>' 或 'MYBRAIN_PR: SKIPPED - <原因>'" >&2
  echo "      實際讀到: ${last_line}" >&2
  exit 1
fi
