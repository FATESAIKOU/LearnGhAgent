# 170_R1_step2-plan_C1.md

## 狀況理解

Step 2 的第一個 sub-step C1：取得 MCP 生態的 repo metadata 與主要文件。目標是建立基礎資訊層，包含：(1) MCP protocol 官方資源概覽；(2) 主流 AI coding agent 對 MCP 的支援方式；(3) 初步盤點生產可用的 MCP server。後續 C2 將補足更多 server 細節與分類。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 modelcontextprotocol.io 官方站 | 取得 MCP protocol 概述、架構、生態 | 理解 MCP 定位與核心概念 | 成功：MCP 是 Anthropic 發起、現由 Linux Foundation 託管的開放標準，定位為「AI 的 USB-C」，支援 10 種語言 SDK |
| 讀取 github.com/modelcontextprotocol 組織頁 | 取得組織 repo 清單與 stars 數據 | 了解官方維護的專案規模 | 成功：49.4k followers，42 repos，核心 repos 含 servers(89.1k⭐)、python-sdk(23.8k⭐)、typescript-sdk(13k⭐)、inspector(10.6k⭐) |
| 讀取 github.com/modelcontextprotocol/servers | 取得官方參考 server 清單 | 了解官方提供的 reference server | 成功：7 個 active reference server（Everything/Fetch/Filesystem/Git/Memory/SequentialThinking/Time），13 個 archived server |
| 讀取 registry.modelcontextprotocol.io | 了解 MCP Registry 生態 | 確認是否有公開的 server 目錄 | 成功：存在官方 Registry，但頁面為動態載入，無法直接爬取完整清單 |
| 讀取 Claude Code MCP 文件 | 了解 Claude Code 的 MCP 支援程度 | 確認 agent 支援方式 | 成功：原生支援，支援 HTTP/SSE/stdio/WebSocket 四種 transport，OAuth 2.0，plugin MCP，channels，tool search |
| 讀取 opencode-ai/opencode README | 了解 opencode 的 MCP 支援 | 確認 agent 支援方式 | 成功：原生支援（mcpServers 設定），支援 stdio 與 SSE，但專案已 archive（移至 Crush） |
| 讀取 VS Code MCP 文件 | 了解 VS Code Copilot 的 MCP 支援 | 確認 agent 支援方式 | 成功：原生支援，有完整 MCP server 管理 UI，支援 sandbox、MCP Apps、extension gallery |
| 讀取 cursor.com MCP 文件 | 了解 Cursor 的 MCP 支援 | 確認 agent 支援方式 | 成功：原生支援，有 MCP 設定頁面 |
| 讀取 microsoft/playwright-mcp | 取得 browser automation MCP server 資訊 | 盤點生產可用 server | 成功：35.7k⭐，TypeScript，支援 15+ 種 MCP client，含完整文件與 CLI 參數 |
| 讀取 bytebase/dbhub | 取得 database MCP server 資訊 | 盤點生產可用 server | 成功：3.3k⭐，TypeScript，支援 Postgres/MySQL/SQL Server/MariaDB/SQLite，零依賴，token efficient |
| 讀取 run-llama/mcp-server-llamacloud | 取得 RAG/retrieval MCP server 資訊 | 盤點生產可用 server | 成功：87⭐，TypeScript，連接 LlamaCloud managed index，功能較單一 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| MCP protocol 定位 | 官方站描述 | 開放標準，Linux Foundation 託管，10 SDKs，支援 HTTP/SSE/stdio/WebSocket |
| Claude Code MCP 支援 | 官方文件 | 原生支援，完整 transport 支援，OAuth，plugin，channels |
| opencode MCP 支援 | README | 原生支援（mcpServers），但專案已 archive |
| VS Code MCP 支援 | 官方文件 | 原生支援，完整管理 UI，sandbox，MCP Apps |
| Cursor MCP 支援 | 官方文件 + Playwright README | 原生支援 |
| Codex MCP 支援 | Playwright README | 原生支援（codex mcp add） |
| GitHub Copilot CLI MCP 支援 | Playwright README | 原生支援（/mcp add） |
| 已盤點生產可用 server | 3 個（Playwright/DBHub/LlamaCloud）+ 官方 reference servers | 不足 5-10 個，需 C2 補查更多 community server |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研範圍 | 僅官方 server / 含 community server | 含 community server | PR 要求「非玩具、有社群採用」，community server 更符合 |
| Agent 支援調查方式 | 逐一讀取各 agent 官方文件 / 依賴 Playwright README 的 client 清單 | 兩者並行 | 官方文件提供深度，Playwright README 提供廣度（列出 15+ client） |
| Server 盤點數量 | 先查 3-5 個 / 一次查 10 個 | 先查 3 個，C2 補查 | 避免單次 fetch 過多資料被截斷，C2 可針對性補查 |
| 是否需要 CDP | 一般 web fetch / CDP (port 9222) | 一般 web fetch | 所有目標頁面均可正常存取，無 CAPTCHA 阻擋 |
