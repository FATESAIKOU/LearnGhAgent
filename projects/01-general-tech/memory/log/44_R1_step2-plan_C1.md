# 44_R1_step2-plan_C1.md

## 狀況理解

Step 1 確認調研標的為 ollama/ollama。本 sub-step C1 為 Step 2 的第一個動作：取得 repo metadata、README、關鍵子文件（development guide、API docs、Modelfile、CLI reference、官網），並補查背景脈絡。

## 執行的動作與結果

| 動作 | 目的 | 預期效果 | 實際結果 |
|------|------|----------|----------|
| `gh repo view ollama/ollama` | 取得 repo metadata | stars、license、語言、release 等 | gh CLI 不可用，改由 GitHub 頁面擷取 |
| webfetch GitHub repo page | 取得 repo metadata | 175k stars, 16.7k forks, MIT, Go 66.2% + C 27% | 成功取得完整 metadata |
| webfetch raw README.md | 取得專案說明 | 安裝方式、API 範例、生態列表 | 成功取得完整 README |
| webfetch docs/development.md | 了解建置方式 | CMake + Go 建置流程、GPU backend 選項 | 成功取得完整開發文件 |
| webfetch docs.ollama.com | 取得官方文件首頁 | 文件結構概覽 | 成功取得 |
| webfetch docs.ollama.com/api | 取得 API 參考 | REST API endpoints 列表 | 成功取得 |
| webfetch docs.ollama.com/modelfile | 取得 Modelfile 參考 | 模型自訂格式（FROM/PARAMETER/TEMPLATE 等） | 成功取得完整參考 |
| webfetch docs.ollama.com/cli | 取得 CLI 參考 | ollama run/pull/create/serve 等指令 | 成功取得 |
| webfetch docs.ollama.com/quickstart | 取得快速入門 | 安裝後的第一步 | 成功取得 |
| webfetch ollama.com | 取得官網 | 產品定位、定價方案 | 成功取得（含 Pro $20/mo, Max $100/mo 雲端方案） |
| webfetch go.mod | 確認技術棧 | Go 1.26, gin, cobra, sqlite3, llama.cpp 等 | 成功取得 |
| webfetch docs.ollama.com/api/chat | 取得 chat API 細節 | OpenAPI spec、streaming、tool calling、structured output | 成功取得完整 OpenAPI 規格 |
| webfetch docs.ollama.com/llms.txt | 取得文件索引 | 所有文件頁面列表 | 成功取得（約 60+ 頁面） |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 驗證結果 |
|----------|----------------|----------|
| repo metadata | GitHub 頁面擷取 | 175k stars, 16.7k forks, MIT, Go 66.2% + C 27%, v0.30.10 |
| 核心功能 | README + docs 交叉比對 | 本地 LLM 執行引擎，支援 chat/generate/embed/tool calling/vision/thinking |
| 技術架構 | go.mod + development.md | Go server + C/C++ llama.cpp native backend + MLX engine |
| 生態 | README community integrations | 100+ 第三方整合，20+ 語言 SDK |
| 商業模式 | ollama.com | 本地免費 + 雲端付費（Pro $20/mo, Max $100/mo） |
| 文件完整性 | llms.txt 索引 | 約 60 頁文件，涵蓋 API/CLI/Modelfile/GPU/整合/疑難排解 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|----------|----------|----------|----------|
| 資料來源優先級 | GitHub README / 官方 docs / 第三方文章 | 官方 docs 為主，GitHub README 為輔 | 官方 docs 結構最完整，AGENTS.md 要求優先使用可靠來源 |
| 子文件選取 | 全部 60+ 頁 / 僅核心 5 頁 | 核心 5 頁（API/CLI/Modelfile/development/quickstart）+ 索引 | 6000 字限制，核心文件已涵蓋分析所需 |
| 背景脈絡補查 | 搜尋 llama.cpp 歷史 / 直接引用 README | 直接引用 README 提及的 llama.cpp | README 已明確標示 backend 為 llama.cpp，無需額外搜尋 |
