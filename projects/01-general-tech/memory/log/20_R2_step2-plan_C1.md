# 20_R2_step2-plan_C1.md

## 狀況理解

Step 1 已確認調研標的為 GitHub repo `ollama/ollama`，需依 SKILL.md 標準調研動作執行 C1：取得 repo metadata、擷取主要文件、補查背景脈絡。此 step 為資料收集階段，不進行分析或撰寫報告。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view ollama/ollama --json ...` | 取得 repo metadata | 獲得 stars、license、語言、topic 等結構化資料 | 成功：174,616 stars、MIT license、Go 為主語言、15 個 topics（llama, llm, go, deepseek 等） |
| `webfetch` README.md（raw GitHub） | 擷取專案主要說明文件 | 了解專案定位、安裝方式、API 用法、社群整合 | 成功：取得完整 README，含安裝指令、REST API 範例、Python/JS SDK、大量社群整合列表 |
| `webfetch` docs/development.md | 了解編譯與開發方式 | 掌握專案技術棧與建置流程 | 成功：Go + CMake + C/C++（llama.cpp）的建置流程，支援 CUDA/ROCm/Vulkan/Metal 後端 |
| `webfetch` docs.ollama.com/api | 了解 REST API 規格 | 掌握 API endpoint 與使用方式 | 成功：取得 API 基礎 URL（localhost:11434/api）、chat/generate/embed 等 endpoint 概覽 |
| `webfetch` docs.ollama.com/quickstart | 了解快速入門流程 | 掌握使用者第一手體驗 | 成功：ollama 指令互動選單、launch 整合工具、API 快速範例 |
| `webfetch` docs.ollama.com/modelfile.md | 了解模型自訂機制 | 掌握 Modelfile 格式與參數 | 成功：FROM/PARAMETER/TEMPLATE/SYSTEM/ADAPTER 等指令完整說明 |
| `webfetch` docs.ollama.com/import.md | 了解模型匯入流程 | 掌握 Safetensors/GGUF 匯入方式 | 成功：支援 Safetensors 與 GGUF 兩種格式，含量化選項（q4_K_M 等） |
| `webfetch` docs.ollama.com/gpu.md | 了解硬體支援範圍 | 掌握 GPU 加速支援清單 | 成功：NVIDIA（CC 5.0+）、AMD ROCm、Apple Metal、Vulkan 完整 GPU 列表 |
| `webfetch` docs.ollama.com/cli.md | 了解 CLI 指令集 | 掌握所有子命令與用法 | 成功：run/pull/push/create/ls/ps/serve/launch/signin/signout 等完整 CLI 參考 |
| `webfetch` github.com/ggml-org/llama.cpp | 補查底層推論引擎背景 | 了解 Ollama 依賴的 llama.cpp 專案 | 成功：117k stars、MIT license、C/C++ 實作、GGUF 格式、多後端支援 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Repo metadata 完整性 | 確認 nameWithOwner、stars、license、language、topics、description 皆取得 | 完整取得，無缺漏 |
| 主要文件覆蓋率 | 確認 README + 關鍵子文件（dev guide、API、Modelfile、import、GPU、CLI）皆已擷取 | 6 份關鍵文件已取得 |
| 背景脈絡補查 | 確認 llama.cpp 作為底層引擎的定位與功能已了解 | 已確認 Ollama 為 llama.cpp 的上層封裝 |
| 資料品質 | 確認所有文件來源為官方（raw GitHub 或 docs.ollama.com） | 皆為官方來源，無第三方轉載 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件選取範圍 | (a) 只讀 README；(b) 讀 README + 開發文件 + API + Modelfile + import + GPU + CLI | (b) 讀取 7 份文件 | 涵蓋使用者面（README/CLI/Quickstart）、開發者面（dev guide/API）、進階面（Modelfile/import/GPU），確保分析報告各 section 有足夠素材 |
| 背景脈絡補查方式 | (a) 只查 Ollama 自身文件；(b) 查 llama.cpp 原始專案 | (b) 查 llama.cpp | Ollama 的 README 明確標註「Supported backends: llama.cpp」，理解底層引擎是分析其技術定位的必要條件 |
| 文件來源選擇 | (a) 只從 GitHub raw 抓；(b) 從 docs.ollama.com 官方文件站抓 | (b) 兩者並用 | GitHub raw 提供最新版 README 與開發文件，docs.ollama.com 提供結構化 API/CLI/Modelfile 參考，互補 |
