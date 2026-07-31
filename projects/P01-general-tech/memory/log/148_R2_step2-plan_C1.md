# 148_R2_step2-plan_C1.md

## 狀況理解

本 sub-step 為 R2 的第一個調研動作：取得 ego-lite 與 BrowserBase 兩者的 repo metadata、README、關鍵子文件、安裝腳本與核心原始碼。使用者要求「clone/看兩邊程式碼」做深度比較，以及提供官方安裝指南。

## 執行的動作與結果

| 動作 | 目的 | 預期效果 | 實際結果 |
|------|------|----------|----------|
| `gh repo view citrolabs/ego-lite` | 取得 ego-lite metadata | 星數、授權、語言、建立時間 | 7007 stars, MIT, JavaScript, 2026-04-16 |
| `gh repo view FATESAIKOU/BrowserBase` | 取得 BrowserBase metadata | 同上 | 0 stars, 無授權, Shell, 2026-06-07 |
| `git clone --depth 1` 兩 repo | 下載原始碼 | 本地可讀取 | 兩者皆成功 |
| 讀取 ego-lite README.md | 理解專案定位與功能 | 核心敘述、功能表、比較表 | 140 行，含 feature table、vs 競品表、benchmark |
| 讀取 ego-lite AGENTS.md | 理解架構與資料流 | 架構描述、目錄結構、開發指令 | 60 行，含 CDP harness 架構、Space 模型、學習子系統 |
| 讀取 ego-lite SKILL.md | 理解 agent 使用方式 | helper 列表、workflow、caveats | 209 行，含完整 helper reference、ownership policy |
| 讀取 ego-lite install.md + scripts/install.sh | 理解安裝流程 | 234 行 shell script，下載 DMG → 安裝到 /Applications → 啟動 |
| 讀取 ego-lite .claude-plugin/marketplace.json | 確認 Claude Code marketplace 註冊 | 版本 1.2.5, plugin 結構 | 已註冊 marketplace |
| 讀取 ego-lite package/ego-browser/src/index.ts | 核心入口 | installEgoSdk, runMain, CDP 包裝 | 343 行，含 helper injection、ready signal、session 管理 |
| 讀取 ego-lite package/ego-browser/src/helpers.ts | helper 實作 | task space 管理、locator facade | 867 行，含完整 task space ownership policy 實作 |
| 讀取 ego-lite package/ego-browser/src/browser-runtime.ts | CDP runtime | session 管理、event queue、dialog 追蹤 | 326 行，含 15s timeout、2s session TTL、10k event cap |
| 讀取 BrowserBase README.md | 理解專案定位 | 103 行，含問題描述、解法、安裝、使用 |
| 讀取 BrowserBase scripts/install-opencode.sh | OpenCode 安裝腳本 | 39 行，jq 修改 opencode.json + skill symlink |
| 讀取 BrowserBase scripts/install-claude.sh | Claude Code 安裝腳本 | 19 行，claude mcp add + skill symlink |
| 讀取 BrowserBase scripts/chrome-devtools-wrapper.sh | 核心 wrapper | 48 行，啟動 stock Chrome + exec MCP server |
| 讀取 BrowserBase scripts/_vendor.sh | 共用 vendor 邏輯 | 27 行，npm install + skill symlink |
| 讀取官方文件 lite.ego.app/document/ | 補官方安裝指南 | Quick start、ego-browser reference、Skills 說明 | 三頁完整文件 |

## 動作結束後的現狀

| 驗證面向 | 驗證內容 | 結果 |
|----------|----------|------|
| ego-lite 原始碼完整性 | 已讀取入口、helpers、browser-runtime、install script | 已掌握核心架構 |
| BrowserBase 原始碼完整性 | 已讀取 wrapper、installer、vendor script | 已掌握核心架構（~40 行 wrapper + MCP） |
| 安裝指南 | 官方文件 + repo 內 install.md + install.sh | 已取得完整安裝流程 |
| 兩者比較素材 | 四維度（安全性/易用性/Token效率/操作效率）所需資訊 | 已收集足夠，待 C2 分析 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 理由 |
|----------|----------|----------|------|
| 原始碼閱讀深度 | 僅讀 README / 讀核心 source | 讀核心 source（index.ts, helpers.ts, browser-runtime.ts） | 使用者要求「看兩邊程式碼」做深度比較 |
| BrowserBase 原始碼範圍 | 全部腳本 / 僅 wrapper | 全部 4 個腳本 | 總計僅 133 行，可完整閱讀 |
| 官方文件範圍 | 僅 quick start / 含 ego-browser + skills | 含 ego-browser + skills | 安裝指南需要完整理解 skill 註冊機制 |
