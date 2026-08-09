# 186_R1_step2-plan_C1.md

## 狀況理解

本 sub-step 為 R1 Step 2 的第一個資料收集階段（C1）。R1 Step 1 已確認技術標的為 `sqlite-vec`（asg017/sqlite-vec，SQLite 向量搜尋擴充），並定義 3 個分析面向：①解決問題＋vs pgvector/chroma；②適用規模；③vs 獨立向量資料庫。C1 的任務是依 `do/skills/document/SKILL.md` 標準調研動作取得 repo metadata、README、關鍵子文件與背景脈絡，供後續收斂。目標是建立對標的的「第一手事實層」，不含評斷。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view asg017/sqlite-vec` | 取得 repo metadata | stars/license/預設分支/更新時間 | nameWithOwner=`asg017/sqlite-vec`；stargazerCount=`7990`；license=`Apache-2.0`；defaultBranch=`main`；updatedAt=`2026-08-08`；description=「A vector search SQLite extension that runs anywhere!」 |
| `gh api .../tags` | 確認版本成熟度 | 判斷是否 pre-v1 | 最新 tag=`v0.1.10-alpha.4`；長期停在 0.1.x alpha，佐證「pre-v1、會有 breaking changes」聲明 |
| 抓取 README.md（raw main） | 取得首頁說明 | 定位核心賣點與安裝 | 核心賣點：極小、pure C、零依賴、「fast enough」；`vec0` virtual table 支援 float/int8/bit 向量、metadata/auxiliary/partition key 欄位；Mozilla Builders 主贊助；`sqlite-vss` 的接續者；支援 Python/Node/Ruby/Go/Rust/Datasette/rqlite/WASM |
| 抓取 ARCHITECTURE.md | 理解內部實作 | 取得 vec0 shadow tables 與 query plan | 揭露 `vec0` 用 shadow tables（chunks/rowids/vector_chunks/metadata/auxiliary）存資料；query plan 有 FULLSCAN / POINT / KNN 三種；KNN 用 `idxStr` 編碼傳遞 query vector、k、partition、metadata 約束 |
| 抓取 site/features/vec0.md、knn.md | 理解 KNN 機制與欄位型別 | 取得功能事實 | 三種非向量欄位（metadata 可進 WHERE、auxiliary 分開存但不可進 KNN WHERE、partition key 內部 shard）；KNN 有兩種做法（`vec0` virtual table 或純 scalar function brute-force）；支援 L1/L2/cosine；`k=` 或 SQLite 3.41+ `LIMIT` |
| 抓取 site/guides/performance.md、scalar-quant.md | 補規模/記憶體面向 | 取得調校與量化事實 | performance 主題：page_size、memory mapping、in-memory index、chunk_size；量化（SQ）：float16(2B)/int8(1B) 縮減，犧牲品質；提供 sqf16/sqi8/bq2 |
| 抓取 benchmarks-ann/README.md | 確認基準測試範圍 | 判斷可達規模 | 內建 cohere1m / cohere10m（768d）與多種 index type（brute-force float/int8/bit、rescore、IVF、DiskANN） |
| 抓取 site/index.md、introduction.md | 補定位與使用情境 | 取得開場定位 | 定位為 local/fast 情境：laptop、server、mobile、browser(WASM)、Raspberry Pi；強調「pure SQL、不需 server」 |
| 查 tree 確認文件結構 | 盤點關鍵子文件 | 確認無遺漏的 FAQ/limit/why 文件 | repo 無獨立 why-vec.md 或 FAQ.md；相關資訊散於 ARCHITECTURE、site/guides（performance、rag、hybrid-search、scalar-quant、binary-quant）、benchmarks |

**取得的關鍵事實摘要（供 C2 收斂）：**
- 定位：極小、pure C、零依賴、SQLite 內嵌、pre-v1（0.1.x alpha）
- 載體：`vec0` virtual table（shadow tables 分塊），或純 scalar function 暴力搜尋
- 功能：float/int8/bit 向量、metadata/auxiliary/partition 欄位、L1/L2/cosine、量化（SQ、bit）、IVF、DiskANN、rescore
- 規模證據：官方 benchmark 到 cohere10m；README 自承「fast enough」而非 high-performance

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata 完整 | gh repo view / api | 取得 name、stars(7990)、license(Apache-2.0)、main、更新時間、描述 |
| 版本狀態 | tags API | 最新 0.1.10-alpha.4，確認 pre-v1 聲明屬實 |
| README 讀取 | raw main 抓取 | 完整取得核心賣點、安裝、sample SQL |
| 子文件涵蓋 | tree 盤點＋抓取 | 涵蓋 vec0/knn/performance/quantization/benchmarks/architecture |
| 反爬 | webfetch/curl | 全程無 CAPTCHA，未觸發 CDP |
| 對應 Step1 三面向 | 比對需求 | C1 資料已覆蓋 ①(vs pgvector/chroma 待 C2 補)、②(benchmark 到 10M、pre-v1)、③(內嵌 vs 獨立 DB 待 C2) |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件抓取範圍 | 僅 README / README＋關鍵子文件 | README＋ARCHITECTURE＋vec0/knn/performance/quantization/benchmarks | Step1 需涵蓋「解決什麼、機制、規模、取捨」，需子文件支撐，但避免全抓 site（過度冗長） |
| 規模判斷來源 | 只用 README / 輔以 benchmark | 以 README「fast enough」＋benchmarks-ann（cohere10M）雙重佐證 | 避免單一來源偏誤；benchmark 提供可驗證的規模上限 |
| 是否用 CDP | 直接用 / 遇阻再用 | 未用 | 全部 raw fetch 成功，無 CAPTCHA |
| 是否抓第三方比較文（pgvector/chroma） | 這輪做 / 下輪做 | 下輪（C2）做 | C1 定位為「標的自身事實」，對照組資料留待 C2 避免本 log 超長 |
| why-vec/FAQ 文件缺失處理 | 視為遺漏 / 改查 site | 改查 site/guides 與 benchmark | tree 確認無專屬 why 文件，功能面分散於 guides，已抓取代表篇章 |

**下一步（C2）：** 補齊對照組背景脈絡——pgvector（PostgreSQL extension）、chroma（獨立 embedded DB）、獨立向量資料庫（Milvus/Qdrant/Weaviate）的定位與差異，以及 SQLite 內嵌 vs 獨立向量資料庫的取捨論點，供最終報告 DA 表使用。
