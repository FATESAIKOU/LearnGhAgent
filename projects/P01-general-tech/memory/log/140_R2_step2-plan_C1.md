# 140_R2_step2-plan_C1.md

## 狀況理解

本 sub-step 為 R2 的第一個調研動作。使用者提出 3 個問題：(1) Hallmark 的核心定位釐清（生成 vs 審計 vs 驗證）；(2) 安裝後是否自動套用於所有對話；(3) 安裝到 Claude Code / Opencode 的逐一步驟。需取得 repo metadata、README、SKILL.md、Claude Code 官方 skills 文件、Opencode 官方 skills 文件，以回答這三題。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view Nutlope/hallmark --json ...` | 取得 repo metadata | 確認 stars、license、語言、建立日期等 | 成功：17.9k stars, 901 forks, CSS primary, MIT, 2026-04-27 建立，非 archived |
| `gh api repos/.../readme` | 取得 README.md | 確認安裝方式、4 verbs 說明、主題範例 | 成功：安裝指令 `npx skills add nutlope/hallmark`，4 verbs 說明，20 themes + Custom 模式 |
| `gh api repos/.../contents/skills/hallmark/SKILL.md` | 取得核心 SKILL.md | 確認 frontmatter description、設計流程、slop test 細節 | 成功：description 明確寫「Anti-AI-slop design skill for greenfield pages, audits, redesigns, and design extraction...」，含 6 條跨 verb 紀律、Design flow 6 步驟、Component-scope flow、58 道 slop gates |
| `gh api repos/.../contents/package.json` | 取得 package.json | 確認 skill 封裝格式 | 成功：含 `skill.entry`、`skill.references`、`skill.harnesses`（claude-code, cursor, codex）欄位，為標準 npm skill 封裝 |
| `gh api repos/.../contents/skills/hallmark/references` | 列出 references 目錄 | 確認參考文件完整度 | 成功：25+ 個參考文件（anti-patterns.md, slop-test.md, macrostructures.md, themes/ 等） |
| `gh api repos/.../contents/skills/hallmark/references/slop-test.md` | 讀取 slop test 細節 | 確認 58 道閘門的具體內容 | 成功：含 pre-emit self-critique（6 軸 1-5 分自評）、Visual/Structural/Microinteractions/Variety/Implementation/Hero/Diversification 等閘門類別 |
| WebFetch Claude Code skills 官方文件 | 確認 Claude Code 的 skill 載入機制 | 確認自動套用行為 | 成功：Claude Code 根據 description 自動載入相關 skill；`disable-model-invocation: true` 可禁止自動載入；skill 內容在載入後持續存在於 context 中 |
| WebFetch Opencode skills 官方文件 | 確認 Opencode 的 skill 載入機制 | 確認自動套用行為 | 成功：Opencode 透過 `skill` tool 按需載入，agent 看到可用 skills 列表後可選擇載入；非自動套用 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Hallmark 核心定位 | 比對 README 首句 + SKILL.md frontmatter description + 4 verbs 說明 | 核心 identity 為「anti-AI-slop design skill」，default verb 是生成新 UI，audit/redesign/study 為次要 verb |
| Claude Code 自動套用行為 | 讀取 Claude Code 官方 skills 文件 | 預設為 description matching 自動載入（Claude 判斷相關時自動載入），可透過 `disable-model-invocation: true` 關閉 |
| Opencode 自動套用行為 | 讀取 Opencode 官方 skills 文件 | 預設為按需載入（agent 透過 `skill` tool 手動載入），非自動套用 |
| 安裝步驟完整性 | 比對 README + package.json + Claude Code 官方文件 | 有 3 種安裝方式：`npx skills add`、手動複製到 `~/.claude/skills/`、手動複製到 `.cursor/rules/` |
| R1 報告缺口 | 比對 R1 報告與 R2 提問 | R1 報告 §1 已回答「解決什麼問題」但未給出「一句話定位」；§3 詳述機制但未說明安裝後行為；未給出安裝指令 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否讀取全部 25+ references | (a) 全部讀取 (b) 只讀 slop-test.md 與關鍵文件 | (b) 只讀 slop-test.md | 使用者問題聚焦於定位、自動套用、安裝步驟，非 slop test 細節。slop-test.md 已足夠驗證 R1 報告的正確性 |
| 自動套用行為的資訊來源 | (a) 從 README 推測 (b) 查 Claude Code + Opencode 官方文件 | (b) 查官方文件 | 自動套用行為取決於 Agent 框架的 skill 載入機制，非 Hallmark 本身能決定。官方文件為唯一可靠來源 |
| 是否查 npm 上的 skills-cli 套件 | (a) 查 (b) 不查 | (b) 不查 | `npx skills add` 的詳細行為可從 README 與 package.json 推斷，且 npm 頁面回傳 403，無需強行取得 |
