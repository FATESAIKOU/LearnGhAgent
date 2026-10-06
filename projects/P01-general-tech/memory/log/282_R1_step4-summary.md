# 282_R1_step4-summary.md

## 狀況理解

R1 首輪，標的 **Laya**（`NandhaKishorM/laya`，HF `convaiinnovations/laya`）——Jev／System 1 Model 的開源復刻，PR #282，Closes #273。使用者附帶影片觀點：Jev「放棄自由生成、直接回傳結構化判斷」、快 20×／成本 1%／零幻覺有場景限制（格式保證正確、答案不保證）、Laya 發布的是訓練碼非 Jev 權重、作者對照數字取自第三方未統一基準。前 3 step 已完成：Step 1 定調並對齊第二大腦既有 Jev 判定；Step 2 取回 repo 硬事實；Step 3 產出報告並自評。Step 4 收斂整輪動作與待追問方向。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 綜整 Step1~3 logs 與報告 | 收斂本輪全貌 | 產出 summary | 完成，歸納三差異點：非自迴歸決策引擎、RLCD＋proper scoring、可下載微調 |
| 確認產出檔案齊全 | 驗證交付完整性 | 全檔案存在 | report + 4 step logs（含本檔）皆已寫入 |
| 檢查禁用語與 §5 | 對齊 AGENTS.md | 合規 | 無禁用語；R1 無提問故不建 §5 |

## 動作結束後的現狀

**本輪產出檔案清單：**
- 報告：`output/282_laya.md`
- logs：`memory/log/282_R1_step1-intent.md`、`282_R1_step2-plan_C1.md`、`282_R1_step3-qa.md`、`282_R1_step4-summary.md`

**核心結論：** Laya 為非自迴歸 System 1 決策引擎，單次 forward pass 由 encoder＋決策頭輸出三原語（choice／score／noul）；訓練用 RLCD（REINFORCE＋group-mean baseline）配嚴格 proper scoring rule；三 checkpoint（421M 英文／322M 多語言／421M 微調版）；可 pip／CLI／HTTP（相容 Jev `/v1/systemone`）／MCP／LangChain 部署。自我揭露 base zero-shot 近隨機、`score` 最弱、非英文 checkpoint 崩且高信心。與已判「試用」的 Jev 同構想，但 Laya 是**判斷零件**而非執行者；其 router 僅在 forward 前選 checkpoint，非使用者已放棄的 Model Router。快 6–7× 為第三方量測、未統一基準，不可搬用。

**待追問方向：**
- 「格式保證正確、答案不保證」在 Laya 上的實測驗證方法（confidence 閾值分流是否可靠）
- Laya 能否替代 Jev 成為第二大腦「測試能力邊界」下一步的執行載體
- 訓練配方未公開（資料集僅見 notebook 載入 `LocalLLaMA/typed-decisions`），是否值得自行復現

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| summary 定位 | 重述報告／收斂動作 | 收斂動作 | step4 是「自己的動作總結」，非重產報告 |
| 待追問方向 | 寫「無」／列張力點 | 列 3 項張力點 | 校準驗證、Jev 替代性、訓練配方是使用者最可能追問的缺口 |
| 長度控制 | 詳細／精簡 | 精簡至 2000 字內 | 硬性驗證拒絕超長，summary 不需承載報告內容 |
