# 304_R1_step2-plan_C1

## 狀況理解

Step 1 已判定：R1 全新主題，標的為 OpenRig（mvschwarz/openrig），使用者要的是「多個 CLI agent 如何被組織成團隊」的內容解析，非重新查 metadata。C1 任務為依 document skill 標準動作：取 repo metadata、擷取 README 與關鍵子文件、補背景脈絡。影片無字幕軌，故以 repo 一手文件＋作者部落格補齊「為何推這支、解決什麼」的缺口。使用者既有 herdr 手工四 pane 流程為現行參照，需在資料中確認 OpenRig 與 herdr 的關係。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` / `gh api repos/...` | 取結構化 metadata | 掌握星數、語言、時序、topics | 成功：7,578★、592 fork、Apache-2.0、TS 為主（33017KB vs 其餘合計 <1MB）、建於 2026-04-01、topics 含 multi-agent/agent-orchestration/tmux |
| `gh api ../releases`、npm registry | 確認版本與活躍度 | 掌握發布節奏 | v0.6.10（2026-10-12）為最新；npm 首發 2026-04-06，5 個月內迭代至 0.6.x；open issues 177、subscribers 30 |
| 取 README.md（476 行） | 了解定位、安裝、核心概念 | 取得一手自述 | 成功：一句定位「A harness wraps a model. A rig wraps your harnesses.」；daemon+CLI+TUI+MCP、tmux 為底 |
| 取 ARCHITECTURE.md | 掌握系統分層與量體 | 理解 request path 與規模 | 成功：五個 package（daemon/cli/tui/ui/test-system）；94 migrations、87 個 rig 指令、18 個 MCP tool、6 個 runtime adapter |
| 取 rig-spec.md | 了解拓樸定義格式 | 確認 YAML 規格 | 成功：RigSpec v0.2 pod-aware；pods/members/edges/continuity_policy/culture_file |
| 取 ROADMAP / CHANGELOG | 了解演進方向 | 判斷成熟度 | 成功：規劃新增 OpenCode/Cursor/Grok/Devin 的共享 adapter |
| 抓 blog「Why I Built OpenRig」 | 補影片缺失的動機脈絡 | 取得作者第一人稱動機 | 成功：reboot 後 30 分鐘無法重建 agent 拓樸的痛點 |
| 查 herdr npm | 釐清與使用者現行流程關係 | 確認第三方或內建 | herdr 為外部套件（ogulcancelik/herdr，terminal workspace manager），OpenRig 預設安裝並整合 |

一手文件關鍵事實（供 Step 3 分析）：

- **定位層級**：harness（包 model）之上再加一層 rig（包 harnesses）。管理的是「agent 團隊」而非 agent 本身：哪些 session 在跑、彼此關係、重開機後如何恢復。
- **核心機制**：本機 daemon（Hono HTTP，預設 port 7433）＋SQLite＋tmux＋runtime adapter。CLI/TUI/MCP 三個前端皆走 local HTTP。agent 本身不被修改。
- **RigSpec（YAML）**：pods（含 members、edges）＋continuity policy＋culture file；座席（seat）為穩定角色位址如 `dev-build@starter`，對話可換、身份與 context 留存。
- **通訊**：`rig send`／`broadcast`／`chatroom`／`ask`（daemon 端 evidence 搜尋，非第二次 LLM call）／`capture`。
- **Snapshots**：`rig down --snapshot`、`rig up <name>` 還原，逐 node 回報 resumed/fresh-primed/awaiting-decision。
- **內建團隊**：starter（builder+reviewer）／workshop（lead+builder+QA+reviewer）／factory（7 人）；專科隊 code-review／research／pm；secrets-manager（受 agent 操作的 Vault）。
- **Runtimes**：claude-code、codex、pi、omp、terminal、stub 六種 adapter。
- **背景動機（blog）**：痛點是「多 agent 形成有機拓樸後，重開機無法重建、且會忘記某支 agent 的存在」；主張把 context 管理從 session 層提升到 topology 層（distributed context management），三支柱 ontology／epistemology／topology，並以 CULTURE.md 定義群體規範。作者自陳前作為 Cursor 時代的 Agent Focus。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| metadata 一致性 | issue 表 vs `gh api` | 星數 7,569→7,578（當日差）、fork 590→592，其餘相符 |
| repo 是否為真碼庫 | ARCHITECTURE 的量體計數（94 migrations/87 commands/18 tools） | 非空殼，工程量體具體 |
| 標的核心命題 | README 定位句 vs Step 1 判定 | 確認「組織多 agent 成團隊」命題正確 |
| 影片缺口是否可補 | blog＋README 動機段 | 可補：動機、示範（TUI 拓樸圖、snapshot 還原）有具體材料 |
| 與使用者既有流程關係 | herdr npm 查詢 | herdr 為第三方，OpenRig 整合而非自研，與 Step 1 的「herdr 手工版」對照成立 |
| 替代方案線索 | README 比對頁、ROADMAP | 有 Claude Managed Agents 對照頁；同級方案待 C2 展開 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件取用範圍 | 僅 README／README＋ARCHITECTURE＋spec／全 docs 掃描 | README＋ARCHITECTURE＋rig-spec＋ROADMAP＋CHANGELOG | docs/ 逾 50 檔，C1 只需建立事實基礎與系統分層，細部留後續 sub-step |
| 影片缺口處理 | 略過／以官方文件與作者 blog 補 | 以 blog 補動機、以文件補機制 | 影片無字幕軌，逐字稿不可得；一手來源優於猜測 |
| metadata 是否重查 | 逕用 issue 附表／重查確認 | 重查（gh api） | 星數為動態值，需以實查時間戳鎖定，且補取 issue 未附的 topics/建立時間 |
| 是否深挖程式碼 | 讀 src／只讀頂層文件 | 只讀頂層文件 | 6000 字上限與 C1 定位，核心機制可由 ARCHITECTURE 摘要取得 |
| herdr 關聯處理 | 視為 OpenRig 自研／查證後標為第三方 | 查 npm 後標為第三方整合 | 避免把使用者既有工具誤植為 OpenRig 產物 |
