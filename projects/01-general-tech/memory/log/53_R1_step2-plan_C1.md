# 53_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1：取得 PentestGPT repo 的完整 metadata、README、關鍵原始碼結構、論文摘要。此為 R1 首次調研，需建立對該專案的全面理解以支撐後續分析。

## 執行的動作與結果

| 動作 | 目的 | 預期達成效果 | 實際結果 |
|------|------|-------------|---------|
| `gh api repos/GreyDGL/PentestGPT` | 取得完整 repo metadata | 取得 stars/forks/license/topics/語言等 | 成功。13.9k stars, 2.4k forks, MIT, Python 91.4%, topics: llm/penetration-testing |
| `gh api repos/.../contents/pentestgpt` | 列舉 autonomous agent 模組結構 | 了解 v1.0 核心目錄布局 | 成功。core/ interface/ prompts/ 三子目錄 |
| `gh api repos/.../contents/pentestgpt/core` | 列舉 core 模組檔案 | 了解 pipeline/controller/backend/session 等元件 | 成功。10 個檔案含 pipeline.py, controller.py, backend.py, session.py, config.py, events.py, langfuse.py |
| `gh api repos/.../contents/pentestgpt_legacy` | 列舉 legacy 模組結構 | 了解 legacy 互動模式布局 | 成功。main.py, config.py, llm/registry.py, prompts/ 等 |
| `gh api repos/.../contents/pentestgpt/prompts/stages.py` | 讀取 stage prompt 定義 | 了解 CTF/Pentest pipeline 各階段 prompt | 成功。取得完整 prompt 片段（工具列表、flag 模式、持續策略） |
| `gh api repos/.../contents/pentestgpt/core/pipeline.py` | 讀取 pipeline 架構 | 了解 PipelineMode/StageDefinition/StageResult 定義 | 成功。CTF 模式用 DFS, Pentest 模式用 BFS |
| `gh api repos/.../contents/pentestgpt/core/controller.py` | 讀取 controller 實作 | 了解 agent lifecycle 與 flag detection | 成功。5-state 模型 + 6 種 flag pattern regex |
| `gh api repos/.../contents/pentestgpt/core/backend.py` | 讀取 backend 抽象層 | 了解 AgentBackend 介面設計 | 成功。MessageType/AgentMessage/AgentBackend ABC |
| `gh api repos/.../contents/pentestgpt/core/session.py` | 讀取 session 管理 | 了解 SessionInfo/SessionStore 持久化 | 成功。JSON 序列化、pause/resume 支援 |
| `gh api repos/.../contents/pentestgpt/core/config.py` | 讀取設定管理 | 了解 Pydantic-based 設定 | 成功。max_iterations, target, mode, permission_mode 等 |
| `gh api repos/.../contents/pentestgpt/interface/main.py` | 讀取 CLI entry | 了解命令列參數 | 成功。--target, --instruction, --model, --mode 等 |
| `gh api repos/.../contents/pentestgpt/core/pipelines.py` | 讀取 pipeline factory | 了解 CTF/Pentest stage 定義 | 成功。CTF: recon→exploit→walkthrough; Pentest: asset→vuln→report |
| `gh api repos/.../contents/pyproject.toml` | 讀取專案設定 | 了解依賴與工具鏈 | 成功。pydantic, langfuse, openai, anthropic, google-genai 等 |
| `gh api repos/.../readme` | 取得完整 README | 取得專案說明文件 | 成功。含 v1.0 新功能、benchmark、telemetry、citation |
| webfetch USENIX 論文頁面 | 取得論文摘要 | 了解學術背景 | 成功。USENIX Security 2024, Distinguished Artifact Award, 三模組架構 |
| webfetch arxiv | 確認論文 arXiv 位置 | 取得 arXiv 連結 | 失敗。arXiv:2308.06741 為不相關的 MARL 論文，PentestGPT 論文僅在 USENIX |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 驗證結果 |
|---------|---------------|---------|
| Repo metadata 完整性 | 確認 stars/forks/license/topics/language/created/pushed | 完整取得 |
| 原始碼架構理解 | 確認 autonomous agent (v1.0) 與 legacy 兩套系統 | 已理解兩者差異 |
| Pipeline 設計 | 確認 CTF (DFS) 與 Pentest (BFS) 兩種 pipeline | 已理解 stage 順序與 prompt 設計 |
| 論文背景 | 確認 USENIX Security 2024 發表 | 已取得摘要與 citation |
| Benchmark 數據 | 確認 XBOW 86.5% success rate | 已取得成本/時間/難度分層數據 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---------|---------|---------|---------|
| 論文取得方式 | 下載 PDF / 讀 USENIX 摘要頁 | USENIX 摘要頁 | PDF 為二進位無法直接解析，摘要頁已含足夠資訊 |
| 原始碼調研深度 | 僅讀目錄結構 / 讀關鍵檔案內容 | 讀關鍵檔案內容 | 需理解 pipeline/controller/backend 設計以回答「如何解決問題」 |
| Legacy 模式調研 | 略過 / 讀 main.py + registry | 讀 main.py | legacy 模式為論文核心貢獻，需理解其三模組互動設計 |
