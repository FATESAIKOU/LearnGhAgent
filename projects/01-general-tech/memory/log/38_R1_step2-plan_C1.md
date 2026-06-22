# 38_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1：取得 ollama/ollama 的 repo metadata 與主要文件。這是 R1 的第一個調研 sub-step，目標是建立對該專案的基本認知，為後續深入分析鋪路。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` + `gh api repos/ollama/ollama` | 取得 repo metadata | 獲得 stars、forks、license、語言、描述等 | 成功：Go 語言、174,721 stars、16,704 forks、MIT license、15 個 topics |
| `gh api repos/ollama/ollama/readme` | 擷取 README.md | 了解專案定位、安裝方式、API 用法 | 成功：取得完整 README（下載、REST API、Python/JS SDK、社群整合列表） |
| `gh api repos/ollama/ollama/contents/docs` | 列出 docs/ 目錄 | 了解有哪些子文件可讀 | 成功：約 30+ 文件，含 api.md、modelfile.mdx、quickstart.mdx、gpu.mdx、faq.mdx、development.md 等 |
| 讀取 api.md | 了解 REST API 設計 | 掌握 endpoints 與參數 | 成功：11 個 endpoints（generate、chat、create、list、show、copy、delete、pull、push、embeddings、version） |
| 讀取 modelfile.mdx | 了解模型自訂機制 | 掌握 Modelfile 格式 | 成功：FROM/PARAMETER/TEMPLATE/SYSTEM/ADAPTER/LICENSE/MESSAGE 指令 |
| 讀取 development.md | 了解建置方式 | 掌握從原始碼編譯流程 | 成功：Go + CMake + C/C++，支援 CUDA/ROCm/Vulkan/MLX 後端 |
| 讀取 quickstart.mdx | 了解快速入門 | 掌握基本使用流程 | 成功：ollama 互動選單、launch 工具、API 呼叫 |
| 讀取 gpu.mdx | 了解 GPU 支援 | 掌握硬體相容性 | 成功：NVIDIA（CC 5.0+）、AMD ROCm、Vulkan 支援表 |
| 讀取 faq.mdx | 了解常見問題 | 掌握升級、log、context window 設定 | 成功：環境變數、GPU 確認方式 |
| `gh api repos/ollama/ollama/releases?per_page=5` | 取得近期 release | 了解專案活躍度與最新功能 | 成功：v0.30.6~v0.30.10（2026/6/5~6/17），MLX、Cohere2Moe、Gemma 4 QAT 等 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata 完整性 | 確認有 stars、forks、license、language、topics、description | 完整取得 |
| 文件覆蓋率 | 確認 docs/ 目錄結構與關鍵文件內容 | 已讀取 7 份核心文件 |
| 專案活躍度 | 確認 release 頻率與最新版本 | 高活躍：2026/6 月內 5 個 release |
| 技術棧 | 確認主要語言與建置工具 | Go + C/C++ (llama.cpp)，多 GPU 後端 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件選取策略 | 讀全部 docs/ vs 只讀核心文件 | 讀 7 份核心文件 | 6000 字限制，選取最相關的：README、API、Modelfile、Development、Quickstart、GPU、FAQ |
| 背景脈絡補查 | 搜尋外部文章 vs 僅用 repo 內文件 | 先用 repo 內文件 | C1 目標是建立基本認知，外部脈絡留給後續 sub-step |
| release 數量 | 取 3 筆 vs 5 筆 | 取 5 筆 | 5 筆可看出近期發展方向（MLX、launch 功能、新模型支援） |
