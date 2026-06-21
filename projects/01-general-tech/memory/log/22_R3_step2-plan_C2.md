# 22_R3_step2-plan_C2.md

## 狀況理解

C1 已完成資料收集。本 sub-step 的目標是：從「業務定位」與「價值維度」角度分析 anthropics/courses，回答使用者的三個核心問題：
1. **anthropics/courses 是誰** — 身份定位（非技術架構）
2. **可以用在什麼業務** — 具體業務場景
3. **加速還是提升品質** — 價值維度判斷

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 分析 Anthropic 公司定位 | 回答「anthropics 是誰」 | 說明 Anthropic 是 Claude LLM 的開發公司 | Anthropic 是一家 AI 安全公司，2021 年由前 OpenAI 員工創立，主要產品為 Claude 系列 LLM。courses 是其官方教育資源 |
| 分析 courses repo 的業務定位 | 回答「courses 是誰」 | 說明 courses 是 Anthropic 的官方教育入口 | courses 不是產品、不是工具、不是框架，而是「官方教材」。它的角色是降低 Claude 生態系的採用門檻 |
| 對應課程內容到業務場景 | 回答「可以用在什麼業務」 | 列出具體業務場景 | 從課程案例與 docs.anthropic.com 的 use-case guides 交叉比對，得出 6 個可直接對應的業務場景 |
| 分析各課程的價值維度 | 回答「加速還是提升品質」 | 判斷每個課程的價值歸屬 | 5 門課程中，2 門偏向「加速」，2 門偏向「提升品質」，1 門兼具兩者 |

### 業務場景對應表

| 業務場景 | 對應課程 | 課程中的具體案例 |
|---|---|---|
| 客服自動化（Customer Support Chatbot） | real_world_prompting（Lesson 5）、tool_use（Lesson 6） | 客服機器人 prompt walkthrough、多工具聊天機器人 |
| 通話摘要與紀錄（Call Summarization） | real_world_prompting（Lesson 4） | 通話摘要 prompt walkthrough |
| 醫療問診輔助（Medical Intake） | real_world_prompting（Lesson 2） | 醫療 prompt walkthrough |
| 內容審核（Content Moderation） | prompt_engineering（Chapter 9 進階案例） | 複雜 prompt 建構練習 |
| 法律文件摘要（Legal Summarization） | prompt_engineering（Chapter 9） | 法律服務複雜 prompt |
| Prompt 品質保證（Evaluation / Regression Testing） | prompt_evaluations（全部 9 課） | 從人工評估到 promptfoo 自動化回歸測試 |

### 價值維度分析

| 課程 | 加速（Speed） | 提升品質（Quality） | 判斷依據 |
|---|---|---|---|
| API fundamentals | ✅ 主要 | — | 讓開發者「更快」上手 Claude SDK，縮短從 0 到第一個 API call 的時間 |
| Prompt engineering | ✅ 主要 | ✅ 次要 | 提供「現成可用的 prompt 模板與技巧」，加速開發；同時透過系統化方法提升 prompt 品質 |
| Real world prompting | — | ✅ 主要 | 以真實案例展示如何建構「生產級」prompt，直接提升產出品質 |
| Prompt evaluations | — | ✅ 主要 | 教導如何量化評估 prompt 品質，建立回歸測試機制，直接提升品質 |
| Tool use | ✅ 主要 | — | 讓開發者「更快」實現工具呼叫、結構化輸出等進階功能，避免從零摸索 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 業務場景的完整性 | 比對課程案例與 docs.anthropic.com 的 use-case guides | 6 個場景均有課程對應，但 courses 的案例偏向「教學示範」而非「可直接部署的生產程式碼」 |
| 加速/品質判斷的客觀性 | 以課程目標描述為依據，非主觀推測 | 各課程的 README 目標描述可直接對應到加速或品質提升 |
| 是否回答了使用者的三個問題 | 對照使用者原文 | 三個問題均已涵蓋：身份定位（C2 §1）、業務場景（C2 §2）、價值維度（C2 §3） |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 業務場景的呈現方式 | 條列式 vs 表格 | 表格 | 表格可同時呈現「場景」、「對應課程」、「具體案例」三個維度，掃讀效率最高 |
| 是否需要區分「課程內容」與「可直接部署的解決方案」 | 是 vs 否 | 是 | 使用者可能誤以為 courses 提供可直接上線的業務解決方案，需明確區分「這是教材，不是產品」 |
| 加速/品質的判斷粒度 | 整體 repo 一個結論 vs 各課程分別判斷 | 各課程分別判斷 | 5 門課程的價值維度不同，統一結論會失真 |
