# 127_R1_step2-plan_C1.md

## 狀況理解

R1 Step 2 C1：取得 `MadsLorentzen/ai-job-search` 的 repo metadata 與主要文件，為後續分析建立完整資訊基底。目標是理解該技術的定位、架構、核心機制。

## 執行的動作與結果

| 動作 | 目的 | 預期達成效果 | 實際結果 |
|------|------|-------------|---------|
| `gh api repos/...` 取得 repo metadata | 取得結構化 repo 資訊 | 獲得 stars、forks、語言、授權、topic 等 | 成功：20.9k stars, 6k forks, MIT, TypeScript 69%/Python 24%/TeX 7%, 12 topics |
| WebFetch README.md | 理解專案定位與功能 | 取得完整 README | 成功：取得完整 README，含架構圖、指令表、檔案結構、工作流程 |
| WebFetch CLAUDE.md | 了解 Claude Code 整合方式 | 取得候選人設定檔模板 | 成功：取得完整 CLAUDE.md，含 profile 模板、驗證清單 |
| WebFetch SETUP.md | 了解安裝與設定流程 | 取得完整安裝指南 | 成功：取得完整 SETUP.md，含依賴安裝、三種 onboarding 路徑 |
| WebFetch SKILL.md (job-application-assistant) | 了解核心 skill 定義 | 取得 skill 規格 | 成功：取得 workflow 定義、reference files 對照表 |
| WebFetch 01~07 profile files | 了解評估框架與模板 | 取得完整技能檔案 | 成功：取得 candidate-profile、behavioral-profile、writing-style、job-evaluation、cv-templates、cover-letter-templates、interview-prep |
| WebFetch CONTRIBUTING.md | 了解專案貢獻政策 | 取得貢獻規則 | 成功：取得「universal template」哲學與 merge/decline 標準 |
| WebFetch commands/apply.md | 了解 /apply 完整流程 | 取得 drafter-reviewer 工作流細節 | 成功：取得 7-step 流程（parse→evaluate→draft→review→revise→compile→present） |
| WebFetch commands/setup.md | 了解 /setup 完整流程 | 取得三種 onboarding 路徑細節 | 成功：取得 Path A/B/C 完整流程 |
| WebFetch settings.json | 了解 Claude Code 權限設定 | 取得 permission allowlist | 成功：取得允許的 skill 與 bash 指令 |
| `gh api repos/.../languages` | 取得語言佔比 | 確認技術棧 | 成功：TypeScript 152KB, Python 52KB, TeX 16KB |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 驗證結果 |
|---------|--------------|---------|
| Repo metadata | 確認 stars/forks/license/language/topics | 20.9k stars, 6k forks, MIT, TypeScript 主語言, 12 topics |
| 核心定位 | README 描述 | AI job application framework built on Claude Code，fork-and-own 模式 |
| 架構理解 | 檔案結構 + 指令流程 | 完整：/setup→/scrape→/rank→/apply→/interview→/outcome 生命週期 |
| 核心機制 | /apply 的 drafter-reviewer workflow | 7-step 流程含 PDF compile-and-inspect loop + ATS 驗證 |
| 背景脈絡 | Claude Code 整合方式 | 透過 .claude/commands/ 與 .claude/skills/ 定義 Claude Code 自訂指令與技能 |
| 貢獻政策 | CONTRIBUTING.md | 嚴格：只 merge universal 功能，market-specific 內容導向 fork |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---------|---------|---------|---------|
| 文件擷取範圍 | 僅 README / README+核心文件 / 含原始碼 | README+核心文件（CLAUDE.md, SETUP.md, SKILL.md, 01~07, commands, CONTRIBUTING.md, settings.json） | C1 目標是建立完整架構理解，原始碼留給 C2 視需要深入 |
| 背景查詢 | 不查 / 查 Claude Code 背景 / 查 job search 市場 | 暫不查，C1 先收斂 repo 內部資訊 | C1 範圍為 repo metadata 與文件，背景脈絡留給 C2 |
| 語言佔比解讀 | 僅列數字 / 分析意義 | 分析意義：TypeScript 為 CLI 工具主語言，Python 為 salary 工具，TeX 為 CV/cover letter 模板 | 有助於理解技術棧分工 |
