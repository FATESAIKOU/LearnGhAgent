# 254_R1_step2-plan_C1

## 狀況理解

R1 首次調研，標的為 `chaitanyagiri/munder-difflin`（local multi-agent harness）。本 sub-step C1 依 document skill 標準動作：取得 repo metadata、擷取 README 與關鍵子文件、補查背景脈絡。Step 1 已定位分析角度＝機制描述＋對照他的審計性疑慮與「個人 AiAgent 入口」專案，故 C1 需特別抓取協作機制（hive）、終端/事件平面（SPEC）、記憶層（MEMORY_GRAPH_SPEC）等文件。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` 取 metadata | 取得 stars/license/分支/更新時間 | 確認標的規模與成熟度 | 5,493 stars；MIT（licenseInfo 標 other，README 明示 source code 為 MIT）；main 分支；created 2026-05-31；updated 2026-08-30；primaryLanguage JavaScript；非 fork/非 archived |
| `gh api` 列根目錄 | 盤點關鍵文件 | 找出 README 外的設計文件 | 見 `DESIGN.md`/`HIVE.md`/`SPEC.md`/`MEMORY_GRAPH_SPEC.md`/`CHANGELOG.md`/`docs/`/`blog/`/`src/main/` |
| 抓 README.md | 取得產品定位、架構、功能 | 建立整體心智模型 | 374 行；定位「把終端 agent CLI 包成協作團隊」；架構圖（GOD agent→agents→shared hive）；功能清單完整 |
| 抓 HIVE.md | 取得多 agent 協作層設計 | 理解協作機制核心 | 217 行；git-as-audit 單 committer、single-writer-per-file、god agent 仲裁、FIPA-lite 訊息 schema、Stop-hook 自主迴圈 |
| 抓 SPEC.md | 取得終端/事件平面 | 理解兩 data plane 架構 | 314 行；Terminal Plane（node-pty）+ Event Plane（hooks→UDS）；Sims 隱喻狀態機 |
| 抓 MEMORY_GRAPH_SPEC.md | 取得記憶層視覺化設計 | 理解記憶/知識圖譜 | 212 行；force-directed SVG 圖、topic 抽取、MemPalace 語意記憶 |
| 抓 package.json | 確認技術棧與版本 | 驗證依賴 | v0.4.6；Electron 32 / React 18 / Pixi 8 / xterm 5 / node-pty / better-sqlite3 / zustand / monaco |
| 抓 docs/message-queue.md、CHANGELOG 頭、docs/research 清單 | 補背景脈絡 | 補足協作與演進脈絡 | message-queue 152 行（誰可打字進 agent 終端）；CHANGELOG 0.4.6（中/阿語、自更新、telemetry 收斂）；research 有 v0.3.4/0.3.5 實作計畫 |

**關鍵機制收斂（供後續 sub-step 使用）：**
- **hive**＝本機 git repo（`<harnessHome>/hive/`），僅 main process 單 committer 避免 `index.lock` 衝突；每 agent 只寫自己 `agents/<id>/`，跨 agent 傳遞由 router 把 sender `outbox/` 移到 recipient `inbox/`。
- **god agent（Michael）**＝固定常駐 `claude` 程序，負責 roster/routing、仲裁、blackboard 單一 scribe、task ledger；routine 自行解決，critical（花費/破壞性/scope）才升級給人。
- **自主迴圈**＝`Stop` hook 回 `{"decision":"block"}` 讓 agent 持續 drain inbox，以 `stop_hook_active` + cursor 防無限迴圈。
- **記憶**＝markdown-first（`memory.md` + 共享 blackboard），SQLite FTS；語意層用 MemPalace CLI（非 MCP），detect-and-degrade 為 no-op。
- **兩 data plane**＝Terminal（node-pty 真實位元組）+ Event（hooks→UDS→renderer 驅動 avatar）。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| metadata 完整性 | stars/license/分支/更新時間是否齊全 | 通過：5,493 stars、MIT、main、2026-08-30 更新 |
| 主要文件擷取 | README + 4 份設計文件 + package.json 是否取得 | 通過：README/HIVE/SPEC/MEMORY_GRAPH_SPEC/DESIGN/package.json 全數落地 |
| 背景脈絡補查 | 是否補上協作與演進脈絡 | 通過：message-queue、CHANGELOG、research 清單 |
| 對照 Step 1 角度 | 是否抓到審計性（git audit）與協作機制 | 通過：HIVE 明示 git-as-audit、單 committer、FIPA-lite 訊息 schema |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 抓哪些子文件 | ① 只抓 README ② 抓 README + 4 份設計文件 + package.json | ② | 標的機制核心在 HIVE/SPEC/MEMORY_GRAPH_SPEC，只抓 README 不足以支撐報告 |
| 是否抓 docs/blog 全量 | ① 全量抓取 ② 只抓 message-queue + CHANGELOG 頭 + research 清單 | ② | 避免過度調研；C1 目的為建立骨架，細節留給後續 sub-step 依需補 |
| 背景脈絡來源 | ① 僅 repo 內文件 ② repo 內文件為主，網路補查留待 C2 | ② | 本 sub-step 聚焦 repo 文件；替代方案/技術背景屬報告 §4，留 C2 網路搜尋 |
