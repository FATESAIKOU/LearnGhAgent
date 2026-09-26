# 282_R2_step3-qa.md

## 狀況理解

- R2 追問輪 Step 3。使用者 5 問為界定向（Q1 模型 vs 軟體／Q2 成本／Q3 與 Jev 關係／Q4 效能語意）＋判準向（Q5 借模型層或系統層）。
- 本 step 須：把 5 問沉澱為 `output/282_laya.md` 的 `## 5. User Q&A`（5 個獨立 QA），既有 §1–§4 不刪、可補；並對照第二大腦寫 §4 的替代方案與 DA 表。
- Step2 C1 已取得 Q1–Q5 硬事實與獨立第三方 eval；Step1 已確認 MyBrain `laya` 零命中、Q5 判準命中骨幹。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀既有報告 `output/282_laya.md`（163 行） | 確認可追加位置與不刪既有 | 鎖定 §5 落點 | 報告原無 §5（R1 無提問） |
| mybrain-read 更新鏡像 @4ce59b3、讀骨幹 | 取 §4 對照與 Q5 判準 | 不以通則回答 | 骨幹 12 檔；讀 `技術取捨準則`／`判定總表`／`下一步清單`／`核心價值觀`／`統一的兩端稅` |
| 讀 `Jev`／`DeepSeek V4`／`needle` 原檔 | 取判定與信任層級 | 逐則標 URL＋層級 | Jev 試用（agent draft）；DeepSeek V4 降低 Model Routing（human stable）；needle 不採用（process draft） |
| 補查 HF API＋pyproject＋README＋`common.py`＋`staged-adoption.md` | 驗證 Q1/Q2/Q3/Q5 硬事實 | 不引二手 | 三權重＝三個獨立 HF repo（皆 apache-2.0/commercial-use）；`common.py` 見 `proper_reward`；deps 無雲端 SDK |
| 追加 §5（Q1–Q5）並補正 §3 權重位置、§4 `統一的兩端稅` URL | 沉澱本輪 | 5 獨立 QA、既有不刪 | 完成；報告 17,636 字 < 50000 |
| 軟性驗證（讀 `judge/` 觀點逐節自評） | 對齊格式與禁用語 | 合規 | 4 section 齊、Q 數 5；無「也許／我認為」 |

## 動作結束後的現狀

**產出報告：** `output/282_laya.md`（檔名沿用 R1）。本輪變更：
- 新增 `## 5. User Q&A`（Q1–Q5，5 個獨立 QA，序號由 1 起）。
- §3 新增「三個 checkpoint 的實體位置」小節（修正 repo 歸屬）。
- §4 對照表補 `統一的兩端稅` 完整 GitHub URL 與 `generated.by`／`status`。
- 檔頭改註 R1/R2 產出關係。

**§4 第二大腦對照（本輪實際引用）：** `技術取捨準則`（骨幹／`claude-code/opus-5`＋`draft`，AI 草稿未 review）、`DeepSeek V4`（`human:fatesaikou`＋`stable`）、`Switchyard`／`OmniRoute`（皆不採用）、`needle`、`Jev`（`agent:personal-assistant`＋`draft`）、`下一步清單`（`claude-code/opus-5`＋`draft`）。`laya` 本身 **MyBrain 零命中**，已明寫無既有判定。

**衝突聲明：** Laya 的 `router_questions()` preset（small vs frontier）撞使用者 stable 的「降低 Model Routing 優先級」；語言 Router 不在此列。

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| §4 替代方案列法 | ①照通則列 Jev/needle 等 ②對照 MyBrain 判定後再列 | ② | 任務明定對照；`needle` 不採用的理由需照判定語意轉述 |
| Q2 付費判定佐證 | ①只引 README 自陳 ②加 pyproject deps 全文掃描 | ② | 「有無付費」需可證偽：無計費 SDK 為硬證據 |
| Q5 是否照使用者「沒必要學」結論 | ①順著答不必學 ②分層：架構不必、訓練目標與系統層可抽 | ② | 使用者前提只在架構層成立；骨幹 `技術取捨準則` 要求抽「方案方向」，不分層會誤導 |
| 既有 §1–§4 | ①重寫 ②保內容＋局部補正 | ② | AGENTS.md：不刪既有內容 |
| 是否另開報告檔 | ①新檔 ②沿用 `282_laya.md` | ② | 任務明定檔名不變 |
