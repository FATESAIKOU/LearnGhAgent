# pstack — 把 AI coding agent 的產出紀律化的 Agent Skills 工作流

> 調研標的：[`backnotprop/pstack`](https://github.com/backnotprop/pstack)，`cursor/plugins/pstack` 的 standalone mirror。作者 Lauren Tan（poteto），MIT。
> 資料來源：repo README、`MIRROR.md`、`plugin.json`、`skills/poteto-mode/SKILL.md`、23 個 playbook、`docs/guide/`、`agents/`、GitHub API、skills.sh。抓取時間 2026-10-18。
> 版本：mirror `0.15.25`；上游 `cursor/plugins/pstack` 同日為 `0.15.26`。

---

## 1. 這個技術解決什麼問題？

### 1.1 一句話

pstack 解決的具體問題是：**AI coding agent 能以高吞吐產生看起來合理的程式碼與說明，但產出缺少可執行證據與工程紀律，於是人成為驗證瓶頸，多 agent 並行也無法被信任。**

它把這個問題拆成七個子問題：「寫太多」「沒驗證」「等人審」「不能並行」「單模型盲點」「重複犯錯」「回報膨脹」，並用一組純檔案的 Agent Skills 回應。

### 1.2 被解決的子問題

| 子問題 | 具體表現 | pstack 的對應 |
|---|---|---|
| 產出膨脹與過度設計 | 新增抽象層、重複驗證器、相容層、無必要註解，diff 比需求大 | `principle-laziness-protocol`、`principle-subtract-before-you-add`、`no-comments`、`unslop` |
| 未驗證就宣告完成 | 以「it compiles」、自我回報、代理指標取代真實產物檢查 | `principle-prove-it-works`、`tdd`、`blast-radius`、`benchmark-checklist` |
| 驗證依賴人 | 每一步都要人看，agent 無法自己證明做對了 | `principle-never-block-on-the-human`、`create-verification-skill`、autonomy 規則 |
| 多 agent 並行不安全 | 多個 agent 改同一狀態、審查量跟不上、衝突與重工 | worktree／cloud 隔離、`swarm`、`arena`、獨立 verdict、`principle-guard-the-context-window` |
| 單模型盲點 | 同一個模型 review 自己的產出，容易同意自己 | `interrogate`、`arena` 的跨模型 panel 與 cross-judge |
| 重複犯錯 | 每次被糾正只改當次，下一次 agent 再犯 | `correct`、`reflect`、`principle-encode-lessons-in-structure` |
| 回報與文件膨脹 | AI 腔、長句、emoji、模糊結論、沒有證據的斷言 | `unslop` 的 28 條實際規則（編號到 33，含跳號）、`technical-writing`、`poteto-mode` 的 Writing the reply |

### 1.3 問題描述中的模糊之處

| 模糊點 | 說明 |
|---|---|
| 「quality」沒有量測定義 | README 說「write less, but higher quality code」，但 repo 沒有 LOC 前後對照、缺陷率、review 時間、task 成功率等 benchmark。品質是作者的主張與使用經驗，不是量測結果。 |
| 「write less」沒有基線 | 沒有說明相對哪一種 agent 預設行為、少多少行、少多少 token。laziness protocol 是規則，不是已驗證的壓縮率。 |
| 「turns Cursor into a real engineering team」是定位語 | 這是產品定位，不是可驗證的組織效果。repo 沒有團隊導入案例或前後比較。 |
| 假設瓶頸是紀律，不是能力 | pstack 的原則是「如何做工程」。若 agent 缺少的是領域知識、模型推理能力或工具權限，原則是補不上的。 |
| 假設 harness 具備 subagent 與多模型 | 多個 skill 依賴 `Task`／subagent、跨模型呼叫、雲端 worker。沒有這些能力的 harness 會退化為單 agent 依序執行，效果與成本結構都改變。 |
| 作者的環境是 Cursor 內部 | 預設模型是 `grok-4.7-xhigh-fast` 與 `claude-opus-5-5-xhigh`。外部使用者未必有同樣的模型存取與額度。 |

### 1.4 邊界

pstack 不是程式庫、不是執行引擎、不是模型。它是**一組 Markdown 檔構成的 Agent Skills 與路由規則**。它改變的是 agent 的工作方式，不改變模型本身的能力。這一點決定了 pstack 的效果上限：原則能約束行為，不能補足知識。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 repo 明確提到的背景

| 背景 | repo 的說法 | 出處 |
|---|---|---|
| AI 產出過量且品質不足 | 「there's a growing sense that ai writes too much slop code. i agree.」 | README |
| 吞吐量不是目標 | 「throughput without quality is not a goal i aspire to. if you want to go fast, go deep first.」 | README |
| 驗證是最慢的一步 | 「Verification is the slowest step in most agent work, because it's the step that usually waits on a human.」 | `docs/guide/06-verify-and-ship.md` |
| 不能自我驗證的 agent 把工作退回給人 | 「An agent that can't [check its own work] hands every result back to you to check by hand.」 | `docs/guide/01-setup.md` |
| 信任是並行的前提 | 「when you can go deep on one agent and trust it to write good, verifiable code, you can truly parallelize with confidence.」 | README |
| 每個前沿模型各有強弱 | 「every frontier model has its strengths and weaknesses. use any model with pstack.」 | README |
| 技能需要跨 harness 流通 | pstack 是 plain Agent Skills，`skills` CLI 可裝進 Claude Code、Codex、Pi、Cursor、OpenCode | README 的 mirror 段 |

### 2.2 通用技術背景（repo 未明說，屬一般技術脈絡）

| 背景 | 說明 | 與 pstack 的關聯 |
|---|---|---|
| LLM 的預設輸出傾向 | 下一個 token 的合理性、人類偏好訓練帶來的順從傾向，會讓 agent 傾向給出「看起來完成」的答案，而不是「已驗證完成」的答案 | pstack 用 defensive rules 與 executable verification 對抗這個傾向 |
| 長任務的 context 壓力 | 長對話中，早期約束會被淹沒，agent 會用摘要與推測取代原始證據 | `guard-the-context-window` 把大量讀取丟給 subagent，主線只留摘要 |
| 程式碼是負債，審查容量有限 | 變更量增加時，review 容量不會等比例增加；未審查的變更會累積成風險 | pstack 把「減少 diff」與「可執行證據」放在同一條流程 |
| Prompt 工程的演進 | 從單一 system prompt，到 repo 規則檔（AGENTS.md／CLAUDE.md），再到可組合的 Agent Skills 與 plugin | pstack 是「skill 組合 + 路由 + 驗證」這一代的產物 |
| Agent Skills 標準化 | `agentskills.io` 定義 `skills/<name>/SKILL.md` 的目錄格式；plugin manifest 讓技能可打包發布 | pstack 用同一格式，因此能跨 harness 安裝 |
| 多模型與成本分層 | 不同模型在代碼、判斷、寫作上的強弱不同；高價模型適合判斷與約束設計，低價模型適合機械工作 | pstack 的 `setup-pstack` 把角色對應到模型，預設 code 用 grok、judgment／prose 用 opus |

### 2.3 問題的結構

```text
AI 生成速度上升
        │
        ▼
變更量上升 ──► 人工審查容量固定 ──► 未驗證變更累積
        │                                   │
        └────────► 信任不足 ◄───────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
   只能單 agent 深度使用      直接並行後人工補審
   （吞吐量受限）              （風險與重工上升）
```

這個結構說明了 pstack 的兩個賣點為什麼放在一起：**深度**（單 agent 的嚴謹度）與**並行**（多 agent 的信任）。兩者不是兩個獨立功能，而是同一個「驗證能力」的兩個結果。

### 2.4 既有做法為什麼不足

| 做法 | 不足 |
|---|---|
| 單檔 system prompt／規則檔 | 所有規則常駐，無法按任務載入；沒有路由、沒有驗證、沒有跨模型檢查 |
| 人工逐步 review | 審查容量固定，成為瓶頸；agent 越快，人越跟不上 |
| 只看測試通過 | 測試是代理指標。pstack 的 `prove-it-works` 明確要求看真實產物，而不是「it compiles」 |
| 多 agent 直接並行 | 沒有隔離、沒有獨立判定、沒有共同契約，衝突與重工增加 |
| 單一模型自我 review | 同一個模型的盲點會重複；同意自己的判斷不構成第二意見 |
| 純 plan／spec-first | plan 與實作會漂移；pstack 的立場是「the best spec is code」，直接以可執行的程式碼與驗證為規格 |

---

## 3. 這個技術是如何解決該問題的？

### 3.1 形態與規模

| 項目 | 內容 |
|---|---|
| 形態 | 核心是純檔案化 Agent Skills：`skills/<name>/SKILL.md`；另有少量 TypeScript／Shell 輔助腳本（watch-pr、worktree-audit、orch） |
| 上游與 mirror | 上游 `cursor/plugins/pstack`；mirror `backnotprop/pstack` 保留上游內容，改寫 Cursor 專屬指令 |
| 安裝 | `npx skills add backnotprop/pstack`（skills CLI，支援 Claude Code、Codex、Pi、Cursor、OpenCode）；Cursor 原版用 `/add-plugin pstack` |
| 技能數 | 54 個 skill 目錄 = 30 個操作型 skill（含入口與 setup）+ 24 個 `principle-*` |
| 路由 | 23 個 playbook |
| subagent | `poteto-agent`（一般 delegate）、`comment-sicko`（唯讀註解審查） |
| 文件 | 10 篇 guide + README；另有 dormant 的 `automations/benny` |
| 授權與維護 | MIT；mirror 建立 2026-05-27，24 commits、1 位 contributor、0 個 release；上游 `cursor/plugins` 仍活躍。2,154 stars、155 forks、8 watchers、0 open issues |
| 採用訊號 | skills.sh 顯示 186.2K total installs；GitHub 外有 Codex／plugin 等第三方移植與再包裝 |
| Harness | Cursor 優先；mirror 針對 Claude Code、Codex、Pi、OpenCode 改寫 |

### 3.2 分層架構

```text
┌──────────────────────────────────────────────────────┐
│ 入口層   /poteto-mode（手動叫用，唯一入口）           │
│          讀 24 個 principle 索引、匹配 23 個 playbook │
├──────────────────────────────────────────────────────┤
│ 路由層   playbook steps → 個別 skill                  │
│          how / why / architect / arena / swarm        │
│          interrogate / tdd / unslop / no-comments     │
│          technical-writing / benchmark-checklist      │
├──────────────────────────────────────────────────────┤
│ 執行層   subagent：poteto-agent                       │
│          模型角色：code=grok、judgment/prose=opus     │
│          隔離：worktree / cloud / local               │
├──────────────────────────────────────────────────────┤
│ 驗證層   prove-it-works / tdd / blast-radius          │
│          benchmark-checklist / create-verification-   │
│          skill / show-me-your-work                    │
├──────────────────────────────────────────────────────┤
│ 學習層   reflect / correct / automate-me              │
│          把糾正寫回 skill、lint、type、CI             │
└──────────────────────────────────────────────────────┘
```

### 3.3 入口：`poteto-mode` 的路由

`poteto-mode` 的檔頭標記 `disable-model-invocation: true`，代表它不會被模型自動叫用，必須由使用者明確啟動。啟動後，它做五件事：

1. 讀取 24 個 principle 的索引，取得本次任務可用的判斷詞彙。
2. 把任務匹配到 23 個 playbook 之一。
3. 把該 playbook 的步驟**原文複製**進 todo list；不做的步驟保留並標 `skip: <reason>`。
4. 按步驟呼叫其他 skill；需要並行或對抗式檢查時，啟動 subagent 或跨模型 panel。
5. 回覆時指名「用了哪條 principle、它改變了哪個決策」，並用 `unslop` 的規則書寫。

虛擬碼：

```text
task = user_prompt
principles = read("skills/poteto-mode/SKILL.md").principles
playbook = match(task, 23 playbooks)
todo = copy_verbatim(playbook.steps)

for step in todo:
    skill = route(step)
    result = run(skill, context=principles)
    if step.requires_verification:
        evidence = verify_real_artifact(result)
    if step.is_irreversible:
        pause_for_human()

reply = unslop(result, cite(principles_that_changed_decision))
```

這個設計把「流程記憶」從人腦移到檔案：使用者不需要記住 23 個 playbook 的步驟，也不需要記住什麼時候該用 `blast-radius`；入口只要求一件事，說清楚目標與完成條件。

### 3.4 24 個 principle：判斷詞彙

| 群組 | 數量 | 代表 principle | 作用 |
|---|---:|---|---|
| Core | 10 | laziness-protocol、foundational-thinking、redesign-from-first-principles、attack-the-premise、subtract-before-you-add、minimize-reader-load、outcome-oriented-execution、experience-first、exhaust-the-design-space、build-the-lever | 決定「要做多少」「什麼時候重想設計」 |
| Architecture | 6 | model-the-domain、boundary-discipline、type-system-discipline、make-operations-idempotent、migrate-callers-then-delete-legacy-apis、separate-before-serializing-shared-state | 決定狀態、驗證、相容層放在哪裡 |
| Verification | 5 | prove-it-works、fix-root-causes、sequence-verifiable-units、test-behavior-not-implementation、explain-the-number | 決定「什麼算證明」 |
| Delegation | 2 | guard-the-context-window、never-block-on-the-human | 決定什麼交給 subagent、什麼時候不要問人 |
| Meta | 1 | encode-lessons-in-structure | 把重複的糾正變成 lint、type、CI、script |

兩個細節讓 principle 不只是口號：

- **只引用本次讀過的 leaf**：`poteto-mode` 要求 agent 在回覆中指名 principle 時，必須是本次 session 讀過該 principle 的 `SKILL.md`，不能憑記憶引用。
- **引用必須對應一個決策**：回覆要寫「這條 principle 改變了哪個選擇」。沒有決策對應的引用被視為 name-dropping。

這使 principle 同時是**提示詞**與**審計欄位**：它既引導行為，也讓人可以檢查 agent 是否真的用了它。

### 3.5 23 個 playbook：任務路由

| 類別 | playbook | 用途 |
|---|---|---|
| 理解 | investigation、runtime forensics、trace forensics | 唯讀問答、從 live instrumentation 診斷、從 profiling artifact 診斷 |
| 變更 | bug fix、perf、hillclimb、feature、refactoring、prototype、visual parity | 重現與修復、效能、單一指標的持續改進、新行為、行為不變的重構、便宜的原型、像素級對齊 |
| 交付 | babysit、shipping、opening a PR、worktree cleanup | 把 PR 推到 merge-ready、獨立驗證後落地、開 PR、清理 worktree |
| 自主 | autonomous run、orchestrate、autopilot-full、autopilot-stack、session pickup、pause safely、multi-phase plan | 長任務不停、專案級協調、PR queue 自動化、線性 stack、接續前一個 agent、安全暫停、多階段計畫 |
| 元 | authoring a skill、eval | 寫或改 SKILL.md、評估 skill／prompt 變更對 agent 行為的影響 |

playbook 的共同結構是**可驗證單元**：每一步結束在一個可檢查的狀態，交付時以 PR 收尾。大型或跨切面的工作會被路由到 `figure-it-out`，由它設計一個客製的 playbook；專案級、多日、多 PR 的工作路由到 `orchestrate`。

### 3.6 驗證堆疊

| 機制 | 做法 | 產出 |
|---|---|---|
| `principle-prove-it-works` | 完成後檢查真實產物：跑功能、讀實際值、看 diff；不從 proxy、自我回報、「it compiles」推論 | 可重跑的 script 與輸出 |
| `tdd` | 有便宜的本機測試路徑時，先寫失敗測試，確認失敗原因正確，再修，再跑 | failing-before／passing-after 證據 |
| `blast-radius` | 找出「這個變更安全是因為哪一個事實」，再用真實程式碼證明；證據分五級：自己說、指到 `file:line`、證明壞情況走不到、跑程式、在運行中的 app 重現 | 一個被證明或被標 `unproven` 的安全事實 |
| `benchmark-checklist` | 用七個問題審查量測數字：限制因素、是否 tuned、是否違反物理上限、是否報錯、是否重現、是否影響 end-to-end、工作是否真的在計時區間內 | faster／slower／no measurable difference／inconclusive |
| `create-verification-skill` | 訪談 repo，產生 project-local 的 `verify-<app>` skill：Launch、Doctor、Drive、Evidence、Cleanup，外加 feature map；生成後先自己跑一次證明可用 | 專案內可重複驅動 app 的驗證 skill |
| `show-me-your-work` | 用 `decisions.tsv` 記錄每個決策的時間、phase、decision、why、evidence、result；長任務結束前用不同模型家族審計 trail | 可審計的決策軌跡與 Attention 清單 |

這一層是 pstack 與「純提示詞工作流」的主要差別：它不要求人相信 agent 的自我描述，而是要求 agent 產出**人可以重跑的證據**。

### 3.7 多模型編排

| skill | 拓撲 | 模型策略 | 產出 |
|---|---|---|---|
| `how` | 2–4 個 explorer + 1 個 explainer | explorer 用 `grok-4.7-xhigh-fast`，explainer 用 `claude-opus-5-5-xhigh` | 子系統的架構說明 |
| `why` | 依證據類別平行查詢 MCP | 每個類別一個 subagent | 有引用來源的「為什麼這樣設計」 |
| `architect` | 先 `how` 取得 ground，再用 `arena` 產生設計候選 | 至少兩個結構上不同的候選 | 型別、簽名、模組邊界的 sketch 與 rationale |
| `arena` | N 個候選 + 1 個 cross-judge + graft | 不同模型家族各跑候選，cross-judge 偏好與 parent 不同家族 | 一個合成產物與選擇理由 |
| `swarm` | N 個 worker 切 slices 或 race | worker 用 `grok-4.7-xhigh-fast`；每個 worker 有獨立輸出 | 一份 `PASS`／`ISSUES`／`BLOCKED` 報告 |
| `interrogate` | 每個模型一個 reviewer | 預設 opus + grok | Act on／Consider／Noted／Dismissed 四桶與 Agreement Map |

這裡的對抗訊號來自**模型多樣性**，不是角色扮演。`interrogate` 明確說「The adversarial signal comes from model diversity, not assigned personas」。這與「讓同一個模型扮演三個角色」是不同機制。

### 3.8 自主性與隔離

| 規則 | 內容 |
|---|---|
| 可逆工作直接做 | 使用任何 MCP 工具； reversible 的外部動作（team chat、ticket update、kick off eval）不需要先問 |
| 不可逆工作暫停 | force-push 到共享分支、deploy、刪資料、對客戶發訊息 |
| Session override | 「don't stop」「going to bed」「run until done」「be fully autonomous」會讓 agent 持續執行 |
| 不說違心的 yes | 「No is an acceptable answer」；被問要不要做某事時，給真實判斷，不把同意當預設 |
| 隔離 | 每個候選或 worker 有自己的 worktree／輸出；`swarm` 的 worker 不共用可寫狀態 |
| Context 保護 | 大量讀取交給 subagent，主線只保留摘要與決策 |

### 3.9 把糾正變成結構

| 機制 | 做什麼 |
|---|---|
| `reflect` | 從本次 transcript 找出可留存的學習，三個 reviewer 並行，合成 Accepted／Rejected／Backlog，經人核准後修改 skill |
| `correct` | 找出 agent 在這個 repo 重複犯的錯誤類別，依序用 architecture → types → lint → test → docs 修正；每條規則配一個 enforcement |
| `automate-me` | 從使用者最近的 transcript 挖出實際工作方式，草擬一個 `<name>-mode` skill，底層仍路由到 pstack |
| `no-comments` | 在 review 前移除註解，讓 `comment-sicko` 檢查被註解遮住的問題 |
| `unslop` | 28 條實際規則（編號到 33，含跳號）移除 AI 腔、長句、模糊歸因、裝飾性 emoji、模糊結論 |

這一層回應的是「重複犯錯」：不是再寫一條提醒，而是把提醒變成下一個 agent 無法繞過的結構。

### 3.10 跨 harness 移植

mirror 的主要工作是把 Cursor 專屬指令改寫成 harness 無關的描述。`poteto-mode` 的 Harness 段提供對照：

| Cursor | 其他 harness |
|---|---|
| `Task` | Claude Code 的 `Agent`、OpenCode 的 `task`、Codex 的 `spawn_agent` |
| `AskQuestion` | Claude Code 的 `AskUserQuestion`、OpenCode 的 `question` |
| `agent-transcripts/` | `~/.claude/projects/<slug>/*.jsonl`、`~/.pi/agent/sessions/...`、`~/.codex/sessions/...`、OpenCode 的 `~/.local/share/opencode/storage/` |
| `.cursor/skills/` | `.claude/skills/`、`.pi/skills/`、`.agents/skills/` |
| `~/.cursor/rules/pstack-models.mdc` | `~/.agents/pstack-models.md` |

沒有 subagent 工具的 harness（例如沒有 extension 的 Pi）會把 delegated step 改成自己依序做；沒有 `deslop`／`control-cli`／`control-ui` 時，改用現有的 diff 檢查、Playwright／CDP、tmux／PTY。這使 pstack 的可移植性成立，但效果與成本會隨 harness 能力改變。

### 3.11 設計立場

| 立場 | 內容 | 影響 |
|---|---|---|
| 不寫 plan | 「the best spec is code」；repo 沒有預設的 planning skill，plan 只在 multi-phase 或使用者要求時出現 | 與 spec-first 工作流的前提相反 |
| 最小變更 | laziness protocol、subtract before add、no comments | diff 傾向變小，但不保證功能正確 |
| 驗證優先 | prove it works、blast radius、benchmark checklist | 品質的舉證責任從人轉到可執行證據 |
| 模型多樣性 | 對抗訊號來自不同模型，不是 persona | 需要多模型存取與成本 |
| 自主但有約束 | 可逆直接做，不可逆暫停 | 與「不加人工審核關卡、但要有 verify」同向 |
| 手動入口 | 54 個 skill 中 53 個標 `disable-model-invocation: true`，只有 `setup-pstack` 不標 | 避免技能自行跳出來搶路由；單一入口由人明確啟動 |
| 可 fork | MIT；`automate-me` 產生自己的 mode；`setup-pstack` 改模型角色 | 使用者可以把 pstack 當基底，改成自己的風格 |

### 3.12 機制與問題的對應

| 問題 | 機制 | 可觀察產出 |
|---|---|---|
| 產出膨脹 | principles + `unslop` + `no-comments` | 較小的 diff、較乾淨的 prose |
| 未驗證 | `prove-it-works`、`tdd`、`blast-radius`、`benchmark-checklist` | 命令輸出、測試、script、before／after 數字 |
| 人成為瓶頸 | `create-verification-skill`、`never-block-on-the-human` | project-local verify skill、agent 自己跑的證據 |
| 並行不安全 | worktree／cloud 隔離、`swarm`、獨立 verdict | 隔離的 branch、`PASS`／`ISSUES`／`BLOCKED` 報告 |
| 單模型盲點 | `arena`、`interrogate` | 跨模型 Agreement Map、cross-judge 意見 |
| 重複犯錯 | `correct`、`reflect` | lint／type／CI／skill 修改 |
| 長任務漂移 | playbook + todo + `show-me-your-work` | `decisions.tsv`、Attention 清單 |
| 跨 harness | mirror 的 mapping | Claude Code／Codex／Pi／OpenCode 可安裝 |

### 3.13 核心機制一句話

**pstack 把「工程紀律」拆成三件事：入口路由（playbook）、判斷詞彙（principle）、可執行證據（verification），再用多模型與隔離把單 agent 的嚴謹度放大到多 agent。**

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.0 先讀他的判準

以下判準來自第二大腦骨幹與相關檔。**標 `draft` 的是 AI 整理或自動流程產出，未經他本人 review；轉述時不當成他的定稿。**

| 判準 | 內容 | 對 pstack 的意涵 |
|---|---|---|
| 理解優先 | 不穩定或不熟悉時先自己兜，MVP 是理解的驗證點；「用現成的比較快」不是說服他的理由 | 整套安裝 54 個 skill 與「先自己兜以理解」相反；抽取機制後自建較接近 |
| MVP→Feature 唯一閘門 | 只有「能不能影響個人 workflow」才進 Feature | pstack 目前不在 `下一步清單`，沒有進入 workflow 的依據 |
| Reject≠沒價值 | 被拒者仍可抽取「它對需求的理解」與「解決方案的方向」 | 即使不採用，仍可抽取 blast-radius、benchmark-checklist、correct 等機制 |
| 約束放 harness，不放權限 | 不要加人工審核關卡；要補驗證機制（測試、validator、CI、可回滾） | pstack 的驗證堆疊與此同向 |
| 汰換看上游死活 | 不看有沒有更好的；維護停更或需求消失才汰換 | pstack 上游仍活躍，不因「有更好」而汰換；但成熟度仍是導入門檻 |
| 不追新 | 新不構成理由 | 2,154 stars 與 186.2K installs 是採用訊號，不是他的採用理由 |
| 同族預設拒 | 已在營運同族產品時，同類新標的預設拒；翻盤看規模、存續、穩定、治理 | pstack 不是他營運的同族產品，這條不直接適用；但它對「同類工作流包」的保守態度可對照 |

### 4.1 第二大腦對 pstack 的紀錄

以 `pstack`、`backnotprop`、`poteto` 對 `FATESAIKOU/MyBrain` 全 bundle 做 grep：**0 命中。** pstack 是首見，第二大腦沒有他對這個 repo 的既有判定。

### 4.2 既有判定

| 檔案 | 判定 | 理由摘要 | 信任層級 | 時間 | URL |
|---|---|---|---|---|---|
| 技術取捨準則（骨幹） | 判準，非工具判定 | 理解優先、MVP→Feature 閘門、Reject≠沒價值、約束放 harness、不加人工審核關卡 | `generated.by claude-code/opus-5`、`status draft`：**AI 草稿，未經他 review** | 2026-08-01 | [連結](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md) |
| 判定總表（骨幹） | 索引，非單一判定 | 129 筆判定的總表；pstack 不在其中 | `generated.by ollama-cloud/deepseek-v4-flash`、`status draft`：**AI 草稿，未經他 review** | 2026-08-02 | [連結](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md) |
| AI 開發 workflow 方案比較 | 採用 | 三案比較；定案「對齊用 mattpocock 的 grill，長期沈澱用 OpenSpec，superpowers 留給團隊場景」 | `generated.by claude-code/opus-5`、`status draft`：**AI 草稿，未經他 review** | 2026-08-02 | [連結](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/AI開發workflow方案比較.md) |
| AI 開發 workflow 三案實測 | 實測紀錄 | 案 A 94.6 分、$0、0 subagent；案 B 51.5 分、$0.12、28 subagent；superpowers 沒有自動觸發；TDD 與兩階段 review 沒跑 | `generated.by claude-code/opus-5`、`status draft`：**AI 草稿，未經他 review** | 2026-08-02 | [連結](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/AI開發workflow實測.md) |
| agent-skills | 觀望 | 24 個 lifecycle skill、7 命令 × 6 階段；2026-08-11 由採用降級，原因為資源而非技術，未排入下一步 | `generated.by human:fatesaikou`、`status stable`：**他本人的判定** | 2026-06-20（2026-08-11 降級） | [連結](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/agent-skills.md) |
| GStack 學習 | 不採用 | 多角色強制工作流 + 防禦性提示詞 + 每個 Duty 拆四檔；屬理解優先的抽取行為，會自己兜一套類似的 | `generated.by human:fatesaikou`、`status stable`：**他本人的判定** | 2026-03-22 | [連結](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/GStack%20學習.md) |
| Spec-Driven Development 的消費期限 | 不採用 | SDD 已在 OpenSpec + mattpocock 中實踐，不需新導入；價值在「消費期限」判斷框架 | `generated.by ollama-cloud/deepseek-v4-flash`、`status draft`：**AI 草稿，未經他 review** | 2026-08-15 | [連結](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Spec-Driven%20Development.md) |
| 下一步清單（骨幹） | 無 pstack 條目 | 清單是目前可直接執行的下一步；技術側有 LLM 推論骨架、ego-lite、ox-alpha、QMD 等，沒有 agent workflow 大改 | `generated.by claude-code/opus-5`、`status draft`：**AI 草稿，未經他 review** | 2026-08-11 | [連結](https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md) |
| 專案現況表（骨幹） | 無 workflow 大改 | 20 個動手做專案：日常在用 4、進行中 1、理解已達成 10、索引 5；沒有 pstack 類專案 | `generated.by ollama-cloud/deepseek-v4-flash`、`status draft`：**AI 草稿，未經他 review** | 2026-08-02 | [連結](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/專案現況表.md) |
| 同族預設拒 | 判準 | 已在營運同族產品時，同類新標的預設拒；翻盤條件是外部客觀的成熟度 | `generated.by process:learn-gh-agent`、`status draft`：**自動流程草稿，非他本人** | 2026-10-06 | [連結](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/同族預設拒.md) |

### 4.3 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **OpenSpec + mattpocock grill**（第二大腦記錄的主幹；draft） | OpenSpec 管 proposal／specs／design／tasks／archive；mattpocock 的 grill 在開工前逼問，順手寫 `CONTEXT.md` 與 ADR | 人願意每步打指令；專案要長期累積規格；需要可回滾的 spec 真相 | 7 個指令靠人；實作階段沒有強制 TDD；短期品質靠規格精度 | 長期規格會累積；變更可追溯；人的決定權最大 |
| **superpowers**（draft 記錄：Reserve） | 8 個 skill 自動串：brainstorming、worktree、writing-plans、subagent-driven-development、TDD、review、verification、finish | 團隊場景；可接受 subagent 成本；需要流程強制 | 實測 28 個 subagent、$0.12；plan 27.8K；TDD 與兩階段 review 沒跑；沒有 `using-superpowers` 時不自動觸發 | 單次交付快一倍；隔離乾淨；團隊交棒規格密度高 |
| **agent-skills**（他判觀望） | 24 個 lifecycle skill + 7 命令 × 6 階段；把 Google 工程文化寫進 skill | 需要完整開發生命週期；願意照命令走 | 判定成立但未排程；與現有 OpenSpec + mattpocock 重疊 | 私有產品開發流程可快速組裝；工程紀律一致 |
| **GStack**（他判不採用） | 9 個 Role、多個 Duty，每個 Duty 拆 `judgeStandard`／`inputSpec`／`outputSpec`／`processDefinition`；多角色強制審查 | 需要組織級角色分工；可接受重流程 | 多角色強制工作流、防禦性提示詞、每個 Duty 四檔；他判理解優先抽取 | 用角色與關卡壓制 LLM 亂給承諾；架構可抽取 |

### 4.4 切入點差異

| 方案 | 切入層 | 品質擔保者 | 對人的假設 |
|---|---|---|---|
| **pstack** | 任務路由 + 驗證 + 多模型對抗 | 流程 + 可執行證據 | 人只給目標與不可逆閘門 |
| **OpenSpec + mattpocock** | 規格 artifact | 人 | 人每步駕駛，規格長期累積 |
| **superpowers** | 流程強制 | 流程本身 | 人退到核可位，接受 subagent 成本 |
| **agent-skills** | 生命週期命令 | 命令與工程文化 | 人照階段走 |
| **GStack** | 組織角色 | 角色關卡 | 人扮演多角色 |

### 4.5 明確衝突與一致

| 面向 | 第二大腦立場 | pstack | 關係 |
|---|---|---|---|
| 主幹 workflow | OpenSpec + mattpocock（draft，2026-08-02） | 明確反對 planning，主張「the best spec is code」 | **直接衝突** |
| 採用姿勢 | GStack 不採用（human stable）；agent-skills 觀望（human stable）；理解優先、先自兜 | 54 個 skill 的整套包；mirror 單人維護、5 個月、0 release | **整套採用與他的預設相反**；抽取機制則一致 |
| 驗證 | 約束放 harness、不加人工審核關卡、要 verify | prove-it-works、blast-radius、benchmark-checklist、create-verification-skill | **高度一致** |
| 成本 | 模型分級；superpowers 實測 $0.12 vs $0、28 subagent vs 0 | 預設 opus 5.5 xhigh + grok 4.7 xhigh；panel 與 swarm 放大成本 | **預設成本與他的分級相衝**；角色設定可調 |
| 成熟度 | 汰換看上游死活；同族預設拒有成熟度閘門 | mirror 2026-05 建立、24 commits、1 contributor、0 release；上游 `cursor/plugins` 仍活躍，mirror 落後一版 | **mirror 未過成熟度閘門**；上游仍活躍 |
| 平行 | 他的多 agent 實測用契約先行 + PM 獨立驗證 | swarm／arena／autonomy + 獨立 verdict | **方向一致、實作不同** |

衝突點展開：

1. **前提層衝突：pstack 的「不寫 plan」與他已定案的 spec-anchored 主幹直接相衝。** 第二大腦記錄的 2026-08-02 定案（AI 草稿，未經他 review）是「對齊用 mattpocock 的 grill，長期沈澱用 OpenSpec」。pstack 說 planning 不是預設、最好的 spec 是 code。若把 pstack 當主幹，等於刪掉 OpenSpec 的長期沈澱層。這不是工具偏好差異，是品質擔保者的差異：OpenSpec 由人與累積的規格擔保，pstack 由流程與可執行證據擔保。
2. **整套採用與他的前例相衝。** GStack 是 `human:fatesaikou`／`stable` 的「不採用」，理由是多角色強制工作流屬理解優先的抽取；agent-skills 是 `human:fatesaikou`／`stable` 的「觀望」，理由是未排入下一步。pstack 是同一姿態的更大包（54 個 skill、23 個 playbook）。照前例，預設動作是抽取，不是替換主幹。
3. **預設成本與他的模型分級相衝。** 他把高價模型留給 harness 與判斷標準，機械工作給中低價；pstack 預設 opus 5.5 xhigh 與 grok 4.7 xhigh，並用 panel 與 swarm 放大呼叫量。這一點可由 `setup-pstack` 改角色設定，屬可調參數，不是架構缺陷。
4. **一致點：驗證與約束。** pstack 的 `never-block-on-the-human`、`prove-it-works`、`encode-lessons-in-structure` 與他的「約束放 harness、不加人工審核關卡、要 verify」同向。他的 superpowers 實測也顯示「流程強制」在個人場景只兌現一半；pstack 把品質重心放在可執行驗證而非流程關卡，這一點比 superpowers 更接近他的判準。
5. **成熟度與維護風險。** 被調研的 mirror 是 5 個月、24 commits、單一 contributor、0 release；上游 `cursor/plugins` 仍活躍。依他的「汰換看上游死活」與成熟度閘門，這不構成「已死」，但 mirror 的同步由一人承擔，也不構成「可依賴的基礎設施」。採用整包會讓 workflow 依附在一個人的同步節奏上。

### 4.6 反面論證

| 支持把 pstack 當主幹的理由 | 反面與限制 |
|---|---|
| 54 個 skill 覆蓋理解、變更、交付、自主、元工作，範圍完整 | 範圍完整不等於每個能力都需要；與現有 OpenSpec + mattpocock 大面積重疊；維護面與學習面同步放大 |
| 驗證堆疊具體，blast-radius 與 benchmark-checklist 有可操作步驟 | 這些機制依賴專案有可驅動的 app 或可重跑的 script；純研究、純文件、純資料工作只能部分套用 |
| 多模型 panel 降低單模型盲點 | 需要多模型存取與額度；panel 與 swarm 的成本隨模型數與 worker 數線性上升 |
| 自主與 overnight run 提高吞吐 | 指南自己說：沒有可檢查的完成條件、隔離與決策紀錄，迴圈只會更快產生未檢查的工作 |
| 不寫 plan，直接以 code 為 spec，減少 plan 與實作的漂移 | 與他現行的 spec-anchored 主幹相反；且「code 即 spec」要求 code review 與驗證能力足夠強，否則失去可追溯性 |
| MIT、可 fork、`automate-me` 可改成自己的風格 | mirror 單人維護、0 release、落後上游；上游活躍但 mirror 的同步由一人承擔；fork 後的同步成本由使用者承擔 |

### 4.7 依他的判準推演出的定位

以下是**依上述判準的推演，不是他本人的判定**：

- pstack 解的問題與他的「驗證放在 harness」同向，但它的**整套採用**與他的「理解優先、抽取後自兜、主幹已定」相衝。兩者同時成立。
- 以 `MVP→Feature` 閘門看，pstack 目前不在 `下一步清單`，也沒有進入他的日常 workflow 的依據。整包安裝不會通過閘門。
- 可抽取的機制有四項，皆屬於「補驗證、不換主幹」：
  1. **blast-radius 的證據階梯**：自己說 → `file:line` → 證明壞情況走不到 → 跑程式 → 在運行中的 app 重現。可直接對照他的 judge／validate 設計。
  2. **benchmark-checklist 的七問**：把「量到的數字」變成可反駁的檢查，適合放進 P01 的報告 QA 或效能調研。
  3. **create-verification-skill 的 Launch／Doctor／Drive／Evidence／Cleanup + feature map**：與 LearnGhAgent 的 do／know／judge／guardrail 同問題域，可作為「agent 如何證明自己在真實 app 上做對了」的結構參考。
  4. **correct 的修正順序**：architecture → types → lint → test → docs，且每條規則配一個 enforcement。這與他的「約束放 harness、encode lessons in structure」一致。
- pstack 的 `principle` 引用規則（只引用本次讀過的 leaf、引用必須對應一個決策）也可作為 agent 回報的審計欄位，而不是拿來當新的 workflow 主幹。
