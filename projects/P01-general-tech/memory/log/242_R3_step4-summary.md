# 242_R3_step4-summary.md

## 狀況理解

R3 是 R2 後的追問，標的仍為 Switchyard（NVIDIA-NeMo）。三問：① OmniRoute 免費聚合 + Switchyard fallback 結合是否可行；② 若可行具體設定步驟；③ AI wrapping 部分給 prompt 骨子。已完成 Step 1（意圖）、Step 2（C1 調研）、Step 3（QA 驗證並更新報告）。本 step 總結整輪產出。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 確認 Step 1-3 產出 | 盤點本輪成果 | 掌握完整交付 | 3 個 step log + 更新後報告齊全 |
| 撰寫本 summary log | 收斂整輪 | 產出 Step 4 總結 | 完成本檔 |

## 動作結束後的現狀

**本輪產出檔案清單：**
- 分析報告：`output/242_switchyard.md`（R3 更新：§5 追加 Q4-Q6，§4 補 OmniRoute quota/failover 對照；未刪既有）
- Step 1 log：`memory/log/242_R3_step1-intent.md`
- Step 2 log：`memory/log/242_R3_step2-plan_C1.md`
- Step 3 log：`memory/log/242_R3_step3-qa.md`
- Step 4 log：`memory/log/242_R3_step4-summary.md`（本檔）

**本輪核心結論：**
- Q4 結合不可行：fallback 能力原生在 OmniRoute（circuit + quota exhausted→ineligible），Switchyard 只有 retry + judge fail-open、無 quota 感知；方向反、指令不存在、兜出去會重複 OmniRoute 原生機制，無收益。
- Q5 可行反向接法：Switchyard `[llm_clients]` 把 `base_url` 指向 OmniRoute 本機（localhost:20128），OmniRoute 做免費聚合+fallback，Switchyard 只疊路由政策。
- Q6 AI wrapping：方向修正為「OmniRoute→Switchyard TOML 產生器」，非承載 fallback。

**待追問方向：**
- 是否要實測反向接法在 claudecode/opencode 的實際承接（含 OllamaCloud/Claude 上游 client 指法驗證）
- 是否要深挖 OmniRoute 免費 provider pool 額度上限與穩定性
- 是否要評估 Switchyard 路由演算法（llm_classifier/stage_router）成本與副作用

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| R3 是否可合併 | 3 問拆 3 條 / 合併 | 拆 3 條 | 三問各自獨立（可行性/步驟/AI prompt），拆開才可獨立追答 |
| 整合方向 | 使用者方向（O→S）/ 反向（S 吃 O endpoint） | 採反向 | fallback 屬 OmniRoute；反向維持原生能力，Switch 只疊路由 |
| 使用者想像指令 | 當存在 / 實際查證 | 實際查證 | `gen-switchyard.toml`、`switchyard update` 皆不存在，明示「預設沒有」成立 |
| AI wrapping 定位 | 當核心解 / 僅輔助 | 輔助 | 兜出 fallback 會重複 OmniRoute 已有機制，無收益；僅作 TOML 產生器選項 |
