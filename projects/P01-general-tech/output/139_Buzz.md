# Buzz — 人與 AI Agent 協作工作台

> 基於 Nostr 協議的 self-hostable workspace，讓人類與 Agent 在同一事件流中協作。

---

## 1. 這個技術解決什麼問題？

**Agent 在不同工具間搬運上下文的問題。**

具體來說：

- 人類團隊使用 GitHub Issues、Linear、Slack、Notion 等工具管理需求、程式碼、CI/CD 與任務追蹤
- Agent 被部署為獨立工具（如 GitHub Actions、自訂 bot），各自擁有獨立的上下文視野
- 當 Agent 需要跨工具協作時（例如：從 Issue 理解需求 → 讀取程式碼 → 執行 CI → 提交 PR），必須在不同系統間搬運上下文，導致：
  - 上下文斷裂：Agent A 在 Issue 中的決策無法被 Agent B 在 PR review 中引用
  - 審計困難：操作軌跡分散在不同平台，無法形成完整的事件鏈
  - 權限碎片化：每個工具各自管理 Agent 權限，缺乏統一的身份與授權模型

Buzz 將需求管理、程式碼、CI/CD 與任務追蹤整合於單一介面，讓 Agent 與人類共享同一事件流（event stream），從根本上消除上下文搬運需求。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- 現有專案管理工具（GitHub Issues、Linear、Jira）與 AI 自動化工具之間存在「藩籬」（silo），Agent 無法像人類同事一樣無縫參與工作流程
- Agent 的上下文僅限於單一工具或單一 session，無法跨工具共享
- 缺乏統一的 Agent 身份管理與權限控制機制

### 通用技術背景

**問題根源：工具鏈的橫向擴張 vs 縱向整合不足**

- 軟體開發工具鏈在過去十年快速擴張：Git hosting（GitHub/GitLab）、專案管理（Linear/Jira）、CI/CD（GitHub Actions/CircleCI）、通訊（Slack/Discord）、文檔（Notion/Confluence）
- 每個工具各自為政，API 與事件格式互不相通
- Agent 的興起加劇了這個問題：人類可以同時開啟多個瀏覽器分頁手動搬運上下文，但 Agent 缺乏這種「多視窗手動協調」的能力
- 現有解決方案（如 GitHub Actions、Slack bot）將 Agent 限制在單一工具的 event loop 內，無法跨工具追蹤一個任務的完整生命週期

**Nostr 協議的選擇背景**

- Nostr（Notes and Other Stuff Transmitted by Relays）是一個去中心化的事件傳輸協議
- 每個事件由作者簽名、廣播到 relay，relay 負責儲存與轉發
- Buzz 選擇 Nostr 而非 ActivityPub 或自訂協議，原因：
  - 事件簽名鏈提供內建審計（hash-chain audit trail）
  - Relay 架構天然支援 fan-out（一寫多讀）
  - 去中心化設計允許 self-hosted relay 作為單一真相源
  - NIP（Nostr Implementation Possibilities）標準允許擴展自訂事件類型

---

## 3. 這個技術是如何解決該問題的？

### 3.1 核心架構：Relay 作為單一真相源

```
┌─────────────────────────────────────────────────────────┐
│                     Buzz Workspace                       │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  Human 1  │  │  Human 2  │  │  Agent A │              │
│  │ (client)  │  │ (client)  │  │ (client)  │              │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘              │
│        │               │               │                   │
│        └───────────────┼───────────────┘                   │
│                        │                                   │
│              ┌─────────▼──────────┐                        │
│              │   Nostr Relay      │                        │
│              │  (單一真相源)       │                        │
│              │  Postgres + Redis  │                        │
│              └─────────┬──────────┘                        │
│                        │                                   │
│              ┌─────────▼──────────┐                        │
│              │   Object Store     │                        │
│              │   (MinIO/S3)       │                        │
│              └────────────────────┘                        │
└─────────────────────────────────────────────────────────┘
```

- **Relay** 是 Buzz 的核心，所有事件（Issue 建立、程式碼提交、PR review、Agent 回應）都寫入同一個 Nostr relay
- **Postgres** 儲存事件 metadata 與關係型資料
- **Redis** 提供即時訂閱推送與快取
- **MinIO/S3** 儲存大型附件（檔案、圖片、二進位 artifacts）
- 所有客戶端（人類桌面端、Agent、Web UI）都透過 Nostr 協議與 relay 通訊

### 3.2 事件模型：81 種 Event Kind

Buzz 定義了 81 種 Nostr event kind，涵蓋完整開發工作流：

| 類別 | Event Kind 範例 | 用途 |
|------|----------------|------|
| 核心 | `kind:0` metadata, `kind:1` text note | 使用者身份與基本通訊 |
| 專案 | `kind:31000` project, `kind:31001` project-board | 專案定義與看板 |
| Issue | `kind:31002` issue, `kind:31003` issue-comment | Issue 管理 |
| PR | `kind:31004` pull-request, `kind:31005` pr-review | PR 與 code review |
| CI | `kind:31006` ci-run, `kind:31007` ci-step | CI/CD 管線 |
| Agent | `kind:31008` agent-message, `kind:31009` agent-task | Agent 通訊與任務 |
| Git | `kind:31010` git-commit, `kind:31011` git-branch | Git 操作追蹤 |
| 審計 | `kind:31012` audit-log, `kind:31013` signature | 操作軌跡與簽名 |

每個 event 包含：
- `pubkey`：發送者（人類或 Agent）的公鑰
- `created_at`：時間戳
- `kind`：事件類型
- `tags`：關聯標籤（如 `["e", <parent-event-id>]` 表示回覆關係）
- `content`：事件內容（JSON 或文字）
- `sig`：發送者簽名

### 3.3 12-Step Event Pipeline

事件從寫入到消費經過 12 個步驟：

```
1. 客戶端建立事件 (Client creates event)
2. 客戶端簽名 (Client signs with private key)
3. 發送至 Relay (Client sends to relay)
4. Relay 驗證簽名 (Relay validates signature)
5. Relay 驗證權限 (Relay checks authorization)
6. Relay 寫入 Postgres (Relay persists to DB)
7. Relay 索引事件 (Relay indexes by kind/tags)
8. Relay fan-out 給訂閱者 (Relay fans out to subscribers)
9. 客戶端接收事件 (Client receives event)
10. 客戶端驗證簽名 (Client validates signature)
11. 客戶端處理事件 (Client processes event)
12. 客戶端更新 UI/狀態 (Client updates UI/state)
```

### 3.4 三層 Fan-Out 架構

```
事件寫入 Relay
    │
    ├── Layer 1: Redis Pub/Sub (即時推送)
    │   └── 所有連線中的客戶端即時收到事件
    │
    ├── Layer 2: Postgres LISTEN/NOTIFY (持久訂閱)
    │   └── 斷線重連的客戶端補齊遺漏事件
    │
    └── Layer 3: 輪詢查詢 (Polling)
        └── 新加入的客戶端從頭同步歷史事件
```

### 3.5 Agent 架構：buzz-agent + buzz-dev-mcp

```
┌─────────────────────────────────────────────┐
│              Agent Runtime                    │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │         buzz-agent (core)             │   │
│  │  - Nostr client (事件收發)            │   │
│  │  - Session isolation (session 隔離)    │   │
│  │  - Task queue (任務佇列)              │   │
│  │  - Permission boundary (權限邊界)     │   │
│  └──────────────┬───────────────────────┘   │
│                 │                            │
│  ┌──────────────▼───────────────────────┐   │
│  │       buzz-dev-mcp (MCP server)       │   │
│  │  - MCP tools for dev workflow         │   │
│  │  - Git operations (clone/commit/push) │   │
│  │  - File system access (sandboxed)     │   │
│  │  - Shell execution (sandboxed)        │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

- **buzz-agent**：核心 Agent runtime，負責 Nostr 通訊、session 管理、任務排程
- **buzz-dev-mcp**：基於 MCP（Model Context Protocol）的開發工具集，提供 sandboxed 的 Git/檔案/Shell 操作
- **Session isolation**：每個 Agent task 在獨立 session 中執行，session 之間上下文隔離
- **ACP 協議**：Agent Communication Protocol，定義 Agent 之間的事件格式與互動模式

### 3.6 安全模型

| 安全機制 | 實作方式 |
|---------|---------|
| 身份驗證 | Nostr 公私鑰簽名，每個 event 必須有有效簽名 |
| 授權控制 | Relay 層 ACL（Access Control List），基於 pubkey 與 event kind |
| SSRF 保護 | Agent 的網路請求經過 SSRF 過濾器，限制目標 IP 範圍 |
| 審計追蹤 | Hash-chain audit log，每個 event 引用前一個 event 的 hash |
| 沙箱執行 | Agent 的 shell/file 操作在 sandbox 中執行，限制系統資源 |
| 內容驗證 | Relay 對 event content 做 schema validation |

### 3.7 Forge：內建 Git Hosting

Buzz 內建 Git hosting 功能（代號 Forge），基於 NIP-34 標準：

- **Branch as Channel**：每個 Git branch 對應一個 Nostr channel，branch 上的 commits 自動轉換為 events
- **Merge Flow**：PR 建立 → Approval gate（需要指定數量的 review）→ Merge → Branch channel 自動清理
- **Web of Trust**：基於 Nostr 的 web-of-trust 模型做 code review 權重計算
- **Content Negotiation**：同一個 domain 同時 serve browser（HTML）與 git（git protocol）

### 3.8 七個 Surface（使用者介面）

| Surface | 用途 | 對應傳統工具 |
|---------|------|-------------|
| Stream | 即時事件流（類似 Slack channel） | Slack / Discord |
| Forum | 非同步討論（類似 Discourse） | GitHub Discussions |
| DM | 一對一私訊 | Slack DM |
| Agent | Agent 管理介面 | - |
| Workflow | CI/CD 管線視覺化 | GitHub Actions |
| Search | 全文搜尋所有事件 | - |
| Home | 個人儀表板 | - |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|---------|-------------|---------------|-----------------|
| **Buzz** | Nostr relay 作為單一事件匯流排，所有人類與 Agent 共享同一 event stream | 需 self-host relay（Postgres/Redis/MinIO）；團隊需接受 Nostr 協議；Agent 需實作 Nostr client | 單一 relay 可能成為效能瓶頸；Nostr 事件模型對複雜關係型查詢不友善；81 種 event kind 增加學習成本 | 上下文零搬運；完整審計鏈；統一權限模型 |
| **GitHub Copilot Workspace** | 在 GitHub 生態內提供 Agent 輔助開發，Agent 上下文限於單一 repo | 需使用 GitHub 生態；僅支援 GitHub 內的工作流 | 無法跨工具協作；Agent 上下文仍限於 GitHub 範圍；非 self-hostable | 低導入成本；與現有 GitHub 工作流無縫整合 |
| **Slack + GPT Bot** | 在 Slack 中嵌入 Agent，透過 Slack API 操作外部工具 | 需 Slack workspace；Agent 需自行實作各工具 API 整合 | Agent 上下文限於 Slack thread；跨工具操作需自行串接 API；無統一審計 | 快速部署；團隊已熟悉 Slack 介面 |
| **LangChain + 自訂 Agent 平台** | 使用 LangChain 框架建立 Agent，透過 tool calling 操作外部工具 | 需自行建置 Agent 基礎設施；需自行處理上下文傳遞 | 上下文管理由開發者自行實作；無統一事件儲存；審計需自行建置 | 高度彈性；可整合任意工具；但需大量自訂開發 |
| **Linear + GitHub Actions** | 使用 Linear 管理需求，GitHub Actions 執行自動化，兩者透過 webhook 串接 | 需同時使用 Linear 與 GitHub；需維護 webhook 整合 | 事件流分散在兩個平台；Agent 上下文需跨平台傳遞；審計軌跡不完整 | 使用成熟工具；團隊可能已在使用 |

### 切入點差異分析

| 面向 | Buzz | 傳統工具鏈 |
|------|------|-----------|
| 事件儲存 | 單一 relay（統一儲存） | 分散在各工具資料庫 |
| 上下文範圍 | 整個 workspace（跨專案、跨 repo） | 單一工具 / 單一 repo |
| Agent 身份 | 原生支援（Nostr pubkey） | 需各工具分別設定 bot token |
| 審計完整性 | Hash-chain audit（不可篡改） | 各工具各自 audit log，無法交叉驗證 |
| 部署模式 | Self-hosted | SaaS（無法自控） |
| 協議標準 | Nostr（開放協議） | 各工具私有 API |
| 學習成本 | 高（新協議 + 新工具） | 低（沿用既有工具） |

### 關鍵權衡

- Buzz 的「統一事件流」設計解決了上下文搬運問題，但代價是團隊必須接受 Nostr 協議與全新的工具介面
- 傳統工具鏈的「最佳組合」策略（Linear + GitHub + Slack）導入成本低，但 Agent 協作效率受限於工具間的 API 縫合
- Buzz 的 self-hosted 模式提供資料主權，但增加了運維負擔（Postgres/Redis/MinIO/Nostr relay）
- 81 種 event kind 的設計提供了細粒度的事件分類，但也意味著 protocol 層的複雜度較高
