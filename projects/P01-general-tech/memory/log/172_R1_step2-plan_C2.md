# 172_R1_step2-plan_C2.md

## 狀況理解

C1 已取得 Gemini Spark 的官方文件與第三方分析。本 sub-step 需補查替代方案細節，並將 Gemini Spark 與使用者既有 workflow（GAS Gmail 自動化、BrowserBase、Feedly 自動閱讀）做對照分析，回答「能否對上我的工作流」這個核心問題。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 MyBrain 中 GAS Gmail 自動化專案全文 | 理解使用者既有 Gmail 自動化的實作細節與成熟度 | 判斷 Gemini Spark 的 Gmail 功能是否 overlap | GAS MVP 已達成理解：批次讀 Gmail → AI 摘要（Ollama/Copilot 動態切換）→ 寫入 Google Sheet，含進度保存、批次合併、類別分類。使用者已掌握此能力 |
| 讀取 MyBrain 中 BrowserBase 專案 | 理解使用者瀏覽器自動化的現狀 | 判斷 Gemini Spark 的 browser 功能是否 overlap | BrowserBase 進行中：chrome-devtools MCP wrapper 已接上 claudecode/opencode，目標是讓 browser 泛化 |
| 讀取 MyBrain 中 Feedly 自動閱讀專案 | 理解使用者資訊攝取自動化的現狀 | 判斷 Gemini Spark 的資訊彙整功能是否 overlap | Feedly 自動閱讀日常在用：瀏覽器自動化 + AI agent 穩定取代手動閱讀整理流程 |
| 讀取 MyBrain 技術取捨準則 | 理解使用者的技術決策框架 | 判斷 Gemini Spark 是否符合其決策模式 | 理解優先（先自己兜）、MVP 是理解裝置、Reject 不採納不等於沒價值、agent 約束在 harness 不在權限 |
| 讀取 MyBrain 中 Claude Cowork / ChatGPT Agent 相關評估 | 確認使用者是否已評估過同級替代方案 | 取得替代方案比較素材 | 無直接評估 Claude Cowork 或 ChatGPT Agent 的條目 |
| 比對 Gemini Spark 功能與使用者既有 workflow | 回答核心問題 | 產出對照分析 | 見下方分析 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| GAS Gmail 自動化 vs Spark Gmail 功能 | 功能對照 | GAS 已達成理解（批次讀取 + AI 摘要 + Sheet 寫入），Spark 提供類似能力但以 agent 形式（Task/Skills/Schedules），且深度整合 Google Workspace API |
| BrowserBase vs Spark browser 功能 | 功能對照 | BrowserBase 是自建 browser MCP wrapper，Spark 提供內建 remote/local browser 控制，但 Spark 的 browser 功能「coming this summer」尚未完全可用 |
| Feedly 自動閱讀 vs Spark 資訊彙整 | 功能對照 | Feedly 自動閱讀是使用者日常在用 workflow，Spark 無 Feedly 整合，但可透過 Google Search 與 Gmail 做資訊彙整 |
| 替代方案比較 | 讀取 DataCamp 比較表 | Spark vs Claude Cowork vs ChatGPT Agent 三者在架構、生態系、定價上的差異已掌握 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 報告中 workflow 對照的深度 | (A) 只列功能對照表 (B) 加上採用建議 | B | 使用者明確問「能不能對上我的工作流」，需要給出判斷與理由 |
| 替代方案範圍 | (A) 只列 Claude Cowork + ChatGPT Agent (B) 加上自建方案（GAS + BrowserBase） | B | 使用者已有自建方案，需比較「用 Spark」vs「繼續自建」的取捨 |
