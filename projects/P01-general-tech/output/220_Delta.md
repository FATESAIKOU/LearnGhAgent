# Delta 技術分析報告

> 調研標的：Zed 團隊 2026-08-12 發布的「Delta」與其後端「DeltaDB」
> 狀態：Private beta（GitHub 無公開 repo，本報告以官方 blog 與 docs 為一手來源）
> 一手來源：zed.dev/blog/introducing-delta、zed.dev/blog/introducing-deltadb、zed.dev/blog/crdts、delta.dev/docs

---

## 1. 這個技術解決什麼問題？

**Delta／DeltaDB 解決的問題是：生成式 AI 協作下的「程式碼」與「程式碼背後的意圖」被切開存放，導致程式碼變更無法追溯到它為什麼被這樣改。**

具體拆成三個子問題：

- **意圖遺失**：現有工具（含 Zed）只保留「生成完的程式碼」。開發者為什麼改、跟 agent 討論了什麼、在 commit 前做了哪些編輯——這些意圖沒有被記錄，團隊事後只能從 diff 逆推。
- **diff 語意不連續**：以 Git commit 為最小記錄單位時，commit 之間的編輯過程（agent 的逐筆 operation）是黑箱，無法還原「這行程式碼是在哪一段對話脈絡下出現的」。
- **協作同步成本**：多人＋多 agent 各自持有一份本地工作樹時，「最新程式碼有沒有 commit／有沒有 push」的狀態判斷造成認知負擔，agent 在雲端跑時也與本機工作樹脫節。

對照使用者三問的「① 對個人工作流是加成還是替換」：**Delta 的設計前提是「團隊」多玩家協作，問題陳述本身不落在「個人單機工作流」的痛點上。** 對個人情境而言，它既非「替換」既有工具（它不取代編輯器或 harness，而是另起一套以 thread 為中心的環境），也不是明顯「加成」——加成的前提是「你有一個需要多人共同 review agent 產物的團隊」這個情境成立。若僅個人使用，被它解決的「意圖遺失」與「協作同步」兩個子問題中，後者幾乎不成立。

**問題描述模糊之處**：「意圖」一詞未被 Delta 給出操作型定義——它指「agent 對話原文」，而非「結構化、可驗證的需求規格」。這與使用者自己對「意圖/需求管理」的既有沉澱（AI-DLC 中工程師主司需求折衝、品質担保）語意不同，後者是「人先想清楚再讓 AI 實作」，Delta 是「把想與做之間的過程錄下來」。兩者解決的是不同層次的問題，不能混為一談。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **現有工具只保留「生成後的程式碼」**：Zed 本身是 AI 原生編輯器，能讓 agent 產生程式碼，但「產生到產出」之間的意圖與對話沒有被保存。Delta 團隊指出「軟體是存在於 commit 與 commit 之間」（Software Is Made Between Commits）。
- **Zed 基盤包袱**：Delta 之所以另起新 app 而非直接裝在 Zed 上，是因為不想動搖已擁有大量用戶的 Zed 基盤；「ZedDB」可以載入 Zed 也有此計畫，但為了不受 Zed 限制、全力發揮 DeltaDB 潛能而另立新 app。
- **多玩家即時同步需求**：每個成員都持有一份本地工作樹副本，DeltaDB 負責即時同步，免除「最新程式碼已否 commit／push」的判斷。
- **Agent 執行的移動性**：可以把作業移交給 cloud runner（雲端 agent）後闔上筆電，agent 會持續在與 thread 同步的狀態下運作——這需要「工作樹＋對話」一起被同步，而非只有程式碼。

### 通用技術背景（文章未明確、由調研補足）

- **Git 的粒度與單一語意**：Git commit 是「作者、時間、快照差異」的封閉單位，不含產生過程。傳統上「為什麼改」靠 commit message 與 PR 討論補足，兩者都是人為附加、可漏可離題，無法與每個 operation 對應。
- **AI 產生程式碼的過程密集但不可見**：agent 執行時會產生大量逐筆 operation（file edit、tree change、message），這些在 Git 模型下全部被壓縮成一個 commit，過程消失。
- **CRDT（Conflict-free Replicated Data Type）**：用於多人無衝突複製的資料結構。DeltaDB 用它做 conflict-free 的 replicated worktree，讓多個本地副本即時收斂到一致狀態，不需中央鎖定。
- **行號 anchor 的不穩定**：以行號為 reference 的註解／討論，在程式碼編輯後會失效。Delta 改用 delta（記錄變更）當 anchor，使 reference 在 code 移動後仍存活。
- **agent harness 生態的連動協議**：Agent Client Protocol（ACP，見 Zed 說明）與第三方 harness 連動（首波 Claude Code），是讓不同 agent 工具能接上 Delta thread 的橋。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 定位與屬性（對應使用者三問的「② harness / tool / 團隊大一統 culture」）

| 層面 | 歸類 | 判定理由 |
|---|---|---|
| **Delta（app）** | **harness 等級的「執行＋review 環境」** | 它承載 agent 執行（在 checkout 中工作）、對話、review，是 agent 運行的場所，不只是單一 tool |
| **DeltaDB（資料層）** | **version-control 等級的「以 conversation 為中心的資料庫」** | 它取代的是「Git 之上的記錄模型」，把 commit＋edit＋chat 綁在一起；不是單一 tool，而是資料模型 |
| **整體產品** | **「團隊營運文化」的載體，但非「大一統平台」** | 相較 Buzz（Block 的整合 CI/CD＋任務追蹤的大一統工作台），Delta 不收斂 CI/CD 與任務管理，只鎖定「coding + agent conversation + review」；它是單一垂直域的協作環境，不是全流程大一統 |

**對照 Harness Engineering 關鍵五問（memory / read / action / permission / verify）評估 Delta：**

| 五問 | Delta 的做法 | 與使用者準則的關係 |
|---|---|---|
| memory | thread 內的 conversation + worktree 全量同步，即時複製；跨 session 的對話保留在 thread | 記憶以「對話原文」承載，非結構化抽取 |
| read | 每個參與者一份本地 worktree 副本，DeltaDB 即時同步 | 與「他看的到什麼」一致 |
| action | agent 在 checkout（真實檔案夾）工作；可 push 到 local remote | 動作在真實檔案系統上執行 |
| permission | .gitignore 尊重；未見細粒度權限模型 | 未見 ACL／審核關卡設計 |
| verify | docs 未提供明確的程式化驗證閘門（Linter／CI 綁定）描述 | **與使用者「約束在 harness／驗證規則程式化」的準則存在張力**——Delta 以「錄下過程」為賣點，而非「程式化驗證 agent 做對了」 |

**結論（②）**：Delta 是「以 thread 為中心的 agent 協作 harness」，DeltaDB 是它底下的「conversation-as-source 版本資料層」。它不是 tool（單一功能），也不是 Buzz 式大一統 platform culture；介於「harness」與「協作環境」之間。**它把 harness 的執行與記憶綁進 Zed 自家封閉生態**，這與使用者「自架 harness 全自控、不綁定特定供應商」的方向直接衝突。

### 3.2 核心機制

```
Delta / DeltaDB 的資料模型
┌─────────────────────────────────────────────────────────────┐
│  Thread（私有的、可分享的協作單位）                            │
│  ├── Conversation（agent / 人的訊息）                          │
│  └── Worktree（檔案樹，每參與者一份本地副本）                   │
│        │                                                      │
│        └── DeltaDB：以 delta 為最小記錄單位                    │
│             • delta = 對 thread / worktree 的一次變更           │
│               （file edit、tree change、message、comment）     │
│             • 連續產生，不需 stage / commit                     │
│             • 每個 operation 有 stable identity                │
│             • anchor 綁在 delta 而非行號 → code 移動後仍存活     │
└─────────────────────────────────────────────────────────────┘
```

- **delta 為最小單位**：每個 operation 有 stable identity，anchor 綁在 delta 上；程式碼搬移後，討論與 reference 不會因為行號改變而失聯。
- **CRDT 複製 worktree**：多個本地副本 conflict-free 同步，即時收斂，無中央鎖定。底層機制見 Zed 的 CRDT 實作（anchor、tombstone、Lamport timestamp、undo map）。
- **與既有 git repo 相容**：兩組 remote——`origin`（共享上游）＋`local`（本機 repo）；agent 可 push 到 local，免 GitHub round-trip；支援 jj colocated。
- **執行模型**：agent 在 checkout（真實檔案夾）工作；一次只在單一機器跑（本機或 cloud runner）；cloud runner 讓 agent 在筆電闔上後持續與 thread 同步運行。
- **WASM／WebGL 網頁版**：同一 Rust app 編譯成 WebAssembly 並以 WebGL 繪製，非 JS 重寫的簡易版；接受分享連結的人不必裝 app，直接用瀏覽器讀 thread。
- **第三方 harness 連動**：首波支援 Claude Code，session 可 live 同步進 Delta thread。

### 3.3 本質突破評估（對應使用者三問的「③ 有無本質突破，沒有就自己幹」）

**相對於「Git 為底」的既有記錄模型，DeltaDB 有兩項實質差異：**

1. **conversation 成為第一等記錄**：不只記錄 commit，連 commit 前的編輯與 agent 對話都納入同一個可查詢的 delta 流。「程式碼＋意圖」被綁在同一資料層。
2. **delta-anchor 取代行號 anchor**：reference 綁在變更（delta）而非行號，程式碼編輯後仍可追蹤——這是解決「討論失聯」的具體工程突破。

**但這是否構成「本質突破」，需放到使用者的既有判定光譜看：**

| 面向 | DeltaDB 的作法 | 使用者既判定 | 衝突點 |
|---|---|---|---|
| 團隊級「意圖／記憶」治理 | conversation-as-source，delta 流 | EverOS（Reject）、TencentDB（Reject）：要求「資訊隨組織自我維護更新」＋「防腐化機制」 | **DeltaDB 以「錄下過程」取代「自我維護」**——它沒有把對話結構化、去重、防腐化，只是保存原文。與「沒有防腐化機制的記憶＝必定過期的文件」判準衝突 |
| agent 協作 harness | 單一 app＋單一資料層 | Aionui（Accept）：Open 多 agent、ACP、私人 Agent 系統 | **Delta 是封閉、私有 beta、鎖 Zed 生態；Aionui 是開源、開放協定、多模型**。方向相反 |
| 個人 workflow | thread 多人協作 | MVP→Feature 唯一閘門＝「能否影響個人 workflow」 | **Delta 預設不落在個人情境**；個人使用時其核心價值（多人即時同步＋共同 review）不成立 |
| 大一統 culture | 非，只鎖 coding＋review | Buzz（Reject）：規模過大、個人不必要 | 兩者都屬「重平台」路線，但 Delta 範圍較 Buzz 窄 |

**結論（③）**：DeltaDB 在「資料模型」層級（conversation-as-source、delta-anchor）相對於 Git 是實質差異，不是包裝。但把它放到「團隊意圖／記憶治理」這個更高層級看，它與已判 Reject 的 EverOS／TencentDB 是同一家族，且沒有解決使用者最核心的判準——資訊如何自我維護與防腐化。**「沒有就自己幹」的決策點落在這條判準上：如果使用者要的是「結構化、可驗證、能自我維護的意圖管理」，DeltaDB 不是答案，自己兜反而更貼近；如果只要「把 agent 對話原文留下來」，Git 結合現有工具已能達成大部分，不需引入封閉的 Delta。** 詳見 §4。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 DA 表：替代方案對照

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|---------|-------------|---------------|-----------------|
| **Aionui** | 開放多 agent 桌面協作平台（Electron+Rust），ACP 協定統一管理多個 CLI agent，Team Mode 分工 | 需自行整合 CLI agent、自備模型 API key；桌面端 | 平台本身非版本控制，意圖不與 Git delta 綁定；需自行處理記憶/意圖結構化 | 開放、多模型、自控；補 Delta 封閉生態之不足，但「意圖與程式碼綁定」不是它的主訴求 |
| **EverOS** | LLM agent 跨 session 長期記憶 OS，仿銘印記憶生命週期（情節→語意→重建） | 需部署整個記憶 OS；團隊規模 | 機制複雜規模大、無自組織驗證、泛用未專門化 | 跨 session 記憶治理，但使用者判 Reject——不採用以自建 MyBrain 個人級替代 |
| **TencentDB-Agent-Memory** | 團隊級記憶 Hub，四類記憶資產（Chat/Skill/Wiki/CodeGraph）＋L0-L3 分層＋ACL 治理 | 需團隊協作情境、騰訊雲環境 | 無防腐化機制、資訊不會自我維護、單一硬編碼 prompt 決定分層 | 團隊記憶集中，但使用者判 Reject——與 EverOS 同層級同缺陷 |
| **Zed 本體＋既有 git＋PR 討論** | 在不引入新平台下，用既有編輯器＋Git commit message＋PR/issue 對話人工承載意圖 | 需紀律性地寫 commit message、維持 PR 討論品質 | 意圖記錄分散、易漏、與 operation 無對應；過程黑箱 | 零新依賴，但無法達成「意圖與每筆變更對應」 |

### 4.2 第二大腦既有判定對照（含信任層級）

| 標的 | 判定 | GitHub URL | 信任層級 | 時間 |
|---|---|---|---|---|
| Zed（編輯器本體） | → Reject，「他要解的問題不是我的問題」 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Zed.md | human:fatesaikou / stable | 2026-05-31 |
| Aionui | → Accept，在意 OfficeCLI 連動、MultiAgent（ACP）、私人 Agent 系統 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Aionui.md | human:fatesaikou / stable | 2026-07-12 |
| Buzz | → Reject，規模過大、採用效果未知、個人使用不必要 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Buzz.md | opencode/deepseek-v4-pro / draft（**AI 草稿，未經他 review**） | 2026-07-26 |
| EverOS | → Reject，機制複雜規模大、無自組織驗證、泛用未專門化 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/EverOS.md | human:fatesaikou / stable | 2026-05-31 |
| TencentDB-Agent-Memory | → Reject，資訊不自我維護、無防腐化機制 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/TencentDB-Agent-Memory.md | process:learn-gh-agent / draft（**機器產出草稿，未 review**） | 2026-08-10 |
| 技術取捨準則（MVP→Feature 唯一閘門＝能否影響個人 workflow） | 準則 | https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md | claude-code/opus-5 / draft（**AI 草稿，未 review**） | 2026-08-01 |
| 判定總表（86 筆） | 索引 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md | ollama-cloud/deepseek-v4-flash / draft（**AI 草稿，未 review**） | 2026-08-02 |

> ⚠️ **Delta／DeltaDB 本身第二大腦無既有判定**（Step 1 已確認）。上述為替代方案家族的既有判定。技術取捨準則與判定總表為 AI 草稿（未經 review），引用的核心主張（MVP→Feature 閘門、Reject≠沒價值、防腐化判準）在多份 stable 檔有交叉印證，但引用時仍標明草稿來源。

### 4.3 切入點差異與反證

**DeltaDB vs EverOS／TencentDB（團隊意圖／記憶治理）：**

| 面向 | DeltaDB | EverOS／TencentDB |
|---|---|---|
| 承載形式 | 對話原文（delta 流，不結構化） | 結構化抽取（情節→語意→重建／四類資產分層） |
| 與程式碼的關係 | 與 worktree 綁定（delta-anchor） | 與記憶 OS 綁定，非與 Git delta 綁定 |
| 自我維護 | 無結構化、無去重、無防腐化 | TencentDB 明確無防腐化；EverOS 無自組織驗證 |
| 使用者判準 | 未達「資訊自我維護」 | 未達「資訊自我維護」→ 兩者皆 Reject |

**反證表：DeltaDB 的「錄下過程」是否滿足使用者對「意圖管理」的需求？**

| 使用者需求面向 | DeltaDB 是否滿足 | 反證 |
|---|---|---|
| 留下原始討論記錄 | 部分滿足 | 僅在 Delta 封閉環境內；離開 Delta 即失去 |
| 意圖可驗證、可回溯到每筆變更 | 滿足（delta-anchor） | 但「意圖」只是對話原文，未結構化，無法程式化驗證 |
| 資訊隨時間自我維護、防腐化 | 不滿足 | 原文留存即為全部，無去重／衝突合併／回滾（docs 未描述） |
| 可自控、不綁定供應商 | 不滿足 | Private beta、封閉、鎖 Zed 生態、開源時程未定 |
| 影響個人 workflow | 不滿足 | 多人協作為前提，個人單機場景價值弱 |

**結論**：Delta 的資料模型突破（conversation-as-source、delta-anchor）是真實且具參考價值的方案方向；但作為「可採用工具」，它卡在三個既有判準上：① 不影響個人 workflow（MVP→Feature 閘門）；② 封閉生態、非自控（對立於 Aionui 的開放自控方向）；③ 不解決「意圖自我維護／防腐化」這一使用者的團隊記憶核心判準（與 EverOS／TencentDB 同層缺陷）。**因此，Delta 對使用者的價值是「可抽取的方案方向」（以 delta 為 anchor、conversation 入版控），而非「可導入的工具」。若要自幹，DeltaDB 的 delta-anchor 概念是比 Git+PR 更貼近「意圖與變更對應」的設計起點，但其「自我維護」缺口仍需另行設計。**

---

## 5. User Q&A

> 以下為 R2 使用者的四則追問。R2 一手資料來源：delta.dev/docs（concepts/delta-and-git、agents/threads、agents/review-and-sync、concepts/worktrees-and-machines、agents/comments、collaboration/collaborate-thread、privacy-and-security/data-storage、getting-started），官方／stable 層級。

### Q1：保存會話歷史就只是把 user 跟 AI agent 的對話拿來跟 git commit 一一對應？

**A**：不是一對一對應。對話與 file edit 是**同一個 delta 流**裡的兩類 delta，git commit 是另一層、留在 Git 端；DeltaDB 不把「對話」對應到「commit」，而是把「對話＋編輯」一起記成連續的 delta 序列。

```
DeltaDB 的資料粒度（非 1:1 commit）
┌─────────────────────────────────────────────────────────┐
│ Git 層            git commit（留在 git，另層記錄）        │
├─────────────────────────────────────────────────────────┤
│ Delta 層   delta 流（連續產生，不需 stage/commit）         │
│            ├── file edit（程式碼變更）                     │
│            ├── tree change（檔案樹變更）                   │
│            ├── message（對話訊息，本身就是 delta）         │
│            └── comment（註解）                            │
└─────────────────────────────────────────────────────────┘
```

| 面向 | 實際機制 | 與「1:1 對應 commit」的差異 |
|---|---|---|
| delta 定義 | delta＝對 thread／worktree 的一次記錄變更（file edit、tree change、message、comment） | 粒度**細於** commit，一個 commit 前後可能橫跨多個 delta |
| 對話的定位 | conversation 訊息**本身就是 delta**，與 file edit 同屬一個 delta 流 | 對話不是「另外對應到某個 commit」，而是嵌入 delta 流 |
| commit 的關係 | git commit 留在 Git；DeltaDB 另記 delta 流 | 兩層並行，非對話↔commit 的映射 |

**結論**：DeltaDB 的「對話↔程式碼」不是靠「把對話與 commit 一一對應」達成，而是靠「對話與編輯共用同一個 delta 流、以 delta 為 anchor」，使對話能沿著 delta 定位到它觸發的編輯。

---

### Q2：這東西跟我目前的 LearnGhAgent memory 機制是否類似？或者我的機制更好？

**A**：不類似，兩者目的不同層級。Delta 的 conversation 記錄是「協作過程的即時原文留存」；LearnGhAgent 的 `memory/` 是「debug 軌跡」，且**刻意不納入知識**——知識只存在 `output/`。

| 面向 | DeltaDB | 使用者的 LearnGhAgent / MyBrain 機制 |
|---|---|---|
| memory/ 定位 | thread 內對話＋worktree 全量即時同步複製 | `memory/`＝275 份執行軌跡（debug），**刻意不納入知識**（LearnGhAgent.md:52）；知識只在 `output/` |
| 記錄單位 | delta 流（含對話原文與編輯） | 執行 log（step 總結）＋output 最終成果物 |
| 防腐化 | 無結構化、支援原地編輯與 revert | MyBrain 用 append-only log 檢查＋validate/reindex CI 程式化防腐化 |
| 寫入閘門 | 對話自動全錄 | 「人 review」當品質守門員 |

對照第二大腦（https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/LearnGhAgent.md，human:fatesaikou / stable，2026-07-26）：他**刻意把執行軌跡與知識分離**——軌跡不進知識庫，知識是經過人 review 的 output。Delta 反過來把「對話原文」當成知識載體本身。

**結論**：Delta 是「把對話當知識保存」；使用者機制是「把對話當軌跡、另以人 review 後的 output 為知識」。兩者哲學相反，不存在「誰更好」的單一答案——若目標是「程式碼與意圖的逐筆追蹤」，Delta 更細；若目標是「可驗證、可自我維護的知識」，使用者機制勝出，且與他 TencentDB/EverOS 的 Reject 判準一致。

---

### Q3：這東西真的是無損留下嗎？既然是 raw data，之後可以無損轉換？

**A**：不是純 append-only 無損。Delta 支援**原地編輯先前訊息並丟棄其後的回應**、以及 **revert 到較早點並一併還原 worktree**——這兩者都會破壞「無損原文留存」的前提。

| 操作 | 官方行為（delta.dev/docs） | 是否無損 |
|---|---|---|
| 發送新訊息 | 正常 append | 是 |
| 原地編輯先前訊息 | **發送後取代該訊息之後的對話（後續回應被丟棄）** | 否——後續原文消失 |
| revert 到較早點 | thread 回到該點，**並一併還原 worktree** | 否——較晚的對話與編輯狀態被回退 |
| 刪除 thread | 僅移除本機、伺服器副本不即時移除（retention/backup 可能暫留） | 否（伺服器端可能暫留，但非使用者可控的無損保證） |

儲存機制：DeltaDB 存「deltas in sequence」以重建 thread，本身是**可重建**的，但「可重建」≠「無損原文」——一旦使用者執行原地編輯或 revert，被取代的 delta 就不是可復原的完整原文。

**對使用者「若無損則不需防腐」立場的修正**：使用者正確指出「raw data 無損則之後可無損轉換、防腐只在轉換/收斂時必要」。但這個前提在 Delta 不成立——因為它支援破壞原文的操作（原地編輯、revert）。**Delta 不是無損 raw data 庫，因此防腐缺口比 R1 報告所述更實質**：它不是「沒做防腐化」，而是「連無損留存都不保證」。

**結論**：Delta 的對話留存**不是**無損 append-only；它提供破壞性編輯與回退。因此「raw data 無損即可無損轉換」的免防腐前提在 Delta 上不成立，防腐缺口成立且比 R1 判定更硬。

---

### Q4：這東西的記憶用途是「Code Review」而已？還是也有設計給「新機能開發設計」或「既有程式碼改修」？

**A**：不是只有 Code Review。官方 getting-started 明列的用途含**探索 codebase、修 bug、scaffold 新功能**；review 只是「bring changes in」前的整合閘門，非唯一用途。

| 用途 | 官方佐證（delta.dev/docs） | 定位 |
|---|---|---|
| 新功能開發（scaffold feature） | getting-started：「scaffold a feature」 | 明確支援 |
| 既有程式碼改修（fix a bug） | getting-started：「fix a bug」 | 明確支援 |
| 程式碼探索 | getting-started：「explore the codebase」 | 明確支援 |
| Code Review | review-and-sync：review 是 bring changes in 前的整合閘門；agent 在獨立 checkout 工作，review 後才 push local/origin | 整合前閘門，非唯一用途 |
| review 的載體 | comments：annotation 式 comment（選取文字片段附註、可回覆），agent 把 comment 當針對該段落的回饋 | review 的一種具體形式 |

**結論**：Delta 的用途涵蓋**新功能開發、既有改修、程式碼探索、Code Review** 四者，review 僅是其中一個整合閘門；它是以 thread 為單位的完整開發協作環境，不是 review 專用工具。
