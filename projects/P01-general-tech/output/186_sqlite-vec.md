# sqlite-vec 技術分析報告

> 標的：`asg017/sqlite-vec`（SQLite 向量搜尋擴充）
> 版本狀態：v0.1.10-alpha.4（pre-v1，長期停在 0.1.x alpha）
> 授權：Apache-2.0 ｜ stars：7990 ｜ 預設分支：main ｜ 更新：2026-08-08
> 定位：A vector search SQLite extension that runs anywhere!

---

## 1. 這個技術解決什麼問題？

**一句話：** sqlite-vec 解決「在 SQLite 內直接做向量相似度搜尋（KNN），不必另起一座獨立向量資料庫」的問題——讓既有 SQLite 資料庫能同時存放一般關聯資料與向量，並用同一套 SQL 語法查詢兩者。

具體拆解成三個子問題：

| 子問題 | 說明 |
|---|---|
| 向量與關聯資料分離 | 傳統做法是向量放獨立 DB、關聯資料放 SQLite/Postgres，兩邊要同步、要 join、要維護兩套系統 |
| 多一個部署單元 | 獨立向量資料庫是額外的 server/進程，要安裝、要連線、要管資源 |
| 查詢語法割裂 | 向量查詢與 SQL 查詢是兩套語言，應用層要自己拼裝 |

sqlite-vec 把向量搜尋做成 SQLite 的 extension（`vec0` virtual table），向量就住在 SQLite 檔案裡，用 `SELECT ... ORDER BY distance` 就能查。

**模糊之處：** 「解決什麼問題」的邊界取決於「規模」——sqlite-vec 官方自承是「fast enough」而非 high-performance。若使用者要的是「百萬級以上、低延遲、高並發」的向量檢索，sqlite-vec 不是為此設計，這點在 §3、§4 會展開。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章中明確提到的背景

- **sqlite-vss 的接續者**：sqlite-vec 是 `sqlite-vss` 的後繼專案，作者（Alex Garcia）在 sqlite-vss 的基礎上重寫，改用 shadow tables 自管索引，擺脫對 Faiss 的依賴。
- **「runs anywhere」的動機**：作者定位在 local/fast 情境——laptop、server、mobile、browser（WASM）、Raspberry Pi。核心賣點是「極小、pure C、零依賴、不需 server」。
- **Mozilla Builders 主贊助**：專案由 Mozilla Builders 計畫贊助，屬開源基礎設施性質。

### 2.2 通用技術背景（非文章明說，屬通用脈絡）

- **向量檢索的興起**：embedding 模型把文字/圖片/音訊轉成高維向量後，「找最相似」變成「算距離」，催生 ANN（近似最近鄰）檢索需求。
- **資料庫分裂**：關聯資料（SQL）與向量資料（ANN）分屬不同系統，導致「雙寫、雙查、雙維護」的架構複雜度。SQLite 作為最普及的嵌入式資料庫，長期缺乏原生向量能力，才需要 extension 補上。
- **嵌入式 vs 獨立服務的張力**：獨立向量資料庫（Milvus/Qdrant/Weaviate）解決大規模、分散式、高可用，但代價是部署與運維成本；嵌入式方案（SQLite extension、Chroma embedded）犧牲規模換取零部署。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 載體：`vec0` virtual table

sqlite-vec 透過 SQLite 的 virtual table 機制提供 `vec0`，把向量搜尋包成 SQL 表。建立與查詢：

```sql
-- 建立：float 向量，維度 3，附 metadata 欄位
CREATE VIRTUAL TABLE vec_examples USING vec0(
  sample_embedding float[3],
  metadata text
);

-- 插入：向量 + metadata
INSERT INTO vec_examples(sample_embedding, metadata)
VALUES ('[1.0, 2.0, 3.0]', '{"name": "foo"}');

-- KNN 查詢：找最接近 [1.0, 2.0, 3.0] 的前 10 筆
SELECT rowid, distance, metadata
FROM vec_examples
WHERE sample_embedding MATCH '[1.0, 2.0, 3.0]'
  AND k = 10;
```

### 3.2 內部實作：shadow tables

`vec0` 用 SQLite 的 shadow tables 分塊儲存，不依賴外部索引庫：

```
vec_examples
├── vec_examples_chunks          # 向量分塊
├── vec_examples_rowids          # rowid 對應
├── vec_examples_vector_chunks   # 向量資料本體
├── vec_examples_metadata        # metadata 欄位
└── vec_examples_auxiliary       # auxiliary 欄位
```

### 3.3 Query plan：三種執行路徑

| 路徑 | 觸發 | 行為 |
|---|---|---|
| FULLSCAN | 無索引條件 | 全表掃描，暴力算距離 |
| POINT | 指定 rowid | 單點查詢 |
| KNN | `MATCH` + `k=` | 走索引，用 `idxStr` 編碼傳遞 query vector、k、partition、metadata 約束 |

### 3.4 欄位型別與約束

| 欄位型別 | 用途 | 能否進 KNN WHERE |
|---|---|---|
| 向量欄位（float/int8/bit） | 距離計算 | 是（MATCH 標的） |
| metadata | 一般欄位，可進 WHERE 過濾 | 是 |
| auxiliary | 分開存放，不參與距離 | 否（不可進 KNN WHERE） |
| partition key | 內部 shard 分區 | 是（限定搜尋範圍） |

### 3.5 距離與量化

- 距離度量：L1、L2、cosine。
- 量化（scalar quantization）：float16（2B）、int8（1B），以犧牲品質換記憶體縮減；提供 `sqf16`/`sqi8`/`bq2`。
- 進階索引：IVF、DiskANN、rescore（粗排後精排）。

### 3.6 規模證據

- 官方 benchmark（`benchmarks-ann/`）內建 cohere1m / cohere10m（768 維）與多種 index type（brute-force float/int8/bit、rescore、IVF、DiskANN）。
- README 自承「fast enough」而非 high-performance——這是定位聲明，不是性能保證。

### 3.7 生態與語言支援

支援 Python、Node、Ruby、Go、Rust、Datasette、rqlite、WASM。查詢走純 SQL，不需 server。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 對照組 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **pgvector**（PostgreSQL extension） | 在 Postgres 內加 `vector` 型別與 ANN index（HNSW/IVFFlat），向量與關聯資料同庫 | 已有 Postgres 部署；接受 server 架構 | 需 Postgres 版本支援；索引建置與記憶體成本；與 SQLite 無關 | 在既有關聯資料庫內獲得向量檢索，免另起向量 DB |
| **Chroma**（embedded 向量資料庫） | 獨立 embedded 向量 DB，Python/JS 原生，預設持久化到磁碟 | 接受「向量資料與關聯資料分離」；以 Python/JS 為主 | 多一個資料來源要同步；非 SQL 介面 | 快速起一個 local 向量檢索，API 簡單 |
| **獨立向量資料庫**（Milvus / Qdrant / Weaviate） | 專用 ANN server，分散式、高可用、大規模 | 需要百萬級以上、低延遲、高並發、多節點 | 部署/運維成本高；多一個 server 單元；資料同步複雜 | 大規模、高吞吐、可水平擴展的向量檢索 |
| **Faiss / HNSW 等 ANN 函式庫** | 直接嵌入程式的 ANN 索引函式庫，不經資料庫 | 自己管理索引生命週期與持久化 | 無 SQL 介面；要自己寫查詢與儲存層 | 極致效能與控制力，但工程成本高 |
| **長上下文模型取代 RAG**（思考方式） | 把資料直接塞進 context，不做向量檢索 | 資料量在 context 可容範圍；模型支援長上下文 | 成本與延遲隨 context 增長；非檢索架構 | 省去向量 DB 與 RAG 的建置與維護 |

### 4.2 切入點差異

- **pgvector** 與 sqlite-vec 同屬「關聯資料庫內嵌向量」路線，差別在載體：pgvector 綁 Postgres（server），sqlite-vec 綁 SQLite（嵌入式、零 server）。sqlite-vec 的優勢是部署極簡、可跑在 WASM/mobile/edge；pgvector 的優勢是 Postgres 的成熟度與並發能力。
- **Chroma** 與 sqlite-vec 同屬「嵌入式」路線，但 Chroma 是獨立 embedded DB（向量與關聯資料分離），sqlite-vec 是 SQLite extension（向量與關聯資料同庫、同 SQL）。sqlite-vec 的優勢是「不用多一個資料來源」。
- **獨立向量資料庫** 是規模路線：當資料量、延遲、並發需求超過嵌入式方案能扛的範圍時才需要。sqlite-vec 官方 benchmark 到 cohere10M，但定位是「fast enough」，不是為高並發生產設計。
- **Faiss/HNSW 函式庫** 是「自己兜」路線：最大控制力，但工程成本最高，且無 SQL 介面。
- **長上下文取代 RAG** 是「不做檢索」的思考方式：直接塞 context，省掉整個向量 DB 層。

### 4.3 對照第二大腦的判定（FATESAIKOU/MyBrain）

**查詢結果：第二大腦沒有 sqlite-vec / pgvector / chroma / Milvus / Qdrant / Weaviate / Faiss 的直接評估判定。** 判定總表（79 筆）中無此主題。以下為間接相關判定，標註信任層級：

| 判定 | 內容 | GitHub URL | 信任層級 |
|---|---|---|---|
| **DeepSeek V4**（試用） | 「長上下文取代 VectorDB+RAG 的架構思路」；規劃發起微型 PoC 對比現有 RAG 方案，尚未定案 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/DeepSeek%20V4.md | human:fatesaikou, stable（本人定稿） |
| **Github 一週熱點 112**（採用） | 對 qmd 工具「Accept, 至少要試過一次向量搜尋」——有「至少試過一次向量搜尋」的意圖 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Github%20一週熱點%20112.md | human:fatesaikou, stable（本人定稿） |
| **codebase-memory-mcp**（不採用） | 用 SQLite 知識圖譜；Reject 理由「問題域是重造輪子、技術複雜但效果難驗證」 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/codebase-memory-mcp.md | human:fatesaikou, stable（本人定稿） |
| **EverOS**（不採用） | 其 hybrid retrieval 用 Milvus，但整體 Reject（機制複雜、規模大、無自組織驗證） | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/EverOS.md | human:fatesaikou, stable（本人定稿） |
| **LeanCtx**（採用） | 本機 ONNX embedding + 語義搜尋，用 Rust rten runtime，不呼叫外部 LLM API | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/LeanCtx.md | human:fatesaikou, stable（本人定稿） |
| **技術取捨準則**（骨幹） | 理解優先（不穩定或不熟悉先自己兜，MVP 是理解驗證點）；MVP→Feature 唯一閘門是「能否影響個人 workflow」；Reject＝不採用≠沒價值；汰換看上游死沒死；不追新 | https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md | claude-code/opus-5, draft（AI 草稿，未 review） |

**與本報告結論的衝突點（查詢最有價值處）：**

1. **「長上下文取代 VectorDB+RAG」與「向量資料庫」的張力**：DeepSeek V4 判定（stable）提出「長上下文取代 VectorDB+RAG」的架構思路，並規劃 PoC 對比。這與「導入 sqlite-vec 做向量檢索」的方向存在張力——若長上下文方案成立，向量 DB 層可能被取代。本報告 §4 的「長上下文取代 RAG」替代方案即對應此判定。**衝突點：** 若使用者正朝長上下文方向走，sqlite-vec 的導入價值需先與此 PoC 對比，而非直接採用。

2. **「至少試過一次向量搜尋」的意圖**：Github 一週熱點 112（stable）對 qmd 寫「Accept, 至少要試過一次向量搜尋」。這支持「試用 sqlite-vec 做一次向量搜尋」的動作，與 sqlite-vec 的嵌入式、零部署特性契合——它是最低成本的「試一次向量搜尋」載體。

3. **「不追新」與「pre-v1」**：技術取捨準則（draft）明列「不追新」「汰換看上游死沒死」。sqlite-vec 長期停在 0.1.x alpha（pre-v1），依此準則屬「不夠穩定」——依「理解優先」原則，這反而觸發「先自己兜/先試用理解」而非直接採用。**衝突點：** 若直接建議「採用 sqlite-vec 進 Feature」，與「不追新、pre-v1 不穩定」衝突；正確的落點是「試用理解」，不是「採用」。

4. **「Reject≠沒價值」**：codebase-memory-mcp 的 Reject 理由是「重造輪子、效果難驗證」，但準則明示被拒專案仍可抽取需求理解與方案方向。sqlite-vec 若被判定不採用，其「SQLite 內嵌向量」的方向仍可抽取。

**結論：** 第二大腦無 sqlite-vec 直接判定。間接判定顯示：使用者有「至少試過一次向量搜尋」的意圖（支持試用），同時有「長上下文取代 VectorDB+RAG」的架構思路（與導入向量 DB 存在張力），且依「不追新、pre-v1 不穩定」準則，sqlite-vec 的合理落點是「試用理解」而非「直接採用進 Feature」。以上判定中，技術取捨準則為 AI 草稿（未 review），其餘為本人定稿。
