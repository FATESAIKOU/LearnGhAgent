# AX（Agent Executor）— Google 開源的 Agent 工作負載編排器

> 標的：`google/ax`（官網 `agentexecutor.io`）／Go／Apache-2.0
> 調研時點：2026-09-26。repo 最新 push 同日、最新 release `v0.3.1`（2026-09-25）、建於 2026-03-30。
> 全名對照：repo 自我定位為 *declarative orchestrator to run billions of autonomous agent workloads in a cluster*；產品別名 Agent Executor。

---

## 1. 這個技術解決什麼問題？

AX 解決的問題是：**長程（long-running）agent 工作負載在生產環境中難可靠、難有效率地管理。**

具體拆成四個被解決的子問題：

| # | 被解決的具體問題 | 問題成立的場景 |
|---|---|---|
| P1 | **agent 任務沒有可規模化的隔離執行單位** | 同時有成千上百個 agent 任務，每個會裝工具、拉 repo、跑程式，彼此必須互不污染 |
| P2 | **agent 大部分時間在等待，卻持續佔用資源** | agent 在等模型回應、等 tool 回應、等人類確認；閒置時 sandbox 仍活著的成本高 |
| P3 | **每個 agent 框架各自重造啟動前的環境準備** | 每個任務都要重新 clone repo、裝 toolchain、掛 MCP、載 skill，重複且易漂移 |
| P4 | **大量短命任務會壓垮傳統控制平面** | 以 Kubernetes CRD 承載百萬級短命 task，會撞上 etcd 的儲存上限與寫入瓶頸 |

官方部落格（Jaana Dogan／Ethan Bao，2026-05-20）對問題的原始陳述為一句話：

> "long-running agent workflows are fragile and incredibly hard to manage reliably and efficiently in production."

**問題描述中的模糊處（需指出）**：

| 模糊處 | 說明 |
|---|---|
| 「billions of tasks」的單位 | README 與官網以「billions」描述規模，但未定義 task 的平均生命週期、並發峰值與「registered vs concurrently running」的差別。此數字是設計目標，不是已驗證的實測值 |
| 「orchestration」的範圍 | 影片觀點將 AX 直接對比 K8s 的 orchestration。AX 實際外包了執行層給 Agent Substrate，自身只做宣告式控制平面與排程。把 AX 等同於「Agent 時代的 K8s」是把兩層壓成一層 |
| Gateway primitive 的存在性 | 官網列為第 4 個 primitive，repo 的實作與文件皆無此 kind（詳見 §3 與附錄 A）。官網與 repo 對「當前能力」的陳述不一致 |

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 agent 是一種新的工作負載型態

問題的根因不是「工具不夠多」，而是 agent 的執行形狀與既有兩種運算抽象都不吻合：

```
                    狀態      生命週期        資源使用
微服務          ──  無狀態    長命常駐        平穩
batch job       ──  一次性    跑完即結束      可預測
agent workload  ──  累積狀態  長命且反覆等待   爆發式（算一下、等很久）
```

官方原文：「They are neither microservices nor batch jobs. They accumulate state, need strict isolation, call out to model APIs and tool servers, and can waste resources if nobody is watching.」

三個性質推導出三個需求：

| agent 的性質 | 推導出的需求 | 對應子問題 |
|---|---|---|
| 累積狀態、可中斷可續 | suspend／resume 與狀態快照 | P2 |
| 呼叫外部模型與工具、可能執行不可信程式碼 | 強隔離 + 網路與憑證邊界 | P1 |
| 爆發式資源使用、多數時間閒置 | 高密度多工（oversubscription） | P2 |
| 任務數量級遠高於服務數量級 | 控制平面要能承受高頻短命寫入 | P4 |

### 2.2 背景中「文中明確提到」與「通用技術背景」的區分

| 類別 | 內容 | 出處 |
|---|---|---|
| **文中明確提到** | 長程 workflow 脆弱且難管理（官方部落格）；既有 orchestrator 對「保持閒置 sandbox 常開」成本過高，且缺乏原生 sub-second suspend/resume（官網 About）；etcd 單數字 GB 儲存上限與寫入瓶頸（DESIGN.md，明確寫出為何不用 CRD） | 官方文件 |
| **文中明確提到** | agent 瓶頸已從「能力」轉向「信任」：智力來自模型，信任來自 runtime／身分／治理／安全 | 第二大腦〈AI 分層商品化與信任瓶頸〉（見 §4） |
| **通用技術背景** | Kubernetes 是為「數千個長命服務」最佳化，不是為「數百萬個 sub-second 呼叫」設計 | 此為容器編排的通用限制；官方以「standard Kubernetes is optimized to handle thousands of long-running services」對照說明 |
| **通用技術背景** | namespace + cgroup 隔離無法防 kernel 漏洞導致的容器逃逸，多租戶場景需 gVisor／microVM 級隔離 | 通用資訊安全背景；Substrate 以支援 microVM 與 gVisor 回應此點 |

### 2.3 為何出現在 2026 年

```
模型與 harness 能力提升
        ↓
agent 任務從「分鐘級」變成「小時到數天級」
        ↓
「長時間等待」的比例上升 → 閒置成本與狀態保存成為主要矛盾
        ↓
既有抽象（微服務／batch）的錯配被放大
        ↓
需要一層專為 agent 設計的執行與編排層
```

官方敘事：「As models and harnesses improve, agents are taking on increasingly complex tasks that can run for hours or even days.」

---

## 3. 這個技術是如何解決該問題的？

### 3.1 整體架構

AX 分兩層：**AX 本身是宣告式控制平面；實際的 sandbox 執行外包給 Agent Substrate。**

```
                          ax apply -f task.yaml
                                    │
                                    ▼
                              ax-server
                        (無狀態 gRPC API :8080 + /healthz)
                                    │
                         寫入 Task Hash ＋ 發布 event
                                    │
                                    ▼
                                  Redis
                    (Task Hashes ＋ Event Streams ＋ PubSub)
                                    │
                          XREADGROUP（Redis Streams 當工作佇列）
                                    │
                                    ▼
                            ax-controller
                     (可水平擴充的 reconciliation workers)
                                    │
                          gRPC（Control API）
                                    │
                                    ▼
                         Agent Substrate（ate-system）
                    ┌──────────────────────────────┐
                    │ Atespace 建置                 │
                    │ Actor 建立與啟用              │
                    │ Worker 指派                   │
                    └──────────────────────────────┘
```

| 元件 | 角色 |
|---|---|
| `ax` | CLI。apply 宣告、檢視與 watch 資源、tunnel 進叢集 |
| `ax-server` | 無狀態 gRPC API（:8080）。驗證 manifest、寫入 Redis、發布事件 |
| `ax-controller` | Reconciliation worker。消費 Redis stream，在 Substrate 上建 atespace 與 actor，把 task 推向期望狀態。加 replica 即擴充 |
| `ax-task-runner` | 每個 task 容器內的 entrypoint（PID 1）。建置 workspace、提供 metadata、執行 agent 命令 |

**關鍵設計選擇：狀態不存 etcd 而存 Redis。** DESIGN.md 明寫理由：把百萬級短命 task 當 CRD 會把 etcd 推過舒適區（單數字 GB 儲存上限、寫入速率瓶頸、控制平面退化）。以 Redis Streams 當 API server 與 controller 之間的工作佇列。

### 3.2 核心資源模型：三個 primitive

repo 實作的 kind 為 **Task／Workspace／Model**（`ax.io/v1alpha1`）。

| Primitive | 解決哪個子問題 | 做什麼 |
|---|---|---|
| **Task** | P1 | 最小隔離執行單位。宣告 container image、command、cpu/memory requests 與 limits、env、要綁的 workspace。刻意做小：agent 不是一個跑完即結束的 process，AX 不模型化那個形狀，只給一個「便宜地建立、隔離、suspend、丟棄」的單位，讓 agent 依需要組合多個 |
| **Workspace** | P3 | 宣告式環境。宣告一次、被多個 task 綁定，runner 在命令啟動前把 git repo clone 到 workspace 路徑、掛 MCP server／registry、materialize skill registry。綁定可帶 `goal`：首開機時把該自然語言敘述交給一個 Antigravity agent 完成安裝 toolchain 等收尾 |
| **Model** | 憑證與模型設定的集中 | provider + model id + provider 參數（如 max_tokens）+ 指向 K8s Secret 的憑證引用。設定存在一處，換 key／釘版本／調參都只需一次 `ax apply` |

YAML 形狀（官方範例，3 個 kind 一檔）：

```yaml
apiVersion: ax.io/v1alpha1
kind: Workspace
metadata: {name: golang}
spec:
  git:
    - repo: https://github.com/golang/go.git
      branch: "my-fix"
---
apiVersion: ax.io/v1alpha1
kind: Task
metadata: {name: test}
spec:
  workspaces:
    - name: golang
      goal: "Ensure that Go tool chain is available and is built from source"
  debug: true   # 開了才有 guest service，才能 ax ssh
---
apiVersion: ax.io/v1alpha1
kind: Model
metadata: {name: default-model}
spec:
  provider: google
  model: gemini-3.8-flash
  secretKey: {name: gemini-api-secret, key: GEMINI_API_KEY}
```

### 3.3 如何解 P2（閒置資源）：suspend／resume

AX 把「暫停與續跑」做成 Task 生命週期的一等操作：

- `ax suspend task`：checkpoint actor 狀態並暫停；`Ready` condition 設為 False（reason `TaskSuspended`）。
- `ax resume task`：續跑，`Ready` 復原。
- 執行層的快照與 sub-500ms 恢復由 Agent Substrate 提供，AX 負責把它接進 Task 生命週期。

狀態語意：`status.phase` 為單字摘要（Running／Suspended／Failed／Terminating）；細節在 conditions（`WorkspaceReady`＝所有 workspace 建置完成且此後維持 True；`Ready`＝唯一應等待的 condition）。

### 3.4 如何解 P1（隔離與邊界）：sandbox 與網路

**sandbox 內部（`docs/sandbox.md`）**：每個 task 容器以 `ax-task-runner` 為 PID 1，開機流程為：

1. 載入 Task 與所有綁定的 Workspace spec。
2. 在 :80 起 metadata 與 guest-management daemon（HTTP/1.1 + h2c）。
3. 首次執行時依綁定順序建置各 workspace（clone git、設 skills path；有 goal 則交給 Antigravity agent，預設 10 分鐘、需容器內有 `GEMINI_API_KEY`）。
4. 以第一個 workspace 為工作目錄，啟動 `spec.command` 並監督。

metadata server 端點：

| 端點 | 方法 | 回傳 | 說明 |
|---|---|---|---|
| `/healthz` | GET | text/plain | liveness，永遠 200 |
| `/readyz` | GET | text/plain | readiness，初始化中 503、完成後 200 |
| `/metadata/v1alpha1/ax/task` | GET | application/yaml | Task 啟動設定（不含 status） |
| `/metadata/v1alpha1/ax/workspaces` | GET | application/yaml | 所有綁定的 Workspace（多文件流） |

guest service（process service 與 filesystem service，即 `ax ssh` 的底層）**預設關閉**，只有 `spec.debug: true` 才開，因為它允許任意 process 執行與檔案存取。

**網路（`docs/networking.md`）**：task 沒有自己的 Service 或 Ingress。所有請求經過 Substrate 的 `atenet-router`，讀單一 header `ate-target-actor: <atespace>/<task>`，解析 actor 所在的 worker，若已 suspend 則先 resume 再 proxy。

```bash
curl -H "ate-target-actor: default/task123" \
  http://atenet-router.ate-system.svc.cluster.local/metadata/v1alpha1/ax/task
```

### 3.5 底層依賴：Agent Substrate（AX 能力的實際來源）

AX **不是自足的**。它排程的每個 task 都是 Substrate 上的 sandboxed actor，部署前 Substrate 必須已在叢集（namespace `ate-system`，Control API 在 `api.ate-system.svc.cluster.local:443`）。

Substrate 提供的能力，也就是 AX 對外宣稱的密度與恢復能力：

| Substrate 能力 | 數值／機制 |
|---|---|
| 高密度 | 比標準 container runtime 高 10x；把大量 actor 多工到少量 ready worker（靠 agent 多數時間閒置） |
| 快速恢復 | sub-500ms resume；500+ suspend/resume activations 每秒 |
| 隔離 | microVM 與 gVisor，原生 zero-trust kernel 與網路隔離 |
| 與 K8s 的關係 | 用 K8s 做基礎設施供給與 worker 生命週期（Pods），但另建最小控制平面以繞過 K8s 對高頻呼叫的限制 |
| framework agnostic | 管理標準 OCI 容器，可承載 ADK／LangChain／Claude Code／Codex／Antigravity／MCP |

### 3.6 與 Kubernetes 的關係（校正影片觀點）

| 面向 | K8s | AX |
|---|---|---|
| 宣告式 YAML manifest | 是 | 是（`ax.io/v1alpha1`） |
| CLI 動詞 | kubectl apply/get/watch/describe | ax apply/get/watch/describe/ssh/suspend/resume |
| 資源 kind | 數十種 | 3 種（Task／Workspace／Model） |
| 狀態存放 | etcd | **Redis**（明言避開 etcd 限制） |
| 執行單位 | Pod／container | Substrate actor |
| 工作佇列 | controller 直讀 API server | Redis Streams + XREADGROUP |
| 執行層 | 內含 | **外包給 Substrate** |

README 的自我對照句為 "If you have used Kubernetes, `ax` will feel similar."。形式層「像」，狀態層與執行層「不同」。

### 3.7 成熟度與發展方向

| 項目 | 現況 |
|---|---|
| 版本 | v0.3.1（2026-09-25）；README 明載「stable release 前會有 major breaking changes」 |
| 熱度 | 11,655 stars／558 forks／48 open issues |
| 維護主體 | 首貢獻者 `rakyll`（Jaana Dogan，480 次 commit），另有 Google 員工 |
| roadmap 五大項 | ① 穩定核心 spec（含新增 Sandbox／SandboxConfig）② Actor 架構（遷移到新 Actor API、把 workspace 建置拆成獨立 actor、最小權限政策、閒置偵測自動 suspend、stateful task branching）③ agentic environment（動態策展 workspace、可自訂 agent runtime）④ 網路／身分／治理／可觀測（**SPIFFE 身分與 mTLS**、Google 平台治理要求、OTel telemetry 與 trajectory 收集）⑤ 文件 |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案與 DA 表

以下四個方案與 AX 解同一個「agent 工作負載如何執行與編排」問題，切入點不同。

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **K8s 原生（Job／CronJob／自寫 CRD + controller）** | 以 K8s 既有抽象表達 agent 任務：Job 跑 task、Pod 當隔離單位、NetworkPolicy 做網路限制、HPA／KEDA 做擴縮、etcd 存狀態 | 已有 K8s 叢集；接受以 etcd 承載 task 狀態；自建 suspend/resume 與 checkpoint | 百萬級短命 task 會撞 etcd 儲存上限與寫入瓶頸（AX DESIGN.md 明列此為其不用 CRD 的理由）；無原生 sub-second 狀態保存／恢復；閒置 sandbox 成本高 | 對「數千個長命服務」最佳化；對長程大量 agent 任務的成本與延遲不成立 |
| **Agent Substrate 直用** | 直接使用 Substrate 的 actor／worker 模型與 Control API 執行 agent；自行提供 task 宣告、workspace 準備、model 設定 | 能直接操作 Substrate Control API；自行承擔 agentic 抽象層 | 喪失 AX 的宣告式 manifest、workspace 自動化、Model 集中管理；Substrate 自身為 pre-1.0、低 opinion 系統 | 直接取得高密度與 sub-second resume；多一層自建維護負擔 |
| **kagent（CNCF Sandbox）** | K8s-native agent framework，以 CRD 宣告 agent；底層同樣用 Agent Substrate 跑 sandboxed、stateful agent | 使用 K8s 與 kagent 生態；接受其 agent 抽象與框架慣例 | 與 AX 依賴同一底層但抽象層不同；agent 的宣告與生命週期受框架綁定 | 適合已深度使用 K8s、且要的是 agent 管理框架而非低階執行編排者 |
| **應用層 workflow 框架（LangGraph／Temporal／ADK／A2A 一類）** | 在單一應用程式內以圖或狀態機編排 agent 步驟；Temporal 提供 durable execution；A2A 提供 agent 間協定 | 問題屬「單一應用內的 agent 流程」而非「叢集層大量 workload 編排」；另備隔離與資源控制 | 不解決 sandbox 隔離、密度、sub-second resume；多租戶與資源上限需另行實作 | 對應用內確定性 workflow 有效；對叢集層 fleet 編排無效 |

**切入點差異一句話**：K8s 原生是「用既有編排器硬做」；Substrate 直用是「只買執行層」；kagent 是「買 agent 框架」；應用層框架是「編排單一應用內部的步驟」。AX 的位置是「買 agent 專用的宣告式控制平面，並把執行層綁定 Substrate」。

### 4.2 對照第二大腦（FATESAIKOU/MyBrain）

> 鏡像 `d2aeff7`（2026-09-26 同步）。以下每則標信任層級；`draft` 者為未經使用者 review 的 AI 草稿。**這些是他的判定，不是本報告的判定。**

#### 4.2.1 直接命中：他手上的座標

| MyBrain 檔案與判定 | 信任層級 | 與 AX 的關係 |
|---|---|---|
| [MyLinuxPool](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/MyLinuxPool.md)：「把三台各自為政的機器變成可託管叢集」；明確邊界為「**沒有排程、沒有佇列、沒有自動擴縮**。它是讓機器可達的基礎設施，不是工作調度器」；worker 無狀態、provider 之間不互連、沒有多租戶 | `draft`，`by: ai:claude-opus-5`（日誌作者 `human:fatesaikou`，09-15／09-25／09-26 證實為當期實際推進） | **同問題域的自建版**。AX 補上的正是他刻意標為「沒有」的四項：排程、佇列、自動擴縮、多租戶隔離 |
| [AIContainer](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/靈感/AIContainer.md)：「一台 Linux ＋ CodeAgent 的完整作業環境」；三件事為遠端機器啟停、永續連線、與入口的非同步通訊 | `draft`，`by: claude-code/opus-5.5` | AIContainer 的「永續連線」與 AX 的 durable execution／connection recovery 解同題；AIContainer 明言「必須是一台電腦，不是被包成幾個 tool 的受限沙箱」，與 AX 的 sandbox 定位方向相反 |
| [個人 AiAgent 入口](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/%E5%80%8B%E4%BA%BA%20AiAgent%20%E5%85%A5%E5%8F%A3.md)：2026-09-06 **放棄大一統架構**，拆成「簡單問答」與「複雜任務」兩個互不為前提的東西 | `draft`，`by: claude-code/opus-5.5` | 他的架構決策是「拆」，AX 的形狀是「以三個 primitive 統管所有 agent workload」 |

#### 4.2.2 判定過的替代方案

| MyBrain 判定 | 信任層級 | 內容 |
|---|---|---|
| [Openship](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Openship.md)：**不採用** | `stable`，`generated.by: opencode/deepseek-v4-pro`，`verified by human:fatesaikou` 2026-08-09 → **較高信任** | 理由：「目前用例只有一台低價 VPS 且沒打算在上面跑服務，為此導入外部 ControlPanelService 過重」 |
| [munder-difflin](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/munder-difflin.md)：**不採用** | `draft`，`by: process:learn-gh-agent` | 三個理由：基於 GUI 且不想被限制 UI；引入的是一種固定拓樸，實際需要可自由切換的拓樸；「還太早而且包太多」 |
| [KEDA／Linkerd／Istio](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/靈感/GKE%20%E6%93%B4%E5%BC%B5%E5%AD%B8%E7%BF%92.md)：判「單獨一個底層元件學不到東西」 | `draft`，`by: claude-code/opus-5` | 能學的是把真實負載完整跑通的動線（容器化→部署→對外→憑證），故有 GKE 擴張學習（低優先） |
| [gVisor / microVM](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/gVisor%20-%20microVM.md)：**不採用**，但**理解已達成** | `stable`，`generated.by: human:fatesaikou` → **他本人的結論** | 「Cloud 都有自己解決方案，知道就好，不會進 workflow」；留下隔離技術光譜與場景決策樹。**AX／Substrate 的隔離走的就是 gVisor／microVM 這條線** |
| [Ansible + k3s](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/Ansible.md)：理解已達成 | `stable`，`generated.by: human:fatesaikou` | 已建過 local Ansible + k3s 可測試環境，理解 inventory／playbook／role 與 k8s 模組冪等性 |

**判定總表中的其他相關否決**（皆為 `draft`，`by: ollama-cloud/deepseek-v4-flash`，未經他 review）：Buzz（規模過大、個人使用不必要）、macro（太重型）、Semantica（企業稽核場景、對個人過度重型）。此三者的否決形狀與 AX 的企業級定位同構。

**查不到的部分（明寫）**：第二大腦**沒有** AX／Agent Executor／Open Agentic Orchestration 的任何紀錄（0 命中）；**沒有** Agent Substrate、kagent、LangGraph、Temporal、Airflow、Nomad、E2B 的判定。§4.1 的四個替代方案中，只有「K8s 原生」與「應用層框架」在第二大腦有鄰近座標，其餘三個屬本報告依 repo 事實新列。

#### 4.2.3 與既有判定的衝突（對照最有價值處）

| # | 衝突 | 具體內容 |
|---|---|---|
| C1 | **「外部控制平面過重」vs AX 是更大的控制平面** | Openship 因「為一台 VPS 導入外部控制平面過重」被拒（`stable`，經他 verify）。AX 是叢集級控制平面，規模更大。**但兩者問題域不同**：Openship 管理的是「部署服務」，AX 管理的是「執行 agent workload」；AX 真正對照的是他自建的 MyLinuxPool，而非 Openship。衝突成立於「為個人導入」的判斷上，不成立於「技術定位」上 |
| C2 | **「引入一種固定拓樸」vs AX 的統一 primitive** | munder-difflin 因「引入一種拓樸，而實際需要能自由切換的拓樸」被拒（`draft`）。AX 同樣以三個 primitive 固定了 agent 的執行拓樸。**差異**：munder-difflin 的 GUI 理由不適用於 AX（AX 是 headless YAML），但其「固定拓樸」與「pre-1.0 還太早」的結構相同 |
| C3 | **MVP→Feature 唯一閘門** | [技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md)（`draft`，`by: claude-code/opus-5`，內含他原話）：「要真的能影響到我個人 workflow 我才會立刻進 Feature」。AX 需 K8s ＋ Substrate ＋ Go ＋ `ko` ＋ container registry 才能起步。依此準則，AX 停在 Judge（理解）階段，不進 Feature |
| C4 | **「單獨一個底層元件學不到東西」** | GKE 擴張學習的判準（`draft`）指出：能學的是把真實負載完整跑通的動線。AX 不是單一底層元件，而是該動線的極致版（含部署與憑證）。**但**他的學習目的是「打通一次動線」，AX 的設計目標是「承載 billions」，規模與目的落差大 |

#### 4.2.4 與 AX 方向一致的既有準則（非衝突，值得指出）

[技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md) 第五條「AI agent 的信任邊界：約束在 harness，不在權限」的例外（`draft`，`claude-code/opus-5`）明確寫道：

> 給 AI 一台完整的 linux 機器時，指令黑名單擋不住。**把邊界挪到真的能承擔它的地方：該機器上的執行身分、憑證有無、網路規則。那是機器配置的事。**

AX 的設計方向與此一致：

| 他的準則 | AX 對應機制 | 現況 |
|---|---|---|
| 邊界挪到「執行身分」 | roadmap 的 SPIFFE ID／X.509-SVID ＋ 零信任 mTLS | **未實作**（roadmap 第 4 項） |
| 邊界挪到「憑證有無」 | Model 的 credentials 存 K8s Secret；官網 Gateway 宣告「注入憑證」 | Secret 機制已實作；Gateway 未實作 |
| 邊界挪到「網路規則」 | 官網 Gateway 的 allowlist hosts+ports；Substrate 原生網路隔離 | Gateway 未實作；Substrate 隔離已存在 |
| 能力以「不存在」實現，而非黑名單 | Substrate 以 gVisor／microVM＋zero-trust 隔離，非指令黑名單 | 已存在 |

同時，[統一的兩端稅](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/統一的兩端稅.md)（`draft`，`claude-code/opus-5`）的判準為：「先問這兩個是同一件事的不同實作，還是不同的事」。AX 把互動式 coding、長命 agent server、Jupyter、無頭瀏覽器測試全部收進同一組 Task／Workspace／Model。依此準則，需先回答這些 workload 是否為「同一件事」；若是不同的事，統一介面裝不下它們各自真正需要的控制粒度。

### 4.3 小結（不評論優劣，僅定位）

| 若使用者的問題是… | 對應的切入層 |
|---|---|
| 「我要在叢集上跑大量長程 agent，且要規模化與閒置回收」 | AX ＋ Agent Substrate |
| 「我只要執行層的密度與 resume，宣告層自己寫」 | Agent Substrate 直用 |
| 「我要在 K8s 上管理 agent 的生命週期與框架整合」 | kagent |
| 「我要編排單一應用內的 agent 步驟」 | 應用層框架（LangGraph／Temporal／ADK／A2A） |
| 「我要讓手上的三台機器可達、可跑 worker」 | 他自己的 MyLinuxPool（刻意無排程、無佇列） |

---

## 附錄 A：影片觀點的事實校正

| 影片觀點 | 校正後的事實 | 依據 |
|---|---|---|
| 全名 Open Agentic Orchestration | repo 自我定位為 *declarative orchestrator*；產品名 Agent Executor。官網未使用 Open Agentic Orchestration 作為正式全名 | README／官網 |
| 以 K8s 為類比、後來變成標準 | README 原句為 "If you have used Kubernetes, ax will feel similar."；**狀態層不使用 etcd**，執行層外包 Substrate | README／DESIGN.md |
| YAML 宣告 task／workspace／gateway／model | repo 實作 **3 個 kind**：Task／Workspace／Model。**Gateway 不在實作中**——`pkg/apis/v1alpha1/types.go` 只定義 `KindTask`／`KindWorkspace`／`KindModel`；`ax.proto` 的 RPC 只有 Task／Workspace／Model；repo code search `Gateway` 命中 0；`docs/concepts.md` 無 Gateway。官網列為第 4 primitive，屬官網藍圖。判定依據分支：`main`，2026-09-26 | repo／官網 |
| 企業級、起步較重 | 成立。pre-1.0（v0.3.1）；部署需 K8s ＋ Agent Substrate ＋ Go ＋ `ko` ＋ registry；roadmap 明列治理與穩定化為未完成項 | README／roadmap |

## 附錄 B：關鍵事實索引

| 事實 | 值 | 來源 |
|---|---|---|
| repo | `google/ax` | GitHub |
| 官網 | `agentexecutor.io` | metadata |
| 語言／授權 | Go／Apache-2.0 | metadata |
| stars／forks／open issues | 11,655／558／48 | metadata（2026-09-26） |
| 建立／最新 push | 2026-03-30／2026-09-26 | metadata |
| 最新 release | v0.3.1（2026-09-25） | releases |
| 實作 kind 數 | 3（Task／Workspace／Model） | types.go／ax.proto |
| 底層依賴 | Agent Substrate（3,814 stars，Apache-2.0，建於 2026-05-13） | Substrate repo |
| 官方部落格 | 2026-05-20，Jaana Dogan（rakyll）／Ethan Bao | cloud.google.com |
