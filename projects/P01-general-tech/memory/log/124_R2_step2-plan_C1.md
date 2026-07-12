# 124_R2_step2-plan_C1.md

## 狀況理解

R2 使用者提出兩個實務問題：(1) Ubuntu 本地部署 Meetily 的逐步指令，含 RTX 2060s GPU 與 Ollama Cloud（deepseek-v4-flash）兩種方案，用於 TTS 與摘要；(2) Meetily 能否在 Google Meet 等通訊軟體中錄製會議內容。

C1 為 Step 2 的第一個 sub-step，目標是取得 repo metadata、關鍵文件、架構細節，為後續 C2（部署步驟撰寫）與 C3（錄音可行性分析）提供基礎資料。

## 執行的動作與結果

| 動作 | 目的 | 預期達成效果 | 實際的結果 |
|------|------|-------------|-----------|
| `gh repo view` 取得 repo metadata | 取得專案基本資訊 | 獲得名稱、描述、語言、stars、license 等 | 完成。name: meetily, 描述: Privacy-First AI Meeting Assistant, 主要語言: Rust, license: MIT, stars: 大量 |
| 讀取 README.md | 了解專案功能、安裝方式、架構概述 | 取得安裝指引、功能列表、GPU 支援說明 | 完成。README 涵蓋 Windows/macOS/Linux 安裝、GPU 加速（CUDA/Metal/Vulkan）、Ollama 支援、系統架構（Tauri + Next.js） |
| 讀取 docs/building_in_linux.md | 取得 Ubuntu 建置細節 | 取得 Linux 建置的完整步驟、GPU 偵測邏輯、CUDA/Vulkan 設定 | 完成。文件提供 Ubuntu 的 apt 安裝指令、CUDA toolkit 安裝、CMAKE_CUDA_ARCHITECTURES 設定、Vulkan 備援方案 |
| 讀取 docs/BUILDING.md | 取得跨平台建置指引 | 確認 Linux/macOS/Windows 建置差異 | 完成。Linux 部分與 building_in_linux.md 一致 |
| 讀取 docs/architecture.md | 了解系統架構 | 取得高階架構圖與元件說明 | 完成。Tauri Core + Audio Engine + Transcription Engine + Database + Summary Engine |
| 讀取 Cargo.toml（workspace + frontend/src-tauri + llama-helper） | 了解技術棧與相依性 | 確認 GPU feature flags、音訊處理庫、LLM 整合方式 | 完成。關鍵發現：whisper-rs 0.13.2 支援 cuda/vulkan/hipblas/metal/coreml/openblas 等 features；cpal 0.15.3 負責音訊擷取；llama-helper 使用 llama-cpp-2 做本地 LLM 推理 |
| 讀取 tauri.conf.json | 了解 CSP 與權限設定 | 確認網路連線限制與 Ollama 整合 | 完成。CSP 允許 localhost:11434（Ollama 預設埠），無外部 API 強制依賴 |
| 讀取 scripts/auto-detect-gpu.js | 了解 GPU 自動偵測邏輯 | 確認自動偵測的優先順序與判斷條件 | 完成。偵測順序：CUDA > ROCm > Vulkan > OpenBLAS > CPU |
| 讀取 audio/capture/system.rs | 了解 Linux 系統音訊擷取實作 | 確認 Linux 上系統音訊的擷取方式 | 完成。Linux 使用 cpal default host（PulseAudio/PipeWire），無 macOS 的 Core Audio tap 特殊實作 |
| 讀取 audio/recording_commands.rs | 了解錄製流程 | 確認錄製啟動流程與裝置選擇邏輯 | 完成。使用 cpal 的 default_input_device / default_output_device |
| 讀取 ollama/ollama.rs | 了解 Ollama 整合方式 | 確認 Ollama 作為 LLM provider 的實作 | 完成。支援 localhost 端點、模型列表查詢、下載管理 |
| 讀取 summary/llm_client.rs | 了解摘要引擎的 LLM 客戶端 | 確認支援的 LLM providers | 完成。支援 OpenAI、Claude、Groq、Ollama、OpenRouter、BuiltInAI、CustomOpenAI |
| 查閱近期 open issues/PRs | 了解專案活躍度與已知問題 | 確認有無 TTS 相關 issue 或系統音訊相關 bug | 完成。無 TTS 相關 issue；有 VAD 相關 bug（#578）與語言選擇功能 PR（#581~#584） |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 驗證結果 |
|---------|-------------|---------|
| TTS 功能存在性 | 搜尋 README、Cargo.toml、源碼中 TTS 相關關鍵字 | **Meetily 無 TTS 功能**。README 僅提及 STT（Whisper/Parakeet）與摘要。使用者可能混淆 TTS 與 STT |
| RTX 2060s 相容性 | 確認 CUDA compute capability | RTX 2060s = Turing 架構，compute capability 7.5 → CMAKE_CUDA_ARCHITECTURES=75。CUDA toolkit 需安裝 |
| Ollama Cloud 支援 | 檢查 Ollama 整合程式碼 | Meetily 的 Ollama 整合僅支援**本地 Ollama 伺服器**（localhost:11434）。Ollama Cloud 可透過 Custom OpenAI endpoint 設定，但需確認 API 相容性 |
| Linux 系統音訊擷取 | 檢查 system.rs 與 cpal 實作 | Linux 上 cpal 使用 PulseAudio/PipeWire，可擷取系統音訊輸出（如瀏覽器中的 Google Meet）。需安裝 pulseaudio-utils 或 pipewire |
| Ubuntu 最低相依性 | 檢查 building_in_linux.md | 需安裝：build-essential, cmake, git, Rust, Node.js, pnpm。GPU 方案需額外安裝 nvidia-driver + nvidia-cuda-toolkit |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---------|---------|---------|---------|
| TTS 問題處理 | 直接告知無 TTS / 查證後確認 | 查證後確認無 TTS | 使用者明確提到 TTS，需在報告中澄清 Meetily 無 TTS 功能，僅有 STT 與摘要 |
| Ollama Cloud 方案 | 視為不支援 / 提供 Custom OpenAI 替代方案 | 提供 Custom OpenAI 替代方案 | Meetily 支援 Custom OpenAI endpoint，可指向 Ollama Cloud 的 API |
| 調研深度 | 僅讀 README / 深入源碼 | 深入源碼（Cargo.toml、audio capture、ollama、summary） | 使用者要求「逐步指令」，需確認每個步驟的技術細節是否正確 |
| 後續 C2 方向 | 合併兩個問題 / 分開處理 | 分開處理 | 問題 1（部署）與問題 2（錄音可行性）性質不同，C2 應先處理部署步驟，C3 處理錄音可行性 |
