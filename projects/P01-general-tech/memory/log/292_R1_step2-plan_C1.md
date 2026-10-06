# 292_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1 任務：取得 Paperclip（`paperclipai/paperclip`）repo metadata 與主要文件。R1 首次調研，無前輪。Step 1 交棒缺口：功能與架構、manage agents 的機制、與既有前案異同、影片 133 期無字幕、97,403 stars 真偽與活躍度。C1 聚焦 metadata＋文件，替代方案與市場交叉查證留待 C2。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` 取 metadata | 驗證 PR body 數值 | 確認 stars/license/語言/時間 | 97,420 stars、MIT、TypeScript、2026-03-02 建立、預設分支 `master`、fork 16,478、homepage paperclip.ing |
| `gh api` 列根目錄 | 掌握 repo 結構 | 找出關鍵文件 | 有 README/DESIGN/AGENTS/ROADMAP/adapter-plugin、`server/`、`ui/`、`packages/`、`cli/`、`doc/`、`skills/` |
| curl raw README.md（593 行） | 取得自述與問題陳述 | 取得 §1、§3 素材 | 四支柱、功能表、Without/With 對照、架構圖、FAQ、Roadmap、telemetry |
| curl DESIGN.md／AGENTS.md／ROADMAP.md／package.json | 補架構與工程邊界 | 確認技術棧與 repo map | server=Express REST、ui=React+Vite、db=Drizzle、pnpm workspace、Node 24.11+、Rust runner |
| curl `doc/GOAL.md`、`doc/PRODUCT.md` | 取得定位與核心概念 | 補「問題背景」與機制 | 明列「control plane not execution plane」、company 為單位、adapter 定義 agent、任務須追溯公司 goal |
| `gh api releases`／`commits`／`languages` | 查活躍度真偽 | 交叉驗證 | 最新 release v2026.1001.0（2026-10-02）；最新 commit 2026-10-05；TypeScript 87.8MB、Rust 2.7MB |
| `curl registry.npmjs.org/paperclipai` | 查發布狀態 | 確認可否安裝 | npm 首發 2026-03-03、latest 2026.1001.0、有 beta/nightly/canary |
| `gh repo view openclaw/openclaw` | 查 README 關鍵類比 | 確認定位 | OpenClaw 391,421 stars，MIT，TypeScript |

**關鍵發現**：README 核心定位句「If OpenClaw is an *employee*, Paperclip is the *company*.」——Paperclip 不執行 agent，而是編排多 agent 成「公司」（org chart／budgets／governance／goal alignment）。支援 adapter：Claude Code、Codex、Cursor、Gemini CLI、OpenCode、Pi、Hermes、Grok、Kimi、OpenClaw、自訂 HTTP/process。四支柱：Agentic Task Manager、Org Chart for Agents、Agent Employee Training、Agentic OS。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| stars 真偽 | `gh repo view` + commits 活躍度 | 97,420 屬實（PR body 97,403 為查詢時點落差），每日多次 commit |
| license／語言 | `gh repo view`／`languages` | MIT、TypeScript 為主，含 Rust runner |
| 專案活躍度 | releases + commits | 高活躍，release 每 1-2 週 |
| 架構層級 | README + GOAL + PRODUCT | control plane（server+UI）vs execution（adapter），明確分離 |
| 管理機制 | README 四支柱 | 任務/org chart/訓練/infra 四軸，含 heartbeat、budget hard-stop、approval gate |
| 定位類比 | README + OpenClaw metadata | OpenClaw=employee、Paperclip=company |
| 文件完整度 | repo 根 + `doc/` | `doc/` 逾 60 檔，含 SPEC、PRODUCT、GOAL、DATABASE |

**C2 待補缺口**：
1. 與 MyBrain 既有前案（munder-difflin／Buzz／Aionui／maka）的切入點異同 → 支撐 §4 DA 表。
2. 同級替代方案（如 Paperclip 對照 OpenClaw 生態、Asana/Trello＋agent、其他 agent 編排工具）。
3. 影片 133 期無字幕，改尋文字版（GitHub Trending 週報）或於報告註記缺口。
4. §3 機制細節：atomic checkout、heartbeat 執行流、budget hard-stop 的具體運作。
5. `doc/SPEC.md`／`doc/architecture/` 若需更深機制再抓。

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| metadata 來源 | PR body 數值 / `gh api` 實查 | 以 `gh api` 為準 | PR body 為轉錄值，需交叉驗證 |
| 文件取用順序 | README 為主 / README+GOAL+PRODUCT | README+GOAL+PRODUCT | README 為行銷面，GOAL/PRODUCT 提供問題與機制定義 |
| 是否抓 SPEC.md | 抓 / C2 再抓 | C2 再抓 | C1 已足證定位，避免超量；SPEC 留待機制章節 |
| 影片缺口處理 | 假裝看過 / 明列缺口 | 明列缺口交 C2 | 不可虛構未取得資料 |
| OpenClaw 查證 | 不查 / 查 metadata | 查 | README 以此類比定位，須確認其真實性 |
| 前案比較 | C1 一併做 / 留 C2 | 留 C2 | C1 專注 metadata 與文件，避免 log 超長 |
