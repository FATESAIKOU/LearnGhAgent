# Ollama 技術分析報告

## 1. 這個技術解決什麼問題？

Ollama 解決的是「在本地端執行大型語言模型（LLM）的門檻過高」的問題。具體而言：

- 使用者需要手動下載模型權重檔案（通常數 GB 至數十 GB）
- 需要自行處理模型格式轉換（Hugging Face Safetensors → GGUF）
- 需要自行編譯或配置推論引擎（如 llama.cpp、transformers）
- 需要自行撰寫 API 層或整合程式碼才能將模型嵌入應用
- 不同模型有不同的依賴與執行方式，缺乏統一的執行介面

Ollama 將上述流程封裝成一個單一的 CLI 工具 + REST API 伺服器，讓使用者只需一條指令（`ollama run <model-name>`）即可下載並執行 LLM。

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- LLM 推論需要大量 GPU 運算資源，傳統上依賴雲端 API（OpenAI、Anthropic 等）
- 雲端 API 有資料隱私、延遲、持續付費等限制
- llama.cpp 專案（C/C++ 實作）讓消費級硬體（CPU、消費級 GPU）也能執行 LLM，但使用上仍需手動操作

### 通用技術背景

- 2023～2024 年間，開源 LLM 數量爆炸成長（Llama 2/3、Mistral、DeepSeek、Phi 等），但缺乏統一的本地執行標準
- GGUF 格式（llama.cpp 定義的二進位模型格式）逐漸成為開源 LLM 的事實標準，但一般使用者仍需了解 GGUF 與 Safetensors 的差異
- 量化技術（Q4_K_M、Q5_K_M 等）讓模型體積與記憶體需求大幅降低，但參數選擇對非技術使用者不直觀
- 各模型對系統提示（system prompt）、對話模板（chat template）的格式要求不同，手動設定容易出錯

## 3. 這個技術是如何解決該問題的？

Ollama 的架構分為三層：

```
┌─────────────────────────────────────────┐
│  CLI (ollama run/pull/push/create/ls)    │  ← 使用者介面層
│  REST API (localhost:11434)              │
├─────────────────────────────────────────┤
│  Model Store (~/.ollama/models/)         │  ← 模型管理層
│  Modelfile (自訂模型定義)                │
├─────────────────────────────────────────┤
│  llama.cpp (C/C++ 推論引擎)              │  ← 推論執行層
│  GPU Backend (CUDA/ROCm/Vulkan/Metal)    │
└─────────────────────────────────────────┘
```

### 3.1 模型下載與管理

- 使用者執行 `ollama pull <model-name>` 時，Ollama 從官方 registry（ollama.com/library）下載預先量化好的 GGUF 格式模型
- 模型儲存在 `~/.ollama/models/` 目錄，支援 `ollama ls` 列出已下載模型、`ollama rm` 刪除
- 模型命名採用 `model-name:tag` 格式（如 `llama3.2:3b`），tag 對應不同大小與量化版本

### 3.2 統一的執行介面

- `ollama run <model-name>`：互動式對話模式，自動載入模型到記憶體
- `ollama run <model-name> "prompt"`：單次查詢模式
- REST API `POST /api/chat` 與 `POST /api/generate`：供外部應用整合
- API 支援串流（streaming）回應，相容 OpenAI API 格式

### 3.3 Modelfile 自訂機制

Modelfile 是 Ollama 的自訂模型定義檔，類似 Dockerfile 的概念：

```
FROM llama3.2:3b          # 基底模型
PARAMETER temperature 0.7  # 推論參數
PARAMETER top_p 0.9
SYSTEM "You are a helpful assistant"  # 系統提示
TEMPLATE "{{ .Prompt }}"  # 對話模板
ADAPTER ./my-lora.safetensors  # LoRA 適配器
```

- `ollama create my-model -f ./Modelfile` 建立自訂模型
- 支援匯入 Safetensors 格式（Hugging Face）與 GGUF 格式
- 支援量化選項（q4_K_M、q5_K_M、q8_0 等）

### 3.4 硬體加速

- 自動偵測可用 GPU：NVIDIA（CUDA CC 5.0+）、AMD（ROCm）、Apple（Metal）、Vulkan
- 無 GPU 時自動回退 CPU 執行
- 支援多 GPU 並行推論

### 3.5 底層推論引擎

- 使用 llama.cpp 作為核心推論引擎（C/C++ 實作）
- 支援 GGUF 格式模型載入
- 支援 KV cache 快取加速連續對話
- 支援批次處理（batch processing）提升吞吐量

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **llama.cpp** | 直接使用 C/C++ 推論引擎，手動下載 GGUF 模型並透過 CLI 或 binding 執行 | 需了解 GGUF 格式、模型來源、編譯選項；需自行撰寫整合程式碼 | 無統一模型管理；無內建 API 伺服器；需手動處理對話模板 | 更底層的控制權，無額外抽象層開銷 |
| **LocalAI** | 提供 OpenAI API 相容的本地 LLM 伺服器，支援多種後端（llama.cpp、transformers、whisper 等） | 需 Docker 或自行編譯；設定檔較複雜（YAML 配置） | 功能範圍較大（含語音、圖片生成），學習曲線較高；資源消耗較重 | 更完整的 OpenAI API 相容性（含 embeddings、whisper、stable diffusion） |
| **vLLM** | 高效能 LLM 推論伺服器，使用 PagedAttention 最佳化記憶體管理 | 需 NVIDIA GPU（CUDA）；主要支援 Hugging Face 格式（非 GGUF） | 不支援消費級 GPU 量化推論；設定較複雜；無 CLI 互動模式 | 更高的推論吞吐量與記憶體效率，適合生產環境部署 |
| **GPT4All** | 提供桌面應用 + 本地 LLM 執行環境，強調隱私與離線使用 | 需下載桌面應用；模型選擇受限於其生態系 | 無 REST API（或功能有限）；模型更新較慢；不支援自訂模型匯入 | 最簡單的圖形化操作體驗，非技術使用者友善 |

### 切入點差異

- **Ollama vs llama.cpp**：Ollama 是 llama.cpp 的上層封裝，犧牲部分底層控制權換取易用性與模型管理功能
- **Ollama vs LocalAI**：Ollama 專注 LLM 執行（範圍較窄但深度較高），LocalAI 涵蓋多模態但設定複雜度更高
- **Ollama vs vLLM**：Ollama 定位個人開發者與消費級硬體，vLLM 定位生產環境與伺服器級 GPU
- **Ollama vs GPT4All**：Ollama 以 CLI/API 為核心（開發者導向），GPT4All 以桌面 GUI 為核心（一般使用者導向）
