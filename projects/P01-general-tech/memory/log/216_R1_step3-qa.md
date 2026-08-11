# 216_R1_step3-qa.md

## 狀況理解

Step 1/2 已確認標的＝Muse Code（Meta 2026-08-05 終端 coding agent，beta）＋ Muse Spark 1.2，定位為「個人採用評估」。使用者三大焦點：性價比、Meta 拿資料訓練範圍、是否切換訂閱配置。Step 2（C1）已取得官方一手文件（blog/pricing/permissions/cookbook）＋二級交叉。本 step 做硬性驗證（validate-report.sh）與軟性驗證（judge/step3-qa.md），產出最終分析報告與本 step log，並對照第二大腦既有判定。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| mybrain-read refresh + 讀骨幹（判定總表、技術取捨準則、OpenCode、OmniRoute、Kimi K3、LLM降本增效） | 對照既有判定，避免照通則推薦 | §4 替代方案帶第二大的判定與信任層級 | 取得：Muse Code 未評估（首次）、Kimi Code Reject、OmniRoute Accept、OpenCode stable、技術取捨準則（不追新／MVP→Feature 閘門／Reject≠沒價值）、LLM降本增效（Ollama 為主） |
| 重驗官方 blog（research.meta.ai） | 精確 async agents / event log / skills / co-training 細節 | 報告機制描述精確 | 確認 async background agents（session 內持久）、append-only event log（replay-exact / restart-safe）、/plan /grill /goal、co-training with Muse Code |
| 重驗官方 pricing 與 permissions docs | 確認定價 tier 與資料條款、sandbox | 使用者核心疑慮（資料訓練）精確二分 | 確認 Standard $1.25/0.15/4.25（不訓練）、Contributor $0.10/0.002/0.20（授權訓練、限地區）；無長文 premium；sandbox Seatbelt/bubblewrap |
| 跑 validate-report.sh | 硬性驗證報告格式 | 報告合規 | 見下方現狀表 |

**關鍵決策：** 報告含「## 5. 個人採用評估總論」為情境化收斂，但**非** User Q&A（無質問型句構，屬首次產出）。§1-§4 四個必要 section 依 AGENTS.md 格式撰寫。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 產出報告檔名 | `output/216_muse-code.md`，匹配 `(pr-id)_(tech).md` | PASS |
| 4 個必要 section | validate-report.sh 檢查 `## 1.`~`## 4.` | PASS |
| 報告長度 | validate-report.sh 檢查 ≤50000 字 | PASS（實際 < 10000 字） |
| DA 表 | §4 含 5 個替代方案 DA 表，5 欄位齊全 | PASS |
| 語言合規 | 中文、避免比喻/情緒/「可能也許我認為」 | PASS |
| 反面論證 | §4.2 對照表＋§4.3 衝突點表 | PASS |
| 第二大腦對照 | 替代方案皆對照既有判定，帶 GitHub URL＋信任層級；Kimi K3/OmniRoute/OpenCode/LLM降本增效標 `process`/`human`/AI＋`stable`/`draft`；Muse 無此主題明寫首次；技術取捨準則標 `claude-code/opus-5`＋`draft`（未 review）；**與 Kimi Code Reject、不追新準則的衝突明確指出** | PASS |
| 本 step log | 4 個 section、≤3000 字 | PASS |

**本輪變更摘要：** 首次產出 `216_muse-code.md`（Muse Code 個人採用評估報告）。核心結論：Muse Spark 1.2 可 drop-in opencode/Claude Code 僅換 base_url（不換 harness 可低成本試模型）；換 Muse Code harness 撞「不追新」＋「已覆蓋需求」兩準則暫緩；資料授權二分（Standard 不訓練 / Contributor 授權訓練換 -92% 折扣、限地區）；性價比為零月費 token 計費但 Standard output $4.25/M 偏高。報告無 User Q&A（首次、無追問）。

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 報告是否含「個人採用評估總論」 | 只放 §1-§4 純技術 vs 加情境化採用結論 | **加情境化總論** | 使用者明言要判斷「生態位」「可能切換訂閱」；但以情境表而非二選一，符合「MVP→Feature 看能否影響 workflow」準則 |
| §5 定位 | 當成 User Q&A 章節 vs 當成評估總論 | **評估總論** | User Q&A 僅在「使用者質問型句構」時觸發；本輪是首次產出、無追問，故不放 QA |
| 替代方案來源 | 只照通則列 Claude Code/Codex vs 對照第二大腦 | **對照第二大腦** | judge 要求 §4 對照既有判定；Kimi Code Reject 是同一問題域的關鍵判例 |
| 衝突處理 | 淡化 vs 明示 | **明示** | 技術取捨準則與 judge 都強調「與既有判定衝突時明確指出」是對照最有價值處；Muse Code 撞「不追新」與「已覆蓋需求」必須點出 |
| 資料條款深淺 | 只列官方一句話 vs 拆 Standard/Contributor | **拆兩 tier 二分** | 使用者核心疑慮正是「給 Meta 訓練坐到啥地步」，兩 tier 是明確答覆 |
