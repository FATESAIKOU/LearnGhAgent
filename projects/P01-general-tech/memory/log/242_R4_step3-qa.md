# 242_R4_step3-qa.md

## 狀況理解

R4 是對「反向接法」（Switchyard 指到 OmniRoute）的價值質疑，質問型句構（「意義在哪」「是因為…還是…」）。Step 1 定調：逐一驗證 2 個候選猜測再收斂意義。Step 2 C1 已證：Switchyard 的 fallback 僅 retry+judge fail-open+決策清單，無 quota/circuit/failover；OmniRoute 可承接 Claude 訂閱（Tier 1）與 OllamaCloud（API key）。本 step 基於調研更新報告，做 QA 驗證並產出 execution log。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀既有報告 242_switchyard.md | 盤點 R1-R3 既有內容 | 對齊結論，避免矛盾 | 既有 Q1-Q6、§4 對照齊全 |
| 用 mybrain-read 查第二腦 | §4 替代方案對照個人判定 | 依準則推薦而非通則 | 讀判定總表/OmniRoute.md/取捨準則/DeepSeek V4 |
| 更新報告 §5 | 追加 R4 QA | 沉澱本輪問答 | 新增 Q7，改 header 註記；未刪既有 |
| 撰寫本 step log | 記錄 QA 驗證動作 | 產出 step log | 完成本檔 |

## 動作結束後的現狀

**產出檔案與本輪變更摘要：**
- 分析報告：`output/242_switchyard.md`（本輪變更：§5 新增 Q7「反向架構下 Switchyard 的意義」；header 註記加 R4 Q7；§1-§4 未改）
- Step 3 log：`memory/log/242_R4_step3-qa.md`（本檔）
- 檔案總長：34531 bytes（遠低於 50000 上限）

**Q7 內容摘要：**
- 猜測①（訂閱掛不進 OmniRoute）證偽：Claude 訂閱（Tier 1）+ OllamaCloud（API key）皆可掛。
- 猜測②（效能）方向半對但因果反：Switchyard 是多一跳 + judge 額外 call，非加速。
- 意義＝唯一手動加的「weak/strong 路由政策層」；對照 DeepSeek V4 stable 判定「降低 Model Routing 優先級」直接衝突；若只要統一 endpoint+fallback，OmniRoute 已全包。

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 猜測驗證順序 | 先講意義 / 先證偽 2 猜測 | 先證偽 2 猜測 | 使用者明列 2 具體猜測，須先證偽/證實再收窄 |
| §4 是否修改 | 是 / 否 | 否 | 本輪無新增替代方案，既有對照已含 OmniRoute/準則 |
| Q7 是否改既有 QA | 改 / 不動 | 不動 | 既有 QA 不可刪改（AGENTS.md） |
| 來源標注 | 混記 / 分層 | 分層 | 區分 DeepSeek V4（human stable）與其他 AI draft |
