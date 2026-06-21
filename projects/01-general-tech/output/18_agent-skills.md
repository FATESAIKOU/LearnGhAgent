# agent-skills 技術分析報告

> 調研標的：GitHub repo `addyosmani/agent-skills`（64k stars, MIT license）
> 調研日期：2026-06-21

---

## 1. 這個技術解決什麼問題？

AI 程式碼生成代理（Claude Code、Cursor、Gemini CLI 等）在生成程式碼時，預設行為是走**最短路徑**——跳過規格撰寫、測試、安全審查、程式碼審查等工程紀律，直接產出「看起來對」的程式碼。這導致：

- 規格不明確就開始寫程式，後續反覆修改
- 測試覆蓋不足或測試寫法不當
- 安全漏洞未被發現就合併
- 效能問題在生產環境才浮現
- 程式碼品質不一致，難以維護

**agent-skills 解決的問題**：讓 AI 代理在開發流程的每個階段（定義→規劃→建置→驗證→審查→發佈）都遵循結構化的工作流程，強制執行資深工程師會遵守的工程紀律，而非讓代理自由發揮。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的原因

- AI 編碼代理的激勵結構偏向「最短的路徑」——代理被訓練成快速產出答案，而非產出高品質、可維護的軟體
- 代理缺乏「何時該做什麼」的工程判斷力：不知道何時該寫規格、該測試什麼、如何審查、何時可以發佈
- 代理會自我合理化跳過步驟：「這個太小了不需要規格」、「我之後再加測試」、「先寫程式再補文件」

### 通用技術背景

- **LLM 的 token 經濟**：代理的 context window 有限，且每次 API 呼叫都有成本。代理傾向於用最少 token 完成任務，而工程紀律（寫規格、寫測試、做審查）需要額外的 token 消耗
- **AI 輔助開發的成熟度不足**：2024-2025 年間，AI 編碼工具快速普及，但「如何讓 AI 寫出可維護的生產級程式碼」的方法論尚未標準化。多數使用者直接把 prompt 丟給代理，沒有結構化的工作流程
- **資深工程師的知識難以傳遞**：資深工程師的工程判斷（何時寫規格、如何拆任務、測試策略、審查標準）是 tacit knowledge，難以用簡單的 prompt 傳遞給 AI 代理
- **工具碎片化**：Claude Code、Cursor、Gemini CLI、Copilot 各有不同的 plugin/rule 機制，缺乏統一的工程紀律標準

---

## 3. 這個技術是如何解決該問題的？

agent-skills 的核心機制是**將工程紀律編碼為結構化的 Markdown 工作流程（SKILL.md）**，讓 AI 代理在執行任務時遵循。

### 3.1 三層架構

```
┌─────────────────────────────────────────────────────────┐
│  Slash Commands（.claude/commands/）— 使用者的進入點     │
│  /spec  /plan  /build  /test  /review  /ship  /webperf  │
│  使用者輸入指令 → 啟動對應的 skill workflow              │
├─────────────────────────────────────────────────────────┤
│  Skills（skills/<name>/SKILL.md）— 核心工作流程          │
│  24 個 skill，每個含：                                   │
│  - Overview（概述）                                      │
│  - When to Use（觸發條件）                               │
│  - Process（步驟式工作流程）                             │
│  - Common Rationalizations（反合理化表）                 │
│  - Red Flags（紅旗警示）                                │
│  - Verification（驗證標準）                              │
├─────────────────────────────────────────────────────────┤
│  Personas（agents/<role>.md）— 專業審查角色              │
│  code-reviewer / test-engineer / security-auditor        │
│  web-performance-auditor                                │
│  用於 /ship 階段的平行 fan-out 審查                      │
└─────────────────────────────────────────────────────────┘
```

### 3.2 反合理化機制（Anti-Rationalization）

每個 skill 內建一個表格，列出代理常用的跳過藉口與對應的反駁：

| 代理的藉口 | 反駁 |
|-----------|------|
| "這個太小了不需要 skill" | 大小不是跳過紀律的理由 |
| "我可以直接快速實作" | 快速實作通常遺漏邊界條件 |
| "我先收集 context" | 收集 context 本身就是 skill 的一部分 |

這不是建議性的提醒，而是**強制性的工作流程步驟**——代理被指示「必須忽略這些想法，嚴格遵循 skill 流程」。

### 3.3 生命週期覆蓋

agent-skills 將開發流程分為 6 個階段，每個階段對應多個 skill：

```
DEFINE（定義）→ PLAN（規劃）→ BUILD（建置）→ VERIFY（驗證）→ REVIEW（審查）→ SHIP（發佈）
  /spec        /plan        /build         /test        /review       /ship
```

24 個 skill 分布在這些階段中，從 idea-refine（點子收斂）到 shipping-and-launch（上線檢查），涵蓋完整生命週期。

### 3.4 平行審查機制（Parallel Fan-out）

`/ship` 指令會同時啟動 4 個審查 persona（code-reviewer、test-engineer、security-auditor、web-performance-auditor），各自獨立產出審查報告後再合併為 go/no-go 決策。這是唯一被認可的多 persona 協作模式。

### 3.5 跨工具相容性

agent-skills 支援 7 種以上的 AI 編碼工具（Claude Code、Cursor、Gemini CLI、Antigravity、OpenCode、Windsurf、GitHub Copilot），透過不同的安裝方式（plugin、rules file、AGENTS.md）整合。核心 skill 檔案是純 Markdown，不綁定特定 runtime。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表：替代方案對照

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|---------|-------------|--------------|----------------|
| **Superpowers**（obra/superpowers, 234k stars） | 以 subagent 驅動的完整開發方法論：Socratic brainstorming → 子代理執行任務 → 兩階段審查（spec compliance + code quality）→ git worktree 隔離 | 願意讓代理長時間自主執行（數十分鐘到數小時）；工作內容需要大量前期架構推理 | token 消耗集中在前期的架構推理階段；git worktree 隔離增加磁碟使用量；subagent 無法再 spawn subagent | 適合探索性、架構不確定的工作，代理自主完成後回傳審查過的結果 |
| **Matt Pocock's skills**（mattpocock/skills, 138k stars） | 個人化的 Claude Code 工具集：/tdd（強制 red-green-refactor）、/grill-me（需求盤問）、/diagnose（除錯）、pre-commit/git guardrails | 使用 Claude Code 為主要開發工具；偏好 TypeScript 生態系；接受個人化的 opinionated 工作流 | 僅深度覆蓋規劃+建置階段，缺乏安全、效能、CI/CD、發佈等後期階段；跨工具支援有限 | 低儀式感的日常開發工具集，適合 TypeScript 專案的每日開發循環 |
| **agent-skills**（本專案） | 以 SDLC 階段為組織原則的完整 skill 集合：meta-skill 路由 + 反合理化表 + 平行審查 persona + 參考檢查清單 | 願意在每個階段設置人為檢查點；需要跨安全/效能/CI/CD 的完整覆蓋 | 每個階段都需要人為介入（無法完全自主）；24 個 skill 的 context 管理需要選擇性載入 | 從定義到發佈的引導式生命週期，每個階段有品質閘門，合併前有平行審查 |

### 切入點差異

- **Superpowers** 的切入點是**自主性**：它假設使用者想「交給代理去做，回來看結果」，因此投資大量 token 在前期的架構推理與 subagent 隔離
- **Matt Pocock's skills** 的切入點是**個人效率**：它反映單一資深工程師的日常 workflow，精準但範圍有限
- **agent-skills** 的切入點是**流程覆蓋**：它假設使用者想在每個階段都有品質檢查點，因此覆蓋範圍最廣（從 idea 到 launch），但需要較多的人為參與

### 實證對比

Om Mishra 的單一任務對照實驗（同模型 Sonnet 4.6、同 repo、同 prompt）：
- agent-skills：~8 分鐘進入程式碼階段，7 次驗證（含完整 test suite），捕獲了 feature 外部的相容性問題
- Superpowers：~12 分鐘進入程式碼階段，5 次驗證，前期架構推理較深
- token 效率：兩者幾乎相同，各 replan 一次

結論：agent-skills 在**驗證深度**上有優勢，Superpowers 在**前期架構推理**上有優勢。選擇取決於任務類型。

### 組合建議

三者可以互補，但**不能同時作為主要 router**（會造成指令衝突、路由邏輯打架、TDD 哲學不一致）。建議：
- 選一個作為主要 router
- 從其他專案 cherry-pick 個別 skill（如 Matt 的 grill-me、Superpowers 的 subagent isolation）
