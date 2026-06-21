# 22_R3_step2-plan_C1.md

## 狀況理解

本 sub-step 為 R3 的 Step 2 第一個調研動作。使用者 R2/R3 的三個子問題是：(1) `anthropics/courses` 是誰（repo 的定位與歸屬），(2) 可以用在什麼業務（適用場景），(3) 加速還是提升品質（對業務的影響類型）。R1 報告已產出但以技術架構視角為主，缺少業務視角的回答。本 step 需重新取得 repo 原始資料，從業務視角提取資訊。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view anthropics/courses --json` | 取得 repo metadata | 獲得 owner、stars、forks、語言、建立時間等結構化資料 | 成功取得：owner=anthropics, stars=21931, forks=2325, 主要語言=Jupyter Notebook, 授權=CC BY-NC 4.0, 建立於 2024-05-30 |
| Web fetch README.md | 取得 repo 首頁說明 | 了解 repo 定位、課程列表、建議學習順序 | 成功取得：5 門課程（API fundamentals → Prompt engineering → Real world prompting → Prompt evaluations → Tool use），建議依序學習 |
| Web fetch 5 個子課程 README | 取得各課程的詳細內容與目標 | 了解各課程的學習目標、章節結構、適用對象 | 成功取得全部 5 個課程的 README，涵蓋各課程的章節列表與學習目標 |
| Web fetch LICENSE | 確認授權條款 | 了解商用限制 | 成功取得：CC BY-NC 4.0（非商業用途授權，商用需另行授權） |
| 讀取 R1 報告 `output/22_anthropic-courses.md` | 確認既有內容 | 了解 R1 已涵蓋的範圍，避免重複 | R1 報告 84 行，以技術架構視角描述課程內容與替代方案，未以業務視角回答「誰、什麼業務、加速/品質」 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo 歸屬 | 比對 gh API 回傳的 owner 與 README 內容 | owner=anthropics（Anthropic 公司官方帳號），repo 為官方維護的教育課程 |
| 課程完整度 | 確認 5 個課程目錄皆存在且有對應 README | 5 門課程皆完整，無缺漏 |
| 授權限制 | 讀取 LICENSE 全文 | CC BY-NC 4.0，非商業用途免費，商用需另行授權 |
| 業務視角資訊充足性 | 評估現有資料能否回答使用者三個子問題 | 充足：從 README 與課程內容可推導出目標受眾（開發者）、適用業務場景（客服、醫療、通話摘要等）、以及對業務的影響類型（加速 onboarding + 提升 prompt 品質） |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否需要 fetch 課程內部的 notebook 內容 | (a) 僅讀取各課程 README；(b) 深入讀取個別 notebook | (a) 僅讀取 README | 使用者問題屬於業務視角（誰、什麼業務、加速/品質），README 已提供足夠的課程目標與案例類型資訊，不需深入 notebook 細節 |
| 是否需要查詢 Anthropic 公司背景 | (a) 查詢 Anthropic 公司定位與產品線；(b) 不查，直接從 repo 資訊推導 | (b) 不查 | repo 本身已明確標示為 Anthropic 官方課程，且使用者問題聚焦於「這個 repo 是誰」，而非「Anthropic 公司是誰」 |
| 是否需要查詢類似課程的業務影響數據 | (a) 搜尋業界使用 anthropics/courses 的案例與效益數據；(b) 不查，僅基於課程內容推論 | (b) 不查 | 使用者問題可從課程設計意圖（README 中的學習目標描述）合理推論，不需外部案例數據 |
