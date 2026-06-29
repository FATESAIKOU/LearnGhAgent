# 103_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認技術標的為 llama.cpp 與 vLLM 兩個專案。C1 的任務是取得兩者的 repo metadata、README 關鍵內容、以及背景脈絡（ggml 底層庫、PagedAttention 論文），為後續分析建立事實基礎。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view ggerganov/llama.cpp --json ...` | 取得 llama.cpp 的 metadata | 獲得 stars、語言、描述、建立時間等 | 成功：118k stars、C++、2023-03 建立、topic: ggml |
| `gh repo view vllm-project/vllm --json ...` | 取得 vLLM 的 metadata | 獲得 stars、語言、描述、建立時間等 | 成功：84k stars、Python、2023-02 建立、topic 含 pytorch/cuda/deepseek 等 |
| `gh api repos/.../readme` | 取得兩者的 README.md | 了解專案定位、功能列表、快速入門 | 成功：llama.cpp 強調無依賴 C/C++ 實現、多硬體後端、量化支援；vLLM 強調高吞吐、PagedAttention、OpenAI 相容 API |
| `webfetch ggml repo` | 了解 llama.cpp 底層的 ggml 張量庫 | 確認 ggml 的角色 | 成功：ggml 是 tensor library for ML，llama.cpp 是其主力 playground |
| `webfetch vLLM PagedAttention blog` | 了解 vLLM 核心技術 | 確認 PagedAttention 原理 | 成功：OS 虛擬記憶體概念應用於 KV cache 管理，減少 60-80% 記憶體浪費 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| llama.cpp 定位 | README 描述 + metadata | LLM inference in C/C++，純 C++ 無依賴，主打本地/邊緣推理 |
| vLLM 定位 | README 描述 + metadata | 高吞吐 LLM serving engine，主打雲端/伺服器端部署 |
| 核心技術差異 | 比對 README 與 blog | llama.cpp 靠 ggml + 量化；vLLM 靠 PagedAttention + continuous batching |
| 硬體支援範圍 | README 比對 | llama.cpp 涵蓋 CPU/GPU/Apple Silicon/WebGPU；vLLM 主力 NVIDIA GPU，擴充 AMD/TPU |
| 使用場景 | README 與 blog 比對 | llama.cpp 偏向單機/本機執行；vLLM 偏向多用戶/API server |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 背景資料範圍 | 僅 README / 含底層庫與論文 | 含 ggml 與 PagedAttention blog | 使用者問「是啥用在哪」，需理解核心機制才能解釋清楚 |
| 資料來源優先序 | 僅 GitHub API / 補 web fetch | 兩者並用 | GitHub API 取得結構化 metadata，web fetch 補 blog 與底層庫說明 |
| 是否查更多子文件 | 查 docs/ 目錄 / 僅 README | 僅 README + blog | 6000 字上限，C1 只需建立事實基礎，細節留 C2 |
