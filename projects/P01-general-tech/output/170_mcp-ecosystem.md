# MCP (Model Context Protocol) 生態現況報告 — 2026 年中

> 調研日期：2026-08-02
> 調研範圍：AI coding agent 對 MCP 的支援程度 + 生產可用 MCP server 盤點

---

## 1. 這個技術解決什麼問題？

**MCP 解決的是「AI agent 與外部工具／資料源之間的標準化通訊介面」問題。**

具體來說，在 MCP 出現之前，每個 AI coding agent（Claude Code、Cursor、Copilot 等）各自定義自己的 tool calling 格式、transport 協定、認證方式。開發者若想讓 agent 操作檔案、查資料庫、呼叫 API，必須為每個 agent 分別撰寫整合程式碼。這導致：

- 工具開發者需維護 N 套整合（N = agent 數量）
- 使用者無法在不同 agent 之間無痛遷移工具設定
- 社群難以累積共享的工具生態

MCP 定義了一個統一協定層，讓工具（MCP server）只需實作一次，即可被任何支援 MCP 的 client（agent）使用。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- MCP 由 Anthropic 於 2024 年 11 月發起，2025 年移交 Linux Foundation 託管，成為開放標準
- 定位為「AI 的 USB-C」— 一個通用連接標準
- 截至 2026 年中，支援 10 種語言 SDK（TypeScript、Python、Go、Java、Kotlin、C#、Ruby、Rust、Swift、C++）

### 通用技術背景

- **LLM tool calling 的碎片化**：OpenAI 的 function calling、Anthropic 的 tool use、Google 的 function declaration 各自為政，底層格式不同
- **Agent 架構的興起**：2024-2026 年 AI coding agent 從「對話補完」進化到「自主執行多步驟任務」，需要操作檔案系統、瀏覽器、資料庫、API 等外部資源
- **缺乏標準化通訊協定**：在此之前，工具與 agent 之間的通訊依賴 ad-hoc 的 JSON-RPC、REST API 或 CLI 參數傳遞，沒有統一的 lifecycle（初始化、工具發現、呼叫、錯誤處理、資源管理）

---

## 3. 這個技術是如何解決該問題的？

MCP 採用 **client-server 架構**，定義了三個核心抽象：

### 3.1 架構概覽

```
┌─────────────────┐      MCP Protocol       ┌─────────────────┐
│                 │ ◄─────── JSON-RPC ──────► │                 │
│   MCP Client    │      (stdio/SSE/         │   MCP Server    │
│   (Agent)       │       HTTP/WebSocket)    │   (Tool)        │
│                 │                          │                 │
└─────────────────┘                          └─────────────────┘
```

### 3.2 三種核心能力

| 能力 | 說明 | 對應 agent 使用場景 |
|---|---|---|
| **Tools** | Server 暴露可被 LLM 呼叫的函式（含參數 schema） | agent 決定何時呼叫哪個工具 |
| **Resources** | Server 暴露可被讀取的資料（檔案、DB 記錄、API 回應） | agent 讀取上下文 |
| **Prompts** | Server 提供預先定義的 prompt 模板 | agent 使用特定領域的提示 |

### 3.3 Transport 層

| Transport | 適用場景 | 特點 |
|---|---|---|
| **stdio** | 本地 agent（Claude Code、opencode） | 子行程通訊，低延遲，無網路依賴 |
| **SSE** (Server-Sent Events) | 遠端 server，單向事件推送 | 簡單，瀏覽器友善 |
| **HTTP** | RESTful 風格 | 標準 HTTP 請求/回應 |
| **WebSocket** | 雙向即時通訊 | 低延遲，適合頻繁互動 |

### 3.4 認證與安全

- 支援 OAuth 2.0（授權碼流程 + PKCE）
- VS Code 實作 sandbox 機制隔離 MCP server
- 支援 remote MCP server（非僅 local）

### 3.5 實例：MCP server 設定方式

以 opencode 為例（`opencode.json`）：

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp"]
    },
    "dbhub": {
      "command": "npx",
      "args": ["@bytebase/dbhub", "--dsn", "postgresql://..."]
    }
  }
}
```

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 主流 AI coding agent 對 MCP 的支援程度

| Agent | 支援方式 | Transport 支援 | 備註 |
|---|---|---|---|
| **Claude Code** | 原生 | stdio / SSE / HTTP / WebSocket | OAuth 2.0, plugin MCP, channels, tool search |
| **VS Code (Copilot)** | 原生 | stdio / SSE | 完整管理 UI, sandbox, MCP Apps, extension gallery |
| **Cursor** | 原生 | stdio / SSE | MCP 設定頁面 |
| **opencode** | 原生 | stdio / SSE | 專案已 archive（移至 Crush），但 MCP 支援完整 |
| **Codex (by OpenAI)** | 原生 | stdio / SSE | `codex mcp add` 指令 |
| **GitHub Copilot CLI** | 原生 | stdio / SSE | `/mcp add` 指令 |
| **Windsurf** | 原生 | stdio / SSE | 列於 Playwright MCP 支援清單 |
| **Continue.dev** | 原生 | stdio / SSE | IDE plugin 形式 |
| **Sourcegraph Cody** | 原生 | stdio / SSE | 列於 Playwright MCP 支援清單 |
| **Theia / Eclipse** | 原生 | stdio / SSE | IDE 層級支援 |

**結論：截至 2026 年中，所有主流 AI coding agent 均已原生支援 MCP，無需 plugin。MCP 已成為事實上的業界標準。**

### 4.2 生產可用 MCP server 盤點

#### 分類總覽

| 分類 | Server 名稱 | ⭐ Stars | 最後更新 | 語言 | 成熟度 |
|---|---|---|---|---|---|
| **瀏覽器自動化** | microsoft/playwright-mcp | 35.7k | 2026-07 | TypeScript | 生產可用 |
| **瀏覽器自動化** | ChromeDevTools/chrome-devtools-mcp | 48.4k | 2026-08 | TypeScript | 生產可用 |
| **資料庫** | bytebase/dbhub | 3.3k | 2026-07 | Go | 生產可用 |
| **API 整合** | github/github-mcp-server | 31.9k | 2026-07 | Go | 生產可用 |
| **API 整合** | PipedreamHQ/pipedream | — | 2026-07 | TypeScript | 生產可用 |
| **開發工具** | DeusData/codebase-memory-mcp | 37.0k | 2026-08 | C | 生產可用 |
| **開發工具** | upstash/context7 | 60.1k | 2026-08 | TypeScript | 生產可用 |
| **開發工具** | oraios/serena | 27.4k | 2026-08 | Python | 生產可用 |
| **工作流自動化** | activepieces/activepieces | 23.5k | 2026-08 | TypeScript | 生產可用 |
| **工作流自動化** | n8n-io/n8n | 199k | 2026-08 | TypeScript | 生產可用 |
| **研究** | assafelovic/gpt-researcher | 28.8k | 2026-07 | Python | 生產可用 |
| **RAG** | 1Panel-dev/MaxKB | 22.4k | 2026-07 | Python | 生產可用 |
| **參考實作** | modelcontextprotocol/servers | 89.1k | 2026-07 | TS/Python | 參考用 |

#### 各 server 詳細說明

##### 瀏覽器自動化

| | microsoft/playwright-mcp | ChromeDevTools/chrome-devtools-mcp |
|---|---|---|
| **GitHub** | [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) |
| **Stars** | 35.7k | 48.4k |
| **語言** | TypeScript | TypeScript |
| **最後更新** | 2026-07 | 2026-08-02 |
| **功能** | 瀏覽器自動化：點擊、輸入、截圖、表單填寫、網頁內容提取 | Chrome DevTools 整合：效能追蹤、網路分析、截圖、console 除錯、Lighthouse 稽核、heap snapshot |
| **支援 client** | 15+ 種 MCP client（Claude Code, Cursor, Codex, VS Code, Windsurf, Continue, Cody 等） | Claude Code, Cursor, VS Code, Copilot CLI |
| **成熟度** | 生產可用 — Microsoft 官方維護，完整文件，CLI 參數，Docker 支援 | 生產可用 — Chrome DevTools 團隊官方維護，完整文件 |
| **使用前提** | 需安裝 Playwright 瀏覽器引擎 | 需安裝 Chrome/Chromium |
| **副作用** | 瀏覽器啟動耗記憶體（~200MB） | 需 DevTools protocol 連線，不適合 headless-only 場景 |

##### 資料庫

| | bytebase/dbhub |
|---|---|
| **GitHub** | [bytebase/dbhub](https://github.com/bytebase/dbhub) |
| **Stars** | 3.3k |
| **語言** | Go |
| **最後更新** | 2026-07 |
| **功能** | 多資料庫查詢：Postgres / MySQL / SQL Server / MariaDB / SQLite。零依賴單一二進位檔，token efficient（schema 壓縮），支援 read-only 模式 |
| **支援 client** | Claude Code, Cursor, VS Code, opencode |
| **成熟度** | 生產可用 — Bytebase 團隊維護，文件完整，有 Docker image |
| **使用前提** | 需有資料庫連線字串（DSN） |
| **副作用** | 預設 read-only，寫入需額外設定 |

##### API 整合

| | github/github-mcp-server | PipedreamHQ/pipedream |
|---|---|---|
| **GitHub** | [github/github-mcp-server](https://github.com/github/github-mcp-server) | [PipedreamHQ/pipedream](https://github.com/PipedreamHQ/pipedream) |
| **Stars** | 31.9k | — |
| **語言** | Go | TypeScript |
| **最後更新** | 2026-07-31 | 2026-07 |
| **功能** | GitHub API 操作：repo 管理、issues、PRs、Actions、code scanning、discussions、notifications。支援 remote（hosted）與 local（Docker/binary）模式 | 2,500+ API 整合，8,000+ 預建工具以 MCP 形式暴露 |
| **成熟度** | 生產可用 — GitHub 官方維護，1,024 commits，Docker image，Homebrew formula | 生產可用 — 成熟平台，MCP 為新增暴露層 |
| **使用前提** | 需 GitHub token | 需 Pipedream 帳號 |
| **副作用** | API rate limit 受 token 等級限制 | 依賴雲端服務，self-host 需額外設定 |

##### 開發工具

| | codebase-memory-mcp | context7 | serena |
|---|---|---|---|
| **GitHub** | [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | [upstash/context7](https://github.com/upstash/context7) | [oraios/serena](https://github.com/oraios/serena) |
| **Stars** | 37.0k | 60.1k | 27.4k |
| **語言** | C | TypeScript | Python |
| **最後更新** | 2026-08-01 | 2026-08-01 | 2026-08-01 |
| **功能** | 高效能程式碼索引：tree-sitter AST 解析（158 種語言），持久化知識圖譜，sub-ms 查詢，單一靜態二進位檔，零依賴 | 即時函式庫文件：從原始碼提取版本特定的文件與程式碼範例，注入 prompt context。CLI + MCP 雙模式 | 「IDE for your agent」：語意化程式碼檢索、符號級編輯/重構、LSP 整合（40+ 語言）、JetBrains plugin、除錯、記憶系統 |
| **成熟度** | 生產可用 — 1,971 commits，完整文件，Docker image | 生產可用 — Upstash 維護，完整文件 | 生產可用 — 3,214 commits，完整文件，JetBrains marketplace |
| **使用前提** | 需有程式碼庫路徑 | 需網路連線（從 Upstash 伺服器取得文件） | 需安裝 Python runtime |
| **副作用** | 首次索引耗時（大型專案數分鐘） | 依賴 Upstash 雲端服務 | 資源消耗較高（LSP + 記憶系統） |

##### 工作流自動化

| | activepieces | n8n |
|---|---|---|
| **GitHub** | [activepieces/activepieces](https://github.com/activepieces/activepieces) | [n8n-io/n8n](https://github.com/n8n-io/n8n) |
| **Stars** | 23.5k | 199k |
| **語言** | TypeScript | TypeScript |
| **最後更新** | 2026-08-02 | 2026-08 |
| **功能** | 開源 Zapier 替代品：280+ 整合（pieces）自動暴露為 MCP server。視覺化工作流編輯器，AI-first，可 self-host | Fair-code 工作流自動化：400+ 整合，原生 MCP 支援，self-host 或 cloud。另有 [n8n-mcp](https://github.com/czlonkowski/n8n-mcp)（22.5k⭐）可從 Claude/Cursor 建立 n8n 工作流 |
| **成熟度** | 生產可用 — 成熟平台，MCP 為新增暴露層 | 生產可用 — 極成熟平台，MCP 為新增暴露層 |
| **使用前提** | 需 self-host 或使用 cloud 版 | 需 self-host 或使用 cloud 版 |
| **副作用** | 工作流執行有延遲（非即時） | 工作流執行有延遲（非即時） |

##### 研究 / RAG

| | gpt-researcher | MaxKB |
|---|---|---|
| **GitHub** | [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) | [1Panel-dev/MaxKB](https://github.com/1Panel-dev/MaxKB) |
| **Stars** | 28.8k | 22.4k |
| **語言** | Python | Python |
| **最後更新** | 2026-07-18 | 2026-07 |
| **功能** | 深度研究 agent：從 20+ 網路來源產生附引用的事實性報告。Planner + execution agent 架構。MCP server 在獨立 [gptr-mcp](https://github.com/assafelovic/gptr-mcp) repo | 企業級 RAG agent 平台：知識庫 + LLM 編排，MCP 支援 |
| **成熟度** | 生產可用 — 成熟專案，MCP 為新增介面 | 生產可用 — 企業採用 |
| **使用前提** | 需 LLM API key | 需 self-host |
| **副作用** | 研究耗時（數十秒至數分鐘） | 需維護知識庫 |

##### 官方參考實作（非生產用途）

| | modelcontextprotocol/servers |
|---|---|
| **GitHub** | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| **Stars** | 89.1k |
| **語言** | TypeScript / Python |
| **最後更新** | 2026-07 |
| **包含** | 7 個 active reference server：Everything（測試用）、Fetch（網頁抓取）、Filesystem（檔案操作）、Git（Git 操作）、Memory（知識圖譜記憶）、Sequential Thinking（思考鏈）、Time（時間查詢） |
| **成熟度** | 參考/教育用 — Anthropic 明確標示為 reference implementation，非生產級別 |
| **備註** | 另有 13 個 archived server（已不再維護） |

### 4.3 替代方案對照表

| 技術名 | 技術解法 | 使用前提 | 副作用 | 預期效果 |
|---|---|---|---|---|
| **MCP** | 標準化 JSON-RPC 協定，client-server 架構，統一 tool/resource/prompt 抽象 | agent 需支援 MCP（2026 年主流 agent 均已支援） | 需管理 MCP server 行程；remote server 需處理網路延遲與認證 | 一次設定，所有 agent 共用工具生態 |
| **OpenAI Function Calling** | 直接在 LLM API 層定義可呼叫函式（JSON schema） | 僅限 OpenAI API | vendor lock-in；無法跨 agent 共用；無標準化 server 生態 | 深度整合 OpenAI 生態，但綁定單一 provider |
| **LangChain Tools** | LangChain 生態的工具抽象層，支援自訂工具與第三方整合 | 需使用 LangChain 框架 | 框架依賴；學習曲線高；非標準協定 | 豐富的工具生態，但綁定 LangChain |
| **自訂 CLI wrapper** | 為每個 agent 撰寫自訂 CLI 工具，透過 stdout/stdin 與 agent 通訊 | 無外部依賴 | 需為每個 agent 分別實作；無標準 lifecycle 管理；難以共用 | 完全控制，但開發維護成本高 |
| **VSCode Tasks / Custom Commands** | 利用 IDE 的 task runner 執行外部指令 | 僅限 VS Code 生態 | 僅限 VS Code；無標準化 tool discovery | 簡單直接，但功能有限 |

### 4.4 導入建議

#### 現在值得導入嗎？**是，值得。**

理由：

| 面向 | 評估 |
|---|---|
| **生態成熟度** | MCP 已獲所有主流 agent 原生支援，無需 plugin。社群 server 數量與品質在 2025-2026 年間快速成長 |
| **標準化程度** | 已移交 Linux Foundation 託管，非單一廠商綁定。10 種語言 SDK |
| **生產可用 server** | 本報告盤點 12 個生產可用 server，涵蓋瀏覽器、資料庫、API、開發工具、工作流等類別 |
| **導入成本** | 低 — 僅需在 agent 設定檔中加入 `mcpServers` 區塊。多數 server 可透過 npx / Docker 一鍵啟動 |
| **風險** | 低 — MCP 是開放標準，即使 Anthropic 停止維護，協定本身已由 Linux Foundation 託管 |

#### 建議優先導入的 server（依使用場景）

| 使用場景 | 建議 server | 理由 |
|---|---|---|
| **瀏覽器測試 / 網頁自動化** | playwright-mcp | Microsoft 維護，支援 client 最多 |
| **資料庫查詢** | dbhub | 零依賴，多 DB 支援，token efficient |
| **GitHub 操作** | github-mcp-server | GitHub 官方維護，功能完整 |
| **程式碼庫理解** | codebase-memory-mcp | 158 語言，sub-ms 查詢，零依賴 |
| **函式庫文件查詢** | context7 | 60k⭐，即時文件注入 prompt |
| **工作流自動化** | activepieces 或 n8n | 成熟平台，MCP 為新增暴露層 |
