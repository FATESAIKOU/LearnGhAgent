# 279_R2_step2-plan_C1.md

## 狀況理解

R2 意圖（見 step1 log）是把 AX 當**外部對照樣本**，檢驗使用者「AI 公司」這條線的三組缺口：Q1 AX 是否內建（a）產出持久化（AiStorage：MyBrain／Session／成果物）（b）worker 間通訊手段；Q2 AX 與 herdr 的層級差別；Q3 AX 有無「AI 團隊運作」概念。

本 sub-step C1 任務＝**取得 AX repo metadata 與主要文件**，但著眼點從「解什麼問題／如何解」轉為「資料層與協作層」，並補上 herdr 官網與 Agent Substrate 兩份外部事實。R1 已完成三層（Task／Workspace／Model）與 Substrate 依賴的基本盤；C1 不重做，改聚焦在 R1 未拆的兩問：**持久化邊界**與**任務間通訊邊界**。第二大腦座標已於 step1 取得，本 step 只補技術事實。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh`／`git clone google/ax`（v0.3.1 主線） | 取 code 真相 | 確認是否內建資料層／通訊層 | 讀 `docs/runner.md`、`sandbox.md`、`networking.md`、`concepts.md`、`manifests.md`、`DESIGN.md` |
| 讀 `docs/runner.md`、`sandbox.md` 持久化段 | Q1a：產出存哪 | 找儲存機制 | 唯一持久面＝`/workspace` **DurableDir 卷**（Substrate 提供），suspend 時快照、resume 還原；runner 寫 marker 在 `/ax`。**無**跨任務的成果物庫、無 Session 目錄、無查詢介面 |
| grep `internal/substrate/client.go` 快照設定 | Q1a：快照落點 | 找真本儲存 | `SnapshotsConfig` 走 bucket（預設 `gs://snapshot-substrate-test-ax-substrate/ate-env/`，可 `AX_SNAPSHOTS_BUCKET` 覆寫）；scope 為 `DATA`，只保 volume 內容，**不保 process memory** |
| grep Redis／DESIGN.md | Q1a：控制面狀態 | 判定狀態存放 | Redis 存 Task Hashes ＋ Event Streams ＋ PubSub，供 server↔controller。**這是控制面工作佇列，非住民資料層** |
| 讀 `docs/networking.md`＋grep task 間呼叫 | Q1b：任務間通訊 | 找 messaging／IPC | Task **無自己的 Service／Ingress**。入站一律經 Substrate `atenet-router`，靠外部帶 header `ate-target-actor: <atespace>/<task>`；無任務對任務的內建訊息匯流排 |
| clone `agent-substrate/substrate` 讀 `threat-model.md`、`roadmap.md` | Q1b：底層通訊契約 | 判定 actor 互通 | T-17：**actor 間網路預設全拒**（default-deny），需顯式放行。A2A 呼叫模型列在 **Substrate roadmap**（第 97 行「Actor-to-Actor（A2A）Calling Model」），**未實作** |
| 讀 `docs/egress-traffic.md`、`network-egress.md` | Q1b：對外通路 | 找唯一可用通道 | actor TCP 出站走 `atunnel`→egress gateway，**有政策與 allowlist**；WebSocket 與 CONNECT 被擋。入站＋出站是唯一兩條腿，皆經 Substrate，非任務間 |
| grep AX TaskSpec／credentials | Q1b：任務能否創建 sibling | 檢查有無 API 憑證 | `TaskSpec` 僅 image／command／env／resources／workspaces／debug。**無 service account／無 AX API token**→沙箱內 agent 無法呼叫 AX 建任務 |
| grep `docs/concepts.md` spawned | 確認「任務樹」說法 | 校正 README 敘事 | 原文只說 task「可以是大量被 spawned 的任務樹的 root」，但**未提供沙箱內 spawn 的介面**；屬概念描述非現行能力 |
| webfetch `https://herdr.dev` | Q2：herdr 層級 | 取一手定位 | 定位「the runtime coding agents run on」；**server 常駐**、認得 pane 內 agent 狀態（working／blocked／idle／done）、CLI／socket 可讓 agent 互相 prompt 並 `--wait`；跨本機＋SSH 多機；v0.9.1、40,432 stars |
| 讀 MyBrain（step1 已取）＋本 step 複核 | Q2／Q3：對照座標 | 對齊他的語彙 | 見「現狀」段，標信任層級與 URL |

## 動作結束後的現狀

### Q1a 產出持久化——AX 只有「沙箱存活」，沒有「資料層」

| 面向 | AX 現況 | 對照他的 AiStorage |
|---|---|---|
| 持久單位 | 單一 Task 的 `/workspace` DurableDir 卷；**per-actor** | MyBrain／Atelier／Agora／Foundry 四個獨立要素 |
| 跨任務共享 | 無。卷綁單一 actor template，**不跨任務** | 依「案件」跨 Session 彙整 |
| 真本落點 | bucket（DATA scope 快照） | Google Drive 上的 git-annex |
| 檢索／重播 | 無查詢介面 | Agora 附可擴充搜尋；Foundry 有產出目錄 |
| 身分 | 無 profile／無使用者模型 | 身分綁 profile；授權依 profile |

判定：**AX 的持久化止於「讓這個 sandbox 睡醒後還在」，不是「記住這家公司做過什麼」。** 他的 AiStorage 四要素在 AX 無對應物。

### Q1b worker 間通訊——AX 沒有通訊手段，預設隔離

| 通訊方向 | 現行機制 | 是否內建 |
|---|---|---|
| 外部 → Task | atenet-router ＋ header `ate-target-actor` | ✅ |
| Task → 外部 | atunnel → egress gateway（政策 allowlist） | ✅ |
| Task ↔ Task | Substrate **default-deny**（T-17）；A2A 在 roadmap 未實作 | ❌ |
| Task → AX 控制面（建 sibling） | 無 token／service account | ❌ |
| 共享媒介 | Workspace 可共同 clone 同一 git／指向同一 MCP endpoint（**間接**） | ⚠️ 非訊息匯流排 |

判定：**「worker 之間如何通訊」在 AX 的答案是「不允許，且沒有內建手段」。** 可用的只有間接共享（共同 git remote／MCP server）與外部客戶端逐 task 路由。

### Q2 herdr 差別——不同軸，不是同一層的替代

| 面向 | herdr | AX |
|---|---|---|
| 層 | agent **互動／注意力**層（終端 server） | agent **工作負載**層（叢集控制平面） |
| 協調單位 | pane 裡的**對話** | 沙箱化的 **Task** |
| 跨機 | SSH 串多機，同一 herd | K8s＋Substrate 排程 actor |
| 狀態感知 | 認得 working／blocked／idle／done | 只認 Task phase／condition |
| 交棒 | `herdr agent prompt <name> --wait` | 無；task 不可變、無 prompt 介面 |
| 隔離 | 終端 session，共用使用者環境 | gVisor／microVM 強隔離 |

判定：**herdr 編排「誰在做什麼、誰卡住等你」；AX 編排「沙箱開幾個、睡醒多快」。** 一個管對話與人機接力，一個管算力與隔離。

### Q3 AI 團隊運作——AX 無組織模型

| 組織要素 | AX | 他既有座標 |
|---|---|---|
| 職務（know／do／judge／dont） | ❌ 無 | Atelier 以職務為單位（`draft`, claude-code/opus-5.5） |
| 員工身分／profile | ❌ 無（atespace＝隔離邊界，非部門） | AiStorage：身分綁 profile（`draft`） |
| 交接／信箱 | ❌ 無（A2A 未實作） | Agora 交接單（`draft`） |
| 團隊拓樸 | ❌ 無；primitive 只有 Task／Workspace／Model | munder-difflin 判**不採用**（GUI 限制、固定拓樸、還太早，`draft`） |

判定：**AX 有「多任務」，沒有「多職務」。** atespace 最接近組織概念，但它是隔離邊界而非團隊；Workspace／Model 是共用環境與憑證，不是角色。

MyBrain 座標（唯讀，僅供 C2 對照）：[MyLinuxPool](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/MyLinuxPool.md)（worker 無狀態、provider 不互連、無排程佇列，`draft`）、[AiStorage](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/AiStorage.md)（四要素，`draft`）、[herdr 配置](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/herdr%20配置.md)（`draft`）、[munder-difflin](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/munder-difflin.md)（`draft`）、[AIContainer](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/靈感/AIContainer.md)（`draft`）。**查不到**：無 `google/ax`／Agent Executor 任何紀錄（0 命中）；無 herdr 與編排器的直接對比；無「AX 是否滿足 AI 公司需求」的既有判定（本輪新作）。

## 其中的決斷點

| 意思決定面向 | 可選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 本 step 調研焦點 | 重跑 R1 的三 primitive／聚焦資料層與通訊層 | 後者 | R1 已固化基本盤；R2 三問全落在 R1 未拆的兩層 |
| 持久化判定依據 | 只讀 AX docs／追進 Substrate 快照契約 | 追進 Substrate | `/workspace` 的持久能力實由 Substrate DurableDir 提供，只看 AX 會誤判為「AX 有資料層」 |
| 任務間通訊的證據等級 | 以 README「task tree」當現行能力／以 code＋Substrate threat-model 校正 | 後者 | TaskSpec 無憑證、actor 間 default-deny；README 的 tree 是概念敘事 |
| herdr 事實來源 | 只引 MyBrain 舊筆記／另抓官網一手 | 兩者並用 | 舊筆記記 v0.8.0，官網已 v0.9.1；層級判定需一手證據 |
| 「AI 團隊」判準 | 用通用 multi-agent 定義／用他的職務＋profile＋交接座標 | 後者 | 他問「有沒有」，答案取決於他自己的組織語彙 |
