# 150_R1_step2-plan_C1.md

## 狀況理解

Step 2 的第一個 sub-step C1：取得 terminal-browser 的 repo metadata 與主要文件。使用者要求的三個調查面向（亮點對比、問題背景解法、穩定性評估）都需要原始專案細節才能回答。本 step 負責收集原始資料，不進行分析。

## 執行的動作與結果

| 動作 | 目的 | 預期達成效果 | 實際結果 |
|------|------|-------------|---------|
| `gh repo view` + `gh api repos/...` | 取得 repo metadata | 獲得 stars/forks/language/created/license 等 | 成功。473 stars, 20 forks, 建立於 2026-07-06，無 license，主要語言 Rust |
| `gh api repos/.../languages` | 取得語言組成 | 了解技術棧 | 成功。Rust 761KB, TypeScript 438KB, JavaScript 15KB, Swift 13KB, Shell 10KB, Just 1KB |
| `gh api repos/.../readme` | 取得 README.md | 了解專案說明與使用方式 | 成功。取得完整 README，含安裝、使用、架構說明 |
| `webfetch terminal-browser.com` | 取得官網內容 | 了解產品定位與展示 | 成功。官網展示 split pane、agent 操作、SSH 等場景 |
| `gh api repos/.../releases/latest` | 取得最新 release 資訊 | 了解版本狀態 | 成功。v0.3.2，2026-07-30 發布 |
| `gh api repos/.../contents` | 列出 repo 根目錄結構 | 了解專案組織 | 成功。目錄：browser/, cli/, engine/, skill/, store/, terminals/ 等 |
| 讀取 CLAUDE.md / AGENTS.md | 取得開發慣例 | 了解團隊 coding style | 成功。不寫註解、不寫向後相容邏輯 |
| 讀取 skill/SKILL.md | 取得 agent skill 定義 | 了解 agent 操作介面 | 成功。agent-browser 相容 CLI，支援 snapshot/click/fill/eval |
| 讀取 engine/Cargo.toml | 取得 Rust 引擎依賴 | 了解底層實作 | 成功。pixel-core + pixel-node，依賴 tiny-skia, fontdue, taffy 等 |
| 讀取 browser/package.json | 取得 Electron 層設定 | 了解前端架構 | 成功。Electron 43.1.1, React 18, pixel-react |
| 讀取 cli/package.json | 取得 CLI 層設定 | 了解 CLI 架構 | 成功。TypeScript CLI，依賴 pixel-store, pixel-terminals |
| `gh api repos/.../issues` | 取得 open issues | 了解已知問題 | 成功。5 open issues：brew formulae, persist partitions, iTerm click bug, Linux support(WIP), SSH browser |
| `gh api repos/.../pulls` | 取得 open PRs | 了解進行中的開發 | 成功。3 open PRs（與 issues 重疊） |
| `webfetch kitty graphics protocol` | 查 Kitty graphics protocol 文件 | 了解底層通訊協定 | 成功。取得完整協定規格文件 |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 驗證結果 |
|---------|-------------|---------|
| Repo metadata | stars/forks/language/license/created | 473/20/Rust/無 license/2026-07-06 |
| 最新版本 | v0.3.2, 2026-07-30 | 專案僅 25 天，已發布 3 個 minor 版本 |
| 支援平台 | macOS Apple Silicon only | Linux WIP (PR #4) |
| 架構理解 | Electron offscreen rendering + Rust pixel engine + Kitty protocol | 完整取得 |
| Agent 操作介面 | agent-browser 相容 CLI | 支援 snapshot/click/fill/eval |
| 已知問題 | 5 open issues | iTerm click bug, 無 Linux 支援, 無 brew formula |
| License | 無 license 檔案 | 新聞與 repo 皆確認無 license |
| 開發者 | Rob Pruzan (zenbu-labs) | 單一開發者，無其他 contributor 資料 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---------|---------|---------|---------|
| 是否讀取所有子目錄原始碼 | 是 / 僅讀取關鍵文件 | 僅讀取關鍵文件 | 6000 字限制，原始碼細節留待 Step 3 分析時按需補查 |
| 是否查詢 commits 歷史 | 是 / 否 | 嘗試但 API 回傳空 | API 可能因 repo 過新或 rate limit 無資料，不影響分析 |
| 是否查詢 contributor 列表 | 是 / 否 | 嘗試但 API 回傳空 | 同上，推測為單一開發者專案 |
| 是否查詢替代方案背景 | 是 / 否 | 否 | 留待 Step 2 C2 或 Step 3 再做 |
