# 195_R1_step1-intent.md

## 狀況理解

使用者透過 PR #195 要求調研 `sqlite-vec`（SQLite 的向量擴充），並明確列出三個題目：
1. 它解決什麼問題、與 pgvector / chroma 的差異
2. 適合什麼規模的應用
3. 與獨立向量資料庫的取捨

這是 R1（PR body 第 1 次發言），為三層意圖判定用的測試 issue。任務性質為標準技術調研，非追問或 review。使用者意圖清晰：產出結構化分析報告，比較 SQLite 系向量方案與獨立向量資料庫的定位差異。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 PR body（#195） | 理解使用者意圖 | 確認調研標的與三項題目 | 確認標的為 sqlite-vec，三題明確 |
| 讀取 know/AGENTS.md、我.md | 確認 Step 1 規範與互動偏好 | 產出 4-section log、先查第二大腦 | 規範確認完畢 |
| 執行 refresh.sh | 更新 MyBrain 鏡像 | 取得最新第二大腦 | ⚠️ 更新失敗，沿用既有副本（可能過期） |
| grep 骨幹檔 | 定位策展結論 | 取得使用者對向量檢索的取捨準則 | 命中 11 份骨幹檔，含技術取捨準則 |
| grep sqlite-vec / pgvector / chroma / 向量 / RAG | 搜尋相關評估紀錄 | 找到使用者對該主題的舊結論 | **第二大腦無此主題**（sqlite-vec、pgvector、chroma 皆零命中） |
| 讀取 DeepSeek V4、判定總表、技術取捨準則、專案現況表 | 取得脈絡與準則 | 理解使用者對向量檢索的既有立場 | 取得相關脈絡（見下方） |

MyBrain 查詢結果（⚠️ refresh 失敗，內容可能過期；信任層級標註）：
- **sqlite-vec / pgvector / chroma 本身：無任何評估紀錄**。`https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md`（AI 產出 draft）與全 bundle grep 皆零命中。**第二大腦無此主題**。
- **DeepSeek V4**（`human:fatesaikou`，stable）：曾提出「長上下文取代 VectorDB+RAG」的架構思路，並規劃對比現有 RAG 方案的微型 PoC，尚未定案。`https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/DeepSeek%20V4.md`
- **codebase-memory-mcp**（判定總表，AI draft）：用 SQLite 為 LLM agent 建程式庫結構理解，判定 skip（重造輪子、效果難驗證）。
- **技術取捨準則**（骨幹，AI draft）：理解優先——不穩定或不熟悉就先自己兜，MVP 為理解驗證點；MVP 進 Feature 唯一閘門是「能否影響個人 workflow」；Reject 不等於沒價值。`https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md`

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 是否已評估過該標的 | grep 判定總表 + 全文掃描 sqlite-vec/pgvector/chroma | ✅ 無任何評估紀錄，屬全新標的 |
| 是否有進行中專案相關 | 專案現況表掃描 | ✅ 無直接掛勾；僅間接相關於 RAG/向量檢索架構方向（DeepSeek V4） |
| 是否有取捨準則 | 讀技術取捨準則（骨幹） | ✅ 有：理解優先、MVP 為驗證點、workflow 閘門、Reject≠沒價值 |
| MyBrain 資料時效 | refresh.sh 輸出 | ⚠️ 更新失敗，沿用既有副本，可能過期 |

結論：本輪為全新技術調研，無使用者的舊結論可直接引用。報告中「他對 sqlite-vec 的立場」不得杜撰為其舊結論；但可用其取捨準則（理解優先、workflow 閘門）作為評估框架。可補充其「長上下文可能取代 VectorDB+RAG」的既有架構思考作為對照脈絡。

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否先查第二大腦 | 是 / 否 | 是 | 我.md 核心規則：涉及技術方案推薦須先 search-from-mybrain |
| sqlite-vec 無命中時如何處理 | 用通用知識填空當作他的結論 / 明說無此主題 | 明說無此主題 | skill 規定查不到須明說，不得用通用知識冒充其舊結論 |
| 是否採納 DeepSeek V4 的 RAG 脈絡 | 不採納 / 作為對照脈絡引用 | 作為對照脈絡引用 | 與向量檢索主題高度相關，是其本人穩定評估（human, stable），可作報告 §4 對照 |
| 評估框架 | 純技術比較 / 以其取捨準則衡量 | 兩者並用 | 既回答三題（技術比較），也呼應其 workflow/理解優先準則以貼合使用者 |
