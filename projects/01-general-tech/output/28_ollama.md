# Ollama 技術分析報告

> 調研標的：GitHub [ollama/ollama](https://github.com/ollama/ollama)
> 分析日期：2026-06-21 | 版本：v0.30.10 | License：MIT
> 核心語言：Go 66.2% / C 27.0% | Stars：175k | Forks：16.7k

---

## 1. 這個技術解決什麼問題？

Ollama 解決的是「**在本地機器上執行、管理、自訂大型語言模型（LLM）的流程過於繁瑣**」的問題。

具體來說，Ollama 將以下操作整合為單一 CLI 工具：

- 模型下載與版本管理（`ollama pull` / `ollama run`）
- 模型執行（封裝底層推理引擎）
- REST API 提供（預設 `localhost:11434`）
- 模型自訂（Modelfile 機制）
- 多模型並存與切換

**模糊之處**：Ollama 官方定位為「Start building with open models」，未明確區分其目標使用者是「終端使用者」還是「開發者」。實際上它同時服務兩者：終端使用者用 `ollama run` 直接對話，開發者用 REST API 整合進應用。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- Ollama README 指出其目標是讓使用者「get up and running with large language models locally」，暗示在此之前本地執行 LLM 的門檻過高。
- 支援 macOS、Linux、Windows 三平台，暗示跨平台一致性是痛點。

### 通用技術背景

LLM 在 2022-2023 年（ChatGPT 爆發後）快速普及，但本地執行面臨以下障礙：

| 障礙 | 說明 |
|------|------|
| **模型格式碎片化** | Hugging Face 上的模型有 PyTorch、TensorFlow、SafeTensors、GGUF 等多種格式，每種需要不同載入方式 |
| **推理引擎選擇困難** | llama.cpp、vLLM、TensorRT-LLM、MLC-LLM 等引擎各有不同依賴與安裝方式 |
| **GPU 後端碎片化** | NVIDIA CUDA、AMD ROCm、Apple Metal、Intel oneAPI 等後端需要不同編譯參數與 runtime |
| **模型管理缺失** | 下載、版本追蹤、模型切換缺乏標準工具，使用者需手動管理權重檔案 |
| **API 標準不一致** | 每個推理引擎暴露的 API 不同，開發者難以寫出可移植的應用 |

Ollama 的出現正值開源 LLM（Llama、Mistral、Qwen 等）大量釋出，但「下載權重 → 編譯引擎 → 啟動服務」的流程對非 ML 工程師而言門檻極高。

---

## 3. 這個技術是如何解決該問題的？

Ollama 的解法是**分層封裝**，將複雜的推理流程隱藏在統一的 CLI + REST API 背後。

### 3.1 系統架構

```
┌─────────────────────────────────────────────┐
│                 使用者介面層                    │
│  ┌──────────┐  ┌────────────┐  ┌──────────┐  │
│  │ ollama   │  │ REST API  │  │ SDK      │  │
│  │ CLI      │  │ :11434    │  │ (py/js)  │  │
│  └────┬─────┘  └─────┬──────┘  └────┬─────┘  │
├───────┴──────────────┴──────────────┴────────┤
│              Go 服務層（ollama 主體）            │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ 模型管理  │  │ 請求路由  │  │ Modelfile    │ │
│  │ (pull/    │  │ (generate │  │ 解析器       │ │
│  │  push/rm) │  │  /chat)   │  │              │ │
│  └────┬─────┘  └─────┬────┘  └──────┬───────┘ │
├───────┴──────────────┴──────────────┴────────┤
│           推理引擎層（C/C++ native）            │
│  ┌─────────────────────────────────────────┐  │
│  │          llama.cpp (GGUF)               │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │  │
│  │  │CUDA  │ │ROCm  │ │Metal │ │Vulkan│…  │  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘   │  │
│  └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### 3.2 核心機制

#### a) 模型管理（`ollama pull` / `ollama run`）

Ollama 使用自己的模型倉儲格式（基於 GGUF），透過 `ollama pull <model>:<tag>` 從官方 registry（或自建 registry）下載模型。模型儲存在 `~/.ollama/models/`。

```
ollama pull llama3.2:3b    # 下載 Llama 3.2 3B 模型
ollama run llama3.2:3b     # 下載（若無）→ 載入 → 啟動互動式對話
```

#### b) REST API（`localhost:11434`）

Ollama 啟動後在 11434 埠暴露 HTTP API，主要端點：

| 端點 | 方法 | 用途 |
|------|------|------|
| `/api/generate` | POST | 單次文字生成（非對話） |
| `/api/chat` | POST | 多輪對話生成 |
| `/api/embeddings` | POST | 產生文字嵌入向量 |
| `/api/tags` | GET | 列出本地模型 |
| `/api/pull` | POST | 下載模型 |
| `/api/push` | POST | 上傳模型至 registry |
| `/api/create` | POST | 從 Modelfile 建立模型 |
| `/api/ps` | GET | 列出目前載入的模型 |

API 請求範例（generate）：

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

API 請求範例（chat）：

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2:3b",
  "messages": [
    {"role": "user", "content": "Why is the sky blue?"}
  ],
  "stream": false
}'
```

#### c) Modelfile — 模型自訂機制

Modelfile 是 Ollama 的模型藍圖，類似 Dockerfile 之於容器。使用者可基於現有模型建立自訂版本：

```
# 基礎模型
FROM llama3.2:3b

# 系統提示詞
SYSTEM "You are a helpful assistant specialized in Python programming."

# 推理參數
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 4096

# 掛載 LoRA adapter
ADAPTER ./my-lora.safetensors

# 嵌入授權資訊
LICENSE "MIT"
```

建立自訂模型：

```bash
ollama create my-custom-model -f ./Modelfile
```

#### d) 底層推理引擎：llama.cpp

Ollama 使用 [llama.cpp](https://github.com/ggml-org/llama.cpp) 作為預設推理引擎。llama.cpp 是純 C/C++ 實作，無外部依賴，支援：

- **GGUF 格式**：統一模型格式，內含權重、tokenizer、metadata
- **量化支援**：1.5-bit 到 8-bit 多種量化方案（Q2_K, Q3_K, Q4_K_M, Q5_K_M, Q8_0, IQ1_S 等）
- **GPU 後端**：CUDA、ROCm、Metal、Vulkan、SYCL、OpenVINO、CANN、WebGPU 等 15+ 後端
- **CPU+GPU 混合推理**：部分層在 GPU、部分在 CPU

Ollama 在編譯時選擇啟用哪些後端（透過 CMake flags），使用者無需手動處理後端選擇。

### 3.3 安裝方式

| 平台 | 安裝方式 |
|------|----------|
| macOS | `brew install ollama` 或官網 .dmg |
| Linux | `curl -fsSL https://ollama.com/install.sh \| sh` |
| Windows | 官網 .exe 安裝檔 |
| Docker | `docker run -d -v ollama:/root/.ollama -p 11434:11434 ollama/ollama` |

### 3.4 商業模式

| 方案 | 價格 | 說明 |
|------|------|------|
| 本地版 | 免費 | 完全本地執行，無雲端依賴 |
| Ollama Cloud Free | 免費 | 雲端託管，有限額度 |
| Ollama Cloud Pro | $20/月 | 雲端託管，較高額度 |
| Ollama Cloud Max | $100/月 | 雲端託管，最高額度 |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表：替代方案對照

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|----------|--------------|----------------|------------------|
| **LocalAI** | Go 實作，提供 OpenAI API 相容的本地 LLM 服務，支援多種後端（llama.cpp、transformers、diffusers） | 需 Docker 或 Go 編譯環境；需手動下載模型 | API 相容性非 100%；部分後端需額外編譯依賴 | 可無痛替換 OpenAI API 呼叫，適合已有 OpenAI 整合的應用 |
| **GPT4All** | nomic.ai 開發，C++ 實作，專注桌面端本地 LLM 執行，內建 GUI 與模型瀏覽器 | 僅支援其專屬模型格式（.guf）；模型選擇受限於 nomic 生態 | 模型生態封閉，無法使用 Hugging Face 上任意模型 | 最簡單的桌面端 LLM 體驗，一鍵安裝即用 |
| **LM Studio** | 專有軟體，提供圖形化介面管理與執行 LLM，支援 GGUF 模型，內建模型瀏覽器與下載 | 僅 Windows/macOS；專有授權，無法自訂或嵌入 | 無 CLI 與 REST API（或有限）；無法 headless 部署；商業使用需注意授權 | 最友善的 GUI 體驗，適合非技術使用者探索 LLM |
| **llamafile** | Mozilla 專案，將 llama.cpp + 模型權重打包成單一可執行檔（.llamafile），跨平台執行 | 需下載對應平台的 .llamafile 檔案；檔案體積大（含權重） | 每次更換模型需下載新檔案；無法動態切換模型 | 零安裝、零依賴，下載後直接執行，適合展示與教學 |

### 切入點差異分析

| 面向 | Ollama | LocalAI | GPT4All | LM Studio | llamafile |
|------|--------|---------|---------|------------|-----------|
| **安裝難度** | 低（brew/curl/docker） | 中（Docker 或編譯） | 低（一鍵安裝） | 低（GUI 安裝） | 最低（下載即執行） |
| **API 標準** | 自訂 API | OpenAI 相容 | 自訂 API | 自訂 API | 自訂 API |
| **模型來源** | 官方 registry + 自訂 | 任意 GGUF | 僅 nomic 生態 | 任意 GGUF | 內嵌單一模型 |
| **headless 部署** | 支援 | 支援 | 不支援 | 不支援 | 支援 |
| **多模型管理** | 支援（tag 版本） | 支援 | 有限 | 支援 | 不支援（單檔單模型） |
| **GPU 加速** | 全後端 | 依後端選擇 | 有限 | 支援 | 支援 |
| **自訂模型** | Modelfile | 無 | 無 | 無 | 無 |
| **授權** | MIT 開源 | MIT 開源 | MIT 開源 | 專有 | Apache 2.0 |

### 總結

Ollama 的核心競爭力在於**模型管理 + REST API + 自訂機制（Modelfile）** 的整合，填補了「底層推理引擎（llama.cpp）」與「終端使用者/開發者」之間的空隙。替代方案各有側重：LocalAI 強在 API 相容性、GPT4All 與 LM Studio 強在桌面 GUI、llamafile 強在零依賴部署，但沒有一個方案同時提供 Ollama 的模型管理、API、自訂三層整合。
