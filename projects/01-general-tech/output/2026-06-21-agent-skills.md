# 技術分析報告：addyosmani/agent-skills

> 調研日期：2026-06-21
> 標的：https://github.com/addyosmani/agent-skills

---

## 1. 這個技術解決什麼問題？

AI coding agent（如 Claude Code、Cursor、Gemini CLI 等）在生成程式碼時，預設行為是走「最短路徑」——跳過規格撰寫、測試、安全審查、程式碼審查等工程紀律，直接產出可運行的程式碼。這導致產出品質停留在 prototype 層級，而非 production-grade。

agent-skills 解決的具體問題是：**AI agent 缺乏內建的工程判斷力，無法自動執行資深工程師在開發流程中會遵守的結構化工作流程（spec → plan → build → test → review → ship）。**

## 2. 這個問題為什麼會發生？（背景）

**文章中明確提到的背景：**

- AI coding agent 的預設行為是「最短路徑」——給定一個 prompt，agent 傾向於直接產出程式碼，跳過 spec、測試、安全審查等步驟
- agent 會產生「合理化藉口」（rationalizations）來跳過步驟，例如「之後再加測試」、「這個很簡單不用寫 spec」
- 這些問題源自 agent 的訓練目標是「完成使用者的即時請求」，而非「產出長期可維護的軟體」

**通用技術背景（文章中未明確提及但為已知事實）：**

- LLM 的訓練資料中，程式碼生成任務的 ground truth 通常是「可運行的程式碼片段」，而非「遵循完整開發流程的產出」。這使得 agent 在沒有外部引導的情況下，自然傾向於跳過流程性步驟
- 現有 AI coding tool 的設計哲學多為「降低進入門檻」，強調快速產出而非工程紀律
- 資深工程師的開發紀律（寫 spec、寫測試、code review）是經驗累積的結果，無法透過簡單的 prompt 指令讓 agent 內化

## 3. 這個技術是如何解決該問題的？

agent-skills 將資深工程師的開發紀律編碼為 24 個結構化 skill，每個 skill 是一個 agent 可執行的 workflow，包含以下核心機制：

### 3.1 Skill 的結構化格式

每個 `SKILL.md` 遵循固定 anatomy：

```
┌─ Frontmatter ──────────────┐
│ name: lowercase-hyphen-name │
│ description: + trigger 條件 │
└────────────────────────────┘
Overview         → 這個 skill 做什麼
When to Use      → 觸發條件（何時啟用）
Core Process     → 步驟化 workflow（agent 照做）
Common Rationalizations → 藉口表 + 反駁
Red Flags        → 違反 skill 的 observable 信號
Verification     → 退出條件（需有證據）
```

**關鍵設計：**
- **Process, not prose**：skill 是 agent 可執行的步驟序列，不是參考文件
- **Anti-rationalization**：每個 skill 內建「藉口表」，列出 agent 可能用來跳過步驟的藉口，並附上事實反駁。例如「之後再加測試」的反駁是「沒有測試就無法驗證行為是否正確，後續修改會產生回歸」
- **Verification is non-negotiable**：每個 skill 的退出條件需要可驗證的證據（測試通過、build 輸出、runtime data），「看起來對」不被接受

### 3.2 三層架構

| 層級 | 定義 | 範例 | 職責 |
|------|------|------|------|
| **Skill** | 有步驟與退出條件的 workflow | `code-review-and-quality` | 怎麼做（the *how*） |
| **Persona** | 單一角色 + 單一視角 | `code-reviewer` | 誰來做（the *who*） |
| **Command** | 使用者進入點 | `/review`, `/ship` | 何時做（the *when*） |

### 3.3 8 個 Slash Command 對應完整生命週期

```
/spec    → Define   （規格先於程式碼）
/plan    → Plan     （拆成小型原子任務）
/build   → Build    （一次一個垂直切片）
/test    → Verify   （測試就是證據）
/review  → Review   （改善程式碼健康度）
/webperf → Audit    （先測量再最佳化）
/code-simplify → Simplify（清晰勝於巧妙）
/ship    → Ship     （越快越安全）
```

### 3.4 平行審查機制（`/ship`）

`/ship` 會平行 fan-out 給 4 個 persona（code-reviewer、security-auditor、test-engineer、web-performance-auditor），各自在獨立 context 中產出報告，再由主 agent 合併為 go/no-go 決策。這解決了單一 agent context 無法同時承載多個審查視角的問題。

### 3.5 跨工具相容性

skill 是純 Markdown 格式，可被 Claude Code、Cursor、Gemini CLI、Antigravity、OpenCode、Windsurf、Copilot 等多種 agent tool 載入。這降低了採用門檻——使用者不需要更換工具就能導入這些 workflow。

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 替代方案對照表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|---------|-------------|---------------|----------------|
| **Superpowers** (obra) | 完整的開發方法論，強調自主性與前期推理：Socratic brainstorming → 子 agent 執行 → 兩階段審查（spec 合規 + 程式碼品質），使用 git worktree 隔離並行工作 | 願意讓 agent 長時間自主執行；工作屬於探索性或架構性任務 | 前期推理時間較長（約 12 min vs agent-skills 的 8 min）；驗證範圍較窄（5 次 vs 7 次） | 適合長時間自主執行、探索性工作；前期架構推理更深入 |
| **Matt Pocock's skills** | 單一專家的日常 Claude Code 工作流程開源化，核心為 `/tdd`（agent 層級強制 red-green-refactor）與 `/grill-me`（需求盤問） | 使用 Claude Code 為主要工具；專案偏向 TypeScript 生態 | 生命週期覆蓋範圍較窄（集中在 planning + build + tooling）；跨工具支援有限 | 低儀式感的日常工具包；需求盤問與嚴格 TDD 為亮點 |
| **手寫 system prompt / AGENTS.md** | 直接在 agent 的 system prompt 或 AGENTS.md 中撰寫開發流程規範 | 對 agent 的 prompt 機制有深入理解；願意手動維護 | 缺乏結構化格式（無 anti-rationalization、無 verification gate）；難以跨工具移植；不易擴充 | 最輕量的方案，但品質與可維護性最低 |

### 切入點差異

- **agent-skills**：以「生命週期階段」為組織原則，每個階段有對應的 command 與 skill，人類在每個階段有 checkpoint。適合需要完整流程覆蓋、多工具支援的場景。
- **Superpowers**：以「自主執行」為核心設計目標，子 agent 隔離執行 + 兩階段審查。適合長時間放手讓 agent 工作的場景。
- **Matt Pocock's skills**：以「個人效率」為核心，精選日常高頻使用的 workflow。適合已經有成熟開發習慣的個人開發者。

### 注意事項

三個專案可以 cherry-pick 個別 skill 混用，但不能同時將兩個作為主要 router（meta-skill）。同時啟用兩個 router 會導致 command 名稱衝突（如 `/tdd` 被定義兩次）、routing logic 競爭、TDD 哲學不一致，產出不可預期的行為。
