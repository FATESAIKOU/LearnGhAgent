# 189_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認調研標的為 **sqlite-vec**（asg017/sqlite-vec，SQLite 向量擴充）。使用者三點問題：①解決什麼問題、與 pgvector／chroma 差異；②適合規模；③與獨立向量資料庫取捨。本 sub-step（C1）依 document skill 標準動作：取得 repo metadata → 擷取 README 與關鍵子文件 → 補查背景脈絡。目標是建立技術本質與能力邊界的完整素材，供後續 C2 做橫向比較與規模判斷。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 do/skills/document/SKILL.md | 確認標準調研動作流程 | 依規範執行 | 規範確認：gh repo view → README → 背景脈絡補查 |
| `gh repo view asg017/sqlite-vec` | 取得 repo metadata | 掌握 stars／license／更新時間 | 成功：7990 stars、Apache-2.0、default branch=main、updatedAt=2026-08-08、desc「A vector search SQLite extension that runs anywhere!」 |
| 擷取 raw README.md | 取得專案定位與核心功能 | 掌握定位、安裝方式、範例 | 成功：定位「extremely small, fast enough」；**sqlite-vss 的後繼者**；pre-v1（breaking changes）；純 C 無依賴、可跑 Linux/Mac/Win/WASM/Raspberry Pi；vec0 virtual table 支援 float/int8/bit 向量；Mozilla Builders 專案，贊助者 Fly.io/Turso/SQLite Cloud/Shinkai |
| 擷取官方文件首頁＋introduction | 取得文件結構與定位 | 掌握文件地圖 | 成功：文件 WIP；定位「runs everywhere、pure SQL、多語言 binding」；版本 v0.1.10-alpha.4 |
| 擷取 API Reference | 取得完整函式能力 | 掌握向量型別、距離、量化能力 | 成功：型別 float32/int8/bit；距離 L2/cosine/hamming；量化 binary/i8；運算 vec_add/sub/normalize/slice；subtype 223/224/225 |
| 擷取 vec0 Virtual Table 文件 | 取得非向量欄位機制 | 掌握 metadata／partition key／auxiliary 三種欄位 | 成功：metadata 欄位（max 16，可進 KNN WHERE）、partition key（max 4，內部 shard 加速）、auxiliary 欄位（max 16，存大資料免 JOIN） |
| 擷取 KNN queries 文件 | 確認檢索演算法本質 | 判斷是否 ANN 索引 | 成功：**brute-force KNN**（vec0 或手動 distance 函式＋ORDER BY），無 ANN 索引；`k=N` 或 LIMIT（3.41+） |
| 擷取 performance guide | 取得效能調校資訊 | 掌握規模上限線索 | 部分：文件 WIP，僅列 page_size／memory mapping／in-memory index／chunk_size 標題，無實測數據 |
| 擷取 Mozilla Hacks 公告 | 補查背景脈絡 | 掌握誕生動機與定位 | 成功：Mozilla Builders 贊助，動機＝「Local AI」、on-device RAG／語意搜尋、資料不出裝置；與 llamafile 同批 |
| 補查 sqlite-rembed／sqlite-lembed | 掌握 embedding 生態配套 | 了解完整本地向量鏈 | 成功：sqlite-rembed（遠端 embedding API）、sqlite-lembed（本地 .gguf embedding），與 sqlite-vec 搭配成完整本地 RAG 鏈 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata | gh repo view | 7990 stars、Apache-2.0、main、2026-08-08 更新、定位「runs anywhere」 |
| 核心能力 | README＋API Reference＋vec0 文件 | 型別 float/int8/bit、距離 L2/cosine/hamming、量化 binary/i8、三種非向量欄位機制 |
| 演算法本質 | KNN queries 文件 | **brute-force KNN，無 ANN 索引**（關鍵：規模上限的決定性因素） |
| 背景脈絡 | Mozilla Hacks 公告 | Local AI 動機、on-device RAG、資料不出裝置；Mozilla Builders 專案 |
| 效能數據 | performance guide | 文件 WIP，無實測數據（規模判斷需靠演算法本質推論＋外部資料） |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件來源 | (A) 僅 README (B) 補官方文件站多頁 | B | 使用者問「解決什麼問題／規模／取捨」，需能力邊界細節（vec0 欄位機制、距離、量化），README 不足 |
| 演算法本質確認 | (A) 假設有 ANN (B) 查 KNN 文件確認 | B | 是否 ANN 直接決定「適合規模」答案，必須以文件為準，不能臆測 |
| 效能數據取得 | (A) 依 performance guide (B) 標注 WIP 並留待 C2 補外部資料 | B | performance guide 為 WIP 無數據，規模判斷需在 C2 補第三方 benchmark／官方 issue 討論 |
| 下一步 C2 方向 | (A) 直接寫報告 (B) 補 pgvector／chroma／獨立向量庫比較＋規模資料 | B | 使用者三點問題本質是橫向比較，C1 只完成 sqlite-vec 本體，比較與規模需 C2 補查 |
