# 200_R1_step2-plan_C1.md

## 狀況理解

R1 技術標的為 opencode 的 skill／agent 系統，3 個子面向（skill 發現與載入、skill 與 command/plugin 關係、對比 Claude Code）。Step 2 C1 任務為取得 repo metadata 與主要文件。Step 1 已從第二大腦得知 2026-08-04 日誌實測過 skill/command 探索路徑，本次需補 Claude Code 對比與 plugin 關係；C1 只定位與擷取原始碼，不在這步做結論。技術 repo 為 `anomalyco/opencode`（README 聲明為官方 repo）。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view anomalyco/opencode` | 取得 repo metadata | stars、license、語言、預設分支 | 成功：195k stars、MIT、TypeScript、forkCount 24986 |
| 抓取 git trees 全檔清單（7270 檔） | 定位 skill/agent/command/plugin 相關原始碼 | 找到核心實作檔路徑 | 命中 `packages/core/src/skill*.ts`、`config/plugin/skill.ts`、`plugin/skill.ts`、app 層 `packages/opencode/src/skill/index.ts` |
| 抓 README（`main` 分支） | 取得概覽 | README 全文 | 失敗：`main` 404，預設分支為 `dev` |
| 抓 README（`dev` 分支） | 取得概覽 | README 全文 | 成功：確認 Agents（build/plan/general）、安裝方式 |
| 抓取 docs（skills/agents/commands.mdx） | 取得官方定義 | 對照實作的依據 | 成功：取得 skill 目錄位置、frontmatter、permission、command/agent 語法 |
| 抓核心原始碼 skill.ts/discovery.ts/tool/skill.ts/guidance.ts | 理解 v2 skill 載入機制 | 確認 source 型別與掃描邏輯 | 成功：確認 directory/url/embedded 三種 source、glob 掃 `{*.md,**/SKILL.md}`、`<available_skills>` 注入 system context |
| shallow clone repo（sparse） | 追查 `.claude`/`.agents` compat 接線位置 | 確認官方文件聲明的路徑對應哪份實作 | 成功：定位 `packages/opencode/src/skill/index.ts` 為真正掃描 `.claude`/`.agents` 的 app 層實作 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 技術標的定位 | 確認 repo 與預設分支 | anomalyco/opencode，預設分支 `dev`（非 `main`），官方文件與原始碼一致 |
| skill 載入實作位置 | 追蹤 skill 掃描程式碼 | 有兩套：core 層 `packages/core/src/skill.ts`（v2, directory/url/embedded source）與 app 層 `packages/opencode/src/skill/index.ts`（真正掃 `.claude`/`.agents`、`.opencode`、config skills.paths/urls） |
| skill 發現路徑 | 對照 docs 與原始碼 | `.claude/skills`、`.agents/skills`（global 與 project up-walk）、`.opencode/{skill,skills}`、`config.skills.paths/urls`（url 走 index.json pull） |
| frontmatter | 對照 core 與 app 層解碼 | app 層僅認 `name`+`description`（`isSkillFrontmatter`）；core 層認 `name/description/slash`；docs 另列 license/compatibility/metadata |
| skill 與 permission | 確認載入時的權限門檻 | `SkillV2.available()` 依 agent permission 過濾 `skill` action，deny 則隱藏；tool/skill.ts 載入時再 assert |
| command／plugin 關係 | 抓 config/plugin 原始碼 | command 吃 `.opencode/commands/`（markdown 或 JSON `command` 欄位）；plugin 吃 `.opencode/plugins/`、global plugin 目錄、npm 套件，經 `ctx.skill.transform()` 注入 skill source |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 抓取目標分支 | `main` / `dev` | `dev` | `main` 上 README 404，`gh repo view` 顯示預設分支為 `dev`，官方內容以 dev 為準 |
| skill 實作取哪套 | 只看 core 層 / 連 app 層一起看 | 兩套都看 | core 層未含 `.claude`/`.agents` 掃描，僅 app 層 `skill/index.ts` 有此邏輯；只看 core 會漏掉 compat 路徑 |
| repo 內容取得方式 | 逐檔 curl / shallow clone sparse | 先 curl 後 clone | curl 快速定位核心檔；`.claude` 字串在逐檔 grep 找不到，改用 shallow clone 全庫 grep 才定位到 app 層實作 |
| 本步範圍 | 直接寫結論 / 只蒐證 | 只蒐證並記錄來源 | C1 為資訊取得 step，結論留給 C2/C3；log 只記錄「取得哪些原始碼與文件」 |
