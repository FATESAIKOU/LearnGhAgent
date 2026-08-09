# sqlite-vec 技術分析報告

> 調研標的：`asg017/sqlite-vec`（SQLite 的向量搜尋擴充）
> 資料來源：官方 repo（7990 stars、Apache-2.0、2026-08-08 更新）、官方文件站、Mozilla Hacks 公告、第二大腦 MyBrain 對照
> 版本：v0.1.10-alpha.4（pre-v1，breaking changes 可能發生）

---

## 1. 這個技術解決什麼問題？

**一句話**：sqlite-vec 讓「SQLite 資料庫」直接具備「向量相似度檢索」能力，使開發者能在既有 SQLite 檔案上，用純 SQL 語法做 KNN（K-Nearest Neighbors）搜尋，而不必另起一座獨立的向量資料庫服務。

具體被解決的問題是**「向量檢索與關聯資料的割裂」**：

- 應用程式通常同時有「結構化資料」（使用者、文章、訂單）與「非結構化資料的向量表徵」（embedding）。傳統做法是結構化資料放 SQLite／PostgreSQL，向量放另一套向量庫，兩邊要同步、要 JOIN、要維護兩套系統。
- sqlite-vec 把向量當成 SQLite 的一種資料型別（`vec0` virtual table），讓「向量檢索」與「一般 SQL 查詢」在同一份資料庫、同一條 SQL 語句裡完成，消除跨系統搬移與同步成本。

**問題描述是否含糊**：使用者三點問題（解決什麼、適合規模、與獨立向量庫取捨）本身清楚，但「適合什麼規模」沒有單一數字答案——它由「演算法本質（brute-force KNN，無 ANN 索引）」與「資料量、維度、查詢頻率」共同決定，需在 §3 與 §4 展開，不能給單一閾值。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章中明確提到的背景

- **sqlite-vss 的後繼者**：sqlite-vec 是作者 asg017 前一個專案 sqlite-vss 的繼承者，定位為「extremely small, fast enough」的向量擴充。sqlite-vss 依賴外部 ANN 函式庫（Faiss），sqlite-vec 改為**純 C、零外部依賴**，可編譯到 Linux／macOS／Windows／WASM／Raspberry Pi。
- **Mozilla Builders 贊助**：官方公告（Mozilla Hacks）說明誕生動機是 **Local AI**——on-device RAG、語意搜尋、資料不出裝置。與 llamafile 同批獲得贊助，目標是讓「本機、離線、免外部服務」的 AI 應用可行。
- **生態配套**：作者同時維護 sqlite-rembed（遠端 embedding API 擴充）與 sqlite-lembed（本機 .gguf embedding 擴充），三者可組成一條「本機 embedding → 本機向量檢索」的完整本地 RAG 鏈。

### 2.2 通用技術背景（非文章明說，由調研補上）

- **向量檢索的兩大流派**：ANN（Approximate Nearest Neighbor，近似最近鄰，用索引換速度，如 HNSW、IVF）與 brute-force（暴力全掃，精確但 O(N)）。sqlite-vec 走**後者**——`vec0` 或手動 distance 函式＋`ORDER BY`，無 ANN 索引。這決定了它的規模天花板。
- **向量資料庫的興起**：RAG（Retrieval-Augmented Generation）普及後，embedding 檢索成為 LLM 應用的標準組件，催生獨立向量資料庫（pgvector、Chroma、Milvus、Qdrant、Weaviate、FAISS 等）。這些系統多數內建 ANN 索引，能撐到百萬級以上向量。
- **SQLite 的定位**：嵌入式、單檔、零伺服器、廣受歡迎（手機、桌面、邊緣裝置）。它的優勢是「隨處可跑、零部署」，劣勢是「單機、無網路服務、擴展性有限」。sqlite-vec 是這條定位在向量領域的延伸。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 核心機制：把向量變成 SQLite 的一等公民

sqlite-vec 提供 `vec0` virtual table，讓向量以「欄位」形式存在，並用 SQL 直接查詢：

```sql
-- 建立向量表：embedding 欄位為 3 維 float32
CREATE VIRTUAL TABLE vec_items USING vec0(
  embedding float[3]
);

-- 插入向量
INSERT INTO vec_items(rowid, embedding)
  VALUES (1, '[0.1, 0.2, 0.3]');

-- KNN 查詢：找與 query 最接近的 3 筆
SELECT rowid, distance
FROM vec_items
WHERE embedding MATCH '[0.1, 0.2, 0.3]'
  AND k = 3;
```

### 3.2 支援的向量型別與距離

| 型別 | 說明 | 距離函式 |
|---|---|---|
| `float[dim]` | float32 向量 | L2、cosine |
| `int8[dim]` | 8-bit 整數向量（可量化） | L2、cosine、hamming |
| `bit[dim]` | 二值向量（可量化） | hamming |

- 量化：`binary`（float→bit）、`i8`（float→int8），可大幅縮小儲存與運算量。
- 向量運算：`vec_add`、`vec_sub`、`vec_normalize`、`vec_slice` 等。
- subtype：223／224／225 標記向量型別。

### 3.3 非向量欄位機制（vec0 的三種欄位）

| 欄位型別 | 數量上限 | 用途 |
|---|---|---|
| metadata 欄位 | 16 | 可進 KNN 的 `WHERE` 條件（過濾） |
| partition key | 4 | 內部 shard 加速，把資料分桶 |
| auxiliary 欄位 | 16 | 存大資料（如原始文字），免 JOIN 直接取回 |

### 3.4 檢索演算法本質：brute-force KNN

- 官方 KNN queries 文件明示：**無 ANN 索引**，是暴力全掃＋排序。
- 查詢方式：`k=N`（限制回傳筆數）或 `LIMIT`（SQLite 3.41+）。
- 也可手動用 distance 函式＋`ORDER BY` 自組查詢。

**規模含義**：查詢成本與「向量總數 × 維度」成正比（O(N·d)）。資料量小時極快、零索引建置成本；資料量大時線性退化，這是「適合規模」的決定性因素。

### 3.5 效能調校（文件 WIP）

官方 performance guide 仍為 WIP，僅列標題：`page_size`、memory mapping、in-memory index、`chunk_size`。無實測數據，規模判斷需靠演算法本質推論＋第三方 benchmark。

### 3.6 部署特性

- 純 C、零外部依賴，可編譯至 Linux／macOS／Windows／WASM／Raspberry Pi。
- 多語言 binding（Python、Node、Ruby、Rust 等）。
- 資料不出裝置，符合 Local AI／on-device 定位。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **pgvector**（PostgreSQL 擴充） | 在 PostgreSQL 內加向量型別與 ANN 索引（HNSW／IVF），SQL 查詢 | 已有或願意部署 PostgreSQL 伺服器；資料量中大型；需要 ANN 索引撐規模 | 需維護資料庫伺服器；索引建置與記憶體成本；與 SQLite 的嵌入式定位不同 | 百萬級向量、ANN 加速、與關聯資料同庫 |
| **Chroma**（獨立向量資料庫） | 專用向量資料庫，內建 embedding 與 ANN 索引，API 簡潔 | 願意引入獨立服務；資料量中大型；需要 ANN 索引 | 多一套服務要部署與同步；與關聯資料分離需自行 JOIN | 快速上手、ANN 加速、專注向量場景 |
| **FAISS**（函式庫） | 純向量檢索函式庫，提供多種 ANN 索引，非資料庫 | 願意自己管理索引與持久化；需要高效 ANN | 非資料庫，需自行處理儲存與同步；學習曲線 | 極高效 ANN 檢索、靈活索引選擇 |
| **Milvus／Qdrant／Weaviate**（獨立向量資料庫） | 分散式向量資料庫，支援大規模 ANN 與多租戶 | 需要分散式、超大規模、高可用 | 部署與運維成本最高；對個人／小型應用過重 | 億級向量、水平擴展、生產級 |

### 4.2 切入點差異

- **sqlite-vec vs pgvector**：兩者都是「把向量塞進既有關聯資料庫」，但 sqlite-vec 走嵌入式單檔、零伺服器、brute-force；pgvector 走伺服器、ANN 索引、可擴展。規模與部署模型不同。
- **sqlite-vec vs Chroma／Milvus 等獨立向量庫**：獨立向量庫內建 ANN 索引，能撐大規模，但多一套服務、與關聯資料分離；sqlite-vec 犧牲規模換「零部署、同庫 JOIN、資料不出裝置」。
- **sqlite-vec vs FAISS**：FAISS 是函式庫非資料庫，效能極高但需自管持久化；sqlite-vec 是資料庫擴充，犧牲部分效能換 SQL 整合與持久化。

### 4.3 第二大腦對照（MyBrain）

**查詢結果**：第二大腦 `技術/技術評估` 底下**沒有** sqlite-vec、pgvector、Chroma、FAISS、Milvus、Qdrant 的任何評估紀錄（判定總表 79 筆中無此類條目）。因此本報告的替代方案比較是**一般知識**，非使用者既有判定。

**相關既有脈絡（可對照，非直接判定）：**

1. **DeepSeek V4**（`技術/技術評估/DeepSeek V4.md`，generated.by=`human:fatesaikou`、status=`stable`，2026-04-26）——使用者本人寫的定稿。主張「1M 長上下文可能取代 VectorDB+RAG」，規劃發起微型 PoC 對比公司現有 RAG 方案。**與本報告的潛在衝突**：若長上下文真取代 RAG，則 sqlite-vec 這類向量檢索組件的必要性會被削弱。本報告不否認此方向，但指出 sqlite-vec 的價值在「本機、離線、資料不出裝置」的場景，與「塞進長上下文」是不同取捨——前者是檢索成本與隱私，後者是上下文成本。此衝突需使用者自行定案。
2. **LeanCtx**（`技術/技術評估/LeanCtx.md`，generated.by=`human:fatesaikou`、status=`stable`，2026-06-06）——使用者本人寫的定稿，判定＝採用。其語義搜尋用**本機 ONNX embedding 模型（all-MiniLM-L6-v2，384 維）＋純 Rust runtime 在 CPU 跑**，不呼叫外部 LLM。**這與 sqlite-vec 高度同構**：都是「本機、輕量、免外部服務的向量檢索」。LeanCtx 的 embedding 是 384 維、CPU 執行，正是 sqlite-vec 的典型適用場景（低維、本機、資料量不大）。**衝突點**：LeanCtx 已用 Rust 自建檢索層，若使用者已投入，sqlite-vec 是「現成替代」而非「必要新增」——依技術取捨準則，這會影響是否值得導入。
3. **技術取捨準則**（`抽象理解/本質洞察/技術取捨準則.md`，generated.by=`claude-code/opus-5`、status=`draft`，**AI 草稿，未經使用者 review**）——原則：理解優先（不熟先自兜、MVP＝理解驗證點）、MVP 升 Feature 唯一閘門＝能否影響個人 workflow、Reject≠沒價值。**這決定了「適合規模」與「獨立庫取捨」的答法**：不以技術優劣為唯一判準，要看是否進入日常 workflow。sqlite-vec 對使用者的意義，取決於他是否真有「本機向量檢索」的日常需求（LeanCtx 顯示有），而非純粹技術比較。

**衝突總結**：第二大腦無 sqlite-vec 直接判定；但 DeepSeek V4（長上下文取代 RAG）與 LeanCtx（已自建本機檢索）兩則與本報告的「sqlite-vec 有價值」結論存在張力——前者質疑向量檢索的長期必要性，後者顯示他已用別的方式解決本機檢索。本報告據此把結論收斂為：sqlite-vec 的適用前提是「本機、低維、資料量不大、要 SQL 整合」，而非通用向量庫替代品。

---

## 5. 附錄：規模與取捨的落地判斷

> 依技術取捨準則（AI draft，未經 review），技術優劣非唯一判準，以下為落地判斷。

### 5.1 適合規模

| 面向 | 判斷 |
|---|---|
| 資料量 | 適合**數萬至數十萬級**向量；百萬級以上因 brute-force 線性退化，需 ANN 索引 |
| 維度 | 低維（如 384 維 embedding）較佳；高維（1024+）運算成本高 |
| 查詢頻率 | 低～中頻（本機、單使用者、on-device）適合；高 QPS 生產服務不適合 |
| 部署 | 嵌入式、單檔、零伺服器、邊緣／桌面／手機 |

### 5.2 與獨立向量資料庫的取捨

| 取捨面向 | 選 sqlite-vec | 選獨立向量庫（pgvector／Chroma／Milvus） |
|---|---|---|
| 部署成本 | 零（嵌入式） | 高（伺服器／服務） |
| 資料同步 | 同庫，無同步 | 需與關聯資料同步 |
| 規模 | 數十萬級 | 百萬～億級 |
| 隱私 | 資料不出裝置 | 依部署位置 |
| 索引 | 無（brute-force） | ANN（HNSW／IVF） |
| 適用 | 本機、個人、邊緣、低維 | 生產、多使用者、大規模 |

### 5.3 對使用者的落地建議（對照 MyBrain）

- 若需求是「本機、離線、資料不出裝置的向量檢索」（LeanCtx 顯示有此需求樣態），sqlite-vec 是現成且輕量的選項，但需注意 LeanCtx 已用 Rust 自建檢索層——依技術取捨準則，是否導入取決於能否影響日常 workflow，而非技術優劣。
- 若方向是「長上下文取代 RAG」（DeepSeek V4 的未定案 PoC），sqlite-vec 的長期必要性需先與此方向對齊。
- 第二大腦無 sqlite-vec 直接判定，以上為一般知識＋既有脈絡推論，非使用者拍板結論。
