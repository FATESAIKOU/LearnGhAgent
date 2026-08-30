# 252_R1_step2-plan_C1.md

## 狀況理解

R1 首次調研標的為 **maka**（`apache/maka`，Apache Incubating 的 local-first AI agent workspace）。本 sub-step C1 依 document skill 標準動作：取得 repo metadata、擷取 README 與關鍵子文件、補查背景脈絡。目標是建立「問題定義、核心機制、架構邊界」的事實基礎，供後續 C2（替代方案）與報告撰寫使用。無先前輪次，不需針對舊意圖。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view apache/maka --json ...` | 取得 repo metadata | 確認 stars、license、分支、更新時間、語言 | 取得：TypeScript、Apache-2.0、main 分支、**4053 stars**、created 2026-05-27、updated 2026-08-30、description 為 local-first AI agent workspace |
| `gh api .../README.md` | 擷取主文件 | 理解定位、surfaces、能力、架構 | 完整取得：Why Maka、三種 surface（Desktop/TUI/CLI/Eval）、Agent Runtime 能力、本地資料與 recovery、repo layout |
| `gh api .../ARCHITECTURE.md` | 擷取後端架構 | 理解 Runtime Host 單一執行權威與 Eval 邊界 | 取得：Runtime Host 為唯一執行權威、Runtime Event Log 為 canonical source、Agent Graph、Eval 邊界（Experiment/Cell/Attempt）、code boundaries |
| `gh api .../DESIGN.md` | 擷取產品設計 | 理解產品定位與設計系統 | 取得：Creative North Star「The Companion Command Center」、design tokens、surface 深度階梯 |
| `gh api .../docs/architecture/runtime-host-architecture.md` | 擷取 Runtime Host 深讀 | 理解 Host 為何存在、parts、Turn 流程 | 取得：Runtime 工作超越 request connection、State Root 獨佔 lease、Host Kernel/Composition/Domain Module/Hosted Execution 分工、sequence diagram |
| `gh api .../docs/architecture/runtime-core-architecture-draft.md` | 擷取 Runtime core 深讀 | 理解 Event Log 為核心設計 | 取得：**「Log Is the Runtime」**、`State(t)=Project(RuntimeEvents[0..t], policy, config)`、Model-history/UI/Terminal/Recovery 皆為 log 的 projection |
| `gh api .../git/trees/main?recursive=1` | 盤點文件結構 | 定位關鍵子文件與 docs 目錄 | 取得完整 tree：packages/core、storage、mcp、runtime、runtime-host、eval、cli、ui、computer-use；docs/architecture 含 30+ 篇 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata | gh repo view | 4053 stars、Apache-2.0、TypeScript、main、2026-05-27 建立、活躍更新 |
| 定位與 surface | README | local-first agent workspace；Desktop（Electron+React）、TUI/CLI、Eval 三種 surface，皆經 Runtime Host |
| 核心架構 | ARCHITECTURE.md + runtime-core | Runtime Host 單一執行權威；Runtime Event Log 為 semantic source of truth；state 為 log 的 projection |
| 本地資料與 recovery | README | 資料在 Electron userData/workspaces/default（runtime.sqlite、credential-vault.json 等）；resume 預設關閉 |
| 產品定位 | DESIGN.md | Companion Command Center；task 為中心，activity/permissions/failures 可檢視 |
| 本 step 產出 | memory/log/252_R1_step2-plan_C1.md | 已產出，含 4 section |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 深讀文件範圍 | 僅 README / README+ARCHITECTURE / 加 runtime 深讀 | README + ARCHITECTURE + runtime-host + runtime-core 兩篇深讀 | 標的之核心價值在「Event Log 為 source of truth」與「Runtime Host 單一權威」，需深讀確認機制，非僅 surface 描述 |
| 是否讀 DESIGN.md | 是 / 否 | 是 | 產品定位（Companion Command Center）是問題定義與心智模型的重要輸入，且為官方文件 |
| 是否讀 zh-CN 版本 | 是 / 否 | 否 | 英文版為權威，zh-CN 為翻譯，內容重複，節省 token |
| 背景脈絡補查 | 本 step 內完成 / 留待 C2 | 留待 C2 | C1 聚焦 repo 內部事實；替代方案（Buzz/macro/odysseus/Aionui/deepseek-harness）與 Apache Incubating 背景屬外部脈絡，歸 C2 處理 |
