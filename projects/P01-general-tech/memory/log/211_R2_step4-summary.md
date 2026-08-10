# 211_R2_step4-summary.md

## 狀況理解

R2 為使用者對 R1 報告（AirLLM）的追問，2 個問題皆以「RTX 2070S + 64GB RAM 跑 deepseek-v4-flash:0731」為前提：Q1 可行性、Q2 秒速/context 試算。Step 1~3 已完成：確認標的、補齊「模型×框架×硬體」資料、將 QA 沉澱進報告 §5 並補 §4.5 硬體對照。本 step 總結本輪。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 產出 Step 1 log | 記錄意圖理解 | 確認標的與兩問語意 | 標的 AirLLM+deepseek-v4-flash:0731@2070S；對照第二大腦 llama.cpp/vllm=Reject(Reserve) |
| 產出 Step 2 log（C1） | 記錄資料取得 | 對齊模型/框架/硬體 | 確認 291B params、hybrid attention、FP4+FP8、V4 官方未宣告支援、2070S 需 fp16、issue #299「可跑但極慢」 |
| 產出 Step 3 log | 記錄 QA 與報告更新 | 交付可掃讀量化回答 | 更新 `output/211_AirLLM.md`：新增 §4.5 + §5（Q1、Q2） |
| 產出本 Step 4 log | 總結本輪 | 收斂產出清單 | 本檔 |

## 動作結束後的現狀

**本輪產出檔案清單：**

| 檔案 | 內容 |
|---|---|
| `output/211_AirLLM.md` | 最終報告（新增 §4.5 硬體對照 + §5 User Q&A 兩條，§1~§4.4 保留） |
| `memory/log/211_R2_step1-intent.md` | Step 1 意圖理解 log |
| `memory/log/211_R2_step2-plan_C1.md` | Step 2 資料取得 log |
| `memory/log/211_R2_step3-qa.md` | Step 3 QA log |
| `memory/log/211_R2_step4-summary.md` | 本總結 log |

**待追問方向：** 無（兩問均已量化回答並標誤差）。

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| Q1 答法 | (A) 直接給可/不可 (B) 拆「能載入/能正確/能用得好」 | B | 需區分可行性與可用性；V4 非官方支援 + 社群 TPS 極慢 |
| Q2 估算法 | (A) 引社群定性 (B) 自權重×I/O 頻寬量化推估 | B | 使用者要求「試算」，給數字並標誤差 |
| §4 對照 | (A) 照通則 (B) 對照第二大腦既有判定 | B | 使用者「比起我之前檢討過的方案」，引用 Reject(Reserve) 避免衝突 |
| 硬體資料 | (A) 通用知識 (B) 查 MyBrain | B 後接 A | 第二大腦無硬體欄，2070S 規格自通用知識取得，明寫來源 |
| 是否更新 §1~§4 | (A) 只加 §5 (B) 補 §4.5 | B | R2 為硬體×模型實用追問，§4.5 讓對照落到實用層 |
