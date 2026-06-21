# Vercel Eve — Agent Framework 分析報告

> 調研日期：2026-06-21（Eve 開源第 5 天，beta 階段）
> 資料來源：vercel.com/eve、vercel.com/docs/eve、eve.dev/docs、GitHub vercel/eve

---

## 1. 這個技術解決什麼問題？

**Eve 解決的問題：開發者需要一個統一的框架來建構「可投入生產的 AI agent」，該 agent 需要具備持久化對話、工具呼叫、沙箱隔離、多平台部署、人機協作（HITL）等能力，而現狀是這些能力分散在多個獨立工具與服務中，開發者必須自行拼湊整合。**

具體來說，Eve 解決以下子問題：

| 子問題 | 說明 |
|--------|------|
| Agent 狀態持久化 | 對話中斷（crash、redeploy）後需能無損恢復，而非從頭開始 |
| 工具定義與註冊 | 工具需有型別安全的輸入輸出、自動發現、無需手動註冊 |
| 指令與技能分離 | 系統提示詞（always-on）與按需載入的程序（skills）需分開管理 |
| 多通道交付 | 同一 agent 需同時服務 Slack、Discord、Web Chat、API 等多個介面 |
| 沙箱隔離 | 模型執行的 shell/file 操作需與 app runtime 隔離，不洩漏 credentials |
| 人機協作 | 敏感操作需等待人類審批後才執行，且審批過程需 durable |
| 部署與可觀測性 | Agent 需能部署到 production 並提供 run-level 的監控 |

**模糊之處**：Eve 的定位是「agent 的 Next.js」，但 Next.js 解決的是 web app 的明確痛點（SSR、routing、data fetching），而「agent 的痛點」目前仍在快速演化中。Eve 選擇的解決方案（filesystem-first、durable workflow）是否為最優解，需待生態成熟後驗證。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **LLM 本身是 stateless 的**：每次模型呼叫都是獨立請求，不保留對話歷史。開發者需自行管理 context window 的壓縮與歷史儲存。
- **工具呼叫需要型別安全**：LLM 輸出 JSON 格式的 tool call，但缺乏編譯期檢查，runtime 錯誤常見。
- **生產環境需要 durable execution**：agent 可能執行數分鐘到數天的任務（如資料分析、多步驟審批），process crash 或 redeploy 不應丟失進度。
- **多平台交付的複雜性**：Slack、Discord、Web 各有不同的 API、認證、事件格式，為每個平台重寫 agent 邏輯是常見的浪費。

### 通用技術背景（文章中未明確提及）

- **Agent 框架的歷史演進**：2023-2024 年間出現了大量 agent 框架（LangChain、AutoGPT、CrewAI 等），但它們多數專注於「agent 的思考鏈」而非「agent 的基礎設施」。Eve 選擇從基礎設施層切入（durability、sandbox、multi-channel），而非從 prompt engineering 層切入。
- **Vercel 的產品策略**：Vercel 已擁有 AI SDK（模型呼叫抽象層）、AI Gateway（模型路由與 fallback）、Workflows（durable execution）、Sandbox（隔離執行）、Connect（第三方服務認證）。Eve 是將這些既有產品整合成一個 agent 專用框架的「上層封裝」。
- **Filesystem-first 的設計哲學**：類似於 Next.js 的 filesystem-based routing，Eve 將 agent 的每個元件（tools、skills、channels、connections）對應到檔案系統的目錄結構。這降低了認知負擔（「看到目錄就知道 agent 能做什麼」），但也意味著動態註冊需要額外的抽象層（`defineDynamic`）。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 核心架構：Filesystem-first

Eve 的 agent 是一個目錄。每個子目錄對應一個「slot」，slot 決定檔案的載入方式：

```
my-agent/
├── package.json
├── agent/
│   ├── agent.ts              # runtime config（model、compaction 等）
│   ├── instructions.md       # 永遠在 context 中的系統提示詞
│   ├── instrumentation.ts    # 遙測配置（OTel）
│   ├── channels/             # 通道適配器（Slack、Discord、Web 等）
│   ├── connections/          # 外部服務認證（MCP、OAuth）
│   ├── hooks/                # 生命週期事件訂閱
│   ├── skills/               # 按需載入的程序（Markdown）
│   ├── lib/                  # 共享輔助程式碼（import-only，不進 sandbox）
│   ├── sandbox/              # 沙箱配置與 workspace seed 檔案
│   ├── tools/                # 型別安全的工具（TypeScript + Zod）
│   ├── schedules/            # 定時任務
│   └── subagents/            # 子 agent（專用 agent）
└── evals/                    # 評估測試
```

**路徑即 identity**：`agent/tools/get_weather.ts` 自動註冊為 tool `get_weather`，無需手動註冊表。

### 3.2 Durable Execution（Workflow SDK）

Eve 使用 Vercel Workflow SDK 實現 durable session：

```
Session（整個對話，可持續數天）
  └── Turn（一次使用者輸入 + 所有觸發的工作）
        └── Step（一次模型呼叫 + 其 tool calls，durable checkpoint）
```

- 每個 step 完成後 checkpoint 狀態
- Process crash 或 redeploy 後從最後完成的 step 恢復
- 已完成的 step 永不重播（replay recorded result）
- 中斷的 step 會重播，因此非冪等操作需放在 `needsApproval` 之後

### 3.3 工具系統

```typescript
// agent/tools/get_weather.ts
import { defineTool } from "eve/tools";
import { z } from "zod";

export default defineTool({
  description: "Get the current weather for a city.",
  inputSchema: z.object({ city: z.string().min(1) }),
  async execute({ city }, ctx) {
    return { city, condition: "Sunny", temperatureF: 72 };
  },
});
```

- **型別安全**：Zod schema 自動推論 `input` 型別
- **自動發現**：檔案路徑即工具名稱
- **App runtime 執行**：工具在 app runtime 執行（有 `process.env`），非 sandbox
- **Human-in-the-loop**：`needsApproval: always()` 等 helper 控制審批行為
- **輸出投影**：`toModelOutput` 可讓 channel 看到完整資料而 model 只看摘要

### 3.4 沙箱隔離

```
┌─────────────────────┐     ┌──────────────────────┐
│   App Runtime       │     │   Sandbox            │
│  (trusted side)     │     │  (isolated side)     │
│                     │     │                      │
│  process.env ✓      │     │  process.env ✗      │
│  Node.js code ✓     │     │  /workspace only     │
│  Network unrestricted│     │  Network by policy   │
│  Tool execute()     │────>│  bash / file tools   │
└─────────────────────┘     └──────────────────────┘
```

- 內建工具（`bash`、`read_file`、`write_file`、`glob`、`grep`）在 app runtime 執行，proxy 到 sandbox
- Credentials 永遠不進入 sandbox
- 支援 credential brokering（在 firewall 層注入 auth header）

### 3.5 多通道支援

```typescript
// agent/channels/slack.ts
import { connectSlackCredentials } from "@vercel/connect/eve";
import { slackChannel } from "eve/channels/slack";

export default slackChannel({
  credentials: connectSlackCredentials("slack/my-agent"),
});
```

- 同一 agent codebase 部署到 Slack、Discord、Teams、Web Chat、API、cron、CLI
- Channel 負責：標準化輸入、持有 continuationToken、決定交付方式
- 內建 eve HTTP channel（預設啟用），提供 REST API + NDJSON streaming

### 3.6 技能系統（Skills）

- Markdown 文件，按需載入（`load_skill` tool）
- 描述（description）作為 routing hint，model 決定何時載入
- 支援 flat markdown、packaged directory、`defineSkill` TypeScript 三種形式
- Skills 是 agent-scoped（subagent 看不到 root 的 skills）

### 3.7 評估系統（Evals）

```typescript
// evals/weather/brooklyn-forecast.eval.ts
import { defineEval } from "eve/evals";
import { includes } from "eve/evals/expect";

export default defineEval({
  description: "Basic message and tool-usage coverage for the weather agent.",
  async test(t) {
    await t.send("What is the weather in Brooklyn?");
    t.completed();
    t.calledTool("get_weather");
    t.check(t.reply, includes("Sunny"));
  },
});
```

- 使用真實 HTTP session 驅動 agent
- 支援 gate（硬性斷言）與 soft（追蹤指標）
- 支援 LLM-as-judge 評分
- 可輸出到 Braintrust

### 3.8 定價模型

Eve 無獨立定價，按使用的 Vercel 資源計費：

| 資源 | 使用情境 |
|------|----------|
| Vercel Functions | Agent route 服務、session 請求、stream 附加、channel webhook、tool 執行 |
| Vercel Workflows | Session/turn/subagent 狀態持久化 |
| Vercel Sandbox | 隔離的 filesystem 與 command 執行 |
| AI Gateway | Model 字串解析與請求路由 |
| Model providers | Token 處理（input、cached、output） |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|----------|--------------|----------------|------------------|
| **LangChain / LangGraph** | 以 chain/graph 抽象定義 agent 流程，提供 tool integration、memory、callback 等模組化元件 | 需熟悉 chain/graph 概念；Python/JS 生態 | 抽象層較厚，debug 困難；版本迭代快，API 不穩定 | 快速 prototyping 多種 agent 模式，但 production 需大量自訂 |
| **OpenAI Assistants API** | OpenAI 託管的 agent 服務：內建 code interpreter、RAG、function calling，state 由 OpenAI 管理 | 僅支援 OpenAI 模型；資料需傳送至 OpenAI 伺服器 | Vendor lock-in；無法自訂執行環境；定價按 token + 工具使用計費 | 最小運維成本的 agent 部署，但靈活性最低 |
| **CrewAI** | 多 agent 協作框架：定義 role-based agent，以 task 為單位分配工作，支援順序/階層流程 | 需設計 agent role 與 task 分解策略 | 多 agent 溝通 overhead；除錯複雜度隨 agent 數增加 | 適合需要多角色分工的場景（如研究 + 寫作 + 審查） |
| **AutoGPT / 自主 agent** | 以「思考-行動-觀察」循環自主執行任務，使用檔案系統作為長期記憶 | 需明確的目標定義與終止條件 | 容易陷入無限循環；token 消耗大；缺乏生產級 durability | 適合探索性任務，不適合需要確定性結果的生產場景 |
| **MCP (Model Context Protocol)** | 標準化 tool 與 resource 的發現/呼叫協議，非框架而是互操作性標準 | 需實作 MCP server/client | 只解決 tool 層的標準化，不處理 durability、multi-channel 等 | 作為 Eve 的 connections 底層協議，與 Eve 互補而非競爭 |

### 切入點差異分析

| 面向 | Eve | LangChain | OpenAI Assistants | CrewAI |
|------|-----|-----------|-------------------|--------|
| **Durability** | 內建（Workflow SDK checkpoint） | 需自行整合（第三方 state store） | 由 OpenAI 管理（黑箱） | 無內建支援 |
| **Sandbox** | 內建（多 backend：Vercel/Docker/microsandbox） | 無內建 | Code interpreter（有限） | 無內建 |
| **Multi-channel** | 內建（Slack/Discord/Teams/Web/API/cron） | 需自行實作 | 僅 API | 需自行實作 |
| **Filesystem-first** | 核心設計原則 | 無 | 無 | 無 |
| **HITL** | 內建（approval + ask_question，durable pause） | 需自行實作 callback | 需自行實作 | 需自行實作 |
| **Evals** | 內建（defineEval + LLM-as-judge） | LangSmith（外部服務） | 無官方方案 | 無官方方案 |
| **Deployment** | Vercel 一鍵部署 + 自託管 | 任意平台（需自行配置） | OpenAI 託管 | 任意平台 |
| **Model 支援** | 任何 AI SDK provider + AI Gateway | 任何 provider | 僅 OpenAI | 任何 provider |

### Eve 的獨特定位

Eve 不是「另一個 agent 框架」，而是 **Vercel 既有 AI 基礎設施的整合層**。它的競爭優勢不在 prompt engineering 或 chain 抽象，而在於：

1. **Durability 作為預設行為**：其他框架需要開發者自行處理 state persistence，Eve 預設就是 durable
2. **Filesystem-first 降低認知負擔**：目錄結構即 agent 架構，新開發者可以直觀理解
3. **Vercel 生態整合**：AI Gateway、Sandbox、Workflows、Connect 開箱即用
4. **多通道原生支援**：同一 agent 同時服務多個平台，無需重寫

### 限制與風險

- **Vendor lock-in 風險**：雖然支援自託管，但核心體驗（Workflow SDK、Sandbox）與 Vercel 平台深度綁定
- **Beta 階段**：API 與行為可能變更，不適合對穩定性要求極高的 production 使用
- **生態尚未成熟**：開源僅 5 天，社群貢獻、第三方整合、最佳實踐均不足
- **學習曲線**：filesystem-first 雖直觀，但 12 個 slot 的完整理解仍需時間
- **定價不透明**：無獨立定價，實際成本需根據使用模式估算
