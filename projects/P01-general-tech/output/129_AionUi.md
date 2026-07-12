# AionUi 技術分析報告

> 調研標的：https://github.com/iofficeai/aionui
> 版本：v2.1.33 | License：Apache-2.0 | Stars：29.8k | 主要語言：TypeScript (89%)

---

## 1. 這個技術解決什麼問題？

**AionUi 解決的問題是：多個 AI agent（CLI agent、內建 agent）缺乏一個統一的桌面協作（Cowork）平台，導致使用者無法在同一介面中同時管理、排程、遠端存取多個 AI agent，也無法讓 agent 之間協同工作。**

具體而言，AionUi 針對以下子問題：

- **碎片化的 agent 管理**：使用者若同時使用 Claude Code、Codex、Gemini CLI、OpenClaw 等 CLI agent，需在不同終端機視窗間切換，無統一介面
- **缺乏 agent 間協作機制**：單一 agent 能力有限，但市面上缺乏讓多個 agent 以「團隊模式」分工協作的框架
- **無法排程自動化**：CLI agent 需手動觸發，無法設定 cron 排程讓 agent 在指定時間自動執行任務
- **缺乏遠端存取**：桌面 agent 無法從手機或瀏覽器遠端操控
- **Office 文件生成門檻高**：AI agent 生成 PPT/Word/Excel 需依賴複雜的程式碼或第三方工具，缺乏內建支援

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **Claude Code 等 CLI agent 僅限 macOS**：Anthropic 的 Claude Code（原 Claude Cowork）只支援 macOS，且僅綁定 Claude 模型，無法使用其他 LLM 提供者
- **CLI agent 無 GUI 介面**：Claude Code、Codex、Gemini CLI 等均為終端機工具，操作門檻高，缺乏可視化操作介面
- **無統一 agent 管理**：每個 CLI agent 各自獨立，無中央管理面板，無法同時查看多個 agent 的狀態與輸出
- **無排程機制**：CLI agent 設計為互動式工具，不支援背景排程執行

### 通用技術背景（文章中未明確提及，但為必要脈絡）

- **LLM API 生態碎片化**：OpenAI、Anthropic、Google、AWS Bedrock、Ollama 等 30+ 平台各有不同 API 規格，使用者需分別管理 API key 與 endpoint
- **MCP（Model Context Protocol）標準化不足**：雖然 Anthropic 提出 MCP 作為工具擴充標準，但各 agent 對 MCP 的支援程度不一，缺乏統一管理
- **Electron 作為跨平台桌面框架的成熟**：Electron 讓 Web 技術（React）可打包為跨平台桌面應用，為 AionUi 的技術可行性提供基礎
- **Rust 作為高效能後端語言的興起**：AionCore（Rust 後端）提供本地 agent 引擎，效能優於純 Node.js 方案

---

## 3. 這個技術是如何解決該問題的？

AionUi 採用 **Electron 前端 + Rust 後端（AionCore）** 的雙 repo 架構，透過以下機制解決前述問題：

### 3.1 架構總覽

```
┌─────────────────────────────────────────────────┐
│                  AionUi (Electron)               │
│  ┌───────────────────────────────────────────┐   │
│  │          Renderer (React 19)              │   │
│  │  - 聊天介面 / 預覽面板 / 設定頁面         │   │
│  │  - 21 個內建助理 / 技能管理               │   │
│  └──────────────┬────────────────────────────┘   │
│                 │ IPC (contextBridge)              │
│  ┌──────────────┴────────────────────────────┐   │
│  │          Main Process (Node.js)            │   │
│  │  - Bridge (IPC handlers)                   │   │
│  │  - Services (Cron, MCP, Agent)             │   │
│  │  - Database (better-sqlite3)               │   │
│  │  - Channels (Telegram/Lark/DingTalk/WeChat)│   │
│  │  - WebServer (WebUI)                       │   │
│  └──────────────┬────────────────────────────┘   │
│                 │ 子程序啟動                       │
│  ┌──────────────┴────────────────────────────┐   │
│  │     AionCore (Rust 後端二進位)              │   │
│  │  - 內建 agent 引擎                         │   │
│  │  - ACP (Agent Communication Protocol)      │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 3.2 核心機制

#### (1) 內建 Agent 引擎（AionCore）

- 以 Rust 實作的本地 agent 引擎，隨 AionUi 安裝即附帶
- 支援 30+ LLM 平台（Gemini、Claude、OpenAI、DeepSeek、Ollama 等）
- 提供檔案讀寫、網頁搜尋、圖片生成、MCP 工具等完整 agent 能力
- 使用者只需貼上 API key 即可使用，無需額外安裝 CLI 工具

#### (2) 多 Agent 整合（ACP 協定）

- **ACP（Agent Communication Protocol）**：AionUi 自定義的 agent 間通訊協定，用於協調多個 agent
- 自動偵測已安裝的 CLI agent（Claude Code、Codex、Hermes Agent、OpenClaw 等 20+）
- 統一介面：所有 agent 在同一桌面視窗中操作，無需切換終端機
- 並行會話：多個 agent 可同時執行，各自擁有獨立上下文

#### (3) Team Mode（團隊模式）

```
使用者指令
    │
    ▼
┌──────────┐
│  Leader  │ ← 接收指令、拆解子任務、分配給 Teammate
│  Agent   │
└────┬─────┘
     │ 透過 Team MCP Server 分配任務
     ├────────────────────────────────────┐
     │                                    │
     ▼                                    ▼
┌──────────┐                    ┌──────────┐
│ Teammate │  ... (並行執行)    │ Teammate │
│ Agent 1  │                    │ Agent N  │
└──────────┘                    └──────────┘
     │                                    │
     └────────── 非同步信箱 ──────────────┘
                          │
                          ▼
                    共享任務面板 (Shared Task Board)
```

- Leader agent 接收使用者指令，拆解為子任務
- 透過 Team MCP Server 分配給多個 Teammate agent 並行執行
- 非同步信箱機制讓 agent 間可交換結果
- 共享工作目錄，所有 agent 可讀寫同一資料夾

#### (4) 排程任務（Cron）

- 三種排程模式：標準 cron 表達式（含時區）、固定間隔（每 N 分鐘/小時）、一次性觸發
- 任務可綁定至特定對話，保留上下文歷史
- 支援 keep-awake（防止系統休眠）與喚醒後遺漏觸發偵測
- 每個任務可獨立設定模型、工作目錄、推理強度

#### (5) 遠端存取

- **WebUI 模式**：Electron 啟動 HTTP 伺服器，可從瀏覽器/手機存取
- **聊天平台整合**：Telegram、Lark（飛書）、DingTalk（釘釘）、WeChat（微信）
- 支援 LAN、跨網路、伺服器部署

#### (6) Office 文件生成（OfficeCLI）

- 透過 `@office-ai/aioncli-core` 套件，支援 PPT（Morph 動畫）、Word（.docx）、Excel（.xlsx/.xlsm/.csv）
- 21 個內建專業助理，涵蓋 PPT 製作、論文寫作、財務模型、儀表板等場景

#### (7) 三層技能系統

| 技能層級 | 來源 | 說明 |
|---------|------|------|
| Builtin | AionUi 內建 | pptx、docx、pdf、xlsx、mermaid 等 |
| Custom | 使用者自訂 | 放在 `skills/` 目錄下 |
| Extension | 第三方擴充 | 透過 Extension SDK 貢獻 |

- 每個對話可獨立啟用/停用技能
- MCP 工具統一管理：一次設定，自動同步至所有 agent

#### (8) 預覽面板

支援 10+ 檔案格式即時預覽：PDF、Word、Excel、PPT、程式碼、Markdown、圖片、HTML、Diff 等，無需切換應用程式。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表：替代方案對照

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|---------|-------------|---------------|-----------------|
| **Claude Code (原 Claude Cowork)** | Anthropic 官方 CLI agent，在終端機中與 Claude 協作 | macOS 系統、Claude 訂閱 ($100/月) | 僅支援 Claude 模型、無排程、無遠端存取、僅 macOS | 單一 agent 深度協作，但生態封閉 |
| **OpenClaw** | 開源 CLI agent，支援多模型後端 | 手動安裝 CLI、自行設定模型 | 無 GUI、無多 agent 協作、無排程 | 輕量級 CLI agent，可自選模型 |
| **Hermes Agent** | 開源 agent 框架，強調工具使用與自主決策 | 手動安裝、Python 環境 | 無桌面 GUI、無多 agent 管理 | 強大的工具使用能力，但缺乏平台化 |
| **LangChain / LangGraph** | 框架層級的 agent 編排，支援多 agent 圖形化工作流 | 需程式開發能力、Python/TypeScript 環境 | 非終端使用者產品、需自行建置 UI | 高度靈活的工作流編排，但開發成本高 |
| **AutoGPT / AgentGPT** | 自主 agent 框架，可設定目標後自動執行 | 需 API key、自行部署 | 缺乏桌面整合、無 Office 文件生成 | 自主任務執行，但缺乏協作與平台化 |
| **Copilot for X (GitHub Copilot / Cursor)** | IDE 內嵌 AI 輔助，專注程式碼生成 | 特定 IDE（VS Code、Cursor、JetBrains） | 僅限 IDE 場景、無通用 agent 能力 | 深度 IDE 整合，但場景單一 |

### 切入點差異分析

- **AionUi vs Claude Code**：AionUi 是 Claude Code 的「全模型、跨平台、開源增強版」。Claude Code 僅 macOS + Claude 模型，AionUi 擴展至 Windows/Linux + 30+ 模型 + 排程 + 遠端存取
- **AionUi vs OpenClaw/Hermes**：AionUi 提供 GUI 介面與多 agent 管理，而 OpenClaw/Hermes 僅為 CLI 工具。AionUi 可整合這些 CLI agent 作為其一
- **AionUi vs LangChain**：LangChain 是開發者框架，需自行建置 UI 與部署；AionUi 是終端使用者產品，開箱即用
- **AionUi vs AutoGPT**：AutoGPT 專注單一 agent 自主執行；AionUi 強調多 agent 協作（Team Mode）與桌面整合
- **AionUi vs Copilot**：Copilot 鎖定 IDE 場景；AionUi 是通用桌面 agent 平台，涵蓋文件生成、檔案管理、排程等非程式碼場景
