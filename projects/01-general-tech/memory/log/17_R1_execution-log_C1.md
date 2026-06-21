# C1 - 取得 repo metadata 與主要文件

## 狀況理解

標的為 addyosmani/agent-skills，一個 GitHub 上的公開 repo。需取得 repo 基本 metadata（stars、license、語言、活躍度等），以及 README.md 與關鍵子文件（docs/、skills/、agents/、references/），作為後續分析的基礎素材。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|-----------|-----------|-------------|-----------|
| `gh repo view addyosmani/agent-skills --json ...` | 取得 GitHub repo metadata | 取得 stars、license、語言、更新時間等 | 失敗：gh CLI 未認證（GH_API_FAILED） |
| `webfetch https://api.github.com/repos/addyosmani/agent-skills` | 替代方案取得 repo metadata | 同上 | 成功：取得完整 JSON，含 stars=64199、forks=6937、MIT license、primaryLanguage=Shell、created=2026-02-15、updated=2026-06-21、topics=[agent-skills,antigravity,claude-code,cursor,skills] 等 |
| `webfetch README.md` (raw) | 擷取專案主要說明文件 | 了解專案定位、功能、結構 | 成功：取得完整 README，含 24 skills 列表、8 個 slash commands、7 個平台整合方式、專案結構樹 |
| `webfetch docs/comparison.md` | 取得與同類專案的比較 | 了解 agent-skills vs Superpowers vs Matt Pocock's skills 的差異 | 成功：取得完整對照表，含核心概念、組織原則、生命週期覆蓋範圍、獨特機制等 |
| `webfetch docs/getting-started.md` | 取得通用入門指南 | 了解跨平台使用方式 | 成功 |
| `webfetch docs/skill-anatomy.md` | 取得 SKILL.md 格式規範 | 了解 skill 的標準結構 | 成功：含 frontmatter、6 個標準 section、寫作原則 |
| `webfetch docs/agents.md` | 取得 agent persona 文件 | 了解 4 個 specialist personas 的設計與使用規則 | 成功：含 persona/skill/command 三層架構、決策矩陣、Claude Code interop |
| `webfetch docs/opencode-setup.md` | 取得 OpenCode 整合方式 | 了解本專案如何與 OpenCode 協作 | 成功：agent-driven 方式，無 plugin 系統，透過 AGENTS.md + skill tool |
| `webfetch docs/cursor-setup.md` | 取得 Cursor 整合方式 | 了解 Cursor 設定 | 成功 |
| `webfetch docs/gemini-cli-setup.md` | 取得 Gemini CLI 整合方式 | 了解 Gemini CLI 設定 | 成功 |
| `webfetch docs/antigravity-setup.md` | 取得 Antigravity CLI 整合方式 | 了解 Antigravity 設定 | 成功 |
| `webfetch docs/copilot-setup.md` | 取得 GitHub Copilot 整合方式 | 了解 Copilot 設定 | 成功 |
| `webfetch docs/windsurf-setup.md` | 取得 Windsurf 整合方式 | 了解 Windsurf 設定 | 成功 |
| `webfetch CONTRIBUTING.md` | 取得貢獻指南 | 了解 skill 貢獻規範 | 成功 |
| `webfetch skills/using-agent-skills/SKILL.md` | 取得 meta-skill | 了解 skill 發現與路由機制 | 成功：含完整決策樹、6 條核心操作行為、生命週期序列 |
| `webfetch skills/spec-driven-development/SKILL.md` | 取得 spec skill | 了解 spec-driven 工作流 | 成功：含 4 階段 gated workflow、spec template、rationalizations |
| `webfetch skills/test-driven-development/SKILL.md` | 取得 TDD skill | 了解 TDD 工作流 | 成功：含 RED-GREEN-REFACTOR、Prove-It pattern、test pyramid、anti-patterns |
| `webfetch skills/doubt-driven-development/SKILL.md` | 取得 doubt-driven skill | 了解 adversarial review 機制 | 成功：含 CLAIM-EXTRACT-DOUBT-RECONCILE-STOP 5 步驟、cross-model escalation |
| `webfetch agents/code-reviewer.md` | 取得 code reviewer persona | 了解 review 框架 | 成功：含 5 軸 review、severity 分類、輸出模板 |
| `webfetch agents/security-auditor.md` | 取得 security auditor persona | 了解安全審計框架 | 成功：含 6 大 scope、OWASP Top 10、severity 分類 |
| `webfetch agents/test-engineer.md` | 取得 test engineer persona | 了解測試策略框架 | 成功：含 5 種測試場景、coverage analysis 模板 |
| `webfetch agents/web-performance-auditor.md` | 取得 web performance auditor persona | 了解效能審計框架 | 成功：含 Quick/Deep 模式、CWV scorecard、metric-honesty rule |
| `webfetch references/orchestration-patterns.md` | 取得 orchestration 模式參考 | 了解 endorsed patterns 與 anti-patterns | 成功：含 5 種 endorsed patterns、4 種 anti-patterns、決策流程 |
| `webfetch plugin.json` | 取得 plugin manifest | 了解 Antigravity plugin 設定 | 成功：name=agent-skills, version=1.0.0 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|-----------|----------------|---------|
| Repo metadata 完整性 | 確認取得 stars、license、語言、建立/更新時間、topics、open issues | 通過：64.2K stars, MIT, Shell, 2026-02 建立, 6 topics |
| 主要文件完整性 | 確認 README.md 已取得 | 通過：完整內容含 24 skills、8 commands、7 platforms |
| 關鍵子文件完整性 | 確認 docs/ 下 8 份文件已取得 | 通過：comparison, getting-started, skill-anatomy, agents, 6 個平台 setup guides |
| Skill 文件代表性 | 確認 meta-skill + 3 個代表性 skill 已取得 | 通過：using-agent-skills, spec-driven-development, test-driven-development, doubt-driven-development |
| Agent persona 完整性 | 確認 4 個 personas 已取得 | 通過：code-reviewer, security-auditor, test-engineer, web-performance-auditor |
| 參考文件完整性 | 確認 orchestration-patterns 已取得 | 通過 |
| 背景脈絡補查 | 確認 comparison.md 已提供與 Superpowers、Matt Pocock's skills 的對照 | 通過：含 DA 表、head-to-head 實驗連結 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|-------------|------------|---------|---------|
| Repo metadata 取得方式 | (a) gh CLI (b) GitHub API via webfetch | (b) GitHub API via webfetch | gh CLI 未認證導致失敗，webfetch 為可靠替代方案 |
| 需擷取的 skill 文件數量 | (a) 全部 24 個 skill (b) 僅 meta-skill + 代表性 skill | (b) 僅 meta-skill + 代表性 skill | 24 個 skill 逐一擷取會超出 6000 字限制且重複性高；選取 meta-skill（路由邏輯）、spec-driven（定義階段核心）、TDD（驗證階段核心）、doubt-driven（獨特機制）即可涵蓋主要模式 |
| 需擷取的 docs/ 文件 | (a) 全部 (b) 僅 comparison + getting-started + skill-anatomy | (a) 全部 | 各平台 setup guide 對理解「跨平台整合差異」至關重要（req.md 中列為缺乏資訊） |
| 背景脈絡補查方式 | (a) 網路搜尋 (b) 依賴 repo 內 comparison.md | (b) 依賴 repo 內 comparison.md | comparison.md 已提供與 Superpowers、Matt Pocock's skills 的完整對照表及 head-to-head 實驗，足以滿足 Step 1 需求 |
