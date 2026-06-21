# 22_R3_step2-plan_C1.md

## 狀況理解

本 sub-step 為 R3 的 Step 2 第一個子步驟（C1）。R3 使用者重複 R2 的三個子問題：(1) `anthropics/courses` 是什麼（「是誰」），(2) 可以用在什麼業務，(3) 是加速還是提升品質。使用者認為 R2 未回答到問題。C1 的任務是取得 repo metadata 與主要文件，為後續回答這三個問題做準備。R1 報告已涵蓋課程架構與替代方案，但缺乏「業務視角 × 加速/品質」的框架。C1 不需重新做 R1 的完整調研，而是針對 R3 意圖補足資訊。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view anthropics/courses --json` | 取得 repo metadata（stars, forks, 語言, 授權, 更新時間等） | 確認 repo 的基本屬性與活躍度 | 21931 stars, 2325 forks, 主要語言 Jupyter Notebook, 最後推送 2025-11-13, 授權 Other |
| `gh api repos/anthropics/courses/readme` + base64 decode | 取得 README.md 全文 | 了解 repo 的定位、課程列表與建議學習順序 | 5 門課程：API fundamentals → Prompt engineering → Real world prompting → Prompt evaluations → Tool use；使用 Claude 3 Haiku 降低學員成本 |
| `gh api repos/anthropics/courses/contents` | 列出 repo 根目錄結構 | 確認目錄組織方式 | 5 個課程目錄 + README.md + LICENSE + .gitignore |
| 逐一讀取 5 個課程的 README.md | 了解各課程的學習目標與內容範圍 | 取得各課程的詳細描述，用於判斷業務適用場景 | 各課程 README 已取得（見下方摘要） |
| 讀取 R1 最終報告 `output/22_anthropic-courses.md` | 確認 R1 已產出的分析內容 | 避免重複調研，聚焦於 R3 的資訊缺口 | R1 報告已說明課程架構、核心機制、替代方案，但未以「業務場景 × 加速/品質」框架回答 |

### 各課程 README 摘要

| 課程 | 學習目標 | 內容 |
|---|---|---|
| API fundamentals | 掌握 Claude SDK 基本操作 | 6 個 notebook：API key → messages 格式 → 模型比較 → 參數 → 串流 → vision |
| Prompt engineering | 掌握提示工程最佳實務 | 9 章（初級 3 + 中級 3 + 進階 3 + 附錄），含 Example Playground |
| Real world prompting | 將提示技巧應用於真實場景 | 5 個案例：醫療 prompt、客服機器人、通話摘要、提示工程流程、提示回顧 |
| Prompt evaluations | 量化評估 prompt 品質 | 9 課：評估概論 → Workbench → 程式評分 → 分類評估 → promptfoo 整合 |
| Tool use | 讓 Claude 呼叫外部工具 | 6 課：概論 → 第一個工具 → 強制 JSON → 完整工作流程 → 工具選擇 → 多工具聊天機器人 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Repo metadata 完整性 | 確認已取得 stars, forks, 語言, 授權, 更新時間, 描述 | 完整取得 |
| 課程內容覆蓋 | 確認已讀取所有 5 門課程的 README | 完整取得 |
| R1 報告與 R3 需求的差距 | 比對 R1 報告內容與 R3 提問 | R1 報告未回答：(a) repo 的定位（官方教學資源 vs 產品/工具），(b) 適用的業務場景條列，(c) 加速開發 vs 提升品質的具體貢獻 |
| 是否需要額外調研 | 判斷是否需 fetch 更多資料（如各 notebook 內容、外部合作頁面） | 暫不需要。README 層級的資訊已足夠回答 R3 的三個問題。若後續使用者追問特定課程細節，再深入 notebook 內容 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研深度 | (a) 只讀 README, (b) 深入讀取各 notebook 內容 | 只讀 README | R3 的問題是「這是什麼 / 業務用途 / 加速或品質」，屬於定位與應用層級的問題，README 層級資訊已足夠。notebook 細節屬於「如何實作」層級，非本輪需求 |
| 是否需要 fetch 外部資源（AWS Workshop, Google Vertex 版本） | (a) 需要, (b) 不需要 | 不需要 | 外部合作版本僅是同一課程的不同部署平台，不影響對 repo 本質的理解 |
| 是否需要搜尋 Anthropic 官方對該 repo 的定位說明 | (a) 需要, (b) 不需要 | 不需要 | README 第一句 "Anthropic's educational courses" 已明確定位 |
