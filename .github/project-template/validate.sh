#!/usr/bin/env bash
set -euo pipefail
step="${1:?missing step}"
file="${2:?missing file}"
if [[ ! -f "$file" ]]; then echo "FAIL: file not found: $file" >&2; exit 2; fi
content="$(cat "$file")"
char_count=${#content}
check_max_length() {
  if (( char_count > $1 )); then echo "FAIL: $file length $char_count > max $1" >&2; return 1; fi
}
check_sections() {
  local missing=()
  for sec in "$@"; do grep -qF "$sec" "$file" || missing+=("$sec"); done
  if (( ${#missing[@]} > 0 )); then echo "FAIL: $file missing sections:" >&2; printf '  - %s\n' "${missing[@]}" >&2; return 1; fi
}
case "$step" in
  step-log-short)  check_max_length 2000; check_sections "## 狀況理解" "## 執行的動作與結果" "## 動作結束後的現狀" "## 其中的決斷點" ;;
  step-log-medium) check_max_length 3000; check_sections "## 狀況理解" "## 執行的動作與結果" "## 動作結束後的現狀" "## 其中的決斷點" ;;
  step-log-long)   check_max_length 6000; check_sections "## 狀況理解" "## 執行的動作與結果" "## 動作結束後的現狀" "## 其中的決斷點" ;;
  report)
    check_max_length 50000; check_sections "## 1." "## 2." "## 3." "## 4."
    basename="$(basename "$file")"
    if ! [[ "$basename" =~ ^[0-9]+_.+\.md$ ]]; then echo "FAIL: report filename '$basename' does not match (pr-id)_(tech).md" >&2; exit 1; fi
    ;;
  *) echo "FAIL: unknown step '$step'" >&2; exit 2 ;;
esac
echo "ALL CHECKS PASSED: $step $file"