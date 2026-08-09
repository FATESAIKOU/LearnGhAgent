# 183_R1_step2-plan_C1.md

## 狀況理解

標的：`asg017/sqlite-vec`，SQLite 的向量搜尋擴充。Step 1 已定調為全新技術標的（第二大腦無評估記錄）。本 sub-step（C1）目標＝依 document skill 標準動作取得 repo metadata 與主要文件，建立事實基底供後續 C2（差異/取捨/規模分析）使用。R1 無追問，聚焦三點：與 pgvector/chroma 差異、適合規模、與獨立向量資料庫取捨。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view asg017/sqlite-vec`（JSON） | 取得 repo metadata | 得到 stars、license、branch、更新時間 | ✅ stars=7990、license=Apache-2.0、預設分支 main、updatedAt=2026-08-08、createdAt=2024-04-20、description「A vector search SQLite extension that runs anywhere!」 |
| webfetch raw README.md | 擷取主文件 | 掌握定位、安裝、範例 | ✅ 自述「extremely small, fast enough」；pre-v1（預期 breaking changes）；`vec0` virtual table 支援 float/int8/bit 向量；純 C 零依賴，可在瀏覽器(WASM)/Raspberry Pi 執行；為 `sqlite-vss` 的後繼者；Mozilla Builders 贊助 |
| webfetch 官方 docs 首頁 + introduction | 補查背景脈絡 | 取得定位描述與功能總覽 | ✅ 定位「runs everywhere、pure SQL、no server」；純 SQL（CREATE/INSERT/SELECT），無需額外設定與伺服器 |
| webfetch API Reference | 取得技術細節 | 掌握向量型別、距離函式、量化 | ✅ 支援 float32/int8/bit 三種向量；距離函式 L2/cosine/hamming；二進位與 int8 量化；`vec0` 儲存 BLOB（subtype 223/224/225） |
| webfetch `vec0` Virtual Table 文件 | 取得索引/表結構機制 | 掌握 KNN 搜尋、metadata/partition/aux 欄位 | ✅ vec0 支援 metadata（16 上限、可 WHERE 過濾）、partition key（最多 4、內部 shard）、auxiliary 欄位（16 上限、不能 WHERE）；KNN 用 `match` + `order by distance limit k` |
| webfetch 未命中頁面（overview/features.html、docs/overview.md） | 試補其他文件 | 取得額外脈絡 | ❌ 404，官方文件結構為 site/ 下的 .md，正確路徑已由 side nav 補上 |

**關鍵事實收斂（供 C2 使用）**：
- 定位：SQLite 單檔資料庫的向量搜尋擴充，嵌入式、純 SQL、零 server。
- 成熟度：pre-v1（v0.1.10-alpha.4），官方明示「expect breaking changes」，2024-04 建立、活躍更新。
- 核心機制：`vec0` virtual table + 以 BLOB 存向量；KNN 查詢為 `where X match ? order by distance limit k`；內建距離函式與量化。
- 可擴充性機制：metadata 欄位做 WHERE 過濾、partition key 做內部 sharding（提醒過度 sharding 會拖慢）。
- 未見 ANN（近似最近鄰）索引機制之明確宣告——需在 C2 查證是 brute-force 全掃還是含索引。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata | gh api JSON | 完整取得（stars/license/日期/描述） |
| 主文件 | raw README | 取得定位、安裝、範例 |
| 技術細節 | 官方 docs（intro/api/vec0） | 取得向量型別、距離、量化、table 機制 |
| 資料完整性 | 對照 side nav 章節 | 已涵蓋 Getting Started、API、vec0；尚未細讀 performance 指南 |

**缺漏（待 C2 補）**：明確的「是否含 ANN 索引 vs brute-force」、官方規模/效能指引、與 pgvector/chroma 差異的對照素材。

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件來源 | 官方 docs 站（alexgarcia.xyz/sqlite-vec）／僅 raw repo 檔案／第三方文 | 官方 docs 站為主 | 官方 docs 站結構清晰且 side nav 完整，一次抓取即得 API 全貌，勝過拼 raw 檔 |
| 是否續查 performance 指南 | 本 step 續抓／留待 C2 | 留待 C2 | C1 已達成「metadata+主要文件」目標，效能/規模屬 C2 的差異與取捨分析範疇，避免本 step 過長 |
| 反爬策略 | webfetch 一般抓取／CDP | webfetch 一般抓取 | 全程未遭遇 CAPTCHA/反爬，無需動用 CDP |
