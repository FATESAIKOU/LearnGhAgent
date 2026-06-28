#!/usr/bin/env bash
# 硬性驗證腳本：檢查 step 產出是否符合 AGENTS.md 規定的格式
# 用法：
#   ./validate.sh <step> <file-path>
#   step 可選值：
#     step-log    : 驗證通用 step log（4 個通用 section，用於 Step1/2/3/4 的 log）
#     report      : 驗證 output/ 摘要報告
#
# 回傳 0 = 通過，非 0 = 失敗（錯誤訊息印到 stderr）
set -euo pipefail

step="${1:?missing step}"
file="${2:?missing file}"

if [[ ! -f "$file" ]]; then
  echo "FAIL: file not found: $file" >&2
  exit 2
fi

content="$(cat "$file")"
char_count=${#content}

check_max_length() {
  local max="$1"
  if (( char_count > max )); then
    echo "FAIL: $file length $char_count > max $max" >&2
    return 1
  fi
  echo "OK: $file length $char_count <= $max"
}

check_sections() {
  local -a required=("$@")
  local missing=()
  for sec in "${required[@]}"; do
    if ! grep -qF "$sec" "$file"; then
      missing+=("$sec")
    fi
  done
  if (( ${#missing[@]} > 0 )); then
    echo "FAIL: $file missing sections:" >&2
    printf '  - %s\n' "${missing[@]}" >&2
    return 1
  fi
  echo "OK: $file has all required sections"
}

case "$step" in
  step-log)
    check_max_length 8000
    check_sections "## 狀況理解" "## 執行的動作與結果" "## 動作結束後的現狀" "## 其中的決斷點"
    ;;
  step-log-short)
    check_max_length 2000
    check_sections "## 狀況理解" "## 執行的動作與結果" "## 動作結束後的現狀" "## 其中的決斷點"
    ;;
  step-log-medium)
    check_max_length 3000
    check_sections "## 狀況理解" "## 執行的動作與結果" "## 動作結束後的現狀" "## 其中的決斷點"
    ;;
  step-log-long)
    check_max_length 6000
    check_sections "## 狀況理解" "## 執行的動作與結果" "## 動作結束後的現狀" "## 其中的決斷點"
    ;;
  report)
    check_max_length 50000
    check_sections "## 1." "## 2." "## 3." "## 4."
    basename="$(basename "$file")"
    if ! [[ "$basename" =~ ^[0-9]+_.+\.md$ ]]; then
      echo "FAIL: report filename '$basename' does not match (pr-id)_(date).md" >&2
      exit 1
    fi
    echo "OK: report filename format"
    ;;
  *)
    echo "FAIL: unknown step '$step' (use: step-log|step-log-short|step-log-medium|step-log-long|report)" >&2
    exit 2
    ;;
esac

echo "ALL CHECKS PASSED: $step $file"
