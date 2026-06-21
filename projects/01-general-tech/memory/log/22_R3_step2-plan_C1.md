# 22_R3_step2-plan_C1.md

## 狀況理解

本輪（R3）使用者重複追問兩個具體問題：(1) anthropics/courses 是誰、(2) 可以用在什麼業務、加速還是提升品質。R1 報告 §1-§4 未直接回答這兩個問題。本 sub-step 為 Step 2 的第一個動作：取得 repo metadata、README 與各子課程 README，釐清「誰」與「業務場景」。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view anthropics/courses --json` | 取得 repo metadata（owner、stars、語言、授權等） | 確認 owner 為 anthropics（Anthropic 公司），語言為 Jupyter Notebook，21.9k stars | 成功取得完整 metadata |
| 讀取 GitHub repo 首頁 | 取得 README.md 內容 | 確認 repo 描述為 "Anthropic's educational courses"，含 5 門課程列表 | 成功取得 README |
| 讀取 5 個子課程的 README.md | 了解各課程內容與目標 | 確認課程涵蓋 API 基礎、提示工程、真實世界提示、評估、工具使用 | 5 份 README 全部成功取得 |
| 讀取 R1 最終報告 | 回顧已產出的分析內容 | 確認報告中未直接回答「是誰」與「業務場景加速/品質」 | 報告 84 行，無 §5 Q&A 節 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 「是誰」的答案素材 | 從 repo owner 與 README 確認 | owner 為 `anthropics`（Anthropic 公司），repo 為官方維護的免費教育課程 |
| 「業務場景」的答案素材 | 從 5 門課程 README 提取 | 各課程明確列出目標學員與應用場景（API 整合、提示工程、客服機器人、醫療 prompt、通話摘要、評估自動化、工具呼叫） |
| 「加速還是品質」的答案素材 | 從課程設計判斷 | 課程同時涵蓋加速（API 基礎、tool use 工作流）與品質（prompt engineering、evaluations）兩個面向 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否需要補查 Anthropic 公司背景 | 補查 vs 不補查 | 不補查 | 使用者問的是「anthropics/courses 是誰」，指 repo 本身而非 Anthropic 公司；repo owner 資訊已足夠回答 |
| 是否需要補查各課程 notebook 細節 | 讀取全部 notebook vs 僅讀 README | 僅讀 README | 使用者問業務場景與加速/品質，README 的課程描述已足夠判斷，不需深入 notebook 程式碼 |
