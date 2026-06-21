# 技術分析報告：addyosmani/agent-skills

> 調研日期：2026-06-21
> 標的：https://github.com/addyosmani/agent-skills
> Stars：64.2K | Forks：6.9K | License：MIT | 主要語言：Shell | 建立：2026-02-15

---

## 1. 這個技術解決什麼問題？

**AI coding agent 缺乏標準化、可複用、跨平台的行為定義方式。**

具體來說，存在以下子問題：

- 每個 AI coding agent（Claude Code、Cursor、Gemini CLI、OpenCode、Copilot、Windsurf、Antigravity）各有自己的設定檔格式與行為注入機制，使用者需為每個平台重複撰寫類似指令
- 使用者對 agent 的行為描述散落在 prompt、設定檔、slash command 中，缺乏結構化、可版本控管的單一來源
- 缺乏「讓 agent 具備特定領域能力（如 TDD、安全審計）」的標準封裝單元，導致能力難以分享與複用
- 缺乏 agent persona 的標準化定義，不同 agent 對同一任務的行為不一致

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- 2025-2026 年間，AI coding agent 工具大量湧現（Claude Code、Cursor、Gemini CLI、OpenCode、Copilot、Windsurf、Antigravity），每個平台各自發展了不同的 agent 行為擴充機制
- 這些平台缺乏共同的 skill 格式標準，導致使用者需為每個平台重複撰寫類似內容
- agent-skills 專案於 2026-02 建立，試圖建立一個「skill 格式標準」來統一跨平台的行為定義

### 通用技術背景

- 傳統 IDE 的擴充機制（VS Code extensions、JetBrains plugins）是針對靜態程式碼編輯設計，不適用於 LLM-based agent 的動態行為控制
- LLM agent 的行為控制依賴 system prompt 與工具定義，但 prompt engineering 缺乏結構化標準，導致行為難以預測與重現
- 軟體工程領域的「關注點分離」原則（Separation of Concerns）在 agent 行為定義上尚未被系統化應用

---

## 3. 這個技術是如何解決該問題的？

agent-skills 採用三層架構來標準化 agent 行為定義：

### 3.1 三層架構

```
┌─────────────────────────────────────┐
│  Agent Personas（角色人格）          │
│  ┌─────────────────────────────────┐│
│  │  Skills（技能單元）              ││
│  │  ┌───────────────────────────┐  ││
│  │  │  Slash Commands（快捷指令） │  ││
│  │  └───────────────────────────┘  ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

- **Agent Persona**：定義 agent 的整體角色與行為框架（如 code-reviewer、security-auditor、test-engineer、web-performance-auditor）。每個 persona 包含其 scope、決策矩陣、輸出模板。
- **Skills**：封裝特定能力的標準化單元，以 `SKILL.md` 格式定義。包含 frontmatter（name、description、model-requirements、context-reserve）與 6 個標準 section（behavior、instructions、rules、workflow、examples、rationalizations）。
- **Slash Commands**：提供快速觸發特定行為的捷徑（如 `/review`、`/test`、`/audit`、`/explain` 等 8 個 commands）。

### 3.2 SKILL.md 標準格式

每個 skill 遵循以下結構：

```yaml
---
name: <技能名稱>
description: <一句話描述>
model-requirements: <最低模型需求>
context-reserve: <保留的 context 比例>
---
## behavior
<agent 應表現的行為模式>

## instructions
<逐步操作指示>

## rules
<硬性規則，不可違反>

## workflow
<工作流程的生命週期>

## examples
<範例輸入/輸出>

## rationalizations
<設計決策的理由>
```

### 3.3 跨平台整合機制

agent-skills 不依賴特定平台的 plugin 系統，而是透過以下方式跨平台運作：

| 平台 | 整合方式 | 載入機制 |
|------|---------|---------|
| Claude Code | 將 skills/ 目錄加入專案，透過 AGENTS.md 引用 | 檔案系統讀取 |
| Cursor | 將 skills/ 目錄加入專案，透過 .cursorrules 引用 | 檔案系統讀取 |
| Gemini CLI | 將 skills/ 目錄加入專案，透過 AGENTS.md 引用 | 檔案系統讀取 |
| OpenCode | 透過 skill tool 動態載入 SKILL.md | 工具呼叫 |
| Copilot | 將 skills/ 目錄加入專案，透過 .github/copilot-instructions.md 引用 | 檔案系統讀取 |
| Windsurf | 將 skills/ 目錄加入專案，透過 .windsurfrules 引用 | 檔案系統讀取 |
| Antigravity | 透過 plugin.json 註冊為 plugin | plugin 系統 |

### 3.4 核心 Skills 一覽（24 個）

| Skill | 功能 |
|-------|------|
| using-agent-skills | meta-skill：skill 發現與路由決策樹 |
| spec-driven-development | 4 階段 gated workflow（Spec → Implement → Verify → Document） |
| test-driven-development | RED-GREEN-REFACTOR 循環 + Prove-It pattern |
| doubt-driven-development | CLAIM-EXTRACT-DOUBT-RECONCILE-STOP 5 步驟 adversarial review |
| code-review | 5 軸 code review（correctness、security、performance、maintainability、style） |
| security-audit | 6 大 scope 安全審計（OWASP Top 10、dependency、auth、data、config、deploy） |
| test-strategy | 5 種測試場景策略 + coverage analysis |
| web-performance | Quick/Deep 雙模式效能審計 + Core Web Vitals scorecard |
| ...（另有 16 個 skill） | ... |

### 3.5 生命週期覆蓋

agent-skills 的 skills 覆蓋軟體開發的完整生命週期：

```
Specification → Implementation → Verification → Documentation → Maintenance
     ↑              ↑               ↑               ↑              ↑
  spec-driven    TDD,          TDD,           using-agent-    code-review,
  development    doubt-driven  test-strategy  skills          security-audit,
                                                               web-performance
```

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 對照表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|---------|-------------|---------------|-----------------|
| **agent-skills** | 以 SKILL.md 標準格式封裝 agent 行為，透過檔案系統跨平台載入 | 專案需安裝對應的 AI coding agent 工具；agent 需支援從檔案讀取行為定義 | 無統一 registry，skill 發現依賴目錄結構；無版本管理機制 | 跨平台 agent 行為一致；skill 可分享與複用 |
| **Superpowers** (superpowered.dev) | 以 VS Code extension 形式提供 agent 能力，依賴 VS Code 生態 | 必須使用 VS Code 或 Cursor；需安裝 extension | 綁定特定 IDE；無法在 CLI-only agent 中使用 | 與 IDE 深度整合；提供 GUI 管理介面 |
| **Matt Pocock's skills** (mattpocock/skills) | 以 TypeScript 定義 agent 行為，強調型別安全與程式化組合 | 需熟悉 TypeScript；agent 需支援程式化 skill 定義 | 學習曲線較高；非開發者難以貢獻 | 型別安全的 skill 組合；可程式化控制行為 |
| **手寫 system prompt** | 直接在 agent 設定檔中撰寫自然語言行為描述 | 無特殊前提 | 無結構化標準；難以複用與版本控管；跨平台需重寫 | 最簡單的入門方式；無需學習新格式 |

### 4.2 切入點差異

- **agent-skills** 以「格式標準化」為核心，透過純文字檔案的 SKILL.md 格式達成跨平台相容，降低貢獻門檻
- **Superpowers** 以「IDE 整合」為核心，提供 GUI 管理與 VS Code 深度整合，但犧牲了 CLI agent 的相容性
- **Matt Pocock's skills** 以「型別安全」為核心，適合需要程式化組合與靜態驗證的場景，但非開發者難以參與
- **手寫 system prompt** 以「最低成本」為核心，適合一次性或小型專案，但缺乏結構化與可複用性

### 4.3 反面論證

| 質疑點 | agent-skills 的回應 | 潛在弱點 |
|--------|-------------------|---------|
| SKILL.md 是否會成為另一種 vendor lock-in？ | 格式為純文字 Markdown，無專屬工具依賴 | 缺乏正式規範文件，格式可能隨專案演進變動 |
| 24 個 skills 是否過多？ | 涵蓋完整生命週期，使用者可選擇性採用 | 初次使用者可能面臨選擇困難 |
| 跨平台行為一致性如何保證？ | 同一份 SKILL.md 在不同平台載入 | 各平台對 Markdown 的解析行為可能不同，無標準化測試套件 |
| 與現有專案工作流程如何共存？ | skills/ 目錄可與既有專案結構共存 | 需在專案中新增目錄與檔案，可能與既有規範衝突 |

---

## 附錄：專案結構

```
agent-skills/
├── agents/              # Agent personas（4 個）
│   ├── code-reviewer.md
│   ├── security-auditor.md
│   ├── test-engineer.md
│   └── web-performance-auditor.md
├── skills/              # Skills（24 個）
│   ├── using-agent-skills/SKILL.md
│   ├── spec-driven-development/SKILL.md
│   ├── test-driven-development/SKILL.md
│   ├── doubt-driven-development/SKILL.md
│   └── ...
├── docs/                # 文件
│   ├── comparison.md
│   ├── getting-started.md
│   ├── skill-anatomy.md
│   ├── agents.md
│   ├── opencode-setup.md
│   ├── cursor-setup.md
│   ├── gemini-cli-setup.md
│   ├── antigravity-setup.md
│   ├── copilot-setup.md
│   └── windsurf-setup.md
├── references/           # 參考資料
│   └── orchestration-patterns.md
├── plugin.json           # Antigravity plugin manifest
├── CONTRIBUTING.md
└── README.md
```
