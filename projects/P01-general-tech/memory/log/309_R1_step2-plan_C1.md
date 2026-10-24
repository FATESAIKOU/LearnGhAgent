# 309_R1_step2-plan_C1.md

## 狀況理解

Step 1 已判定標的為 `backnotprop/pstack`，是 `cursor/plugins/pstack` 的 standalone mirror。C1 只做「取得 repo metadata 與主要文件」，不進入逐個 skill 的細讀與替代方案比較。需確認：repo 規模與活躍度、mirror 與上游的關係、檔案結構、入口文件（README、`poteto-mode`、plugin manifest、guide）所定義的定位與機制。後續 C2 再處理個別 skill／playbook 與背景脈絡。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view backnotprop/pstack --json ...` | 取得 stars、license、分支、更新時間 | 建立基本檔案 | 2,152 stars、155 forks、8 watchers、0 open issues、MIT、`main`、最後 push 2026-10-15 |
| `gh api repos/backnotprop/pstack` | 取得建立時間、語言、topics、size | 判斷專案年齡與性質 | 建立 2026-05-27，TypeScript（僅 scripts），size 2,877 KB，topics 為 agentskills／pstack |
| 取 README（27,385 bytes） | 取得完整定位、安裝、skill 清單 | 界定 §1～§4 素材 | 成功；mirror 前言與上游 README 分成兩段 |
| 取 `git/trees/main?recursive=1` | 盤點目錄結構 | 確認 skill／playbook／principle 數量 | 成功；`skills/`、`agents/`、`docs/guide/`、`automations/benny/`、`skills/poteto-mode/scripts/` |
| 讀 `skills/poteto-mode/SKILL.md`（23,594 bytes） | 取得入口 skill 的實際規則 | 理解路由、原則、autonomy、subagent、harness 對照 | 成功；含 24 原則索引、23 playbook、模型分工與非 Cursor harness 映射 |
| 讀 `plugin.json`、`MIRROR.md`、`docs/guide/README.md`、`01-setup.md`、`02-poteto-mode.md`、`07-overnight.md`、`08-principles.md` | 確認版本、同步方式、使用流程 | 補齊文件層級脈絡 | 成功；mirror 版 0.15.25，上游同日已 0.15.26 |
| 交叉查 `cursor/plugins` 的 pstack 路徑 | 確認上游活躍度與版本差 | 區分 mirror 與原版 | 上游 2026-10-18 仍在合 PR（0.15.26）；mirror 落後一個版本 |
| 查 GitHub 搜尋與相關 fork | 確認外部採用型態 | 判斷是否只有單一 mirror | 另有 `nicksinai/pstack-codex`、`tommy-ca/pstack`、`FetchUpstream/pstack-plugin` 等移植／再包裝 |
| 查 skills.sh 頁面 | 取得安裝量線索 | 補充 stars 以外的採用訊號 | 顯示 186.2K total installs |
| `gh api commits`／`contributors`／`releases` | 確認維護結構 | 判斷 bus factor | 24 commits、唯一 contributor `backnotprop`、0 releases |

取得的關鍵事實：

- 安裝路徑有兩條：mirror 的 `npx skills add backnotprop/pstack`（skills CLI，支援 Claude Code、Codex、Pi、Cursor、OpenCode），與 Cursor 原版的 `/add-plugin pstack`。
- 內容規模：16 個可獨立使用的 skill、8 組需搭配安裝的 skill、24 個 `principle-*`、2 個 subagent（`poteto-agent`、`comment-sicko`）、23 個 playbook、10 頁 guide、1 個 dormant 的 benny automation pack。
- 入口 `poteto-mode` 的機制：讀 24 原則索引 → 把任務匹配到 playbook → 將步驟原文複製進 todo → 按步驟呼叫 `how`／`why`／`architect`／`arena`／`swarm`／`interrogate`／`unslop` 等 skill → 回覆中指名用了哪條原則、改變了哪個決策。
- 模型分工：預設 code delegate 走 `grok-4.7-xhigh-fast`，prose 與 judgment 走 `claude-opus-5-5-xhigh`；`/setup-pstack` 寫入角色→模型對應規則，其他 harness 寫 `~/.agents/pstack-models.md`。
- 明確的設計立場：反對先寫 plan（「the best spec is code」）、反對 AI slop、以減少 LOC 與可驗證性為目標、允許 autonomous run 與多 agent 並行。
- README 與 `poteto-mode` 都附有 harness 對照表（Task／AskQuestion／skill 目錄／transcript 路徑），mirror 的主要改寫即為去除 Cursor 專屬指令。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 標的性質 | README 首段與 `MIRROR.md` | 純檔案化 Agent Skills；mirror 保留上游內容並改寫 harness 依賴 |
| 版本 | `plugin.json` 與上游 commit | mirror 0.15.25；上游 0.15.26（落後約 1 日） |
| 維護結構 | contributors／commits／releases | 單一維護者、無 release、靠 commit 與版本號推進 |
| 文件完整度 | guide 10 頁＋README＋23 playbook | 安裝、路由、設計、驗證、 overnight、principle 操作都有專頁 |
| 外部採用 | forks、skills.sh、GitHub 搜尋 | 有 Codex／Grok／plugin 等第三方移植與再包裝，非孤立專案 |
| C1 邊界 | 是否已讀完所有 skill | 否；只讀入口與文件層，個別 skill 細節留 C2 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 取得 metadata 的方式 | 1. `gh api` 2. `webfetch` | `gh api`／`gh repo view` | 環境已認證，欄位穩定且可一次取齊 |
| 讀哪一份 README | 1. mirror 2. 上游 `cursor/plugins` | mirror 為主、上游只做版本交叉 | 使用者給的是 mirror；mirror 前言才說明跨 harness 安裝 |
| 主要文件範圍 | 1. 只讀 README 2. 加讀入口 skill 與 guide | README＋`poteto-mode/SKILL.md`＋關鍵 guide | 入口 skill 才含實際路由與 harness 映射，README 只是目錄 |
| 是否逐個 skill 細讀 | 1. C1 全讀 2. 留給 C2 | 留給 C2 | C1 目標是定位與盤點，全部細讀會超出 log 長度且混淆階段 |
| 是否把 stars 當主要訊號 | 1. 只看 stars 2. stars＋安裝量＋fork 生態 | 三者並列 | pstack 是多 harness 的 skill 包，單看 GitHub stars 會低估採用面 |
