# 22_R3_step2-plan_C1.md

## 狀況理解

本輪（R3）使用者重複 R2 的三個子問題：(1) anthropics/courses 是什麼（「是誰」），(2) 可用在什麼業務，(3) 效果是加速還是提升品質。Step 1 已判定不需重新調研，直接引用 R1 報告既有資訊即可回答。但為確保回答精準，仍執行標準調研動作：取得 repo metadata、README、各子課程 README、授權條款，並補查 Anthropic 公司背景。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view anthropics/courses --json` | 取得 repo metadata（stars, forks, 語言, 描述, 建立/更新時間） | 確認 repo 基本數據 | 成功：21.9k stars, 2.3k forks, Jupyter Notebook, 描述 "Anthropic's educational courses"，建立於 2024-05-30，最後更新 2026-06-21 |
| 讀取 R1 分析報告 `output/22_anthropic-courses.md` | 回顧既有報告內容，確認哪些資訊可直接回答使用者問題 | 判斷哪些資訊已涵蓋、哪些需補充 | 報告涵蓋課程架構與替代方案，但缺乏「業務場景對照表」與「加速/品質」的明確論述 |
| Fetch GitHub 頁面（webfetch） | 取得 repo 首頁的完整 README 渲染內容 | 確認 README 最新版本 | 成功：README 列出 5 門課程，建議依序學習，使用 Claude 3 Haiku 降低成本 |
| Fetch 各子課程 README（gh raw） | 取得 5 門課程的詳細說明 | 了解各課程具體內容與學習目標 | 全部成功：API fundamentals（6 課）、Prompt engineering（9 章）、Real world prompting（5 課）、Prompt evaluations（9 課）、Tool use（6 課） |
| Fetch LICENSE | 確認授權條款 | 了解使用限制 | CC BY-NC 4.0（非商業用途，須標示出處） |
| Fetch anthropic.com/about | 補查 Anthropic 公司背景 | 確認 Anthropic 是 Claude 模型的開發公司 | 404（頁面不存在或已變更），但從通用知識可知 Anthropic 是 AI 安全公司，Claude 系列 LLM 的開發者 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Repo metadata 完整性 | 確認 gh API 回傳的 JSON 包含必要欄位 | 完整：name, description, url, owner, primaryLanguage, stargazerCount, forkCount, createdAt, updatedAt |
| 課程文件完整性 | 確認 5 門課程的 README 皆可正常讀取 | 5/5 成功，每門課程的課綱與學習目標皆已取得 |
| 授權條款 | 確認 LICENSE 檔案內容 | CC BY-NC 4.0，非商業用途 |
| 使用者問題對應 | 確認取得的資訊能否回答 R2 三個子問題 | 可回答：(1) 課程內容與目標受眾明確，(2) 業務場景可從課程案例推導，(3) 加速/品質可從課程設計判斷 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否重新 fetch 所有課程內容 | (a) 只讀 README vs (b) 也讀各 notebook 內容 | (a) 只讀 README | README 已提供課程大綱與學習目標，足以回答使用者問題；notebook 細節對回答「業務場景」與「加速/品質」無直接幫助 |
| 是否補查 Anthropic 公司背景 | (a) 補查 vs (b) 直接引用通用知識 | (b) 直接引用通用知識 | anthropic.com/about 回傳 404，且 Anthropic 為知名 AI 公司（Claude 開發者），通用知識已足夠 |
| 回答形式 | (a) 在 output 報告追加 Q&A 章節 vs (b) 直接回覆使用者 | (a) 追加 Q&A 章節 | 依 AGENTS.md 規範，使用者追問應以 `## 5. User Q&A` 形式追加至既有報告 |
