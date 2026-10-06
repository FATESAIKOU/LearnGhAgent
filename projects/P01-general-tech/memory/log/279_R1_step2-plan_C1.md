# 279_R1_step2-plan_C1.md

## 狀況理解

Step 1 已定調：標的為 Google 開源 Agent 工作負載編排器 **AX**（`google/ax`、官網 `agentexecutor.io`），核心意圖是回答「解什麼問題／為何發生／如何解／有何替代」，並以使用者自建的 MyLinuxPool／AIContainer（agent 執行環境線）為對照軸。影片觀點給出待驗證假設：全名 Open Agentic Orchestration、以 K8s 為類比、YAML 宣告 task／workspace／gateway／model、企業級、起步重。

本 sub-step C1 任務＝取得 repo metadata 與主要文件，確認官方真實定位、核心資源模型、與底層依賴，並檢核影片描述的 gateway 是否真的存在。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view google/ax` + `gh api repos/google/ax` | 取得 metadata | 掌握熱度、授權、語言、活躍度 | Go 專案、Apache-2.0、11,655 stars、558 forks、48 open issues；建於 2026-03-30，最新 push 2026-09-26（當日），明確活躍。homepage 指向 `agentexecutor.io` |
| `gh api .../readme`（base64 解碼） | 擷取主文件 | 官方自我定位與範例 | 定位句：「declarative orchestrator to run **billions** of autonomous agent workloads in a cluster」，明言「If you have used Kubernetes, ax will feel similar」。三 primitive：Task／Workspace／Model（README Why 表） |
| 抓 `git/trees/main?recursive=1` | 看檔案結構 | 判斷專案成熟度與子系統 | 完整 Go 佈局：`cmd/`（ax CLI、ax-server、ax-controller、ax-task-runner）、`internal/`（controller、substrate、workspace、store/redis、tunnel）、`pkg/apis/v1alpha1`、`runner/`、`docs/`、`deploy/`；含設計文件 DESIGN.md |
| 讀 `docs/concepts.md`、`docs/manifests.md` | 理解三資源語意 | 取得權威定義 | Task＝最小隔離執行單位（cheap、可 suspend 可丟棄）；Workspace＝宣告式環境（git／MCP／skills，可帶 `goal`）；Model＝provider＋參數＋K8s Secret 憑證 |
| 讀 `docs/roadmap.md` | 看發展階段與治理方向 | 判斷是否企業級 | 5 大項：核心 spec 穩定、Actor 架構、agentic environment、**SPIFFE 身分／治理／可觀測**、文件。含 idle 自動 suspend、task branching |
| 讀 `DESIGN.md` | 看架構與 API | 取得系統層級圖 | 狀態存 **Redis**（明言避開 etcd 單位數 GB／寫入瓶頸）＋ Redis Streams 當工作佇列；元件：ax-server（gRPC 8080）／ax-controller（可水平擴）／ax-task-runner（PID 1） |
| 讀 `docs/sandbox.md`、`docs/runner.md`、`docs/networking.md` | 補齊執行面 | 掌握 runner contract 與網路 | runner 是容器 PID 1，起 metadata server（80，HTTP+h2c）、備妥 workspace、跑 `spec.command`；除錯開 `spec.debug` 才有 guest service 與 `ax ssh`。網路走 Agent Substrate 的 **atenet-router**，以 header `ate-target-actor: <atespace>/<task>` 路由 |
| 抓 `examples/task.yaml`、releases | 確認可運行範例與版本 | 驗證是否 pre-1.0 | 範例 Task/Workspace/Model 齊備；最新 release **v0.3.1（2026-09-25）**，README 明載「major breaking changes prior to stable release」 |
| 查 `agent-substrate/substrate`、`agent-substrate/env` | 查底層依賴 | 判定 AX 是否獨立完整 | Substrate：3,814 stars、Apache-2.0；定位「run millions of sandboxes、10x density、sub-500ms resume、gVisor/microVM、framework agnostic」。AX 依賴 Substrate，**非自足** |
| 抓官方部落格（cloud.google.com，2026-05-20） | 補背景脈絡 | 取得官方問題陳述 | 作者 Jaana Dogan（rakyll）／Ethan Bao；問題：「long-running agent workflows are fragile and hard to manage」；原生能力：durable execution、secure isolation、session consistency、connection recovery、trajectory branching |
| webfetch `agentexecutor.io` | 比對官網與 repo | 驗證影片 gateway 說法 | 官網列 **四個** primitive：Task／Workspace／**Gateway（Network policies：allowlist hosts+ports、注入憑證）**／Model。但 repo README／docs／`ax.proto` 僅 Task／Workspace／Model，**無 Gateway** |
| 讀 `ax.proto`、`types.go` grep | 確認 API 是否含 Gateway | 判定 gateway 是否已實作 | proto service 只有 Task／Workspace／Model RPC；無 Gateway kind。官網的功能描述**超前於 repo 實作** |
| 查 contributors 與最新 commit | 看維護主體 | 判斷誰在主導 | 首貢獻者 `rakyll`（480 次，即 Jaana Dogan），另有 Google 員工；最新 commit 2026-09-26 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 官方定位 | README／官網／部落格 | 宣告式 agentic 編排執行層，跑在 Agent Substrate 之上，主打「billions of tasks、sub-second resume」 |
| 核心資源模型 | docs/manifests.md＋ax.proto | 目前實作 **3 個** kind：Task／Workspace／Model（`ax.io/v1alpha1`） |
| 影片 gateway 說法 | 官網 vs repo 對比 | 官網列為第 4 primitive，repo 尚未實作 → 影片描述的 gateway 屬**官網藍圖**，非當前 code |
| 與 K8s 的關係 | README 明喻＋DESIGN.md＋依賴 | 形式上 kubectl-shaped（apply/get/watch/describe）；但**狀態不存 etcd**，改存 Redis；且執行層外包給 Substrate |
| 成熟度 | releases＋README warning＋roadmap | pre-1.0（v0.3.1），宣告將有 breaking changes；roadmap 明列治理與穩定化為未完成項 |
| 底層依賴 | Substrate repo | AX 不獨立：需先裝 Agent Substrate（命名空間 `ate-system`），且需 `ko`＋registry 部署 |
| 背景脈絡 | 官方部落格 | 問題源自長程 agent workflow 脆弱、難可靠管理；五項原生能力已定義 |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 資料來源優先序 | 官網／部落格／repo 文件／二手評論 | 以 repo 文件為主、官網＋部落格為輔 | repo 是可驗證的實作真相；官網行銷語與 repo 有落差（Gateway 即例），須以 code 校正 |
| Gateway 的處理 | 當成既有 primitive／標為未實作藍圖 | 標為官網藍圖、repo 未實作 | `ax.proto` 與 docs 均無 Gateway；不校正會讓報告複製影片的過時描述 |
| 底層依賴是否納入 | 只講 AX／一併講 Substrate | 一併納入 | AX 的密度與 resume 能力實由 Substrate 提供，切開會誤判 AX 的能力邊界 |
| 是否另開 C2 | 併入 C1／拆出 C2 | 拆出 C2 | C1 已達 6000 字上限風險；替代方案（K8s Jobs、LangGraph、kagent、Agent Substrate 直用）與使用者 MyLinuxPool 對照需獨立篇幅 |
