#!/usr/bin/env bash
set -euo pipefail
file="${1:?missing file}"
if [[ ! -f "$file" ]]; then echo "FAIL: file not found: $file" >&2; exit 2; fi
content="$(cat "$file")"
if (( ${#content} > 50000 )); then echo "FAIL: $file length ${#content} > 50000" >&2; exit 1; fi
for sec in "## 1." "## 2." "## 3." "## 4."; do
  if ! grep -qF "$sec" "$file"; then echo "FAIL: $file missing section: $sec" >&2; exit 1; fi
done
basename="$(basename "$file")"
if ! [[ "$basename" =~ ^[0-9]+_.+\.md$ ]]; then
  echo "FAIL: report filename '$basename' does not match (pr-id)_(tech).md" >&2; exit 1
fi
echo "OK: report valid"
