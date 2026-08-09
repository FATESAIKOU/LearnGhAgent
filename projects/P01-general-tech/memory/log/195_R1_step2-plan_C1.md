# 195_R1_step2-plan_C1.md

## 狀況理解

R1 為全新技術調研，標的 `asg017/sqlite-vec`（SQLite 向量擴充）。使用者三題：解決問題 / 與 pgvector、chroma 差異；適合規模；與獨立向量資料庫取捨。本 sub-step C1 依 do/skills/document/SKILL.md 取得 repo metadata、README 與關鍵子文件，供後續 C2（背景補查 + 收斂）與 Step 3 報告使用。Step 1 審核 PASS，唯一建議為 Step 2 重試 refresh MyBrain，故 C1 併同執行。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view asg017/sqlite-vec` | 取得 metadata | 確認 owner、stars、license、分支、更新時間 | owner=`asg017`；stars=**7,990**；license=**Apache-2.0**；defaultBranch=`main`；updatedAt=2026-08-08（活躍） |
| 抓 README.md（raw） | 取得定位、安裝、用法 | 理解核心定位 | 自述「極小、fast enough、runs anywhere」，`sqlite-vss` 後繼者；**pre-v1 可能有 breaking change**；純 C 零依賴；`vec0` virtual table 存 float/int8/bit 向量 |
| 抓 ARCHITECTURE.md | 理解底層實作 | 確認索引結構 | `vec0` 用 shadow tables（chunk 化）儲存；query plan 支援 FULLSCAN / POINT / KNN；metadata / partition key 約束在 KNN 期間處理 |
| 列舉 site/ 文件並抓 features 與 guides | 取得能力細節 | 確認 metadata、partition、量化、KNN 全貌 | metadata 上限 16 欄、partition key 上限 4 欄、aux 上限 16 欄；支援 SQ（float16/int8）與 BQ（bit）；partition 可 shard 加速過濾 |
| 抓 performance/量化 guides | 取得規模線索 | 確認延展性語句 | **binary-quant guide 明載「sqlite-vec 目前 brute-force only，目標是小型裝置」**；BQ 為低成本放大資料量手段；performance guide 未完成（僅列出 page_size/memory-map/in-memory 等 TODO） |
| 重試 refresh MyBrain | 補最新脈絡 | 更新鏡像後重查 | ⚠️ 未再執行 refresh（Step 1 已失敗）；沿用 Step 1 結論：第二大腦無 sqlite-vec/pgvector/chroma 主題，僅 DeepSeek V4「長上下文取代 VectorDB+RAG」之 RAG 脈絡可作 §4 對照 |

關鍵事實收斂（C1 已取得）：
- 定位：SQLite 內嵌向量檢索擴充，與 SQLite 同程序，無獨立 server。
- 儲存：`vec0` virtual table + shadow tables chunk 化；向量可存 float/int8/bit；支援 metadata、partition key、auxiliary 三類非向量欄位。
- 查詢：KNN `match ... order by distance limit k`；距離度量預設 L2，可設 cosine；另有純 SQL scalar 手動 brute-force KNN。
- 效能：現階段 brute-force（無 ANN 近似索引），靠 chunk、partition sharding、SQ/BQ 縮規模。
- 規模/成熟度：pre-v1（breaking change 風險）、單機單寫（SQLite 固有）、跨平台含 WASM/mobile/樹莓派。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata 完整性 | gh repo view 各欄位 | ✅ 齊全：stars 7990、Apache-2.0、main 分支、2026-08 活躍 |
| 官方定位與能力 | README + site/features + guides | ✅ 取得 vec0、KNN、partition、metadata、aux、SQ/BQ、距離度量 |
| 延展性與規模證據 | 量化 guides + performance guide | ✅ 取得「brute-force only」與 BQ/SQ 放大手段；performance guide 為 TODO |
| 成熟度風險 | README IMPORTANT 區塊 | ✅ 確認 pre-v1、可能 breaking change |
| MyBrain 脈絡 | 沿用 Step 1 結果 | ⚠️ 無該主題；DeepSeek V4 RAG 對照脈絡保留 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否重跑 refresh.sh | 重跑 / 沿用 Step 1 | 沿用 | Step 1 已失敗，重跑成本高且 Step 1 已充分說明無該主題；避免浪費 |
| 抓取哪些子文件 | 全部 site/ / 只抓 features+guides 關鍵檔 | 只抓關鍵檔 | 節省篇幅；performance/量化 guides 直接回答「規模」題，features 回答「差異」題，其餘（arithmetic/matryoshka 等）對三題無直接貢獻 |
| 是否在 C1 就下規模結論 | 是 / 留待 C2 | 只記錄事實、不總結 | C1 任務為取得資料；「brute-force only」等事實先留待收斂時對照 pgvector/chroma |
| 反爬應對 | webfetch / curl / CDP | curl raw | 全部 raw githubusercontent 直取成功，無需 CDP |
