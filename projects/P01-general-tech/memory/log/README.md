# memory/log

> 執行過程記錄目錄。每個 step 一個 log（agent 動作總結，非 LLM 詳細產出）。
>
> 檔名規則：
> - `(pr-id)_R(round-id)_step1-intent.md` — Step 1 意圖理解
> - `(pr-id)_R(round-id)_step2-plan_(step-id).md` — Step 2 執行計劃（step-id = C1, C2...）
> - `(pr-id)_R(round-id)_step3-qa.md` — Step 3 品質保證
> - `(pr-id)_R(round-id)_step4-summary.md` — Step 4 總結
>
> 每個 log 格式固定（4 個通用 section）：
> ## 狀況理解 / ## 執行的動作與結果 / ## 動作結束後的現狀 / ## 其中的決斷點