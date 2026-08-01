# terminal-browser 技術分析報告

> 調研日期：2026-07-31 | 版本：v0.3.2 | 來源：gihyo.jp 新聞 + GitHub repo + 官網

---

## 1. 這個技術解決什麼問題？

terminal-browser 解決的是「在既有終端機（terminal）內直接顯示並操作完整 Chromium 瀏覽器」的問題。

具體來說，它讓使用者可以在 terminal pane 內看到一個真正的瀏覽器畫面（含 CSS、JS、canvas 渲染），並透過滑鼠/鍵盤/觸控板直接操作該頁面，同時提供 CLI 讓 coding agent 也能以程式化方式控制瀏覽器（snapshot、click、fill、eval）。

**重要區別**：這與使用者背景中提到的「將原生 binary 搬上瀏覽器執行」是**相反方向**。terminal-browser 是把瀏覽器搬進 terminal，而不是把 terminal 搬進瀏覽器。它**不解決**在瀏覽器沙箱中執行原生 binary 的問題。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- 支援 Kitty graphics protocol 的 terminal（Ghostty、Kitty、cmux、WezTerm 等）已具備在 terminal 內顯示像素的能力，但缺乏一個能將 Chromium 渲染結果導向 terminal 的整合層
- Electron 提供 offscreen rendering API，可在不開視窗的情況下取得 GPU 渲染像素，但沒有現成工具將這些像素餵給 terminal
- 開發者需要在 terminal 中同時查看網頁（例如 localhost 開發伺服器、HTML plan 預覽），但傳統 terminal 只能顯示文字，必須另開瀏覽器視窗切換

### 通用技術背景

- **terminal 的顯示限制**：傳統 terminal 只能顯示等寬文字與 ANSI 色碼，無法直接渲染網頁內容。使用者若要在 terminal 工作流程中查看網頁，只能：
  - 另開瀏覽器視窗（context switch 成本高）
  - 使用 w3m/lynx 等純文字瀏覽器（無法渲染現代 Web 應用）
  - 使用 tmux 分割 + 截圖輪詢（非即時、操作困難）
- **Kitty graphics protocol**：2018 年由 Kitty terminal 開發者 Kovid Goyal 提出的擴充協定，允許 terminal 內的程式透過特定 escape sequence 傳送像素資料。此協定已被 Ghostty、WezTerm、VSCode terminal 等廣泛採用，但生態中缺乏「將完整瀏覽器嵌入 terminal」的實作
- **Agent 操作瀏覽器的需求**：coding agent（如 Claude Code、opencode）需要操作瀏覽器來驗證前端變更、填寫表單、擷取網頁內容。既有方案如 agent-browser、Puppeteer 需要獨立瀏覽器實例，無法與 terminal 內的工作流程整合

---

## 3. 這個技術是如何解決該問題的？

### 整體架構

```
┌─────────────────────────────────────────────────────────┐
│                   使用者 Terminal                        │
│  (Ghostty / Kitty / WezTerm / cmux 等支援 KGP 的 terminal) │
└────────────────────────┬────────────────────────────────┘
                         │ Kitty graphics protocol (escape sequences)
                         │ + terminal input events (mouse/keyboard)
                         ▼
┌─────────────────────────────────────────────────────────┐
│              terminal-browser CLI (TypeScript)           │
│  - terminal-browser open <url>                           │
│  - terminal-browser action -- <command>                  │
│  - terminal-browser ls                                   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Rust Pixel Engine (pixel-core)              │
│  - 接收 Electron 傳來的 pixel buffer                     │
│  - 合成 browser UI（tab bar、網址列等）到同一 canvas     │
│  - 將最終 pixel buffer 編碼為 KGP escape sequence        │
│  - 處理 terminal 輸入事件 → 轉換為 Chromium 合成事件     │
└────────────────────────┬────────────────────────────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
┌─────────────────┐ ┌──────────┐ ┌──────────────┐
│ Electron (browser)│ │ Swift App │ │ pixel-store   │
│ - Chromium 實例   │ │ (背景)    │ │ - state mgmt  │
│ - Offscreen      │ │ - 讀取    │ │ - tab mgmt    │
│   Rendering API  │ │   trackpad│ │ - browser mgmt│
│ - 產出 pixel buf │ │   事件    │ │               │
└─────────────────┘ └──────────┘ └──────────────┘
```

### 核心機制拆解

#### 3.1 像素渲染管線

| 步驟 | 元件 | 說明 |
|------|------|------|
| 1 | Electron (browser/) | 啟動 Chromium 實例，使用 `offscreen rendering API` 在不顯示視窗的情況下渲染網頁，從 GPU 直接讀取 pixel buffer |
| 2 | Rust Engine (engine/) | 接收 Electron 的 pixel buffer，使用 `tiny-skia` 進行 2D 合成，將 browser UI（tab、按鈕、網址列）疊加到網頁畫面上 |
| 3 | Rust Engine → Terminal | 將最終 pixel buffer 編碼為 Kitty graphics protocol 的 escape sequence，寫入 stdout，由 terminal 解析並顯示 |

#### 3.2 輸入事件管線

| 輸入類型 | 來源 | 處理方式 |
|---------|------|---------|
| 滑鼠點擊/移動 | Terminal | terminal 將滑鼠事件編碼為 ANSI escape sequence，terminal-browser 解析後轉換為 Chromium 合成事件 |
| 鍵盤輸入 | Terminal | 同上，透過 terminal 的 keyboard event 傳遞 |
| 觸控板滾動 | Swift Background App | terminal 無法提供 trackpad 的精細滾動事件，因此由一個 Swift 寫的背景應用程式直接從 macOS 的 I/O Kit 讀取觸控板事件，非侵入式監聽 |
| 多點觸控/無限 canvas | Swift App + Chromium | 透過上述機制，支援 Web 應用的 infinite canvas 操作 |

#### 3.3 外框 UI 實作

- **圖形引擎**：Rust 實作（pixel-core + pixel-node），使用 `tiny-skia` 做 2D 渲染、`fontdue` 做字型解析、`taffy` 做 flexbox 佈局
- **UI 定義**：TypeScript + React，透過 custom React renderer（pixel-react）將 React component tree 渲染到 Rust engine 的 canvas 上
- **共享 canvas**：browser UI 與網頁內容繪製到同一個 canvas，實現 tab/按鈕疊加在網頁之上的效果

#### 3.4 Agent 操作介面

`terminal-browser action` 子命令提供 agent-browser 相容的 CLI：

```
terminal-browser action -- snapshot          # 取得頁面截圖
terminal-browser action -- click @e14        # 點擊元素
terminal-browser action -- fill @e3 "hello"  # 填寫表單
terminal-browser action -- eval "doc.title"   # 執行 JS
```

支援 selector：`--browser <key>`、`--tab <id>`、`--target <id>` 選擇操作目標。

#### 3.5 SSH 支援

terminal-browser 在 SSH 連線中運作時，pixel 資料透過 Kitty graphics protocol 的 escape sequence 經由 SSH session 本身傳輸，無需額外 port forwarding。這使得遠端開發者可以直接預覽 remote 機器上的 Web 應用。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|---------|-------------|---------------|-----------------|
| **xterm.js + hterm** | 在瀏覽器中用 JS 實作 terminal 模擬器，透過 WebSocket 連接後端 shell | 瀏覽器環境、後端需提供 shell 存取 | 只能執行 terminal 命令，無法顯示圖形化網頁內容；效能受限於 JS 單執行緒 | 在瀏覽器內獲得 terminal 操作能力 |
| **Headless Chrome + Puppeteer/Playwright** | 無頭模式執行 Chromium，透過 DevTools Protocol 控制，截圖或串流畫面 | 需安裝 Chromium binary，通常需伺服器環境 | 無即時畫面顯示（需自行實作畫面串流）；操作需撰寫程式碼 | 自動化瀏覽器操作，適合 CI/CD 與測試 |
| **VSCode Terminal + Simple Browser** | VSCode 內建 terminal 與 Simple Browser 側邊欄，可在同一視窗內並排顯示 | VSCode 編輯器環境 | 僅限 VSCode 生態；Simple Browser 功能有限（無 tab、無 agent CLI） | 在編輯器內獲得 terminal + 簡易瀏覽器並排 |
| **tmux + w3m/lynx** | 在 terminal 內使用純文字瀏覽器，透過 tmux 分割畫面 | 僅需 terminal 環境 | 無法渲染 CSS/JS/Canvas；現代網站大多無法正常使用 | 在 terminal 內獲得純文字網頁瀏覽能力 |
| **awrit** | terminal-browser 的前身專案，同樣使用 Electron offscreen + Kitty protocol | 同 terminal-browser | 已停止維護，功能較少 | 在 terminal 內顯示 Chromium 畫面 |

### 4.2 切入點差異分析

| 面向 | terminal-browser | xterm.js | Headless Chrome | VSCode Simple Browser |
|------|-----------------|----------|----------------|---------------------|
| **方向** | 瀏覽器 → terminal | terminal → 瀏覽器 | 瀏覽器無畫面 | 瀏覽器 → 編輯器側欄 |
| **畫面即時性** | 即時（60fps） | N/A（純文字） | 需自行實作 | 即時 |
| **Agent 操作** | 原生支援（agent-browser CLI） | 無 | 需自行封裝 | 無 |
| **SSH 支援** | 原生（透過 KGP escape seq） | 需 WebSocket 轉發 | 需 port forwarding | 不支援 |
| **平台限制** | macOS Apple Silicon only | 跨平台（瀏覽器） | 跨平台 | 跨平台（VSCode） |
| **完整 Chromium** | 是 | 否 | 是 | 否（簡易 WebView） |

### 4.3 對使用者核心問題的對照

使用者想解決的問題：**在瀏覽器中執行原生 binary（opencode/claudecode）**

| 方案 | 能否執行原生 binary | 限制 |
|------|-------------------|------|
| terminal-browser | **否** | 方向相反：瀏覽器進 terminal，不是 terminal 進瀏覽器 |
| xterm.js + WebSocket | **部分** | 需後端伺服器提供 shell 環境，binary 在後端執行，瀏覽器僅為顯示端 |
| WebAssembly 重構 | **僅 JS 生態** | 原生 binary（Go/Rust 編譯）無法直接在瀏覽器 sandbox 執行 |
| GAS (Browser) + Native Messaging | **部分** | 需安裝 browser extension + native host，部署複雜 |

**結論**：terminal-browser 不改變「瀏覽器無法直接執行原生 binary」這個本質限制。它解決的是不同方向的問題。

### 4.4 穩定性評估

| 評估面向 | 現狀 | 風險等級 |
|---------|------|---------|
| **專案年齡** | 25 天（2026-07-06 建立） | 高 |
| **版本狀態** | v0.3.2，3 個 minor 版本 / 25 天 | 中（迭代快速但未達 stable） |
| **開發者** | 單一開發者 Rob Pruzan | 高（bus factor = 1） |
| **License** | 無 license 檔案 | 高（無法商用/分發） |
| **平台支援** | macOS Apple Silicon only | 中（Linux WIP，無 Windows） |
| **已知問題** | iTerm click bug、無 brew formula、無 persist partitions | 中 |
| **Stars/社群** | 473 stars，20 forks | 中低（關注度高但貢獻者少） |
| **維護承諾** | 無公開維護計畫或 funding | 高 |
| **Electron 版本** | Electron 43.1.1（最新） | 低（跟進上游） |
| **CI/CD** | GitHub Actions 存在 | 低 |

**綜合評估**：terminal-browser 目前處於**非常早期的原型階段**。技術概念有趣，但以「一年以上中長期維護」的標準來看，風險極高：單一開發者、無 license、無商業模式、僅支援單一平台。不建議將其視為穩定基礎設施。

---

*報告完畢。無 User Q&A 章節（首次產出）。*
