#!/usr/bin/env bash
# 硬性驗證腳本：檢查 step 產出是否符合 AGENTS.md 規定的格式
# 用法：
#   ./validate.sh <step> <file-path>
#   ./validate.sh req <file>           # 驗證 Step 1 意圖理解產出
#   ./validate.sh execution-log <file> # 驗證 Step 2 執行記錄
#   ./validate.sh report <file>        # 驗證 Step 4 分析報告
#   ./validate.sh summary <file>       # 驗證 Step 4 summary
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
  req)
    check_max_length 2000
    check_sections "## 標的" "## 使用者意圖" "## 關鍵條件" "## 缺乏資訊"
    ;;
  execution-log)
    check_max_length 6000
    check_sections "## 狀況理解" "## 執行的動作與結果" "## 動作結束後的現狀" "## 其中的決斷點"
    ;;
  report)
    check_max_length 20000
    check_sections "## 1." "## 2." "## 3." "## 4."
    # 檔名格式：(日期)-(技術名).md
    basename="$(basename "$file")"
    if ! [[ "$basename" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}-.+\.md$ ]]; then
      echo "FAIL: report filename '$basename' does not match (date)-(tech).md" >&2
      exit 1
    fi
    echo "OK: report filename format"
    ;;
  summary)
    check_max_length 1000
    check_sections "## 本輪產出" "## 變更摘要" "## 待追問"
    ;;
  *)
    echo "FAIL: unknown step '$step' (use: req|execution-log|report|summary)" >&2
    exit 2
    ;;
esac

echo "ALL CHECKS PASSED: $step $file"