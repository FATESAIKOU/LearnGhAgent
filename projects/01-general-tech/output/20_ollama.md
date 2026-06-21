# Ollama 技術分析報告

> 調研標的：GitHub [ollama/ollama](https://github.com/ollama/ollama)（174,616 stars, MIT license, Go 語言）
> 建立時間：2023-06-26 | 調研時間：2026-06-21

---

## 1. 這個技術解決什麼問題？

Ollama 解決的是「**在本地（個人電腦或自有伺服器）上以最低操作成本執行大型語言模型（LLM）**」的問題。

具體來說，它解決了以下子問題：

| 子問題 | 說明 |
|---|---|
| 模型下載與管理 | 使用者不需要手動尋找模型檔案、處理 GGUF 格式、管理版本；Ollama 提供 `ollama pull` / `ollama run` 一鍵下載並執行 |
| 硬體加速抽象 | 不同 GPU 後端（NVIDIA CUDA、AMD ROCm、Apple Metal、Vulkan、MLX）需要不同的編譯與執行環境；Ollama 統一封裝 |
| API 標準化 | 每個模型可能有不同的 prompt template、context length、sampling 參數；Ollama 透過 Modelfile 與 REST API 提供統一介面 |
| 跨平台安裝 | macOS / Windows / Linux / Docker 四種平台，安裝指令統一為 `curl ... \| sh` |

**模糊之處**：Ollama 官方文件未明確定義「支援的模型範圍」。實際上它依賴 llama.cpp 的模型支援能力，理論上任何 GGUF 格式模型都可執行，但官方 library 僅收錄經過驗證的模型。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- llama.cpp 專案（Georgi Gerganov 發起）提供了在消費級硬體上執行 LLM 的 C/C++ 實作，但 llama.cpp 本身是底層函式庫，需要使用者自行處理模型下載、prompt template、GPU 後端選擇等操作
- 各 GPU 供應商（NVIDIA、AMD、Apple）使用不同的加速框架（CUDA、ROCm、Metal），llama.cpp 雖支援多後端，但編譯與配置門檻高

### 通用技術背景

- 2023 年起開源 LLM 大量湧現（Llama、Mistral、Qwen、DeepSeek 等），但這些模型以原始權重或 GGUF 格式釋出，缺乏統一的執行環境
- 雲端 API（OpenAI、Anthropic）雖然方便，但有資料隱私顧慮、延遲問題、以及持續的 API 費用
- 消費級 GPU 記憶體（8GB~24GB）已能執行 7B~13B 參數的量化模型，但缺乏一個「安裝即用」的軟體層來降低進入門檻

---

## 3. 這個技術是如何解決該問題的？

Ollama 的架構分為三層：

### 3.1 執行引擎層（Go + llama.cpp）

```
┌─────────────────────────────────────────────┐
│  Ollama CLI / Daemon (Go)                   │
│  - REST API server (localhost:11434)        │
│  - 模型生命週期管理（下載/載入/卸載/快取）    │
│  - Modelfile 解析與模型自訂                  │
├─────────────────────────────────────────────┤
│  llama.cpp (C/C++)                          │
│  - GGUF 模型載入與推理                       │
│  - GPU 後端抽象層                            │
│    ├─ CUDA (NVIDIA)                         │
│    ├─ ROCm (AMD)                            │
│    ├─ Metal (Apple Silicon)                 │
│    ├─ Vulkan (跨平台)                        │
│    └─ MLX (Apple MLX / CUDA)                │
└─────────────────────────────────────────────┘
```

- Go 負責：HTTP API、模型管理、CLI 互動、系統服務
- llama.cpp 負責：模型推理、GPU 加速、量化支援
- 兩者透過 CGO 連結

### 3.2 模型管理機制

**Modelfile**：類似 Dockerfile 的模型自訂格式

```
FROM llama3.2
SYSTEM "You are a helpful assistant"
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
TEMPLATE """{{ .System }}
USER: {{ .Prompt }}
ASSISTANT: """
```

支援指令：`FROM`（基底模型）、`PARAMETER`（推理參數）、`TEMPLATE`（prompt 模板）、`SYSTEM`（系統提示詞）、`ADAPTER`（LoRA 適配器）、`LICENSE`、`MESSAGE`（範例對話）、`REQUIRES`（模型需求）

**模型儲存**：以 SHA256 digest 為識別碼的 content-addressable storage，支援分層（layer）管理，類似容器映像檔

### 3.3 API 設計

REST API 位於 `localhost:11434/api`，主要端點：

| 端點 | 功能 |
|---|---|
| `POST /api/generate` | 文字補全（completion） |
| `POST /api/chat` | 對話生成（chat），支援 tool calling |
| `POST /api/create` | 建立模型（從現有模型 / GGUF / Safetensors） |
| `POST /api/pull` | 下載模型（支援斷點續傳） |
| `POST /api/push` | 上傳模型 |
| `GET /api/tags` | 列出本地模型 |
| `POST /api/show` | 顯示模型詳細資訊 |
| `DELETE /api/delete` | 刪除模型 |
| `POST /api/copy` | 複製模型 |

API 無嚴格版本化（無 `/v1/` 前綴），所有回應含 `total_duration`、`load_duration`、`prompt_eval_count`、`eval_count` 等效能指標。

### 3.4 安裝與整合

- 安裝：單行指令（`curl ... | sh`）或 Docker
- SDK：官方提供 Python（`ollama` pip package）與 JavaScript（`ollama` npm package）
- 生態系整合：涵蓋 Chat UI（Open WebUI、Lobe Chat）、IDE（Continue、Cline）、框架（LangChain、LlamaIndex、Haystack）、RAG（RAGFlow、MaxKB）、監控（Langfuse、OpenLIT）等數百個專案

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **llama.cpp** | 直接使用 C/C++ 函式庫，透過編譯選項選擇 GPU 後端，以 CLI 或 binding 執行 GGUF 模型 | 需 C/C++ 編譯環境；需手動下載模型檔案；需自行處理 prompt template | 無統一 API；無模型管理功能；需自行撰寫整合程式碼 | 最低 overhead 的推理效能；完全控制底層參數 |
| **LocalAI** | 以 Docker 為基礎的 LLM 推理伺服器，提供 OpenAI API 相容端點，支援多種後端（llama.cpp、whisper.cpp 等） | 需 Docker 環境；需手動掛載模型目錄；配置檔為 YAML | 容器化增加資源開銷；模型管理不如 Ollama 直覺 | 可直接取代 OpenAI API endpoint；支援多模態（文字+語音+影像） |
| **vLLM** | 以 PagedAttention 演算法最佳化 LLM 推理吞吐量，專注於高併發場景 | 需 NVIDIA GPU + CUDA；需 Python 環境；主要支援 HuggingFace 格式模型 | 不支援消費級 GPU 量化模型（GGUF）；安裝依賴複雜；資源需求高 | 高吞吐量推理（適合生產部署）；支援 continuous batching |
| **GPT4All** | 以 C++ 實作的本地 LLM 執行器，強調隱私與離線使用，提供桌面 GUI | 支援 CPU 與少量 GPU 後端；模型格式為 GPT4All 專用格式 | 模型選擇受限（僅支援經過轉換的模型）；GPU 加速支援有限 | 最簡單的離線 LLM 體驗；內建 RAG 與文件問答功能 |

### 4.2 切入點差異分析

```
                    ┌── 易用性 ──┐
                    │            │
               GPT4All       Ollama
                    │            │
                    │            ├── LocalAI
                    │            │
                    └── 效能 ──┐  │
                               │  │
                          vLLM │  │
                               │  │
                          llama.cpp
                               │
                    ┌── 底層控制 ──┘
```

- **Ollama** 位於「易用性」與「效能」的中間地帶：比 GPT4All 支援更多 GPU 後端與模型，比 LocalAI 安裝更簡單，比 vLLM 更適合個人使用
- **llama.cpp** 是 Ollama 的底層引擎，Ollama 在其上封裝了模型管理與 API 層
- **vLLM** 與 Ollama 的目標場景不同：vLLM 面向生產環境的高併發推理，Ollama 面向個人開發者的本地實驗與整合
- **GPT4All** 與 Ollama 最接近，但 GPT4All 的 GPU 支援較弱、模型生態較封閉
