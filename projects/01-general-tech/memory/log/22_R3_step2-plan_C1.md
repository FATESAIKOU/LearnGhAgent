# 22_R3_step2-plan_C1.md

## 狀況理解

R3 使用者重複追問 R2 的三個子問題：(1) anthropics/courses 的身份（誰／什麼組織的產物）；(2) 適用的業務場景；(3) 效果是加速還是提升品質。本 sub-step 需取得 repo metadata、README、各課程 README、授權條款，以回答上述問題。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view anthropics/courses --json` | 取得 repo metadata（stars, forks, 語言, 描述, 建立時間, 更新時間, owner） | 確認 repo 基本屬性與 owner 資訊 | 成功取得：owner=anthropics, stars=21931, forks=2325, 語言=Jupyter Notebook(99.9%)+Python(0.1%), 建立於 2024-05-30 |
| `gh api repos/anthropics/courses/contents` | 列出 repo 根目錄結構 | 確認課程目錄清單 | 5 個課程目錄：anthropic_api_fundamentals, prompt_engineering_interactive_tutorial, real_world_prompting, prompt_evaluations, tool_use |
| 讀取 README.md（raw.githubusercontent + gh API） | 取得 repo 頂層說明 | 了解 repo 定位與課程建議順序 | README 說明為「Anthropic's educational courses」，建議依序學習 5 門課程，使用 Claude 3 Haiku 降低 API 成本 |
| 讀取 5 個課程各自的 README.md | 取得各課程的學習目標與內容大綱 | 了解每個課程解決的子問題 | 全部成功取得：API fundamentals(6 課)、Prompt engineering(9 章)、Real world prompting(5 課)、Prompt evaluations(9 課)、Tool use(6 課) |
| 讀取 LICENSE | 確認授權條款 | 了解使用限制 | CC BY-NC 4.0（非商業用途），禁止商用 |
| 讀取既有報告 output/22_anthropic-courses.md | 回顧 R1 已產出的分析內容 | 確認哪些面向已回答、哪些未回答 | 報告涵蓋「解決什麼問題」「背景」「如何解決」「替代方案」，但未直接回答「誰的產物」「業務場景」「加速或品質」 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo 身份 | 從 gh API 取得 owner 與描述 | owner=anthropics（Anthropic 公司官方帳號），描述="Anthropic's educational courses" |
| 課程內容完整性 | 比對 5 個課程 README | 5 門課程涵蓋 API 基礎→提示工程→真實案例→評估→工具使用，共約 35+ 個 notebook |
| 授權限制 | 讀取 LICENSE 全文 | CC BY-NC 4.0，非商業用途，不可商用 |
| R1 報告缺口 | 比對 R1 報告與 R2 問題 | R1 未回答「誰的產物」「業務場景」「加速或品質」 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研範圍 | 僅 README vs 深入各課程 notebook 內容 | 僅 README 層級 | 使用者問的是「身份、業務場景、加速/品質」，屬高層次定位問題，不需深入 notebook 細節 |
| 背景查詢方式 | 搜尋 Anthropic 公司背景 vs 僅依 repo 內容 | 僅依 repo 內容 | repo 本身已清楚標示 owner=anthropics，且 README 已說明課程目的；使用者問題可從 repo 內容直接回答 |
| 是否查詢 Anthropic 公司資訊 | 查 vs 不查 | 查 | 使用者問「是誰」需要說明 Anthropic 公司背景，repo 本身無法提供此資訊，需外部查詢 |
