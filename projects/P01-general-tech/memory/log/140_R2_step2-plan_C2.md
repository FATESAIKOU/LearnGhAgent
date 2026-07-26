# 140_R2_step2-plan_C2.md

## 狀況理解

C1 已取得所有必要資料。本 sub-step 針對使用者 R2 的 3 個問題進行分析合成，產出回答內容，供 Step 3 寫入最終報告的 §5 User Q&A。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 分析 Hallmark 的 4 verbs 與 SKILL.md frontmatter description | 回答 Q1：核心定位 | 給出明確的「一句話定位」+ 對照表 | 完成：Hallmark 是「生成階段強制約束系統」，非「撰寫工具」也非「驗證工具」 |
| 分析 Claude Code 官方 skills 文件的自動載入機制 | 回答 Q2：自動套用行為 | 確認 Claude Code 與 Opencode 的差異 | 完成：Claude Code 自動載入（description matching），Opencode 按需載入（skill tool） |
| 整理安裝步驟 | 回答 Q3：逐一步驟 | 給出 Claude Code 與 Opencode 的完整安裝指令 | 完成：3 種安裝方式，含 Opencode 的相容路徑 |

## 動作結束後的現狀

**Q1 分析結果：**

Hallmark 的核心 identity 是「**生成階段強制約束系統**」，不是「撰寫工具」也不是「驗證工具」。對照表：

| 面向 | 撰寫工具 | 驗證工具 | Hallmark |
|------|----------|----------|---------|
| 介入時機 | 生成前/中 | 生成後 | **生成中**（注入 prompt 約束） |
| 產出 | 直接產出 UI 程式碼 | 產出評分/建議 | 產出 UI 程式碼（受約束） |
| 是否修改產出 | 是（生成） | 否（只檢查） | 是（生成時強制遵循規則） |
| Audit verb | 無 | 有 | 有（但非核心） |
| 核心機制 | 模板/元件庫 | 規則檢查 | **prompt 注入 + 結構/風格強制多樣性 + 自檢** |

**Q2 分析結果：**

| Agent 框架 | 預設載入行為 | 控制方式 |
|---|---|---|
| **Claude Code** | **自動載入**（當 conversation 與 skill description 匹配時，Claude 自動載入 skill 內容） | 在 SKILL.md frontmatter 設 `disable-model-invocation: true` 可禁止自動載入 |
| **Opencode** | **按需載入**（agent 透過 `skill` tool 看到可用 skills 列表，可選擇載入或不載入） | 透過 `opencode.json` 的 `permission.skill` 設定 allow/deny/ask |

Hallmark 的 SKILL.md 中 `description` 包含 "Use when the user asks to build a new app or landing page"，因此在 Claude Code 中，當使用者說「幫我建一個 landing page」時，Claude Code **會自動載入 Hallmark**。在 Opencode 中則不會自動載入，需 agent 判斷後手動呼叫 `skill` tool。

**Q3 安裝步驟分析結果：**

3 種安裝方式，適用於不同情境：

1. **`npx skills add nutlope/hallmark`**（最簡單，自動安裝到 Claude Code）
2. **手動複製到 Claude Code**：`~/.claude/skills/hallmark/`
3. **手動複製到 Opencode**：`~/.config/opencode/skills/hallmark/` 或 `.opencode/skills/hallmark/`

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| Q1 定位的表述方式 | (a) 一句話定義 (b) 對照表 + 一句話 | (b) 對照表 + 一句話 | 使用者混淆的根源是 Hallmark 同時具備生成與審計功能，需用對照表明確區分各 verb 的角色 |
| Q2 是否需區分 Claude Code 與 Opencode | (a) 只回答 Claude Code (b) 兩者都回答 | (b) 兩者都回答 | 使用者明確問了「claudecode/opencode之流」，需涵蓋兩者 |
| Q3 是否包含 Opencode 的安裝方式 | (a) 只給 Claude Code 步驟 (b) 給兩者 | (b) 給兩者 | Hallmark 官方 README 未提及 Opencode，但 Opencode 相容 Claude skill 格式，可安裝 |
