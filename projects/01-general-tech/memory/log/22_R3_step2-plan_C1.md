# 22_R3_step2-plan_C1.md

## 狀況理解

使用者 R3 重複 R2 的三個子問題：(1) anthropics/courses 是誰，(2) 可以用在什麼業務，(3) 加速還是提升品質。使用者認為前次未獲回答。R1 報告的 §5 User Q&A 實際上已包含這三個問題的答案（Q1-Q3），但使用者可能未注意到或 R2 回應未明確指引。本 step 需取得 repo metadata 與課程文件，確認答案的完整性。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view anthropics/courses --json ...` | 取得 repo 元資料 | 確認 owner、stars、forks、語言、建立時間 | owner=anthropics, stars=21933, forks=2328, 主要語言=Jupyter Notebook, 建立於 2024-05-30 |
| `gh api repos/anthropics/courses/readme` | 擷取 README.md | 了解 repo 整體定位與課程列表 | 確認 5 門課程：API fundamentals、Prompt engineering interactive tutorial、Real world prompting、Prompt evaluations、Tool use |
| `gh api repos/anthropics/courses/contents` | 列出 repo 根目錄結構 | 確認目錄布局 | 5 個課程目錄 + .gitignore + LICENSE + README.md |
| 讀取 5 門課程各自的 README.md | 了解各課程內容與目標 | 確認各課程的學習目標與適用對象 | 各課程 README 已取得，內容涵蓋從 API 基礎到工具使用的完整路徑 |
| 讀取 R1 最終報告 `output/22_anthropic-courses.md` | 確認 R1 是否已涵蓋使用者提問 | 判斷是否需要補充調研 | R1 報告 §5 已有 Q1-Q3 直接回答三個子問題 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo 歸屬（是誰） | 從 `gh repo view` 的 owner 欄位確認 | 明確：Anthropic 公司官方 repo，非第三方社群專案 |
| 業務場景 | 從 5 門課程 README 的學習目標與案例提取 | 5 門課程各自對應不同業務場景（API 串接、提示工程、垂直領域應用、品質評估、工具整合） |
| 加速 vs 品質 | 比對各課程內容定位 | 3 門偏品質（prompt engineering、real world prompting、evaluations），2 門偏加速（API fundamentals、tool use） |
| R1 報告涵蓋範圍 | 比對 §5 Q1-Q3 與使用者提問 | R1 報告已完整回答三個子問題，無需額外調研 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否需要額外調研 | (a) 已足夠，直接進入 Step 3 QA (b) 再搜尋外部資料補強 | (a) 已足夠，直接進入 Step 3 QA | R1 報告 §5 已完整回答三個子問題，無需重複調研 |
| 如何處理使用者「沒回答到」的感受 | (a) 在 Step 3 QA 中明確指出答案已在 §5 (b) 重新撰寫答案 | (a) 在 Step 3 QA 中明確指出答案已在 §5，並確認其完整性 | 答案已存在，重新撰寫是重複勞動；應在 QA 環節確認答案是否滿足使用者需求 |
