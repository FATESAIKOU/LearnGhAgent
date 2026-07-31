# Qoder 技術分析報告

## 1. 這個技術解決什麼問題？

Qoder 解決的是「開發者需要一個整合式 AI 編程環境，能無縫切換多個頂尖 LLM、執行長時間自主任務（agent/quest），並在超額時有免費降級備援」的問題。

具體來說，Qoder 同時解決三個層面的問題：

- **模型聚合**：使用者不需分別註冊 Qwen、DeepSeek、GLM、Kimi、MiniMax 等多家 provider，透過 Qoder 一個入口即可使用所有模型
- **IDE 整合**：提供 Desktop App（Electron-based IDE）、JetBrains Plugin、CLI 三種開發介面，將 LLM 能力嵌入開發流程（inline chat、agent mode、quest）
- **用量管理**：以 Credits 為單位的月訂閱制，用量超額後自動降級至免費 Lite tier，避免意外超額帳單

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到

- 2024-2026 年間，中國與亞洲 LLM 供應商（Qwen、DeepSeek、GLM、Kimi、MiniMax）快速崛起，提供高品質但各自獨立的 API
- 開發者需要同時使用多家模型（不同模型擅長不同任務），但逐一註冊、管理 API key、追蹤用量極為繁瑣
- 現有 IDE 的 AI 插件（如 GitHub Copilot、Cursor）多綁定單一模型或單一 provider，缺乏靈活性

### 通用技術背景

- LLM API 定價模式分歧：OpenAI/Anthropic 採 token-based pay-as-you-go，中國供應商價格更低但各自為政
- 開發者對「agentic coding」（AI 自主執行多步驟任務）的需求增長，需要比單次問答更複雜的執行框架
- 月訂閱制（如 ChatGPT Plus $20、Claude Pro $20）已成主流，但這些訂閱限制在單一模型生態系內
- OpenRouter 等純 API gateway 雖解決了模型聚合問題，但不提供 IDE 整合或 agent 執行框架

## 3. 這個技術是如何解決該問題的？

Qoder 的架構可拆為三層：

```
┌─────────────────────────────────────────────────┐
│                  產品層 (IDE/CLI/Plugin)          │
│  Desktop App  │  JetBrains Plugin  │  CLI        │
│  (Electron)   │  (Java)            │  (Node.js)  │
├─────────────────────────────────────────────────┤
│                  執行層 (Agent Framework)         │
│  Ask Mode  │  Agent Mode  │  Quest  │  Experts  │
│  (單次問答)  │  (自主執行)   │  (長期任務)│  (多agent) │
├─────────────────────────────────────────────────┤
│                  模型層 (Model Aggregator)        │
│  Qwen3.7  │  DeepSeek-V4  │  GLM-5.2  │  Kimi   │
│  MiniMax  │  + BYOK (自帶API key)                │
└─────────────────────────────────────────────────┘
```

### 3.1 模型聚合（Model Aggregator）

Qoder 本身不訓練模型，而是作為 aggregator 向多家 LLM provider 採購 API 並轉售：

| 模型 | Provider | Credits 消耗率 | 定位 |
|------|----------|---------------|------|
| Qwen3.7-Max | Alibaba (Qwen) | 0.5x | 頂尖 agentic 能力，可執行 35 小時任務 |
| Qwen3.7-Plus | Alibaba (Qwen) | 0.1x | 推理/效率/多模態均衡 |
| DeepSeek-V4-Pro | DeepSeek | 0.5x | 複雜推理與程式碼生成 |
| DeepSeek-V4-Flash | DeepSeek | 0.1x | 快速推理、低成本 |
| GLM-5.2 | Zhipu AI (GLM) | 0.6x | 複雜系統工程與長期任務 |
| Kimi-K2.7-Code | Moonshot (Kimi) | 0.3x | 長上下文編碼，精確指令跟隨 |
| MiniMax-M3 | MiniMax | 0.2x | 原生多模態、1M 上下文 |

**BYOK（Bring Your Own Key）**：使用者可自帶 Alibaba Cloud / DeepSeek / Z.ai / Kimi / MiniMax / Xiaomi MIMO 的 API key，此時不消耗 Qoder Credits，直接由 provider 計費。

### 3.2 執行框架（Agent Framework）

Qoder 提供四層執行模式，由淺入深：

```
執行模式階層：
┌─────────────────────────────────────────────┐
│  Quest - Experts Mode  (~75 credits/次)      │ ← 多 agent 平行協作
├─────────────────────────────────────────────┤
│  Quest - Agent Mode    (~50 credits/次)      │ ← 長期自主任務 (up to 26h)
├─────────────────────────────────────────────┤
│  Editor - Agent Mode   (~7-12 credits/次)   │ ← 多步驟自主執行
├─────────────────────────────────────────────┤
│  Editor - Ask Mode      (~3-4 credits/次)    │ ← 單次問答
└─────────────────────────────────────────────┘
```

- **Ask Mode**：單次問答，類似 ChatGPT 對話
- **Agent Mode**：AI 自主規劃、執行程式碼、使用工具，完成多步驟任務
- **Quest**：長時間背景執行任務（最長 26 小時），適合大型重構
- **Experts Mode**：多個 expert agent 平行協作，各自負責不同面向

### 3.3 定價與用量管理

**月訂閱方案：**

| 方案 | 月費 | Credits/月 | 超額後 |
|------|------|-----------|--------|
| Free | $0 | 0（僅 Lite tier） | - |
| Pro | $20 | 2,000 | 降級至 Lite（免費有限次數） |
| Pro+ | $60 | 6,000 | 降級至 Lite |
| Ultra | $200 | 20,000 | 降級至 Lite |

**Credit Pack（加購）：** $20 / 1,500 Credits，有效期 1 個月，可堆疊

**Tier 消耗率（以 Auto = 1.0x 為基準）：**

| Tier | 消耗率 | 說明 |
|------|--------|------|
| Auto | ~1.0x | 智慧路由，預設推薦 |
| Ultimate | ~1.6x | 專家級深度推理 |
| Performance | ~1.1x | 進階推理 |
| Efficient | ~0.3x | 標準推理，高性價比 |
| Lite | 免費 | 基本推理，尖峰時段可能較慢 |

### 3.4 產品線

| 產品 | 說明 |
|------|------|
| Desktop | Electron-based IDE，主要產品 |
| JetBrains Plugin | JetBrains IDE 插件 |
| CLI | `npm install -g @qoder-ai/qodercli`，終端機 AI 夥伴 |
| QoderWork | 非編碼工作（法律、財務、行銷等）的 AI 助手 |
| QoderWake | 7x24 背景執行的 AI 員工 |
| Cloud Agents | 企業級雲端 AI agent 平台 |
| Enterprise | 團隊管理、SSO、用量監控 |

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|----------|-------------|---------------|-----------------|
| **OpenRouter** | 純 API gateway，聚合 400+ 模型，5.5% markup，無月費 | 使用者需自行開發或整合到現有工具（IDE/CLI） | 無 IDE 整合、無 agent 框架、需自行處理用量管理 | 最低成本的模型聚合方案，但需自行建構開發環境 |
| **ChatGPT Plus/Pro** ($20/$200) | OpenAI 自有模型（GPT-4o/o3），網頁/App/API 三種介面 | 接受僅使用 OpenAI 模型生態系 | 無法使用其他 provider 模型；Pro $200 價格較高 | 最成熟的單一模型體驗，但模型選擇受限 |
| **Claude Pro/Max** ($20/$100) | Anthropic 自有模型（Sonnet/Opus/Fable），含 Claude Code CLI | 接受僅使用 Anthropic 模型生態系 | 無法使用其他 provider 模型；Max $100 起 | 頂尖編程能力，但模型選擇受限 |
| **Ollama Cloud** ($20) | Ollama 官方雲端託管，執行開源模型 | 接受開源模型（Llama/Qwen/DeepSeek 等），非頂尖閉源模型 | 無法使用閉源頂尖模型（GPT-4o/Claude Opus 等） | 固定價格無限用量（受 fair use 限制），但模型能力上限較低 |
| **GitHub Copilot** ($10/$19) | 深度整合 VS Code/GitHub，以程式碼補全與 inline chat 為主 | 使用 VS Code 或 JetBrains，接受 GitHub 生態 | 模型選擇受限（主要為 OpenAI 模型），agent 能力較弱 | 最無縫的 IDE 整合，但 agentic 能力遠低於 Qoder |

### 4.2 切入點差異分析

```
                   模型選擇自由度
                  高 ▲
                     │
           OpenRouter │     Qoder
           (純 gateway)│  (IDE + gateway)
                     │
                     │
                     │
              Ollama Cloud│
              (開源模型)  │
                     │
                     │
              Copilot │  ChatGPT/Claude
              (單一模型) │  (單一生態系)
             低 ────────────┼───────────► IDE 整合深度
                     低     │     高
```

- **Qoder 的定位**：同時佔據「高模型自由度」與「高 IDE 整合深度」的象限，這是 OpenRouter（只有 gateway）和 ChatGPT/Claude（只有單一模型）都無法同時提供的
- **OpenRouter 的優勢**：純 API 無月費，適合已有自建工具鏈的開發者；400+ 模型選擇遠多於 Qoder 的 7 個
- **ChatGPT/Claude 的優勢**：自有模型品質頂尖，生態系完整（plugins、GPTs、projects）
- **Ollama Cloud 的優勢**：固定 $20 無限用量（受 fair use 限制），適合大量使用開源模型的場景

### 4.3 使用者 4 個問題的直接回答

#### Q1: Qoder 到底在賣什麼？

Qoder 賣的是**三層捆綁產品**：

1. **模型聚合服務**（LLM 二房東）：向 Qwen/DeepSeek/GLM/Kimi/MiniMax 採購 API，加價後以 Credits 形式轉售
2. **IDE 客戶端軟體**：Desktop App（Electron）、JetBrains Plugin、CLI 三種形式
3. **Agent 執行框架**：Ask/Agent/Quest/Experts 四層執行模式

不是單純的「LLM 二房東」，也不是單純的「CLI/Desktop 包裝」，而是**模型聚合 + IDE 整合 + Agent 框架**的三合一產品。

#### Q2: 與 Ollama Cloud / ChatGPT / Anthropic 的訂閱差異？

| 比較維度 | Qoder Pro ($20) | Ollama Cloud ($20) | ChatGPT Plus ($20) | Claude Pro ($20) |
|----------|-----------------|-------------------|-------------------|-----------------|
| 模型來源 | 多家第三方（Qwen/DeepSeek/GLM/Kimi/MiniMax） | 開源模型（Llama/Qwen/DeepSeek 等） | 僅 OpenAI（GPT-4o/o3/mini） | 僅 Anthropic（Sonnet/Opus/Fable） |
| 用量單位 | 2,000 Credits/月（約 500-666 次 Ask） | 無限（fair use） | 有限（message-based，未公開具體數字） | 有限（5-hour session window） |
| 超額處理 | 降級至免費 Lite tier | 降速/限制 | 降速/限制 | 降速/限制 |
| IDE 整合 | Desktop App + JetBrains + CLI | 無（僅 API） | 網頁 + App + API | 網頁 + App + Claude Code CLI |
| Agent 能力 | Quest (26h) + Experts Mode | 無內建 | 有限（GPTs） | Claude Code |
| BYOK | 支援（6 家 provider） | 不適用 | 不支援 | 不支援 |

**價格比較（以 DeepSeek-V4-Pro 為例）：**

- Qoder Pro $20 = 2,000 Credits。若全部用於 Ask Mode（~3.5 credits/次）≈ 571 次問答
- DeepSeek 官方 API 定價：DeepSeek-V4-Pro 約 $2-5/MTok（input）+ $8-25/MTok（output）
- 571 次問答若每次平均 2K input + 4K output tokens ≈ 1.14M input + 2.28M output tokens
- 直接 DeepSeek API 成本 ≈ $2.28 + $18.24 = ~$20.52（與 Qoder Pro $20 大致持平）

**結論**：Qoder 的定價並非明顯低於直接使用 API，而是**將多家 API 的 markup 隱藏在 Credits 系統中**，賣點是「一個月費使用多家模型 + IDE 整合」，而非單純的價格優勢。

#### Q3: 性價比優勢能否持續？

**優勢來源分析：**

| 優勢來源 | 可持續性 | 風險 |
|----------|---------|------|
| 向中國 provider 採購的低價 API | 中 | 中國 provider 可能漲價或限制海外 access |
| Credits 系統的模糊定價（不揭露 token 單價） | 低 | 使用者若精算會發現 markup 不低 |
| 多家模型聚合的便利性 | 高 | 這是真實需求，但 OpenRouter 也提供 |
| IDE + Agent 框架的整合 | 高 | 這是 Qoder 的護城河，但 Cursor/Windsurf 也在追趕 |
| 公司規模小（Bright Zenith Private Limited） | 低 | 新加坡小型公司，資金與營運風險高於 OpenAI/Anthropic |

**關鍵風險**：
- Qoder 背後是新加坡小型公司 Bright Zenith Private Limited，非知名 AI 公司，無公開融資資訊
- 產品依賴第三方 API，若 provider 漲價或限制 access，Qoder 的利潤空間會被壓縮
- GitHub 上存在 qoder-free(385 stars)、qoder-proxy(134 stars)、qoder2api(74 stars) 等逆向/破解工具，顯示社群對定價的不滿
- Credit Pack $20/1,500 Credits 的加購價（$0.0133/credit）比 Pro 方案（$0.01/credit）貴 33%，顯示加購不划算

**結論**：Qoder 的「便利性優勢」（IDE + 多模型）可持續，但「價格優勢」不顯著且不可持續。

#### Q4: 比 OpenRouter 優勢大嗎？

| 比較維度 | Qoder | OpenRouter |
|----------|-------|------------|
| 商業模式 | 月訂閱 $20-200 | Pay-as-you-go，5.5% markup |
| 模型數量 | 7 個精選模型 | 400+ 模型 |
| IDE 整合 | Desktop + JetBrains + CLI | 無（僅 API） |
| Agent 框架 | 內建（Ask/Agent/Quest/Experts） | 無（需自行開發） |
| BYOK | 支援 6 家 provider | 支援（$25K 內免平台費） |
| 最低成本使用 | $20/月（Pro） | $0（僅付 API 費用） |
| 超額處理 | 降級至免費 Lite | 直接扣款或拒絕請求 |
| 公司背景 | Bright Zenith（新加坡小型公司） | OpenRouter Inc.（美國，獲融資） |

**OpenRouter 的優勢場景**：
- 已有自建 IDE/CLI 工具鏈的開發者
- 需要 400+ 模型選擇（不限於中國模型）
- 用量不固定，不想付月費
- 需要純 API 整合

**Qoder 的優勢場景**：
- 想要開箱即用的 IDE + AI 整合
- 需要長時間 agent 任務（Quest up to 26h）
- 偏好月訂閱制的可預測費用
- 主要使用中國模型（Qwen/DeepSeek/GLM/Kimi）

**結論**：Qoder 與 OpenRouter 不是直接競爭關係。Qoder 是「IDE 產品 + 模型聚合」，OpenRouter 是「純 API gateway」。若使用者只需要模型聚合，OpenRouter 更便宜、模型更多；若需要 IDE 整合 + agent 框架，Qoder 是唯一選擇。
