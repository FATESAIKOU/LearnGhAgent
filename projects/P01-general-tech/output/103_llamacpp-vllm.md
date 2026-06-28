# llama.cpp 與 vLLM 技術分析報告

> 調研日期：2026-06-28 | 基於 GitHub repo metadata、README、ggml 底層庫、PagedAttention 論文

---

## 1. 這個技術解決什麼問題？

### llama.cpp

llama.cpp 解決的是 **在消費級硬體（個人電腦、筆電、手機）上執行大型語言模型（LLM）推理的問題**。具體子問題：

| 子問題 | 具體表現 |
|---|---|
| **GPU VRAM 不足** | 70B 參數模型需要 140GB+ VRAM（FP16），消費級 GPU（RTX 4090 24GB）無法載入 |
| **依賴複雜的深度學習框架** | PyTorch + CUDA + NCCL 等依賴鏈安裝複雜，不適合輕量部署 |
| **邊緣裝置推理** | 手機、Raspberry Pi 等裝置無 NVIDIA GPU，無法執行主流 LLM |
| **量化支援碎片化** | 各框架量化格式不統一（GPTQ、AWQ、GGUF），缺乏統一的高效實作 |
| **隱私需求** | 雲端 API 推理需傳送資料至第三方伺服器，無法滿足本地資料隔離需求 |

### vLLM

vLLM 解決的是 **在生產環境中高吞吐、低延遲地服務 LLM 推理的問題**。具體子問題：

| 子問題 | 具體表現 |
|---|---|
| **KV cache 記憶體碎片化** | 傳統推理框架中 KV cache 預先分配最大長度，浪費 60-80% 記憶體 |
| **請求排程效率低** | 無連續批處理（continuous batching）時，GPU 利用率低，空轉時間長 |
| **高併發場景吞吐不足** | 單一 GPU 一次只能處理一個請求，無法充分利用 GPU 算力 |
| **API 相容性** | 缺乏與 OpenAI API 相容的標準化服務介面，整合成本高 |
| **多 GPU 分散式推理** | 模型並行（tensor parallelism）需手動配置，缺乏自動化支援 |

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

**llama.cpp 背景：**

- **LLM 參數規模爆炸**：從 GPT-3（175B）到 Llama 3（405B），模型參數量持續增長，FP16 推理需要數百 GB VRAM
- **ggml 張量庫**：llama.cpp 底層使用 ggml（Gerganov's ML tensor library），一個純 C 實作的張量運算庫，無外部依賴，支援 CPU 與 GPU 後端
- **GGUF 格式**：llama.cpp 定義的模型儲存格式，統一量化參數、tokenizer、模型結構於單一檔案，取代舊版 GGML 格式
- **量化技術成熟**：從 4-bit 到 2-bit 量化（Q2_K 到 Q8_0），使模型在精度損失可控下大幅降低記憶體需求

**vLLM 背景：**

- **KV cache 記憶體管理問題**：自迴歸生成中，每個 token 的 KV 向量需快取，但傳統實作為每個請求預先分配最大長度（如 2048 tokens），實際使用遠低於此
- **作業系統虛擬記憶體啟發**：PagedAttention 論文（Kwon et al., 2023）將 OS 分頁概念引入 KV cache 管理，將 KV cache 分割為固定大小的 page block
- **Continuous batching**：Orca 論文（2022）提出 iteration-level batching，在每個 decode step 動態增減批次中的請求，取代傳統的 request-level batching

### 通用技術背景（文章中未明確提及但為必要脈絡）

- **Transformer 自迴歸生成特性**：每個新 token 的生成需計算所有先前 token 的 attention，KV cache 是避免重複計算的必要機制，但記憶體消耗隨序列長度線性增長
- **GPU 記憶體瓶頸**：NVIDIA GPU VRAM 增長速度（每代約 2x）遠低於模型參數增長速度（每年約 10x），量化與記憶體管理成為必要
- **邊緣 AI 趨勢**：Apple Silicon（M 系列晶片）的統一記憶體架構使大模型在個人電腦上執行成為可能，llama.cpp 是主要受益者
- **LLM 服務化需求**：從單一模型推理到多模型、多用戶、多租戶的服務架構，需要專用的推理引擎而非訓練框架

---

## 3. 這個技術是如何解決該問題的？

### 3.1 llama.cpp 核心機制

```
llama.cpp 架構
┌─────────────────────────────────────────────────────┐
│                    llama.cpp                         │
│  ┌──────────────────────────────────────────────┐   │
│  │              推理引擎 (C/C++)                  │   │
│  │  • 模型載入與解析 (GGUF format)               │   │
│  │  • 前向傳播 (forward pass)                    │   │
│  │  • 採樣策略 (top-k, top-p, temperature)       │   │
│  └──────────────┬───────────────────────────────┘   │
│                  │                                    │
│  ┌──────────────▼───────────────────────────────┐   │
│  │            ggml (張量運算庫)                   │   │
│  │  • 純 C/C++ 實作，無外部依賴                    │   │
│  │  • 支援 CPU (x86_64 SSE/AVX, ARM NEON)        │   │
│  │  • 支援 GPU (CUDA, Metal, Vulkan, WebGPU)     │   │
│  │  • 自動向量化 + 多執行緒                       │   │
│  └──────────────┬───────────────────────────────┘   │
│                  │                                    │
│  ┌──────────────▼───────────────────────────────┐   │
│  │         量化層 (GGUF + k-quants)               │   │
│  │  • Q2_K ~ Q8_0 多級量化                       │   │
│  │  • 重要性加權量化 (importance-based)           │   │
│  │  • 混合精度 (不同層不同量化級別)                │   │
│  └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

**a) 量化機制（k-quants）**

llama.cpp 的量化不是簡單的均勻量化，而是基於重要性加權：

```
量化流程：
原始權重 (FP16) → 分組 (group = 32 weights)
                 → 計算 scale 與 offset
                 → 根據權重重要性分配 bits
                 → 儲存為 GGUF 格式

量化級別對照：
Q2_K:  2.56 bpw (bits per weight) → 70B 模型約 22GB
Q3_K:  3.50 bpw                   → 70B 模型約 30GB
Q4_K:  4.50 bpw                   → 70B 模型約 39GB
Q5_K:  5.50 bpw                   → 70B 模型約 48GB
Q6_K:  6.50 bpw                   → 70B 模型約 56GB
Q8_0:  8.50 bpw                   → 70B 模型約 73GB
FP16: 16.00 bpw                   → 70B 模型約 140GB
```

**b) 多硬體後端**

| 後端 | 支援硬體 | 特點 |
|---|---|---|
| CPU | x86_64 (SSE/AVX2/AVX512), ARM (NEON) | 無 GPU 也可執行，速度較慢 |
| CUDA | NVIDIA GPU | 完整 GPU 加速 |
| Metal | Apple Silicon (M1/M2/M3/M4) | 統一記憶體架構，可載入大模型 |
| Vulkan | 跨平台 GPU | AMD/Intel GPU 支援 |
| WebGPU | 瀏覽器 | WebAssembly 版本，瀏覽器內執行 |
| SYCL | Intel GPU | Intel 生態支援 |

**c) GGUF 格式**

```
GGUF 檔案結構：
┌─────────────────────┐
│ Header              │ → magic number, version, tensor count
├─────────────────────┤
│ Metadata KV pairs   │ → tokenizer, model architecture, hyperparams
├─────────────────────┤
│ Tensor info         │ → name, type (quantized), offset, size
├─────────────────────┤
│ Tensor data         │ → 量化後的權重資料 (mmap-friendly)
└─────────────────────┘
```

GGUF 設計為 memory-mappable，載入時無需解析整個檔案，可直接 mmap 到記憶體。

### 3.2 vLLM 核心機制

```
vLLM 架構
┌─────────────────────────────────────────────────────┐
│                    vLLM                              │
│  ┌──────────────────────────────────────────────┐   │
│  │          LLM Engine (Python/PyTorch)           │   │
│  │  • 模型載入 (HuggingFace Transformers)        │   │
│  │  • 前向傳播 (CUDA kernels)                    │   │
│  │  • 採樣與輸出處理                             │   │
│  └──────────────┬───────────────────────────────┘   │
│                  │                                    │
│  ┌──────────────▼───────────────────────────────┐   │
│  │        PagedAttention (核心創新)               │   │
│  │  • KV cache 分頁管理                          │   │
│  │  • 非連續記憶體配置                           │   │
│  │  • 記憶體共享 (copy-on-write)                 │   │
│  └──────────────┬───────────────────────────────┘   │
│                  │                                    │
│  ┌──────────────▼───────────────────────────────┐   │
│  │     Scheduler (Continuous Batching)           │   │
│  │  • iteration-level scheduling                 │   │
│  │  • 請求排隊與優先級管理                       │   │
│  │  • 記憶體預算追蹤                             │   │
│  └──────────────┬───────────────────────────────┘   │
│                  │                                    │
│  ┌──────────────▼───────────────────────────────┐   │
│  │     API Server (OpenAI 相容)                   │   │
│  │  • /v1/chat/completions                       │   │
│  │  • /v1/completions                            │   │
│  │  • /v1/embeddings                             │   │
│  │  • 串流輸出 (streaming)                       │   │
│  └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

**a) PagedAttention 核心機制**

PagedAttention 將 KV cache 分割為固定大小的 page block（通常 16 或 32 tokens），類似 OS 的虛擬記憶體分頁：

```
傳統 KV cache 配置（浪費）：
Request A: [KV for token 1 | KV for token 2 | ... | KV for token N | 未使用空間 ]
                                                                   └── 預先分配但未使用 ──┘

PagedAttention KV cache 配置：
Request A: [Page 0] → [Page 1] → [Page 2] → ... (動態增長)
            └── 16 tokens ──┘  └── 16 tokens ──┘

Page Table (類似 OS page table):
┌──────────┬──────────┐
│ Logical  │ Physical │
│ Page ID  │ Page ID  │
├──────────┼──────────┤
│    0     │   42     │
│    1     │   87     │
│    2     │   13     │
│    3     │   55     │
└──────────┴──────────┘
```

PagedAttention 的三個關鍵效益：

| 效益 | 機制 | 量化效果 |
|---|---|---|
| **消除內部碎片** | 僅分配實際使用的 page，不預先分配最大長度 | 記憶體使用減少 60-80% |
| **非連續記憶體** | 物理 page 可分散在記憶體各處，透過 page table 映射 | 消除記憶體壓縮（defragmentation）需求 |
| **記憶體共享** | 多個請求共享相同 prefix 的 KV cache page（copy-on-write） | 共享 prefix 場景（如 system prompt）記憶體節省 50-90% |

**b) Continuous Batching**

```
傳統 batching (request-level):
Batch 1: [Req A, Req B, Req C] → 全部完成 → Batch 2: [Req D, Req E, ...]
          ↑ 等待最慢的請求完成後才能開始下一批          ↑

Continuous batching (iteration-level):
Time step 1: [Req A, Req B, Req C] → 全部 decode 一個 token
Time step 2: [Req A, Req B, Req C, Req D] → Req D 新加入
Time step 3: [Req A, Req C, Req D, Req E] → Req B 完成離開，Req E 加入
Time step 4: [Req C, Req D, Req E] → Req A 完成離開
```

Continuous batching 的效果：

| 指標 | 傳統 batching | Continuous batching |
|---|---|---|
| GPU 利用率 | 低（等待批次完成時空轉） | 高（持續有新請求加入） |
| 平均延遲 | 高（新請求需等當前批次完成） | 低（新請求立即加入下一 iteration） |
| 吞吐量 | 基線 | 2-4x 提升（視工作負載） |
| 實作複雜度 | 低 | 高（需 iteration-level scheduler） |

**c) 量化支援**

vLLM 支援多種量化格式，與 llama.cpp 的 GGUF 不同，vLLM 主要使用：

| 量化格式 | 精度 | 特點 | vLLM 支援狀態 |
|---|---|---|---|
| GPTQ | 4-bit | 基於 Hessian 矩陣的最佳化量化 | ✅ 完整支援 |
| AWQ | 4-bit | 啟發式權重重要性分組 | ✅ 完整支援 |
| FP8 | 8-bit | NVIDIA H100 原生支援 | ✅ 完整支援 |
| SqueezeLLM | 3/4-bit | 非均勻量化 | ✅ 支援 |

### 3.3 兩者核心差異對照

| 面向 | llama.cpp | vLLM |
|---|---|---|
| **實作語言** | C/C++（ggml 張量庫） | Python（PyTorch + CUDA kernels） |
| **部署場景** | 單機/邊緣/本機推理 | 伺服器/雲端/API 服務 |
| **核心技術** | 量化（k-quants）+ 多硬體後端 | PagedAttention + Continuous Batching |
| **模型格式** | GGUF（自訂格式） | HuggingFace Transformers（原生） |
| **GPU 需求** | 可無 GPU（純 CPU 推理） | 必須 GPU（NVIDIA CUDA 為主） |
| **量化支援** | 2-bit ~ 8-bit（k-quants 系列） | 4-bit/8-bit（GPTQ/AWQ/FP8） |
| **API 服務** | 內建 HTTP server（簡易） | 完整 OpenAI 相容 API server |
| **多 GPU** | 有限支援（主要單 GPU） | 完整支援（tensor/pipeline parallelism） |
| **批次處理** | 無（單請求推理） | Continuous batching（高吞吐） |
| **記憶體管理** | 靜態分配 | PagedAttention 動態管理 |
| **生態整合** | 獨立 binary，無框架依賴 | HuggingFace 生態，可整合 LangChain 等 |
| **典型用戶** | 個人開發者、隱私敏感用戶 | 企業、API 服務提供商 |

### 3.4 使用場景對照

```
使用場景光譜：

個人筆電推理 ─── 邊緣裝置 ─── 自架伺服器 ─── 雲端 API 服務
     │              │             │               │
     ▼              ▼             ▼               ▼
  llama.cpp      llama.cpp    llama.cpp / vLLM    vLLM
  (CPU/GPU)      (ARM/GPU)    (依需求選擇)       (多 GPU)

具體案例：
┌─────────────────────────────────────────────────────────────┐
│ 場景 A：個人筆電上執行 Llama 3 8B                          │
│ → llama.cpp + Q4_K 量化 → 8GB RAM 即可執行                  │
│ → 離線使用，無需網路連線                                    │
├─────────────────────────────────────────────────────────────┤
│ 場景 B：手機上執行小型模型                                  │
│ → llama.cpp (Android/iOS 編譯) + Q2_K 量化                  │
│ → 1-3B 參數模型可在旗艦手機上即時推理                      │
├─────────────────────────────────────────────────────────────┤
│ 場景 C：企業內部 Chatbot API                                │
│ → vLLM + 4x A100 80GB + Continuous Batching                 │
│ → 支援數百個同時連線，延遲 < 200ms                          │
├─────────────────────────────────────────────────────────────┤
│ 場景 D：瀏覽器內執行推理                                    │
│ → llama.cpp WebGPU 後端 + WebAssembly 編譯                  │
│ → 完全在瀏覽器內執行，無伺服器成本                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

#### 針對「LLM 推理執行」的替代方案（與 llama.cpp 同級）

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Ollama** | 基於 llama.cpp 的上層封裝，提供 Docker-like CLI 管理模型下載與執行 | 需安裝 Ollama binary；底層仍依賴 llama.cpp | 抽象層增加少量開銷；不支援自訂量化參數；模型管理依賴 Ollama 生態 | 簡化 llama.cpp 使用流程，一行指令即可下載並執行模型 |
| **LM Studio** | GUI 介面封裝 llama.cpp，提供圖形化模型管理與推理 | 需桌面作業系統（Windows/macOS/Linux） | 無 headless 模式；不適合自動化部署；GUI 消耗額外資源 | 非技術使用者可圖形化操作，無需 CLI |
| **MLC LLM** | 基於 Apache TVM 的編譯最佳化，將 LLM 編譯為各平台原生 binary | 需 TVM 編譯工具鏈；支援平台有限 | 編譯時間長；模型切換需重新編譯；社群較小 | 跨平台最佳化（Apple Silicon、Android、WebGPU），推理速度可能優於 llama.cpp |
| **TensorRT-LLM** | NVIDIA 官方 LLM 推理最佳化框架，使用 TensorRT 編譯與最佳化 | 僅支援 NVIDIA GPU；需 TensorRT 工具鏈 | 僅 NVIDIA 生態；建置流程複雜；模型格式需轉換 | NVIDIA GPU 上推理速度最佳，支援 FP8/INT4/INT8 量化 |

#### 針對「LLM 服務引擎」的替代方案（與 vLLM 同級）

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **TGI (Text Generation Inference)** | HuggingFace 官方推理引擎，支援 continuous batching 與量化 | 需 HuggingFace 生態；主要支援 NVIDIA GPU | 功能迭代較 vLLM 慢；PagedAttention 實作較晚；社群貢獻較少 | 與 HuggingFace 生態無縫整合，一行指令部署 HF 模型 |
| **SGLang** | 以編譯器思維設計的 LLM 服務引擎，引入 RadixAttention 與 structured generation | 需 Python 3.10+；GPU 記憶體需求與 vLLM 相近 | 較新（2024），生態尚未成熟；文件與範例較少 | 特定場景（structured output、多輪對話）吞吐量可超越 vLLM |
| **TensorRT-LLM (server mode)** | NVIDIA Triton Inference Server 整合 TensorRT-LLM 作為 backend | 需 NVIDIA GPU + Triton Server 基礎設施 | 部署複雜度最高；需 NVIDIA 生態全棧 | 企業級部署，支援多模型、多 backend、A/B testing |
| **llama.cpp (server mode)** | llama.cpp 內建 HTTP server，提供簡易 API | 適合低併發場景（< 10 同時請求） | 無 continuous batching；無 PagedAttention；吞吐量遠低於 vLLM | 最簡單的單機 API 部署方案，一行指令啟動 |

### 4.2 各方案切入點差異

```
問題維度                    llama.cpp  Ollama  MLC LLM  TRT-LLM  vLLM  TGI  SGLang
──────────────────────────────────────────────────────────────────────────────────
無 GPU 可推理               ✓         ✓       ✓        ✗        ✗     ✗    ✗
消費級 GPU 推理             ✓         ✓       ✓        △        ✗     ✗    ✗
多 GPU 分散式               ✗         ✗       ✗        ✓        ✓     ✓    ✓
高吞吐 API 服務             ✗         ✗       ✗        ✓        ✓     ✓    ✓
OpenAI 相容 API             △         ✓       ✗        △        ✓     ✓    ✓
多平台支援                  ✓         ✓       ✓        ✗        ✗     ✗    ✗
量化格式多樣性              ✓         ✓       △        △        ✓     △    ✓
生態成熟度                  ✓         ✓       ✗        △        ✓     ✓    ✗
部署簡單度                  ✓         ✓       ✗        ✗        △    △     ✗

✓ = 完整支援  △ = 部分支援  ✗ = 不支援
```

### 4.3 選擇建議

```
你的需求是什麼？
│
├─ 在個人筆電/桌機上執行 LLM？
│   ├─ 要 CLI 操作 → llama.cpp
│   ├─ 要 GUI 操作 → LM Studio
│   └─ 要一鍵管理 → Ollama
│
├─ 在手機/邊緣裝置上執行？
│   └─ llama.cpp (ARM/WebGPU)
│
├─ 在伺服器上提供 API 服務？
│   ├─ 單 GPU、低併發 → llama.cpp server
│   ├─ 多 GPU、高吞吐 → vLLM
│   ├─ HuggingFace 生態 → TGI
│   └─ 企業級部署 → TensorRT-LLM + Triton
│
└─ 追求極致推理速度？
    ├─ NVIDIA GPU → TensorRT-LLM
    └─ 非 NVIDIA → llama.cpp (Vulkan/Metal)
```

---

## 5. User Q&A

（無 — 首次產出，尚無使用者提問）

---

## 6. 附錄：關鍵名詞對照

| 名詞 | 說明 |
|---|---|
| **ggml** | 純 C/C++ 實作的張量運算庫，llama.cpp 的底層引擎 |
| **GGUF** | llama.cpp 的模型儲存格式，取代舊版 GGML，支援 mmap 載入 |
| **k-quants** | llama.cpp 的量化方法，基於重要性加權的分組量化 |
| **PagedAttention** | vLLM 的核心技術，將 KV cache 分頁管理，類似 OS 虛擬記憶體 |
| **Continuous Batching** | iteration-level 的動態批次處理，每個 decode step 可增減請求 |
| **KV cache** | Transformer 自迴歸生成中快取先前 token 的 Key/Value 向量 |
| **Tensor Parallelism** | 將模型層的權重分割到多個 GPU 上，每個 GPU 計算部分 |
| **Pipeline Parallelism** | 將模型層按順序分配到多個 GPU，每個 GPU 計算連續的幾層 |
