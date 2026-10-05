# 279_R3_step2-plan_C1.md

## 狀況理解

R3 是「判定＋行動意向」輪（見 step1 log）：使用者下 **Accept(Weak)／試用**，並提兩點——追問1「AX 很像我的 MyLinuxPool 將要擔當的 ai 工位」、追問2「可能要實際部署嘗試一下」。

本 sub-step C1 任務＝**取得 repo metadata 與主要文件**。著眼點因 R3 語境而收斂為兩條：

1. **執行單元層**：把 AX 的 Task／Workspace（＝他口中的「ai 工位」）拆到能與 MyLinuxPool worker 對比的粒度。
2. **部署起步層**：取得追問2「實際部署」的真實前置成本（prerequisites、部署命令、外部依賴）。

R1 已固化三 primitive 與 Substrate 依賴基本盤；R2 已拆持久化與通訊層。C1 **不重做**，只補 R1/R2 未取的可執行細節，並複查 repo 是否已 drift。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view`／`gh api releases` | 刷新 metadata 與版本 | 確認 R1 數字是否仍成立 | **stars 13,127**（R1 為 11,655）、forks 558；description 改為 "Google's open agentic orchestration runtime"；`pushedAt` 2026-09-27；最新 release 仍 **v0.3.1**（2026-09-25） |
| `gh api .../contents/docs` | 確認文件有無增減 | 對齊 R1 的 docs 清單 | 仍為 concepts／development／logo／manifests／networking／roadmap／runner／sandbox（8 檔），無新增 |
| `git clone --depth 1 google/ax`（HEAD） | 取 code 真相 | 對照 docs 與現況 | HEAD＝`ac23328`（2026-09-27）"**Replace Redis Streams queue and controller with direct execution and resource locking**" |
| 讀 `README.md`、`docs/concepts.md` | 取官方定位與 primitive 定義 | 校正 R1 | Task／Workspace／Model 三 primitive 不變；仍明載「billions of tasks／Substrate／feel similar to Kubernetes」 |
| 讀 `DESIGN.md` | 取當前架構 | 檢查是否與 R1/R2 描述一致 | **已 drift**：現為 `ax-server`（direct-execution gRPC）＋Redis（Resource Store／**Locks**／PubSub）＋**fine-grained distributed locks**；已無「Redis Streams 佇列＋ax-controller」 |
| 讀 `internal/controller/reconciler.go`、`internal/lock/lock.go` | 驗證 direct execution | 判定新調和模型 | `TaskReconciler.Reconcile` 直接對 Substrate 建 Actor、Suspend/Resume；`Locker` 提供 per kind/atespace/name 排他鎖 |
| 讀 `Makefile`、`deploy/ax-server.yaml`、`deploy/redis.yaml`、`docs/development.md` | 追問2：部署前置 | 取得真實起步成本 | 需 K8s ＋ Substrate（`ate-system`）＋ Go 1.27+ ＋ `ko` ＋ registry；`make deploy`＝`deploy-redis`＋`deploy-server`（`ko apply`） |
| 讀 `docs/sandbox.md`、`runner.md`、`networking.md` | 執行單元：工位內部 | 拆 Task 的可比粒度 | runner 為 PID 1；`/workspace` DurableDir 卷；workspace 綁定可帶 `path`／`goal`（Antigravity，需 `GEMINI_API_KEY`，預設 10 分） |
| 讀 `examples/task.yaml`、`simple.yaml`、`manifests.md` | 取可運行範例 | 部署試用素材 | `simple.yaml`＝零 Workspace/Model 的最小 Task；`task.yaml`＝Task＋Workspace＋Model 一檔 |
| `git clone agent-substrate/substrate` 讀 README | 複查底層 | 校正 Substrate 定位 | 「run millions of sandboxes／10x density／sub-500ms resume／maps actors onto ready workers／K8s 供給 Pods」 |

## 動作結束後的現狀

### A. AX 的執行單元 vs 他的「ai 工位」

| 面向 | AX Task（含 Workspace） | MyLinuxPool worker |
|---|---|---|
| 單位 | 沙箱化 Substrate **Actor**（actor 以 task 命名） | 拋棄式 Linux 容器＋CodeAgent |
| 生命週期 | 有：Running／Suspended／Failed／Terminating，可 suspend/resume | 無生命週期狀態（`create`／`delete`） |
| 排程 | 有：Substrate 把 actor 排到 ready worker | **無排程** |
| 佇列 | 有：ax-server direct-execution ＋ per-resource 鎖 | **無佇列** |
| 環境準備 | Workspace 宣告式（git／MCP／skills／goal）在命令啟動前完成 | 無宣告層，靠進容器後自理 |
| 隔離 | gVisor／microVM（Substrate） | provider 之間**不互連**、無多租戶 |
| 對外路由 | 無自帶 Service；經 `atenet-router`＋header `ate-target-actor` | 無 |

判定：**AX 的 Task 是他「ai 工位」的企業級版本。** 兩者都是「一個被隔離、可丟棄的執行單元」；差別在 AX 把工位接上了排程、生命週期與宣告式環境準備，而 MyLinuxPool 刻意把這四項標為「沒有」。

### B. 追問2 的部署前置（實際試用的真實成本）

| 前置 | 內容 | 是否可繞 |
|---|---|---|
| K8s 叢集 | 需可 pull 自建 registry 的叢集 | 需（追問2 的門檻） |
| Agent Substrate | `ate-system` namespace；Control API `api.ate-system.svc:443`；另裝 | **不可繞**，AX 非自足 |
| Go 1.27+ / `ko` / registry | 建置與部署控制面映像 | 可繞（用預建映像） |
| Redis | `deploy/redis.yaml`（單 replica，無持久化設定） | `make deploy` 自帶 |
| `GEMINI_API_KEY` secret | 只有在 workspace 綁定帶 `goal` 時需要 | 可繞（用 `simple.yaml` 或無 goal 的 Workspace） |

一句話：**「實際部署」的最小路徑＝一個 K8s ＋ 一份 Substrate，然後 `make deploy` ＋ `ax apply -f examples/simple.yaml`。**

### C. 需修正的舊資訊（供 Step3 更新報告）

| 舊描述（R1/R2 報告） | 現況（HEAD 2026-09-27） | 依據 |
|---|---|---|
| 狀態存 Redis Streams、`ax-controller` 消費工作佇列 | 已改 direct execution ＋ distributed locks；`cmd/` 已無 `ax-controller` | HEAD commit／`DESIGN.md`／`cmd/` 清單 |
| stars 11,655 | 13,127 | `gh api` |
| description「declarative orchestrator…」 | 「Google's open agentic orchestration runtime」 | metadata |

不變項：三 primitive、Gateway 仍未實作、pre-1.0（v0.3.1）、依賴 Substrate。

## 其中的決斷點

| 意思決定面向 | 可選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 本 step 焦點 | 重跑 R1 三 primitive／聚焦執行單元與部署成本 | 後者 | R3 是判定＋部署意向；追問1 要可比粒度，追問2 要前置成本 |
| 「ai 工位」對照方式 | 通用容器/K8s 敘事／對他的 MyLinuxPool worker | 後者 | 他問「像不像我的」，答案取決於 worker 的實際邊界 |
| repo 是否重抓 | 沿用 R1 快照／重新 clone HEAD | 重新 clone | R1 快照已 drift；不複查會把舊架構寫進 R3 報告 |
| 架構漂移處理 | 靜默沿用／顯式標差異 | 顯式標差異 | Step3 需據此修正報告，不能讓 Redis Streams 舊敘事殘留 |
| 追問2 的處理 | 當 QA／當試用路徑 | 試用路徑 | 非質問句構；記為部署前置清單，不進 §5 |
| Substrate 是否重讀 | 引 R1／重抓 README 校正 | 重抓 | 需要其密度/resume 原文支撐「工位」能力邊界 |
