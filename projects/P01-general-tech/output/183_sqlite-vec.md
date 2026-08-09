# sqlite-vec：SQLite 的向量搜尋擴充

> 標的：`asg017/sqlite-vec`（https://github.com/asg017/sqlite-vec）
> 調研輪次：R1（PR #183，對應 issue #182）
> 資料基準：repo metadata、官方 README、官方 docs（intro / API / vec0），抓取於 2026-08-09。
> 資料來源標注：本報告除「第二大腦」標注段落外，其餘為一般技術知識／官方文件，非使用者既有結論。

---

## 1. 這個技術解決什麼問題？

**sqlite-vec 解決的問題是：在「嵌入式、單一檔案、零伺服器」的 SQLite 資料庫內，直接做向量資料的儲存與 KNN（k-nearest neighbor，k 近鄰）搜尋，而不需要額外架設獨立的向量資料庫服務。**

具體可拆成三層：

| 問題 | 說明 | sqlite-vec 對應作法 |
|---|---|---|
| **向量沒地方放** | 文字 embedding、圖像特徵等維度向量，需要一個儲存載體與原始資料共存 | 用 `vec0` virtual table 把向量以 BLOB 存在 SQLite 單一 `.db` 檔內 |
| **向量要能被語意搜尋** | 不能用 SQL 的 `=` / `LIKE` 找「最相似的向量」 | 提供 `match` + `order by distance limit k` 的 KNN 語法 |
| **不想要一套獨立服務** | 嵌入式場景（行動裝置、瀏覽器、邊緣裝置、本機小工具）架不起或不想架獨立向量 DB server | 純 C、零依賴、可在 WASM／Raspberry Pi 執行、直接嵌入進應用程式 |

**問題描述的模糊之處（需明言）**：官方自述定位是「runs anywhere、pure SQL、no server、small & fast」，「anywhere」是行銷宣稱，**實際效能與規模界線官方並未給出明確數字承諾**（見 §2 與 §3 的查證）。「fast」是相對性的：對「小到中等」資料集成立，對百萬級以上 ANN 資料集則與獨立向量 DB 不在同一量級。這是 PR body 三問中「適合什麼規模」直接相關的含糊點。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章／官方明確提到的背景

| 背景 | 內容 |
|---|---|
| **SQLite 是嵌入式資料庫霸主** | SQLite 是單檔、零 server、內建於瀏覽器與作業系統的資料庫，但原生不支援向量型別與向量搜尋 |
| **向量搜尋是新需求** | 2023 年後 LLM embedding 普及，RAG 需求爆發，「在現有資料庫裡存向量並找最近鄰」變成普遍需求 |
| **前身 sqlite-vss 失敗** | sqlite-vec 官方明述自己是 `sqlite-vss` 的後繼者——vss 依賴外部函式庫、跨平台編譯麻煩；vec 重寫為純 C 零依賴以解決 |
| **贊助來源** | 由 Mozilla Builders 贊助，定位偏小型、嵌入、可攜 |

### 2.2 通用技術背景（非官方明述，為補上的脈絡）

- **向量距離計算的性質**：找「最相似」要算距離（L2 / cosine / hamming）。資料量小時暴力全掃（brute-force）即可；資料量大時必須用 ANN（近似最近鄰）索引（HNSW、IVF 等）犧牲少量準確率換取速度。
- **兩種架構典範的拉扯**：
  - **嵌入式**（SQLite + extension、DuckDB、Faiss 等）：零 server、部署輕、與應用同程序，適合中小資料。
  - **獨立向量資料庫**（pgvector on Postgres、Milvus、Qdrant、Weaviate、Chroma）：獨立服務、分散式、可水平擴展、提供 HNSW/IVF 等成熟 ANN，適合大資料與高並發。
- 需求端為何興起：RAG、語意搜尋、推薦系統都需要「把非結構化內容轉成向量再檢索」，而這些資料常與原本的關係型資料同處一個應用，驅動「能否就地解決」的動機。

> **「與獨立向量資料庫的取捨」之所以存在，根源於上述兩種典範：** 嵌入式換到「零 server、極簡部署」，代價是規模與並發天花板；獨立 DB 換到「規模與效能」，代價是架設與營運負擔。PR body 的取捨問題，正是這條光譜的選擇題。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 核心機制（怎麼做，不評論好壞）

**① 用 `vec0` virtual table 存向量**

sqlite-vec 以 SQLite virtual table 機制註冊 `vec0` 表，向量的表示、儲存、比對都由擴充接管：

```
CREATE VIRTUAL TABLE vec_items USING vec0(
  embedding float[768]
);
```

- 支援三種向量型別：`float32`、`int8`、`bit`。
- 向量以 **BLOB** 形式儲存在 SQLite 檔內，並以 SQLite subtype（223/224/225）標記是哪一種向量型別。
- 向量維度在建表時固定。

**② 以 SQL 語法做 KNN 查詢**

```
SELECT * FROM vec_items
WHERE embedding MATCH ?
ORDER BY distance
LIMIT k;
```

- `MATCH ?` 傳入查詢向量。
- `ORDER BY distance` + `LIMIT k` 即為 KNN。
- 內建距離函式：**L2**（float/int8/bit 皆可）、**cosine**、**hamming**（僅 bit）。

**③ 支援量化以縮小資料**

- 二進位量化（binary quantization）：把 float 向量量化為 bit 向量，大幅縮小儲存與加速比對，官方作為壓縮手段。
- int8 量化：以 8-bit 整數存向量。

**④ 附屬欄位機制（metadata / partition / auxiliary）**

| 欄位型態 | 上限 | 可做 WHERE 過濾 | 用途 |
|---|---|---|---|
| metadata 欄位 | 16 | ✅ | 儲存可過濾的屬性（如 category、tags） |
| partition key | 4 | ✅ | 把向量分組內部 sharding，加速局部搜尋；過度 sharding 反而拖慢 |
| auxiliary 欄位 | 16 | ❌ | 隨查詢結果一併回傳的附屬資料（如原始文字、URL） |

**⑤ 成熟度狀態**

- 版本 `0.1.10-alpha.4`，**pre-v1**，官方明示「expect breaking changes」。
- 專案建立於 2024-04，至 2026-08 仍活躍更新；repo 描述為「A vector search SQLite extension that runs anywhere!」。

### 3.2 查證：是否含 ANN 索引？（本報告對官方文件的檢驗）

調研文件（intro / api / vec0 文件）中**未見 HNSW / IVF 等 ANN 索引機制的明確宣告**。vec0 的定位與 partition key 的「sharding」語意，均屬「對暴力掃描做分區縮小」而非成熟的 ANN 近似索引。**官方文件也未給出明確的規模／效能數據承諾。**

因此在 R1 中，對「適合什麼規模」的結論採保守定調：

- **實際適用**：萬級至百萬級以下、單機／嵌入、延遲容忍度寬的中小資料集。
- **不適合當宣稱目標**：以億級規模、毫秒級高並發為硬需求的場景，應視為超出此擴充的設計意圖。

> 此為對官方文件可證範圍內的事實陳述。若後續使用者追問，可再深入 repo 的 C 實作與 issue 討論確認是否存在更深的索引機制（見 §5 待查證，若 R2 觸發）。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

> 本節先對照使用者的第二大腦（FATESAIKOU/MyBrain）判過的相關方案，再列同級替代方案與 DA 表。
> ⚠️ **MyBrain 鏡像更新失敗（沿用 adf968c，2026-08-04 副本），本節第二大腦內容可能過期。**
> 已 grep 確認：第二大腦中**無 sqlite-vec、pgvector、chroma、qdrant、weaviate、faiss、HNSW 的獨立評估記錄**。以下相關結論為 grep 到的間接脈絡。

### 4.1 第二大腦相關脈絡（與本標的相關的既有判定）

| 主題 | 第二大腦記錄 | 信任層級 | 與 sqlite-vec 的關聯 |
|---|---|---|---|
| **DeepSeek V4** | 評估「長上下文（1M）可能取代 VectorDB+RAG」的架構降維，規劃微型 PoC 對比現有 RAG 方案，**尚未定案**（試用列） | `process` 產出、status 未列「—」 | 若此方向成立，整條「向量 DB 檢索」需求都可能被長上下文替代，影響所有向量方案（含 sqlite-vec）的長期價值。URL: https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/DeepSeek%20V4.md |
| **EverOS** | 以 Milvus 做 hybrid retrieval（BM25 + Vector），但整體判定為「不採用」——機制複雜規模大、導入規模與專案年紀不符 | `process` 產出 | 顯示他對「獨立向量 DB 的複雜度 vs 專案規模」敏感：**規模太小撐不起獨立向量 DB**，此與 sqlite-vec「嵌入式輕量」的賣點方向一致。URL: https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/EverOS.md |
| **context-mode** | MCP server，用 FTS5 做 session 延續，處於研究階段（觀望列） | `process` 產出 | 說明他已有在 SQLite 系（FTS5 全文）上就地解決「檢索」的經驗，與「SQLite + extension 就地擴充」的思路同源。URL: https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/context-mode.md |
| **codebase-memory-mcp** | 用 tree-sitter+LSP+SQLite 建立程式庫結構理解，判定「skip：問題域是重造輪子」 | `process` 產出 | SQLite 就地儲存知識圖譜，非向量搜尋，但顯示他對「SQLite 系重造輪子」的保守傾向。URL: https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/codebase-memory-mcp.md |

**第二大腦沒有直接判定 sqlite-vec 或任何同級向量資料庫。** 上述均為間接脈絡，非針對本標的的結論。

### 4.2 對照他的技術取捨準則（骨幹檔）

來源：`抽象理解/本質洞察/技術取捨準則.md`，`generated.by=claude-code/opus-5`、`status=draft`（AI 校正稿，未經本人 review，以下為該檔主張、非已定稿決策）。

| 準則 | 內容 | 對 sqlite-vec 的意涵 |
|---|---|---|
| 理解優先 | 不穩定或不熟悉就先自己兜，MVP 是理解驗證點 | sqlite-vec 本身 **pre-v1、明示 breaking changes**，依此準則會傾向「先自己兜」或 MVP 試作，而非直接採用 |
| Reject ≠ 沒價值 | 被拒仍抽取需求理解與方案方向 | 即使不採用，其「單檔就地向量搜尋」的思路仍有抽取價值 |
| 汰換看上游死沒死 | 不因「有更好替代」汰換，只因「維護停更／需求消失」汰換 | sqlite-vec 目前上游仍活躍，若採用則「死沒死」是未來汰換唯一判準，不該只因出現更好的就去換 |
| 進 Feature 唯一閘門 | 能否影響個人 workflow | sqlite-vec 是否進 Feature，取決於它能否進他的日常 workflow，而非純技術優劣 |

> **衝突提示**：若依「理解優先」準則，sqlite-vec 的 pre-v1 不穩定狀態反而是「先自己兜」的觸發條件；但另一方面「汰換看上游死沒死」不否定「不穩定的新專案」本身。兩者需以「是否進個人 workflow」為最終閘門收斂。這與 PR 本體「測試用 issue」的後設性質一致——本報告是分析材料，不是採用決策。

### 4.3 同級／替代方案 DA 表

> 切入點差異簡述：**就地擴充 vs 關聯式整合 vs 純向量服務 vs 純檢索函式庫**，落在「嵌入式→獨立服務」的光譜不同位置。

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **sqlite-vec**（本標的） | SQLite `vec0` virtual table 就地存向量並 KNN；純 C 零依賴、可 WASM | 資料量中小、單機嵌入、pre-v1 可接受 breaking change | 未見成熟 ANN 索引；規模/並發天花板低；breaking change 風險 | 極簡部署、單檔攜帶、零 server；適用中小語意搜尋 |
| **pgvector**（Postgres 擴充） | 在既有 Postgres 上加向量型別與 HNSW/IVF 索引，`ORDER BY embedding <-> query` 語法 | 已用 Postgres、想要關係資料與向量同庫 | 需維運 Postgres；寫入索引有成本；規模受單庫節點限制（可讀複本擴展） | 與既有 SQL 資料整合、支援成熟 ANN、跨中小到大規模 |
| **Chroma**（嵌入式向量 DB） | 開源向量 DB，提供 client API 與 persistence；可嵌入或跑 server | 想快速起一個語意檢索、重視開發 DX | 是獨立程式與儲存，非「單檔」；規模大時需轉 server 模式 | 快速原型、簡易 API、中小規模語意檢索 |
| **Milvus**（獨立分散式向量 DB） | 獨立分散式向量資料庫，成熟 ANN（HNSW/IVF）、分片與水平擴展 | 億級資料、高並發、需分散式與維運能力 | 架設與營運負擔重、資源需求高（他對 EverOS 的顧慮） | 大規模、高並發、可水平擴展的向量檢索 |
| **Faiss**（檢索函式庫，非資料庫） | Facebook 的向量相似性檢索函式庫，含多種 ANN 索引，嵌入進 Python 程式 | 只需「算最近鄰」的計算核心，不在乎資料庫語意與持久化 | 非資料庫，需自己管儲存與索引生命周期 | 高效 ANN 計算核心，作為嵌入組件而非完整方案 |

**切入點差異總結**：

```
          嵌入式（零 server、小規模）            ←——→            獨立服務（大規模、高並發）
sqlite-vec ── pgvector(在既有DB上) ── Chroma ── ── Milvus
               Faiss = 純計算函式庫（不屬資料庫，是上面任一的加速底層）
```

- **sqlite-vec / Chroma** 都是「嵌入式、中小規模」，差別在 sqlite-vec 是「單檔 SQLite 就地」，Chroma 是「獨立儲存的 DB 程序」。
- **pgvector** 是「在既有關聯式庫上加能力」，適合已有 Postgres 的人。
- **Milvus** 是唯一主打「分散式大規模」的純向量 DB。
- **Faiss** 是底層計算函式庫，不做資料庫語意。

### 4.4 對使用者個人脈絡的落點（僅供參考，非採用決策）

- 依他的「理解優先」與「規模敏感」傾向，sqlite-vec 的價值在於：**在「不想架獨立向量 DB」的中小嵌入場景，提供一個單檔就地方案**——與他對 EverOS/Milvus「規模與複雜度不符」的顧慮正好相反。
- 但他已在評估「長上下文取代 VectorDB+RAG」（DeepSeek V4），若該方向定案，**整個向量資料庫層級的需求都可能被架構降維**，此為本標的最重要的外部不確定因素。
- 第二大腦對 sqlite-vec 無任何直接記錄；本段為依其既有準則與脈絡的推論，非其已下結論。

---

## 附錄：資料來源

| 來源 | 內容 | 抓取日期 |
|---|---|---|
| repo metadata（gh api） | stars=7990、Apache-2.0、main、2024-04 建立、2026-08 活躍、描述 | 2026-08-09 |
| 官方 raw README | 定位、安裝、範例、pre-v1、sqlite-vss 後繼、Mozilla 贊助 | 2026-08-09 |
| 官方 docs introduction | runs everywhere、pure SQL、no server | 2026-08-09 |
| 官方 docs API Reference | float32/int8/bit、L2/cosine/hamming、BLOB subtype 223/224/225、量化 | 2026-08-09 |
| 官方 docs vec0 | metadata(16)/partition(4)/auxiliary(16)、KNN `match+order by distance limit k`、shard | 2026-08-09 |
| 第二大腦 MyBrain | 技術取捨準則、判定總表、DeepSeek V4 / EverOS / context-mode / codebase-memory-mcp | 2026-08-04 鏡像 |
