# OmniRoute — 免費 AI 網關與多模型路由代理

> 調研日期：2026-07-25 | 版本：v3.8.47 | 授權：MIT | 語言：TypeScript | Stars：29,675

---

## 1. 這個技術解決什麼問題？

**開發者在使用多個 AI 模型提供者（Provider）時，面臨以下具體問題：**

- 每個 AI 工具（Claude Code、Codex CLI、Cursor、Cline、Copilot 等）需要各自設定不同的 API Endpoint 與 API Key
- 每個 Provider 有各自的 API 格式（OpenAI、Anthropic、Gemini 格式互不相容）
- 單一 Provider 的免費額度有限，用完即停，缺乏自動切換機制
- 缺乏統一的成本追蹤與用量管理
- 部分 Provider 有地理限制或 CAPTCHA 阻擋

**OmniRoute 的定位：** 一個本機執行的 AI 路由網關（Local AI Gateway），透過單一 OpenAI 相容 Endpoint 統一連接 250+ Provider（含 90+ 免費來源），提供模型路由、自動 Fallback、Token 壓縮、用量統計等功能。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- 2024-2026 年間，LLM Provider 數量爆炸性成長（OpenAI、Anthropic、Google Gemini、xAI Grok、DeepSeek、Qwen、Mistral、Groq 等），每個 Provider 有各自的 API 規格、認證方式、計價模式
- 多數 Provider 提供免費額度（Free Tier）作為獲客手段，但這些額度分散在不同平台，各自有不同 Rate Limit、到期時間、使用條款
- 開發者工具（IDE Plugin、CLI Agent）多數只支援 OpenAI 相容格式，無法直接使用非 OpenAI Provider

### 通用技術背景（自行推測補充）

- AI 編碼代理（Coding Agent）的普及（Claude Code、Codex、Cursor 等）使得開發者需要同時管理多個模型的 API 存取
- Provider 的免費額度政策變動頻繁（Gemini 2025/12 縮減 50-80% 免費額度、GitHub Models 2026/06 關閉新用戶註冊），手動追蹤成本極高
- 不同 Provider 的 API 格式差異（OpenAI Chat Completions vs Anthropic Messages vs Gemini generateContent）使得直接切換 Provider 需要改寫客戶端程式碼
- 部分 Provider（如 Google Antigravity、ChatGPT Web）使用 OAuth 或 Session Cookie 而非傳統 API Key，無法直接整合進標準工具鏈

---

## 3. 這個技術是如何解決該問題的？

### 3.1 核心架構

OmniRoute 基於 Next.js 16 建置，作為本機代理（Local Proxy）運作：

```
Client (Claude Code / Codex / Cursor / 任何 OpenAI 相容工具)
    │  http://localhost:20128/v1
    ▼
OmniRoute Gateway
    ├── OpenAI 相容 API 層 (/v1/*)
    ├── SSE + Translation Core (格式轉換引擎)
    ├── 27+ Provider Executor (Provider 專用執行器)
    ├── 18 種路由策略 (Routing Strategies)
    ├── 10 引擎壓縮管線 (Compression Pipeline)
    ├── MCP Server (95 工具) + A2A Protocol
    └── SQLite 持久層 (設定/用量/日誌)
    │
    ├── Tier 1: Subscription (Claude Code, Codex, Copilot)
    ├── Tier 2: API Key (DeepSeek, Groq, xAI, Mistral)
    ├── Tier 3: Cheap (GLM $0.5, MiniMax $0.2)
    └── Tier 4: Free (Kiro, Qoder, Pollinations)
```

### 3.2 統一 API 層

所有客戶端指向 `http://localhost:20128/v1`，OmniRoute 內部透過 Translator Registry 將請求轉換為目標 Provider 的格式：

- **Request Translators（9 個模組）：** antigravity-to-openai、claude-to-gemini、claude-to-openai、gemini-to-openai、openai-responses、openai-to-claude、openai-to-cursor、openai-to-gemini、openai-to-kiro
- **Response Translators（8 個模組）：** claude-to-openai、cursor-to-openai、gemini-to-claude、gemini-to-openai、kiro-to-openai、openai-responses、openai-to-antigravity、openai-to-claude
- 支援端點：`/v1/chat/completions`、`/v1/messages`、`/v1/responses`、`/v1/embeddings`、`/v1/images/generations`、`/v1/audio/transcriptions`、`/v1/audio/speech`、`/v1/videos/generations`、`/v1/music/generations`、`/v1/search`、`/v1/moderations`、`/v1/rerank`、`/v1/ocr`、`/v1/ws`（WebSocket）

### 3.3 模型路由與 Fallback

**Combo 機制：** 使用者定義一個模型鏈（Combo），OmniRoute 依序嘗試：

```
Combo "always-on":
  1. cc/claude-opus-4-7    ← Subscription（先用完訂閱額度）
  2. cx/gpt-5.5            ← 第二個訂閱
  3. glm/glm-5.1           ← 便宜備援（$0.5/1M）
  4. kr/claude-sonnet-4.5  ← 免費無上限（永不失敗）
```

**18 種路由策略：**

| # | 策略 | 行為 |
|---|------|------|
| 1 | `priority` | 依序嘗試，用完再換 |
| 2 | `fill-first` | 填滿每個目標配額再前進 |
| 3 | `weighted` | 加權隨機分配 |
| 4 | `round-robin` | 輪詢循環 |
| 5 | `p2c` | Power-of-Two-Choices 負載平衡 |
| 6 | `least-used` | 選取當前負載最低者 |
| 7 | `random` | 均勻隨機（去重） |
| 8 | `strict-random` | 純隨機（可重複） |
| 9 | `cost-optimized` | 最小化每請求成本 |
| 10 | `headroom` | 選取剩餘配額最多者 |
| 11 | `reset-window` | 偏好配額即將重置者 |
| 12 | `reset-aware` | 依重置時間排序 |
| 13 | `context-relay` | 跨目標傳遞對話上下文 |
| 14 | `context-optimized` | 依上下文大小選最佳 |
| 15 | `lkgp` | 黏著最後成功目標 |
| 16 | `auto` | 12 因子即時評分 |
| 17 | `fusion` | 並行多模型 + Judge 合成 |
| 18 | `pipeline` | 鏈式處理（輸出餵給下一個） |

**Auto-Combo 引擎：** 設定 model 為 `auto` 時，OmniRoute 根據 12 個因子（健康狀態、配額、成本、延遲、成功率、新鮮度等）即時評分並選取最佳目標。支援 `auto/coding`、`auto/fast`、`auto/cheap`、`auto/offline`、`auto/smart` 等變體。

### 3.4 三層 Resilience

| 層級 | 範圍 | 行為 |
|------|------|------|
| Circuit Breaker | 整個 Provider | 上游持續失敗時停止請求，自動探測恢復 |
| Connection Cooldown | 單一帳號/Key | Rate-limited 的 Key 暫時跳過，其他 Key 繼續服務 |
| Model Lockout | Provider + Model | 僅隔離特定配額耗盡的模型 |

### 3.5 Token 壓縮管線（10 引擎堆疊）

每筆請求透明通過壓縮管線，無需客戶端修改：

| # | 引擎 | 效果 |
|---|------|------|
| 1 | Session-Dedup | 跨輪次去重複內容 |
| 2 | CCR | 大區塊存檔為檢索標記 |
| 3 | RTK | 工具輸出智慧過濾（Shell/Test/Build/Git） |
| 4 | Headroom | 表格資料壓縮（~30%，GCF v3.2） |
| 5 | Relevance | 對最後用戶查詢做句子評分 |
| 6 | Caveman | 規則式散文壓縮（~65-75%） |
| 7 | LLMLingua-2 | ML 語意剪枝（MobileBERT ONNX） |
| 8 | Lite | 空白+圖片 URL 修剪 |
| 9 | Aggressive | 摘要+舊輪次漸進老化 |
| 10 | Ultra | 啟發式 + 小型 SLM 模型 |

預設模式：Lite（~15%）、Standard/Caveman（~30%）、Aggressive（~50%）、Ultra（~75%）、RTK（60-90% on 工具輸出）

### 3.6 免費額度聚合

OmniRoute 聚合 40+ Provider Pool 的免費額度，經 Pool-Deduped 計算：

| 類別 | 數量 |
|------|------|
| 穩定每月免費 Token | ~1.54B |
| 首月含註冊獎勵 | ~2.15B |
| 永久免費無上限 Provider | SiliconFlow、GLM-4-Flash、Tencent、Baidu、Kilo Gateway、OpenCode Zen |
| 理論上限（所有 Rate Limit 24/7） | ~10B（不作為宣傳數字） |

最大貢獻者：Mistral 1.00B、LLM7 150M、Groq 117M、Gemini 60M、Cerebras 30M、Cloudflare AI 30M、SambaNova 30M

### 3.7 Provider 執行器（27+ 專用執行器）

每個 Provider 有專用 Executor 處理其獨特協定：

| Executor | Provider | 特殊處理 |
|----------|----------|----------|
| DefaultExecutor | OpenAI、Anthropic、Gemini、Qwen、OpenRouter 等 | 動態 URL/Header |
| AntigravityExecutor | Google Antigravity | 429 混淆、身分輪換 |
| ChatGPTWebExecutor | ChatGPT Web | TLS 客戶端模擬 |
| ClaudeIdentityExecutor | Claude.ai | 指紋塑造、工具重新映射 |
| CodexExecutor | OpenAI Codex | 系統指令注入 |
| CursorExecutor | Cursor IDE | ConnectRPC + Protobuf |
| KiroExecutor | AWS CodeWhisperer/Kiro | AWS EventStream → SSE |
| 以及其他 20+ 專用執行器 | | |

### 3.8 其他功能

- **MCP Server：** 95 工具、30 作用域、3 種傳輸（stdio/SSE/Streamable HTTP）
- **A2A Protocol：** JSON-RPC 2.0 + SSE、6 技能、Agent-to-Agent 工作流
- **Memory 系統：** FTS5 + Vector（int8 量化）、可選記憶衰減
- **Guardrails：** PII 遮罩、Prompt Injection 檢測、Vision 內容過濾
- **Quota-Share：** 團隊共享單一訂閱帳號的配額分配
- **Cloud Agents：** Codex Cloud、Devin、Jules 任務生命週期管理
- **MITM Proxy：** 攔截忽略 Proxy 環境變數的 CLI 流量
- **TLS 指紋隱藏：** JA3/JA4 偽裝，避免上游 CAPTCHA
- **Dashboard：** 30+ 管理頁面（Provider、Combo、成本、用量、健康狀態、壓縮、審計等）
- **CLI：** 80+ 命令（chat、setup、doctor、connect、tokens 等）
- **部署方式：** npm global、Docker（AMD64+ARM64）、Desktop Electron、Termux（Android）、PWA

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|----------|-------------|---------------|-----------------|
| **LiteLLM** | Python SDK 層，提供 `litellm.completion()` 統一介面，支援 ~100 Provider | Python 生態系、需要程式碼整合 | 無 Dashboard、無壓縮、無 MCP/A2A、Fallback 僅 priority-based | 適合 Python-first 團隊，生產部署成熟（k8s/Helm） |
| **OpenRouter** | SaaS 服務，單一 API Key 存取 ~50 Provider，按 Token 計費 | 不需自架、接受 SaaS 加價 | 非自託管（資料經第三方）、無免費額度整合、無壓縮 | 最簡單的入門方案，單一帳單涵蓋所有 Provider |
| **Portkey** | 商業 AI 網關，提供 Gateway + Observability，支援 ~30 Provider | 付費訂閱、商業 SLA 需求 | 非開源、免費版功能受限、Provider 覆蓋最少 | 企業級 SLA 與合規功能，Managed Dashboard |
| **直接使用 Provider SDK** | 各 Provider 原生 SDK 直接呼叫 | 專案僅用單一或少數 Provider | 無統一管理、無自動 Fallback、需手動處理格式轉換 | 無額外依賴，最小延遲 |

### 切入點差異

- **OmniRoute vs LiteLLM：** OmniRoute 以「本機代理」而非「SDK」形式存在，不需改寫應用程式碼即可使用；LiteLLM 需要 Python 程式碼整合。OmniRoute 在 Provider 數量（250 vs ~100）、免費額度整合、Token 壓縮、MCP/A2A 支援上顯著領先
- **OmniRoute vs OpenRouter：** OpenRouter 是 SaaS，不需自架但資料經過第三方；OmniRoute 完全本機執行，資料不離開使用者機器。OpenRouter 不提供免費額度聚合、Token 壓縮、OAuth Provider 支援
- **OmniRoute vs Portkey：** Portkey 是商業產品，提供 SLA 與合規功能但非開源且 Provider 覆蓋最少（~30）；OmniRoute 開源 MIT 授權，功能面更廣但無商業 SLA
- **OmniRoute vs 直接使用 SDK：** 直接使用 SDK 無需額外基礎設施，但無法實現跨 Provider 自動 Fallback、統一用量追蹤、Token 壓縮等進階功能

### OmniRoute 的獨特定位

OmniRoute 在以下面向與替代方案有顯著差異：

| 面向 | OmniRoute | LiteLLM | OpenRouter | Portkey |
|------|-----------|---------|------------|---------|
| Provider 數量 | 250+ | ~100 | ~50 | ~30 |
| 免費 Provider | 90+ | 無 | Pass-through | 無 |
| OAuth Provider | 15+ | Partial | 無 | 無 |
| 路由策略 | 18 種 | Priority-based | Tier-based | Weighted |
| Token 壓縮 | 10 引擎堆疊 | 無 | 無 | 無 |
| MCP Server | 95 工具 | 無 | 無 | 無 |
| A2A Protocol | 6 技能 | 無 | 無 | 無 |
| TLS 指紋隱藏 | JA3/JA4 | 無 | 無 | 無 |
| 自託管 | 是 | 是 | 否 | 付費版 |
| 授權 | MIT | MIT | Proprietary | Proprietary |
