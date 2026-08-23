# 242_R3_step3-qa.md

## 狀況理解

R3 是 R2 後的追問，Step 2（C1）已對齊「思想是否對上」：關鍵結論是「用量用完自動 fallback」原生在 **OmniRoute**（circuit + quota exhausted→ineligible），Switchyard 只有 retry + judge fail-open，無 quota 感知；使用者想像的「OmniRoute→Switchyard TOML 匯出 + Switchyard 承載 fallback」方向顛倒且指令不存在。本 step 任務＝把 R3 三問沉澱成 QA 追加進報告 §5，並同步對照第二大腦的取捨準則與既有判定後定稿報告。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| mybrain-read 查骨幹（技術取捨準則、判定總表、OmniRoute.md、下一步清單） | §4 對照第二腦，不照通則列 | 拿到使用者判準 | 準則「先自己兜＋MVP 驗證」「進 Feature 唯一閘門＝影響 workflow」；OmniRoute=採用（draft）；下一步清單有「OmniRoute 試用」未 MVP；DeepSeek V4 明說降低 Model Routing 優先級 |
| 寫 R3 QA（Q4-Q6）進報告 §5 | 沉澱 R3 三問 | 追加、不刪既有 | 完成 Q4（結合可行性）、Q5（結合設定步驟）、Q6（AI wrapping prompt） |
| 更新報告 §4 對照 | 反映「fallback 歸屬 Omni」事實 | §4 與 QA 一致 | 補 OmniRoute 原生 quota/failover 對照與結論 |

## 動作結束後的現狀

**產出報告：** `output/242_switchyard.md`（檔名沿用 R1；R3 在 §5 追加 Q4-Q6，§4 補 OmniRoute quota/failover 對照；未刪既有內容）
**本輪變更摘要：**
- §5 新增 Q4：結合「OmniRoute 免費聚合 + Switchyard fallback」是否可行 → 不可行（能力在 Omni 不在 Switch；方向反、指令不存在、兜出去會重複 OmniRoute 原生 quota/failover）
- §5 新增 Q5：可行的反向接法（Switchyard `[llm_clients]` 指向 OmniRoute localhost:20128，OmniRoute 做免費聚合+fallback，Switch 只做路由政策）與具體 TOML 步驟
- §5 新增 Q6：若仍要「確定性 wrapping」的 prompt 骨幹（方向修正：做「OmniRoute→Switchyard TOML 產生器」而非承載 fallback）
- §4 補對照：OmniRoute 的三層 Resilience（Circuit Breaker/Cooldown/Lockout）＝「用量用完 fallback」歸屬；與 DeepSeek 降 Model Routing 優先級一致

**硬性驗證：** 報告長度約 24k 字 < 50000 上限；QA 序號接續既有 Q3→Q4/Q5/Q6；未刪改既有 QA。§4 已標 GitHub URL 與信任層級，AI draft（OmniRoute）註明未經 review。

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| R3 是否可合併 | 3 問拆 3 條 / 合併 | 拆 3 條 | 使用者三問各自獨立（可行性/步驟/AI prompt），拆開才可獨立追答 |
| 整合方向 | 使用者方向（O→S）/ 反向（S 吃 O endpoint） | 採反向 | Step 2 已證 fallback 屬 OmniRoute；反向維持原生能力，Switch 只疊路由 |
| §4 對照基準 | 通則 / 第二腦判準 | 第二腦判準 | 取捨準則明言照通則會推到他反對的方向；OmniRoute Accept(draft)、DeepSeek 降優先皆需併列 |
| AI wrapping 定位 | 當核心解 / 僅輔助 | 輔助 | 兜出的 fallback 會重複 OmniRoute 已有機制，無收益；只作為 TOML 產生器選項 |
