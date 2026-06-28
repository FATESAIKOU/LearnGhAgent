#!/usr/bin/env bash
set -euo pipefail
file="${1:?missing file}"
if [[ ! -f "$file" ]]; then echo "FAIL: file not found: $file" >&2; exit 2; fi
content="$(cat "$file")"
if (( ${#content} > 3000 )); then echo "FAIL: $file length ${#content} > 3000" >&2; exit 1; fi
for sec in "## 狀況理解" "## 執行的動作與結果" "## 動作結束後的現狀" "## 其中的決斷點"; do
  if ! grep -qF "$sec" "$file"; then echo "FAIL: $file missing section: $sec" >&2; exit 1; fi
done
echo "OK: step3 log valid"
