# Maka — Apache 的本地優先 AI Agent 工作台

> 標的：`https://github.com/apache/maka`（Apache Incubating）
> 調研基準：README、ARCHITECTURE.md、DESIGN.md、docs/architecture/runtime-host-architecture.md、docs/architecture/runtime-core-architecture-draft.md（皆為 repo 內文件，2026-08-30 時點）

---

## 1. 這個技術解決什麼問題？

Maka 要解決的具體問題是：**一個 AI agent 在執行多步任務時，其模型輸出、工具呼叫、工具結果、權限決定與終止事件分散在多處、缺乏單一可稽核的紀錄來源（single source of truth），導致使用者無法信任、無法重現、無法稽核 agent 到底做過什麼、以及出錯後無法乾淨地復原。**

更精確地拆解，Maka 面對的是三個相互關聯的缺陷：

| 缺陷面向 | 具體內容 |
|---|---|
| 可信度 | agent 的行為（每通 model message、每次 tool call、每次 tool 回傳、每次 permission 決定）散落在不同層級，使用者無從查證「它真的照我允許的方式執行」 |
| 復原性 | 任務中途失敗或需要中斷時，沒有乾淨的 checkpoint，無法從已知狀態續跑（recovery / resume），只能從頭重來 |
| 治理 | agent 工具執行的邊界（sandbox、權限、Eval）缺乏統一的執行權威與稽核軌跡，多 surface（Desktop／TUI／CLI）各自執行會造成行為不一致 |

Maka 的宣稱是「**Log Is the Runtime**」——把 runtime 的語意真相（semantic source of truth）定義為一條 **append-only 的 Runtime Event Log**，所有其他狀態（model history、UI、終端、復原）都是這條 log 的 **projection（投影）**。

### 問題描述本身的模糊之處

「工作台（workspace）」一詞在 README 與 DESIGN.md 中定義得相當廣，涵蓋「任務組織」「permission 檢視」「activity 檢視」「failures 檢視」等，這與市面上常見的「AI 聊天應用」「agent 框架」「agent harness」邊界重疊。文件並未嚴格區分「Maka 是給人用 agent 的介面」vs「Maka 是 agent 本身」——實際架構中 Runtime Host 是執行權威、surface 只是前端，但「到底 Maka 的 agent 邏輯在哪一層」需要從 runtime-core 的 draft 文件才能判讀，屬未完全定稿的模糊地帶。

---

## 2. 這個問題為什麼會發生？（背景）

### 文中明確提到的背景

- **Runtime 的執行生命週期超越單一 HTTP request**：`docs/architecture/runtime-host-architecture.md` 明確指出 agent runtime 的工作會跨越單一 request connection 的壽命。傳統「request → response」的 web 模型假設狀態在單次請求內完結，但 agent 多步任務需要長時間持有狀態、在異步執行中維持一致性，這迫使狀態必須被持久化到「執行層之外」——這是 Runtime Event Log 與 Runtime Host 出現的直接動機。
- **多 surface 需要單一權威**：Maka 提供 Desktop、TUI、CLI 三種 surface（外加 Eval），若每種 surface 各自內嵌 agent 執行邏輯，同一任務在不同介面上行為會分叉。因此架構把「執行權威」收斂到單一 Runtime Host，surface 只當 client。

### 通用技術背景（文章未明說，屬環境脈絡）

| 背景 | 說明 |
|---|---|
| AI agent 的「行為可稽核」需求 | LLM 是非確定性的，工具呼叫又具備真實副作用（寫檔、改狀態、呼叫外部服務）。過去 CLI agent 工具（如各種 REPL 式 harness）傾向只把 model 的來回訊息存成 chat log，**工具呼叫與權限決定常不進 log**，造成「對話紀錄完整但行為不可稽核」。 |
| 事件溯源（Event Sourcing） | Runtime Event Log 本質是事件溯源思維：以不可變、append-only 的事件序列為真相來源，狀態是事件的投影。此模式在分散式系統與金融系統中成熟，Maka 把它套到 agent runtime 的狀態管理。 |
| local-first 軟體運動 | 使用者的資料與執行都留在本機（Electron userData／workspaces），不依賴雲端服務——呼應 local-first 對資料自主權與隱私的訴求。 |
| Apache 生態的治理偏好 | 專案採 Apache Incubating 流程，架構文件（ARCHITECTURE.md／DESIGN.md）詳實，反映「先定義清楚架構與執行邊界再實作」的治理風格。 |

---

## 3. 這個技術是如何解決該問題的？

Maka 的解法核心是兩件事：**單一執行權威（Runtime Host）＋ 以 Runtime Event Log 為真相來源的事件溯源架構**。以下分層說明。

### 3.1 總體架構（ARCHITECTURE.md）

```
┌─────────────────────────────── Maka ───────────────────────────────┐
│                                                                     │
│   Surface 層        Desktop (Electron+React) │ TUI │ CLI │ Eval    │
│                          │                     │      │            │
│                          ▼                     ▼      ▼            │
│   Runtime 層       ┌─── Runtime Host（單一執行權威）────────────┐   │
│                    │   ├ Host Kernel                          │   │
│                    │   ├ Composition（組 agent graph）          │   │
│                    │   ├ Domain Modules                       │   │
│                    │   └ Hosted Execution                     │   │
│                    └───────────────────────────────────────────┘   │
│                          │                                          │
│   Storage 層      ┌─── Runtime Event Log（append-only）───────────┐ │
│                    │   = canonical / semantic source of truth     │ │
│                    └──────────────────────────────────────────────┘ │
│                          │ projection                              │
│                          ▼                                          │
│   Projection 層   Model History │ UI │ Terminal │ Recovery/Resume    │
└──────────────────────────────────────────────────────────────────────┘
```

- **三種 surface 皆經同一 Runtime Host**，不各自內嵌執行邏輯。
- **State 是 log 的投影**：`State(t) = Project(RuntimeEvents[0..t], policy, config)`。

### 3.2 Runtime Event Log 為核心（runtime-core-architecture-draft.md）

這是 Maka 最關鍵的設計主張——**「Log Is the Runtime」**：

| 機制 | 內容 |
|---|---|
| 紀錄對象 | model messages、tool calls、tool results、permission decisions、termination events |
| 寫入方式 | **append-only**，不可刪改，確保稽核軌跡不可竄改 |
| 真相地位 | Runtime Event Log 是語意上的真相來源（semantic source of truth），其他一切狀態都由此投影 |
| 投影產物 | Model-history（對話歷史）、UI（畫面狀態）、Terminal（輸出）、Recovery（復原）皆為 log 的 projection |

```
State(t) = Project( RuntimeEvents[0..t], policy, config )
                │
                ├── Model-history projection → 給 agent / 使用者看對話脈絡
                ├── UI projection            → 渲染畫面
                ├── Terminal projection      → 輸出到終端
                └── Recovery projection      → 支援 resume / 復原
```

好處：**只要 log 完整，任何一時刻的狀態都可重建**，出錯可回溯，任務可從已知事件點恢復。

### 3.3 Runtime Host 為單一執行權威（runtime-host-architecture.md）

| 部件 | 職責 |
|---|---|
| **Host Kernel** | 持有狀態根（State Root）的**獨佔 lease**，確保同一時間只有一個執行實體能改動 runtime 狀態 |
| **Composition** | 組裝 agent graph（agent 之間的連線與依賴） |
| **Domain Modules** | 業務領域邏輯模組 |
| **Hosted Execution** | 在 sandbox 邊界內執行工具呼叫 |

- **State Root 獨佔 lease**：避免多 surface 或多執行個體同時寫狀態造成競態，這是「單一權威」的實作保證。
- **Turn 流程**（sequence）：Host 接收請求 → 檢查 lease → 執行 agent turn → 把事件 append 進 log → release lease → 各 projection 更新。

### 3.4 本地資料與 recovery（README）

| 面向 | 內容 |
|---|---|
| 資料位置 | Electron `userData`／`workspaces/default`（如 `runtime.sqlite`、`credential-vault.json`） |
| resume | **預設關閉**，為 opt-in 功能——因為重建是 log 的投影，原則上可支援，但預設不主動啟動 |
| 執行邊界 | 工具在 **sandbox 邊界**內執行，permission 決定會記錄進 log |

### 3.5 Eval 邊界（ARCHITECTURE.md）

Eval 是第四種 surface，用於評估，具獨立邊界層級：**Experiment / Cell / Attempt**，讓評估任務與正式執行在邊界上分離，避免污染實際使用軌跡。

### 3.6 產品定位（DESIGN.md）

產品設計的北極星為 **「The Companion Command Center」**——以 **task** 為中心，讓 activity、permissions、failures 都可視、可檢視、可稽核。這與 §1 的「以 log 為真相、可稽核」主張一致：log 不只是技術機制，也是產品上「讓使用者看得見 agent 做了什麼」的基礎。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

Maka 所處的問題域是「**agent 工作台 / agent harness**」——即以一個介面統一管理、執行、稽核 AI agent。以下替代方案同時對照第二大腦 FATESAIKOU/MyBrain 的既有判定（信任層級與時間已標註）。

### 4.1 替代方案清單

| 技術 | 切入點 | 對照第二大腦判定 |
|---|---|---|
| **Aionui** | 多 AI agent 統一桌面協作平台（Electron＋Rust），聚焦「同時管理、排程、遠端存取多個 agent，讓 agent 之間協同」 | `採用`（`human:fatesaikou`／`stable`）——**使用者已定稿採用**，理由在意 OfficeCLI 連動與 MultiAgent |
| **Buzz** | Block 打造的人與 Agent 協作工作台，統一事件流與權限控制，整合需求/程式碼/CI/CD/任務追蹤於單一介面 | `不採用`（`opencode/deepseek-v4-pro`／`draft`）——**AI 草稿，未經使用者 review**；理由：規模過大、個人使用不必要、效果未知 |
| **macro** | 開源團隊工作台＋團隊級記憶系統（一切皆 block＋@mention 雙向連結＋每晚 cron 合成記憶） | `不採用`（`process:learn-gh-agent`／`draft`）——**流程產出草稿，非使用者本人**；理由：太重型、記憶無防腐化機制；但資料模型原語可借鑑 |
| **odysseus** | 一站式本地 AI 工作空間（聊天＋Agent＋本地模型下載伺服＋深度研究＋文件編輯＋郵件行事曆筆記管理），資料全在本地 | `不採用`（`human:fatesaikou`／`stable`）——**使用者已定稿不採用**；理由：本質是 Local LLM Model 的 wrapping、意義不大 |
| **deepseek-harness（dsh）** | DeepSeek 開源 agent harness，一切皆插件、Cordis 驅動、session log 為 model 可見性唯一來源 | `觀望`（`process:learn-gh-agent`／`draft`）——**流程產出草稿，非使用者本人**；理由：很重型無法立刻 Accept，但機制可參考個人 AiAgent 入口設計 |

> 信任層級判定來源：`/tmp/mybrain @ b0d3826 (2026-08-24)`。判定總表為 `技術/技術評估/判定總表.md`（AI 草稿，`status: draft`，`by: ollama-cloud/deepseek-v4-flash`）。各技術原文見 `技術/技術評估/<名稱>.md`。**注意：Buzz、macro、deepseek-harness 的「不採用／觀望」為 AI 或流程草稿，非使用者本人定稿，僅 Aionui 與 odysseus 為 `human:fatesaikou`／`stable` 的本人定稿。**
> 
> 另：第二大腦 **無 maka 此主題**（grep `maka` 零命中），故 maka 無先前判定；上述替代方案的判定為既有同域判定，不代表對 maka 的結論。

### 4.2 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Maka** | Runtime Host 單一執行權威＋Runtime Event Log 為 append-only 真相來源，狀態皆 log 投影；Desktop/TUI/CLI/Eval 四 surface 皆經同一 Host；sandbox 邊界執行工具 | Apache Incubating、TypeScript；需本機 Electron userData；需接受事件溯源架構（狀態皆由 log 重建） | 事件溯源增加架構複雜度；resume 預設關閉；專案仍在 Incubating（架構部分仍為 draft）；多 surface 需統一 lease 機制 | 單一可稽核真相來源、乾淨復原、多 surface 行為一致、本機資料自主 |
| **Aionui** | 多 agent 桌面協作平台，統一台面管理/排程/遠端存取多個 agent，支援 agent 間協同（ACP 協作協定） | 需要多 agent 同時協同的場景；Electron＋Rust；需連動既有 GUI 工具 | 鎖定桌面多 agent 協作；與 OfficeCLI 連動需額外整合；協作協定依賴其生態 | 單一桌面入口管理多 agent、agent 間協同、GUI 整合（使用者採用的理由） |
| **Buzz** | 人與 Agent 協作工作台，統一事件流＋權限控制，整合需求/程式碼/CI/CD/任務追蹤 | 大型團隊協作；需整合完整專案管理＋CI/CD 鏈 | 規模過大、個人使用效益不明；與個人 workflow 脫節 | 一站式團隊協作＋事件流治理（但使用者評估個人價值不高） |
| **macro** | 一切皆 block＋@mention 雙向連結＋每晚 cron 合成記憶＋Agent 層的團隊工作台 | 需要團隊級記憶與雙向連結的工作空間；接受重型架構 | 太重型；記憶無防腐化機制；涵蓋多問題域 | 統一 block 資料模型＋自動合成記憶（資料原語可借鑑） |
| **odysseus** | 本地 LLM 聊天＋Agent＋模型下載伺服＋深度研究＋文件/郵件/行事曆/筆記的一站式空間 | 自有硬體可跑本地模型；需要全本地資料 | 本質是 Local LLM wrapping，LLM 能力與工具深度有限；fenced code block 工具呼叫模式 | 全本地一站式工作空間（使用者評估意義不大） |
| **deepseek-harness（dsh）** | 一切皆插件、Cordis 驅動、session log 為 model 可見性唯一來源的 agent harness | 可接受重型插件架構；參考個人 AiAgent 入口設計 | 太重無法立刻採用；需等更輕量方案或入口架構定案 | 插件化 harness＋log 為唯一 model 可見性來源（個人 AiAgent 入口可參考） |

### 4.3 切入點差異

| 維度 | Maka | Aionui | Buzz | macro | odysseus | dsh |
|---|---|---|---|---|---|---|
| 核心主張 | **log 為真相**＋單一 Runtime 權威 | 多 agent 桌面協同 | 人與 agent 統一工作台＋權限 | 團隊記憶＋block 資料模型 | 全本地一站式 | 一切皆插件＋log 可見性 |
| 治理重心 | 稽核與復原（event sourcing） | 協同（多 agent 管理） | 團隊協作＋CI/CD | 記憶合成 | 本地模型包裝 | 插件擴充 |
| 執行權威 | 單一 Runtime Host＋State Root lease | 各 agent 協作協定 | 統一事件流＋權限控制 | Agent 層＋cron 合成 | 本機模型 | Cordis 插件 |
| 對個人（使用者） | 可稽核、可復原、多 surface | 已採用 | 個人價值低（draft） | 太重型（draft） | 已不採用 | 觀望中（draft） |

### 4.4 與使用者既有立場的關係與衝突點

- **與「個人 AiAgent 入口」構想同域**：`技術/靈感/個人 AiAgent 入口.md`（`claude-code/opus-5`／`draft`，2026-08-11）描述他想要「app＋拆開後端、ChatSession、擴張 MyBrain 讀寫權限」的個人 agent 入口，卡在執行環境未定。Maka 的「Runtime Event Log 為真相來源」與「Runtime Host 單一權威」架構，與他入口專案的「ChatSession 記錄與切換」需求高度同域——Maka 可作為該構想的**架構參考**。
- **與「技術取捨準則」的關係**：`抽象理解/本質洞察/技術取捨準則.md` 載明「理解優先：先自己兜→MVP」「Reject ≠ 沒價值」「MVP→Feature 唯一閘門是能否影響個人 workflow」。據此，**本報告對 maka 不下「採用／不採用」結論**——這是使用者本人的決策，不在此代決。
- **衝突點需指出**：Buzz 與 macro 的「不採用」判定是 **AI／流程草稿**（前者 `opencode/deepseek-v4-pro`，後者 `process:learn-gh-agent`），非使用者本人定稿。若把這些草稿當成使用者的既定立場，會高估其信任依據。此為查詢第二大腦時需特別留意之處。
- **Aionui 為使用者本人採用的同域工具**（`human:fatesaikou`／`stable`），在評估 Maka 的替代價值時，Aionui 是既有已採用選項，Maka 與之的定位（事件溯源 vs 多 agent 協同）明顯不同。

---

## 附註

- 本報告 §4 之第二大腦判定與信任層級以 `/tmp/mybrain @ b0d3826 (2026-08-24)` 為基準；AI／流程產出的判定已註明為草稿、非使用者本人 review。
- Maka 本身為 Apache Incubating 專案，部分架構文件（runtime-core-architecture-draft.md）標有 `draft`，其「Log Is the Runtime」主張之最終實作仍待專案發展確認。
