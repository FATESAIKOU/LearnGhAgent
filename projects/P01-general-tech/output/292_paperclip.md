# Paperclip 技術分析報告

> 調研標的：https://github.com/paperclipai/paperclip
> 調研日期：2026-10-05
> repo 實查（`gh api`）：Stars 97,420、License MIT、主要語言 TypeScript（87.8MB）＋ Rust（2.7MB）、建立 2026-03-02、預設分支 `master`、fork 16,478、homepage paperclip.ing、最新 release v2026.1001.0（2026-10-02）、最新 commit 2026-10-05、npm 首發 2026-03-03
> 定位：AI agent 團隊的開源**控制平面（control plane）**。README 核心類比句：「If OpenClaw is an *employee*, Paperclip is the *company*.」
> repo 實查（R2 @ 2026-10-05）：Stars 97,626、fork 16,499、27 個 release、adapters 13、sandbox-providers 8（詳見 §5 Q2）。
> **資料來源限制**：GitHub 一周熱點 133 期影片無字幕軌（YouTube transcripts disabled），逐字稿取不到，影片觀點與示範內容未納入本報告；本報告內容全部來自 repo 文件（README／`doc/GOAL.md`／`doc/PRODUCT.md`／`doc/SPEC.md`／`doc/plugins/PLUGIN_SPEC.md`／`doc/memory-landscape.md`）與 GitHub API 實查。

---

## 1. 這個技術解決什麼問題？

**Paperclip 解決的問題是：當「員工」全部是 AI agent 之後，既有的任務管理軟體不夠用——缺的是一間公司的「控制平面」，而不是一張待辦清單。**

被解決的具體問題可拆為下列子問題：

| # | 子問題 | repo 文件中的對應描述 |
|---|---|---|
| 1 | 多個 agent 各自獨立、失去追蹤 | 「你有 20 個 Claude Code 分頁開著，記不清哪個在做什麼；重開機全部遺失」 |
| 2 | 任務與目的脫鉤 | agent 不知道「為何做這件事」，缺少從任務往上的目標脈絡 |
| 3 | 成本失控 | 「失控迴圈燒掉數百美元 token、吃光額度，而你還不知道發生了什麼」 |
| 4 | 缺乏組織與治理 | 「一堆散亂的 agent config 資料夾，你得自己重造任務管理、通訊與協調機制」 |
| 5 | 無法規模化營運 | 缺少角色、權限、審核、預算這些「公司層」的機制 |

**問題描述是否含糊**：`doc/GOAL.md` 的願景句（「Paperclip 是自主經濟的骨幹」、要讓 AI 公司產出「可與世界大國 GDP 匹敵的經濟產出」）屬宣言性描述，非可驗證的問題定義。可調研的具體問題域是 `doc/PRODUCT.md` 明列的那句：**「Task management software doesn't go far enough. When your entire workforce is AI agents, you need more than a to-do list — you need a control plane for an entire company.」** 本報告以這句為問題定義的基準。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **終端 agent 是一對一、單 session 的工具**：Claude Code、Codex、Cursor、Gemini CLI、OpenCode 等設計為「一個人對一個 agent」的互動工具，本身不含多 agent 的組織、通訊與成本治理。
- **agent 生態碎片化**：不同 harness 各有 session、記憶與工具介面，彼此沒有標準協作協定。README 的 FAQ 直接以「為什麼不把 OpenClaw 指向 Asana／Trello」自問，並回答「agent orchestration 有許多細微處：誰把工作 checkout 走了、session 怎麼續接、成本怎麼監控、治理怎麼建立」。
- **「員工是 agent」改變了管理單位的尺度**：傳統工具管理的是「人＋任務」，此情境要管理的是「agent 的身分、權限、預算、產出與稽核」。`doc/PRODUCT.md` 因此把 **company 定為 first-order object**。

### 通用技術背景（repo 未明述，但為必要脈絡）

- **heartbeat／wakeup 是長時任務 agent 的常見執行模型**：agent 不常駐，靠外部喚醒（heartbeat）、執行、回報，是可水平擴充的前提。Paperclip 的「If it can receive a heartbeat, it's hired.」即建立在此模型上。
- **control plane / execution plane 分離**：把「編排與治理」與「實際執行 agent」分離，是系統可水平擴充與可替換 runtime 的架構慣例。Paperclip 明採此分離（見 §3）。
- **本機優先（local-first）＋ 內嵌資料庫**：Node.js 生態讓單一 process 內嵌 PostgreSQL 與本機檔案儲存成為可行，使「零設定開跑」成為可能。
- **agent 的產出需要可稽核**：agent 自主工作若要放行，變更與花費需留下可回放紀錄；對應 Paperclip 的 activity log、run history、revision。

---

## 3. 這個技術是如何解決該問題的？

Paperclip 以 **Node.js server ＋ React UI** 為殼，實作一個**控制平面**；agent 本體仍在外部執行，透過 adapter 回報。

### 3.1 架構總覽

```
┌──────────────────────────────────────────────────────────────┐
│                       PAPERCLIP SERVER                       │
│                                                              │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│  │Identity & │  │  Work &   │  │ Heartbeat │  │Governance │  │
│  │  Access   │  │   Tasks   │  │ Execution │  │& Approvals│  │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘  │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│  │ Org Chart │  │Workspaces │  │  Plugins  │  │  Budget   │  │
│  │ & Agents  │  │ & Runtime │  │           │  │ & Costs   │  │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘  │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│  │ Routines  │  │ Secrets & │  │ Activity  │  │  Company  │  │
│  │& Schedules│  │  Storage  │  │ & Events  │  │Portability│  │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘  │
└──────────────────────────────────────────────────────────────┘
         ▲              ▲              ▲              ▲
   ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴─────┐
   │  Claude   │  │   Codex   │  │   CLI     │  │ HTTP/web  │
   │   Code    │  │           │  │  agents   │  │   bots    │
   └───────────┘  └───────────┘  └───────────┘  └───────────┘
        （execution plane：agent 在外部執行，phone home）
```

### 3.2 四個核心機制

#### (1) Company 為單位 ＋ 目標樹（Goal Alignment）

- **Company 是 first-order object**：一個 instance 可跑多間公司，各有獨立的 task／agent／權限／活動史。
- **所有工作必須向上追溯到公司目標**，形成 parent 鏈：

```
我正在研究 Facebook 廣告（current task）
  because → 我要為軟體做 Facebook 廣告（parent）
    because → 我要增加 100 個新註冊（parent）
      because → 我要這週營收達到 $2,000（parent）
        ... → 我們要打造第一名的 AI 筆記 App、3 個月做到 $1M MRR
```

- 每個任務因而能回答「我為何在做這件事」，這是 alignment 的機制本體。

#### (2) Org Chart ＋ Adapter（角色與執行邊界）

- **每個 employee 都是一個 agent**，具有角色、title、匯報線、權限、預算。
- **agent 的身分與行為由 adapter config 定義**（例如 OpenClaw 用 `SOUL.md`／`HEARTBEAT.md`、Claude Code 用 `CLAUDE.md`）。Paperclip **不規定**格式，由 adapter 決定——最小契約只有「be callable」。
- 支援的執行方式有四類：

| 類別 | 做法 | heartbeat 語義 |
|---|---|---|
| Local CLI/session adapter | 啟動或續接 Claude Code／Codex／Gemini／OpenCode／Pi／Cursor | 執行該 session 並追蹤 |
| Run a command | 跑一個 process（shell／Python）並追蹤 | 執行並監控 |
| Fire-and-forget request | 對外部常駐 agent 發 webhook／API | 通知該 agent 醒來（OpenClaw 風格） |
| External adapter plugin | 透過 plugin flow 動態載入 adapter 套件 | 可擴充 runtime |

#### (3) Heartbeat Execution（喚醒—執行—回報）

- **DB-backed wakeup queue ＋ coalescing**：agent 被排入喚醒佇列（任務指派、follow-up、排程觸發），執行時依序做 **budget 檢查 → workspace 解析 → secret 注入 → skill 載入 → adapter 呼叫**。
- 每次 run 產生 log、usage 記錄、adapter-specific session state。
- **atomic checkout ＋ execution lock**：單一 assignee、執行鎖，避免多個 run 搶同一任務。
- **bounded recovery**：支援的失敗可自動回復，需要人處理的情況會被升起。

#### (4) Governance ＋ Budget（治理與成本硬停）

- **Approval gate**：board 審核流程、執行政策的 review／approval stage、decision tracking。
- **Budget hard-stop**：以 company／agent／project／goal／issue／provider／model 分層記錄 token 與成本，超過門檻警示、超過上限硬停。
- **Governance with rollback**：approval gate 強制執行、config 變更 revisioned、壞變更可回滾。
- **Activity & Events**：變更動作、heartbeat 狀態、成本事件、approval、comment 皆寫成 durable activity 供稽核。

#### (5) 技術棧

| 部位 | 內容 |
|---|---|
| Server | Express REST（`server/`） |
| UI | React ＋ Vite（`ui/`） |
| DB | Drizzle ORM ＋ PostgreSQL（本機內嵌自動建立） |
| 套件管理 | pnpm workspace |
| Runtime 需求 | Node.js 24.11+、pnpm 9.15+ |
| Native runner | Rust（`PAPERCLIP_RUNNER_BINARY` 可換預編譯 binary） |
| 發布 | `npx paperclipai@latest onboard --yes`；有 beta／nightly／canary channel |

### 3.3 定位邊界（repo 自述的「不是什麼」）

| 不是 | 說明 |
|---|---|
| 不是 chatbot | 對話附著在 task／plan／decision／output 上 |
| 不是 agent framework | 不教怎麼建 agent，只教怎麼「經營由 agent 組成的公司」 |
| 不是 workflow builder | routine／pipeline 在組織內運作，帶角色、目標、預算、治理 |
| 不是 prompt manager | agent 自帶 prompt／model／runtime |
| 不限單一 agent、不只 code review | 可從一個 agent 長成團隊；coding／PR review 只佔其中一類工作 |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

以下替代方案**已對照第二大腦（FATESAIKOU/MyBrain）的既有判定**。每則標 GitHub URL 與信任層級；`draft` 且 `generated.by` 為 AI 者一律註明「未經他 review 的 AI 草稿」。

### 4.1 同問題域：第二大腦既有判定

問題域定為「把多個 agent 組織成可管理的團隊／工作台」。第二大腦中**查無 `paperclip` 任何主題**（`grep -ri paperclip` 0 命中，鏡像 @ `c3319a0`／2026-10-05），下列為同軸既有紀錄，僅供對照，**不得升格為他對本標的之既有判定**。

| 標的 | 判定 | 信任層級 | 來源 |
|---|---|---|---|
| **Aionui** | 採用 | `human:fatesaikou` / `stable`（**本人定稿**） | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Aionui.md |
| **munder-difflin** | 不採用 | `process:learn-gh-agent` / `draft`（自動流程，未 review） | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/munder-difflin.md |
| **Buzz** | 不採用 | `opencode/deepseek-v4-pro` / `draft`（AI 草稿，未 review） | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Buzz.md |
| **maka** | 不採用 | `process:learn-gh-agent` / `draft`（自動流程，未 review） | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/maka.md |
| **macro** | 不採用 | `process:learn-gh-agent` / `draft`（自動流程，未 review） | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/macro.md |

**判定語意**（依 `技術/技術評估/判定總表.md`，`ollama-cloud/deepseek-v4-flash` / `draft`，未經他 review）：「採用」＝進 Judge/MVP 或 Feature；「試用」＝只需測能力邊界；「觀望」＝有價值但未排入下一步；「不採用」≠ 沒價值，仍抽取需求理解與方案方向。判定總表：https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md

### 4.2 DA 表：替代方案對照

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Paperclip**（本標的；第二大腦無紀錄） | Node.js server＋React UI 控制平面；company 為單位；org chart＋adapter 定義 agent；heartbeat 喚醒；目標樹 alignment；budget hard-stop＋approval gate；plugin 系統 | 自架 Node 24.11+/pnpm；Postgres；要自己接 agent adapter；採 UI 管理 | 重型全包；Postgres＋Rust runner 維運；GUI 為主要介面；open-by-default 的 skill 權限模型 | 一處管理多 agent 的任務、成本、治理與稽核；agent 換 runtime 不動控制面 |
| **munder-difflin**（第二大腦：**不採用**，`draft`） | Electron 桌面 app；把 CLI agent 包成「AI 辦公室」；hive（git 為記憶／信箱載體）＋ GOD agent 仲裁；Pixi.js 座位視覺化 | 桌面環境；每個座位掛真 CLI agent＝真 token 成本 | 基於 GUI；單一協作拓樸不能自由切換；pre-release、80 open issues | 共享記憶＋信箱＋自主迴圈＋可稽核（git-as-audit）；**機制可抽取，形態不符他的目標** |
| **Aionui**（第二大腦：**採用**，`human`/`stable`） | Electron 前端＋Rust 後端（AionCore）；內建 agent 引擎＋ACP 多 agent 協作協定＋Team Mode＋排程＋遠端存取 | 需安裝桌面 app；多 agent 協作依賴其自定義 ACP 協定 | 綁定 AionCore 內建引擎與 ACP 生態 | 統一桌面介面管理多 agent；他特別在意 OfficeCLI 連動與 MultiAgent |
| **Buzz**（第二大腦：**不採用**，`opencode`/`draft`） | Block 的蜂群思維工作台；統一事件流＋權限控制；整合需求／程式碼／CI/CD／任務追蹤 | 組織級導入 | 規模過大、個人使用不必要、採用效果未知 | 人與 agent 在同 workspace 共享上下文；判「統一工作平台可能是未來趨勢，值得觀察」 |
| **maka**（第二大腦：**不採用**，`process`/`draft`） | local-first agent workspace；「Log Is the Runtime」：append-only Runtime Event Log 為語意真相來源；Runtime Host 單一執行權威；四 surface 經同一 Host | 需接受 event-sourcing 模型與 Host 常駐 | 東西重型、方案未收斂、執行核心未定 | 可稽核、可復原、多 surface 行為一致 |

### 4.3 切入點差異分析

- **Paperclip vs munder-difflin**：兩者都提供「多 agent 的協作／管理層」。差異在**管理單位與載體**——Paperclip 管的是 **company（org chart＋goal＋budget＋governance）**，載體是 **server＋DB**；munder-difflin 管的是 **一支 CLI agent 隊伍**，載體是 **本機 git repo（hive）**。munder-difflin 被判「基於 GUI、只是一種拓樸、還太早且包太多」——此三點**同樣適用於 Paperclip**（見 4.5 衝突）。
- **Paperclip vs Aionui**：Aionui 是「桌面協作平台」，重心在**統一 GUI 操作多 agent**；Paperclip 是「控制平面」，重心在**組織、目標與成本治理**。Aionui 已由他本人 `stable` 採納；Paperclip 多出 company／goal／budget／governance 這一整層，但同樣是重型整合路線。
- **Paperclip vs Buzz**：兩者皆為「人＋agent 工作台」且都整合任務與 CI/CD。Buzz 被判「規模過大、個人使用不必要」。Paperclip 的 scope 更大（多公司、預算、adapter、plugin），**在此判準下只會更重**。
- **Paperclip vs maka**：maka 是「執行核心／runtime」層的 local-first workspace，重心在 log-as-runtime 的可稽核執行；Paperclip 是「控制平面」，**不執行 agent**。兩者解決不同層的問題，但皆屬「重型、方案未收斂」類。
- **另一條替代思路（非產品，為通用做法）**：把既有 ticket 系統（Asana／Trello／Linear）直接指向 agent。Paperclip 的 FAQ 明確以此為對照，回答「agent orchestration 有細微處（checkout 鎖、session 續接、成本監控、治理）」。此路線的取捨見下表。

| 替代思路 | 切入點 | 前提 | 副作用 | 預期效果 |
|---|---|---|---|---|
| **Asana／Trello／Linear＋agent** | 複用既有 ticket 系統，agent 當外部 worker | 已有 ticket 系統；自行處理 checkout／session／成本 | agent 專屬機制（執行鎖、session 續接、token 成本）要自建 | 上手成本低，但 agent orchestration 的細節全落在自己身上 |
| **OpenClaw 等 agent 本體** | 提供單一 agent 的能力（employee） | 需一個「公司層」來編排 | 不含組織、預算、治理 | 有員工沒有公司；Paperclip 即以其為 employee 單位對接 |

### 4.4 對照他的技術取捨準則

來源：`抽象理解/本質洞察/技術取捨準則.md`（`claude-code/opus-5` / **`draft`，未經他 review 的 AI 草稿**），https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md

| 準則 | 對 Paperclip 的對應 |
|---|---|
| **理解優先**：不穩定或不熟悉就先自己兜，MVP 是理解的驗證點 | Paperclip 2026-03 才建立、約 7 個月、已 2,700+ merged PR 且團隊維護（非單人），**穩定性不差**；但對他是全新且重型。依準則，重點是「先理解本質」而非直接導入 |
| **MVP→Feature 唯一閘門**：能否影響個人 workflow | 他正在建 **Ai公司架構**（AiEntry 秘書＋AiContainer 員工＋AiStorage），Paperclip 的 company／org chart／heartbeat 與此**同一題的完整外顯版本**，屬強相關參考 |
| **Reject ≠ 沒價值**：抽取需求理解與方案方向 | 即使不採用，其 **adapter 契約（be callable）／heartbeat queue／atomic checkout／budget hard-stop／goal ancestry** 是可抽取的機制 |
| **約束在 harness 不在權限**：不要人工審核關卡，要補驗證機制 | ⚠️ **部分衝突**：Paperclip 的 approval gate 是「人工審核關卡」；但他要的是 verify 機制。Paperclip 另一側的「verify from diffs／screenshots／tests」與「governance with rollback」才是對症的那半。**同一產品同時含他反對與他認同的兩半** |
| **禁止的能力做成不存在** | Paperclip 的 skill 模型明文「permissions are opt-in restrictions, not opt-in capabilities」——未配置時預設開放，與他的「能力集合裡沒有那條路徑」取向**不同**；但 core safety invariant 不可由 policy 關閉，該部分同向 |

### 4.5 與他既有架構／判定的關聯與衝突（衝突處明確標示）

來源（皆為 AI 草稿，未經他 review）：`技術/動手做/Ai公司架構.md`（`claude-code/opus-5.5` / `draft`）、`技術/靈感/AIContainer.md`（`claude-code/opus-5.5` / `draft`）、`技術/動手做/個人 AiAgent 入口.md`（`claude-code/opus-5.5` / `draft`）；另 `抽象理解/本質洞察/Harness Engineering.md`（`human:fatesaikou` / **`stable`，他本人**）。

| 面向 | Paperclip | 他的架構／判定 | 關係 |
|---|---|---|---|
| 控制面 vs 執行面 | 明採「control plane, not execution plane」；agent 在外部 phone home | Ai公司架構「兩個東西，不是兩層」、「共用媒體，不共用流程」 | **同構**。Paperclip 是此分離原則的完整外顯實作，可作機制參考 |
| 角色／職務 | org chart＋adapter config 定義 agent 身分 | AiStorage 的 **Atelier**（harness＝職務）＋ MyLinuxPool 的 **profile**（能力清單） | **同構**。Paperclip 的 adapter config ＝ 他的 Atelier／profile 的另一種表達 |
| 交接 | task assignment＋heartbeat 喚醒 | Agora 交接單＋指定職務，秘書委派員工 | **同構** |
| 目標追溯 | 任務 parent 鏈上溯 company goal | MyPMO 工單樹（AI公司根的工單／工作樹） | **同構**，可作 goal ancestry 參考 |
| 稽核 | activity log／run history／adapter session state | Harness Engineering 的 `verify`＋MyBrain 的 `validate.py`／append-only 檢查 | 方向一致 |
| **UI 形態** | 以 **React UI／GUI 為主要介面** | munder-difflin 判不採用之理由①：「基於 GUI，而打算打造 AI Container/AI Company **沒打算被限制 UI**」 | ⚠️ **衝突**。Paperclip 主介面即 GUI |
| **規模** | 全包（server＋Postgres＋plugin＋Rust runner＋budget＋governance＋skill studio…） | Buzz 判不採用「規模過大、個人使用不必要」；macro 判不採用「太重型」；munder-difflin 判「還太早而且包太多」 | ⚠️ **衝突**。Paperclip 的 scope 比上述三者更大 |
| **審核關卡** | approval gate（人工審核） | 技術取捨準則五：⚠️「不要建議加人工審核關卡，要補驗證機制」 | ⚠️ **部分衝突**（同 4.4 最後兩列） |
| **執行環境** | 自架 server；有 cloud／sandbox 路線 | 他「禁止的能力做成不存在」；AiContainer 併入 MyLinuxPool | 可對照其 sandbox provider 與 credential 邊界設計 |

### 4.6 反證表：正反並列

| 支持參考 Paperclip 的證據 | 反對導入 Paperclip 的證據 |
|---|---|
| 控制面／執行面分離與他的 Ai公司架構原則同構 | 主介面是 GUI，與 munder-difflin 被拒理由①直接衝突 |
| org chart＋adapter＝Atelier／profile 的同構實作 | scope 大於已被判「太重」的 Buzz／macro／munder-difflin |
| goal ancestry 可對照 MyPMO 工單樹 | approval gate 與「不要人工審核關卡」準則衝突 |
| verify／rollback／activity 對照他的 harness `verify` | Node 24＋Postgres＋Rust runner 的維運負擔，個人使用門檻高 |
| 維護活躍、MIT、2,700+ merged PR，穩定性客觀可查 | 他的執行環境（LLMGateway、AiContainer）尚未定案，時序上 Paperclip「還太早」 |

**結論**：Paperclip 是「AI 公司控制平面」這一題**目前最完整的外顯實作**，與他的 Ai公司架構在多個構面**同構**，是機制抽取的高價值來源；但作為**導入標的**，它同時觸發他過去對 munder-difflin／Buzz／macro 的三條拒絕理由（GUI、太重、時序太早），並在 approval gate 上與他的技術取捨準則相衝突。「參考其控制面機制」與「採用此產品」在此應分開判定。

> **R2 補充（2026-10-05）**：官方 `doc/PRODUCT.md` 明訂 **「Thin core, rich edges」**（把 chat／knowledge 等可選面推往 plugin，避免膨脹控制面），此為上述「太重」衝突的**官方反證**。但 `doc/plugins/PLUGIN_SPEC.md` 自述現況：**single-tenant、self-hosted、single-node；plugin UI 視為 trusted code 非沙箱；dynamic plugin install 尚不 cloud-ready、無共享 artifact store**——設計意圖（thin core）與當前實作（擴張仍受限）存在落差。此條亦為「全整合→難局部擴張」的官方正證，詳見 §5 Q3。

---

## 5. User Q&A

> 使用者於 R2 判「觀望（Reserve）」並提出 5 點追問。以下依 AGENTS.md §5 拆為 Q1–Q5（每個子問題一題，不合併），既有內容不刪改。
> 判定語意（依 `技術/技術評估/判定總表.md`）：**「觀望」＝有價值但未排入下一步**，≠「不採用」。本節回覆一律據此，不寫成 Reject。

### Q1：跟我的 Ai公司構想大幅同構，但這樣不構成我替換的理由

**A**：同構是事實，但「同構」只支持「可抽取機制」，不支持「替換」。兩者是不同的判定層級。

| 命題 | 成立程度 | 依據 |
|---|---|---|
| 兩者同構 | **成立** | Paperclip「control plane, not execution plane」↔ Ai公司架構「兩個東西，不是兩層」；org chart＋adapter ↔ Atelier／profile；goal ancestry ↔ MyPMO 工單樹（見 §4.5） |
| 同構 ⇒ 應該替換 | **不成立** | 同構只意味「解同一題」。是否替換另受規模、擴張性、需求穩定性三條判準約束（Q2–Q4） |

他既有架構的定義句本身即排除「以同構為替換理由」：Ai公司架構為 **AiEntry 與 AiContainer「互不為前提」**、**「共用媒體，不共用流程」**，且**狀態在執行體之外（AiStorage）**。Paperclip 若替換之，等於把「互不為前提的兩個東西」重新綁進**一個 server＋DB＋UI 的統一體**——這正是統一的反向。

> Ai公司架構原文（`claude-code/opus-5.5` / `draft`，未經他 review）：https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/Ai公司架構.md

**結論**：同構成立、且 Paperclip 是可抽取的機制來源，但「同構」不構成替換理由。

### Q2：反而是他規模大，我需要觀望

**A**：「規模大」在本輪是**客觀事實**，非感知。R2 實查數據如下：

| 指標 | 數值 | 意義 |
|---|---|---|
| Stars | 97,626（R1 97,420 → R2 97,626，續增） | 關注度高 |
| Forks | 16,499 | 生態分叉活躍 |
| Releases | 27 個，最新 v2026.1001.0（2026-10-02） | 近月每 1–2 週一發 |
| Adapters | 13（claude／codex／cursor／gemini／grok／hermes／kimi／opencode／pi／openclaw／cursor-cloud…） | 「整合了很多」之硬數據 |
| Sandbox providers | 8（cloudflare／daytona／e2b／exe-dev／kubernetes／modal／novita／createos） | 執行環境廣度 |
| Plugins | 6 子件＋mcp-server | 擴充面 |
| doc 目錄 | 逾 80 檔（含 SPEC、PLUGIN_SPEC、architecture…） | 系統化程度 |

對照他過去對「規模」的判準：Buzz 被判不採用之因即「規模過大、個人使用不必要」；macro 因「太重型」；munder-difflin 因「還太早而且包太多」。**Paperclip 的 scope 在此三者之上**（多公司、預算、adapter、plugin、Rust runner）。

> 技術取捨準則原文（`claude-code/opus-5` / `draft`，未經他 review）：https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md
> 判定總表（`ollama-cloud/deepseek-v4-flash` / `draft`，未經他 review）：https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md

**結論**：規模為硬事實；依既有判準，規模大正是「觀望」而非「採用」的觸發條件。

### Q3：它整合了窗口／儲存／工作空間，部分要素更完整，但整合了全部，想擴張某一部分能力目前還很困難

**A**：此知覺對**當前版本**成立，且有官方正反兩面文件為證。

| 面向 | 官方文件 | 內容 | 對本題的意義 |
|---|---|---|---|
| 設計意圖（反證） | `doc/PRODUCT.md` | 明訂 **「Thin core, rich edges」**；把 chat／knowledge 等放進 plugins；**Do not build enterprise-grade RBAC first** | 官方**自己承認**全包是風險，故設計上把可選面往 plugin 推——不是無節制大一統 |
| 當前實作（正證） | `doc/plugins/PLUGIN_SPEC.md` | 自述 **single-tenant、self-hosted、single-node**；plugin UI 為 **trusted code 非沙箱**；**dynamic plugin install 尚不 cloud-ready**、無共享 artifact store | 設計意圖與實作有落差；「想擴張某一部分」的官方路徑（plugin）**尚未成熟** |
| 記憶整合取徑（對照） | `doc/memory-landscape.md` | 目標為「坐在多個差異很大的 memory 系統之上的**最小契約**，而不抹平差異」 | 官方亦警覺「統一會抹平兩端」 |

他第二大腦中已有一條直接對應此現象的本質洞察——**「統一的兩端稅」**：

| 抱怨方向 | 意思 |
|---|---|
| **相反**（一端嫌太重，一端嫌不夠細） | **分界劃錯了**，這兩個東西不該共用一套機制；修任何一邊都會加深另一邊的痛 |
| 相同（都嫌慢、都嫌難用） | 分界可能對，是實作沒做好，可修 |

Paperclip 的統一體（窗口＋儲存＋工作空間＋治理＋預算收進一個控制面）若兩端性質不同，代價即由兩端反向支付——與他「想擴張某一部分能力很困難」的知覺同構。

> 統一的兩端稅（`claude-code/opus-5` / `draft`，未經他 review）：https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/統一的兩端稅.md

**結論**：官方設計意圖（thin core）認同此風險，但當前實作（single-node、plugin 未 cloud-ready）佐證「局部擴張仍困難」；此為「觀望」的技術理由。

### Q4：此領域目前沒有最佳解，原始需求大規模變動導致的擴張重構在所難免；既然我已有同構服務，就先繼續運用、摸清需求輪廓，再轉換也不遲

**A**：此判斷與他既有的**汰換準則**一致。技術取捨準則第四條：

| 會汰換 | 不會汰換 |
|---|---|
| 維護停更或社群死了（外部客觀事實） | ❌ 出現更好的替代（**他不追新**） |
| 用不到了，需求消失 | ❌ 「能跑就不動」 |

Paperclip 維護活躍（27 releases、2,700+ merged PR、團隊維護），**上游未死**；且他有同構服務在用。依準則，此情境**不觸發汰換**。更根本的理由是：汰換判準的兩個入選條件都是外部客觀事實，而「此領域無最佳解、需求將大規模變動」意味著**現在替換只是把重構成本提前**，且換到一個同構但更重的系統。

| 選項 | 現在替換 | 先續用同構服務 |
|---|---|---|
| 需求輪廓 | 尚未摸清即鎖定 | 續摸清，轉換時機可選 |
| 重構成本 | 立即支付，且可能重付 | 延後至需求穩定後支付 |
| 上游風險 | Paperclip 若重構，跟著動 | 既有服務已熟悉 |

> 技術取捨準則第四（`claude-code/opus-5` / `draft`，未經他 review）；技術取捨準則三「Reject ≠ 沒價值，抽取需求理解與方案方向」：https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md

**結論**：先續用同構服務、摸清需求輪廓再轉換，與汰換準則一致；Paperclip 的角色是**需求理解與機制方向的抽取來源**，非替換標的。

### Q5：我認為 AI 時代最珍貴的是對 AI 應用的需求想像，以及能力邊界的理解

**A**：此為本輪（R2）使用者的**新宣示**。第二大腦中查無以「需求想像」為措辭的既有條目（`grep "需求想像"` 0 命中，鏡像 @ `c3319a0`／2026-10-05），不得歸因為其既有立場；既有相近者為各評估中的「**能力邊界**」（如 gods-eye-view／Jev／VoiceStudio 之「測試能力邊界」）。

與既有骨幹的關係（對照，非等同）：

| 既有條目 | 內容 | 與本宣示的關係 |
|---|---|---|
| 核心價值觀「產出形態：會動的機制 vs 判斷材料」 | 價值是什麼——會動的機制；價值怎麼創造——實際執行 | **同軸**：需求想像與能力邊界皆屬「機制設計所需的判斷」，非判斷材料本身 |
| 技術取捨準則一「理解優先」 | 先自己兜是為了**理解本質**，不是省成本 | **同軸**：能力邊界的理解即理解本質的具體對象 |
| 技術取捨準則二「MVP→Feature 唯一閘門是能否影響 workflow」 | 不穩定或不熟悉先自兜 | **同軸**：需求想像決定該開什麼 MVP |

> 核心價值觀（`claude-code/opus-5` / `draft`，未經他 review）：https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/價值觀/核心價值觀.md

**結論**：本宣示與其「理解優先」「產出形態」兩條骨幹同軸，但「需求想像」一詞為本輪新提出，報告僅以原話呈現，不升格為既有定稿。

---

## 附錄：調研資料來源

| 來源 | 內容 |
|---|---|
| `README.md`（593 行） | 產品定位、四支柱、功能表、Without／With 對照、架構圖、FAQ、Roadmap、telemetry |
| `doc/GOAL.md` | 願景、問題定義（control plane for a company of AI agents）、兩層架構 |
| `doc/PRODUCT.md` | company 為 first-order object、adapter 定義 agent、目標樹、skill policy、principles、邊界；**R2：Thin core, rich edges／Do not build enterprise-grade RBAC first** |
| `doc/SPEC.md`（DRAFT，R2） | V1 治理＝Single human Board＋approval gates（hire、CEO 策略）；budget 逐層下放 |
| `doc/plugins/PLUGIN_SPEC.md`（R2） | plugin runtime 自述現況：single-tenant／self-hosted／single-node；UI 為 trusted code；dynamic plugin install 尚不 cloud-ready |
| `doc/memory-landscape.md`（R2） | 跨多 memory 系統之最小契約，不抹平差異 |
| `doc/DESIGN.md`／`AGENTS.md`／`ROADMAP.md`／`package.json` | 技術棧、repo map、工程邊界 |
| GitHub API（`gh repo view`／`gh api`／`gh api releases`／`/commits`／`/languages`） | stars／license／語言／建立時間／release 節奏／活躍度交叉驗證 |
| npm registry（`registry.npmjs.org/paperclipai`） | 發布狀態、latest、channel |
| MyBrain 鏡像 @ `c3319a0`（2026-10-05） | 判定總表、技術取捨準則、Ai公司架構、AIContainer、個人 AiAgent 入口、Harness Engineering、munder-difflin／Buzz／maka／Aionui／macro |
| **未取得** | GitHub 一周熱點 133 期影片逐字稿（YouTube transcripts disabled） |
