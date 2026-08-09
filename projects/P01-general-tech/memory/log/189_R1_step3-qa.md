# 189_R1_step3-qa.md

## 狀況理解

Step 1 確認標的為 sqlite-vec（asg017/sqlite-vec），Step 2（C1）已取得 repo metadata、README、官方文件（vec0、KNN、API、performance guide）、Mozilla Hacks 公告與 embedding 生態配套。本 step 需：①依 AGENTS.md「分析報告格式」產出最終報告（4 個必要 section，無 User Q&A）；②用 search-from-mybrain 對照第二大腦，把既有判定寫進 §4；③產出本 step 的 execution log。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀 judge/step3-qa.md 與 validate-step3.sh、validate-report.sh | 確認軟性驗證觀點與硬性驗證規則 | 產出合規 | 確認：4 section、DA 表、中文、結構化、反面論證、檔名格式、第二大腦對照；log≤3000 字、報告≤50000 字 |
| 跑 search-from-mybrain（refresh.sh） | 更新鏡像 | 取得最新第二大腦 | 更新失敗沿用舊副本（2026-08-09），回報中標注可能過期 |
| 讀骨幹：判定總表、技術取捨準則、專案現況表 | 抓使用者對向量／RAG 的既有判定與準則 | 讓 §4 對照真實立場 | 見下方三則線索 |
| grep MyBrain 向量／RAG／sqlite／pgvector／chroma／faiss 等 | 確認替代方案是否被評估過 | 判斷 §4 引用來源 | 判定總表 79 筆無任何向量庫條目 → 第二大腦無此主題 |
| 讀 DeepSeek V4、LeanCtx 全文 | 抓與 sqlite-vec 相關的既有脈絡 | 建立對照與衝突點 | 見下方 |
| 撰寫 output/189_sqlite-vec.md | 產出最終分析報告 | 回答使用者三點問題 | 完成，含 4 section＋附錄落地判斷 |
| 撰寫 memory/log/189_R1_step3-qa.md | 產出本 step log | 記錄動作總結 | 完成 |

**查到的第二大腦線索（每則帶 URL 與信任層級）：**

1. **DeepSeek V4**——`https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/DeepSeek%20V4.md`；generated.by=`human:fatesaikou`、status=`stable`（本人定稿）；2026-04-26。主張「1M 長上下文可能取代 VectorDB+RAG」，規劃微型 PoC。→ 與「sqlite-vec 有價值」存在張力，報告 §4.3 明確指出此衝突。
2. **LeanCtx**——`https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/LeanCtx.md`；generated.by=`human:fatesaikou`、status=`stable`（本人定稿）；2026-06-06。判定＝採用。語義搜尋用本機 ONNX embedding（all-MiniLM-L6-v2，384 維）＋純 Rust CPU runtime，不呼叫外部 LLM。→ 與 sqlite-vec 高度同構（本機、輕量、免外部服務），且他已用 Rust 自建檢索層，構成「現成替代」張力。
3. **技術取捨準則**——`https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md`；generated.by=`claude-code/opus-5`、status=`draft`（**AI 草稿，未經 review**）。原則：理解優先、MVP 升 Feature 唯一閘門＝能否影響個人 workflow、Reject≠沒價值。→ 決定「適合規模」與「獨立庫取捨」的答法不以技術優劣為唯一判準。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 產出報告檔名 | 依格式 `(pr-id)_(技術名).md` | `output/189_sqlite-vec.md` |
| 本輪變更摘要 | 新增報告 | 首次產出：4 個必要 section（§1 問題／§2 背景／§3 解法／§4 替代方案）＋附錄落地判斷；無 §5 User Q&A；§4 含 DA 表（4 替代方案）＋第二大腦對照（DeepSeek V4、LeanCtx、技術取捨準則，帶 URL 與信任層級，AI draft 標注未經 review，衝突明確指出） |
| 硬性驗證 | validate-report.sh | 待執行（4 section 齊全、檔名 `189_sqlite-vec.md` 符合、長度 <50000） |
| 硬性驗證 | validate-step3.sh | 待執行（4 section 齊全、長度 <3000） |
| 第二大腦對照 | grep＋讀骨幹 | 無 sqlite-vec／pgvector／chroma 直接判定，報告明寫「第二大腦無此主題」；相關脈絡（DeepSeek V4、LeanCtx）已接入並標衝突 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 技術名 | (A) sqlite-vec (B) sqlite-vector-extension | A | 官方 repo 名與使用者 PR body 皆用 sqlite-vec，最簡潔且可辨識 |
| §4 替代方案來源 | (A) 僅通則列 (B) 通則＋對照第二大腦 | B | judge/step3-qa.md 第 7 項硬性要求對照 MyBrain，且使用者 persona 要求反面論證 |
| 衝突處理 | (A) 忽略 (B) 明確指出 | B | DeepSeek V4（長上下文取代 RAG）與 LeanCtx（已自建本機檢索）與「sqlite-vec 有價值」衝突，正是對照最有價值處，漏掉即 FAIL |
| 規模判斷 | (A) 給單一閾值 (B) 依演算法本質＋多面向 | B | brute-force KNN 決定規模由資料量／維度／頻率共同決定，單一數字會誤導 |
| 落地建議 | (A) 純技術優劣 (B) 對照 workflow 準則 | B | 依技術取捨準則，是否導入取決於能否影響日常 workflow，非技術優劣 |
