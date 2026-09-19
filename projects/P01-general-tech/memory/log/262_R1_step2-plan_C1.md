# 262_R1_step2-plan_C1

## 狀況理解

Step 2 第一個 sub-step（C1），針對 R1 意圖（調研 VoiceStudio 本地 AI 語音工作台）執行「取得 repo metadata 與主要文件」。此為典型工作流 2，無 R2+ 追問情境。目標：從 repo 官方來源收斂出分析所需的事實基線，供後續 C2（背景脈絡補查）與 Step 3 撰寫報告使用。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view debpalash/VoiceStudio --json ...` + `gh api ...` | 取得 metadata | 得到 stars/license/分支/更新時間/描述 | nameWithOwner=debpalash/VoiceStudio；★32,874；fork 3,892；100 open issues；language=Python；license=AGPL-3.0；default branch=main；created 2026-04-09；pushed 2026-09-18；homepage=voicestudio.sh；topics 含 local-first、voice-cloning、tts、stt、dubbing、mcp、tauri、electron 等 |
| `curl` README.md raw + 讀全文 | 取得使用者導向概述 | 掌握產品定位與功能框架 | 「Open source voice cloning and workflow engine. Build local.」；四工作區：voice cloning / voice design / dubbing / models；另含 dictation widget、audiobook、batch、MCP、remote workers；Electron 為 primary desktop（v0.5.3 起，Tauri 為舊版）；default engine = k2-fsa/OmniVoice；AGPL-3.0 |
| 列 `gh api /contents/` + `docs/` + `docs/engines/` | 盤點文件結構 | 找出關鍵子文件 | docs/ 下 20+ 引擎 guides、speech-platform、mcp、performance、benchmarks、competitive-analysis、STRUCTURE、ROADMAP、features.yaml 等；repo 含 backend/、frontend/、omnivoice/、bin/、deploy/ |
| 讀 docs/engines/omnivoide.md + engines/README.md | 了解 default TTS 引擎與引擎矩陣 | 掌握 TTS/STT 引擎清單與硬體需求 | OmniVoice 為 default，zero-shot 跨 600+ 語言、24kHz、VRAM floor 6GB；全 repo 支援 15+ TTS（OmniVoice/GGUF、VoxCPM2、MOSS-TTS-Nano、KittenTTS、MLX-Audio、CosyVoice 3、GPT-SoVITS、Sherpa-ONNX、IndexTTS、Supertonic、dots.tts、Confucius4、audio.cpp…）與 9 STT（WhisperX、Faster-Whisper、MLX-Whisper、Parakeet、Moonshine、FunASR、Sherpa-ONNX、OpenAI-compatible） |
| 讀 docs/performance.md | 了解效能調校與硬體限制 | 掌握 VRAM/CPU 的實際影響 | 詳細 env var 調校（DEVICE、FLASHINFER、PROMPT_DISK_CACHE、IDLE_TIMEOUT、GPU_WORKERS、GENERATE_TIMEOUT 等）；6GB VRAM floor、CPU fallback、Apple Silicon 例外 |
| 讀 docs/speech-platform.md | 了解作為 headless 語音平台的能力 | 掌握整合面（API/WS/MCP/dictation） | 桌面 dictation + headless local speech service；port 3900（backend/API/WS/MCP）、3902（Rust control sidecar）；OpenAI-compatible、WebSocket、MCP Streamable/stdio、JSON-RPC；loopback 免憑證、remote 用 bearer key |
| 讀 docs/mcp.md | 了解 agent 整合面 | 掌握 MCP server 工具集 | mounted at `/mcp`；工具 generate_speech/clone_voice/transcribe/list_*/check_health；per-agent voice binding、output files mode 省 context |
| 讀 docs/competitive-analysis.md | 取得官方自評與競品定位 | 建立競品對照事實 | 官方自評與 voicebox（最直接競品）、pyvideotrans、Patter 之 feature matrix；646 語言 claim、incremental re-dub、AudioSeal watermark 為獨特項；二線競品 KlicStudio、VideoLingo、voice-pro、ebook2audiobook、GPT-SoVITS 等 |
| 讀 docs/STRUCTURE.md + benchmarks.md | 了解架構與效能基準 | 掌握模組分工與實測現況 | backend=FastAPI 40 routers / 88 services / 引擎 adapters；frontend=React19+Vite；omnivoice=模型套件；benchmarks 表目前「no verified rows yet」→ RTF/VRAM 尚無官方實測數據 |

**補充脈絡（repo 內自帶，非我杜撰）：**
- license 策略：AGPL-3.0-only + commercial dual-license；MIT 可併入，GPL 只能當設計文件不能複製（competitive-analysis.md 明文）。
- pyvideotrans（17.9k★）官方已把 VoiceStudio 當 TTS/clone backend，但該整合已確認壞掉（README/competitive-analysis 明文）。
- README 提供讓 coding agent 自助安裝的 prompt 段落（skills 驅動 setup）。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| metadata 完整 | `gh repo view` + `gh api` 交叉比對 | 一致：★32,874 / AGPL-3.0 / main / Python / 646 語言 claim |
| 產品定位 | README + feature-catalog 讀取 | 本地優先、voice cloning+design+dub+dictation+audiobook；default 引擎 OmniVoice；Electron primary |
| 引擎矩陣 | engines/README.md | 15+ TTS / 9 STT / 多 ASR；default OmniVoice + WhisperX/Faster-Whisper |
| 硬體門檻 | omnivoice.md + performance.md | VRAM floor 6GB（僅 OmniVoice 有實測 floor）；GPU auto-detect；Windows 僅 NVIDIA/CUDA 加速 |
| 整合面 | speech-platform.md + mcp.md | port 3900/3902；OpenAI/WS/MCP/JSON-RPC；dictation + agent MCP |
| 競品定位 | competitive-analysis.md（repo 自帶） | 官方自評最直接競品 voicebox；pyvideotrans/Patter 為對照；二線列 7 個 |
| 效能實測 | benchmarks.md | 表為空（尚無官方已驗證 RTF/VRAM 數據）→ 報告不可引用具體 RTF |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| metadata 來源 | (A) gh api (B) webfetch GitHub 頁 | A | gh api 結構化 JSON、較穩；避免網頁渲染 |
| 子文件範圍 | (A) 全抓 docs/ (B) 挑關鍵文件 | B：關鍵 6 份 | 聚焦分析報告 5 點所需；全抓會超 6000 字上限且含過多操作細節 |
| 競品資料來源 | (A) 自己外部搜尋 (B) 用 repo 自帶 competitive-analysis | B 為主、外部補查留 C2 | repo 自帶官方自評矩陣，事實齊全；外部競品對照在 C2 補查時再驗證 |
| 效能數據引用 | (A) 直接引用 (B) 標註「表為空」 | B | benchmarks.md 無已驗證 rows，硬引用即造假；報告需如實標註無官方實測 |
| README 的 646 語言 claim | (A) 全信 (B) 標為「claim」 | B：標為官方宣稱 | 屬 marketing claim，C2 可從模型側（OmniVoice 600+）旁證，但不作為已證事實 |
