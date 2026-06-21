# 20_R2_step2-plan_C1.md

## 狀況理解

Step 1 確認使用者要求調研 GitHub repo `ollama/ollama`。本 sub-step C1 依 SKILL.md 標準調研動作，執行：(1) 取得 repo metadata、(2) 擷取 README.md 與關鍵子文件、(3) 補查背景脈絡。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view ollama/ollama --json ...` | 取得 repo metadata | 取得 stars、license、分支、更新時間等 | 174,616 stars、MIT license、main 分支、2026-06-21 更新、Go 語言 |
| `curl` 抓取 README.md | 取得專案主要說明文件 | 了解專案定位、功能、安裝方式 | 取得完整 README：本地 LLM 執行平台，支援 CLI/REST API/Docker/Python/JS，整合 Claude Code、OpenCode 等工具 |
| `curl` 列出 repo 根目錄 | 了解專案結構與關鍵子文件 | 確認 docs/、api/ 等目錄存在 | 根目錄含 docs/、api/、server/、llm/、cmd/ 等 50+ 項目 |
| `curl` 列出 docs/ 目錄 | 確認關鍵子文件位置 | 找到 API、modelfile、quickstart、development 等文件 | docs/ 含 api.md、modelfile.mdx、quickstart.mdx、development.md、cli.mdx 等 |
| `curl` 抓取 docs/api.md | 取得 API 規格 | 了解 REST API 端點與使用方式 | 取得完整 API 文件：/api/generate、/api/chat、/api/create 等 12 個端點，支援 streaming、structured output、JSON mode |
| `curl` 抓取 docs/modelfile.mdx | 取得模型自訂格式 | 了解 Modelfile 指令與參數 | 取得完整 Modelfile 規格：FROM/PARAMETER/TEMPLATE/SYSTEM/ADAPTER 等指令，支援 Safetensors/GGUF 匯入 |
| `curl` 抓取 docs/quickstart.mdx | 取得快速入門 | 了解基本使用流程 | 取得 quickstart：`ollama` 互動選單、`ollama launch` 啟動工具、`ollama run` 執行模型 |
| `curl` 抓取 docs/development.md | 取得開發建置說明 | 了解原始碼建置方式 | 取得 development 文件：Go + CMake + C/C++ 編譯，支援 CUDA/ROCm/Vulkan/MLX 後端 |
| `curl` 抓取 go.mod | 取得 Go 依賴 | 了解技術棧 | Go 1.26，依賴 gin、cobra、sqlite3、bubbletea 等 |
| `webfetch` Wikipedia | 補查背景脈絡 | 了解歷史、定位、安全性等 | 2023-07-07 首次釋出，使用 llama.cpp 後端，支援本地 LLM 執行，2026-01 有 175,000 台暴露伺服器資安事件 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Repo metadata 完整性 | 確認 stars、license、語言、更新時間 | 完整取得，無缺漏 |
| 主要文件完整性 | README + API + Modelfile + Quickstart + Development | 5 份關鍵文件均已取得 |
| 背景脈絡 | Wikipedia 歷史與技術背景 | 已取得，含版本歷史、安全性事件 |
| 技術棧 | go.mod 確認 Go 版本與依賴 | Go 1.26，gin web framework、llama.cpp 後端 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 子文件選取 | 全部 docs/ 文件 / 僅關鍵文件 | 僅關鍵文件（API、Modelfile、Quickstart、Development） | 其餘文件（faq、troubleshooting、gpu 等）為操作細節，非核心技術說明 |
| 背景資料來源 | Wikipedia / 技術部落格 / 官方文件 | Wikipedia | 提供中立客觀的歷史與定位說明，無行銷偏誤 |
| 是否使用 CDP | 是 / 否 | 否 | 所有 URL 均為公開 GitHub raw 內容，無反爬阻擋 |
