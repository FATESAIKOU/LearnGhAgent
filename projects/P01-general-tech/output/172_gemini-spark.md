# Gemini Spark 技術分析報告

> 調研日期：2026-08-02
> 資料來源：Google 官方支援文件（support.google.com/gemini/answer/17094507）、DataCamp 分析、BuildFastWithAI 技術分析、影片文字稿（YouTube 暢的科技工坊）

---

## 1. 這個技術解決什麼問題？

Gemini Spark 解決的是「**Google 生態使用者需要跨應用、持續運行的 AI agent，來自動化處理 Google Workspace 中的重複性任務**」這個問題。

具體來說，它針對以下場景：

- **跨應用資料彙整**：從 Gmail、Google Calendar、Google Drive、Google Search 等多個 Google 服務中提取資料，彙整成一份報告或文件
- **背景執行任務**：使用者不需保持網頁開啟，任務在雲端 24/7 執行，完成後推播通知
- **重複流程固化**：將一次性的任務流程（Task）封裝成可重複使用的 Skills，或設定定時執行的 Schedules
- **跨對話記憶**：透過 Personal Intelligence 記住使用者的偏好與習慣，減少重複說明

**問題描述的模糊之處**：影片與官方文件未明確定義 Gemini Spark 與既有 Google 服務（如 Gmail 篩選器、Google Apps Script、Google Assistant Routine）的邊界。實際上 Gemini Spark 是這些既有能力的「AI agent 化封裝」，而非全新的基礎能力。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- Google 在 2026/5 Google I/O 大會上發布 Gemini Spark
- 最初僅開放給 Gemini Ultra 訂閱用戶，後調整為 Gemini Pro 以上 + 美國地區
- 底層使用 Gemini 3.5 Flash 模型
- 部署在雲端（Google 稱為「Antigravity harness」），可 24/7 運行

### 通用技術背景

**問題發生的根源：Google Workspace 使用者長期面臨的「應用孤島」困境**

| 問題 | 說明 |
|------|------|
| 應用孤島 | Gmail、Calendar、Drive、Docs、Sheets 各自獨立，使用者需手動切換與搬運資料 |
| 自動化門檻 | Google Apps Script（GAS）可串接，但需撰寫 JavaScript 程式碼，非技術使用者無法使用 |
| 無背景執行 | 一般 AI chatbot 需保持連線，無法在關閉頁面後繼續執行任務 |
| 無跨對話記憶 | 每次對話都是全新開始，無法累積使用者偏好與習慣 |
| 無流程固化 | 重複性任務每次需重新下達相同指令 |

**歷史脈絡**：Google 在 2024-2026 年間逐步推出 Gemini 系列產品（Gemini Chatbot → Gemini Pro/Ultra → Gemini Spark），從對話式 AI 進化到 agent 式 AI。同期競爭對手 Anthropic（Claude Cowork）與 OpenAI（ChatGPT Agent）也在做類似轉型。Gemini Spark 是 Google 對此趨勢的回應，且刻意綁定 Google 生態系作為差異化優勢。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 整體架構

```
┌─────────────────────────────────────────────────────┐
│                   使用者介面層                          │
│         Web / App / MacOS（目前僅 Web 可用）            │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│                  Agent 核心層                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │  Task    │  │  Skills  │  │Schedule  │           │
│  │ (任務)   │  │ (技能)   │  │ (排程)   │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
│       │              │              │                 │
│  ┌────▼──────────────▼──────────────▼─────┐         │
│  │        工作流引擎（自動生成執行計畫）        │         │
│  └────────────────┬────────────────────────┘         │
│                    │                                  │
│  ┌─────────────────▼────────────────────────┐         │
│  │      Gemini 3.5 Flash 模型層             │         │
│  └─────────────────┬────────────────────────┘         │
└─────────────────────┼─────────────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────────────┐
│                 工具層（Connected Apps）                 │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐  │
│  │Gmail │ │Calendar│ │Drive │ │Search│ │MCP (OAuth)│  │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────────┘  │
└───────────────────────────────────────────────────────┘
```

### 3.2 三個核心概念

#### Task（任務）— 單次執行單元

使用者以自然語言下達指令，Gemini Spark 自動：
1. **解析指令**：理解指令中涉及的動作與資料來源
2. **生成工作流**：自動規劃執行步驟（Plan step）
3. **調用工具**：依序呼叫對應的 Connected Apps
4. **執行與回報**：背景執行，完成後推播通知

**範例**：
```
指令：「幫我彙總昨天所有郵件裡面的推廣郵件部分，並且展示這些推廣郵件裡面的品牌」
```
Spark 的執行流程：
```
Plan → 讀取 Gmail（篩選昨日郵件）→ 分類推廣郵件 → 提取品牌名稱 → 彙總展示
```

#### Skills（技能）— 固化重複流程

將 Task 封裝成可重複使用的 Skills，支援兩種建立方式：
- **Gemini 協助生成**：使用者描述流程，Spark 自動生成 Skill
- **手動定義**：有能力的使用者自行撰寫指令與程式碼

**範例**（股票報告 Skill）：
```
Skill: StockPriceReport
輸入：公司名稱或股票代碼
流程：查詢股價 → 分析趨勢 → 生成報告 → 存入 Google Drive/Vault
調用方式：在 Task 輸入 /StockPriceReport Apple NVIDIA
```

#### Schedules（排程）— 定時自動執行

設定固定時間讓 Spark 自動執行重複任務：
- 支援每日/工作日/自訂日期
- 時區自動使用使用者所在時區（不可修改）
- 可手動觸發測試（Run Now）

**範例**（每日日報）：
```
Schedule: DailyBriefs
時間：每個工作日 7:00 AM
內容：監控股票價格 + 彙總會議日程 + 整理昨日郵件簡報
輸出：Google Doc 存入 Drive/Vault
```

### 3.3 關鍵設定

| 設定 | 功能 | 重要性 |
|------|------|--------|
| Activity | 保持對話與後台任務長時間運行 | 必要（否則任務中斷） |
| Personal Intelligence | 跨對話保留使用者要求與習慣 | 必要（否則無記憶） |

### 3.4 Connected Apps（可操作的應用）

| 類別 | 應用 | 操作類型 |
|------|------|----------|
| Google Workspace | Gmail | 讀取、分類、彙整郵件 |
| Google Workspace | Google Calendar | 讀取日程、建立事件 |
| Google Workspace | Google Drive | 讀取、建立、編輯文件 |
| Google Workspace | Google Docs/Sheets/Slides | 建立與編輯文件 |
| Google 服務 | Google Search | 即時資訊搜尋 |
| Google 服務 | Google Maps | 地點與天氣資訊 |
| 第三方（MCP） | 支援 OAuth 認證的 MCP 服務 | 外部資料存取 |

### 3.5 MCP 整合

Gemini Spark 支援 MCP（Model Context Protocol）接入，但限制：
- **必須支援 OAuth 認證**（不支援 API Key 或無認證的 MCP）
- 目前 MCP 生態中符合此條件的服務有限
- Google 官方文件未提供 MCP 服務清單或推薦

### 3.6 隱私與安全

根據 Google 官方支援文件：
- 使用者資料不會用於訓練模型
- 任務執行日誌保留 30 天
- Personal Intelligence 資料可隨時清除
- 操作 Google Workspace 時需經過 OAuth 授權

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表：替代方案比較

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|----------|--------------|----------------|------------------|
| **Gemini Spark** | Google 官方 AI agent，雲端 24/7 執行 Task/Skills/Schedules，深度整合 Google Workspace | Gemini Pro 以上訂閱（$20-200/月）+ 美國地區 + Google 生態使用者 | 綁定 Google 生態；MCP 僅支援 OAuth 限制第三方整合；時區不可自訂；browser 功能尚未完全可用 | 零程式碼自動化 Google Workspace 工作流；跨應用資料彙整；背景執行 |
| **Claude Cowork**（Anthropic） | AI agent 模式，支援 browser 操作、檔案操作、程式碼執行，可與外部工具整合 | Claude Pro/Max 訂閱（$20-200/月） | 無原生 Google Workspace 整合；需透過 MCP 或 API 橋接；browser 操作為核心但速度較慢 | 泛用型 agent，不綁定特定生態系；browser 操作能力強；適合非 Google 生態使用者 |
| **ChatGPT Agent**（OpenAI） | AI agent 模式，支援 browser 操作、檔案操作、程式碼執行，可與外部工具整合 | ChatGPT Pro 訂閱（$200/月） | 無原生 Google Workspace 整合；需透過第三方工具橋接；定價較高 | 泛用型 agent，OpenAI 生態系；模型能力強但成本高 |
| **自建方案：GAS + BrowserBase + LLM** | 自行撰寫 Google Apps Script 串接 Gmail/Calendar/Drive，搭配 BrowserBase 做 browser 自動化，LLM 做 AI 摘要 | 需具備程式設計能力（JavaScript/Python）；需自行維護基礎設施 | 開發與維護成本高；無統一 agent 介面；需自行處理錯誤與重試；無 Personal Intelligence 跨對話記憶 | 完全自訂；不綁定訂閱制；可整合任意第三方服務；可控制資料流向與隱私 |

### 對照表：Gemini Spark vs 自建方案（使用者既有 workflow）

| 面向 | Gemini Spark | 自建方案（GAS + BrowserBase + LLM） |
|------|-------------|--------------------------------------|
| **Gmail 處理** | 內建，自然語言指令即可 | 已達成理解（GAS MVP：批次讀取 → AI 摘要 → Sheet） |
| **Calendar 整合** | 內建，直接讀取日程 | 需自行串接 Calendar API |
| **Drive 文件生成** | 內建，自動建立 Google Doc/Sheet | 需自行串接 Drive API |
| **背景執行** | 內建（雲端 24/7） | 需自行部署（Cloud Function / VM） |
| **跨對話記憶** | Personal Intelligence 內建 | 需自行實作（DB + 向量檢索） |
| **定時排程** | Schedules 內建 | 需自行設定（Cloud Scheduler / cron） |
| **流程固化** | Skills 內建 | 需自行封裝（function / module） |
| **MCP 整合** | 有限（僅 OAuth） | 完全自訂 |
| **Browser 操作** | 尚未完全可用（coming this summer） | BrowserBase 已進行中 |
| **非 Google 服務** | 弱（僅 MCP OAuth） | 強（可接任意 API） |
| **開發成本** | 低（零程式碼） | 高（需開發與維護） |
| **營運成本** | 訂閱制（$20-200/月） | 自建基礎設施費用 |
| **資料控制** | Google 雲端，受 Google 隱私政策約束 | 完全自控 |

### 切入點差異分析

```
問題：Google 生態自動化
│
├─ 零程式碼路線 ────────────── 程式碼路線
│   │                            │
│   Gemini Spark                GAS + BrowserBase + LLM
│   (Google 官方 agent)         (自建方案)
│   │                            │
│   優點：                       優點：
│   • 零程式碼設定               • 完全自訂
│   • 內建 Workspace 整合        • 不綁定訂閱
│   • 背景執行 + 排程            • 可接任意服務
│   • Personal Intelligence      • 資料自控
│   │                            │
│   缺點：                       缺點：
│   • 綁定 Google 生態           • 開發成本高
│   • 訂閱制成本                 • 需自行維護
│   • 第三方整合弱               • 無統一 agent 介面
│   • 資料在 Google 雲端         • 需自行實作記憶/排程
│
└─ 泛用型 agent 路線 ───────────
    Claude Cowork / ChatGPT Agent
    (不綁定特定生態系)
    │
    優點：
    • 跨平台
    • browser 操作能力強
    • 模型能力強
    │
    缺點：
    • 無原生 Google Workspace 整合
    • 需橋接工具
    • 成本可能更高
```

### 對使用者的具體建議

基於使用者既有 workflow（GAS Gmail 自動化已達成理解、BrowserBase 進行中、Feedly 自動閱讀日常在用）：

1. **Gemini Spark 的價值在於「零程式碼的 Google Workspace 自動化」**，對於使用者已用 GAS 實作的部分（Gmail 讀取 + AI 摘要），Spark 提供的是更簡便的替代方案，但不是質的突破

2. **Spark 的 Schedules + Skills 是使用者目前自建方案中尚未完全覆蓋的領域**：
   - 定時排程（Schedules）：使用者目前需手動觸發或自行設定 cron
   - 流程固化（Skills）：使用者目前需自行封裝程式碼
   - 跨對話記憶（Personal Intelligence）：使用者目前需自行實作

3. **Spark 的 browser 功能尚未完全可用**，而使用者的 BrowserBase 專案正在進行中，此面向 Spark 目前無法取代

4. **Spark 的第三方整合能力弱**（僅 MCP OAuth），而使用者的 workflow 涉及 Feedly、BrowserBase 等非 Google 服務，Spark 無法直接整合

5. **結論**：Gemini Spark 不是使用者既有 workflow 的替代品，而是「Google Workspace 內部自動化的零程式碼補充方案」。若使用者願意接受訂閱制成本與 Google 生態綁定，Spark 的 Schedules + Skills 可補足自建方案中尚未完善的定時排程與流程固化能力。但對於非 Google 服務的整合（Feedly、BrowserBase 等），仍需維持自建方案。
