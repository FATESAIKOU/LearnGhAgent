# Meetily — Privacy-First AI 會議助理

> 調研標的：github.com/Zackriya-Solutions/meetily
> 調研日期：2026-07-11

---

## 1. 這個技術解決什麼問題？

**Meetily 解決的是「AI 會議助理在隱私與可用性之間的取捨」問題。**

具體來說，現有的 AI 會議助理（Otter.ai、Fireflies.ai、Fathom、Tactiq 等）都依賴雲端處理：音訊上傳到第三方伺服器進行語音轉文字（STT）與 LLM 摘要。這帶來三個層面的問題：

- **隱私洩漏風險**：會議內容（可能含商業機密、客戶資料、薪資討論）必須離開本地設備，上傳到外部 API。使用者無法控制資料的去向與儲存時長。
- **持續訂閱成本**：多數 SaaS 會議助理按使用者/月收費（$10–$30/user/mo），對團隊而言是持續的營運支出。
- **離線不可用**：依賴雲端 API 意味著網路中斷時完全無法使用，也無法在內網/隔離環境部署。

Meetily 的目標是：**在本地設備上完成從音訊擷取 → 語音轉文字 → LLM 摘要的完整 pipeline，不依賴任何外部服務**，同時保持與雲端方案相當的轉錄品質與摘要能力。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的原因

1. **現有方案全雲端架構**：Otter.ai、Fireflies.ai 等競品均採用「客戶端錄音 → 上傳雲端 → 雲端 STT + LLM → 回傳結果」的架構，資料必然經過第三方伺服器。
2. **本地 LLM 的品質與效能瓶頸**：直到 2024 年，本地運行的語音模型（Whisper）與 LLM（Llama、Mistral）才達到可接受的準確度與速度，且需要 GPU 加速才能即時運轉。
3. **跨平台桌面整合的複雜度**：要從系統音訊擷取會議聲音（而非麥克風），需要作業系統層級的權限與 API，不同平台（Windows/macOS/Linux）的實作方式完全不同。

### 通用技術背景

1. **語音轉文字的技術演進**：OpenAI Whisper（2022）與 Suno Parakeet（2024）將 STT 的準確度提升到實用水準，且 Whisper 有開源模型可本地部署。在此之前，本地 STT 方案（如 PocketSphinx、Kaldi）的準確度遠低於雲端 API（Google Speech-to-Text、Azure Speech）。
2. **本地 LLM 的成熟**：llama.cpp（2023）與 Ollama（2023）讓消費級硬體上運行 LLM 成為可能。2024 年的模型（Llama 3、Mistral、Qwen）在摘要任務上已可與 GPT-3.5 匹敵。
3. **Tauri 的桌面應用框架**：Tauri v2（2024）提供 Rust 核心 + Web 前端的桌面應用架構，體積小（~5MB vs Electron ~150MB）、效能高、可直接呼叫系統 API（音訊擷取、GPU 偵測）。
4. **系統音訊擷取的平台差異**：macOS 需要安裝虛擬音訊驅動（BlackHole），Windows 使用 WASAPI loopback，Linux 使用 PulseAudio/ PipeWire 監聽。每個平台的實作與使用者體驗都不同。

---

## 3. 這個技術是如何解決該問題的？

Meetily 採用**三層架構**（Tauri Rust 核心層 / Python FastAPI 後端層 / Next.js 前端層）來實現全本地 AI 會議助理：

### 3.1 整體架構

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js 前端 (Tauri WebView)              │
│  shadcn/ui · Radix UI · BlockNote · Tailwind               │
│  configService · indexedDBService · recordingService        │
│  storageService · transcriptService · updateService         │
├─────────────────────────────────────────────────────────────┤
│                    Tauri Rust 核心層                         │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Audio    │ │ Whisper      │ │ Parakeet │ │ Summary  │  │
│  │ Engine   │ │ Engine       │ │ Engine   │ │ Engine   │  │
│  │ (cpal)   │ │ (whisper-rs) │ │ (ort)    │ │          │  │
│  └──────────┘ └──────────────┘ └──────────┘ └──────────┘  │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Ollama   │ │ Anthropic    │ │ Groq     │ │ OpenAI   │  │
│  │ Client   │ │ Client       │ │ Client   │ │ Client   │  │
│  └──────────┘ └──────────────┘ └──────────┘ └──────────┘  │
│  ┌──────────┐ ┌──────────────┐                              │
│  │ Database │ │ API Router   │                              │
│  │ (SQLite) │ │ (Tauri cmd)  │                              │
│  └──────────┘ └──────────────┘                              │
├─────────────────────────────────────────────────────────────┤
│                    Python FastAPI 後端 (選用)                │
│  pydantic-ai · ollama · aiosqlite                          │
│  REST API: 會議 CRUD · 轉錄管理 · 摘要生成 · 模型設定       │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心機制

#### 機制一：雙模式 STT 引擎

Meetily 支援兩種語音轉文字引擎，使用者可依硬體與需求切換：

| 引擎 | 模型格式 | 後端 | GPU 加速 | 優點 | 缺點 |
|------|---------|------|---------|------|------|
| **Whisper** (whisper-rs) | GGML/GGUF | whisper.cpp | Metal/CUDA/Vulkan/CoreML/hipBLAS/OpenBLAS | 開源生態最成熟、多語言支援佳 | 體積大（~1.5GB base model） |
| **Parakeet** (ort) | ONNX | ONNX Runtime | DirectML/CUDA | 體積小（~300MB）、速度快 | 僅支援英文、生態較封閉 |

Rust 層的 `whisper_engine` 與 `parakeet_engine` 模組各自封裝模型載入、推理、串流處理邏輯，透過 Tauri command 暴露給前端。

#### 機制二：多 Provider 摘要引擎

摘要生成支援多種 LLM provider，使用者可選：

```
┌─────────────────────────────────────────────────────┐
│                    Summary Engine                     │
├──────────┬──────────┬──────────┬──────────┬─────────┤
│ Ollama   │ Anthropic │ Groq     │ OpenAI   │ OpenRouter│
│ (本地)   │ (雲端)   │ (雲端)   │ (雲端)   │ (雲端)   │
│ llama.cpp│ Claude    │ Llama    │ GPT-4    │ 多模型   │
│ 免費     │ 付費API  │ 免費額度 │ 付費API  │ 付費API  │
└──────────┴──────────┴──────────┴──────────┴─────────┘
```

Python 後端的 `transcript_processor.py` 使用 `pydantic-ai` 框架定義結構化輸出 schema，確保摘要格式一致：

```python
# 虛擬碼：pydantic-ai 結構化摘要
class MeetingSummary(BaseModel):
    title: str
    date: str
    attendees: list[str]
    key_points: list[str]
    action_items: list[dict]  # {owner, task, deadline}
    decisions: list[str]
    next_steps: list[str]
```

#### 機制三：音訊擷取管道

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 系統音訊     │────▶│ Audio Engine  │────▶│ 緩衝區       │
│ (cpal)       │     │ (Rust)       │     │ (Ring Buffer) │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                    ┌──────────────────────────────┘
                    ▼
          ┌──────────────────┐
          │ STT Engine       │
          │ (Whisper/Parakeet)│
          └──────────────────┘
```

- 使用 `cpal`（Cross-Platform Audio Library）擷取系統音訊輸出
- macOS 需搭配 BlackHole 虛擬音訊裝置
- 音訊以 ring buffer 暫存，避免記憶體爆炸
- 支援即時轉錄（streaming）與會後批次轉錄

#### 機制四：全本地資料儲存

```
┌─────────────────────────────────────┐
│         Tauri Rust 核心              │
│  ┌─────────────────────────────┐   │
│  │  SQLite Database             │   │
│  │  ├── meetings (會議資料)     │   │
│  │  ├── transcripts (轉錄內容)  │   │
│  │  └── settings (設定)         │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │  Audio Files (WAV/MP3)     │   │
│  │  (本地檔案系統)             │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

所有資料儲存在本地 SQLite 資料庫與檔案系統，不經由任何外部服務。前端另有 IndexedDB 作為快取層。

#### 機制五：GPU 加速支援

透過 Cargo feature flags 選擇性啟用 GPU 後端：

```toml
# Cargo.toml feature flags
[features]
default = []
cuda = ["whisper-rs/cuda"]        # NVIDIA GPU
metal = ["whisper-rs/metal"]      # Apple Silicon
vulkan = ["whisper-rs/vulkan"]    # 跨平台 GPU
coreml = ["whisper-rs/coreml"]    # Apple CoreML
hipblas = ["whisper-rs/hipblas"]  # AMD ROCm
openblas = ["whisper-rs/openblas"]# CPU OpenBLAS
```

### 3.3 資料流（完整會議處理流程）

```
Step 1: 使用者點擊「開始錄音」
        │
        ▼
Step 2: Audio Engine 擷取系統音訊 (cpal)
        │
        ▼
Step 3: 音訊送入 STT Engine (Whisper/Parakeet)
        │ 即時轉錄文字顯示於前端
        ▼
Step 4: 會議結束 → 完整轉錄文字存入 SQLite
        │
        ▼
Step 5: 轉錄文字送入 Summary Engine
        │ 透過 Ollama/Anthropic/Groq/OpenAI 產生結構化摘要
        ▼
Step 6: 摘要存入 SQLite，前端顯示結果
        │
        ▼
Step 7: 使用者可編輯、匯出、搜尋歷史會議記錄
```

### 3.4 前端功能模組

| 功能 | 實作方式 | 說明 |
|------|---------|------|
| 會議列表 | Next.js + shadcn/ui Table | 顯示歷史會議、搜尋、排序 |
| 即時轉錄 | WebSocket + Tauri event | 會議進行中即時顯示轉錄文字 |
| 摘要檢視 | BlockNote 富文字編輯器 | 可編輯的結構化摘要 |
| 錄音控制 | Tauri command | 開始/暫停/停止錄音 |
| 模型管理 | configService | 下載/切換 Whisper/Parakeet 模型 |
| 設定頁面 | shadcn/ui Form | LLM provider 設定、快捷鍵、音訊裝置 |
| 匯出功能 | Tauri dialog | 匯出為 Markdown/TXT/JSON |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表：替代方案對照

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|---------|-------------|---------------|-----------------|
| **Otter.ai** | 雲端 STT + LLM 會議助理，自動加入日曆會議 | 有 Otter.ai 帳號、瀏覽器擴充功能或 Zoom/Teams 整合 | 所有會議音訊上傳雲端處理、$16.99/user/mo 起、離線不可用 | 高品質轉錄與摘要，但無資料控制權 |
| **Fireflies.ai** | 雲端會議機器人，支援 20+ 會議平台 | 有 Fireflies.ai 帳號、會議平台 bot 整合 | 音訊經第三方伺服器、$10/user/mo 起、bot 需加入會議 | 跨平台整合最廣，但隱私與成本問題相同 |
| **Whisper 手動 pipeline** | 自行撰寫 script：ffmpeg 錄音 → whisper.cpp 轉錄 → ollama 摘要 | 熟悉 CLI、Python/Rust、需手動管理模型與 pipeline | 無 GUI、無即時轉錄、需自行處理錯誤與狀態管理 | 完全免費且隱私，但使用門檻高、無整合體驗 |
| **Mac Whisper** | macOS 原生 Whisper 轉錄工具 | 僅 macOS、需購買 Pro 版（$29） | 僅轉錄無摘要、單一平台、非開源 | 簡單易用的 Whisper 轉錄，但功能單一 |
| **Vocol.ai** | 企業級 AI 會議平台，強調準確度與分析 | 企業採購、需 API 整合 | 封閉生態、價格不透明、資料上雲 | 高準確度與分析深度，但成本與隱私問題最重 |

### 切入點差異分析

| 切入點 | Meetily | Otter.ai | Fireflies.ai | 手動 pipeline | Mac Whisper |
|--------|---------|----------|-------------|--------------|-------------|
| 全本地處理 | ✅ 是 | ❌ 雲端 | ❌ 雲端 | ✅ 是 | ✅ 是 |
| 即時轉錄 | ✅ 是 | ✅ 是 | ✅ 是 | ❌ 批次 | ✅ 是 |
| LLM 摘要 | ✅ 多 provider | ✅ 內建 | ✅ 內建 | ✅ 自建 | ❌ 無 |
| GPU 加速 | ✅ 多後端 | N/A (雲端) | N/A (雲端) | ✅ 手動設定 | ✅ Metal |
| 跨平台 | ✅ Win/Mac/Linux | ✅ Web | ✅ Web | ✅ 跨平台 | ❌ 僅 macOS |
| 開源 | ✅ MIT | ❌ 專有 | ❌ 專有 | ✅ 開源 | ❌ 專有 |
| GUI | ✅ Tauri | ✅ Web | ✅ Web | ❌ CLI | ✅ Native |
| 安裝難度 | 中（需編譯） | 低 | 低 | 高 | 低 |
| 隱私等級 | ★★★★★ | ★★☆☆☆ | ★★☆☆☆ | ★★★★★ | ★★★★★ |

### 結論

Meetily 的核心差異在於：它不是一個「更好的雲端會議助理」，而是一個**將完整 AI 會議處理 pipeline 搬遷到本地的開源桌面應用**。與雲端方案相比，它在隱私與成本上具有絕對優勢，但犧牲了安裝便利性與跨裝置同步。與手動 pipeline 方案相比，它提供了整合的 GUI 與即時轉錄體驗，大幅降低了使用門檻。其多 STT 引擎、多 LLM provider、多 GPU 後端的設計，使其在靈活性上優於任何單一方案。

---

## 5. User Q&A

### Q1：在 Ubuntu 上配置 Meetily 的逐步指令為何？我想用 RTX 2060s 或 Ollama Cloud（deepseek-v4-flash）做 TTS 跟摘要

**A**：

**重要澄清：Meetily 無 TTS（文字轉語音）功能。** Meetily 提供的是 STT（語音轉文字，Speech-to-Text）與 LLM 摘要。使用者提到的「TTS」應為「STT」之誤。以下步驟涵蓋 STT + 摘要的完整配置。

---

#### 方案 A：RTX 2060s 本地 GPU 方案

RTX 2060s 採用 Turing 架構，CUDA compute capability = 7.5。`CMAKE_CUDA_ARCHITECTURES` 需設為 `75`。

| 步驟 | 指令 | 說明 |
|------|------|------|
| 1. 安裝系統相依套件 | `sudo apt update && sudo apt install -y build-essential cmake git libwebkit2gtk-4.1-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev libpulse-dev` | Tauri 與 cpal（PulseAudio）所需 |
| 2. 安裝 NVIDIA 驅動 | `sudo apt install -y nvidia-driver-535`（或最新穩定版） | 確認 `nvidia-smi` 輸出正常 |
| 3. 安裝 CUDA toolkit | `sudo apt install -y nvidia-cuda-toolkit` | 提供 nvcc 編譯器與 CUDA runtime |
| 4. 安裝 Rust | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh` | 選擇 default 安裝 |
| 5. 安裝 Node.js + pnpm | `sudo apt install -y nodejs npm && sudo npm install -g pnpm` | 前端建置所需 |
| 6. Clone 專案 | `git clone https://github.com/Zackriya-Solutions/meetily.git && cd meetily` | |
| 7. 設定 CUDA 架構 | `export CMAKE_CUDA_ARCHITECTURES=75` | RTX 2060s 專用；可寫入 `~/.bashrc` 持久化 |
| 8. 以 CUDA feature 建置 | `cargo tauri build --features cuda` | 啟用 whisper-rs 的 CUDA 後端 |
| 9. 下載 Whisper 模型 | 啟動 Meetily → 設定頁面 → 下載 GGML 格式模型（建議 `base` 或 `small`） | 首次啟動時自動引導 |
| 10. 設定本地 LLM（摘要用） | 安裝 Ollama：`curl -fsSL https://ollama.com/install.sh \| sh` → `ollama pull llama3.2`（或 `mistral`、`qwen2.5`） | Meetily 設定中選擇 Ollama provider，端點 `http://localhost:11434` |
| 11. 啟動 Meetily | 執行產生的 binary（`src-tauri/target/release/meetily`）或透過 Tauri dev 模式 | |

**GPU 自動偵測**：Meetily 的 `scripts/auto-detect-gpu.js` 在 `cargo tauri build` 時會依序偵測 CUDA > ROCm > Vulkan > OpenBLAS > CPU。若步驟 8 使用 `--features cuda`，則強制啟用 CUDA 路徑。

**Vulkan 備援**：若 CUDA toolkit 安裝失敗，可改用 Vulkan 後端：`cargo tauri build --features vulkan`。需額外安裝 `sudo apt install -y vulkan-tools libvulkan-dev`。RTX 2060s 支援 Vulkan，但推理速度約為 CUDA 的 70–80%。

---

#### 方案 B：Ollama Cloud（deepseek-v4-flash）方案

**前提**：Meetily 的 Ollama 整合僅支援**本地 Ollama 伺服器**（localhost:11434）。Ollama Cloud 不提供與本地 Ollama 相容的 API 端點。替代方案是使用 Meetily 的 **Custom OpenAI** provider，將 Ollama Cloud 設定為 OpenAI 相容端點。

| 步驟 | 指令 / 操作 | 說明 |
|------|------------|------|
| 1–6 | 同方案 A 步驟 1–6 | 系統相依性與 clone 專案 |
| 7. 以 CPU 或 Vulkan 建置 | `cargo tauri build --features vulkan`（或 `--features openblas` 純 CPU） | 摘要用 LLM 在雲端，本地僅需 STT 推理 |
| 8. 取得 Ollama Cloud API key | 至 [cloud.ollama.com](https://cloud.ollama.com) 註冊並取得 API key | deepseek-v4-flash 模型需確認在 Ollama Cloud 上可用 |
| 9. 設定 Custom OpenAI provider | Meetily 設定 → LLM Provider → Custom OpenAI → 填入：API URL = `https://api.ollama.com/v1`（或 Ollama Cloud 提供的端點）、API Key = 步驟 8 取得的 key、Model = `deepseek-v4-flash` | Meetily 的 `llm_client.rs` 中 CustomOpenAI 使用與 OpenAI 相容的 chat completions API |
| 10. 下載 Whisper 模型 | 同方案 A 步驟 9 | STT 仍在本地執行 |
| 11. 啟動 Meetily | 同方案 A 步驟 11 | |

**注意**：Ollama Cloud 的 API 端點格式與定價可能隨時間變動。若 Custom OpenAI 連線失敗，請確認 Ollama Cloud 的 API 文件是否與 OpenAI `/v1/chat/completions` 格式相容。

---

#### 兩種方案對照

| 面向 | 方案 A：RTX 2060s 本地 | 方案 B：Ollama Cloud |
|------|----------------------|-------------------|
| STT 執行位置 | 本地 GPU（CUDA） | 本地 GPU（CUDA/Vulkan） |
| 摘要執行位置 | 本地 Ollama（CPU/GPU） | Ollama Cloud 伺服器 |
| 網路需求 | 僅模型下載需網路 | 每次摘要需網路 |
| 隱私 | ★★★★★（全本地） | ★★★☆☆（摘要上雲） |
| 延遲 | STT 即時，摘要 3–10s | STT 即時，摘要取決於網路 |
| 成本 | 電費 + GPU 折舊 | Ollama Cloud 訂閱費 |
| 建置難度 | 中（需 CUDA toolkit） | 低（無需 CUDA） |

---

### Q2：Meetily 能不能在 Google Meet 會議中幫我把會議內容錄起來？

**A**：可以，但有前提條件。

Meetily 使用 `cpal`（Cross-Platform Audio Library）擷取系統音訊輸出。在 Linux 上，cpal 透過 PulseAudio 或 PipeWire 的 `default_output_device` 取得系統音訊串流。

```
Google Meet (瀏覽器)
      │
      ▼ 音訊輸出
 PulseAudio/PipeWire (系統音訊混音器)
      │
      ▼ loopback 監聽
 cpal default_output_device (Meetily Audio Engine)
      │
      ▼
 STT Engine → 轉錄文字 → 摘要
```

**運作條件**：

| 條件 | 說明 | 驗證方式 |
|------|------|---------|
| PulseAudio 或 PipeWire 已安裝 | Ubuntu 預設安裝 PulseAudio；22.04+ 可選 PipeWire | `pactl info` 或 `pactl list sinks` |
| 瀏覽器音訊輸出至系統預設音訊裝置 | Google Meet 音訊需從系統喇叭/耳機輸出 | 確認 Google Meet 中可正常聽到聲音 |
| Meetily 選擇正確的音訊輸入裝置 | Meetily 設定中選擇「系統音訊輸出」作為音訊來源 | 設定頁面 → Audio Device → 選擇監聽裝置 |
| 無 DRM 保護限制 | Google Meet 未對音訊串流施加 DRM 保護 | 一般 Google Meet 會議無 DRM |

**限制**：

- Meetily 無法「自動加入」Google Meet 會議。使用者需手動開啟 Meetily 錄音，然後在瀏覽器中加入 Google Meet 會議。
- Meetily 無瀏覽器擴充功能或 Google Calendar 整合。它僅是獨立的桌面錄音應用，需使用者手動同步操作。
- 若使用耳機麥克風，Meetily 預設擷取系統音訊輸出（即會議中其他人的聲音），使用者的發言需透過麥克風輸入。Meetily 可同時擷取麥克風與系統音訊，但需在設定中正確配置音訊來源。

**結論**：Meetily 可錄製 Google Meet 會議內容（透過 PulseAudio/PipeWire loopback），但需使用者手動啟動錄音，且無自動加入或排程功能。
