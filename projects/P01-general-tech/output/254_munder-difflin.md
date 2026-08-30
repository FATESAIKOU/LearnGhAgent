# munder-difflin 技術分析報告

> 調研標的：https://github.com/chaitanyagiri/munder-difflin
> 版本：v0.4.6（pre-release） | License：MIT（source code） | Stars：5,493 | 主要語言：JavaScript
> 定位：local multi-agent harness——把既有的終端 agent CLI（claude、codex、opencode、grok、kimi、qwen、copilot 等）包成可協作的「辦公室」，以 hive（記憶＋信箱＋黑板＋事件 log）與一個 GOD orchestrator（Michael）協調，並以 Pixi.js 辦公室地板視覺化。

---

## 1. 這個技術解決什麼問題？

**munder-difflin 解決的問題是：多個既有的終端 agent CLI 各自獨立、彼此無法協作，缺乏一個本機的「團隊層」讓它們共享記憶、交換訊息、分工並受一個仲裁者協調。**

具體而言，它針對以下子問題：

- **agent 之間無法通訊**：Claude Code、Codex、opencode 等 CLI agent 各自是孤立的程序，沒有機制讓一個 agent 的產出交給另一個 agent 接續處理。
- **缺乏共享記憶**：每個 agent 的 session 記憶彼此隔離，跨 agent 的知識（誰做過什麼、結論是什麼）沒有統一載體。
- **缺乏分工與仲裁**：多個 agent 同時工作時，誰負責哪個任務、衝突時誰拍板，沒有明確的協調者。
- **缺乏可審計的歷史**：agent 做了什麼、改了哪些檔案，沒有留下可回放、可稽核的紀錄。
- **缺乏可視化**：多個 agent 的狀態與活動散在各自終端，沒有單一視圖掌握全局。

**問題描述是否含糊**：README 自述「一間 Agent 組成的辦公室」是行銷性描述，非精確定義。實際可調研的具體問題域是「local multi-agent harness」——它不解決「agent 本身的能力」（仍依賴底層 CLI），只解決「把多個 agent 組織成一個可協作團隊」的編排層問題。此定位在 HIVE.md 與 SPEC.md 中有明確的機制支撐。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **終端 agent CLI 是單一程序、單一 session**：Claude Code、Codex、opencode 等設計為「一個使用者對一個 agent」的互動工具，沒有內建的多 agent 通訊或共享狀態。
- **agent 生態碎片化**：不同 CLI 由不同廠商維護，各自有獨立的 session、記憶與工具介面，彼此沒有標準化的協作協定。
- **缺乏統一編排層**：市面上多數 agent 工具停留在「單一 agent 深度協作」，把「多個 agent 分工」留給使用者手動切換終端視窗。

### 通用技術背景（文章中未明確提及，但為必要脈絡）

- **多 agent 協作是 agent 工程的新興問題域**：單一 agent 的 context window 與工具能力有限，把任務拆給多個專精 agent 是自然延伸，但協作機制（通訊、記憶、仲裁、審計）尚未標準化。
- **git 作為審計載體的成熟**：git 提供 append-only 的變更歷史與衝突控制，可被借用為「誰改了什麼」的可稽核紀錄，不需另建審計系統。
- **Electron + node-pty 的成熟**：讓桌面 app 能啟動並接管真實終端程序（node-pty 提供 PTY），是「包裝既有 CLI agent」的技術前提。
- **hook 機制作為 agent 擴充點**：多數 CLI agent 支援 hook（如 Stop hook），讓外部 harness 能在 agent 決策點介入，是 harness 控制 agent 迴圈的關鍵縫隙。

---

## 3. 這個技術是如何解決該問題的？

munder-difflin 以 **Electron 桌面 app** 為殼，把多個終端 agent CLI 包成可協作的團隊。核心機制分四層：**hive（協作層）**、**GOD agent（仲裁層）**、**兩 data plane（終端＋事件）**、**記憶層**。

### 3.1 架構總覽

```
┌────────────────────────────────────────────────────────────┐
│                    munder-difflin (Electron)                 │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Renderer (React 18 + Pixi.js 辦公室地板視覺化)        │   │
│  │  - avatar 由 Event Plane 驅動                          │   │
│  └───────────────────────┬──────────────────────────────┘   │
│                          │ IPC                              │
│  ┌───────────────────────┴──────────────────────────────┐   │
│  │  Main Process (Node.js)                                │   │
│  │  - 唯一 git committer（寫 hive）                       │   │
│  │  - router（outbox→inbox 搬移）                         │   │
│  │  - blackboard 單一 scribe                              │   │
│  └───────────────────────┬──────────────────────────────┘   │
│                          │ 啟動 / hook / PTY                │
│  ┌───────────────────────┴──────────────────────────────┐   │
│  │  GOD agent (Michael) = 固定常駐 claude 程序            │   │
│  │  - roster / routing / 仲裁 / task ledger               │   │
│  └───────────────────────┬──────────────────────────────┘   │
│                          │                                 │
│  ┌───────────────────────┴──────────────────────────────┐   │
│  │  Agent CLI 群（claude / codex / opencode / ...）       │   │
│  │  各自透過 hive 的 inbox/outbox 通訊                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  hive = 本機 git repo（<harnessHome>/hive/）           │   │
│  │  - agents/<id>/ 每 agent 只寫自己的目錄                │   │
│  │  - 共享 blackboard / 事件 log / task ledger            │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

### 3.2 核心機制

#### (1) hive：git-as-audit 的協作層

- hive 是**本機 git repo**（`<harnessHome>/hive/`），作為所有 agent 共享的記憶與通訊載體。
- **僅 main process 單一 committer**：所有寫入由 main process 統一 commit，避免多個 agent 同時寫 git 造成 `index.lock` 衝突。
- **single-writer-per-file**：每個 agent 只寫自己 `agents/<id>/` 目錄下的檔案，避免檔案層級寫入衝突。
- **跨 agent 傳遞由 router 搬移**：sender 把訊息寫進自己 `outbox/`，router 把檔案移到 recipient 的 `inbox/`，agent 讀 inbox 即收到訊息。
- **git 即審計**：所有變更以 commit 形式留下歷史，可回放「誰在何時改了什麼」。

#### (2) GOD agent（Michael）：仲裁與協調

- **固定常駐 `claude` 程序**，不隨任務結束而退出，作為團隊的常設協調者。
- 職責：**roster**（誰在團隊裡）、**routing**（訊息該給誰）、**仲裁**（衝突時拍板）、**blackboard 單一 scribe**（共享黑板只有它能寫）、**task ledger**（任務清單）。
- **升級原則**：routine 任務由 agent 自行解決；**critical**（花費、破壞性、scope）才升級給人。

#### (3) 自主迴圈：Stop-hook 驅動

- 利用 CLI agent 的 **Stop hook**：hook 回 `{"decision":"block"}` 讓 agent 不結束、持續 drain inbox，形成自主處理訊息的迴圈。
- 以 `stop_hook_active` + cursor 防止無限迴圈。

#### (4) 兩 data plane：Terminal + Event

| Plane | 內容 | 用途 |
|---|---|---|
| **Terminal Plane** | node-pty 真實位元組 | 實際執行 agent CLI，傳輸真實終端輸出 |
| **Event Plane** | hooks → UDS（Unix Domain Socket）→ renderer | 把 agent 的決策/活動事件送到 renderer，驅動 Pixi.js avatar 動畫 |

- 兩 plane 分離：Terminal 管「實際運算」，Event 管「可視化狀態」，互不阻塞。

#### (5) 記憶層：markdown-first + 語意層

- **markdown-first**：`memory.md` + 共享 blackboard，以人類可讀的 markdown 為主要記憶載體。
- **SQLite FTS**：全文檢索加速查詢。
- **語意層用 MemPalace CLI（非 MCP）**：detect-and-degrade 為 no-op（偵測不到就降級為無操作，不阻塞主流程）。

#### (6) 技術棧

Electron 32 / React 18 / Pixi 8 / xterm 5 / node-pty / better-sqlite3 / zustand / monaco。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

以下替代方案**已對照第二大腦（FATESAIKOU/MyBrain）的既有判定**。每則標 GitHub URL 與信任層級；AI draft 均為未經他 review 的草稿。

### 4.1 第二大腦既有判定（同問題域）

| 標的 | 判定 | 信任層級 | 來源 |
|---|---|---|---|
| **Aionui** | 採用 | `human:fatesaikou` / `stable` | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Aionui.md |
| **DeerFlow** | 觀望 | `human:fatesaikou` / `stable` | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/DeerFlow%20學習紀錄.md |
| **Understand-Anything** | 採用 | `human:fatesaikou` / `stable` | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Understand-Anything.md |
| **deepseek-harness（dsh）** | 觀望（Reserve） | `process:learn-gh-agent` / `draft` | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/DeepSeek%20Harness.md |

**判定語意**（依技術取捨準則，`claude-code/opus-5` / `draft`，未經他 review）：「採用」＝進 Judge/MVP 或 Feature；「觀望」＝有價值但未排入下一步；「不採用」＝不採用≠沒價值，仍抽取需求理解與方案方向。見 https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md

### 4.2 DA 表：替代方案對照

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Aionui**（第二大腦：採用） | Electron 前端 + Rust 後端（AionCore），內建 agent 引擎 + ACP 多 agent 協作協定 + Team Mode（Leader 拆解任務分配給 Teammate）+ 排程 + 遠端存取 | 需安裝桌面 app；多 agent 協作依賴其自定義 ACP 協定 | 綁定 AionCore 內建引擎與 ACP 生態；OfficeCLI 連動為其特色但非通用 | 統一桌面介面管理多個 agent，agent 間以 ACP 協作；他特別在意 OfficeCLI 連動、ACP 協定、私人 Agent 系統設計 |
| **DeerFlow**（第二大腦：觀望） | 多智能體框架，LLM 動態決定下一步工具呼叫 | 需程式開發能力；Python 環境 | 動態流程無審計性、除錯成本高（出錯要翻 agent 對話 log） | 高任務泛用性，但缺乏可稽核的執行軌跡 |
| **Understand-Anything**（第二大腦：採用） | 多代理管線將程式碼庫轉為互動式知識圖譜 | 需對陌生大型程式碼庫做理解 | 專注「理解程式碼」單一場景，非通用 agent 協作 | 讓人能 Review AI 產出、掌握程式庫架構 |
| **deepseek-harness（dsh）**（第二大腦：觀望/Reserve） | 一切皆插件的 agent harness，session log 是 model 可見性唯一來源，capability seam 三件套 | 需接受 Cordis 框架綁定與事件域選域學習成本 | 很重型，無法立刻 Accept | 可重放、可審計的 session；機制可參考個人 AiAgent 入口設計 |

### 4.3 切入點差異分析

- **munder-difflin vs Aionui**：兩者都是「把多個 agent 組織成團隊」的桌面 harness。差異在**協作載體**——munder-difflin 用 **git repo（hive）** 作為記憶與通訊載體，Aionui 用 **ACP 協定 + 內建引擎**。munder-difflin 更貼近「包裝既有 CLI」的輕量路線，Aionui 更貼近「自帶引擎」的整合路線。
- **munder-difflin vs DeerFlow**：DeerFlow 是「LLM 動態決定下一步」的彈性 workflow，**無審計性**；munder-difflin 以 **git-as-audit** 提供可稽核的變更歷史，直接回應他對 DeerFlow「無審計性」的疑慮。
- **munder-difflin vs Understand-Anything**：Understand-Anything 是「多代理管線理解程式碼」的單一場景工具；munder-difflin 是「多 agent 通用協作」的 harness，場景更廣但沒有 Understand-Anything 的知識圖譜產出。
- **munder-difflin vs deepseek-harness**：dsh 是「一切皆插件」的重型 harness，session log 是 model 可見性唯一來源（強審計）；munder-difflin 是較輕量的 git-based harness。dsh 被判定 Reserve（重型），munder-difflin 的輕量 git 路線與此形成對照。

### 4.4 對照他的技術取捨準則（`claude-code/opus-5` / `draft`，未經他 review）

來源：https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md

| 準則 | munder-difflin 的對應 |
|---|---|
| **理解優先**：不穩定或不熟悉就先自己兜，MVP 是理解驗證點 | munder-difflin 是 v0.4.6 pre-release、單人維護、2026-05-31 才建立（約 3 個月），屬「不穩定/不熟悉」→ 依準則一，這反而是「先自己兜」的觸發條件，而非直接採用 |
| **MVP→Feature 唯一閘門**：能否影響個人 workflow | 他正在構思「個人 AiAgent 入口」（執行環境未定），munder-difflin 的「把終端 agent CLI 包成協作團隊」與此形態高度重疊，是直接相關的參考標的 |
| **Reject ≠ 沒價值**：仍抽取需求理解與方案方向 | 即使不採用，munder-difflin 的「git-as-audit 單 committer」「single-writer-per-file」「Stop-hook 自主迴圈」是可抽取的方案方向 |
| **約束在 harness 不在權限**：不要建議加人工審核關卡，要補驗證機制 | munder-difflin 的 git-as-audit 正是「驗證機制」而非「人工審核關卡」，與此準則一致 |

### 4.5 與他的進行中專案關聯（`claude-code/opus-5` / `draft`，未經他 review）

來源：https://github.com/FATESAIKOU/MyBrain/blob/main/技術/靈感/個人%20AiAgent%20入口.md

- 他正在構思「個人 AiAgent 入口」：app＋拆開後端、ChatSession、擴張 MyBrain 讀寫權限；**整個專案卡在執行環境未定**（自架實體 vs 自架雲端 vs 跑在終端）。
- munder-difflin 的「把終端 agent CLI 包成協作團隊」與此專案形態高度重疊，是直接相關的參考標的。
- 但**衝突點**：他的「個人 AiAgent 入口」強調**拆開前後端**（GAS 或 Docker container 後端），而 munder-difflin 是 **Electron 桌面 app 單體**（main process 兼 committer/router/scribe）。兩者架構取向不同——munder-difflin 的協作機制（hive、git-as-audit）可參考，但其「桌面單體」形態與他「拆開後端」的目標不一致。

### 4.6 與他的審計性疑慮的關係

- 他對 DeerFlow 的判定是「動態流程有價值但**無審計性**、除錯成本高」（`human:fatesaikou` / `stable`）。
- munder-difflin 以 **git-as-audit** 提供可稽核的變更歷史，**正面回應**了這個疑慮——這是它與 DeerFlow 的關鍵差異，也是對照最有價值的地方。
- 但需注意：git-as-audit 記錄的是「檔案變更」，**不保證記錄「agent 的決策過程」**。dsh 的「session log 是 model 可見性唯一來源」才是對決策過程的強審計。若他的審計需求是「決策軌跡」而非「檔案變更」，munder-difflin 的 git-as-audit 只覆蓋後者。

---

## 附錄：調研資料來源

- README.md（374 行）：產品定位、架構、功能
- HIVE.md（217 行）：協作層設計（git-as-audit、單 committer、single-writer-per-file、god agent 仲裁、FIPA-lite 訊息 schema、Stop-hook 自主迴圈）
- SPEC.md（314 行）：終端/事件平面（Terminal Plane + Event Plane、Sims 隱喻狀態機）
- MEMORY_GRAPH_SPEC.md（212 行）：記憶層視覺化（force-directed SVG、topic 抽取、MemPalace 語意記憶）
- DESIGN.md、package.json、docs/message-queue.md、CHANGELOG.md、docs/research 清單
