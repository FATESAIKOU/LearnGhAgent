# Ollama 分析報告

> 調研標的：GitHub [ollama/ollama](https://github.com/ollama/ollama)（v0.30.10, MIT License, Go, 174,627 stars）
> 底層後端：llama.cpp

---

## 1. 這個技術解決什麼問題？

Ollama 解決的是「在本地端（個人電腦、自管伺服器）簡便地執行大型語言模型（LLM）並提供標準化 API 存取」的問題。

具體而言，它將以下原本分散且繁瑣的步驟整合為單一工具：

- 模型下載與版本管理（從模型庫 pull / push）
- 模型執行（載入、推理、卸載）
- 模型自訂（透過 Modelfile 調整參數、系統提示、LoRA 適配器）
- 標準化 API 提供（REST API，相容 OpenAI API 風格）
- GPU 加速（NVIDIA CUDA、AMD ROCm、Apple Metal、Vulkan）
- 跨平台支援（macOS / Windows / Linux / Docker）

**模糊之處**：Ollama 官方定位為「Start building with open models」，但「building」的範疇未明確定義——它不提供模型訓練或微調（fine-tuning）功能，僅提供 LoRA adapter 掛載與參數調整。若使用者期待的是訓練框架，Ollama 無法滿足。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- llama.cpp 專案（Georgi Gerganov）提供了在消費級硬體上執行量化 LLM 的 C++ 實作，但缺乏統一的模型管理、API 介面與跨平台封裝
- 各模型格式（GGUF、Safetensors）與量化方案（Q4_K_M、Q8_0 等）差異大，使用者需自行處理下載、格式轉換、參數配置
- GPU 後端（CUDA / ROCm / Metal / Vulkan）各自有不同的安裝與設定流程

### 通用技術背景（文章中未明確提及，但為必要脈絡）

- 2023 年起開源 LLM 數量爆炸（Llama、Mistral、Gemma、Phi 等），但缺乏統一的本地執行標準
- 雲端 LLM API（OpenAI、Anthropic、Google）有資料外洩風險、延遲問題與持續性成本
- GGUF 格式成為開源 LLM 的標準容器格式，但需要對應的載入器與推理引擎
- 量化技術（4-bit / 8-bit）使數十億參數的模型能在 8-24GB VRAM 的消費級 GPU 上執行，但量化模型的選擇與管理對非專業使用者門檻高

---

## 3. 這個技術是如何解決該問題的？

Ollama 的架構可拆為以下層次：

### 3.1 模型管理層

```
ollama pull llama3.2       # 從 ollama.com/library 下載模型
ollama push myuser/myModel # 上傳自訂模型
ollama list                # 列出本地模型
ollama rm llama3.2         # 刪除模型
ollama show llama3.2       # 顯示模型詳細資訊（參數、模板、license）
```

- 模型以 `model:tag` 格式識別（如 `llama3.2:latest`），tag 省略時預設 `latest`
- 模型儲存於 `~/.ollama/models/`（macOS/Linux）或 `C:\Users\<user>\.ollama\models\`（Windows）
- 支援從 GGUF 檔案、Safetensors 目錄或既有模型建立新模型

### 3.2 模型自訂層（Modelfile）

Modelfile 是 Ollama 的模型自訂 DSL，語法類似 Dockerfile：

```
FROM llama3.2
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
SYSTEM You are a helpful assistant.
TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
"""
ADAPTER ./my-lora.safetensors
MESSAGE user What is the capital of France?
MESSAGE assistant Paris
```

支援的指令：

| 指令 | 功能 |
|------|------|
| `FROM` | 指定基底模型（必要） |
| `PARAMETER` | 設定推理參數（temperature, top_k, top_p, num_ctx 等） |
| `TEMPLATE` | 自訂 prompt 模板（Go template 語法） |
| `SYSTEM` | 設定系統提示 |
| `ADAPTER` | 掛載 LoRA / QLoRA 適配器 |
| `LICENSE` | 指定授權條款 |
| `MESSAGE` | 設定對話歷史範例 |
| `REQUIRES` | 指定最低 Ollama 版本 |

### 3.3 推理執行層

```
ollama run llama3.2        # 互動式 CLI
ollama run gemma4 ""       # 預載模型到記憶體
ollama stop llama3.2       # 卸載模型
```

- 底層使用 llama.cpp 進行推理
- 模型載入後預設保持 5 分鐘（可透過 `keep_alive` 或 `OLLAMA_KEEP_ALIVE` 調整）
- 支援並行請求處理（`OLLAMA_NUM_PARALLEL`）與多模型同時載入（`OLLAMA_MAX_LOADED_MODELS`）
- 支援 Flash Attention（`OLLAMA_FLASH_ATTENTION=1`）與 KV cache 量化（`OLLAMA_KV_CACHE_TYPE`）

### 3.4 API 層

REST API 監聽於 `localhost:11434`，主要 endpoints：

| Endpoint | 功能 |
|----------|------|
| `POST /api/generate` | 文字補全（streaming / non-streaming） |
| `POST /api/chat` | 對話補全（支援 tool calling、structured outputs） |
| `POST /api/create` | 建立模型（從既有模型、GGUF、Safetensors） |
| `GET /api/tags` | 列出本地模型 |
| `POST /api/show` | 顯示模型詳細資訊 |
| `POST /api/copy` | 複製模型 |
| `DELETE /api/delete` | 刪除模型 |
| `POST /api/pull` | 下載模型（支援斷點續傳） |
| `POST /api/push` | 上傳模型 |
| `POST /api/embeddings` | 產生嵌入向量 |
| `GET /api/version` | 版本查詢 |

API 設計要點：

- 預設 streaming 回應（逐 token 回傳 JSON），可設 `"stream": false` 改為單一回應
- 支援 JSON mode 與 JSON Schema structured outputs
- 支援 tool calling（function calling），模型可回傳工具呼叫請求
- 支援多模態模型（透過 base64 編碼圖片）
- 回應包含效能統計（`total_duration`, `load_duration`, `prompt_eval_count`, `eval_count` 等）

### 3.5 GPU 加速層

| 後端 | 支援範圍 |
|------|---------|
| NVIDIA CUDA | Compute Capability 5.0+，驅動 531+ |
| AMD ROCm | Linux: ROCm v7, Windows: ROCm v7 / HIP7 |
| Apple Metal | macOS arm64（Apple Silicon） |
| Vulkan | Windows / Linux 通用後端 |

- 支援多 GPU 分散載入（模型無法完全放入單張 GPU 時自動跨 GPU 分配）
- 可透過環境變數指定 GPU 選擇（`CUDA_VISIBLE_DEVICES`, `ROCR_VISIBLE_DEVICES`, `GGML_VK_VISIBLE_DEVICES`）
- 支援 MLX engine（macOS 預設啟用，其他平台需指定 `OLLAMA_MLX_BACKENDS`）

### 3.6 生態整合層

Ollama 透過以下方式融入既有生態：

- **官方 SDK**：Python（`ollama` pip package）、JavaScript（`ollama` npm package）
- **社群整合**：Open WebUI、Continue、Cline、LangChain、LlamaIndex、Dify、crewAI 等數百個專案
- **IDE 整合**：VS Code（Cline、Continue）、JetBrains、Emacs、Sublime Text
- **部署選項**：Docker、Kubernetes（Helm Chart）、Fly.io、Google Cloud Run

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|---------|-------------|---------------|-----------------|
| **llama.cpp** | 純 C++ LLM 推理引擎，提供 `llama-cli` 與 `llama-server` | C++ 編譯環境、手動下載 GGUF 模型 | 無模型管理功能、無標準化 API、需自行處理 GPU 後端選擇 | 最低依賴、最高效能控制，但使用者需自行處理所有周邊事務 |
| **vLLM** | 高效能 LLM 推理引擎，支援 PagedAttention 與連續批次處理 | Python 環境、CUDA GPU、HuggingFace 格式模型 | 資源需求高（建議 A100 等級）、設定複雜、主要面向生產部署 | 高吞吐量、低延遲，適合生產環境 API 服務 |
| **LocalAI** | OpenAI API 相容的本地 LLM 伺服器，支援多後端（llama.cpp、whisper、stable diffusion） | Docker 或 Go 執行環境 | 效能不如原生 llama.cpp、模型格式轉換可能需額外步驟 | 提供 OpenAI API 完全相容的替代方案，適合已使用 OpenAI SDK 的專案 |
| **LM Studio** | 圖形化介面的本地 LLM 執行工具 | macOS / Windows 桌面環境 | 不提供 headless API 模式、Linux 支援有限、不適合自動化部署 | 最適合非技術使用者的 GUI 方案，一鍵下載與執行模型 |

### 切入點差異分析

- **llama.cpp** 是 Ollama 的底層引擎，Ollama 在其上封裝了模型管理、API 標準化與跨平台整合。選擇 llama.cpp 可獲得最大控制權，但需自行處理所有周邊功能。
- **vLLM** 與 Ollama 的目標場景不同：vLLM 針對高併發生產環境（PagedAttention 可大幅提升 GPU 記憶體利用率），Ollama 針對個人開發與小規模部署。vLLM 不支援 Ollama 的模型管理與 Modelfile 自訂機制。
- **LocalAI** 與 Ollama 最為相似，皆提供 OpenAI API 相容的本地 LLM 伺服器。差異在於 LocalAI 支援更多後端（whisper、stable diffusion、TTS），但 Ollama 在模型管理（pull/push）、Modelfile 自訂與 GPU 後端覆蓋率上更完整。
- **LM Studio** 是唯一提供完整 GUI 的方案，適合非技術使用者探索與實驗 LLM，但不適合 CI/CD 整合或 headless 伺服器部署。

### 總結

Ollama 的核心競爭力不在推理效能（底層仍是 llama.cpp），而在於**將 LLM 的取得、管理、自訂、執行與 API 暴露整合為單一工具**，大幅降低本地 LLM 的使用門檻。對於需要快速原型開發、個人使用或小團隊部署的場景，Ollama 是當前生態中最完整的選擇。
