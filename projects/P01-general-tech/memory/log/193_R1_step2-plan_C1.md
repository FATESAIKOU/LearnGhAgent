# 193_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認調研標的為 **sqlite-vec**（asg017/sqlite-vec，SQLite 的向量搜尋擴充），使用者要求三點：解決什麼問題、與 pgvector/chroma 差異、適合規模、與獨立向量資料庫取捨。本 sub-step C1 依 document skill 標準動作：取得 repo metadata → 擷取 README 與關鍵子文件 → 補查背景脈絡。此為 harness 測試案例，非真實導入決策。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 do/skills/document/SKILL.md | 確認標準調研流程 | 依規範執行 | 規範確認：gh repo view → README → 背景脈絡補查 |
| `gh repo view asg017/sqlite-vec` | 取得 repo metadata | 掌握 stars/license/分支/更新 | 成功：7,990 stars、Apache-2.0、main 分支、2026-08-08 更新、描述「A vector search SQLite extension that runs anywhere!」 |
| 擷取 README.md（raw） | 取得專案定位與用法 | 掌握核心功能 | 成功：純 C、零依賴、`vec0` virtual table、支援 float/int8/bit 向量、KNN 查詢、Mozilla Builders 贊助、pre-v1 警告 |
| 擷取 ARCHITECTURE.md | 了解底層實作 | 掌握索引結構 | 成功：`vec0` shadow tables（chunks/rowids/vector_chunks/auxiliary/metadata）、idxStr 查詢計畫（fullscan/point/KNN） |
| 擷取官方 docs（introduction/api-reference/vec0/knn/performance） | 取得功能細節 | 掌握 API 與限制 | 成功：vec_f32/int8/bit 建構、L2/cosine/hamming 距離、binary/i8 量化、metadata/partition key/auxiliary 三種非向量欄位、KNN 語法 |
| 擷取 benchmarks-ann/README.md | 取得規模測試資料 | 判斷適用規模 | 成功：cohere1m（768d/1M 向量）、cohere10m（10M）基準；支援 brute-force、rescore、IVF、DiskANN 索引 |
| 查 latest release | 確認版本成熟度 | 判斷穩定性 | 成功：v0.1.9（2026-03-31），docs 標 v0.1.10-alpha.4，pre-v1 有 breaking change |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata | gh repo view | 7,990 stars、Apache-2.0、活躍更新（2026-08-08） |
| 核心功能 | README + api-reference | 純 C 零依賴、vec0 virtual table、三種向量型別、KNN、量化、metadata/partition/auxiliary |
| 底層機制 | ARCHITECTURE.md | shadow tables + idxStr 查詢計畫，支援 fullscan/point/KNN |
| 適用規模 | benchmarks-ann | 官方基準到 10M 向量，含 IVF/DiskANN 索引 |
| 成熟度 | release + docs | pre-v1（v0.1.x），官方明示 breaking change |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件來源 | 只讀 README vs README+docs+ARCHITECTURE+benchmarks | 全讀 | 使用者問「與 pgvector/chroma 差異」「適合規模」，需 API 細節、索引機制、基準資料才能回答 |
| 是否動用 CDP | 一般 webfetch vs CDP | 一般 webfetch | 官方 docs 與 raw 檔皆成功取得，無反爬阻擋 |
| 下一步 C2 方向 | 直接撰寫報告 vs 補查 pgvector/chroma 差異與獨立向量庫取捨 | 補查替代方案 | 使用者三點中有兩點（差異、取捨）需外部對照資料，C1 僅取得 sqlite-vec 本身 |
