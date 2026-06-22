# Ollama 技術分析報告

> 調研標的：GitHub [ollama/ollama](https://github.com/ollama/ollama)（v0.30.10, 2026-06-17）
> 語言組成：Go 8.2M / C 3.4M / TypeScript 397K / C++ 133K
> 授權：MIT License

---

## 1. 這個技術解決什麼問題？

**Ollama 解決的問題是：讓使用者在本地端（無雲端依賴）以極低的操作成本執行、管理、自訂大型語言模型（LLM）。**

具體而言，Ollama 將以下原本分散且高門檻的操作整合為單一 CLI + REST API：

- 模型下載與版本管理（`ollama pull` / `ollama push`）
- 模型執行與對話（`ollama run` / `ollama chat`）
- 模型自訂（Modelfile：修改參數、系統提示、模板、LoRA adapter）
- 模型分享（push 到 ollama.com 或自架 registry）
- 與外部工具整合（REST API / Python / JS SDK）

在 Ollama 出現之前，要在本地執行 LLM 需要：手動下載 GGUF 權重、配置 llama.cpp 或同等推理引擎、自行撰寫 API wrapper、管理 GPU 記憶體配置。Ollama 將這些步驟封裝成 `ollama run <model>` 一條指令。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- llama.cpp 專案（由 Georgi Gerganov 創立）提供了 C/C++ 實作的 LLM 推理引擎，支援 GGUF 格式模型與多種 GPU 後端（CUDA / ROCm / Vulkan / Metal）。Ollama 直接建構在 llama.cpp 之上。
- GGUF 格式的出現讓模型權重可以標準化分發，但使用者仍需自行處理推理引擎的編譯、模型載入、記憶體管理。
- 大型語言模型（如 Llama 3、Gemma 4）的參數量從 3B 到 405B 不等，需要不同的硬體配置與量化策略。

### 通用技術背景（自行補查）

- 2023 年起，開源 LLM 生態快速發展（Llama、Mistral、Gemma、Qwen 等），但缺乏統一的本地執行工具鏈。每個模型系列有自己的推理程式碼或依賴特定框架。
- 雲端 LLM API（OpenAI、Anthropic、Google）雖然方便，但存在資料隱私、延遲、成本、網路依賴等限制。企業與個人用戶對本地推理的需求持續增長。
- Docker 容器化雖然簡化了環境配置，但 GPU 穿透（GPU passthrough）在 macOS 上不可行，在 Windows/Linux 上需要 nvidia-container-toolkit 等額外設定，對非 DevOps 人員門檻仍高。
- 量化技術（Q4_K_M、Q8_0 等）讓大模型可以在消費級硬體上運行，但量化參數的選擇與效果需要經驗。

---

## 3. 這個技術是如何解決該問題的？

Ollama 的架構可拆解為以下四層：

```
┌─────────────────────────────────────────────┐
│  CLI (ollama run/pull/push/ps/stop/...)     │
│  REST API (localhost:11434)                 │
│  SDK (Python / JavaScript / 社群 SDK)        │
├─────────────────────────────────────────────┤
│  Go 服務層                                   │
│  - 模型生命週期管理（載入/卸載/快取）          │
│  - 請求排程與並行控制                         │
│  - Modelfile 解析與模型自訂                   │
│  - 模型下載/上傳（分層 digest 管理）           │
├─────────────────────────────────────────────┤
│  llama.cpp 推理引擎（C/C++）                  │
│  - GGUF 模型載入與解析                        │
│  - GPU 後端抽象（CUDA/ROCm/Vulkan/Metal/CPU）│
│  - 量化支援（Q4_K_M, Q8_0, ...）             │
│  - Flash Attention / K/V cache 量化           │
├─────────────────────────────────────────────┤
│  硬體層                                      │
│  NVIDIA GPU / AMD GPU / Intel GPU / Apple   │
│  Silicon / CPU-only                         │
└─────────────────────────────────────────────┘
```

### 3.1 模型管理

Ollama 使用 content-addressable storage（基於 SHA256 digest）管理模型層：

```
模型 = 多個 layer 的組合
  - 基礎權重層（GGUF 檔案）
  - 配置層（template / parameters / system prompt）
  - adapter 層（LoRA 微調權重）
  - license 層

每個 layer 以 SHA256 digest 為識別碼，支援去重與增量下載。
```

`ollama pull llama3.2` 的流程：

```
1. 查詢 manifest（取得所有 layer 的 digest 與大小）
2. 比對本地已有 layer（跳過已下載的 digest）
3. 並行下載缺失 layer（支援斷點續傳）
4. 驗證 SHA256
5. 寫入 manifest
6. 清理未使用的 layer
```

### 3.2 Modelfile 自訂機制

Modelfile 是 Ollama 的核心自訂介面，語法類似 Dockerfile：

```
FROM llama3.2
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
SYSTEM You are a helpful assistant.
TEMPLATE """{{ if .System }}{{ .System }}{{ end }}
{{ .Prompt }}"""
ADAPTER ./my-lora.gguf
LICENSE MIT
MESSAGE user What is the capital of France?
MESSAGE assistant Paris
```

支援的 PARAMETER 包括：`temperature`、`top_k`、`top_p`、`min_p`、`repeat_penalty`、`seed`、`num_ctx`、`num_predict`、`stop` 等。

### 3.3 REST API 設計

Ollama 提供 12 個 REST endpoint，全部以 JSON 格式通訊：

| Endpoint | 功能 |
|---|---|
| `POST /api/generate` | 文字生成（支援 streaming / JSON schema / 圖片輸入） |
| `POST /api/chat` | 對話生成（支援 tools / 歷史訊息 / 圖片輸入） |
| `POST /api/create` | 建立模型（從現有模型 / GGUF / Safetensors） |
| `GET /api/tags` | 列出本地模型 |
| `POST /api/show` | 顯示模型詳細資訊 |
| `POST /api/copy` | 複製模型 |
| `DELETE /api/delete` | 刪除模型 |
| `POST /api/pull` | 下載模型 |
| `POST /api/push` | 上傳模型 |
| `POST /api/embeddings` | 產生嵌入向量 |
| `GET /api/ps` | 列出執行中模型 |
| `GET /api/version` | 版本查詢 |

Streaming 為預設行為（SSE 風格 JSON stream），可透過 `"stream": false` 關閉。

### 3.4 並行與資源管理

Ollama 的並行模型：

```
OLLAMA_MAX_LOADED_MODELS (default: 3 * GPU 數)
  └─ 最多同時載入的模型數量

OLLAMA_NUM_PARALLEL (default: 1)
  └─ 單一模型可同時處理的請求數
     └─ context size = num_ctx * OLLAMA_NUM_PARALLEL

OLLAMA_MAX_QUEUE (default: 512)
  └─ 佇列上限，超過回傳 503

keep_alive (default: 5m)
  └─ 模型在記憶體中的保留時間
```

GPU 記憶體不足時，Ollama 會自動卸載閒置模型以釋放 VRAM。

### 3.5 多 GPU 支援

- 若模型可完全放入單張 GPU：載入到該 GPU（最佳效能，無 PCIe 傳輸）
- 若模型無法放入單張 GPU：分散到所有可用 GPU

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表：替代方案對照

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **llama.cpp** (直接使用) | 手動下載 GGUF 檔案，透過 `llama-cli` 或 `llama-server` 執行推理 | C/C++ 編譯環境；需手動管理模型檔案路徑與 GPU 參數 | 無統一模型管理 CLI；無標準化模型自訂格式；需自行撰寫 API wrapper | 更底層的控制能力，但操作步驟多 5～10 倍 |
| **LocalAI** | 提供與 OpenAI API 相容的本地 LLM 伺服器，支援多種後端（llama.cpp、transformers 等） | Docker 或 Go 執行環境；需手動配置後端映射 | 配置複雜度較高；後端抽象層增加效能開銷（約 5-15%）；文件品質波動大 | API 相容性最高（可直接取代 OpenAI endpoint），但入門門檻高於 Ollama |
| **vLLM** | 高效能 LLM 推理引擎，主打 PagedAttention 與連續批次處理 | Python 環境；CUDA GPU（非 NVIDIA GPU 支援有限） | 僅支援特定模型架構（Llama、Mistral、Qwen 等）；不支援 GGUF 格式；資源消耗較高 | 吞吐量最高（適合生產環境多用戶場景），但對消費級硬體與單用戶場景過重 |
| **GPT4All** | 提供桌面 GUI 應用與本地 LLM 執行環境，使用 Nomic AI 的自訂後端 | 桌面作業系統（macOS / Windows / Linux） | 模型選擇受限於 Nomic 生態系；API 相容性較低；社群規模較小 | 最適合非技術用戶（GUI 優先），但靈活性與生態系規模低於 Ollama |

### 切入點差異分析

```
Ollama 的定位：                LocalAI 的定位：
「開發者友善的本地 LLM 工具鏈」   「OpenAI API 的本地替代品」
  CLI 優先                       API 優先
  模型管理內建                    模型管理需手動
  Modelfile 自訂                 無對應機制

llama.cpp 的定位：              vLLM 的定位：
「底層推理引擎」                  「生產級高效能推理」
  無模型管理層                    PagedAttention
  需自行封裝                     批次處理最佳化
  最大靈活性                     最適合多用戶

GPT4All 的定位：
「非技術用戶的桌面 LLM」
  GUI 優先
  模型選擇受限
```

### 反證表：Ollama 的限制

| 限制面向 | 具體內容 | 適用場景 |
|---|---|---|
| 生產環境吞吐量 | 單一模型預設僅 1 個並行請求，需手動調高 `OLLAMA_NUM_PARALLEL` | 高併發 API 服務 |
| 模型架構支援 | 依賴 llama.cpp 支援的架構，新架構（如 Mamba、RWKV）需等待上游 | 非 Transformer 架構模型 |
| 批次處理 | 無 vLLM 等級的 continuous batching | 大量短請求場景 |
| 分散式推理 | 無跨機推理支援 | 單機 VRAM 不足時 |
| 模型訓練/微調 | 僅支援 LoRA adapter 載入，不支援訓練 | 需要 fine-tune 的場景 |
