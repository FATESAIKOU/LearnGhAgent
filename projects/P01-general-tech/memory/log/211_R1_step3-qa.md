# 211_R1_step3-qa.md

## 狀況理解

Step 1/2 已確認標的為 **AirLLM**（lyogavin/airllm，低顯存 LLM 推理工具），並從原始碼確認核心機制（meta device + forward hook 逐層 stream + prefetch + per-expert streaming）。Step 3 任務：基於調研資料產出最終分析報告（`output/211_AirLLM.md`），並對照第二大腦的既有評估與技術取捨準則，確保 §4 替代方案不照通則亂推。本輪為 R1 首次產出，無 User Q&A。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取技術取捨準則（骨幹） | 確認使用者技術判準 | 避免照通則推薦 | 確認「理解優先、MVP→Feature 閘門、Reject≠沒價值」 |
| 讀取判定總表（骨幹） | 確認替代方案是否已評估 | 找出既有判定 | 79 筆中無 AirLLM；llama.cpp/vllm=Reject(Reserve)、Ollama=採用 |
| 讀取 llama.cpp - vllm 評估全文 | 取得替代方案既有判定與理由 | 對照 AirLLM 切入點 | 確認「目前環境挺極限的，感覺目前用不上」 |
| 讀取專案現況表、下一步清單 | 確認 AirLLM 是否與 workflow 相關 | 判斷導入價值 | 無 AirLLM 相關專案或下一步 |
| 產出分析報告 | 交付最終成果物 | 回答 4 個必要 section | 寫入 `output/211_AirLLM.md` |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 產出的報告檔名 | 確認路徑與命名 | `output/211_AirLLM.md`，含 ## 1.~## 4. 四個必要 section |
| 本輪變更摘要 | 首次產出 | 建立完整分析報告；§4 對照第二大腦（llama.cpp/vllm Reject、Ollama 採用），並明確標出與「目前用不上」判定的衝突 |
| 報告長度 | 檢查字數 | 約 4,000 字，遠低於 50,000 上限 |
| §4 對照完整性 | 確認替代方案有標 GitHub URL 與信任層級 | llama.cpp/vllm（human/stable）、Ollama（human/stable）、技術取捨準則（AI draft 已註明未 review） |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| §4 替代方案來源 | (A) 只照通則列 (B) 對照第二大腦既有評估 | B | 使用者對 llama.cpp/vllm 已判 Reject(Reserve)，照通則推薦會推到他反對的方向；需先對照 |
| 是否指出衝突 | (A) 隱藏衝突 (B) 明確標出 | B | 依 mybrain-read 規則，與結論衝突正是查詢最有價值處；AirLLM 與 llama.cpp 同領域，需點明「目前用不上」的既有立場 |
| 對 AirLLM 的定位 | (A) 推薦導入 (B) 定位為「可抽取的需求理解/方案方向」 | B | 依技術取捨準則「Reject≠沒價值」，AirLLM 的逐層 offload + per-expert streaming 是可抽取的方向，而非建議導入 |
| 是否含 User Q&A | (A) 加空節 (B) 不加 | B | R1 無使用者提問，依 AGENTS.md 規則「無提問則無此節」 |
