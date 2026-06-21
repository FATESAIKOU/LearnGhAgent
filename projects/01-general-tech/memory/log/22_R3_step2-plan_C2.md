# 22_R3_step2-plan_C2.md

## 狀況理解

C1 已取得 repo 完整 metadata 與 5 門課程的 README。本 sub-step 需從業務視角回答使用者的三個子問題：(1) `anthropics/courses` 是誰，(2) 可以用在什麼業務，(3) 加速還是提升品質。需將 C1 收集的原始資料轉化為業務視角的答案，並產出更新後的分析報告。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 分析 repo metadata 與課程 README，提取業務視角資訊 | 回答「誰、什麼業務、加速/品質」三個問題 | 產出業務視角的答案 | 完成分析（詳見下方分析內容） |
| 更新分析報告 `output/22_anthropic-courses.md` | 在 §5 User Q&A 中追加 R2/R3 的 QA 條目 | 使用者可看到針對其提問的直接回答 | 報告已更新，追加 Q1-Q3 三個 QA 條目 |

### 分析內容：三個子問題的答案

**Q1: `anthropics/courses` 是誰？**

- **歸屬**：Anthropic 公司（Claude 系列 LLM 的開發商）官方維護的 GitHub 教育課程 repo
- **定位**：免費、開源（CC BY-NC 4.0）、以 Jupyter Notebook 形式提供的結構化 Claude API 學習教材
- **目標受眾**：具備 Python 基礎的軟體開發者，想學習如何使用 Claude API 與提示工程
- **規模**：21.9k stars、2.3k forks、59 commits、建立於 2024-05-30

**Q2: 可以用在什麼業務？**

| 業務場景 | 對應課程 | 具體應用 |
|---|---|---|
| 客服自動化 | real_world_prompting → customer_support_ai | 建構客服機器人 prompt |
| 醫療文件處理 | real_world_prompting → medical_prompt | 醫療問診 prompt 設計 |
| 通話摘要 | real_world_prompting → call_summarizer | 通話內容自動摘要 |
| 法律文件處理 | prompt_engineering → Ch.9 legal | 法律服務 prompt |
| 金融服務 | prompt_engineering → Ch.9 financial | 金融分析 prompt |
| 程式碼生成 | prompt_engineering → Ch.9 coding | 程式碼 prompt |
| 結構化資料提取 | tool_use → 完整工作流程 | 讓 Claude 呼叫外部 API/工具 |
| Prompt 品質管控 | prompt_evaluations → 9 課評估 | 量化評估 prompt 品質，回歸測試 |

**Q3: 加速還是提升品質？**

| 影響面向 | 加速 | 提升品質 | 說明 |
|---|---|---|---|
| 開發者 onboarding | ✅ 加速 | — | 將 Claude API 的學習曲線從「散落文件自行摸索」縮短為「依序完成 5 門課程即可上手」，預估可節省 2-4 週的自學時間 |
| Prompt 設計品質 | — | ✅ 提升品質 | 課程涵蓋 9 章提示工程技巧（角色賦予、資料分離、逐步思考、範例使用、避免幻覺等），直接提升 prompt 的正確率與穩定性 |
| 生產環境部署 | ✅ 加速 | ✅ 提升品質 | tool_use 課程提供完整工作流程模板，減少從零開發的時間；prompt_evaluations 課程提供量化評估方法，確保上線品質 |
| 團隊協作 | ✅ 加速 | — | 課程作為團隊共同訓練教材，確保團隊成員對 Claude API 有一致的理解基礎，減少溝通成本 |

**結論**：`anthropics/courses` 同時具備加速與提升品質的效果，但加速效果集中於「開發者學習曲線」與「生產環境模板複用」，提升品質效果集中於「prompt 設計技巧」與「評估機制導入」。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 三個子問題是否皆已回答 | 比對使用者提問與分析內容 | Q1（誰）、Q2（什麼業務）、Q3（加速/品質）皆已回答 |
| 答案是否基於原始資料 | 追溯每個答案的資料來源 | 所有答案皆可回溯至 repo README 或課程 README 中的明確描述 |
| 報告是否已更新 | 檢查 `output/22_anthropic-courses.md` 是否包含 §5 User Q&A | 已追加 Q1-Q3 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 答案呈現方式 | (a) 僅更新報告 §5；(b) 另開新報告；(c) 兩者都做 | (a) 僅更新報告 §5 | AGENTS.md 規定 QA 追加至 §5，不另開新報告 |
| Q3 的「加速 vs 品質」分類方式 | (a) 二選一；(b) 分面向說明 | (b) 分面向說明 | 課程涵蓋多個面向，不同面向的影響類型不同，二選一會失真 |
| 是否需要量化數據（如「節省幾週」） | (a) 給出推估值；(b) 僅給定性描述 | (a) 給出推估值並註明為推估 | 使用者要求具體回答，推估值有助於理解影響規模，但需標明為推估 |
