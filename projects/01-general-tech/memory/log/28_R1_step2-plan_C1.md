# 28_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1：取得 ollama/ollama 的 repo metadata 與主要文件。使用者要求調研此 GitHub repo，依 01-general-tech 分析報告格式產出報告。此為 R1 首次調研，需從頭收集資料。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view ollama/ollama --json ...` | 取得 repo metadata（stars, forks, language, license, releases 等） | 取得結構化 metadata | `gh` CLI 不可用，改由 GitHub 頁面擷取 |
| webfetch GitHub repo 頁面 | 取得 repo 基本資訊與統計 | 取得 stars, forks, language, topics, license, releases 等 | 成功取得：175k stars, 16.7k forks, 226 releases, MIT license, 主要語言 Go 66.2% / C 27.0% |
| webfetch README.md | 取得專案說明、安裝方式、API 用法、社群整合列表 | 理解專案定位與功能 | 成功取得完整 README，包含安裝指令、REST API 範例、Python/JS SDK、大量社群整合分類 |
| webfetch docs.ollama.com | 取得官方文件入口 | 了解文件結構 | 成功取得，文件涵蓋 Quickstart、API、Modelfile、Cloud、Integrations 等 |
| webfetch docs.ollama.com/api | 取得 API 參考 | 了解 API 端點與用法 | 成功取得：API 預設在 localhost:11434，支援 generate/chat 端點，無嚴格版本化 |
| webfetch docs.ollama.com/quickstart | 取得快速入門 | 了解使用者體驗流程 | 成功取得：`ollama` 指令啟動互動選單，支援 `ollama run`、`ollama launch` 等 |
| webfetch docs.ollama.com/modelfile | 取得 Modelfile 參考 | 了解模型自訂機制 | 成功取得：Modelfile 為模型藍圖，支援 FROM/PARAMETER/TEMPLATE/SYSTEM/ADAPTER/LICENSE/MESSAGE/REQUIRES 指令 |
| webfetch docs.ollama.com/faq | 取得常見問題 | 了解部署與配置細節 | 成功取得：GPU 相容性、並行請求、Flash Attention、KV cache 量化、環境變數等 |
| webfetch ollama.com | 取得官方網站 | 了解商業模式與雲端服務 | 成功取得：提供免費/Pro($20/mo)/Max($100/mo) 三層雲端方案 |
| webfetch github.com/ollama/ollama/blob/main/docs/development.md | 取得開發指南 | 了解建置方式與架構 | 成功取得：Go + CMake + C/C++ native code，支援 CUDA/ROCm/Vulkan/Metal/MLX 後端 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Repo metadata | 確認 stars, forks, license, language, releases | 175k stars, 16.7k forks, MIT, Go+C, v0.30.10 (2026-06-17) |
| 專案定位 | 從 README 與官網確認 | 「Start building with open models」— 本地 LLM 執行與管理工具 |
| 核心技術棧 | 從 README 與 development.md 確認 | Go 主體 + llama.cpp (C/C++) 後端，支援多 GPU 後端 |
| API 設計 | 從 docs.ollama.com/api 確認 | REST API on :11434，支援 generate/chat/embeddings 等 |
| 商業模式 | 從 ollama.com 確認 | 本地免費 + 雲端付費（Pro $20/mo, Max $100/mo） |
| 社群生態 | 從 README 社群整合列表確認 | 極大量整合（Chat UI、IDE、SDK、RAG、Agent 框架等） |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 資料來源優先順序 | GitHub 頁面 / gh CLI / 官方文件 / 第三方文章 | GitHub 頁面 + 官方 docs.ollama.com | gh CLI 不可用；官方文件為第一手權威來源 |
| 文件擷取範圍 | 僅 README / README + 關鍵子文件 / 全部文件 | README + API + Quickstart + Modelfile + FAQ + Development | 涵蓋「是什麼、怎麼用、怎麼擴展、怎麼部署」四個面向 |
| 背景脈絡補查 | 不補查 / 補查 llama.cpp / 補查競爭專案 | 本次 C1 先不補查，留待 C2 處理 | C1 聚焦 repo 本身資料，背景脈絡（llama.cpp、競爭分析）適合獨立 sub-step |
