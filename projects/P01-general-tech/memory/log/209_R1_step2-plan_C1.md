# 209_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認調研標的為 TencentDB-Agent-Memory（騰訊雲開源的團隊級 Agent 記憶 hub，GitHub: TencentCloud/TencentDB-Agent-Memory）。本 sub-step 需取得 repo metadata 與主要文件，建立對技術本體的第一手理解。標的屬使用者已深耕的 agent-memory 領域（MyBrain 已評估 8+ 同類工具），故 C1 需同時掌握其架構分層與組件，供後續 C2 對照使用者既有立場。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 do/skills/document/SKILL.md | 確認標準調研動作流程 | 依規範執行 | 規範確認：gh repo view → README → 背景脈絡補查 |
| `gh repo view` 取得 metadata | 取得 repo 基本資料 | 掌握 stars、license、分支、更新時間 | 18,612 stars、MIT、預設分支 `feat/server_team`、2026-08-09 更新；description 確認「team-level memory hub」定位 |
| `gh api` 列出 repo 根目錄 | 掌握 repo 結構 | 定位關鍵子文件 | 五大組件：MemoryCore / MemoryKnowledge / MemoryPanel / MemoryProxy / sdk，另有 INSTALL、README_CN、deploy |
| 抓取根 README.md | 理解產品定位與核心機制 | 掌握四類記憶資產、L0-L3 分層、Memory Hub、ACL | 取得完整 README：Chat Memory/Skill/Wiki/CodeGraph 四資產、L0-L3 分層、private/team/restricted/agent 四可見度、PersonaMem benchmark（48%→76%, +59%）、技術實作三原則 |
| 抓取 MemoryCore/README.md | 理解記憶核心 | 掌握 L0-L3 儲存與 API | MemoryCore 為記憶與 metadata 核心，SQLite+local files，BM25 預設檢索，HTTP Gateway :8420，不執行 agent 本身 |
| 抓取 MemoryCore/SKILL.md | 理解 OpenClaw 整合 | 掌握插件安裝與配置 | 提供 openclaw-memory-tencentdb 插件安裝、capture/extraction/pipeline/recall/persona/embedding 配置分組 |
| 抓取 MemoryKnowledge/README.md | 理解知識服務 | 掌握 Wiki + CodeGraph 引擎 | KS 服務（:8421, /v3）：LLM-Wiki（FTS5+知識圖譜）、Code-Graph（符號/呼叫/檔案樹）、Auto-Sync、tools/list+call |
| 抓取 MemoryPanel/README.md | 理解控制台 | 掌握團隊記憶管理 UI | 無狀態控制台（:8123），管理團隊/用戶/Agent/任務與資產綁定，React 前端 |
| 抓取 MemoryProxy/README.md | 理解 LLM 代理 | 掌握透明注入機制 | 透明 LLM 請求代理（:8096）：session init、context injection、write-back、auth、rate-limit；L0/L1 toolize、L2/L3 inject；支援 Claude Code/CodeBuddy 免改碼接入 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata | gh repo view | 18,612 stars、MIT、預設分支 feat/server_team、活躍更新 |
| 產品定位 | 根 README | 團隊級記憶 hub，四類記憶資產 + L0-L3 分層 + Memory Hub 控制面板 + ACL |
| 組件架構 | 各子目錄 README | 四服務分工明確：Core(儲存/處理) / Knowledge(Wiki+CodeGraph) / Panel(控制台) / Proxy(LLM 注入) |
| 框架支援 | README + SKILL.md | OpenClaw、Hermes、Claude Code、CodeBuddy、SDK；Proxy 提供免改碼接入 |
| benchmark | 根 README | PersonaMem 48%→76%（+59%） |
| 使用者既有評估 | Step 1 已查 MyBrain | 無此標的條目；同領域已評估 EverOS/OpenHuman/planning-with-files/codebase-memory-mcp/HermesAgent/LeanCtx/Headroom/context-mode |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件抓取範圍 | (A) 僅根 README (B) 連同四大組件 README + SKILL.md | B | 標的為多服務 monorepo，僅根 README 無法掌握實際架構；需各組件 README 才能理解 L0-L3 儲存、Wiki/CodeGraph 引擎、Proxy 注入機制 |
| 是否深入原始碼 | (A) 讀 src 原始碼 (B) 以 README 為準，原始碼留待 C2 視需要 | B | C1 目標是建立第一手理解，README 已含架構圖與 pipeline；原始碼細節留待 C2 對照使用者 workflow 時再深入 |
| 下一步 C2 方向 | (A) 直接撰寫報告 (B) 補查替代方案與使用者 MyBrain 對照 | B | 標的與使用者自建 MyBrain 高度同域，需在報告中對照其既有 8+ 評估與「理解優先」策略，才能回答「與我的方案差異」 |
