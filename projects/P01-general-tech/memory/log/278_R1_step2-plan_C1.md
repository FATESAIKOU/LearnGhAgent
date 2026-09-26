# 278_R1_step2-plan_C1.md

## 狀況理解

R1 首輪，Step 1 已定標的＝**Hindsight**（vectorize-io/hindsight），須以「解決什麼問題／為何發生／如何解決／替代方案」為軸，並對照第二大腦同域既有 Reject 判定（EverOS、TencentDB-Agent-Memory、macro）與他自建的 MyBrain。C1 任務＝document skill 標準動作 1+2：取得 repo metadata 與主要文件（README、關鍵子文件），並補初步背景脈絡。C1 只負責「取原始資料」，不收斂成報告（收斂留給 C2/Step 3）。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` 取 metadata | 確認規模、授權、活躍度 | 建立基本画像 | MIT、Python、**30,249 stars**、3,240 forks、30 contributors、open issues 134、created **2025-10-30**、最新 release **v0.10.1（2026-09-21）**、pushed 2026-09-25。repo 年齡約 11 個月，活躍 |
| `gh api` 取 tree | 定位子文件 | 找到關鍵 docs | 主體為 Python monorepo；`hindsight-docs/docs/` 下有完整開發文件（retain/retrieval/reflect/observations/mental-models/rag-vs-hindsight 等） |
| 取 README.md（raw） | 讀官方定位與 Quick Start | 掌握對外敘事 | 定位「Agent Memory That Learns」；主打 LongMemEval SOTA；三操作 retain/recall/reflect；memory types 四層；60+ integrations；Docker／pip／Helm／Cloud 四種部署 |
| 取 `developer/retain.md` | 機制（寫入） | 理解 ingest 流程 | retain→LLM 抽 facts/temporal/entities/relations→normalize 成 canonical entities、time series、index；fact 分 experience（bank 自身第一人稱）vs world（他人事實），依「誰在說」判定 |
| 取 `developer/retrieval.md` | 機制（檢索） | 理解 recall | **TEMPR 四路並行**：semantic + keyword(BM25，5 後端) + graph traversal + temporal；RRF 融合後 cross-encoder rerank |
| 取 `developer/reflect.mdx` | 機制（推理） | 理解 reflect | **agentic loop**（最多 10 迭代、強制取證、citation 驗證）；階層式檢索 mental models→observations→raw facts；disposition 三 traits（skepticism/literalism/empathy 1-5）＋natural-language mission |
| 取 `developer/observations.mdx` | 機制（固化） | 理解 consolidation | retain 後背景自動 consolidate 成 observations；去重、evidence+proof count、**refined 而非 overwrite**；矛盾時保留演進史；dedup threshold 預設 0.97 |
| 取 `developer/mental-models.mdx` | 機制（快取） | 理解 mental model | 對一個問題的 standing answer，背景重寫；讀取是 DB read（無 LLM）；incremental refresh 抗漂移；tag 決定 scope 與可見性 |
| 取 `developer/rag-vs-hindsight.md` | 官方對照 | 取得官方替代方案論述 | 對 RAG 逐項比較：檢索策略、multi-hop、temporal、entity、consolidation、disposition |
| 取 arXiv 2512.12818 摘要 | 學術來源與數據 | 佐證 benchmark 主張 | 題名「Hindsight is 20/20...」；作者含 Latimer 等；機構線索：Virginia Tech Sanghani Center、The Washington Post、Vectorize。20B 模型 39%→83.6%，scaled 91.4% (LongMemEval)、89.61% (LoCoMo) |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo 存在與規模 | gh repo view | 確認；30k stars、MIT、2025-10 建立、2026-09 仍週更 |
| 主要文件 | README + 5 份 core docs | 全部取得，機制鏈完整（retain→recall→reflect，底層 observations/mental models） |
| 官方問題陳述 | README/論文/rag-vs-hindsight | 明確：「多數記憶系統只檢索對話歷史，Hindsight 要讓 agent 學習而非只記憶」 |
| 三關鍵詞對應 | 影片 vs 官方文件 | 一致：Retain=寫入、Recall=四路檢索、Reflect=agentic 推理 |
| 學術背書 | arXiv 摘要＋機構 | 有論文與獨立機構複現（Virginia Tech / WaPo），論文號 2512.12818 |
| 尚未取得 | 部署成本細節、實際落地案例、與 MyBrain 逐點對照 | 留待 C2/Step 3 |
| 部署形態 | README | Docker／bare-metal(pip)／Helm／Python embedded／Hindsight Cloud；儲存為 PostgreSQL+pgvector 或 Oracle 23ai |

## 其中的決斷點

| 意思決定面向 | 可選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 資料來源 | 只看 README／README+子文件+論文 | README+子文件+論文 | 機制細節集中在 docs/，僅 README 會漏掉 consolidation、TEMPR、disposition 等關鍵 |
| 是否抓官網 | 抓 hindsight.vectorize.io／直接抓 repo docs | 直取 repo docs raw | repo docs 即官網內容來源，raw 更穩、無反爬 |
| 論文定位 | 視為行銷／視為可核來源 | 視為可核來源並記錄機構 | arXiv 為具體可引來源，且明載獨立複現機構 |
| 影片觀點處理 | 直接採信／以官方文件覆核 | 以官方文件覆核 | 影片「落地難」需用實際機制與部署門檻檢核，不可照抄 |
| 是否納入同域對照 | C1 就對照 MyBrain／留 C2 | 留 C2 | C1 專注取原始資料，避免與 Step 1 重工 |
