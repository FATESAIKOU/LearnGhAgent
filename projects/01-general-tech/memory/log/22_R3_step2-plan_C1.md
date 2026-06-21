# 22_R3_step2-plan_C1.md

## 狀況理解

本 sub-step 為 R3 的 Step 2 第一個調研動作。R3 使用者重複追問「anthropics/courses 是誰，可以用在什麼業務，加速還是提升品質」，表示 R1 報告與 R2 回答未從「業務定位」與「價值維度」角度回應。本 step 的目標是取得 repo 的完整 metadata、README、各子課程 README，以及 Anthropic 官方對該 repo 的定位說明，為後續以業務視角重新組織回答做準備。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view anthropics/courses --json` | 取得 repo 的結構化 metadata | 獲得 stars、forks、語言、建立時間、描述等數據 | 成功取得：21.9k stars、2.3k forks、Jupyter Notebook 99.9%、建立於 2024-05-30、描述為 "Anthropic's educational courses" |
| 擷取 GitHub 頁面（webfetch） | 確認 repo 的目錄結構與檔案列表 | 了解 repo 包含哪些課程目錄 | 確認 5 個課程目錄：anthropic_api_fundamentals、prompt_engineering_interactive_tutorial、real_world_prompting、prompt_evaluations、tool_use |
| 擷取 README.md | 取得 repo 的頂層說明 | 了解課程建議順序與整體定位 | README 明確建議依序學習 5 門課程，並註明使用 Claude 3 Haiku 以降低學員 API 成本 |
| 擷取 5 個子課程的 README.md | 了解各課程的具體內容與學習目標 | 掌握各課程的教學範圍與目標受眾 | 成功取得所有課程的目錄結構與學習目標（詳見下方摘要） |
| 搜尋 Anthropic 官方對 courses 的介紹文章 | 確認 Anthropic 對該 repo 的官方定位 | 取得官方說法以回答「是誰」的問題 | 404（無專屬介紹文章），但 docs.anthropic.com 的 use-case guides 頁面顯示 Claude 的典型業務場景：ticket routing、customer support、content moderation、legal summarization |

### 各課程 README 摘要

| 課程 | 目標受眾 | 核心內容 | 筆記本數 |
|---|---|---|---|
| API fundamentals | 初學者 | API key、messages 格式、模型參數、串流、vision | 6 |
| Prompt engineering interactive tutorial | 初～中階 | 9 章從基本結構到複雜 prompt，含練習題與解答 | 9 章 + 附錄 |
| Real world prompting | 中～高階（需先完成上述課程） | 醫療 prompt、通話摘要、客服機器人等真實案例 | 5 |
| Prompt evaluations | 中～高階 | 人工評估、程式評分、promptfoo 整合、模型評分 | 9 |
| Tool use | 中～高階 | 工具使用概論、強制 JSON、多工具聊天機器人 | 6 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo 身份定位資訊 | 比對 README 描述與 gh metadata | 描述僅 "Anthropic's educational courses"，無更詳細的官方定位說明。Anthropic 未為此 repo 發布專屬介紹文章 |
| 課程內容完整性 | 確認所有 5 個課程目錄均有 README | 完整，無遺漏 |
| 業務場景相關資訊 | 從 docs.anthropic.com 的 use-case guides 取得 | Claude 的典型業務場景包括：ticket routing、customer support chatbot、content moderation、legal summarization。這些場景在 courses 的 real_world_prompting 與 tool_use 課程中有對應案例 |
| 價值維度（加速 vs 品質）判斷所需資訊 | 檢視課程目標描述 | 各課程目標同時涵蓋「加速」（更快上手 API、更快建置 prompt）與「提升品質」（更好的 prompt 設計、系統化評估） |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否需要爬取各課程的 .ipynb 內容 | 是（完整爬取）vs 否（僅 README 已足夠） | 否 | 使用者問的是「身份定位、業務場景、加速/品質」，這些從 README 的課程目標與目錄結構即可判斷，不需深入 notebook 內的程式碼細節 |
| 是否需要查詢 Anthropic 公司背景 | 是（說明 Anthropics 是誰）vs 否（僅專注 repo） | 是，但留待 C2 或回答階段 | 使用者問「anthropics/courses 是誰」，需要先說明 Anthropic 公司定位，再說明 courses repo 的角色。但本 step 僅為資料收集，分析與回答在後續 step |
| 是否需要查詢競爭對手的類似課程 | 是（補 DA 表）vs 否（R1 報告已有 DA 表） | 否 | R1 報告 §4 已有 OpenAI Cookbook、Google Vertex、LangChain、DeepLearning.AI 的 DA 表，本輪不需重複 |
