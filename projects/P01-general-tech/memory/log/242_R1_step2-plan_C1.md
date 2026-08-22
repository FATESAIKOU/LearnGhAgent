# 242_R1_step2-plan_C1.md

## 狀況理解

本 sub-step（C1）執行 Step 2 的第一個資訊取得動作：對技術標的 **Switchyard**（https://github.com/NVIDIA-NeMo/Switchyard）取得 repo metadata、README 與關鍵子文件、license、架構與 routing 演算法脈絡。這是 R1 首次調研，目標是建立對該工具的完整客觀描述，供後續 sub-step 補背景與替代方案、並收斂成最終 5 點分析報告。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view NVIDIA-NeMo/Switchyard --json ...` | 取得 repo metadata | 確認 star/fork、語言、license、活躍度 | 取得：2117 stars、185 forks、Rust、Apache 2.0、created 2026-05-19、pushed 2026-08-21（活躍）、描述「LLM applications 跨模型與 provider 路由，保持 OpenAI/Anthropic API 相容」 |
| 讀取 `do/skills/document/SKILL.md` | 確認標準調研動作 | 對齊文件抓取規範 | 確認 4 步驟：metadata → 主要文件 → 補查背景 → 收斂撰寫；優先 webfetch/curl，CDP 僅反爬時用 |
| 列出 repo 根目錄與 `docs/`、`crates/` | 盤點文件結構 | 找到關鍵文件入口 | 根含 README/CHANGELOG/LICENSE/Cargo.toml；docs/ 含 core_concepts、getting_started、architecture、routing_algorithms；crates/ 含 switchyard-server、libsy、protocol、switchyard-py、switchyard-translation 等 |
| 抓取並讀取 README.md | 掌握工具定位與特色 | 理解「這是什麼、解決什麼」 | 定位為「Rust 的 LLM 流量 proxy 與 library」；三大特色：Protocol Translation（OpenAI↔Anthropic）、Multi-Backend Routing、Prometheus Metrics；**pre-alpha、明示非 production 用** |
| 抓取並讀取 `docs/core_concepts.md` | 理解核心架構 | 掌握執行面、資料模型、路由演算法 | 確認兩個 runtime surface（`switchyard-server` HTTP proxy、`switchyard-libsy` 可嵌入 Rust library）；三層抽象（LLM client → target → route）；演算法：passthrough/random/llm_classifier/stage_router |
| 抓取並讀取 `docs/routing_algorithms/overview.md` | 理解路由策略全貌 | 掌握 routing 選型 | 確認策略含 sub-agent、random、llm_classifier、stage_router、escalation、advisor gate；三層 TOML 部署範例；self-hosted target（vLLM）支援；route ID 對 client 暴露 |
| 抓取並讀取 `docs/getting_started.md`（前 80 行） | 理解安裝與執行 | 掌握部署條件 | 兩條路徑：server（`cargo install switchyard-server`）與 library（libsy embed）；前置 Rust/uv；以 TOML 描述 llm_clients/targets/routes；credential 走 env var |
| `gh repo view --json licenseInfo` | 確認授權 | 掌握 license | Apache License 2.0 |

### 已取得關鍵事實（供後續 sub-step 引用）

- **定位**：Rust 編寫的 LLM 流量代理，讓既有 coding agent（Claude Code / Codex）保留原生 API 語法（OpenAI Chat / Anthropic Messages / OpenAI Responses），由 Switchyard 把請求轉給 vLLM / NIM / Ollama 等開放模型後端。
- **兩條執行路徑**：
  - `switchyard-server`：獨立 HTTP proxy，吃 TOML deployment，暴露三個相容 endpoint。
  - `switchyard-libsy`：可嵌入 Rust library，演算法「只做決策、不自己 call model」，把 model call 交還給 host app。
- **三層抽象**：`llm_clients`（上游 base_url/format/credential env/retry）、`targets`（一個上游 model id + client）、`routes`（client 可見 model id + 演算法）。
- **演算法集合**：`passthrough`、`random`、`llm_classifier`（weak/strong tier）、`stage_router`（tool-result/progress 訊號）、`escalation_router`、`advisor_gate`、`subagent_routing`。
- **protocol 中立**：`switchyard-protocol` 定義 provider-neutral request/response/stream；`switchyard-translation` 做 format 互轉。
- **metrics**：Prometheus（request/error/latency/token/routing overhead）。
- **成熟度**：pre-alpha、快速演化、API 未到 v1.0。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo 存在性與授權 | `gh repo view` / `--json licenseInfo` | repo 存在，Apache 2.0，Active（created 2026-05、pushed 2026-08） |
| 工具定位 | 讀 README | 確認為 LLM 流量 proxy + 路由 + protocol 翻譯 + metrics |
| 核心架構 | 讀 core_concepts / overview | 確認為 Rust 雙路徑（server/libsy）、三層 TOML、多演算法 |
| 執行條件 | 讀 getting_started | 需 Rust/Cargo；可 `cargo install`；TOML 部署 |
| 競爭/替代脈絡 | 對照 Step 1 第二大腦 | 同問題域既有判定：OmniRoute（Accept）、DeepSeek V4「降低 Model Routing 優先級」；C1 已掌握 Switchyard 差異化面（protocol 翻譯 + 演算法套件），供 §4 對照 |

### 尚未取得的（留待後續 sub-step 或網路補查）

- 與 LiteLLM / OpenRouter / Portkey 的逐一功能對照細節（替代方案 §4）。
- 各 routing 演算法的詳細成本與副作用（llm_classifier 額外 model call、stage_router 訊號判定）。
- Switchyard 在 NVIDIA-NeMo 的定位（該 org 的 NIM / NeMo 關係、為何要此工具）。

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件取得途徑 | webfetch / curl / gh api | `gh api contents + base64 decode` | 免被反爬干擾、結構化、穩定；webfetch 非必要（未遇 CAPTCHA） |
| 核心文件挑選 | 只讀 README / 讀 README+core_concepts+overview+getting_started | 讀 4 份 | 兼顧定位、核心抽象、路由選型、部署條件；達成 C1「metadata+主要文件」目標即可，演算法細部留後續 sub-step |
| metadata 欄位 | 僅 description / 完整 fields | 完整 fields | 需 star/fork/language/active 以評估成熟度與採用情況 |
| 與既有判定對照時機 | 本 sub-step 即評 / 留 §4 | 留 §4 | 本 sub-step 僅收斂事實；「是否採用/替代方案優劣」屬分析收斂，避免事實收集階段混入決策 |
