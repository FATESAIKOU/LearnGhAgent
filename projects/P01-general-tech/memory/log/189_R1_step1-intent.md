# 189_R1_step1-intent.md

## 狀況理解

R1 首次任務，PR body 來自 issue #188（測試三層意圖判定用）。技術標的明確：**sqlite-vec**（SQLite 的向量擴充）。使用者要求回答三點：①它解決什麼問題、與 pgvector／chroma 的差異；②適合什麼規模的應用；③與獨立向量資料庫的取捨。附帶條件是「三層意圖判定測試」，但無其他限定。調研目標是技術本質理解與橫向比較，非單一 repo 深度掃碼。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 PR body／issue #188 | 確認技術標的與附帶條件 | 鎖定調研對象 | 標的＝sqlite-vec；問題＝三點比較；無其他條件 |
| 讀取 know/AGENTS.md 與 judge/step1-intent.md | 確認 step1 輸出格式與 review 觀點 | 產出合規 4-section log | 格式與軟性驗證觀點確認完畢 |
| 更新並讀取 MyBrain 鏡像 | 查使用者是否已評估過 sqlite-vec | 避免重複、接入既有結論 | 鏡像 refresh 失敗沿用 2026-08-09 副本（註明可能過期）；判定總表與全文 grep 無 sqlite-vec／pgvector／chroma 條目 → **第二大腦無此主題** |
| 讀骨幹：技術取捨準則、專案現況表 | 抓使用者對向量／RAG 的既有立場與 workflow | 判斷報告該往哪個切入點寫 | 見下方三則相關線索 |
| grep MyBrain 向量／RAG／SQLite 相關 | 找相關評估與進行中專案 | 建立與既有知識的連結 | 見下方三則 |

**查到的第二大腦線索（每則帶 URL 與信任層級）：**

1. **DeepSeek V4**（技術評估）——`https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/DeepSeek%20V4.md`；generated.by=`claude-code`、status=`draft`（AI 草稿，未 review）；2026-04-26。內文主張「1M 長上下文可能取代 VectorDB+RAG」，規劃發起微型 PoC 對比公司現有 RAG 方案。→ 使用者有「長上下文是否取代向量檢索」的未定案取捨，sqlite-vec 報告宜對照此思路。
2. **LeanCtx**（技術評估，判定＝採用）——`https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/LeanCtx.md`；generated.by=`claude-code`、status=`draft`。其語義搜尋用**本機 ONNX embedding 模型 + 純 Rust runtime 在 CPU 跑**，不呼叫外部 LLM。→ 使用者對「本機、輕量、免外部服務的向量檢索」有真實需求樣態，是 sqlite-vec 的潛在落點。
3. **技術取捨準則**（骨幹）——`https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md`；generated.by=`claude-code`、status=`draft`。原則：理解優先（不熟先自兜、MVP＝驗證點）、MVP 進 Feature 唯一閘門＝能否影響個人 workflow、Reject≠沒價值。→ 這決定了「適合規模」與「獨立資料庫取捨」的答法：不以技術優劣為唯一判準，要看是否進入日常 workflow。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 技術標的 | 從 PR body／issue 確認 | sqlite-vec（SQLite 向量擴充），三項問題皆明確 |
| 既有評估 | grep 判定總表＋全文 | MyBrain 無 sqlite-vec／pgvector／chroma 任何評估紀錄（第二大腦無此主題） |
| 相關脈絡 | 讀骨幹＋grep 向量／RAG | 有 DeepSeek V4（長上下文取代 RAG 之議）、LeanCtx（本機向量搜尋）、技術取捨準則三則可對照 |
| 資料可能過期 | refresh.sh 結果 | 更新失敗沿用舊副本，回報中標注可能過期 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研範圍 | (A) 僅掃 sqlite-vec repo (B) 補網路搜尋官方文件＋與 pgvector／chroma 比較 | B | 使用者三點問題本身就是橫向比較（vs pgvector／chroma／獨立向量庫），非單一 repo 能答 |
| 是否先查 MyBrain | (A) 直接調研 (B) 先查使用者立場 | B | 命中「推薦技術方案」場景；LeanCtx 顯示使用者對本機向量檢索有需求，DeepSeek V4 顯示對 VectorDB+RAG 有未定結論，須接入 |
| 報告切入點 | (A) 純技術優劣 (B) 技術優劣＋對照使用者 workflow 取捨準則 | B | 依技術取捨準則，技術優劣非唯一判準，需給出「規模適合」與「與獨立庫取捨」的落地判斷 |
