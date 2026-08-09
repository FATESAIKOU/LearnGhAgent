# sqlite-vec 技術解析報告

> 調研標的：`asg017/sqlite-vec`（SQLite 的向量搜尋擴充）
> 資料來源：repo README / ARCHITECTURE.md / 官方 docs / benchmarks-ann / release 資訊（2026-08 擷取）
> 本報告為 harness 測試案例（PR #193），非真實導入決策。

---

## 1. 這個技術解決什麼問題？

**一句話**：sqlite-vec 解決「在 SQLite 這個單一檔案、零伺服器、隨處可跑的資料庫裡，直接做向量儲存與 KNN（最近鄰）搜尋」的問題，讓應用不需要為了向量檢索而額外架設一套獨立的向量資料庫。

具體拆解它解決的痛點：

| 痛點 | 說明 |
|---|---|
| 向量資料與業務資料分離 | 一般應用把「文字/數值資料」放 SQLite，把「向量」放另一套向量庫，兩邊要同步、要維護兩套系統 |
| 部署複雜度 | 獨立向量資料庫（pgvector 需 PostgreSQL、Chroma 需獨立 process）增加部署與維運成本 |
| 本地/邊緣場景 | 手機、瀏覽器（WASM）、Raspberry Pi 等環境跑不起完整資料庫伺服器，需要極輕量的方案 |
| 資料庫遷移成本 | 已有 SQLite 的應用要加向量功能，若換成 PostgreSQL 或獨立向量庫，需大改資料層 |

**模糊之處**：官方定位是「extremely small, fast enough」——「fast enough」是主觀形容，沒有給出絕對的效能承諾。適用規模的邊界（幾百萬向量？幾千萬？）官方只給基準資料，沒有給「超過多少就該換」的明確閘門。這點在 §3 與 §4 會用基準資料與替代方案補足。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章中明確提到的背景

- **前身 sqlite-vss**：sqlite-vec 是 `sqlite-vss` 的後繼者（successor）。sqlite-vss 依賴 Faiss 等外部 C++ 函式庫，編譯與跨平台支援困難；sqlite-vec 改寫為**純 C、零依賴**，解決了前身「依賴重、難編譯、難跨平台」的問題。
- **Mozilla Builders 贊助**：官方文件明示這是 Mozilla Builders 專案，目標是「enable more powerful local AI applications」——即強化**本地 AI 應用**，呼應「向量搜尋應該能在本地、離線、單機跑」的需求。

### 2.2 通用技術背景（非文章明寫，由調研補上）

- **向量檢索的興起**：LLM 時代，RAG（檢索增強生成）需要把文件切成 chunk、embedding 成向量、再依語意相似度檢索。這催生了「向量資料庫」這個品類。
- **向量資料庫的兩條路線**：
  1. **獨立向量資料庫**（Chroma、Milvus、Qdrant、Weaviate）：專為向量設計，功能完整但需獨立部署。
  2. **嵌入式/擴充式**（sqlite-vec、pgvector、LanceDB）：把向量能力塞進既有資料庫，犧牲部分功能換取部署簡單。
- **SQLite 的定位**：SQLite 是嵌入式資料庫之王，單一檔案、零伺服器、隨處可跑。把向量搜尋做成 SQLite 擴充，等於讓「最普及的嵌入式資料庫」直接獲得向量能力，符合「本地優先、零維運」的趨勢。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 核心機制：`vec0` virtual table

sqlite-vec 透過 SQLite 的 **virtual table** 機制，提供一個名為 `vec0` 的虛擬表。使用者用標準 SQL 建立、插入、查詢向量：

```sql
-- 建立：宣告向量欄位與維度
create virtual table vec_examples using vec0(
  sample_embedding float[8]
);

-- 插入：向量以 JSON 或緊湊二進位提供
insert into vec_examples(rowid, sample_embedding)
  values (1, '[-0.200, 0.250, 0.341, -0.211, 0.645, 0.935, -0.316, -0.924]');

-- KNN 查詢：match + order by distance + limit
select rowid, distance
from vec_examples
where sample_embedding match '[0.890, 0.544, 0.825, 0.961, 0.358, 0.0196, 0.521, 0.175]'
order by distance
limit 2;
```

### 3.2 支援的向量型別與距離

| 向量型別 | 說明 | 距離函式 |
|---|---|---|
| `float` | 32-bit 浮點向量 | L2、cosine |
| `int8` | 8-bit 整數向量（量化） | L2、cosine |
| `bit` | 二進位向量 | hamming |

支援 `vec_f32`、`vec_int8`、`vec_bit` 等建構函式，以及 binary / int8 量化來壓縮儲存。

### 3.3 非向量欄位：metadata / partition key / auxiliary

`vec0` 支援三種非向量欄位，讓向量與業務資料能共存於同一張表：

| 欄位型別 | 用途 |
|---|---|
| **metadata** | 儲存非向量資料，KNN 查詢時一併回傳（不參與距離計算） |
| **partition key** | 分區鍵，可把向量依某欄位分組，查詢時只搜特定分區 |
| **auxiliary** | 輔助欄位，用於過濾或 join |

### 3.4 底層實作（ARCHITECTURE.md）

- **shadow tables**：`vec0` 內部用多張 shadow table 儲存資料——`chunks`、`rowids`、`vector_chunks`、`auxiliary`、`metadata`。
- **idxStr 查詢計畫**：SQLite 的 virtual table 透過 `idxStr` 字串傳遞查詢計畫，sqlite-vec 支援三種：
  - `fullscan`：全表掃描（暴力比對）
  - `point`：單點查詢
  - `KNN`：最近鄰查詢（走索引）

### 3.5 適用規模（benchmarks-ann）

官方基準（`benchmarks-ann/`）提供規模測試資料：

| 基準 | 規模 |
|---|---|
| `cohere1m` | 768 維 / 100 萬向量 |
| `cohere10m` | 1000 萬向量 |

支援的索引/搜尋策略：**brute-force**（暴力）、**rescore**（重排）、**IVF**（倒排檔案）、**DiskANN**（磁碟導向的近似最近鄰）。這表示 sqlite-vec 已具備從暴力掃描到近似索引的規模化手段。

### 3.6 成熟度

- 版本：v0.1.9（2026-03-31 release），docs 標 v0.1.10-alpha.4。
- **pre-v1 警告**：官方明示「expect breaking changes」，API 尚未穩定。
- 語言綁定：Python、Node.js、Ruby、Go、Rust、Datasette、rqlite、sqlite-utils 等。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **pgvector**（PostgreSQL 擴充） | 在 PostgreSQL 內加向量型別與 HNSW/IVFFlat 索引 | 已用或願用 PostgreSQL；需伺服器部署 | 需維運 PostgreSQL；向量與關聯資料同庫但綁定 PG | 向量與關聯查詢可 join，規模可到數億級，成熟度高 |
| **Chroma**（獨立向量資料庫） | 獨立 process 的向量庫，Python 原生，簡潔 API | 願接受獨立部署；以 Python 為主 | 多一套系統要維運；與業務資料分離需同步 | 上手快、功能完整，適合原型與中小規模 |
| **LanceDB**（嵌入式向量庫） | 嵌入式、零伺服器，基於 Lance columnar 格式 | 願用新格式；不需 SQL 語法 | 非 SQLite 生態；格式較新 | 本地/邊緣向量檢索，效能好，無伺服器 |
| **sqlite-vec**（本技術） | SQLite 擴充，`vec0` virtual table | 已用 SQLite；規模在百萬級內；可接受 pre-v1 | pre-v1 有 breaking change；規模上限低於獨立向量庫 | 零部署、與既有 SQLite 資料同庫、隨處可跑 |

### 4.2 切入點差異

| 方案 | 切入點 |
|---|---|
| **pgvector** | 把向量能力「塞進」你已經在用的關聯資料庫，換取 join 與成熟度，代價是綁定 PostgreSQL |
| **Chroma** | 專為向量設計的獨立庫，功能完整但引入第二套系統 |
| **LanceDB** | 嵌入式但非 SQLite，用新格式換效能 |
| **sqlite-vec** | 嵌入式且是 SQLite 擴充，用「零部署 + 同庫」換規模上限 |

### 4.3 對照第二大腦（FATESAIKOU/MyBrain）的既有判定

> 以下為查詢 MyBrain 的結果，標註 GitHub URL 與信任層級。

**sqlite-vec 本身**：第二大腦**沒有** sqlite-vec 主題。`技術/技術評估/` 下無對應檔。→ 不填空，此為新標的。

**向量資料庫 / VectorDB+RAG 的既有立場**：

| 來源 | 判定 | 信任層級 | 內容 |
|---|---|---|---|
| [DeepSeek V4](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/DeepSeek%20V4.md) | 試用（未定案） | `human:fatesaikou` / `stable` | 主張**長上下文可能取代 VectorDB+RAG**，規劃微型 PoC 對比現有 RAG 方案，尚未定案 |
| [Github 一週熱點 112](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Github%20一週熱點%20112.md) | Accept（qmd） | `human:fatesaikou` / `stable` | 「至少要試過一次向量搜尋」——對向量搜尋持正面嘗試態度 |
| [技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md) | 準則 | `claude-code/opus-5` / `draft`（**AI 草稿，未 review**） | 理解優先先自己兜、MVP→Feature 唯一閘門是能否影響個人 workflow、Reject≠沒價值、不追新 |

**與本報告結論的衝突點（查詢最有價值處）**：

1. **「長上下文取代 VectorDB+RAG」與 sqlite-vec 的定位衝突**：他的 DeepSeek V4 判定主張長上下文可能讓 VectorDB+RAG 失去必要性。若此立場成立，sqlite-vec 這類向量庫的價值會被削弱。**衝突點**：本報告 §1–§3 描述 sqlite-vec 的技術能力，但依他的既有立場，這可能不是他該優先投入的方向——他應先驗證「長上下文是否真的取代 RAG」再決定是否值得碰向量庫。此立場為「試用」未定案，故本報告不將其當成結論，僅註記。

2. **「理解優先先自己兜」與「用現成的比較快」**：他的準則（AI 草稿）主張不穩定或不熟悉就先自己兜。sqlite-vec 是 pre-v1（不穩定），依此準則他可能傾向自己兜一個理解本質，而非直接採用。**衝突點**：本報告 §4 把 sqlite-vec 列為「零部署」的誘因，但依他的準則，「零部署」不是採用理由——「能否影響個人 workflow」才是閘門。

3. **「不追新」**：sqlite-vec 是相對新的專案（pre-v1），依「不追新」原則，他不會因為「出現更好的替代」而汰換既有方案。**衝突點**：本報告不應暗示「sqlite-vec 比現有方案好所以該換」——他的汰換判準是「上游死沒死」，不是「有沒有更好的」。

> 註：以上準則檔為 `claude-code/opus-5` 產出的 **AI 草稿（draft）**，未經他本人 review，僅供參考，不當成定稿結論。

### 4.4 規模與取捨的收斂

| 規模 | 建議方向 | 理由 |
|---|---|---|
| 百萬級內、已用 SQLite、本地/邊緣 | sqlite-vec | 零部署、同庫、隨處可跑 |
| 數百萬～數億、需關聯查詢、已用 PG | pgvector | 成熟、可 join、規模大 |
| 需完整向量功能、願獨立部署 | Chroma / Qdrant / Milvus | 功能完整、規模大 |
| 本地/邊緣、不需 SQL、願用新格式 | LanceDB | 嵌入式、效能好 |

---

## 附錄：資料來源

- repo：https://github.com/asg017/sqlite-vec （7,990 stars、Apache-2.0、2026-08-08 更新）
- README：https://raw.githubusercontent.com/asg017/sqlite-vec/main/README.md
- ARCHITECTURE.md：shadow tables + idxStr 查詢計畫
- 官方 docs：introduction / api-reference / vec0 / knn / performance
- benchmarks-ann：cohere1m / cohere10m 基準
- release：v0.1.9（2026-03-31），docs 標 v0.1.10-alpha.4
