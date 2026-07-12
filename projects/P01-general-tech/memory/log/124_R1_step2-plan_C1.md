# 124_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認技術標的為 Meetily（Zackriya-Solutions/meetily），一個隱私優先的 AI 會議助理。本 sub-step C1 為 Step 2 的第一個調研動作：取得 repo metadata、README、關鍵子文件、目錄結構，並補查背景脈絡。

## 執行的動作與結果

| 動作 | 目的 | 預期達成效果 | 實際的結果 |
|------|------|-------------|-----------|
| `gh repo view --json` | 取得 repo metadata | 名稱、描述、星數、語言、授權等 | 23k stars, 2.4k forks, Rust 為主, MIT 授權, 2024-12-26 建立 |
| `gh api repos/.../readme` | 擷取 README.md | 完整專案說明 | 取得完整 README：定位、功能、安裝、架構、PRO 版本對比 |
| `gh api repos/.../contents` | 取得根目錄結構 | 了解專案組織 | backend/ (Python FastAPI + whisper.cpp), frontend/ (Next.js + Tauri), docs/, llama-helper/, scripts/ |
| `gh api repos/.../contents/docs` | 列出 docs 目錄 | 了解有哪些文件 | architecture.md, BUILDING.md, GPU_ACCELERATION.md, building_in_linux.md 等 |
| `gh api repos/.../contents/docs/architecture.md` | 讀取架構文件 | 了解系統架構 | Tauri + Rust 後端 (Audio/Transcription/Summary Engine + SQLite) + Next.js 前端 |
| `gh api repos/.../contents/Cargo.toml` | 讀取 workspace Cargo.toml | 了解 Rust 依賴與 workspace 結構 | workspace 含 frontend/src-tauri 與 llama-helper 兩個 member |
| `gh api repos/.../contents/frontend/src-tauri/Cargo.toml` | 讀取 Tauri Cargo.toml | 了解 Tauri 端依賴與 GPU 加速 feature flags | cpal 音訊、whisper-rs 多後端 (metal/cuda/vulkan/coreml/hipblas/openblas) |
| `gh api repos/.../contents/frontend/package.json` | 讀取前端 package.json | 了解前端技術棧 | Next.js, shadcn/ui, Radix UI, BlockNote, Tailwind, @tauri-apps/api |
| `gh api repos/.../contents/backend/requirements.txt` | 讀取 Python 後端依賴 | 了解 Python 端技術棧 | FastAPI, uvicorn, pydantic-ai, ollama, aiosqlite |
| `gh api repos/.../contents/backend/app/main.py` | 讀取 FastAPI 主程式 | 了解 API 端點設計 | 會議 CRUD、轉錄儲存、模型設定、摘要生成等 REST API |
| `gh api repos/.../contents/backend/app/transcript_processor.py` | 讀取轉錄處理器 | 了解摘要生成邏輯 | 使用 pydantic-ai 搭配 Ollama/Anthropic/Groq/OpenAI 產生結構化摘要 |
| `gh api repos/.../contents/backend/app/db.py` | 讀取資料庫層 | 了解資料模型 | SQLite, meetings/transcripts 表, schema validator |
| `gh api repos/.../contents/frontend/src-tauri/src` | 列出 Rust 源碼目錄 | 了解 Rust 模組劃分 | audio, audio_v2, whisper_engine, parakeet_engine, ollama, anthropic, groq, openai, openrouter, summary, database, api 等 |
| `gh api repos/.../contents/frontend/src/services` | 列出前端服務層 | 了解前端架構 | configService, indexedDBService, recordingService, storageService, transcriptService, updateService |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 驗證結果 |
|---------|-------------|---------|
| Repo metadata 完整性 | 確認所有 JSON field 已取得 | 完整：23k stars, 2.4k forks, Rust primary, MIT, 12 languages |
| 架構理解 | 比對 README + architecture.md + 目錄結構 | 三層架構：Tauri Rust 核心 (音訊/轉錄/摘要/資料庫) + Python FastAPI 後端 + Next.js 前端 |
| 技術棧完整性 | 從 Cargo.toml + package.json + requirements.txt 交叉比對 | Rust (whisper-rs, cpal, tauri) + Python (FastAPI, pydantic-ai, ollama) + TypeScript (Next.js, shadcn/ui) |
| 背景脈絡 | 確認專案定位與競品脈絡 | 隱私優先、全本地處理、支援多種 LLM provider、GPU 加速多後端 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---------|---------|---------|---------|
| 調研深度 | 僅 README / 深入程式碼 | 深入程式碼（讀取 main.py, transcript_processor.py, db.py, Cargo.toml） | 需理解實際架構與資料流才能產出高品質報告 |
| 背景補查 | 不補查 / 查 Whisper/Parakeet/Ollama 技術背景 | 暫不補查，留待 C2 處理 | C1 專注 repo 內部資訊，外部技術背景在後續 sub-step 處理 |
| 文件範圍 | 僅 architecture.md / 含 BUILDING.md 等 | 僅 architecture.md | architecture.md 已涵蓋高階架構，其餘為建置細節，非分析核心 |
