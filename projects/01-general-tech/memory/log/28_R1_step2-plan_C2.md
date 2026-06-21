# 28_R1_step2-plan_C2.md

## 狀況理解

Step 2 C2：補查背景脈絡。C1 已取得 ollama/ollama 的 repo metadata 與主要文件。C2 需補查其底層引擎 llama.cpp，以及競爭替代方案，以支撐分析報告的 §3（核心機制）與 §4（替代方案）。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| webfetch ggml-org/llama.cpp GitHub 頁面 | 了解 Ollama 底層推理引擎 | 取得 llama.cpp 的定位、功能、支援硬體 | 成功：118k stars, MIT, C/C++ 無依賴, 支援 Metal/CUDA/ROCm/Vulkan/SYCL 等後端, 支援 1.5~8bit 量化, CPU+GPU hybrid |
| 分析 llama.cpp 與 Ollama 的關係 | 確認兩者分工 | 理解 Ollama 是 llama.cpp 的上層封裝 | llama.cpp 提供底層推理引擎（C/C++），Ollama 提供 Go 包裝的 REST API + 模型管理 + 安裝體驗 |
| 從已知知識補查競爭方案 | 取得 §4 替代方案資料 | 列出 2~4 個同級替代方案 | 確認以下替代方案：LocalAI（Go, OpenAI API 相容）、GPT4All（nomic.ai, 桌面端）、LM Studio（GUI, 專有）、llamafile（Mozilla, 單檔執行） |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| llama.cpp 定位 | 從 README 確認 | 「LLM inference in C/C++」— 底層推理引擎，無依賴純 C/C++ |
| llama.cpp 硬體支援 | 從 README 後端列表確認 | Metal, CUDA, HIP, Vulkan, SYCL, OpenVINO, CANN, WebGPU 等 15+ 後端 |
| Ollama 與 llama.cpp 關係 | 從 Ollama README 確認 | Ollama 明確標示「Supported backends: llama.cpp」 |
| 競爭方案 | 從已知技術生態確認 | LocalAI / GPT4All / LM Studio / llamafile 為主要同級替代 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 背景查詢範圍 | 僅 llama.cpp / llama.cpp + 競爭方案 / 再加論文 | llama.cpp + 競爭方案 | 論文超出分析報告需求；競爭方案為 §4 必要內容 |
| 競爭方案數量 | 2 個 / 3 個 / 4 個 | 4 個（LocalAI, GPT4All, LM Studio, llamafile） | 涵蓋開源/閉源、API/桌面/單檔 不同切入點 |
