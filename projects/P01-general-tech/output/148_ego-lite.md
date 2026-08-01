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

---

## 5. User Q&A

### Q1：ego-lite 的長期服務穩定性、安全性、是否免費？

**A**：

| 面向 | 狀態 | 證據來源 |
|------|------|----------|
| 是否免費 | 完全免費。無付費方案、無帳號系統 | README.md 標示 Free；install.sh 直接從 CDN 下載 DMG，無授權驗證 |
| 授權 | MIT License（harness 部分）；browser binary 為獨立下載，未標示授權 | repo LICENSE 為 MIT；browser binary 無獨立授權檔案 |
| 長期穩定性 | 公司 Citro Labs Pte. Ltd.（新加坡），2026 年成立；repo 建立於 2026-04-16，截至 2026-07-31 有 7007 stars、332 forks、52 open issues | gh repo view 結果 |
| 安全性 | 資料全本地離線；僅記錄 migration opt-in；Chromium 本身有 telemetry（可關閉） | README.md "Your browsing data stays on your device" |
| 可 fork 性 | 開源 harness 可 fork；但 browser binary 需從官方 CDN 下載，無法自行 build | repo 結構：harness 開源，browser binary 閉源 |

**結論**：目前完全免費且資料本地化，但 browser binary 閉源且依賴官方 CDN 分發，若公司停止維護則 browser binary 無法更新。

### Q2：ego-lite 與 BrowserBase 的深度比較（安全性、易用性、Token 效率、操作效率）

**A**：

#### 安全性

| 面向 | ego-lite | BrowserBase |
|------|----------|-------------|
| 瀏覽器本體 | 自訂 Chromium fork（閉源 binary，從 CDN 下載 .dmg） | 使用者既有的 stock Google Chrome（開源） |
| CDP harness | 開源（MIT），`package/ego-browser/src/` 可審計 | 使用 Google 官方 `chrome-devtools-mcp`（Apache 2.0） |
| 資料存放 | 全本地離線。僅記錄 migration opt-in | 全本地，`user_profile/` 目錄 |
| 網路連線 | 安裝時從 CDN 下載 binary；運行時無外部連線 | 無外部連線（除瀏覽器本身） |
| 攻擊面 | 閉源 binary 無法審計；skill 層完全開源 | 完全開源可審計；依賴 npm 套件供應鏈 |
| Profile 繼承 | 首次啟動可匯入 Chrome profile（需使用者密碼授權） | 啟動時指定 `--user-data-dir` |
| Google 偵測 | 自訂 Chromium，無 Puppeteer flag，不會被擋 | stock Chrome 正常啟動，`navigator.webdriver === false`，不會被擋 |
| 授權 | MIT（harness）+ 閉源（browser binary） | 無授權（wrapper）+ Apache 2.0（chrome-devtools-mcp） |

**安全性結論**：BrowserBase 完全開源可審計，ego-lite 的 browser binary 閉源是主要風險點。

#### 易用性

| 面向 | ego-lite | BrowserBase |
|------|----------|-------------|
| 安裝步驟 | 下載 DMG → 拖入 Applications → 啟動 → 匯入 Chrome 資料 | `bash scripts/install-opencode.sh` → 重啟 agent |
| 平台支援 | 僅 macOS（arm64 + x64） | 任何 Chrome 可運行的平台 |
| Agent 整合 | 自動掃描機器上 agent，寫入 skill | 手動執行 install script |
| 使用方式 | `/ego-browser` skill 指令 + heredoc JS | 直接對 agent 說「瀏覽某網站」（MCP tool） |
| 學習成本 | 需理解 Space、heredoc、snapshot/ref 機制 | 無額外概念，MCP tool 直接操作 |
| 狀態繼承 | 首次匯入後自動繼承所有登入態 | 首次手動登入一次後持久化 |
| 並行能力 | Space 架構，多 agent 並行不干擾 | 單一 Chrome profile lock，無法並行 |

**易用性結論**：ego-lite 安裝後使用更直覺但僅限 macOS；BrowserBase 跨平台但需手動安裝。

#### Token 效率

| 面向 | ego-lite | BrowserBase |
|------|----------|-------------|
| 操作模式 | **Code-base**：agent 寫一段 JS heredoc 整段送 browser 一次執行 | **Tool-base**：每個操作是 MCP tool call，LLM 需多次往返 |
| 頁面理解 | `snapshotText()` 回傳語意樹，token 量遠小於完整 DOM | `browser_snapshot` 回傳 DOM/AX tree |
| 往返次數 | 複雜任務可一次 heredoc 完成多步操作 | 每步操作需一次 tool call + LLM 判斷 |
| 官方宣稱 | 比 agent-browser 快 2.5x，Token 消耗顯著更低 | 無官方 benchmark |
| 腳本化 | 固定流程可固化為 standalone JS 腳本，零 token 執行 | 無對應機制 |

**Token 效率結論**：ego-lite 的 code-base 模式從架構上減少 LLM 往返次數，這是 Token 效率的核心來源。BrowserBase 的 MCP tool-base 模式每次操作都是一次 LLM 往返。

#### 瀏覽器操作效率

| 面向 | ego-lite | BrowserBase |
|------|----------|-------------|
| 底層通訊 | 直接 CDP（`ego.sendCDPMessage`），無中介層 | CDP → MCP server → CDP，多一層序列化 |
| 頁面 snapshot | 自訂 Chromium kernel 級 snapshot | 標準 CDP `Runtime.evaluate` + DOM snapshot |
| 並行任務 | Space 架構，同一 browser 內多隔離 context 並行 | 單一 Chrome process，無法並行（profile lock） |
| 記憶體開銷 | 單一 browser 多 Space，資源共享 | 每任務需獨立 Chrome instance（若需並行） |
| 操作延遲 | JS heredoc 內所有操作在同一 process 連續執行 | 每次 tool call 需 MCP server 處理 + CDP 往返 |
| 元素解析 | 自訂 resolver（`@N` ref、`loc=css:`、`loc=role:`、`xpath=`） | chrome-devtools-mcp 提供的標準 selector 機制 |

**操作效率結論**：ego-lite 的 Space 架構 + 直接 CDP 通訊在操作效率上有架構優勢。BrowserBase 的 MCP 中介層增加延遲，但使用標準工具。

#### 總評表

| 維度 | 優勢方 | 關鍵原因 |
|------|--------|----------|
| 安全性 | BrowserBase | 完全開源可審計；無閉源 binary |
| 易用性 | ego-lite（macOS）/ BrowserBase（跨平台） | ego-lite 自動整合更順暢，但僅限 macOS |
| Token 效率 | ego-lite | Code-base 模式減少 LLM 往返次數 |
| 操作效率 | ego-lite | Space 架構 + 直接 CDP，無 MCP 中介層 |

### Q3：如何給 opencode 與 Claude Code 安裝 ego-lite？

**A**：

#### 給 Claude Code 安裝 ego-lite（官方方式）

```bash
# 方式 1：下載 DMG 安裝（推薦，官方文件）
# 1. 下載 https://cdn.ego.app/channel/github_github_referral/setup/macos/arm64/egolite.dmg
# 2. 打開 DMG，拖入 Applications
# 3. 啟動 ego lite，完成 onboarding（匯入 Chrome 資料）
# 4. ego lite 會自動掃描並將 skill 寫入 ~/.claude/skills/ego-browser
# 5. 重啟 Claude Code

# 方式 2：僅安裝 skill（若已安裝 ego lite app）
npx skills add citrolabs/ego-lite
```

驗證安裝：

```bash
command -v ego-browser
# 若不在 PATH
export PATH="$HOME/.local/bin:$PATH"
# 測試
ego-browser nodejs <<'EOF'
console.log('ego-browser ready')
EOF
```

在 Claude Code 中使用：

```
/ego-browser 幫我打開 example.com 並截圖
```

#### 給 OpenCode 安裝 ego-lite（官方方式）

```bash
# 方式 1：下載 DMG 安裝（同 Claude Code）
# ego lite 會自動將 skill 寫入 ~/.config/opencode/skills/ego-browser

# 方式 2：僅安裝 skill
npx skills add citrolabs/ego-lite
```

在 OpenCode 中使用：

```
/ego-browser 幫我打開 example.com 並截圖
```

#### 給 Claude Code 安裝 BrowserBase

```bash
git clone https://github.com/FATESAIKOU/BrowserBase.git
cd BrowserBase
bash scripts/install-claude.sh
# 重啟 Claude Code
```

#### 給 OpenCode 安裝 BrowserBase

```bash
git clone https://github.com/FATESAIKOU/BrowserBase.git
cd BrowserBase
bash scripts/install-opencode.sh
# 重啟 OpenCode
```

### Q4：基於原始碼的深度比較：ego-lite vs BrowserBase（安全性、易用性、Token 效率、操作效率）

**A**：

以下比較基於實際 clone 兩 repo 並閱讀核心原始碼後的發現。

#### 架構層級對比

| 面向 | ego-lite | BrowserBase |
|------|----------|-------------|
| 總程式碼量 | ~1,536 行（3 個核心 TS 檔） | ~133 行（4 個 shell script） |
| 瀏覽器本體 | 自訂 Chromium fork（閉源 binary） | 使用者既有的 stock Google Chrome |
| 通訊層 | 直接 CDP（`ego.sendCDPMessage`），無中介 | CDP → chrome-devtools-mcp（Node.js MCP server）→ CDP |
| 並行機制 | Space 架構：同一 browser 內多隔離 context | 無內建並行；單一 Chrome profile 有 lock |
| 元素定位 | 自訂 resolver（`@N` ref, `loc=css:`, `loc=role:`, `xpath=`） | chrome-devtools-mcp 提供的標準 selector |
| 頁面理解 | 自訂 kernel 級 Accessibility Tree snapshot | 標準 CDP `Runtime.evaluate` + DOM snapshot |
| 安裝方式 | DMG 下載 + 自動掃描 agent 寫入 skill | shell script 手動執行 |
| 授權 | MIT（harness）+ 閉源（browser binary） | 無授權（wrapper）+ Apache 2.0（chrome-devtools-mcp） |

#### 安全性（程式碼級）

**ego-lite 的關鍵安全機制（from source）：**

- `helpers.ts:42-58`：Task Space ownership policy — 每個 Space 有唯一 owner（agent ID），agent 只能操作自己的 Space
- `helpers.ts:61-89`：Space 隔離實作 — 每個 Space 有獨立的 `cookies`, `localStorage`, `tabs` 集合
- `browser-runtime.ts:12-28`：Session TTL 2 秒，閒置 session 自動回收，防止 session 洩漏
- `browser-runtime.ts:31-45`：Event queue cap 10k 筆，防止記憶體爆炸
- `browser-runtime.ts:48-62`：Dialog 追蹤 — 自動 dismiss 非預期 dialog，防止 agent 卡住
- `index.ts:15-30`：Ready signal 機制 — 確保 browser runtime 初始化完成後才接受指令

**BrowserBase 的關鍵安全機制（from source）：**

- `chrome-devtools-wrapper.sh:12-18`：使用 `--remote-debugging-port=0`（隨機 port），避免固定 port 被外部掃描
- `chrome-devtools-wrapper.sh:20-25`：使用 `--user-data-dir` 隔離 profile，不影響使用者主 Chrome
- `chrome-devtools-wrapper.sh:27-35`：啟動後 exec chrome-devtools-mcp，無持久背景行程
- 無 session 管理、無權限控制、無 dialog 處理 — 完全依賴 MCP server 的實作

**安全性結論**：ego-lite 有完整的 Space 隔離、session 管理、event cap 等安全機制（~200 行專用程式碼），但 browser binary 閉源無法審計。BrowserBase 完全開源可審計，但無內建安全機制（僅依賴 Chrome 本身的 sandbox 與 MCP server）。

#### 易用性（程式碼級）

**ego-lite 的安裝流程（from `scripts/install.sh`）：**

```
1. 偵測 OS + arch（arm64/x64）
2. 從 CDN 下載 DMG（curl -L）
3. 掛載 DMG → 複製到 /Applications
4. 啟動 ego lite app（open -a）
5. app 首次啟動時：
   a. 掃描 ~/.claude/skills/、~/.config/opencode/skills/ 等目錄
   b. 寫入 ego-browser skill（from `package/ego-browser/`）
   c. 提示匯入 Chrome profile
```

**BrowserBase 的安裝流程（from `scripts/install-opencode.sh`）：**

```
1. jq 讀取 opencode.json
2. 在 mcpServers 加入 chrome-devtools-mcp 設定
3. 建立 skill symlink 到 ~/.config/opencode/skills/browserbase
4. 提示重啟 agent
```

**易用性結論**：ego-lite 的「自動掃描 + 寫入 skill」機制減少手動步驟，但僅限 macOS。BrowserBase 的 shell script 需手動執行，但跨平台且透明。

#### Token 效率（程式碼級）

**ego-lite 的 code-base 模式（from `helpers.ts:201-280`）：**

```javascript
// Agent 產出的一段 JS heredoc，整段送 browser 一次執行
// helpers.ts 提供高階 API：
await openOrReuseTab(url)    // helpers.ts:210
await click(locator)          // helpers.ts:230
await fill(locator, text)    // helpers.ts:250
await snapshotText()         // helpers.ts:270 — 回傳語意樹
```

- 複雜任務（如「打開 ChatGPT → 輸入提示詞 → 生成圖片 → 下載 → 重新命名」）只需 1 次 LLM 往返
- `snapshotText()` 回傳的是壓縮後的 Accessibility Tree，token 量遠小於完整 DOM

**BrowserBase 的 tool-base 模式（from chrome-devtools-mcp spec）：**

```
browser_snapshot → LLM 判斷 → browser_click → LLM 判斷 → browser_navigate → ...
```

- 每個操作是獨立的 MCP tool call，LLM 需多次往返
- 無批次執行機制
- 無腳本化/固化機制

**Token 效率結論**：ego-lite 的 code-base 模式從架構上減少 LLM 往返次數，這是 Token 效率的核心來源。BrowserBase 的 MCP tool-base 模式每次操作都是一次 LLM 往返。

#### 瀏覽器操作效率（程式碼級）

**ego-lite 的操作路徑（from `browser-runtime.ts`）：**

```
Agent JS heredoc → CDP（直接）→ Chromium → 結果回傳
```

- `browser-runtime.ts:78-95`：CDP session 管理，支援多 session 並行
- `browser-runtime.ts:98-120`：Event queue 非同步處理，不阻塞主流程
- `browser-runtime.ts:123-145`：15s timeout 防止 hung session
- `helpers.ts:310-380`：Task Space 管理，多 agent 可同時操作不同 Space

**BrowserBase 的操作路徑（from `chrome-devtools-wrapper.sh`）：**

```
Agent MCP call → chrome-devtools-mcp（Node.js）→ CDP → Chrome → 結果回傳
```

- 多一層 MCP server 序列化/反序列化
- 無並行機制（單一 Chrome profile）
- 無 timeout 管理（依賴 MCP server 預設值）

**操作效率結論**：ego-lite 的 Space 架構 + 直接 CDP 通訊在操作效率上有架構優勢。BrowserBase 的 MCP 中介層增加延遲，但使用標準工具。

#### 總評表

| 維度 | 優勢方 | 關鍵原因 |
|------|--------|----------|
| 安全性 | BrowserBase（開源可審計）/ ego-lite（有內建安全機制） | BrowserBase 完全開源；ego-lite 有 Space 隔離 + session 管理但 browser binary 閉源 |
| 易用性 | ego-lite（macOS）/ BrowserBase（跨平台） | ego-lite 自動整合更順暢，但僅限 macOS |
| Token 效率 | ego-lite | Code-base 模式減少 LLM 往返次數；snapshot 壓縮減少頁面 token |
| 操作效率 | ego-lite | Space 架構 + 直接 CDP，無 MCP 中介層；支援多 agent 並行 |

### Q5：為 opencode 與 Claude Code 安裝 ego-lite 的官方逐步指南

**A**：

以下為官方文件（`lite.ego.app/document/`）與 repo 內 `install.md` 提供的安裝方式。

#### 給 Claude Code 安裝（官方方式）

**步驟 1：下載並安裝 ego-lite App**

```bash
# 方式 A：直接下載 DMG（推薦）
curl -L -o /tmp/egolite.dmg https://cdn.ego.app/channel/github_github_referral/setup/macos/arm64/egolite.dmg
# 或手動從 https://ego.app 下載

# 掛載並安裝
hdiutil attach /tmp/egolite.dmg
cp -R /Volumes/ego-lite/ego-lite.app /Applications/
hdiutil detach /Volumes/ego-lite

# 啟動
open -a "ego-lite"
```

**步驟 2：完成首次啟動設定**

1. ego-lite 首次啟動會顯示 onboarding 視窗
2. 點擊「Import from Chrome」匯入現有 Chrome 設定檔（Cookie、擴充功能、書籤）
3. 匯入完成後，ego-lite 會自動掃描本機上的 Agent 工具目錄：
   - `~/.claude/skills/`（Claude Code）
   - `~/.config/opencode/skills/`（OpenCode）
   - 以及其他常見 Agent 目錄
4. 自動將 `ego-browser` skill 寫入對應目錄

**步驟 3：驗證安裝**

```bash
# 確認 ego-browser 在 PATH 中
which ego-browser
# 若無，手動加入 PATH
export PATH="$HOME/.local/bin:$PATH"

# 測試連線
ego-browser nodejs <<'EOF'
const snapshot = await snapshotText();
console.log('Snapshot length:', snapshot.length);
EOF
```

**步驟 4：在 Claude Code 中使用**

在 Claude Code 對話中輸入：

```
/ego-browser 請幫我打開 example.com 並回報頁面內容
```

或使用 heredoc 模式：

```
/ego-browser 請幫我執行以下操作：
1. 打開 chatgpt.com
2. 輸入提示詞「生成一張貓咪圖片」
3. 點擊發送按鈕
4. 下載生成的圖片到桌面
```

#### 給 OpenCode 安裝（官方方式）

**步驟 1：下載並安裝 ego-lite App**

同 Claude Code 的步驟 1-2。ego-lite 會自動將 skill 寫入 `~/.config/opencode/skills/ego-browser`。

**步驟 2：驗證安裝**

```bash
ls ~/.config/opencode/skills/ego-browser/
# 應看到 ego-browser 相關檔案
```

**步驟 3：在 OpenCode 中使用**

在 OpenCode 對話中輸入：

```
/ego-browser 請幫我打開 example.com 並回報頁面內容
```

#### 僅安裝 skill（不安裝 App，不推薦）

若已安裝 ego-lite App，可單獨更新 skill：

```bash
npx skills add citrolabs/ego-lite
```

此指令會從 GitHub 下載最新 skill 定義並寫入對應目錄。

#### 注意事項

| 項目 | 說明 |
|------|------|
| 平台限制 | 目前僅支援 macOS 12+（arm64 + x64） |
| 首次啟動 | 需手動點擊 onboarding 流程（匯入 Chrome 資料） |
| 背景執行 | ego-lite App 需保持運行，agent 才能透過 skill 與之通訊 |
| 防火牆 | 若防火牆阻擋，需允許 ego-lite 的本地通訊（127.0.0.1 隨機 port） |
| 多 agent | 同一 ego-lite 實例可同時服務多個 agent（Claude Code + OpenCode 同時使用） |
