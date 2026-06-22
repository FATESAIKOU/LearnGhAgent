# ollama 技術分析報告

> 調研對象：GitHub [ollama/ollama](https://github.com/ollama/ollama)（v0.30.10, MIT License, 175k stars）
> 調研日期：2026-06-22

---

## 1. 這個技術解決什麼問題？

**Ollama 解決的問題：讓使用者在個人電腦（無 GPU 或消費級 GPU）上，以一條指令完成大型語言模型的下載、執行、管理與 API 暴露，無需手動配置 GPU 驅動、模型格式轉換、量化參數或推理框架。**

具體而言，ollama 解決了以下子問題：

| 子問題 | 說明 |
|--------|------|
| 模型取得 | 從 Hugging Face 或其他來源下載模型後，需轉換為特定推理框架可讀的格式（如 GGUF） |
| 硬體加速配置 | 不同 GPU（NVIDIA CUDA / AMD ROCm / Apple Metal）需安裝對應驅動與 runtime，且推理框架需針對各平台編譯 |
| API 暴露 | 本地模型需自行撰寫 HTTP server 包裝推理邏輯，才能被其他應用（如聊天 UI、IDE 外掛）呼叫 |
| 多模型管理 | 同時管理多個模型版本、量化等級、自訂參數時，缺乏統一的管理介面 |
| 跨平台一致性 | 同一模型在 macOS / Linux / Windows 上的執行方式與 API 介面不一致 |

**模糊之處**：ollama 官方文件未明確定義「支援的模型大小上限」。雖然理論上可執行任意 GGUF 模型，但消費級硬體的 VRAM 限制（8GB~24GB）實質上限制了可流暢運行的模型規模（通常為 7B~70B 參數，依量化等級而定）。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **llama.cpp 的出現**：ollama 的 README 明確指出其底層推理引擎為 [llama.cpp](https://github.com/ggerganov/llama.cpp)，這是一個純 C/C++ 實作的 LLM 推理框架，支援 CPU 與 GPU 推理，並定義了 GGUF 模型格式。llama.cpp 解決了「在非 NVIDIA 硬體上執行 LLM」的問題，但本身僅提供 C++ API 與簡易 CLI，缺乏高階管理功能。
- **模型格式碎片化**：Hugging Face 上的模型以 Safetensors / PyTorch 格式為主，需轉換為 GGUF 才能被 llama.cpp 載入。轉換工具（如 `convert.py`）需手動執行且依賴 Python 環境。
- **GPU 生態分裂**：NVIDIA CUDA、AMD ROCm、Apple Metal 各有不同的驅動安裝流程與編譯選項，llama.cpp 雖支援三者，但使用者需自行編譯對應後端。

### 通用技術背景（非文章明確提及）

- **LLM 部署門檻**：2022~2023 年 LLM 熱潮初期，主流模型（GPT-3, PaLM）僅以雲端 API 形式提供。開源模型（LLaMA, Alpaca, Vicuna）雖陸續釋出，但部署需熟悉 Python、PyTorch、CUDA 等技術棧，非 ML 工程師難以操作。
- **量化技術成熟**：GPTQ、GGML/GGUF、AWQ 等量化格式的成熟，使 7B~13B 參數模型可在 8GB VRAM 的消費級 GPU 上運行，但量化工具鏈仍分散。
- **容器化 vs 原生套件**：部分專案（如 LocalAI）以 Docker 容器封裝推理環境，但容器對 GPU 穿透（GPU passthrough）的支援仍不穩定，且佔用磁碟空間較大。ollama 選擇原生二進位檔安裝，降低使用摩擦。

---

## 3. 這個技術是如何解決該問題的？

Ollama 的架構分為三層：

```
┌─────────────────────────────────────────────┐
│                  CLI (cobra)                  │
│  ollama run / pull / push / create / serve   │
├─────────────────────────────────────────────┤
│              HTTP Server (gin)               │
│  /api/chat  /api/generate  /api/embed        │
│  /api/tags  /api/pull  /api/push  /api/copy  │
│  /api/create  /api/delete  /api/ps           │
│  /api/show  /api/blobs  /api/version         │
├─────────────────────────────────────────────┤
│            Go 核心層 (模型管理)                │
│  - 模型 registry（下載/快取/版本管理）        │
│  - Modelfile 解析器（FROM/PARAMETER/...）     │
│  - 並發請求佇列（單模型單執行緒）             │
│  - 模型生命週期管理（載入/卸載/keep_alive）   │
├─────────────────────────────────────────────┤
│          Native Backend (C/C++)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ llama.cpp │  │  MLX     │  │ (其他)   │  │
│  │ (CUDA/    │  │ (Apple   │  │          │  │
│  │  ROCm/    │  │  Silicon)│  │          │  │
│  │  Vulkan/  │  │          │  │          │  │
│  │  CPU)     │  │          │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────┘
```

### 3.1 模型下載與快取

```
ollama pull llama3.2
```

執行流程：

1. CLI 解析指令，呼叫 Go 層的 `PullHandler`
2. Go 層向 `registry.ollama.ai` 查詢模型 manifest（包含 digest、檔案列表、sha256）
3. 依 manifest 下載 GGUF 模型檔至 `~/.ollama/models/blobs/`，以 sha256 digest 作為檔名（content-addressable storage）
4. 寫入 `~/.ollama/models/manifests/` 記錄模型標籤與 blob 的對應關係
5. 返回完成狀態

**關鍵設計**：blob 儲存以 digest 定址，同一檔案即使被不同模型引用也只存一份。

### 3.2 模型執行（`ollama run` / `/api/chat`）

```
ollama run llama3.2 "Hello, world!"
```

執行流程：

1. Go 層從 manifest 查找模型對應的 GGUF 檔案路徑
2. 載入 GGUF 檔案至 llama.cpp backend（若模型已在記憶體中且 `keep_alive` 未到期，則跳過載入）
3. llama.cpp 執行 tokenization → inference → detokenization
4. 結果以 streaming（SSE, `text/event-stream`）或非 streaming 形式返回
5. 若 `keep_alive` 設為 0，推理完成後立即卸載模型釋放 VRAM

**API 請求範例**（chat endpoint）：

```json
POST /api/chat
{
  "model": "llama3.2",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "stream": true,
  "options": {
    "temperature": 0.7,
    "top_p": 0.9
  }
}
```

**回應（streaming）**：

```
data: {"message":{"role":"assistant","content":"Hi"},"done":false}
data: {"message":{"role":"assistant","content":" there"},"done":false}
data: {"message":{"role":"assistant","content":"!"},"done":false}
data: {"message":{"role":"assistant","content":""},"done":true,"total_duration":123456789}
```

### 3.3 Modelfile — 模型自訂

Modelfile 是 ollama 定義的模型描述格式，類似 Dockerfile 的概念：

```
FROM llama3.2
PARAMETER temperature 0.7
PARAMETER top_p 0.9
SYSTEM "You are a helpful assistant specialized in Python programming."
TEMPLATE "{{ .Prompt }}"
```

支援的指令：

| 指令 | 功能 | 範例 |
|------|------|------|
| `FROM` | 指定基底模型（registry 名稱或本地 GGUF 路徑） | `FROM llama3.2` |
| `PARAMETER` | 設定推理參數 | `PARAMETER temperature 0.7` |
| `TEMPLATE` | 自訂 prompt 模板（Go template 語法） | `TEMPLATE "{{ .Prompt }}"` |
| `SYSTEM` | 設定系統提示詞 | `SYSTEM "You are a bot"` |
| `ADAPTER` | 掛載 LoRA adapter | `ADAPTER ./lora.safetensors` |
| `LICENSE` | 標記模型授權 | `LICENSE MIT` |
| `MESSAGE` | 嵌入 few-shot 範例對話 | `MESSAGE user "Hi"` |
| `REQUIRES` | 宣告所需模型能力 | `REQUIRES vision` |

建立自訂模型：

```
ollama create my-model -f ./Modelfile
```

### 3.4 GPU 支援機制

Ollama 在安裝時自動偵測 GPU 並下載對應的 backend 二進位檔：

| GPU 類型 | 偵測方式 | 使用的 backend |
|----------|----------|----------------|
| NVIDIA GPU (CC 5.0+) | `nvidia-smi` | llama.cpp CUDA backend |
| AMD GPU (ROCm v7) | `rocm-smi` | llama.cpp ROCm backend |
| Apple Silicon (M1+) | `sysctl` 偵測 | llama.cpp Metal backend + MLX |
| 其他 GPU (Vulkan) | Vulkan loader | llama.cpp Vulkan backend |
| 無 GPU | 預設 | llama.cpp CPU backend (BLAS) |

### 3.5 Tool Calling（函式呼叫）

Ollama 支援模型定義可呼叫的工具，模型可在回應中要求執行特定函式：

```json
POST /api/chat
{
  "model": "llama3.2",
  "messages": [{"role": "user", "content": "What's the weather in Paris?"}],
  "tools": [{
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "Get current weather",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {"type": "string"}
        }
      }
    }
  }]
}
```

模型回應包含 `tool_calls` 欄位，應用端執行工具後將結果傳回模型進行第二輪推理（multi-turn agent loop）。

### 3.6 雲端方案

Ollama 提供本地免費 + 雲端付費的混合模式：

| 方案 | 價格 | 說明 |
|------|------|------|
| 本地（Local） | 免費 | 完全在本機執行，無網路需求 |
| Pro | $20/月 | 雲端託管模型，支援 team collaboration |
| Max | $100/月 | 更高用量限制，優先 GPU 資源 |

雲端模型透過 `ollama pull` 下載 cloud 標籤的模型，實際推理在 ollama 雲端伺服器執行，但 API 介面與本地一致。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表：替代方案比較

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|----------|--------------|----------------|------------------|
| **llama.cpp** | 純 C/C++ LLM 推理框架，提供 `llama-cli` 與 `llama-server` 二進位檔 | 需自行編譯（CMake + make），或下載 pre-built binary；需手動下載 GGUF 模型檔 | 無統一模型管理；無自動 GPU 偵測；API 需自行啟動 `llama-server`；無 Modelfile 概念 | 最低 overhead 的推理方案，適合嵌入其他應用或需要完全控制推理管線的場景 |
| **vLLM** | Python 推理引擎，以 PagedAttention 優化 KV cache 記憶體管理，支援 Continuous Batching | 需 Python 3.8+、CUDA GPU（不支援 AMD/Metal）；模型需為 Hugging Face 格式（Safetensors） | 依賴 Python 生態；僅支援 NVIDIA GPU；安裝依賴多（torch, transformers, xformers）；二進位檔體積大 | 高吞吐量場景（生產環境 API serving），batch 推理效率優於 ollama，但部署複雜度較高 |
| **LocalAI** | 以 Docker 容器封裝多種推理後端（llama.cpp, whisper, stable diffusion 等），提供 OpenAI API 相容介面 | 需 Docker 環境；需手動編輯 YAML 配置檔指定模型路徑與後端 | 容器佔用磁碟空間大；GPU passthrough 需額外 Docker 配置；模型管理無統一 CLI | 單一容器提供多模態能力（LLM + 語音 + 圖片生成），但啟動速度與資源效率不如原生二進位檔 |
| **LM Studio** | 圖形化桌面應用（Electron），內建模型瀏覽器與下載介面，支援 GGUF 模型 | 僅提供 GUI（無 headless API-first 設計）；僅支援 Windows/macOS（無 Linux 原生支援） | 無程式化 API（雖有 local HTTP server 但非設計核心）；不適合 CI/CD 或自動化部署；資源消耗較高（Electron） | 最適合非技術使用者的圖形化方案，但無法作為服務元件嵌入其他系統 |

### 切入點差異分析

```
                   純推理引擎 ←──────────────────→ 完整產品
                    (low-level)                    (high-level)

llama.cpp ──→ vLLM ──→ ollama ──→ LocalAI ──→ LM Studio
  C/C++        Python     Go + C      Docker      Electron
  無管理        有管理      有管理      有管理      有管理
  無 API        有 API     有 API      有 API      有 GUI
  無模型管理    無模型管理  有模型管理  有模型管理  有模型管理
```

- **llama.cpp** 是 ollama 的底層基礎，提供推理能力但不提供管理層。選擇 llama.cpp 意味著自行建構管理層。
- **vLLM** 與 ollama 的目標場景不同：vLLM 優化的是「多請求併發吞吐量」（production serving），ollama 優化的是「單使用者開發者體驗」（local development）。
- **LocalAI** 與 ollama 功能重疊度最高，但 LocalAI 以 Docker 為核心部署單元，ollama 以原生二進位檔為核心。LocalAI 支援更多後端（whisper, stable diffusion），ollama 專注於 LLM。
- **LM Studio** 與 ollama 的目標使用者不同：LM Studio 面向非開發者（圖形化操作），ollama 面向開發者（CLI + API）。

### 反證表：ollama 的潛在限制

| 面向 | ollama 的作法 | 替代方案可能更好的情況 |
|------|---------------|----------------------|
| 多請求併發 | 單模型單執行緒佇列，請求依序處理 | vLLM 的 continuous batching 在高併發場景吞吐量更高 |
| 模型格式 | 僅支援 GGUF | vLLM 直接支援 Hugging Face Safetensors，無需轉換 |
| GPU 支援廣度 | NVIDIA + AMD + Apple + Vulkan | vLLM 僅 NVIDIA；llama.cpp 支援範圍與 ollama 相同 |
| 部署方式 | 原生二進位檔（無容器依賴） | LocalAI 的 Docker 方式在 Kubernetes 環境更易整合 |
| 多模態支援 | 僅 LLM（文字 + 視覺） | LocalAI 涵蓋語音辨識、圖片生成 |
| 模型自訂 | Modelfile（類似 Dockerfile） | llama.cpp 直接修改 C++ 程式碼可做到更底層控制 |

**結論**：ollama 在「開發者體驗」與「跨平台 GPU 支援」兩個維度上優於多數替代方案，但在「高併發生產環境 serving」與「多模態支援」上不如專門方案。
