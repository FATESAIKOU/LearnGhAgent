# Ollama 技術分析報告

> 調研標的：GitHub repo `ollama/ollama`（v0.14.x，2026-06-21）
> 授權：MIT | 語言：Go | Stars：174,616

---

## 1. 這個技術解決什麼問題？

Ollama 解決的是「在本地（無雲端依賴）簡易執行大型語言模型（LLM）」的問題。

具體而言，它解決了以下子問題：

- **模型取得與管理**：使用者需手動下載模型檔（GGUF）、處理版本、管理磁碟空間
- **執行環境建置**：LLM 推理需要 GPU 驅動、編譯後端（CUDA/ROCm/Vulkan）、記憶體配置等複雜設定
- **API 標準化**：不同模型有不同的 prompt template、參數格式、輸出結構，缺乏統一介面
- **工具整合**：開發者工具（VS Code、CLI agent）需要一個標準的本地 LLM 端點來整合

Ollama 將上述流程封裝成一個單一二進位檔 + REST API + CLI 的組合，使用者執行 `ollama run <model>` 即可完成從下載到推理的全部流程。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章中明確提到的背景

- Ollama 使用 `llama.cpp` 作為核心推理後端（README 明確標示）
- 支援多種硬體後端：CUDA（NVIDIA）、ROCm（AMD）、Vulkan（跨平台 GPU）、MLX（Apple Silicon）
- 模型格式為 GGUF（llama.cpp 定義的二進位格式）
- 首次釋出於 2023-07-07

### 2.2 通用技術背景

**LLM 本地執行的障礙鏈：**

```
模型權重（數 GB ~ 數十 GB）
  → 需特定格式（GGUF / Safetensors）
  → 需推理引擎（llama.cpp / TensorRT / ONNX）
  → 需 GPU 驅動與記憶體管理
  → 需 prompt template 與 tokenizer 設定
  → 需 API 層供外部程式呼叫
```

在 Ollama 出現前，本地執行 LLM 的典型流程是：

1. 從 Hugging Face 下載模型權重（PyTorch checkpoint 或 Safetensors）
2. 轉換為 GGUF 格式（使用 `convert.py` 腳本）
3. 編譯或下載 `llama.cpp` 二進位檔
4. 手動設定 context size、GPU layers、thread count 等參數
5. 啟動 `llama.cpp` server 或直接 CLI 互動
6. 自行撰寫 wrapper 腳本提供 REST API

這個流程涉及多個工具鏈、格式轉換、編譯步驟，對非 ML 專業的開發者門檻極高。

**2023 年 LLM 生態的關鍵轉折：**

- Meta 釋出 Llama 原始權重 → 社群開發 llama.cpp 實現消費級 GPU 推理
- GGUF 格式標準化 → 模型分發格式統一
- 量化技術（Q4_K_M 等）成熟 → 使 7B~13B 模型可在 8GB VRAM 上執行
- 開發者工具（Copilot、Cline、Continue）開始支援本地模型 → 產生對標準化本地 API 的需求

Ollama 正是在這個時間點（2023-07）切入，將上述碎片化的工具鏈整合為單一產品。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 系統架構

```
┌─────────────────────────────────────────────────┐
│                   使用者介面層                      │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │  CLI     │  │ REST API │  │ SDK (Python/JS)│  │
│  │ (cobra)  │  │ (gin)    │  │                │  │
│  └────┬─────┘  └────┬─────┘  └───────┬────────┘  │
├───────┴─────────────┴─────────────────┴──────────┤
│                  核心服務層                        │
│  ┌──────────────────────────────────────────────┐ │
│  │  Model Registry & Manager                    │ │
│  │  - pull / push / create / copy / delete      │ │
│  │  - 模型版本管理（digest-based）               │ │
│  │  - 模型快取與 blob 儲存                      │ │
│  └──────────────┬───────────────────────────────┘ │
│  ┌──────────────┴───────────────────────────────┐ │
│  │  Inference Scheduler                         │ │
│  │  - 模型載入 / 卸載（keep_alive 控制）        │ │
│  │  - 並行請求佇列管理                          │ │
│  │  - 記憶體管理                                │ │
│  └──────────────┬───────────────────────────────┘ │
├─────────────────┴─────────────────────────────────┤
│                  推理後端層                        │
│  ┌──────────────────────────────────────────────┐ │
│  │  llama.cpp (C/C++)                           │ │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐       │ │
│  │  │CUDA  │ │ROCm  │ │Vulkan│ │ MLX  │       │ │
│  │  └──────┘ └──────┘ └──────┘ └──────┘       │ │
│  └──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 3.2 核心機制

#### 3.2.1 模型管理（Model Registry + Blob Storage）

Ollama 將模型視為「層（layer）」的組合，類似容器映像：

```
模型 = FROM 基底模型 + PARAMETER + SYSTEM + TEMPLATE + ADAPTER
     = 多個 content-addressable blob 的組合
```

- 每個 blob 以 SHA256 digest 為識別碼
- 相同 digest 的 blob 只儲存一份（去重）
- `ollama pull` 只下載本地沒有的層（增量下載，支援斷點續傳）

**Modelfile 範例（從文件）：**

```
FROM llama3.2
PARAMETER temperature 1
PARAMETER num_ctx 4096
SYSTEM You are Mario from super mario bros, acting as an assistant.
```

執行 `ollama create mario -f Modelfile` 後，Ollama 會：
1. 解析 FROM → 定位基底模型的 blob
2. 建立新的 system layer blob（含 SYSTEM 內容）
3. 寫入 manifest（描述各層的 digest 組合）
4. 註冊模型名稱 `mario`

#### 3.2.2 推理執行（llama.cpp 後端）

Ollama 不自行實作模型推理，而是封裝 llama.cpp 作為共享函式庫：

```
使用者請求 → Ollama server → llama.cpp C API → GPU/CPU 推理 → 串流回傳
```

支援的推理參數（透過 PARAMETER 或 API options 傳遞）：

| 參數 | 作用 | 預設值 |
|------|------|--------|
| `num_ctx` | context window 大小（token 數） | 2048 |
| `temperature` | 隨機性控制 | 0.8 |
| `top_k` | 取前 K 個 token 採樣 | 40 |
| `top_p` | 累積機率採樣閾值 | 0.9 |
| `repeat_penalty` | 重複懲罰強度 | 1.1 |
| `seed` | 隨機種子（可重現性） | 0 |
| `num_predict` | 最大生成 token 數 | -1（無限） |
| `stop` | 停止序列 | 無 |

#### 3.2.3 REST API 標準化

Ollama 提供 12 個 REST API 端點，將不同模型的差異抽象化：

| 端點 | 功能 |
|------|------|
| `POST /api/generate` | 文字補全（completion） |
| `POST /api/chat` | 對話生成（chat），支援 tool calling |
| `POST /api/create` | 建立模型（Modelfile / Safetensors / GGUF） |
| `GET /api/tags` | 列出本地模型 |
| `POST /api/show` | 顯示模型資訊 |
| `POST /api/copy` | 複製模型 |
| `DELETE /api/delete` | 刪除模型 |
| `POST /api/pull` | 下載模型 |
| `POST /api/push` | 上傳模型 |
| `POST /api/embed` | 產生 embeddings |
| `GET /api/ps` | 列出執行中模型 |
| `GET /api/version` | 版本查詢 |

**關鍵設計：** 所有端點使用統一的 JSON 格式，模型名稱以 `model:tag` 標示。Ollama 內部根據模型 family（llama / qwen2 / gemma 等）自動選擇對應的 prompt template 與 tokenizer。

#### 3.2.4 工具整合（ollama launch）

Ollama 提供 `ollama launch <tool>` 機制，自動將本地模型與外部工具整合：

```
ollama launch claude    → 設定 Claude Code 使用本地 Ollama 端點
ollama launch opencode  → 設定 OpenCode 使用本地 Ollama 端點
ollama launch openclaw  → 啟動跨平台 AI 助理
```

這個機制透過修改工具的設定檔或環境變數，將 LLM 端點指向 `http://localhost:11434`。

### 3.3 安全性問題（已知）

2026-01 月發現約 175,000 台 Ollama 伺服器暴露於公開網路且無認證機制。Ollama 預設 binding 為 `127.0.0.1:11434`（僅本機），但部分使用者手動改為 `0.0.0.0` 且未設定防火牆規則。官方文件已加入安全警告。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|----------|-------------|---------------|-----------------|
| **llama.cpp** | 直接使用 C/C++ 推理引擎，手動管理模型與 API | 需編譯 C/C++、手動下載 GGUF、自行撰寫 server wrapper | 無統一 API 標準、需自行處理模型版本管理、無 SDK | 完全控制推理參數與後端，無額外抽象層開銷 |
| **LocalAI** | 提供 OpenAI API 相容的本地 LLM 伺服器，支援多後端（llama.cpp、transformers、whisper 等） | Docker 或 Go 執行環境、需手動設定模型 YAML 設定檔 | 設定複雜度高（YAML 設定）、多後端增加除錯難度、資源消耗較高 | 與 OpenAI SDK 完全相容，無需修改程式碼即可切換 |
| **vLLM** | 高效能 LLM 推理引擎，使用 PagedAttention 最佳化記憶體 | 需 NVIDIA GPU + CUDA、Python 環境、HuggingFace 格式模型 | 僅支援 NVIDIA GPU、不支援 GGUF 格式、資源需求高（建議 24GB+ VRAM） | 高吞吐量、支援 continuous batching、適合生產環境部署 |
| **GPT4All** | 桌面應用程式形式的本地 LLM 執行器，強調隱私與易用性 | 下載桌面安裝檔、支援 CPU 推理 | 模型選擇受限（僅支援 Nomic 生態模型）、API 功能較少、不適合伺服器部署 | 一鍵安裝即用、圖形化介面、最低技術門檻 |

### 4.2 切入點差異分析

```
                   易用性（低門檻）
                        │
                   GPT4All ●
                        │
              Ollama ●──┤
                        │
            LocalAI ●───┤
                        │
          llama.cpp ●───┤
                        │
              vLLM ●────┤
                        │
                   效能（高吞吐量）
```

- **Ollama** 定位在「易用性與功能完整性的平衡點」：比 GPT4All 更強大（支援自訂模型、REST API、tool calling），比 llama.cpp 更易用（一鍵安裝、自動模型管理）
- **llama.cpp** 是底層引擎，Ollama 與 LocalAI 都依賴它；選擇 llama.cpp 直接使用意味著放棄所有上層管理功能
- **LocalAI** 與 Ollama 最接近，差異在於 LocalAI 強調 OpenAI API 相容性（可直接替換 OpenAI 端點），但設定更複雜
- **vLLM** 面向生產環境，犧牲易用性換取吞吐量，不適合個人開發者或單機使用
- **GPT4All** 面向一般使用者，功能最受限但門檻最低

### 4.3 反證表：Ollama 的劣勢場景

| 場景 | Ollama 不適合的原因 | 更適合的方案 |
|------|-------------------|-------------|
| 高吞吐量生產部署（>100 req/s） | 無 continuous batching、無分散式推理 | vLLM + TensorRT-LLM |
| 需要完整 OpenAI API 相容性 | /api/chat 與 OpenAI 格式不完全一致（如 streaming 格式差異） | LocalAI |
| 嵌入現有 Python ML pipeline | Ollama 增加一層網路呼叫開銷 | 直接使用 transformers + llama.cpp Python binding |
| 資源受限裝置（4GB RAM 以下） | Ollama server 本身約 50MB + Go runtime 開銷 | 直接使用 llama.cpp 最小編譯 |
| 需要圖形化操作介面 | Ollama 僅 CLI + API，無 GUI | GPT4All / LM Studio |
