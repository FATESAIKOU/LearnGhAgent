# 290_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1：取得 `TencentCloud/Octop` 的 repo metadata 與主要文件。Step1 已定位其為「self-hosted 多用戶／多 agent AI 助理」，並要求本輪查證「開源版 WorkBuddy」的實際對標，避免定位偏移。故 C1 需盤點：metadata 與時序、檔案結構、README 與核心 docs（架構、ADR、AgentTeams/agent 委派）、同廠衛星 repo，並補查官方與媒體對 WorkBuddy 關係的說法。替代方案與 MyBrain 對照留 C2。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` + `gh api repos/...` | 取 metadata | stars/license/語言/時序 | 6855 stars、852 forks、675 open issues、59 watchers、MIT、primary Python、created 2026-07-08、pushed 2026-10-05、homepage octop.cloud |
| `gh api .../topics` | 取標籤 | 判定位 | agent / agentic-ai / ai / ai-agent / ai-agents / local-first / long-term-memory |
| `gh api .../git/trees?recursive=1` | 取完整結構 | 確認組成 | 4347 路徑：src 2138、dashboard 1372、tests 541、desktop 87、fnos 70、docs 48、plugins 23、docker 11 |
| `gh api .../readme` | 取 README | 定位與功能 | 579 行，完整產品說明（見下） |
| `gh api .../releases` | 取版本時序 | 活動度 | v1.0.2b6（2026-10-04）、b5、b4、b3、b2；beta 節奏 |
| `gh api .../commits` | 確認活躍度 | 近期開發 | 2026-10-04 release 1.0.2b6；09-29 b5；09-27 README roadmap |
| 讀 `docs/architecture.md` | 取架構一手文件 | 機制理解 | 分層、單一進程、per-user row 級隔離、三種對話 surface、儲存 |
| 讀 `docs/adr/001`、`002` | 取設計決策 | 單進程理由 | 無外部 queue、SQLite WAL 預設、PostgreSQL 選配 |
| 讀 `docs/expert-teams.md` | 取 AgentTeams 設計 | multi-agent 機制 | 23 條已確認決策、kind=team、房=主持人 thread_id、成員 checkpoint=`主thread~成員id` |
| 讀 `docs/agent-delegation.md` | 取非同步委派 | agent 互調 | `ask_agent(background)` 入 harness inbox 串行執行、完成回叫 |
| 讀 `octop-harness` README | 確認 runtime 底層 | 技術根 | 封裝 LangChain `deepagents.create_deep_agent`、17 家 provider 預設 |
| 查 4 個衛星 repo | 確認 stack 關係 | 同廠模組 | octop-harness/33★、octop-gateway/28★、octop-memory/26★、octop-browser/22★，皆 2026-09-24 建、MIT |
| `webfetch` DuckDuckGo＋Bing＋官網 | 補背景脈絡 | 釐清 WorkBuddy 關係 | 見「背景脈絡」 |

**metadata 與結構事實**

| 面向 | 內容 |
|---|---|
| 一句定位 | 自架、多用戶、多 agent 的 AI 助理平台：單一 Python 進程同時提供 Web dashboard、CLI、IM 通道與 cron |
| Stack | Python3.12＋FastAPI/uvicorn；React18＋TS＋Vite＋Ant Design；SQLite(WAL) 或 PostgreSQL；APScheduler；hatchling/ruff/mypy/pytest |
| Runtime 底層 | octop-harness（LangGraph，封裝 deepagents）；octop-gateway（IM）；octop-memory（階層式召回＋FTS）；octop-browser（CDP 無 Playwright） |
| 核心架構 | 單進程、無外部 queue（ADR001）；DI root `SharedServices`；每 agent 一個 `HarnessAgentRuntime`；per-user 以 JWT＋`agents.user_id` row 級隔離 |
| 對話 surface | Web UI(WS)、CLI(內嵌 server/WS)、IM channel(gateway)、Cron(APScheduler)，共用同一 agent runtime 與 `HarnessProcessor` |
| Multi-agent | AgentTeams(Beta)：主持人（kind=team，輕量工具）＋成員專家；非同步 `ask_agent`／inbox；房=主持人 thread_id，成員各自 checkpoint |
| 功能覆蓋 | 專家庫/市場、MBTI 人格、Skills、MCP/Connector、知識庫 RAG、可攜記憶、瀏覽器/終端 AI、遠端桌面、桌面客戶端、FnOS 套件、acp 雙向 |
| 授權/社群 | MIT；852 forks；約 48 頁 contributors（≈48 人）；Discord＋企業微信群 |

**背景脈絡（WorkBuddy 關係）**

| 發現 | 來源 | 判讀 |
|---|---|---|
| WorkBuddy = 騰訊自家雲端 AI 辦公工作台；Octop 由騰訊雲團隊開源 | Sohu、ZGEO、騰訊雲社群文 | 媒體稱其「開源版 WorkBuddy」，雙軌並行 |
| 官方未自稱 WorkBuddy 開源版；官網稱「Octop 源自 LightClaw ACE」，是面向 agent 時代的系統性重構 | tencentcloud.github.io/Octop | 「開源版」為媒體標籤，非官方描述 |
| 雙軌定位：WorkBuddy＝職場即用型產品（用 AI）；Octop＝自託管平台（擁有 AI） | 騰訊雲社群文 | 能力重疊但交付模式互補 |
| 有文章誤稱 Octop 是「搬進 IDE 的開源 IDE」 | CSDN（weixin_28839549） | 與 README／結構不符，屬二手誤述，報告需排除 |

**發現的出入**

| 項目 | PR body／媒體說法 | 一手實況 | 判定 |
|---|---|---|---|
| stars | 6,845（2026-10-05 實查） | 6855（本次 API） | 取最新；差異為同日上午後新增 |
| 定位 | 「開源版 WorkBuddy」 | repo 自述 self-hosted multi-user/multi-agent；源自 LightClaw ACE | 以 repo 為準，媒體標籤並列說明 |
| 形態 | 部分文章稱「IDE／coding agent」 | 完整 Web/CLI/IM/桌面產品平台 | 排除誤述 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Repo metadata | stars/forks/issues/license/語言/時序/topics | 完整 |
| 文件覆蓋率 | README＋tree＋architecture＋2 ADR＋expert-teams＋agent-delegation＋harness README | 足以支撐 §1–§3 |
| 機制理解 | 單進程、四 surface、multi-agent（inbox/回叫）、儲存後端 | 清晰 |
| WorkBuddy 關係 | 官網＋搜尋多源交叉 | 已釐清：媒體標籤，官方源自 LightClaw ACE；雙軌 |
| 同廠脈絡 | 4 衛星 repo metadata | 已取得 |
| 背景補充 | 通用技術背景與替代方案 | 留 C2 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件深度 | 只讀 README／讀 arch+ADR+核心 docs／逐 src 精讀 | README＋arch＋2 ADR＋expert-teams＋agent-delegation | C1 為 metadata 與主要文件盤點；原始碼細節留 C2/QA |
| 衛星 repo 處理 | 不查／查 metadata／深入讀 | 查 metadata | 確認 stack 組成即可，深入屬 §3 補充 |
| 「開源版」定位 | 採信／標為媒體用語並查證 | 標為媒體標籤，官方源自 LightClaw ACE | repo 與官網為一手，避免定位偏移 |
| 誤述文章處理 | 略過／並列標記 | 並列標記為誤述 | 避免其污染 §1 定位 |
| stars 時差 | 沿用 PR body／取最新 | 取最新 6855 並註記差異 | API 為即時實況 |

## 交接給 C2

- 補通用背景：雲端 vs 自架 AI 助理的隱私/合規脈絡、multi-agent 編排與 multi-user 隔離的技術背景。
- 補替代方案：WorkBuddy（封閉）、Open WebUI、Dify、Coze、LobeChat、AionUi、munder-difflin 等，做 DA 表。
- 已可用來源：MyBrain 的 MyAiEntry／Ai公司架構／Aionui／TencentDB-Agent-Memory；本輪 4 衛星 repo 與官方雙軌說法。
- 待查證：WorkBuddy 具體產品能力（付費/雲端限制）以支撐 §1/§2 對比。
