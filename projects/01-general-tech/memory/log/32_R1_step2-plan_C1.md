# 32_R1_step2-plan_C1.md

## 狀況理解
Step 1 已確認技術標的為 PentestGPT（greydgl/pentestgpt），調研範圍為深入程式架構、論文內容、替代方案比較。本 sub-step C1 依 do/skills/document/SKILL.md 執行標準調研動作：取得 repo metadata、擷取主要文件（README、CLAUDE.md、pyproject.toml、核心原始碼）、補查背景脈絡（USENIX 論文摘要、官方網站）。目標是為後續 sub-step（C2 替代方案搜尋、C3 收斂撰寫）建立完整資訊基礎。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` | 取得 stars、license、語言、release、topics 等結構化資訊 | 建立專案量化輪廓 | 13,840 stars、2,398 forks、MIT license、Python 91.4%、v1.0.0（2025-12-24）、46 issues、13 PRs |
| `gh api` 列出目錄結構 | 確認雙模式架構（pentestgpt/ + pentestgpt_legacy/） | 理解專案組織 | pentestgpt/（core/、interface/、prompts/）、pentestgpt_legacy/（llm/、utils/、prompts/）、tests/、Dockerfile |
| `curl` README.md | 取得功能說明、benchmark、多模型支援表 | 建立功能全貌 | v1.0 agentic upgrade、雙模式、XBOW 86.5%、8 provider 支援表、telemetry 說明 |
| `curl` CLAUDE.md | 取得內部架構指引、測試指令、關鍵模式 | 理解 v1.0 pipeline 設計 | PipelineOrchestrator iteration loop、AgentController 5-state、EventBus singleton、ClaudeCodeBackend subprocess |
| `curl` pyproject.toml | 取得依賴、entry point、開發工具配置 | 理解技術棧 | Python 3.12+、uv、hatchling、pydantic/langfuse/prompt-toolkit/rich/openai/anthropic/google-genai、ruff/mypy/pytest |
| `curl` core/pipeline.py | 理解 pipeline 編排機制 | 取得 StageDefinition、PipelineOrchestrator 實作 | PipelineMode(CTF/PENTEST)、每 stage fresh backend+controller、context file 注入 |
| `curl` core/controller.py | 理解 agent 生命週期與 flag 偵測 | 取得 5-state、pause/resume、flag regex | AgentState(IDLE/RUNNING/PAUSED/COMPLETED/ERROR)、6 組 flag regex、EventBus 訂閱 |
| `curl` core/session.py | 理解 session 持久化 | 取得 SessionInfo、SessionStore CRUD | ~/.pentestgpt/sessions/ JSON 儲存、支援 create/load/list/delete/resume |
| `curl` core/backend.py | 理解 LLM backend 抽象層 | 取得 AgentBackend ABC、ClaudeCodeBackend | `claude -p` subprocess + JSON lines stdin/stdout、OpenRouter auth mode |
| `curl` core/pipelines.py | 理解 CTF/Pentest pipeline stage 定義 | 取得兩種 3-stage pipeline | CTF: recon→exploit(DFS)→walkthrough、Pentest: asset_id→vuln_id(BFS)→report |
| `curl` prompts/stages.py | 理解各 stage prompt 模板 | 取得工具清單、flag pattern、fallback | _TOOLS（15+ 工具）、_FLAG_PATTERNS、_PERSISTENCE、_FALLBACK_STRATEGIES（5 類 stuck 替代方案） |
| `curl` legacy/main.py | 理解 legacy CLI entry | 取得 --list-models、--smoke-test 等參數 | argparse CLI、display_models()、run_interactive() 啟動 3-session |
| `curl` legacy/llm/registry.py | 理解多模型註冊機制 | 取得 ProviderInfo、ModelSpec、8 provider | PROVIDERS dict、OpenAI-compatible providers 共用 connector |
| `webfetch` USENIX 論文頁 | 取得摘要、作者、artifact evaluation | 理解學術背景 | 10 作者、Distinguished Artifact Award、三模組（reasoning/generation/parsing）、228.6% vs GPT-3.5、artifact 三項全過 |
| `webfetch` pentestgpt.com | 取得架構圖、capabilities、results | 補 README 未涵蓋資訊 | 三模組 pseudo-code、v1.0 三大特性、四項 capabilities、GPT-3.5 35%→GPT-4 47%→PentestGPT 80% |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Repo metadata 完整性 | 檢查 stars、license、release、語言、topics、issue/PR 數是否全部取得 | 全部取得，無缺失欄位 |
| 目錄結構理解 | 確認 pentestgpt/ 與 pentestgpt_legacy/ 兩大模組的子目錄均已列出 | 已完整列出：core/（8 檔案）、interface/（3 檔案）、prompts/（2 檔案）、legacy llm/（含 registry/factory/client/providers）、legacy utils/、legacy prompts/ |
| v1.0 agentic pipeline 理解 | 確認 pipeline.py、controller.py、backend.py、session.py、pipelines.py、prompts/stages.py 均已讀取 | 全部讀取，已理解：PipelineOrchestrator iteration loop、AgentController 5-state、ClaudeCodeBackend subprocess、SessionStore file-based、CTF/PENTEST 各 3-stage pipeline、完整 prompt 模板 |
| Legacy 互動模式理解 | 確認 main.py、registry.py 均已讀取 | 已理解：3-session 架構（reasoning/generation/parsing）+ PTT、8 provider 註冊表、OpenAI-compatible 統一 connector |
| 論文背景資訊 | 確認 USENIX 頁面取得摘要、作者、artifact evaluation | 已取得：10 作者、Distinguished Artifact Award、三模組設計動機（context loss）、228.6% 效能提升、artifact 三項全過 |
| 官方網站補充資訊 | 確認 pentestgpt.com 取得 capabilities、results 對照表 | 已取得：四項 capabilities、GPT-3.5/GPT-4/PentestGPT 效能對照表（35%/47%/80%） |
| 資訊缺口識別 | 檢查是否仍有未涵蓋的調研面向 | 替代方案比較（§4 DA 表）尚未執行，需在 C2 進行；論文全文 PDF 尚未下載（USENIX 頁面提供下載連結，C2 可嘗試取得） |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 核心原始碼擷取深度 | A. 僅讀 CLAUDE.md 架構摘要；B. 讀取 pipeline/controller/backend/session/pipelines/prompts 全部核心檔案 | 選擇 B | Step 1 已決斷需深入程式架構，CLAUDE.md 僅提供摘要，實際 prompt 模板、flag regex、stage 定義等細節需從原始碼取得，對 §3（核心機制）說明至關重要 |
| Legacy 模組擷取範圍 | A. 僅讀 main.py entry；B. 加讀 registry.py 模型註冊表 | 選擇 B | README 的多模型支援表是關鍵功能，registry.py 是該表的 single source of truth，需確認 ProviderInfo/ModelSpec 結構以準確描述多模型支援機制 |
| 論文資訊取得方式 | A. 僅依賴 USENIX 頁面摘要；B. 嘗試下載 PDF 全文 | 選擇 A（C1 階段），C2 再嘗試 PDF | USENIX 頁面摘要已提供足夠的 §2（問題背景）資訊：context loss 問題、三模組設計動機、228.6% 效能數據。PDF 全文可在 C2 嘗試取得以補充實驗細節 |
| 官方網站是否需擷取 | A. 跳過（README 已涵蓋）；B. 擷取以補足視覺化資訊 | 選擇 B | pentestgpt.com 提供 README 未有的 pseudo-code 架構圖、capabilities 分類、GPT-3.5/GPT-4/PentestGPT 對照表，對 §3 與 §4 的說明有補充價值 |
| 是否在此 sub-step 就開始替代方案搜尋 | A. 一併執行；B. 留到 C2 | 選擇 B | C1 聚焦於標的專案本身的文件與架構，替代方案搜尋需要額外的網路搜尋與比較分析，應獨立為 C2 以避免 C1 log 過長 |
