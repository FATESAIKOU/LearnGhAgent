# Ollama 技術分析報告

> 調研標的：GitHub repo [ollama/ollama](https://github.com/ollama/ollama)（v0.30.10, 2026-06-17）
> 授權：MIT License | 語言：Go 66.2% + C 27.0% + C++ 1.1% | Stars: 175k | Forks: 16.7k

---

## 1. 這個技術解決什麼問題？

Ollama 解決的是「在本地端（個人電腦或自有伺服器）以最簡操作執行開源大型語言模型（LLM）」的問題。

具體來說，它解決了以下子問題：

- **模型取得與管理**：使用者不需要手動下載模型檔案、不需要理解 GGUF / Safetensors 等格式差異，只需 `ollama pull <model>` 即可取得模型
- **模型執行環境**：使用者不需要自行編譯 llama.cpp、不需要配置 CUDA / ROCm / Metal 等 GPU 後端，Ollama 自動偵測硬體並選擇最佳後端
- **API 介面**：提供 REST API 與 OpenAI-compatible API，讓既有工具（如 LangChain、Continue、Cline）可直接串接
- **跨平台支援**：macOS / Windows / Linux / Docker 皆可執行，不需針對各平台分別配置

**模糊之處**：Ollama 的定位介於「終端使用者工具」與「開發者框架」之間。README 同時宣稱「Start building with open models」與提供 `ollama run` 聊天介面，但未明確區分其目標使用者是開發者還是一般使用者。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- Ollama 底層依賴 [llama.cpp](https://github.com/ggml-org/llama.cpp)（由 Georgi Gerganov 創建），這是一個純 C/C++ 的 LLM 推論引擎，支援多種 GPU 後端（CUDA / ROCm / Metal / Vulkan）與 CPU 推論
- Ollama 使用 GGUF 格式作為模型儲存格式，這是 llama.cpp 專案定義的二進位格式

### 通用技術背景

1. **開源 LLM 的興起**：2023 年起 Meta 開源 LLaMA 系列後，Mistral、Qwen、DeepSeek、Gemma 等開源模型大量出現。這些模型需要本地執行環境，但各自依賴不同的推論框架（Transformers / vLLM / llama.cpp），缺乏統一的操作介面。

2. **GPU 推論的複雜性**：LLM 推論需要 GPU 加速才能達到可用速度，但 GPU 後端（NVIDIA CUDA / AMD ROCm / Apple Metal）的安裝與配置門檻高，且各平台不相容。使用者需要自行編譯對應後端、處理驅動程式版本衝突。

3. **模型格式碎片化**：開源模型以 Hugging Face Safetensors 為主流格式，但 Safetensors 是為訓練設計的，推論時需要轉換。GGUF 格式專為推論最佳化（支援量化、記憶體映射載入），但轉換流程對非技術使用者不友善。

4. **開發者工具整合需求**：2024 年起 AI 輔助編碼工具（Continue、Cline、Copilot）與 LLM 框架（LangChain、LlamaIndex）大量出現，這些工具需要統一的 API 介面來串接不同 LLM 提供者。OpenAI API 格式已成為事實標準，但本地 LLM 執行引擎缺乏對該格式的原生支援。

---

## 3. 這個技術是如何解決該問題的？

Ollama 的架構分為三層：

### 3.1 系統架構

```
┌─────────────────────────────────────────────────┐
│                 使用者介面層                       │
│  CLI (ollama run/pull/ps/rm)                     │
│  REST API (localhost:11434)                      │
│  OpenAI-compatible API (/v1/chat/completions)    │
│  Python SDK / JavaScript SDK                     │
├─────────────────────────────────────────────────┤
│                 服務層 (Go)                       │
│  模型管理 (pull/push/create/delete/copy)         │
│  模型執行生命週期管理 (server process)            │
│  GPU 自動偵測 (discover)                         │
│  Modelfile 解析器                                │
│  Prompt template 引擎 (Go template)              │
├─────────────────────────────────────────────────┤
│                 推論層 (C/C++)                    │
│  llama.cpp (llama-library)                      │
│  GPU Backend: CUDA / ROCm / Metal / Vulkan      │
│  CPU Backend: x86 (AVX/AVX2/AVX512) / ARM NEON  │
│  量化支援: q4_K_M, q8_0, q2_K 等                │
└─────────────────────────────────────────────────┘
```

### 3.2 核心機制

**模型管理（Model Registry）**：
- 使用者透過 `ollama pull <model>` 從 [ollama.com/library](https://ollama.com/library) 下載模型
- 模型以 GGUF 格式儲存在本地 `~/.ollama/models/`
- `ollama push` 可上傳自訂模型至 ollama.com
- 支援從 Hugging Face 直接匯入 Safetensors 格式模型（透過 `ollama create` + Modelfile）

**Modelfile 自訂模型**：
- 類似 Dockerfile 的宣告式格式，用於建立自訂模型
- 支援指令：`FROM`（基底模型）、`PARAMETER`（溫度/context length 等）、`TEMPLATE`（prompt 模板）、`SYSTEM`（系統提示詞）、`ADAPTER`（LoRA 適配器）
- 範例：
  ```
  FROM llama3.2
  PARAMETER temperature 0.7
  PARAMETER num_ctx 8192
  SYSTEM You are a helpful coding assistant.
  ```

**REST API**（12 個 endpoints）：
- `/api/generate` — 文字生成（單次）
- `/api/chat` — 對話生成（支援多輪訊息）
- `/api/create` — 從 Modelfile 建立模型
- `/api/pull` / `/api/push` — 模型上下載
- `/api/embeddings` — 嵌入向量生成
- `/api/ps` — 查看目前載入的模型
- 支援 streaming（SSE）、JSON mode、structured outputs（JSON schema）

**OpenAI-compatible API**：
- 提供 `/v1/chat/completions` 與 `/v1/embeddings` endpoints
- 讓現有 OpenAI SDK 可直接指向 Ollama 使用

**GPU 自動偵測**：
- 啟動時自動掃描系統中的 GPU（NVIDIA / AMD / Apple Metal）
- 依 VRAM 大小自動調整 context window 大小（<24GB: 4k, 24-48GB: 32k, >=48GB: 256k）
- 支援多 GPU 配置

**Prompt Template 引擎**：
- 使用 Go template 語法，支援變數：`{{ .System }}`、`{{ .Prompt }}`、`{{ .Response }}`、`{{ .Messages }}`、`{{ .Tools }}`
- 自動套用模型對應的 chat template（如 ChatML、Llama 3 格式）

### 3.3 執行流程（以 `ollama run gemma4` 為例）

```
1. CLI 解析命令，呼叫 REST API /api/chat
2. 服務層檢查模型是否已下載
   ├─ 未下載 → 從 ollama.com/library 下載 GGUF 檔案
   └─ 已下載 → 讀取模型 manifest
3. 啟動 llama.cpp runner process（獨立子行程）
4. 載入 GGUF 模型至 GPU/CPU
5. 套用 prompt template 格式化使用者輸入
6. llama.cpp 執行推論（token by token）
7. 結果經由 REST API streaming 回傳至 CLI
```

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **llama.cpp** | 純 C/C++ LLM 推論引擎，提供 CLI 與 API server | 需自行編譯或下載 binary；需手動下載 GGUF 模型 | 無模型管理功能；無自動 GPU 偵測；需自行處理模型格式轉換 | 最低依賴、最高效能控制；支援最多 GPU 後端 |
| **LocalAI** | 以容器為基礎的本地 LLM 服務，提供 OpenAI-compatible API | 需 Docker 環境；需手動配置模型檔案路徑 | 容器化增加資源開銷；模型管理依賴外部工具 | 與 Docker 生態整合良好；支援多種後端（llama.cpp / transformers / diffusers） |
| **vLLM** | 高效能 LLM 推論引擎，專注於 PagedAttention 與連續批次處理 | 需 NVIDIA GPU + CUDA；模型需為 Hugging Face 格式或 AWQ/GPTQ 量化 | 不支援 AMD/Apple GPU；安裝依賴複雜（需編譯 CUDA kernel） | 最高吞吐量（適合生產環境）；支援 continuous batching 與 tensor parallelism |
| **GPT4All** | 本地 LLM 執行引擎，提供桌面 GUI 與 API | 需下載應用程式；模型選擇受限於其生態系 | 模型來源較封閉（Nomic AI 維護的模型庫）；擴充性低 | 最簡單的使用者體驗（下載即用）；適合非技術使用者 |

### 切入點差異

- **Ollama vs llama.cpp**：Ollama 在 llama.cpp 之上封裝了模型管理、GPU 自動偵測、REST API、SDK 等層，犧牲了部分底層控制權換取易用性。llama.cpp 提供更細粒度的效能調校（如 batch size、thread count、GPU split 比例），Ollama 則將這些參數自動化或透過 Modelfile 暴露有限選項。

- **Ollama vs LocalAI**：兩者都提供 OpenAI-compatible API，但 LocalAI 以 Docker 為核心部署方式，支援更多模型類型（不僅 LLM，還包含圖片生成、語音辨識）。Ollama 的優勢在於更輕量的安裝（單一二進位檔）與更完整的模型管理生態（ollama.com library + push/pull）。

- **Ollama vs vLLM**：vLLM 定位為生產環境的高吞吐推論引擎，使用 PagedAttention 技術實現高效 KV cache 管理，適合多使用者同時請求的場景。Ollama 定位為個人開發與小規模部署，單機單使用者場景下延遲較低但吞吐量不如 vLLM。

- **Ollama vs GPT4All**：GPT4All 更偏向終端使用者（提供桌面 GUI），模型選擇由 Nomic AI 篩選。Ollama 提供更開放的模型生態（支援任何 GGUF 模型 + Hugging Face 匯入）與更完整的開發者 API。
