# 26_R1_step2-plan_C2.md

## 狀況理解

Step 2 C2：補查背景脈絡。C1 已取得 ollama repo 本身資訊，C2 需補查其底層技術（llama.cpp、GGUF）與競爭產品（LocalAI、vLLM），以支撐分析報告 §2（背景）與 §4（替代方案）。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 llama.cpp README | 了解 ollama 底層推理引擎 | 掌握 llama.cpp 定位與能力 | 成功取得：118k stars，C/C++ LLM inference，支援 1.5~8bit 量化、CUDA/ROCm/Vulkan/Metal/SYCL 後端、OpenAI-compatible API server、GGUF 格式 |
| 讀取 LocalAI README | 了解同級替代方案 | 掌握 LocalAI 定位與差異 | 成功取得：47k stars，Go 為主，60+ backends（llama.cpp/vLLM/whisper.cpp/stable-diffusion/MLX），支援 LLM/vision/voice/image/video 多模態，OpenAI/Anthropic/ElevenLabs API 相容，分散式模式，內建 agent |
| 讀取 vLLM README | 了解同級替代方案 | 掌握 vLLM 定位與差異 | 成功取得：83.5k stars，Python 為主，PagedAttention 核心技術，高吞吐 LLM serving，200+ model architectures，OpenAI API 相容，支援 FP8/INT4/GGUF 量化，分散式推理 |
| 從 C1 已取得的 ollama docs 推斷 GGUF 格式背景 | 了解 GGUF 在 ollama 生態的角色 | 掌握模型格式標準 | ollama 使用 llama.cpp 的 GGUF 格式作為模型儲存格式，透過 Modelfile 支援 Safetensors/GGUF 匯入與量化 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 底層技術鏈 | ollama → llama.cpp → GGUF → 量化推理 | 完整：ollama 包裝 llama.cpp 作為推理後端，使用 GGUF 格式，支援多種 GPU backend |
| 競爭產品覆蓋 | LocalAI（多模態、多 backend）、vLLM（高吞吐 serving） | 已取得兩者定位與核心差異 |
| 背景脈絡完整性 | 問題背景（本地 LLM 推理的需求）、技術限制（GPU VRAM、模型格式碎片化） | 可從 C1+C2 資料推導 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 替代方案選取 | LocalAI / vLLM / llama.cpp / GPT4All / LM Studio / text-generation-webui | LocalAI + vLLM | LocalAI 與 ollama 最直接競爭（同為 Go 生態、本地部署），vLLM 代表不同路線（高吞吐 serving、Python 生態），涵蓋兩種典型替代路徑 |
| 背景查詢深度 | 只查 README vs 深入 docs/ | 只查 README | C2 目的為補查背景脈絡，非完整調研；深入細節留到報告撰寫時按需引用 |
