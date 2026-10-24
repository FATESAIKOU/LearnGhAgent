# OpenRig 技術分析報告

> 調研標的：https://github.com/mvschwarz/openrig
> 版本：v0.6.10（2026-10-12） | License：Apache-2.0 | Stars：7,579 | Forks：592 | 主要語言：TypeScript
> 建立：2026-04-01 | Apache-2.0 | open issues 177 | subscribers 30
> 自述定位：「A harness wraps a model. A rig wraps your harnesses.」——在既有 CLI agent（Claude Code／Codex／Pi）之上架一層「團隊層」，管理 agent 組成的系統，而非 agent 本身。
> 來源：GitHub 一週熱點 135 期。⚠️ 該影片無字幕軌（transcripts disabled），逐字稿與影片觀點取不到；本報告的動機與機制來自 repo 一手文件與作者官方部落格，缺口已標明。
> 註記：本次調研為 R1 首輪，無使用者提問，故無 §5 User Q&A。

---

## 1. 這個技術解決什麼問題？

**OpenRig 解決的問題是：當一個人同時跑多個既有的終端 coding agent（Claude Code、Codex、Pi 等）時，這些 agent 只是一堆彼此獨立、各自為政的終端 session，缺乏一個「系統層」來定義團隊結構、啟動與還原、投遞訊息、共享 context、追蹤歸屬的工作，並在重開機後恢復整支團隊。**

README 的定位句把層級講清楚：**harness 包住一個 model，rig 包住你的 harnesses**。它不改善 agent 本身的能力，而是管理「多個 agent 一起運作時形成的系統」。

具體子問題（皆出自 repo 一手文件與作者官方部落格）：

| 子問題 | 具體內容 |
|---|---|
| **重開機即失去拓樸** | agent 團隊形成有機的協作結構後，重開機無法重建；作者自述曾發生「忘記某支 agent 存在」的情形。問題不在 session 有沒有存檔，而在**整個團隊的關係與角色沒有被持久化**。 |
| **agent 不知道「自己不知道什麼」** | 作者把 Slack 整合做到一半擱置一個月，之後叫 agent 接手，agent 找到能動的東西、也做出可用的整合，卻**另外重造了一套訊息系統**。文件與舊工作都在，問題是 agent 沒有理由去找它們。 |
| **協調失敗（跨 agent）** | ①**範圍膨脹（scope inflation）**：要一個狗屋，agent 一步步「合理地」加上燈、電、發電機、燃料，最後變成月面基地，原始需求消失；每一步在該 agent 的 context 內都站得住。②**服從錯誤權威**：agent 向另一個 agent 請求核准，而對方有大局但沒有細節，資訊被切成兩半、無人拼起來。 |
| **終端蔓延（terminal sprawl）** | 多個 agent 散在各自的終端視窗，缺少單一視圖掌握「哪些 session 在跑、關係為何」。 |
| **跨 agent 通訊與工作歸屬** | 一個 agent 的產出如何交給另一個 agent 接續、哪件工作屬於誰、狀態如何查，沒有統一載體。 |

**問題描述是否含糊**：README 用「network of agents」「AI civilization」等行銷語言包裝。作者自己在部落格中也承認這是**框架（framing）**——他把多 agent 系統類比成人類文明，用意是借用人類處理協調失敗的既有方法。可調研的具體問題域是 **「多 agent harness 的協調層」**：不解決 agent 能力，只解決「把多個既有 agent 組織成可持久、可還原、可通訊的團隊」。此定位在 ARCHITECTURE.md 與 rig-spec.md 中有明確機制支撐，非空泛口號。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **終端 coding agent 是單一程序、單一 session**：Claude Code、Codex 等設計為「一個使用者對一個 agent」，沒有內建的多 agent 通訊、共享狀態或團隊拓樸。
- **agent 生態碎片化**：不同 CLI 由不同廠商維護，各有獨立 session、記憶與工具介面，彼此沒有標準化協作協定。
- **context window 是有限的**：把任務拆給多個專精 agent 是自然延伸，但協作機制（通訊、記憶、仲裁、審計、還原）不隨之自動出現。
- **重開機／壓縮是 context 的斷點**：作者自述長期使用 capable coding agent 後反复遇到同一類失敗——agent 在 context 被壓縮（compaction）後失去方向，或接手時不知道專案已有哪些系統。

### 通用技術背景（文章中未逐條明示，但為必要脈絡）

- **「多 agent 協作」是 agent 工程的新興問題域**：單一 agent 的 context 與工具能力有上限，多 agent 是自然延伸，但協作機制尚未標準化。
- **tmux 作為可持久化的程序載體**：tmux session 可 detach、可 attach、可存活於使用者離開之後，是「讓 agent 常駐且可被觀察」的現成基礎。OpenRig 直接建在 tmux 之上。
- **既有 harness 多支援 hook／telemetry**：Claude Code、Codex 支援 hook 與設定檔，讓外部系統能在 agent 生命週期介入（預信任、注入技能、追蹤活動），是 harness 控制 agent 迴圈的縫隙。
- **SQLite 作為本機狀態庫**：單機、零維運、WAL 模式即可承載 daemon 的持久狀態。
- **作者本人的實作史**：OpenRig 是作者「AI civilization experiments」的開源化；他自述約十八個月前開始讓兩支 coding agent 互相對話，成長為數百支（任何時刻真正工作的只是一小部分）的機隊，並在 Mac Mini 與 VPS 上運行。OpenRig 是這套自建系統的產品化。

### 對照使用者本人的現行處境（來源：第二大腦，見 §4）

使用者目前在 Mac 上用 **herdr** 開 PM／Impl／Test／Review 四個 pane 跑多 agent 開發（`claude-code/opus-5`／`draft`，[herdr 配置](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E5%8B%95%E6%89%8B%E5%81%9A/herdr%20%E9%85%8D%E7%BD%AE.md)）。該流程已踩到與本節相同的問題：兩個專案的 PM 共用同一 session id 而認錯身分、隊員「想完就結束」卻回報 done、驗收不可看 exit code。**這些正是 OpenRig 想解問題的現行手工版**——協調工作目前落在人身上（人當 message bus）。

---

## 3. 這個技術是如何解決該問題的？

OpenRig 以**本機 daemon** 為核心，把多個既有 CLI agent 包成一個可定義、可啟動、可還原、可通訊的團隊。agent 本身不被修改，OpenRig 只加上「它們周圍的協調」。

### 3.1 架構總覽

```
┌───────────────────────────────────────────────────────────────┐
│  前端（皆走 local HTTP 對 daemon，預設 port 7433）              │
│    rig CLI        openrig-tui（TUI）      MCP server（stdio）   │
│         \                |                /                    │
│          +─────── HTTP ──+───────────────+                     │
│                          |                                     │
│              Hono HTTP daemon（packages/daemon）               │
│   routes/ → domain/（services、orchestrators、event bus）      │
│                          |                                     │
│     SQLite（WAL）  +  tmux  +  runtime adapters                │
│                                     claude-code / codex /      │
│                                     pi / omp / terminal / stub │
└───────────────────────────────────────────────────────────────┘
        ↓ 每個 seat 是一個可 attach 的真實 tmux session
┌───────────────────────────────────────────────────────────────┐
│  RigSpec（YAML）：pods / members / edges / continuity_policy / │
│                   culture_file / startup / services            │
│  Seat＝穩定角色位址，如 dev-build@starter                       │
└───────────────────────────────────────────────────────────────┘
```

五個 package：`@openrig/daemon`（私有，HTTP 路由＋domain＋migration＋adapter）、`@openrig/cli`（唯一發布的 npm 套件）、`@openrig/tui`、`@openrig/ui`（React web UI，維護模式）、`test-system`（stub 情境庫，不發布）。狀態存於 `$OPENRIG_HOME`（預設 `~/.openrig`）。

### 3.2 核心機制

#### (1) RigSpec：把團隊拓樸變成宣告式 YAML

- **RigSpec v0.2（pod-aware）** 以 YAML 定義：`pods`（群組，含 `members` 與 `edges`）＋ `continuity_policy`（續存政策）＋ `culture_file`（群體規範）。
- **Seat（座席）** 是穩定角色位址，如 `dev-build@starter`：**佔據該座席的對話可以更換，但身份與已撰寫的 context 留存**。這是「重開機不失拓樸」的關鍵——拓樸先於 session。
- **edge** 描述成員關係（如 `delegates_to`、`can_observe`），把「誰能對誰派工、誰能觀察誰」明文化。
- 團隊用 `rig grow`／`shrink`／`launch`／`remove` **演化**，不是重建。

#### (2) 啟動與還原：boot / snapshot

- `rig up` 一次啟動：tmux session、harness、啟動檔、就緒檢查。
- `rig down --snapshot` 捕捉完整狀態；`rig up <name>` 依名稱還原。
- **還原逐 node 回報結果**：`resumed`（續行）／`fresh-primed`（以既有 context 重新起）／`awaiting-decision`（原對話無法續行，需選 `--fresh`）／`attention_required`／`failed`。**不是一句「還原成功」**，而是把每個座席的真實結果攤開。

#### (3) 通訊：座席之間有地址

| 指令 | 作用 |
|---|---|
| `rig send <seat> "..."` | 送訊息給某座席（線上 agent） |
| `rig broadcast` | 對全體廣播 |
| `rig chatroom` | 群組對話 |
| `rig ask <rig> "..." --seat <s>` | **對離線座席的既有 session 歷史做搜尋**（非第二次 LLM 呼叫），必要時 `--wake` 喚醒原 session |
| `rig capture` | 取回輸出 |

「離線也能問」是其關鍵差異：**不需要每支 agent 常駐，仍保有一條通往它曾知道什麼的路徑**。

#### (4) Context library：把專案 context 變成可導航的結構

延續 §1「agent 不知道什麼存在」的問題，OpenRig 提供：

- `rig context get 'path.md#heading'`：**只取某個標題底下的段落**，而非載入整份文件；段落內再以連結導向更深處（progressive disclosure）。
- `AGENTS.md` 當作 trailhead，配一個 router skill 讓 agent 認出「我現在需要哪一區」。
- **ontology（有哪些東西與關係）＋ topology（整體形狀與連結）＋ epistemology（什麼知識值得信任、階層為何）** 三支點；並用 **lore** 存放「故事／教訓」（如狗屋變月面基地的案例），在 onboarding 與 compaction 後遞給接手座席。
- **Refocus**：沿著「手上的任務→所屬專案」的鏈把意圖重新放回 agent 面前，對治範圍膨脹。

#### (5) 內建團隊與 runtime

- **三支漸進團隊**：`starter`（builder＋reviewer）、`workshop`（lead＋builder＋QA＋reviewer）、`factory`（7 人：lead、advisor、build、QA、design、兩個獨立 reviewer）。
- **專科隊**：`code-review`、`research`、`pm`。
- **`secrets-manager`**：由專科 agent 操作的 HashiCorp Vault 實例（需 Docker）。
- **六種 runtime adapter**：`claude-code`、`codex`、`pi`、`omp`、`terminal`、`stub`。ROADMAP 規劃新增 OpenCode／Cursor／Grok／Devin 的共享 adapter。
- **Discovery / Adopt**：`rig discover` 指紋比對既有 tmux session，`rig adopt` 納入管理。
- **RigBundle**：可攜 archive，內含 vendored AgentSpec 與 SHA-256 完整性檢查，跨機器共享拓樸。

#### (6) 權限與非侵入模式

- 團隊座席預設有 per-launch 的「team default」（Claude 可跑一般 `rig` 指令、專案讀取與常見測試，不需逐一提示；`rig up`／`rig down` 等生命週期指令仍會詢問）。
- **YOLO 預設關閉**；`--non-interruptive` 只是略過 harness 的警告對話框，不授予權限、不寫入設定檔。
- 安裝會寫入 provider hook、workspace trust 設定與 `.codex/plugins/` 等檔案；README 有專章列出「OpenRig 會在你機器上改什麼」，並要求先備份。

### 3.3 一句話機制

**把「多 agent 團隊」這個原本只在使用者腦中與終端裡的有機結構，抽成一份可宣告、可啟動、可還原、可演化、可通訊的 YAML 拓樸，並以本機 daemon＋SQLite＋tmux 持久化，讓 agent 有地址、有角色、有共享 context、有歸屬的工作。**

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

以下替代方案**對照第二大腦（FATESAIKOU/MyBrain）的既有判定**。每則標 GitHub URL 與信任層級；AI／process draft 均註明「未經他 review」。**OpenRig 本身在第二大腦中零命中**（grep `openrig` 全 bundle 無結果）。

### 4.1 第二大腦既有判定（同問題域）

| 標的 | 判定 | 信任層級 | 首見 | 來源 |
|---|---|---|---|---|
| **Aionui** | 採用 | `human:fatesaikou` / `stable` | 2026-07-12 | https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/Aionui.md |
| **munder-difflin** | 不採用 | `process:learn-gh-agent` / `draft`（未經他 review） | 2026-08-30 | https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/munder-difflin.md |
| **Paperclip** | 觀望（Reserve） | `process:learn-gh-agent` / `draft`（未經他 review） | 2026-10-06 | https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/Paperclip.md |
| **herdr（現行手工流程）** | 動手做中（實測持續累積） | `claude-code/opus-5` / `draft`（未經他 review） | 2026-08-11 | https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E5%8B%95%E6%89%8B%E5%81%9A/herdr%20%E9%85%8D%E7%BD%AE.md |

**判定語意**（[技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%BD%E8%B1%A1%E7%90%86%E8%A7%A3/%E6%9C%AC%E8%B3%AA%E6%B4%9E%E5%AF%9F/%E6%8A%80%E8%A1%93%E5%8F%96%E6%8D%A8%E6%BA%96%E5%89%87.md)，`claude-code/opus-5` / `draft`，未經他 review）：「不採用」≠ 沒價值，仍抽取需求理解與方案方向；「觀望」＝有價值但未排入下一步。

### 4.2 DA 表：替代方案對照

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Aionui**（第二大腦：採用，`human:fatesaikou`/`stable`） | Electron 前端＋Rust 後端（AionCore），內建 agent 引擎＋ACP 多 agent 協作協定＋Team Mode（Leader 拆解任務給 Teammate）＋排程＋遠端存取 | 需裝桌面 app；多 agent 協作依賴其自定義 ACP 協定 | 綁定 AionCore 內建引擎與 ACP 生態；GUI 形態 | 統一桌面介面管理多個 agent；他特別在意 OfficeCLI 連動、ACP 協定、私人 Agent 系統設計 |
| **munder-difflin**（第二大腦：不採用，`process`/`draft`） | Electron 桌面 app，把 CLI agent 包成像素辦公室；hive（git-as-audit 記憶／信箱／事件 log）＋GOD agent（Michael）仲裁 | 需裝桌面 app；每個座位掛一個真 CLI agent | GUI 綁定；只提供一種拓樸；pre-release、單人維護 | 多 agent 有共享記憶、信箱、仲裁與可稽核歷史，但形態固定 |
| **herdr＋tmux（使用者現行）** （第二大腦：`claude-code/opus-5`/`draft`） | 終端多工器，認得 pane 內跑哪個 agent 並追蹤 idle／working／blocked／done，開放狀態給 CLI；他手動開 PM／Impl／Test／Review 四 pane | 在終端手動編排；協調規則由人維護 | 協調工作落在人身上（人當 message bus）；無持久共享記憶、無自動還原拓樸 | 已能平行跑多 agent 完成完整專案，但重開機與身分管理靠人的紀律 |
| **Paperclip**（第二大腦：觀望，`process`/`draft`） | AI agent 團隊的開源控制平面：company 為單位、org chart＋adapter 定義 agent、heartbeat 喚醒、任務目標樹、budget hard-stop 與 approval gate | 需接受其 company／adapter 資料模型；規模大 | 全整合難局部擴張；導入重 | 與「Ai 公司架構」高度同構，是機制抽取來源，非替換標的 |

> 另有同軸但第二大腦無紀錄的 **Claude Code 原生 subagents／Agent SDK**（通用知識，非第二大腦判定）：以設定檔定義 subagent、由主 agent 分派，屬「單一 harness 內」的分工，不是跨 harness／跨廠商的團隊層——與 OpenRig 的切入點不同（見下）。

### 4.3 切入點差異分析

- **OpenRig vs Aionui**：兩者都在解「多 agent 的協調層」，且都已被第二大腦以「採用／Accept」看待（Aionui 是既有採用項）。差異在**載體與開放度**：Aionui 是 Electron 桌面單體＋自帶 AionCore 引擎＋自定義 ACP；OpenRig 是 **CLI／TUI／MCP＋本機 daemon＋tmux**，把既有 harness 原封不動包起來（不替換引擎）。若在意「不被 UI 綁住」，OpenRig 的形態比 Aionui 更貼近該偏好。
- **OpenRig vs munder-difflin**：兩者都「把 CLI agent 包成團隊」，但 munder-difflin 被判不採用的兩個核心理由，**在 OpenRig 上不成立**（見 4.4 衝突一）。munder-difflin 的協作載體是 git repo（hive）＋單一 GOD agent；OpenRig 的載體是 SQLite＋tmux＋YAML 拓樸，且拓樸可 grow／shrink／換。
- **OpenRig vs herdr（現行）**：herdr 是**程序層／UI 層**——它認得 agent 狀態、能把「送指令並等對方做完」做成 CLI，但派工、裁決、記憶放哪仍由人決定。OpenRig **直接把 herdr 當底層依賴安裝**（`rig setup` 預設裝 herdr；有 herdr 時 `rig terminal open` 用它排版）。亦即 **OpenRig 建於 herdr 之上**，把使用者現行手工的協調層系統化。
- **OpenRig vs Paperclip**：Paperclip 是**企業治理導向**的控制平面（company、budget hard-stop、approval gate），規模過大；OpenRig 是**單機、開發者個人向**的團隊層。兩者同問題域但層級不同。
- **OpenRig vs Claude 原生 subagents**：後者在**單一 harness 內**分工，不能把 Claude Code 與 Codex 放進同一團隊；OpenRig 的命題正是**跨 harness／跨廠商的團隊層**。

### 4.4 與第二大腦既有判定的衝突（對照最有價值處）

**衝突一：munder-difflin 的不採用理由，對 OpenRig 不成立。**
munder-difflin 的不採用三理由（`process:learn-gh-agent`／`draft`）為：①基於 GUI，不想被限制 UI；②它引入的解決方案本質上是多 Agent 協作的一種拓樸，而需要的是**能自由切換的拓樸**；③排在其他專案之後、太早且包太多。其中：**①與②直接不適用於 OpenRig**——OpenRig 的主介面是 CLI／TUI／MCP（web UI 已進維護模式），且其核心命題就是**以宣告式 YAML 定義、可 grow／shrink／換的拓樸**，正是理由②所缺的「可自由切換」。理由③則**部分仍適用**（見衝突三）。**此處必須指出**：把 munder-difflin 的「不採用」直接外推到 OpenRig，會得到與事實相反的結論——兩者共享「多 agent 團隊」命題，但 munder-difflin 被否的兩個特徵恰好是 OpenRig 刻意解決的點。

**衝突二：使用者現行 herdr 手工流程 vs OpenRig 的關係。**
依 [技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%BD%E8%B1%A1%E7%90%86%E8%A7%A3/%E6%9C%AC%E8%B3%AA%E6%B4%9E%E5%AF%9F/%E6%8A%80%E8%A1%93%E5%8F%96%E6%8D%A8%E6%BA%96%E5%89%87.md)（`claude-code/opus-5`／`draft`）「**理解優先：不夠穩定或不熟悉就先自己兜**」，OpenRig 屬「不夠穩定、不夠熟悉」（2026-04 建立、約 5 個月、v0.6.x、單人維護、177 open issues），觸發「先自己兜」——**而使用者已經在兜**（herdr 四 pane 手工流程）。兩者不是二選一，而是**同一問題的手工版與系統化版**；OpenRig 反而把 herdr 當底層。⚠️ 依準則，**不要把「他不穩定」讀成否定**，它是抽取機制與需求理解的來源。

**衝突三：排序／「太早且包太多」是否仍成立。**
munder-difflin 理由③的前提是「多 agent 架構的 AI Container 得排在個人 AI 入口／MyBrain／LLMGateway／AI 共通執行環境之後」。依 [個人 AiAgent 入口](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E5%8B%95%E6%89%8B%E5%81%9A/%E5%80%8B%E4%BA%BA%20AiAgent%20%E5%85%A5%E5%8F%A3.md)（`claude-code/opus-5.5`／`draft`）現況：入口已做出並實用、MyBrain 營運中、LLMGateway 已獨立成專案、MyLinuxPool 機器池已上線。**排序之前提已大幅鬆動**，但 OpenRig 仍屬「包很多」的全整合系統，此點部分成立。⚠️ 使用者 [下一步清單](https://github.com/FATESAIKOU/MyBrain/blob/main/%E5%B0%88%E6%A1%88/%E4%B8%8B%E4%B8%80%E6%AD%A5%E6%B8%85%E5%96%AE.md)（骨幹，`claude-code/opus-5`／`draft`）**沒有 OpenRig 條目**，本報告是決策材料而非既定動作。

**衝突四：OpenRig 對應的是「入口」還是「AIContainer」。**
個人 AiAgent 入口自述其形態是「App＋Backend、服務簡單問答」；服務複雜任務的**另一個**東西是 AIContainer（「一台 Linux＋CodeAgent」，`claude-code/opus-5.5`／`draft`）。OpenRig 這類「一台機器上跑多個 agent 團隊」的系統，**對應的是 AIContainer 一側，而非入口一側**。把 OpenRig 讀成入口的下一個版本是範疇錯誤。

**衝突五：統一的兩端稅。**
[統一的兩端稅](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%BD%E8%B1%A1%E7%90%86%E8%A7%A3/%E6%9C%AC%E8%B3%AA%E6%B4%9E%E5%AF%9F/%E7%B5%B1%E4%B8%80%E7%9A%84%E5%85%A9%E7%AB%AF%E7%A8%85.md)（`draft`）的判準是「先問是同一件事的不同實作，還是不同的事」。OpenRig 把**拓樸定義、agent 啟動、context library、訊息投遞、snapshot、權限**收進同一系統；判斷其整合是「同一件事的不同實作」還是「不同的事」，會決定導入的兩端稅高低。

### 4.5 依技術取捨準則的對應

| 準則 | OpenRig 的對應 |
|---|---|
| **理解優先**（不穩定／不熟→先自己兜） | 5 個月、單人維護、v0.6.x、177 open issues → 觸發「先自己兜」；使用者已有 herdr 手工版 |
| **MVP→Feature 唯一閘門＝能否影響個人 workflow** | 使用者的多 agent 開發 workflow 已存在（herdr 四 pane＋MyLinuxPool），OpenRig 問的正是這條 workflow 的系統化，屬**直接相關** |
| **Reject ≠ 沒價值** | 即使不採用，OpenRig 的「Seat 穩定地址」「snapshot 逐 node 回報」「rig ask 對離線 session 搜尋」「context get 段落定址」「Refocus」是可抽取的方案方向 |
| **約束在 harness 不在權限** | ⚠️ 依準則「**不要建議加人工審核關卡**，要補驗證機制」。OpenRig 提供還原結果回報、活動遙測、`--verify` 等**驗證向**機制；其 approval／permission 屬 harness 內設定，不是要使用者逐動核准 |
| **通用執行能力無法同時是受限能力** | OpenRig 給 agent 的是一台機器上的真實 tmux session，與此例外一致——邊界應落在機器配置，非 harness 黑名單 |

---

## 附錄：調研資料來源

- `README.md`（約 476 行）：定位、安裝、team default、OpenRig 會改機器上什麼、Teams、Key Concepts
- `ARCHITECTURE.md`：五個 package、request path、daemon 內部分層、adapter、狀態位置
- `docs/reference/rig-spec.md`：RigSpec v0.2（pod-aware）欄位與完整範例
- `docs/reference/*`（逾 50 檔）：getting-started、agent-spec、edge-types、topology-naming、non-interruptive-mode 等
- 官方部落格：〈[Context engineering as world building](https://openrig.dev/blog/how-my-agent-teams-find-their-way)〉（2026-10-16）——context library、ontology／topology／epistemology、distributed context engineering、Doghouse Moonbase 案例
- 官方部落格：〈['Rogue' is doing a lot of work](https://openrig.dev/blog/agent-civilizations)〉（2026-09-18）——scope inflation、權威來源錯誤的協調失敗、Refocus
- GitHub API 實查（2026-10-17）：stars 7,579／forks 592／open issues 177／subscribers 30／created 2026-04-01
- RELEASES／CHANGELOG：v0.6.10（2026-10-12）為最新；npm `@openrig/cli`
- 第二大腦對照：判定總表、技術取捨準則、Aionui、munder-difflin、Paperclip、herdr 配置、個人 AiAgent 入口、下一步清單（皆附 GitHub URL 與信任層級）
- ⚠️ 來源限制：GitHub 一週熱點 135 期影片**無字幕軌**，影片觀點未納入；動機與機制以 repo 一手文件與作者官方部落格補齊
