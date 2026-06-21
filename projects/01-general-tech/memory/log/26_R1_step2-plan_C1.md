# 26_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1：取得 ollama/ollama 的 repo metadata 與主要文件。使用者要求調研 ollama，這是 R1 首次調研，需完整收集 repo 資訊、README、docs/ 下關鍵文件，為後續分析報告鋪路。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view ollama/ollama --json ...` | 取得 repo metadata（stars, forks, license, language, topics, release） | 取得結構化 repo 資訊 | 成功取得：174,630 stars, 16,702 forks, MIT license, Go 為主語言，最新 release v0.30.10（2026-06-17），topics 含 llama/llm/mistral/deepseek/qwen/gemma 等 |
| `gh api repos/ollama/ollama/readme` | 取得 README.md 全文 | 了解專案定位與功能 | 成功取得：定位為「Start building with open models」，支援 macOS/Windows/Linux/Docker，提供 REST API、Python/JS SDK、ollama launch 整合 Claude Code/Codex/OpenCode 等 |
| `gh api repos/ollama/ollama/contents/docs` | 列出 docs/ 目錄 | 了解有哪些子文件可讀 | 成功取得 30+ 文件，含 api.md, modelfile.mdx, cli.mdx, gpu.mdx, faq.mdx, import.mdx, template.mdx, development.md, quickstart.mdx, troubleshooting.mdx 等 |
| 讀取 api.md | 了解 REST API 設計 | 掌握 API endpoints 與使用方式 | 成功取得：12 個 endpoints（generate, chat, create, list, show, copy, delete, pull, push, embeddings, ps, version），支援 streaming / JSON mode / structured outputs |
| 讀取 modelfile.mdx | 了解模型自訂機制 | 掌握 Modelfile 格式與指令 | 成功取得：FROM/PARAMETER/TEMPLATE/SYSTEM/ADAPTER/LICENSE/MESSAGE/REQUIRES 指令，支援 Safetensors、GGUF、LoRA adapter 匯入 |
| 讀取 development.md | 了解編譯方式與架構 | 掌握技術棧與建置流程 | 成功取得：Go + CMake + C/C++ 原生程式碼，支援 CUDA/ROCm/Vulkan/Metal 後端，可選擇 GPU backend 編譯 |
| 讀取 gpu.mdx | 了解 GPU 支援範圍 | 掌握硬體相容性 | 成功取得：NVIDIA CC 5.0+、AMD ROCm v7、Apple Metal、Vulkan 支援，含 GPU 選取與疑難排解 |
| 讀取 faq.mdx | 了解常見問題 | 掌握部署與設定細節 | 成功取得：環境變數設定、proxy、context window、GPU 確認、log 位置、cloud 功能關閉等 |
| 讀取 import.mdx | 了解模型匯入流程 | 掌握自訂模型匯入方式 | 成功取得：Safetensors / GGUF / adapter 匯入流程，支援量化（q4_K_M, q8_0 等） |
| 讀取 template.mdx | 了解 prompt template 引擎 | 掌握 Go template 變數與用法 | 成功取得：System/Prompt/Response/Messages/Tools 等變數，支援 tool calling |
| 讀取 cli.mdx | 了解 CLI 命令 | 掌握使用者操作介面 | 成功取得：run/launch/pull/rm/ls/create/ps/stop/serve/signin/signout 等命令 |
| 讀取 context-length.mdx | 了解 context window 管理 | 掌握 VRAM 與 context 的關係 | 成功取得：預設 context 依 VRAM 自動調整（<24GB: 4k, 24-48GB: 32k, >=48GB: 256k） |
| 讀取 troubleshooting.mdx | 了解疑難排解 | 掌握除錯方式 | 成功取得：log 位置、LLM library 覆寫、GPU 發現問題處理 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Repo metadata 完整性 | 確認 stars, forks, license, language, release, topics 均已取得 | 完整 |
| 關鍵文件覆蓋率 | 確認 README + 12 份 docs/ 子文件已讀取 | 完整覆蓋 API、Modelfile、CLI、GPU、FAQ、Import、Template、Development、Troubleshooting、Context Length |
| 技術棧理解 | 從 development.md 與 repo 結構確認 | Go 主體 + C/C++ (llama.cpp) 原生層 + CMake 建置 |
| 核心功能理解 | 從 README + API + CLI 確認 | 本地 LLM 執行引擎 + REST API + 模型管理 + 工具整合 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件選取範圍 | 全部 docs/ 文件 vs 只讀關鍵文件 | 讀取 12 份關鍵文件 | 涵蓋 API、模型管理、GPU、部署、疑難排解等面向，足以支撐分析報告 |
| 背景脈絡補查 | 立即補查 llama.cpp / GGUF / 競爭產品 vs 留到 C2 再做 | 留到 C2 | C1 專注 repo 本身資訊，背景與替代方案在 C2 處理 |
