# 140_R2_step1-intent.md

## 狀況理解

本輪（R2）為使用者對 R1 報告的追問。使用者提出 3 個問題：

1. **核心定位釐清**：Hallmark 到底是「撰寫好看網頁的工具」、「驗證網頁風格一致性的檢查器」、還是其他？使用者對 R1 報告中 Hallmark 同時具備「生成」與「審計」功能感到混淆，要求明確其核心 identity。
2. **自動套用行為**：若使用者未特別提及 Hallmark，安裝後 Claude Code / Opencode 是否會自動套用其 prompt？這涉及 Skill 的觸發機制是 opt-in 還是 opt-out。
3. **安裝步驟**：要求按照官方 best practice，給出安裝到 Claude Code / Opencode 的逐一步驟指令。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 PR body（R2 使用者提問） | 理解本輪追問的具體問題 | 確認 3 個問題的細節與語氣 | 成功取得：Q1 定位釐清、Q2 自動套用行為、Q3 安裝步驟 |
| 讀取 R1 產出（報告 + step logs） | 回顧已提供的資訊，確認哪些已回答、哪些需補充 | 避免重複回答，聚焦未覆蓋的面向 | 確認：R1 報告已說明 Hallmark 的 4 verbs 與架構，但未明確回答「核心 identity 是什麼」；未說明自動套用行為；未給出安裝步驟 |
| 讀取 AGENTS.md | 確認 Step 1 輸出格式規範 | 確保 log 符合 4-section 格式與 2000 字上限 | 已確認格式要求 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 使用者提問類型 | 判斷是否為 QA 觸發（質問型句構） | Q1 為定位釐清（非質問），Q2 為行為確認（非質問），Q3 為步驟請求（非質問）。三題均非「為何/憑什麼」的質問型句構，不觸發 §5 User Q&A 的追加規則 |
| R1 報告覆蓋缺口 | 比對 R1 報告與 R2 提問 | R1 報告 §3 詳述了機制但未給出「一句話定位」；未提及安裝後行為；未給出安裝指令 |
| 是否需要額外搜尋 | 判斷是否需查官方文件補安裝步驟 | 是。需查 GitHub README 的安裝說明，以及 Claude Code / Opencode 的 Skill 安裝 best practice |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| Q1 定位問題的處理方式 | (a) 直接給一句話定義 (b) 用對照表釐清生成 vs 審計 vs 驗證的差異 | (b) 對照表 | 使用者混淆的根源是 Hallmark 同時具備 Default（生成）、Audit（審計）、Redesign（重構）三個 verb，需用對照表明確區分各 verb 的角色，而非只給一個籠統定義 |
| Q2 自動套用行為的資訊來源 | (a) 從 README 推測 (b) 查 Claude Code / Opencode 官方文件 | (b) 查官方文件 | 自動套用行為取決於 Claude Code / Opencode 的 Skill 載入機制，非 Hallmark 本身能決定。需查兩邊的官方文件確認 |
| Q3 安裝步驟的資訊來源 | (a) 僅依賴 README 的 `npx hallmark` (b) 查 Claude Code / Cursor 的 Skill 安裝官方文件 | (b) 查官方文件 | README 只寫了 `npx hallmark`，但使用者要求「官方 best practice，指令一步一步講」，需查 Claude Code 與 Opencode 的 Skill 安裝文件補足細節 |
