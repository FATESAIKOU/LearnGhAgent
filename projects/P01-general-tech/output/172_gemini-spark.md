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

---

## 5. User Q&A

### Q1：GAS 可不可以直接呼叫外部 API？（我是 Google Drive 2TB 方案，不是 AI 那個）

**A**：可以。Google Apps Script 的 `UrlFetchApp` 類別支援直接呼叫外部 API。

| 能力 | 支援情況 |
|------|----------|
| HTTP 方法 | GET / POST / PUT / DELETE / PATCH |
| 自訂 header | 支援（含 Content-Type、Authorization 等） |
| OAuth 2.0 | 支援（可自訂 Authorization header 或使用 OAuth2 library） |
| mutual TLS | 支援 |
| Payload 大小 | POST 上限 10MB，response 上限 10MB |
| URL 長度 | 上限 2048 字元 |
| 每日配額 | 20,000 calls/day（consumer 帳號） |

**注意**：此能力與使用者是否為 AI 方案無關。GAS 是 Google Workspace 的內建功能，只要擁有 Google 帳號即可使用。使用者的 Google Drive 2TB 方案（非 AI）完全可執行 UrlFetchApp。

**結論**：GAS 可直接呼叫外部 API，配額充足（20,000 calls/day），支援 OAuth 認證，可滿足多數第三方 API 整合需求。

---

### Q2：Gemini Spark 可不可以用 GAS 做 MCP 或者能力擴充？（因為 Gemini Web 不行）

**A**：不行。Gemini Spark 的 MCP 接入是「Spark 作為 MCP client 呼叫外部 MCP server」，而非「外部程式碼（如 GAS）作為 MCP server 接入 Spark」。

| 面向 | 說明 |
|------|------|
| Spark MCP 方向 | Spark → 外部 MCP server（Spark 是 client） |
| GAS 角色 | GAS 可作為 HTTP server 對外提供 API，但 Spark 的 MCP 要求 OAuth 認證，且無官方文件支援自訂 MCP server 接入 |
| Gemini Web 限制 | Gemini Web（Chatbot 模式）不支援 MCP，Spark 是唯一支援 MCP 的 Gemini 模式 |
| 實質限制 | 即使 GAS 部署為 Web App（doGet/doPost），也無法以 MCP 協議註冊到 Spark 的工具清單中 |

**對照表：Spark 能力擴充方式**

| 方式 | 可行性 | 限制 |
|------|--------|------|
| Connected Apps（內建） | 可用 | 僅限 Google 生態（Gmail、Calendar、Drive 等） |
| MCP（OAuth） | 有限可用 | 需找到支援 OAuth 的 MCP server；GAS 無法作為 MCP server |
| 自訂程式碼（GAS） | 不可用 | Spark 無外掛或自訂工具介面 |
| Agent.md 等設定檔 | 不可用 | 影片明確指出 Spark 不支援自訂 agent 設定檔 |

**結論**：Spark 的能力擴充僅限於「內建 Connected Apps」與「OAuth MCP client」兩種方式，無法透過 GAS 或其他自訂程式碼擴充其工具集。

---

### Q3：我的訂閱形態下（Google Drive 2TB 方案（非 AI））能不能用 Spark，有沒有用量限制？

**A**：不能。使用者的 Google Drive 2TB 方案（舊版 Google One，非 AI 方案）不包含 Gemini Spark。

**方案對照表**：

| 方案名稱 | 儲存空間 | 月費 | 包含 Gemini Spark |
|----------|----------|------|-------------------|
| Google One 2TB（舊版，使用者現有） | 2TB | ~$9.99/mo | **否** |
| Google AI Plus | 400GB | $9.99/mo | 否（僅 Gemini Advanced） |
| Google AI Pro | 5TB | $19.99/mo | **是** |
| Google AI Ultra | 10TB+ | $199.99/mo | **是** |

**用量限制**（若升級至 AI Pro）：

| 面向 | 限制 |
|------|------|
| Task 執行次數 | 無明確上限（但受 Gemini Pro 配額約束） |
| Skills 數量 | 無明確上限 |
| Schedules 數量 | 無明確上限 |
| 背景執行時間 | 無明確上限（雲端 24/7） |
| Personal Intelligence 記憶量 | 無明確上限 |
| 地區限制 | 僅美國地區（需 VPN 或美國 IP） |

**結論**：使用者需從現有 Google Drive 2TB 方案升級至 Google AI Pro（$19.99/mo，5TB）才能使用 Gemini Spark。升級後儲存空間從 2TB 增至 5TB，月費從 ~$9.99 增至 $19.99。

---

### Q4：Gemini Spark 可不可以換 LLM 模型，整體擴展性如何？

**A**：不可以。Gemini Spark 固定使用 Gemini 2.0 Flash 模型，無模型切換選項。

| 面向 | 現狀 |
|------|------|
| 模型選擇 | 固定 Gemini 2.0 Flash（不可更換） |
| 模型切換 UI | 無（Spark 模式無模型選擇器） |
| 自訂模型 | 不支援 |
| 底層模型更新 | 由 Google 控制，使用者無法干預 |

**整體擴展性評估**：

| 擴展面向 | 評級 | 說明 |
|----------|------|------|
| 工具擴展 | 低 | 僅內建 Connected Apps + OAuth MCP |
| 模型擴展 | 無 | 固定模型，不可更換 |
| 流程擴展 | 中 | Skills 可固化流程，但無法撰寫自訂程式碼邏輯 |
| 資料源擴展 | 低 | 僅 Google 生態 + MCP（OAuth 限制） |
| 輸出格式擴展 | 中 | 可生成 Google Doc/Sheet，但無法自訂輸出模板 |
| 第三方整合擴展 | 低 | 僅 MCP OAuth，無 API 或 webhook |

**對照：自建方案的擴展性**

| 面向 | Gemini Spark | 自建方案（GAS + LLM API） |
|------|-------------|---------------------------|
| 模型選擇 | 固定 Gemini 2.0 Flash | 可選任意 LLM（GPT-4、Claude、Gemini API 等） |
| 工具擴展 | 僅內建 + MCP OAuth | 可接任意 REST API |
| 流程控制 | 自然語言指令 | 完整程式碼控制（條件、迴圈、錯誤處理） |
| 輸出格式 | Google Doc/Sheet | 任意格式（JSON、CSV、HTML、PDF 等） |

**結論**：Spark 的擴展性極低，模型固定、工具集封閉、無自訂程式碼能力。若模型選擇或擴展性是關鍵需求，Spark 不適合。

---

### Q5：我其實已經有 MyBrain 來做跨 Session 的事實存取，但不知道 Gemini Spark 支不支援

**A**：不支援。Gemini Spark 的 Personal Intelligence 與 MyBrain 在設計哲學與技術實作上完全不同，無法互通或取代。

**對照表：Personal Intelligence vs MyBrain**

| 面向 | Personal Intelligence（Spark） | MyBrain（使用者自建） |
|------|-------------------------------|----------------------|
| 儲存內容 | 使用者的偏好、習慣、對話中提及的資訊 | 結構化知識庫（身份、處境、決策、技術棧等） |
| 儲存格式 | 非結構化（模型內部狀態） | 結構化（Markdown 檔案 + 向量檢索） |
| 存取方式 | 僅 Spark 內部使用，無 API | 可透過搜尋/讀取任意存取 |
| 匯出/匯入 | 不支援 | 支援（純文字檔案） |
| 跨對話保留 | 自動（需開啟 Personal Intelligence 設定） | 自動（每次查詢時讀取） |
| 使用者控制 | 可清除全部記憶，但無法編輯單一條目 | 完全控制（可編輯、刪除、新增任意條目） |
| 與外部工具整合 | 不可用 | 可透過 API 或檔案系統整合 |
| 資料所有權 | Google 雲端 | 使用者自控 |

**關鍵差異**：

```
MyBrain 的設計：
  使用者主動寫入 → 結構化儲存 → 明確檢索 → 提供給 LLM

Personal Intelligence 的設計：
  對話中被動學習 → 非結構化儲存 → 隱式影響 → 僅供 Spark 使用
```

**結論**：Personal Intelligence 無法取代 MyBrain，也無法與 MyBrain 整合。兩者並存時，MyBrain 仍為使用者主要的跨 Session 事實存取方案，Personal Intelligence 僅在 Spark 內部提供額外的對話記憶輔助。
