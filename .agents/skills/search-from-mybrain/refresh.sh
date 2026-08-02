#!/usr/bin/env bash
# 確保第二大腦（FATESAIKOU/MyBrain）在固定位置且是最新的。
#
#     bash refresh.sh            # 更新到 /tmp/mybrain
#     MYBRAIN_DIR=~/x bash refresh.sh
#
# 冪等——重複執行沒有代價。兩個地方會呼叫它：
#
#   1. session 啟動時（Claude Code 的 SessionStart hook／opencode plugin）
#      ——為了速度，查詢時鏡像已經是熱的
#   2. search-from-mybrain skill 每次搜尋之前
#      ——為了正確性，hook 沒跑、session 開很久、CI 環境都還是有效
#
# 這是唯讀鏡像。要寫東西進第二大腦一律走 /sync-to-mybrain，不要碰這裡。

set -uo pipefail

DEST="${MYBRAIN_DIR:-/tmp/mybrain}"
REPO="FATESAIKOU/MyBrain"

# MyBrain 是 private repo，內容含個人醫療、財務、身份資料。/tmp 是全機器
# 可讀的，所以目錄權限收到 700——固定路徑的方便性與內容的私密性都要。
umask 077

if [ -d "$DEST/.git" ]; then
  # 刻意用 fetch + reset --hard 而不是 pull：這是唯讀鏡像，不需要保留本機
  # 變更。shallow clone 碰到 force-push 或本機被誤寫時 pull 會卡住，硬 reset
  # 永遠成功。
  if git -C "$DEST" fetch --depth 1 -q origin main 2>/dev/null; then
    git -C "$DEST" reset --hard -q origin/main
    git -C "$DEST" clean -qfd
  else
    # 沒網路、gh token 過期都會走到這。**不要 exit 1**——session 啟動不能
    # 因為抓不到更新就壞掉，沿用舊副本並說清楚它可能過期即可。
    echo "⚠️  更新失敗，沿用既有副本（可能過期）: $DEST" >&2
  fi
else
  if ! command -v gh >/dev/null 2>&1; then
    echo "❌ 找不到 gh。MyBrain 是 private repo，需要 gh 的認證才能取得。" >&2
    exit 1
  fi
  rm -rf "$DEST"
  mkdir -p "$DEST"
  chmod 700 "$DEST"
  # 用 gh repo clone 而不是裸 git clone——private repo 需要 gh 的認證
  if ! gh repo clone "$REPO" "$DEST" -- --depth 1 -q; then
    echo "❌ clone 失敗。先確認 gh auth status。" >&2
    rm -rf "$DEST"
    exit 1
  fi
fi

echo "✅ $DEST @ $(git -C "$DEST" log -1 --format='%h %ad %s' --date=short)"
