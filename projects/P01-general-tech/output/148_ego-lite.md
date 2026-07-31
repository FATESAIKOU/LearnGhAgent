# ego-lite 技術分析報告

## 1. 這個技術解決什麼問題？

**ego-lite 解決的是「AI Agent 在瀏覽器自動化任務中，與人類共用同一瀏覽環境時遭遇的四大痛點」：**

1. **重複登入**：傳統工具（Playwright、Puppeteer）每次啟動新瀏覽器實例時，Cookie 與登入狀態遺失，需要反覆手動登入。
2. **資源開銷大**：每開一個自動化任務就需要啟動一個獨立的瀏覽器實例，記憶體與進程開銷極高。
3. **Token 消耗高**：傳統 CLI 模式的自動化工具需要 Agent 反覆「呼叫指令 → 觀察結果 → 再呼叫指令」，每次交互都消耗 LLM Token。
4. **執行速度慢**：多輪交互導致任務完成時間長。

**模糊之處**：ego-lite 的「快」與「省」宣稱（2.5x 更快、Token 減少 4 倍）的 benchmark 僅與 Vercel agent-browser 比較，且官方未公開完整的 benchmark 方法論與測試程式碼，無法獨立重現。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **傳統瀏覽器自動化工具的架構限制**：Browser-Use、agent-browser（Vercel）等工具本質上是「瀏覽器自動化框架」，它們不附帶瀏覽器本身，需要驅動一個獨立的瀏覽器實例。這導致：
  - 每次啟動都是全新瀏覽器，無繼承登入狀態
  - Agent 與人類搶同一組分頁
  - 無法並行多工（一個 Agent 佔用整個瀏覽器）
- **CLI 模式的交互瓶頸**：傳統工具以 CLI 指令為單位，Agent 每做一個操作（點擊、填寫、導航）就要發一次指令、等一次回傳、再決定下一步。這在 LLM 驅動的場景下，每次交互都消耗 Token 且增加延遲。

### 通用技術背景（文章中未明確提及）

- **Chromium 的多進程架構**：每個瀏覽器分頁（Tab）本質上是一個獨立的渲染進程。傳統方案每開一個任務就啟動一個完整瀏覽器實例（含 GPU 進程、網路進程、多個渲染進程），資源浪費巨大。ego-lite 的 Space 架構在單一瀏覽器實例內隔離任務，共享底層進程。
- **Accessibility Tree 的應用**：瀏覽器內建 Accessibility Tree 是 DOM 的語意化簡化版本，原本為輔助技術（螢幕閱讀器）設計。ego-lite 將其改造為 Agent 的「頁面快照」（Snapshot），比完整 DOM 更輕量、比截圖更結構化。
- **MCP（Model Context Protocol）的興起**：2024 年底 Anthropic 推出的 MCP 標準化 Agent 與工具的通訊協定。ego-lite 的 `ego-browser` skill 本質上是一個 MCP 風格的工具層，但採用 JavaScript heredoc 而非標準 MCP 的 JSON-RPC 格式。

---

## 3. 這個技術是如何解決該問題的？

### 核心機制

#### 3.1 Space 架構（解決資源開銷與並行問題）

```
單一 Chromium 瀏覽器實例
├── 人類工作區（你的分頁）
├── Space #1（Agent A 的任務）
├── Space #2（Agent B 的任務）
├── Space #3（Agent C 的任務）
└── ...
```

- 所有 Space 共享同一個瀏覽器進程（GPU、網路、儲存）
- 每個 Space 擁有獨立的 Cookie jar、localStorage、分頁集合
- Agent 只能操作其被分配的 Space，無法干擾人類或其他 Agent 的分頁
- 藍色標籤標示 Agent 正在控制的 Space

**資源節省量化**：相比傳統方案（每任務啟動獨立瀏覽器實例），Space 架構將記憶體與進程開銷降低「幾十倍」（官方宣稱，未提供具體 benchmark 數據）。

#### 3.2 Snapshot 機制（解決 Token 消耗問題）

```
網頁
  │
  ▼
Accessibility Tree 提取
  │
  ▼
壓縮 + 分配穩定 @N 參考編號
  │
  ▼
Snapshot（結構化文字表示）
  │
  ▼
Agent 可直接用 @N 參考編號操作元素
```

- 基於 Chromium 核心層級的 Accessibility Tree 提取（非 DOM 序列化）
- 處理巢狀 iframe 等複雜結構（官方宣稱「其他方案在此處持續失敗」）
- 每個可互動元素獲得穩定的 `@N` 參考編號
- Agent 可直接用 `@N` 參考編號操作元素，無需 CSS selector 或 XPath

#### 3.3 ego-browser + JavaScript Heredoc（解決 Token 消耗與速度問題）

```javascript
// Agent 產出的一段 JavaScript（一次性發送）
// 傳統 CLI 模式需要 7 次交互，這裡只需 1 次
await openOrReuseTab('example.com')
await click('.product-card')
await fill('input[name="qty"]', '2')
await click('.add-to-cart')
await navigate('/checkout')
cliLog('done')
```

- Agent 將多步驟操作編寫為一段 Node.js 程式碼（heredoc）
- `ego-browser` 在瀏覽器端一次性執行整段程式碼
- 相比 CLI 模式（每步一次交互），Token 消耗減少約 4 倍（官方宣稱）
- 支援 `ego-browser` 作為 Agent CLI（Claude Code、Codex、Cursor 等）與瀏覽器之間的連接層

#### 3.4 Chrome Profile 繼承（解決重複登入問題）

- 首次啟動時可一鍵匯入現有 Chrome 設定檔
- 所有 Cookie、登入狀態、擴充功能、書籤離線保存在本地
- 後續所有自動化任務直接複用這些登入態
- 無需帳號註冊、無雲端同步

#### 3.5 Skill 固化（解決重複任務的效率問題）

- 成功的操作流程可提煉為可重複使用的 Skill
- Skill 調用時只需一次交互即可完成原本多步的操作
- 官方宣稱：複雜任務重複執行時可達 5x 加速（coming soon，目前 limited beta）

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表：替代方案比較

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|----------|--------------|----------------|------------------|
| **BrowserBase**（使用者自製） | 40 行 shell wrapper 啟動 stock Chrome + 掛載官方 chrome-devtools-mcp | 需安裝 Chrome、Node.js、MCP 相容的 Agent CLI | 無內建並行機制；依賴 MCP 的 29 個獨立工具（每步一次工具呼叫）；瀏覽器實例與 Agent 生命週期分離 | 解決 Puppeteer 被 Google 偵測問題；登入狀態持久化；零自訂 MCP 程式碼維護 |
| **Playwright / Puppeteer** | 程式化控制瀏覽器的標準函式庫，支援多種語言綁定 | 需安裝對應的 Node.js/Python 套件與瀏覽器 binary | 每次啟動新實例需重新登入；Google 可偵測 Puppeteer 啟動的瀏覽器；無內建 Agent 整合 | 成熟穩定、社群龐大、跨平台支援完善 |
| **Browser-Use** | Python Agent 框架，LLM 決定瀏覽器操作步驟 | 需 Python 環境、LLM API key、獨立瀏覽器實例 | 每步操作需 LLM 推理（Token 消耗高）；無內建登入狀態管理；單一瀏覽器實例 | 高階抽象，Agent 可直接用自然語言描述任務 |
| **Browserbase（雲端）** | 雲端瀏覽器平台，REST API 建立 session，CDP 驅動 | 需 API key、付費方案、網路連線 | 雲端 IP 可能被目標網站封鎖；session 建立延遲（約 1-3 秒）；資料經由第三方伺服器 | 高並行（100+ session）、內建 proxy/stealth/captcha 解決方案、SOC 2/HIPAA 合規 |

### 各方案切入點差異

- **BrowserBase**：最小侵入式解法。不寫自訂 MCP server，不修改瀏覽器 binary，僅用 wrapper 繞過 Puppeteer 偵測問題。適合已使用 MCP 生態的開發者。
- **Playwright/Puppeteer**：通用瀏覽器自動化標準。不針對 Agent 場景設計，需自行處理登入狀態與 Agent 整合。
- **Browser-Use**：Agent 優先的 Python 框架。將瀏覽器操作封裝為 LLM 可理解的工具集，但 Token 效率較低。
- **Browserbase（雲端）**：基礎設施級解法。適合需要大規模並行、匿名代理、合規要求的生產環境，但成本較高且資料需經第三方。

### 反證表：ego-lite 的潛在限制

| 面向 | ego-lite 宣稱 | 實際限制 |
|------|--------------|----------|
| 平台支援 | macOS 可用，Windows/Linux Planned | 目前僅 macOS（12+），Windows/Linux 無明確時程 |
| 並行能力 | 無限制 Space | 受本機機器資源限制（CPU、記憶體），非雲端可擴展 |
| 長期服務穩定性 | MIT 開源 + 免費 App | 7k stars、52 open issues；公司為 Citro Labs Pte. Ltd.（新加坡），2026 年成立，無公開財務資訊；開源 repo 可 fork，但瀏覽器 binary 為獨立下載 |
| 安全性 | 資料本地、無帳號 | Privacy Policy 涵蓋的是 EGOBOT（雲端 AI agent 服務），非 ego-lite（本地瀏覽器）；ego-lite 官方宣稱「僅記錄 migration opt-in」，但 Chromium 本身有 telemetry |
| Token 效率 benchmark | 2.5x 更快、Token 更少 | 僅與 Vercel agent-browser 比較；未與 Browser-Use、Playwright MCP 等比較；benchmark 程式碼未公開 |
| 可重複 Skill | 5x 加速（coming soon） | 目前 limited beta，非 GA 功能 |

### 結論

ego-lite 的核心創新在於**將瀏覽器本身設計為 Agent 與人類共用的平台**，而非在既有瀏覽器上疊加自動化層。Space 架構與 Snapshot 機制從瀏覽器核心層解決了資源隔離與頁面理解的問題，JavaScript heredoc 模式則從 Agent 交互層解決了 Token 效率問題。但其平台限制（macOS only）、公司規模（新創早期）、以及 benchmark 覆蓋範圍不足，是評估長期採用時需考量的風險。
