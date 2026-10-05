# 290_R2_step2-plan_C1.md

## 狀況理解

R2 追問輪，三個子問題（Q1 與他的 Ai 公司是否同問題同解法／Q2 穩定性、維護者、規模／Q3 若為小團隊則該吸收哪些概念）。R1 已完成 metadata＋主要文件（README、architecture、2 ADR、expert-teams、agent-delegation、4 衛星 repo），不得重做。

C1 為本輪第一個 sub-step，聚焦「R1 未量化、且 Q1／Q3 對照所需的一手事實」：

| 需求 | R1 是否已答 | C1 任務 |
|---|---|---|
| Q2 維護者身分、規模、成熟度 | **未答**（R1 只記 48 頁 contributors） | 量化維護者集中度、社群規模、治理文件、release/CI 節奏 |
| Q1 解法對照 | 部分（架構已記） | 補「單進程 vs 拆開」的可對照事實：隔離層級、狀態外部化、harness 約束 |
| Q3 可吸收概念 | 部分（機制已記） | 以 Harness 五問為量尺重新標定可移植機制與負面教訓 |
| Q2「新創小團隊」前提 | 未證 | 查證是否為騰訊官方團隊 |

MyBrain 對照留 C2；C1 只做官方／repo 一手事實。

## 執行的動作與結果

先跑 `mybrain-read`（鏡像 `/tmp/mybrain` @ c3319a0），僅取 Q1／Q3 對照錨點（Ai公司架構、技術取捨準則、統一的兩端稅），不重複 R1 的替代方案盤點。

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh api repos/TencentCloud/Octop` | 取即時 metadata | Q2 規模 | 6,992★／864 forks／663 open／59 watchers／MIT／Python；created 2026-07-08；pushed 2026-10-05；size 32.3MB；`organization=TencentCloud` |
| `gh api .../contributors?anon` | 量化維護者 | Q2 集中度 | 48 名 contributors（per_page=1 共 48 頁）；top100 總貢獻 637 |
| `gh api users/jubaoliang` | 查頭號維護者 | Q2 身分 | Tencent、Beijing、followers 27、公開 repo 6；SECURITY.md 指定其 gmail 為窗口 |
| `gh api .../releases` | 取版本節奏 | Q2 成熟度 | v0.9.35→v1.0.0(09-14)→v1.0.2b1..b6；最新 v1.0.2b6 (10-04) |
| `gh api .../stats/commit_activity`＋`participation` | 量化活躍度 | Q2 續航 | 近 12 週 29/34/22/59/31/57/76/56/55/94/8/1（末週資料未滿一週） |
| `gh api .../git/trees?recursive=1` | 數測試檔 | Q2 工程紀律 | 481 個 `tests/**/test_*.py` |
| `gh api .../contents/.github/workflows` | 查 CI | Q2 品質閘 | 9 條：ci、codeql、release、docker-publish、auto-tag、fnos-build、desktop、sync-main-to-develop、anti-spam |
| 抓 `CONTRIBUTING.md`、`SECURITY.md` | 查治理 | Q2 成熟度 | CONTRIBUTING 完整分支模型（main/develop/release/hotfix）；SECURITY 有支援政策與窗口；**無** GOVERNANCE/CODEOWNERS/MAINTAINERS |
| `gh api search/issues` | 分流追蹤量 | Q2 負載 | issue open 389／closed 180；PR open 274／closed 808 |
| `gh api .../commits?until=2026-07-10` | 定位首提交 | Q2 年齡 | first commit「first commit」jubaoliang 2026-07-09 |
| 讀 `src/` 隔離與 agent 機制（R1 已記，重標） | Q1／Q3 對照 | 抽取錨點 | `agents.user_id` row 級隔離；每 agent 一條 `HarnessAgentRuntime`；tools_disabled 減法 |

**維護者集中度（Q2 核心）**

| 帳號 | 貢獻 | 佔比（637） |
|---|---|---|
| jubaoliang | 171 | 26.8% |
| jubaoliang-tencent | 169 | 26.5% |
| liukewia | 55 | 8.6% |
| huangcheng | 35 | 5.5% |
| Pandakingxbc | 27 | 4.2% |
| chujieHong | 25 | 3.9% |
| 其餘 42 人 | 合計 155 | 24.3% |

- jubaoliang ＋ jubaoliang-tencent（同一人之雙帳號，email 同一）合計 **340/637 ≈ 53.4%**。
- top5 帳號合計 482/637 ≈ 75.7%。
- 非騰訊外部貢獻者（如 louisss1016、Bluuok、Lesereingrape）多為單檔小修（config/備份/文件），尚未進入核心。

**成熟度訊號（Q2）**

| 面向 | 事實 | 判讀 |
|---|---|---|
| 組織 | `TencentCloud` 官方 org，非新創小團隊 | **修正使用者前提**：維護者是騰訊雲官方 |
| 年齡 | 2026-07-08 建立、07-09 首提交 | 約 3 個月，極年輕 |
| Bus factor | 頭號帳號佔 53%、top5 佔 76% | **實質集中於少數人**，與「官方團隊」的印象不一致 |
| 版本凍結 | 0.9.35→1.0.0→1.0.2b6，多在 beta | API／設計未凍結；AgentTeams 標 Beta、mobile 封閉測試 |
| 品質閘 | 481 測試檔、9 條 workflow（含 CodeQL）、make all 為 ship bar | 工程紀律高於同期專案 |
| 待辦堆積 | open 663（issue 389＋PR 274） | 吞吐高但消化不及，維護負載重 |
| 治理 | 有 CONTRIBUTING／SECURITY；無 GOVERNANCE／CODEOWNERS／MAINTAINERS | 有流程、無明文決策權歸屬 |

**Q1／Q3 對照錨點（僅標定，論證留 Step3）**

| 錨點 | Octop 事實 | 對應他 MyBrain |
|---|---|---|
| 整合形態 | 單一 Python 進程、四 surface 共用一 runtime、預設 SQLite | Ai公司架構：幾個互不為前提的東西；統一的兩端稅判準 |
| 隔離層級 | JWT＋`agents.user_id` row 級；全進程單一 AgentManager | AiStorage 狀態外部化、AiContainer worker 拋棄式 |
| 工具約束 | 主持人 `init_workspace=False`＋`tools_disabled` 減法 | 技術取捨準則：約束放 harness |
| 狀態外部化 | 房＝主持人 thread_id，成員 checkpoint＝`主thread~成員id` | Ai公司架構原則四「狀態在執行體之外」 |
| 並發 | inbox：同成員串行、不同成員並行；非同步 ask_agent＋回叫 | 可借 AiContainer worker 編排 |
| 安全 | tool approval／shell guardrails／PII redaction | Harness 五問 permission／verify |
| 互操作性 | ACP 雙向（inbound ／outbound 帶 permission gate） | harness 接口與 CodeAgent 委派 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Q2 維護者身分 | org、head 帳號 profile、SECURITY 窗口 | 騰訊雲官方，但實質集中於 jubaoliang |
| Q2 規模量化 | 48 contributors／637 貢獻／top5 76% | 完成 |
| Q2 穩定性 | release 節奏、commit activity、CI、open 堆積 | 高頻迭代但不凍結、待辦堆積 |
| Q1 對照錨點 | 整合／隔離／約束／狀態／並發／安全／互操作 | 七項齊備，可交 Step3 論證 |
| Q3 抽取量尺 | Harness 五問＋技術取捨準則 | 已就緒（MyBrain @ c3319a0） |
| R1 不重複 | 未重抓 README/arch/ADR | 符合 |
| metadata 時差 | 6,992★ vs R1 6,858★ vs PR 6,845★ | 同日續漲，出報告時再複核 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| C1 範圍 | 重做 R1 調研／增量補 Q2 事實＋Q1/Q3 錨點 | 只做增量 | R2 意圖不同，重做浪費 |
| 維護者判定 | 只記 org 名／量化到人 | 量化到帳號與佔比 | Q2 問「誰在維護、規模」，須一手數字 |
| 「小團隊」前提 | 直接採信／查證 | 查證並修正為官方團隊＋高集中 | 事實與前提不符須明示，影響 Q3 |
| Q3 是否等同「該採用」 | 給採用建議／只列可抽取與教訓 | 只列抽取清單與負面教訓 | 準則：Reject≠沒價值，理解優先 |
| 衛星／替代方案 | 再查／沿用 R1 | 沿用 R1 | R1 已充足，避免重工 |
| activity 末週低值 | 判為衰退／標記資料未滿 | 標記未滿一週 | API 週資料末筆常不完整，避免誤判 |

## 交接給 C2

- Q1 論證：以「統一的兩端稅」判準逐項比對 Octop 單進程與 Ai公司架構，判定「同問題／同解法」各到哪一層。
- Q3 抽取清單：以 Harness 五問標定可移植機制（工具減法、狀態外部化、inbox 並發、permission gate、ACP）與負面教訓（單進程垂直擴展限制、待辦堆積）。
- Q2 結論素材：官方團隊、3 個月、頭號維護者佔 53%、beta 未凍結、工程紀律高、open 663。
- 待查證：jubaoliang 是否即專案負責人（僅能由 commit／SECURITY 推斷，無 MAINTAINERS 明載）。
