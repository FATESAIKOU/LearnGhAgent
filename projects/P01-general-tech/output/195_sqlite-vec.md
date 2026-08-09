# sqlite-vec 技術分析報告

> 標的：`asg017/sqlite-vec`（SQLite 的向量檢索擴充）
> 調研來源：repo README、ARCHITECTURE.md、site/features、量化/performance guides（raw githubusercontent 直取）
> 資料時點：2026-08-09（repo updatedAt 2026-08-08，活躍）

---

## 1. 這個技術解決什麼問題？

**一句話**：sqlite-vec 讓「向量檢索」直接跑在 SQLite 裡，解決「應用程式要同時管關聯資料與向量資料、卻被迫多養一套獨立向量資料庫」的整合問題。

具體拆解成三個被解決的問題：

| 被解決的問題 | 說明 |
|---|---|
| **向量與關聯資料分家** | 一般 RAG 應用同時有「文件內容、metadata、使用者、權限」等關聯資料與「embedding 向量」。若向量放獨立 DB，兩邊要手動同步、join、維護一致性。sqlite-vec 讓向量與其他欄位同表共存，一次查詢同時過濾 metadata 與算距離。 |
| **部署複雜度** | 獨立向量資料庫（Milvus/Qdrant/Weaviate）是獨立 server，要裝、要管、要連線、要考慮網路與高可用。sqlite-vec 是 SQLite 的 loadable extension，與應用同程序，零 server、零網路。 |
| **小規模應用的過度設計** | 對小型裝置、邊緣、單機、原型，引入整套向量 DB 是殺雞用牛刀。sqlite-vec 提供「夠用、能跑、隨 SQLite 到處跑」的輕量替代。 |

**模糊之處**：官方自述「極小、fast enough、runs anywhere」是行銷語，沒有給出明確的「多少向量、多少 QPS」數字承諾。README 明載 **pre-v1，可能 breaking change**，且 binary-quant guide 明說「目前 brute-force only，目標是小型裝置」——所以「解決問題」的邊界（能扛多大規模）官方自己都還沒定死。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章中明確提到的背景

- **sqlite-vss 的失敗教訓**：sqlite-vec 是 `sqlite-vss` 的後繼者。sqlite-vss 依賴 Faiss 這個外部 C++ 函式庫，導致編譯與跨平台（尤其 WASM、mobile）困難。sqlite-vec 改為**純 C、零外部依賴**，是對「SQLite 擴充必須好編譯、好移植」這個教訓的直接回應。
- **SQLite 的定位**：SQLite 是嵌入式、單檔、零 server 的資料庫，被用在手機、瀏覽器（WASM）、樹莓派、桌面應用。向量檢索是近年 AI 應用（RAG、語意搜尋）的剛需，SQLite 生態自然想補上這塊。

### 2.2 通用技術背景（非文章明說，由調研補上）

- **向量檢索的興起**：embedding 模型把文字/圖片轉成高維向量，相似度檢索（KNN）成為語意搜尋與 RAG 的核心。這催生了兩類方案：獨立向量資料庫（Milvus、Qdrant、Weaviate、Pinecone）與關聯式資料庫的向量擴充（pgvector、sqlite-vec）。
- **「多一套 DB」的成本**：獨立向量 DB 意味著多一個要部署、監控、備份、學習的系統，且向量資料與業務資料分離，一致性與 join 成本高。對小型應用，這份成本不成比例。
- **ANN 與 brute-force 的取捨**：大規模向量檢索需要近似最近鄰（ANN，如 HNSW、IVF）換取速度，但 ANN 有召回率損失、建索引成本、參數調校。小規模資料 brute-force（全掃描算距離）反而簡單、精確、零索引維護。sqlite-vec 目前選了 brute-force，是「規模優先」的設計取捨。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 核心機制：`vec0` virtual table

sqlite-vec 用 SQLite 的 **virtual table** 機制實作 `vec0`，讓向量像一般資料表一樣用 SQL 操作：

```sql
-- 建立：宣告向量維度與距離度量
CREATE VIRTUAL TABLE vec_items USING vec0(
  embedding float[768] distance_metric=cosine
);

-- 插入：向量與 metadata 同列
INSERT INTO vec_items(rowid, embedding, category)
  VALUES (1, '[0.1, 0.2, ...]', 'docs');

-- 查詢：KNN，一次同時過濾 metadata 與算距離
SELECT rowid, distance
FROM vec_items
WHERE category = 'docs'
  AND embedding MATCH '[0.3, 0.1, ...]'
ORDER BY distance
LIMIT 5;
```

### 3.2 儲存：shadow tables + chunk 化

`vec0` 的資料不直接存在 virtual table，而是存在 SQLite 的 **shadow tables**（`_vec_items_chunks0`、`_vec_items_rowids` 等），向量被切成固定大小的 **chunk** 儲存。這讓向量資料能走 SQLite 的 B-tree、WAL、備份等既有機制，也讓「只讀需要的 chunk」成為可能。

### 3.3 查詢計畫：FULLSCAN / POINT / KNN

ARCHITECTURE.md 說明 `vec0` 支援三種 query plan：

| Plan | 用途 |
|---|---|
| **FULLSCAN** | 全表掃描，逐列算距離（brute-force） |
| **POINT** | 依 rowid 精確取回單一向量 |
| **KNN** | `MATCH ... ORDER BY distance LIMIT k` 的最近鄰查詢 |

### 3.4 非向量欄位：metadata / partition key / auxiliary

| 欄位類型 | 上限 | 用途 |
|---|---|---|
| **metadata** | 16 欄 | 存可過濾的標籤/屬性，KNN 期間可當過濾條件 |
| **partition key** | 4 欄 | 把向量分組（shard），查詢時只掃特定 partition，加速過濾 |
| **auxiliary** | 16 欄 | 存查詢結果要回傳的附屬資料（不參與過濾） |

### 3.5 距離度量與量化

- 距離度量：預設 **L2**，可設 **cosine**。
- 量化壓縮（放大資料量的手段）：
  - **SQ（Scalar Quantization）**：float16 / int8，把浮點向量壓縮，省記憶體、加快掃描。
  - **BQ（Binary Quantization）**：把向量壓成 bit，記憶體再降，適合超大規模但精度損失更大。
- 另有純 SQL 的 scalar 函式，可手動做 brute-force KNN（不經 `vec0`）。

### 3.6 規模現況（關鍵限制）

- **目前 brute-force only**：binary-quant guide 明載「sqlite-vec 目前 brute-force only，目標是小型裝置」。沒有 ANN 近似索引（如 HNSW）。
- 放大規模靠：chunk 化、partition sharding、SQ/BQ 量化，而非近似索引。
- performance guide 尚未完成（僅列出 page_size、memory-map、in-memory 等 TODO），官方對「能扛多大」還沒有定論。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案總覽

| 技術 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **pgvector**（PostgreSQL 擴充） | 在 Postgres 內加向量型別與 HNSW/IVFFlat 索引，SQL 查詢 | 已有/願意用 Postgres；需要 server | 多一個 DB server 要管；HNSW 有召回率與參數調校成本 | 向量與關聯資料同庫，支援 ANN 大規模，成熟度高 |
| **Chroma**（獨立向量 DB） | 專用向量資料庫，Python 原生，內建 embedding 與持久化 | 接受多一套獨立服務；以 Python 為主 | 多一個 server/程序；向量與業務資料分離 | 上手快、API 簡單，適合原型與中小規模 |
| **Milvus / Qdrant / Weaviate**（獨立向量 DB） | 專用向量資料庫，內建 ANN（HNSW 等）、分片、分散式 | 需要大規模、高 QPS、分散式 | 部署/運維成本最高；學習曲線陡 | 百萬級以上向量、高吞吐、可水平擴展 |
| **Faiss / HNSWlib**（函式庫） | 直接嵌入的 ANN 索引函式庫，程式內呼叫 | 願意自己寫整合層與持久化 | 要自己管索引建構、更新、持久化 | 極致效能與控制，但整合成本高 |
| **長上下文取代 RAG**（架構思路） | 不建向量索引，直接把大量文件塞進 LLM 的長 context | 模型支援百萬 token 級 context | 成本與延遲隨 context 成長；非所有場景適用 | 省去向量 DB 整套，架構簡化 |

### 4.2 對照第二大腦（FATESAIKOU/MyBrain）

**查詢結果**：第二大腦中 **sqlite-vec、pgvector、chroma 皆無任何評估紀錄**（判定總表與全文 grep 零命中）。以下為可引用的相關脈絡：

1. **DeepSeek V4**（`human:fatesaikou`，stable，2026-04-26）
   - URL：`https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/DeepSeek%20V4.md`
   - 內容：他提出「**長上下文取代 VectorDB+RAG**」的架構思路——若模型支援 1M token 且成本坍塌，可直接把數十個 Recipe 或完整 codebase 塞進 context，少花時間鑽研公司舊有的複雜 RAG 邏輯。規劃發起微型 PoC 對比現有 RAG 方案，**尚未定案**。
   - **與本報告的衝突點**：本報告 §4 把「長上下文取代 RAG」列為替代方案之一，但對 sqlite-vec 而言，它與「長上下文」是**不同層級**的取捨——sqlite-vec 解決的是「向量資料放哪」，長上下文解決的是「要不要向量檢索」。若他走長上下文路線，sqlite-vec 這類向量 DB 的價值會被削弱；但對「仍需要精確檢索、或 context 塞不下」的場景，向量 DB 仍必要。**此衝突正是查詢最有價值處**：他對向量 DB 的採用與否，高度取決於他對長上下文取代 RAG 的 PoC 結論。

2. **技術取捨準則**（`claude-code/opus-5`，**draft，未經他 review**，2026-08-01）
   - URL：`https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md`
   - 內容（⚠️ AI draft，非他本人定稿）：理解優先——不穩定或不熟悉就先自己兜，MVP 是理解驗證點；MVP 升 Feature 唯一閘門是「能否影響個人 workflow」；Reject 不等於沒價值。
   - **對 sqlite-vec 的意涵**：sqlite-vec 目前 **pre-v1、可能 breaking change、brute-force only**，屬「不夠穩定」的技術。依此準則，他傾向「先自己兜」理解本質，而非直接採用。且 sqlite-vec 是否進 Feature，取決於它能否影響他的個人 workflow——目前他的向量/RAG 需求主要掛在 AxrossRecipe（公司專案）與長上下文 PoC 上，sqlite-vec 與個人 workflow 的直接掛勾不明。

3. **codebase-memory-mcp**（判定總表，AI draft，2026-06-27）
   - URL：`https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/codebase-memory-mcp.md`
   - 內容：用 SQLite 為 LLM agent 建程式庫結構理解，判定 **skip**（重造輪子、效果難驗證）。
   - **與本報告的關係**：這是「SQLite 系」工具在他第二大腦中唯一的判定紀錄，但問題域不同（程式庫結構理解 vs 向量檢索），僅作為「他對 SQLite 系工具傾向 skip」的弱參考，不直接適用於 sqlite-vec。

### 4.3 切入點差異總結

| 方案 | 切入點 |
|---|---|
| **sqlite-vec** | 把向量塞進既有 SQLite，零 server、隨處跑，犧牲 ANN 換簡單 |
| **pgvector** | 把向量塞進既有 Postgres，支援 ANN，適合已有 Postgres 的中大型應用 |
| **Chroma / Milvus / Qdrant** | 專用向量 DB，把向量檢索當一等公民，換取規模與效能，付出運維成本 |
| **Faiss / HNSWlib** | 函式庫層級，把 ANN 當元件嵌入，換取控制力，付出整合成本 |
| **長上下文取代 RAG** | 從源頭消滅「向量檢索」需求，換取架構簡化，受模型 context 能力限制 |

**對使用者（依第二大腦脈絡）的收斂**：
- 若他的長上下文 PoC 成立，sqlite-vec 這類向量 DB 的採用動機會被削弱。
- 若仍需向量檢索且規模小、想零 server，sqlite-vec 是合理候選；但因其 pre-v1 不穩定，依其「理解優先」準則，較可能先自己兜或觀望，而非直接採用。
- 第二大腦無 sqlite-vec/pgvector/chroma 的既有判定，以上為依其準則的推論，非其舊結論。

---

## 附錄：調研資料來源

- `asg017/sqlite-vec` README（定位、安裝、pre-v1 警告）
- `ARCHITECTURE.md`（vec0 shadow tables、query plan）
- `site/features`（metadata/partition/aux 上限、SQ/BQ、距離度量）
- `site/guides/binary-quant`（「brute-force only，目標小型裝置」）
- `site/guides/performance`（未完成，僅 TODO）
- MyBrain：判定總表、技術取捨準則、DeepSeek V4、codebase-memory-mcp
