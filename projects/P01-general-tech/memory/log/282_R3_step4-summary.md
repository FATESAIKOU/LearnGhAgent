# 282_R3_step4-summary.md

## 狀況理解

R3 為 Laya（`NandhaKishorM/laya`，HF `convaiinnovations/laya`）調研的**收尾輪**。使用者判**不採用（Reject）**並列 4 點：①比 Jev 只多了個框架、②準確度還差、③期待同類且更準的產品、④未來寫「收斂 LLM 不確定性」程式時再考慮。前 3 step 已完成：Step1 定調並對齊第二腦；Step2 C1 取回覆核證據（命題①②成立）與新負面事實 issue #963；Step3 將 R3 沉澱入報告 §4／§5（新增 Q6–Q9）。Step4 收斂整輪動作與待追問方向。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 綜整 Step1–3 logs 與報告 | 收斂本輪全貌 | 產出 summary | 完成，歸納 Reject 落定與素材抽取 |
| 確認 §5 序號接續、既有不刪 | 驗證交付完整性 | 全檔案存在 | Q6–Q9 已追加，Q1–Q5 與 §1–§4 保留 |
| 檢查禁用語、長度、觸發點標註 | 對齊 AGENTS.md | 合規 | 無「也許／我認為」；報告 39,219 bytes < 50,000 |

## 動作結束後的現狀

**本輪產出檔案清單：**
- 報告：`output/282_laya.md`（R3 更新 §4 收尾小節、追加 §5 Q6–Q9）
- logs：`memory/log/282_R3_step1-intent.md`、`282_R3_step2-plan_C1.md`、`282_R3_step3-qa.md`、`282_R3_step4-summary.md`

**核心結論：** Reject 落定——Laya 相對已判試用（Accept(Weak)）的 Jev，判斷品質未超越且跨任務／跨語言（尤其中文 feishu 20/64 vs 64/64）普遍落後，增益集中於系統層（可自架／可微調／可整合）。依骨幹「Reject≠沒價值」抽得素材：非自迴歸 encoder＋決策頭、proper scoring rule 的 RLCD 訓練目標、confidence（1−正規化熵／`answer_confidence`）、Router 與 `min_confidence` abstention。新負面事實 issue #963：`laya-train` 預設 4 epoch 對小資料集靜默坍縮。第 4 點「收斂 LLM 不確定性」與 `AiStorage` 的「收斂 AI」同詞不同義，屬新線，MyBrain `Laya` 零命中。

**待追問方向：**
- Laya 的 proper-scoring confidence 能否獨立移植到自兜 encoder＋head（收斂不確定性線）
- 中文／日文文脈下 router 覆蓋度與微調後精度是否足以落地
- `laya-train` 小資料集坍縮（#963）官方是否修正，影響自行復現可行性

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| R3 性質 | ①新調研 ②Reject 落定＋抽取＋記觸發點 | ② | 4 點皆判定與延伸，無新事實需求 |
| §5 是否觸發 | ①無質問句構不加 ②仍加 Q6–Q9 | ② | 4 點為對前輪結論的覆核，AGENTS.md 允許接續追加 |
| 是否推薦採用 | ①推薦為不確定性零件 ②只記錄素材 | ② | R3 已判不採用，不自作推薦 |
| summary 定位 | ①重述報告 ②收斂動作 | ② | step4 為「自己的動作總結」|
