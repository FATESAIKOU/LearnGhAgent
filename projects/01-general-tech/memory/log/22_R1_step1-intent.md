# 22_R1_step1-intent.md

## 狀況理解

使用者要求調研 GitHub repo `anthropics/courses`，並依 01-general-tech 的分析報告格式產出報告。無其他附帶條件或特殊要求。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 PR body | 理解使用者要調研的技術標的 | 確認技術標的與條件 | 技術標的為 `anthropics/courses`，無附帶條件 |
| 讀取 know/AGENTS.md | 確認 Step 1 輸出格式 | 產出符合規範的 log | 格式確認完成 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 技術標的 | 從 PR body 提取 | `anthropics/courses` |
| 附帶條件 | 從 PR body 提取 | 無 |
| 報告格式要求 | 依 AGENTS.md 規範 | 使用 01-general-tech 分析報告格式（4 個 section） |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 技術標的判定 | `anthropics/courses` 或需進一步釐清 | `anthropics/courses` | PR body 明確指定該 GitHub repo |
| 報告格式 | 依 AGENTS.md 或自行決定 | 依 AGENTS.md | AGENTS.md 已明確定義分析報告格式 |
