# 178_R2_step2-plan_C1.md

## 狀況理解

R2 意圖（Step 1 已定調）：使用者以自然語言「把這次的結論存進我的第二大腦吧」要求寫入，**非 `/sync-to-mybrain` 開頭**，故本輪不執行 sync、不寫入，僅提出可執行的提案。

Step 1 已確認：第二大腦**沒有** ollama vision 模型的既有評估，R1 結論（`output/178_ollama-vision-models.md`）是新的待寫入內容。本 sub-step C1 的任務是把「寫入提案」做**具體化**——確認 MyBrain 的寫入格式、分類、連結、流程，讓提案帶可立即執行的細節，而非空泛的「建議存進去」。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀 MyBrain 根目錄 `index.md` 使用規則 | 掌握寫入的目錄結構、frontmatter、日誌連結規範 | 確認 Tech Review 檔的標準格式與來源參照方式 | 規則三：日誌以相對路徑連結主題檔；規則五：外部產出以 `sources[]` 或 GitHub URL 指回、不複製原文；規則六：一主題一檔、合併不碎片；規則七：AI 產出 `status: draft` 不填 `verified`；規則八：`骨幹` tag 於 tags 首元素 |
| 讀 PCM-sync-to-mybrain 的 `do/sync-to-mybrain.md` 與 `know/AGENTS.md` | 確認 sync 流程的執行機制與產出規格 | 確認 `/sync-to-mybrain` 觸發後的七步驟與交付 | 七步：判斷值不值得存→淺 clone→讀 `index.md`→寫檔→reindex+validate→commit/push/開 PR→清理；log 末行需 `MYBRAIN_PR:` |
| 讀 sync 實例（174_R4：Claudian Orchestra PKB） | 拿到一份真實的寫入成品對照 | 確認新主題檔＋日誌＋log 三者的實際長相 | 寫入 4 檔：`技術/技術評估/<名>.md`（Tech Review）、`日誌/YYYY-MM-DD.md`、`log.md`、`技術/技術評估/index.md`（reindex 重生）；來源以 GitHub URL 指回 P01 output |
| 掃 MyBrain `技術/技術評估/` 目錄 | 確認是否已有 ollama / vision 主題檔、避免重複建檔 | 確認寫入標的是新檔 | `grep -i "ollama\|vision\|llava\|qwen\|llama3.2"` 無命中 → 確認為新主題檔，檔名提案 `技術/技術評估/Ollama Vision 模型.md` |
| 讀 R1 報告與 174 檔的 frontmatter 格式 | 比對報告內容與既有檔的 `sources[]` 寫法 | 擬出待寫檔的 frontmatter 與內文骨架 | 174 檔 `sources[]` 含 id/title/resource/author/last_modified，連回 P01 output 與 PR 網址；R1 報告可作待寫檔內文素材 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 寫入分類 | MyBrain `技術/技術評估/` 目錄內容 | 確認應放 `技術/技術評估/`，與 LLM降本增效、Gemini Spark、OKF 同層 |
| 是否新檔 | grep ollama/vision/llava/qwen/llama3.2 | 第二大腦無此主題，寫入為「新增」而非「append」 |
| 寫入格式 | `index.md` 規則三/五/六/七 | Tech Review + frontmatter `sources[]` 連回 P01 output + 日誌相對路徑連結；AI 產出 `draft` |
| 執行流程 | PCM `do/sync-to-mybrain.md` | 由 `/sync-to-mybrain` 觸發七步驟，非本輪；log 末行 `MYBRAIN_PR:` |
| 提案可行素材 | R1 報告 `output/178_ollama-vision-models.md` 內容 | §1-§4 含結論（qwen2.5vl 最適合截圖理解）與對照，足供 sync 階段收斂 |

**待寫檔骨架提案（供 `/sync-to-mybrain` 參數參考）：**
- 新增 `技術/技術評估/Ollama Vision 模型.md`（type: Tech Review，`status: draft`）
- `sources[]`：連回 `projects/P01-general-tech/output/178_ollama-vision-models.md` 與 PR #178
- `日誌/2026-08-08.md`：`→ [Ollama Vision 模型](../技術/技術評估/Ollama%20Vision%20模型.md) — 摘要`
- 手寫根目錄 `log.md` 一條；`index.md` 由 reindex 重生
- 內文核心：三模型規格表、agent 截圖適用性結論、與商業 vision API 取捨、與他既有「降低視覺依賴」方向之張力

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| C1 調研標的 | (A) 重新調研 vision 模型 (B) 調研 MyBrain 寫入慣例 | B | R2 意圖是「存結論」非重做調研；C1 該把提案具體化，不是重複 R1 |
| 寫入檔名提案 | (A) 依技術名「ollama-vision-models」 (B) 中文主題「Ollama Vision 模型」 | B | MyBrain 主題檔慣用中文（LLM降本增效、Gemini Spark），與既有檔一致 |
| 是否本輪就寫入 | (A) 直接動手寫入 (B) 只提出具體提案 | B | 留言非 `/sync-to-mybrain` 開頭，know/我.md 明令本輪只讀不寫；提案已含可執行細節 |
| 提案資訊深度 | (A) 只說「建議存」 (B) 給出檔名/分類/sources/內文骨架 | B | 使用者 Step 1 提案已說「可帶參數指定存什麼」，C1 補足具體參數讓 W00 一接手即可執行 |
