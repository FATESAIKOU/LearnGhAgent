# 256_R2_step3-qa.md

## 狀況理解

本輪 R2，使用者三問皆屬「套用至自身訂閱組合」的質問型句構：**(Q1) 適用性與具體手續、 (Q2) harness（claudecode/opencode/agy）能否自由切換、 (Q3) 合約風險與被停號案例**。Step 1–2 已完成意圖拆解與資料收集（repo metadata＋constants.go＋README＋legal＋ollama_cloud_usage＋antigravity 429 排障）。本 step 將 R2 三問沉澱進既有報告 `output/256_sub2api.md` 的 `## 5. User Q&A`，並以第二大腦對照支撐 §4 判定語意，產出 QA。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀既有報告 `output/256_sub2api.md` | 確認 R1 已建立的機制/§4 基線與附錄 | 界定 R2 只動 §5，不重做 | R1 已含 §1–§4＋附錄，§5 尚無；檔名沿用 |
| 以 mybrain-read 查第二大腦 | 對照 Q2/Q3 的既有判定與風險證據 | 回答 harness 採用狀態＋Anthropic 合約風險 | 命中：`LLM降本增效.md`（本人 stable，原話「可以自由切Harness/LLM」）、`OpenCode.md`、`Muse Code.md`（draft，換 harness 暫緩）、`個人 AiAgent 入口.md` 09-06 節（Anthropic 消費者方案 opt-out/訓練，draft 含原話）；grep 停號/封號/終止 **無命中** |
| 抓 sub2api repo（README/constants.go/ollama_cloud_usage.go/legal） | 落地 Q1/Q2/Q3 事實 | 確認平台白名單、帳號型態、harness 設定、ToS 聲明 | 取得：5+ 平台、oauth/apikey 帳號型態、三協定、Antigravity 端點設定、OllamaCloud Bearer＋web session、README ToS 風險聲明、legal 自審條文 |
| 產出 §5 四個 QA（Q1 適用性／Q2 手續／Q3 harness／Q4 合約風險） | 把 R2 三問沉澱為 QA | 每 QA 含 A＋表格/對照表＋結論，觸發於質問句構 | 4 個 QA 已追加，既有內容未刪改 |
| 執行 `judge/validate-report.sh` | 硬性驗證格式 | 報告 <50000 字、§1–§4 齊、檔名合規 | **OK: report valid** |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 產出的報告檔名 | `output/256_sub2api.md`（沿用 R1） | 存在、未更名 |
| 本輪變更摘要 | §5 新增 Q1–Q4：Q1 訂閱組合適用性、Q2 具體手續、Q3 harness 自由切換、Q4 合約風險與停號；既有 §1–§4＋附錄未刪改 | 已寫入並通過 validator |
| QA 規則 | 按序號遞增接續、保留質問語氣、含 A＋表格/對照表＋結論、遵守無比喻/情緒/模糊用詞 | 通過（唯 Q1–Q4 內引用來源原文含「可能」屬引述非自述） |
| 第二大腦對照 | Q3/Q4 標明 GitHub URL＋信任層級；`draft` 註明未 review；停號查無明寫「第二大腦無此主題」 | 通過 |
| §4 語意一致性 | R2 未推翻 R1 §4；Q4 明示與 `LLM降本增效` 方向一致、公司 Claude 風險疊加之衝突 | 通過 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| Q1/Q2 拆分 | 合併為「能不能用＋手續」一題；拆為適用性與手續兩 QA | 拆兩 QA | 使用者第一問含兩個子問題，依 AGENTS.md 同一輪多子問題拆獨立 QA |
| Q3 harness 切換 | 直接答「能」；先拆 harness 層與 sub2api 層、標 agy 為缺口 | 拆層＋標缺口 | sub2api 管上游→平台，切換是 harness 側；agy 無 repo 設定、無第二大腦記錄，不能臆斷 |
| Q4 停號案例 | 照 repo 聲明答「有風險」；明寫「無一手停號案例＋第二大腦無此主題」 | 後者 | 查無即明說沒有，不編；與他的結論切割 |
| 是否改動 §1–§4 | 更新機制以納 R2；維持 R1 §1–§4 | 維持 | R2 是落地評估非機制重述；既有內容不可刪 |
