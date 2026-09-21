# 271_R1_step3-qa

## 狀況理解

本 step 基於 Step 2（C1）已取得的 colibri metadata、README、benchmarks、GPU_BACKENDS，產出最終分析報告 `output/271_colibri.md`，並做軟性（LLM 自評）與硬性（檔案規範）驗證。R1 為首次調研、無追問，故不建 §5 User Q&A。§4 依指示對照第二大腦：確認 colibri 本身無評估紀錄，同問題域近鄰為 AirLLM（不採用）、llama.cpp/vllm（不採用-Reserve）、omlx（不採用）、freellmapi（不採用）。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| mybrain-read：refresh＋讀骨幹（技術取捨準則、判定總表） | 取得 §4 對照所需之既有判定與取捨準則 | 照其準則而非通則列替代方案 | 取得：理解優先／MVP→Feature 看 workflow／Reject≠沒價值／不追新；判定總表 112 筆 |
| 讀 AirLLM、llama.cpp-vllm、omlx 三份評估全文＋freellmapi 判定 | 確認替代方案之判定、定位、信任層級 | 在 §4 標對判定與 draft 註記 | AirLLM 不採用（太慢）、llama.cpp-vllm 不採用-Reserve（human:stable）、omlx 不採用、freellmapi 不採用；均標註信任層級 |
| grep 第二大腦 colibri／JustVugg／MoE offload 關鍵詞 | 確認標的本身是否已評估 | 有則沿用，無則明寫 | **colibri 查無評估紀錄**，確為首次調研 |
| 撰寫 output/271_colibri.md | 產出 4 節分析報告 | 完成可 review 之報告 | 已產出，見下方變更摘要 |
| 硬性驗證：validate-report.sh | 確認 section 齊全、長度、檔名格式 | PASS | 4 節齊全、長度 < 50000、檔名 271_colibri.md |
| 軟性自評（judge 觀點） | 確認報告對照第二大腦、標信任層級、指出衝突 | PASS | §4.4 明確指出「冷啟動速度與 AirLLM 拒因同量級」之技術張力、硬體落差、抽取價值 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 產出的報告檔名與本輪變更 | `output/271_colibri.md`：首次產出，含 §1 解決什麼問題（含 3 個模糊處）／§2 背景（區分文中明講與通用）／§3 機制（三層階層＋JIT-for-weights＋I/O 引擎＋異構 runtime＋benchmark）／§4 替代方案（DA 表＋第二大腦對照＋切入點＋衝突） | 完成 |
| 本 step 執行 log | `memory/log/271_R1_step3-qa.md`（本檔） | 完成 |
| 報告長度 | 低於 50000 字上限 | PASS |
| log 長度 | 低於 3000 字上限 | PASS |
| §4 第二大腦對照 | AirLLM/llama.cpp-vllm/omlx/freellmapi 判定（含 GitHub URL＋信任層級）、技術取捨準則均已標註 | PASS |
| 衝突標示 | §4.4 明確標出 colibri 冷啟動速度與 AirLLM「太慢」拒因同量級之張力、硬體前提落差、以及 Reject≠沒價值的抽取角度 | PASS |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 技術名（檔名） | ① colibri ② MoE-offload-engine | ① colibri | 以 repo 原始名稱命名，與標的、issue 描述一致，利於檢索 |
| §4 替代方案主軸 | ① 純列 AirLLM/llama.cpp/vLLM ② 再補 omlx/freellmapi＋對照取捨準則 | ② | AirLLM/llama.cpp/vLLM 為同問題域核心對照；omlx/freellmapi 補齊「不採用」判定脈絡，取捨準則讓結論貼合他的判準 |
| 是否標信任層級 | ① 全列 ② 僅標 AI draft | ① | 符合 mybrain-read 規範：每則判定帶 GitHub URL＋generated.by＋status；AI draft 明確註記未 review |
| 衝突是否點出 | ① 不點 ② 指出技術面 vs 既有判定張力 | ② | 查詢最有價值處即在衝突；colibri 冷啟動速度與 AirLLM 拒因同量級是核心張力，硬體落差與抽取價值並列 |
| §5 User Q&A | ① 建空節 ② 不建 | ② | 本輪 R1 使用者僅給標的，無追問；依規則「無提問則無此節」 |
