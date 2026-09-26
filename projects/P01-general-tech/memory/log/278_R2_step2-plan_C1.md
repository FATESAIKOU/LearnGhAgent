# 278_R2_step2-plan_C1.md

## 狀況理解

R2 為質問型追問（觸發報告 §5 User Q&A），三問同一軸：**Hindsight 的複雜度是否正當**。R1 的 C1 已取回「機制怎麼運作」，但未回答「能否更簡單」與「哪些屬應用層、哪些被系統內建」。故本次 C1 不重取 README，而是**針對 Q1/Q2/Q3 取證**：

| 問 | 待證事實 |
|---|---|
| Q1 | Hindsight 的 `fact_type` 究竟分幾類？「事實 vs 推論」是否可用二元標籤表達？ |
| Q2 | 「推論→事實升級」是應用層設計，還是被內建在系統？觀察如何生成、可否手動寫入？ |
| Q3 | 存（retain）與取（recall）是否被包成複雜架構？複雜度是否可關閉、有無輕量路徑？ |

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` / `gh api` 取 metadata | 更新規模（R1 為 30,249） | 時間座標校準 | **30,858 stars**、3,335 forks、MIT、created 2025-10-30、pushed 2026-09-25、70 subscribers |
| 抓 `api/retain.mdx` | 證 Q1 儲存型別 | 確認可寫入的 fact_type | **可寫入的 `fact_type` 只有 `world` 與 `experience`（二元）**；軸是「誰在說」（bank 自身 vs 他人），非「事實 vs 推論」 |
| 抓 `api/memories.mdx` | 證 Q1/Q2 的可寫性 | 觀察可否直接寫 | 觀察是 **derived**；`PATCH` 觀察回 **400**；只能 curate 原始 world/experience fact（edit / invalidate / restore，state=valid\|invalidated，append-only 留審計軌跡） |
| 抓 `api/recall.mdx` | 證 Q1 檢索回傳型別 | 檢索端分類 | 回傳 `type` 仍是 `world`\|`experience`\|`observation`；`prefer_observations` 可讓觀察取代其來源 fact |
| 抓 `observations.mdx`＋`configuration.mdx` | **證 Q2：升級是否內建** | 觀察生成機制 | retain 後**背景自動** consolidate（`enable_auto_consolidation` 預設 true）；LLM 合成、帶 evidence quote＋proof count、矛盾時 refine 非 overwrite；**可整包關閉**（`enable_observations:false`）或改手動觸發 |
| 抓 `mental-models.mdx` | 證「推論」最高層 | standing answer 誰寫 | mental model 由**使用者定義問題**、系統跑 reflect 產出、背景重寫；讀取為 DB read 無 LLM |
| 抓 `retrieval.md` | **證 Q3：取的複雜度** | 檢索管線 | TEMPR 四路並行（semantic/BM25 5 後端/graph/temporal）→ RRF → cross-encoder rerank → 三項乘性加成 → token 截斷 |
| 抓 `installation.md`／`performance.md` | 證 Q3：部署重量 | 門檻量化 | Full image ~9GB／1.5–2GB RAM；Retain 500ms–2s/批（LLM 抽取為瓶頸）；Recall 100–600ms；需 PostgreSQL 14+ 與向量擴充 |
| 抓 `api/memory-banks.mdx` | 證 Q3：可調與輕量模式 | 有無 bypass | `retain_extraction_mode` 可設 `chunks`（**不呼叫 LLM**）、`verbatim`（LLM 僅抽 metadata）；`retain_mission`／`observations_mission` 可限定抽取與合成範圍 |
| 讀 arXiv 2512.12818 摘要 | 核 Q2 官方原始定義 | 對齊論文措辭 | 四網路：world facts／agent experiences／**synthesized entity summaries**／**evolving beliefs**；三操作 retain/recall/reflect |
| 讀 `/tmp/mybrain/抽象理解/本質洞察/統一的兩端稅.md` | 取 Q3 判準原文 | 對照尺 | 判準＝「同一件事的不同實作 vs 不同的事」；重量不是判準，分界才是 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Q1 儲存可分幾類 | 讀 retain/memories/recall API | **可寫入僅 world／experience 二元**；observation 為衍生，不可寫；故「事實／推論」非儲存端標籤，而是「證據 vs 衍生」的**層級結構** |
| Q1 使用者能否自行標 | 讀 memories curate | 可 edit／invalidate，但 **fact_type 只能改 world↔experience**，不能標成「推論」 |
| Q2 升級是否內建 | 讀 observations＋configuration | **是內建且預設開啟**（背景 consolidation）；可關閉或改手動，但預設行為就是系統自動做 |
| Q2 是「升級成事實」嗎 | 讀 observations/mental-models | **不是**。觀察永遠是獨立 type，**不會被升格成 world／experience**；三層各自獨立、越上層越「已定」 |
| Q3 取是否複雜 | 讀 retrieval.md | **是**。四路並行＋RRF＋cross-encoder＋三重加成＋token 截斷，為工程化多階段管線 |
| Q3 存是否複雜 | 讀 retain＋installation | **是**。每 chunk 跑 LLM 抽取＋實體解析＋建圖＋embedding；部署需 PostgreSQL＋向量擴充，full image ~9GB |
| Q3 有無輕量路徑 | 讀 memory-banks／installation | 有：`chunks` 模式不呼叫 LLM、slim image ~500MB、可外接 embeddings/reranker；但四路檢索與固化仍需關閉或承擔 |
| 官方原始措辭 | 讀 arXiv 摘要 | 四網路含「evolving beliefs」，與 observations 對應；官方亦承認現行記憶系統「blur the line between evidence and inference」——正是 Q1/Q2 的原始問題意識 |

**尚未取得（留 Step 3）**：與使用者 MyBrain（append-only＋人 review＋validate/reindex CI）的逐點機制對照；Q3「若複雜是否該 reject」的判準套用結論。

## 其中的決斷點

| 意思決定面向 | 可選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研範圍 | 重跑 R1 全鏈 / 只補 Q1–Q3 證據 | 只補 Q1–Q3 | R2 意圖是質疑架構，非重新介紹技術；重跑會與 R1 重工 |
| 抓哪些檔 | README / 機制 API 與設定 | retain·memories·recall·observations·mental-models·retrieval·installation | 這批直接對應「型別可否二元」「升級是否內建」「存取是否複雜」三問 |
| Q1 證據策略 | 憑 R1 印象回答 / 查 fact_type 與 PATCH 行為 | 查 API 定義 | 「能否只打兩標」必須落到可寫入型別的事實，不能憑印象 |
| 是否讀 mybrain 判準 | 只讀技術文件 / 併讀統一的兩端稅 | 併讀 | Q3 的 reject 觸發點是他的判準，Step 3 需原文對照，C1 先備妥 |
| 資料時效 | 沿用 R1 數字 / 重取 | 重取 | stars 與版本會變，重新標定時間座標避免引用過期數字 |
