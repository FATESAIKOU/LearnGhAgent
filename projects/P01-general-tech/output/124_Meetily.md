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
