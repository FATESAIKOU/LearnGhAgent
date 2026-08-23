# 242_R4_step4-summary.md

## 狀況理解

R4 是 R3 後的追問，標的仍為 Switchyard（NVIDIA-NeMo）。使用者質問「反向接法」（Switchyard 指到 OmniRoute）的意義，並列 2 個候選猜測：① 是否因為 OllamaCloud/Claude 訂閱掛不進 OmniRoute？② 是否效能議題。質問型句構觸發 §5 User Q&A。已完成 Step 1（意圖）、Step 2（C1 補查）、Step 3（QA 更新報告）。本 step 總結整輪。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 確認 Step 1-3 產出 | 盤點本輪成果 | 掌握完整交付 | 3 個 step log + 更新後報告齊全 |
| 撰寫本 summary log | 收斂整輪 | 產出 Step 4 總結 | 完成本檔 |

## 動作結束後的現狀

**本輪產出檔案清單：**
- 分析報告：`output/242_switchyard.md`（R4 更新：§5 新增 Q7，header 註記；§1-§4 未改）
- Step 1 log：`memory/log/242_R4_step1-intent.md`
- Step 2 log：`memory/log/242_R4_step2-plan_C1.md`
- Step 3 log：`memory/log/242_R4_step3-qa.md`
- Step 4 log：`memory/log/242_R4_step4-summary.md`（本文件）

**本輪核心結論（Q7）：**
- 猜測①證偽：Claude 訂閱（Tier 1）+ OllamaCloud（API key）皆可掛進 OmniRoute。
- 猜測②半對但因果反：Switch 是多一跳 + judge 額外 call，非加速。
- 意義＝唯一手動加的「weak/strong 路由政策層」；與 DeepSeek V4 stable「降低 Model Routing 優先級」直接衝突；若只要統一 endpoint+fallback，OmniRoute 已全包。

**待追問方向：**
- 是否要實測反向接法在 claudecode/opencode 實際承接（含 OllamaCloud/Claude 上游指法驗證）
- 是否要深挖 OmniRoute 免費 provider pool 額度上限與穩定性
- 是否要評估 Switch 路由演算法（llm_classifier/stage_router）成本與副作用

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| R4 是否觸發 Q&A | 否 / 是 | 是 | 質問型句構（「意義在哪」「是因為…還是…」） |
| 回答主軸 | 只答意義 / 逐一驗證 2 猜測 | 逐一驗證 2 猜測 | 用戶明列 2 具體猜測，須先證偽/證實再收窄 |
| 是否查第二大腦 | 否 / 是 | 是 | 命中「提到具體工具名→先確認是否已評估」；OmniRoute 判定與「MVP 比較未做」直接相關 |
| Switch 定位 | 新研究方向 / OmniRoute 路線補充 | 補充 | 對齊 DeepSeek V4「降低 Model Routing 優先級」，避免捧成新方向 |
| Q7 是否改既有 QA | 改 / 不動 | 不動 | 既有 QA 不可刪改（AGENTS.md） |
| 來源標注 | 混記 / 分層 | 分層 | 區分 DeepSeek V4（human stable）與 AI draft |
