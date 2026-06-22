# Ollama 技術分析報告

> 調研標的：GitHub [ollama/ollama](https://github.com/ollama/ollama)
> 分析日期：2026-06-22
> 版本參考：v0.30.6 ~ v0.30.10（2026/6/5 ~ 6/17）

---

## 1. 這個技術解決什麼問題？

Ollama 解決的是「在本地端（個人電腦或自有伺服器）以最簡操作執行大型語言模型（LLM）」的問題。

具體來說，它解決了以下子問題：

- **模型取得與管理**：使用者不需要手動下載模型權重、處理 GGUF 格式轉換、或管理模型檔案存放位置
- **硬體加速配置**：自動偵測 GPU（NVIDIA CUDA、AMD ROCm、Apple Metal、Vulkan）並載入對應的推理後端，使用者不需手動安裝或配置 CUDA/ROCm 工具鏈
- **API 標準化**：提供統一的 REST API（`/api/generate`、`/api/chat`、`/api/embed` 等），讓不同模型使用相同介面，開發者不需為每個模型撰寫不同的推理程式碼
- **模型自訂**：透過 Modelfile 機制，使用者可以從基礎模型建立自訂版本（調整 system prompt、temperature、context window、加入 LoRA adapter 等）

**模糊之處**：Ollama 的定位介於「終端使用者工具」與「開發者平台」之間。README 同時展示 `ollama run` 互動聊天與 REST API 兩種使用方式，但未明確區分目標受眾。此外，「支援的模型」範圍由 ollama.com/library 動態定義，repo 本身不固定支援哪些模型，這使得「Ollama 支援哪些模型」成為一個需要查詢外部網站才能回答的問題。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- LLM 推理依賴於 llama.cpp 專案（由 Georgi Gerganov 創立），該專案提供了 GGUF 格式與 CPU/GPU 推理的底層實作
- 不同 GPU 供應商使用不同的加速庫：NVIDIA CUDA、AMD ROCm、Apple Metal、Vulkan
- 模型以 GGUF 格式分發，需要特定的載入與量化工具鏈

### 通用技術背景

- 大型語言模型的權重檔案通常為數 GB 到數十 GB，手動下載與管理對非專業使用者門檻高
- 每個模型的 prompt template 格式不同（如 Llama 的 `<|start_header_id|>`、Mistral 的 `[INST]`），直接使用 llama.cpp 需要使用者自行處理 template
- GPU 推理需要 CUDA/ROCm 等底層庫，安裝與版本對齊對開發者而言是常見痛點
- 在 Ollama 出現之前，要在本地執行 LLM 的典型流程是：下載 llama.cpp → 編譯 → 下載 GGUF 檔案 → 手動執行推理命令 → 自行撰寫 API wrapper。這個流程涉及多個步驟且跨語言（C++ 編譯 + Python/Shell 操作）

---

## 3. 這個技術是如何解決該問題的？

Ollama 的架構可以分為三個層次：

### 3.1 模型管理層（Go）

Ollama 本體以 Go 語言撰寫，負責：

- **模型倉儲管理**：`ollama pull` / `ollama push` 從 ollama.com/library 下載或上傳模型，支援斷點續傳
- **模型生命週期**：`ollama list` 列出本地模型、`ollama show` 顯示模型資訊、`ollama cp` / `ollama rm` 複製與刪除
- **模型自訂**：`ollama create` 從 Modelfile 建立自訂模型

Modelfile 的指令集：

| 指令 | 功能 | 範例 |
|------|------|------|
| `FROM` | 指定基礎模型（必要） | `FROM llama3.2` |
| `PARAMETER` | 設定推理參數 | `PARAMETER temperature 1` |
| `TEMPLATE` | 自訂 prompt template（Go template 語法） | `TEMPLATE """{{ .Prompt }}"""` |
| `SYSTEM` | 設定 system message | `SYSTEM You are a helpful assistant.` |
| `ADAPTER` | 套用 LoRA adapter | `ADAPTER ./lora.safetensors` |
| `LICENSE` | 指定授權條款 | `LICENSE MIT` |
| `MESSAGE` | 設定對話歷史範例 | `MESSAGE user Hello` |
| `REQUIRES` | 指定最低 Ollama 版本 | `REQUIRES 0.14.0` |

### 3.2 推理後端層（C/C++，llama.cpp）

Ollama 內建 llama.cpp 的編譯產物，支援多種 GPU 後端：

| 後端 | 支援平台 | 選擇方式 |
|------|---------|---------|
| CUDA v12/v13 | Linux, Windows | `-DOLLAMA_LLAMA_BACKENDS=cuda_v13` |
| ROCm v7.1/v7.2 | Linux, Windows | `-DOLLAMA_LLAMA_BACKENDS=rocm_v7_2` |
| Vulkan | Linux, Windows | `-DOLLAMA_LLAMA_BACKENDS=vulkan` |
| Metal (MLX) | macOS (Apple Silicon) | 預設啟用 |
| CPU | 所有平台 | 無 GPU 時自動降級 |

Ollama 在啟動時自動偵測可用 GPU 並載入對應的後端函式庫，使用者不需手動設定。

### 3.3 API 層（REST + SDK）

Ollama 提供 11 個 REST endpoints：

| Endpoint | 功能 |
|----------|------|
| `POST /api/generate` | 文字生成（補全） |
| `POST /api/chat` | 對話生成 |
| `POST /api/create` | 建立模型（從 Modelfile / GGUF / Safetensors） |
| `GET /api/tags` | 列出本地模型 |
| `POST /api/show` | 顯示模型詳細資訊 |
| `POST /api/copy` | 複製模型 |
| `DELETE /api/delete` | 刪除模型 |
| `POST /api/pull` | 下載模型 |
| `POST /api/push` | 上傳模型 |
| `POST /api/embed` | 產生 embeddings |
| `GET /api/version` | 版本查詢 |

支援 streaming（SSE）與非 streaming 兩種回應模式。支援 JSON schema structured output、tool calling、multimodal（圖片輸入）。

官方 SDK 提供 Python（`ollama` pip package）與 JavaScript（`ollama` npm package）兩種，社群 SDK 涵蓋 Java、.NET、Rust、Ruby、Swift、R 等語言。

### 3.4 執行流程示意

```
使用者輸入
    │
    ▼
ollama CLI / REST API  ←── Go 層（模型管理、請求路由）
    │
    ▼
llama.cpp runtime  ←── C/C++ 層（tokenization、inference）
    │
    ├── CUDA (NVIDIA GPU)
    ├── ROCm (AMD GPU)
    ├── Metal (Apple GPU)
    ├── Vulkan (通用 GPU)
    └── CPU fallback
    │
    ▼
模型輸出
```

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表：替代方案比較

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|---------|-------------|---------------|-----------------|
| **llama.cpp** | 直接使用 C++ 推理引擎，手動下載 GGUF 檔案並執行命令列推理 | 需自行編譯 C++ 程式碼、手動管理模型檔案、了解 GGUF 格式 | 無統一 API、無模型管理功能、需自行處理 prompt template | 最低層級的控制，效能最佳，但操作門檻最高 |
| **LocalAI** | 提供 OpenAI API 相容的本地 LLM 伺服器，支援多種後端（llama.cpp、transformers 等） | 需 Docker 或手動安裝、需自行下載模型 | 依賴 Docker 生態、模型管理仍需手動操作、後端切換配置複雜 | 與 OpenAI API 完全相容，適合已使用 OpenAI SDK 的專案遷移 |
| **vLLM** | 高效能 LLM 推理引擎，使用 PagedAttention 最佳化記憶體管理 | 需 Python 環境、CUDA GPU、模型需為 HuggingFace 格式 | 僅支援 NVIDIA GPU、不支援 GGUF 格式、對非 NVIDIA 硬體不友善 | 生產環境最高吞吐量，適合大量並發請求場景 |
| **GPT4All** | 桌面應用程式形式的本地 LLM 執行器，強調一鍵安裝與圖形介面 | 需下載桌面應用程式、模型選擇受限於其生態系 | 無 REST API（早期版本）、不適合程式化整合、模型支援較少 | 非技術使用者最友善的選擇，但擴充性與彈性最低 |

### 各方案切入點差異

- **Ollama**：在「易用性」與「彈性」之間取得平衡。提供 CLI + REST API + SDK 三種使用方式，同時支援多種 GPU 後端與模型自訂。定位是「開發者友善的本地 LLM 平台」。
- **llama.cpp**：純粹的推理引擎，不做模型管理或 API 抽象。適合需要最大控制權且願意手動處理所有細節的使用者。
- **LocalAI**：以 OpenAI API 相容性為核心賣點，適合從 OpenAI 遷移到本地部署的場景。但模型管理與後端配置比 Ollama 複雜。
- **vLLM**：以生產環境效能為目標，使用 PagedAttention 技術實現高吞吐量。但硬體限制嚴格（僅 NVIDIA GPU），且不支援 GGUF 格式。
- **GPT4All**：以終端使用者體驗為核心，提供圖形介面與一鍵安裝。但程式化整合能力最弱。
