# 231_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認調研標的為 **semantica（https://github.com/semantica-agi/semantica）——面向可審計 AI 系統的語義圖譜基礎設施**。屬典型工作流 2（給定 GitHub 連結 → 分析 → 產出報告）。本 sub-step C1 依 document skill 標準動作執行：①取得 repo metadata ②擷取 README 與關鍵子文件 ③補查背景脈絡。C1 目標：建立標的的完整事實基礎（定位、架構、模組、差異化、合規面向），供 C2 收斂成報告。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 do/skills/document/SKILL.md | 確認標準調研流程 | 依規範執行 | 規範確認：metadata → 主要文件 → 背景脈絡；GitHub repo 用 gh api / gh repo view |
| `gh repo view semantica-agi/semantica` | 取得 repo metadata | 掌握基本盤 | 取得：created 2025-06-25、MIT、Python、**7797 stars**、updated 2026-08-15、main 分支、非 fork/archived；description「Graph-Native Infrastructure for Context and Accountable AI Systems」 |
| `gh api .../contents/` 列根目錄 | 盤點文件結構 | 定位關鍵子文件 | 取得：README、ARCHITECTURE.md、CHANGELOG.md、docs/、cookbook/、examples/、integrations/、mcp/、plugins/、semantica/（套件本體）、tests/ |
| 抓取 README.md 全文（1619 行） | 取得「主要文件」核心論述 | 掌握定位、架構、模組、差異化 | 取得完整內容（見下方關鍵事實） |
| 抓取 ARCHITECTURE.md | 取得完整資料流與決策生命週期 | 補足架構細節 | 取得 Mermaid 全管線圖與 Decision Intelligence 五階段（Record→Link→Query→Govern→Audit Export） |
| 抓取 docs/concepts.md | 取得核心概念（KG vs Vector vs GraphRAG） | 補足心智模型 | 取得三種檢索方式對照、NER/關係抽取方法（pattern/ml/llm）、KG 優勢（traversal/explainability/temporal/conflict/schema） |
| 抓取 docs/governance.md | 取得專案治理與維護者 | 補足背景 | 取得：由 **Hawksight AI** 維護、開放治理、SemVer 版本策略、MIT |
| 抓取 docs/faq.md | 取得定位澄清與合規宣稱 | 補足差異化與合規 | 取得：非 LangChain/LlamaIndex 替代品而是其上 accountability layer；合規 HIPAA/SOX/GDPR/FDA 21 CFR Part 11；v0.6.5（2026-08）、1000+ tests |
| 抓取 CHANGELOG.md 開頭 | 取得近期演進與成熟度 | 補足成熟度證據 | 取得 Unreleased 新增 retraction/purge（GDPR Art.17 抹除）、metric_errors 等，顯示審計軌跡與時態機制持續強化 |

**關鍵技術事實（供 C2 收斂）：**
- **定位**：自稱「The Open Source Palantir for AI Agents」；在 LLM／vector store／agent framework 之下作為**確定性基礎設施層**，graph 建構、reasoning、provenance 皆不需 LLM。
- **核心問題**：多數 AI agent 無軌跡——只存 embeddings 不存意義，context 無法解釋、決策無法審計；在受監管領域（放貸、醫療、法律、政府、國防）這是合規曝險而非不便。
- **五大能力**：Context Graphs（結構化可查詢的 agent 所知/所決/所推理）、Decision Intelligence（決策為一等公民物件）、AI Governance & Ontology（SHACL/OWL/SKOS）、Full Auditability（W3C PROV-O）、Deterministic Reasoning（forward chaining/Rete/Datalog/SPARQL）。
- **管線**：Sources → Ingest → Parse → Normalize → Split → Extract → Conflict Detection → Deduplication → KG → [Ontology·Reasoning·Provenance·Decisions] → Enriched KG → Vector+Polyglot Graph Store → Export/Visualize/REST·MCP·CLI。
- **決策生命週期**：record_decision() → add_causal_relationship()（CAUSED/INFLUENCED/PRECEDENT_FOR）→ find_similar/trace_chain/analyze_impact → check_decision_rules() → export W3C PROV-O/CSV/JSON。
- **差異化對照**（README 表格）：vs Vector DB+RAG 與 Plain LLM Memory——Semantica 有 decision history、provenance、deterministic reasoning、conflict detection、time travel、compliance export、policy enforcement、entity resolution、multi-agent shared context。
- **儲存**：polyglot——RDF（Oxigraph/Blazegraph/Jena/RDF4J）＋ LPG（Neo4j/FalkorDB/AGE/Neptune）＋ vector store，可換不鎖 vendor。
- **企業資料平台**：原生 Databricks（Unity Catalog+Delta Lake）與 Snowflake connector，免匯出第三方 SaaS。
- **整合**：Agno、MCP server、CLI（50+ 命令）、REST API（100+ endpoints）、Knowledge Explorer 視覺化。
- **成熟度**：v0.6.5（2026-08）、1000+ tests、MIT、7797 stars、Hawksight AI 維護。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata | gh repo view | 取得完整基本盤（stars/license/語言/更新/分支） |
| 主要文件 | README 全文＋ARCHITECTURE | 取得定位、管線、決策生命週期、模組清單 |
| 核心概念 | docs/concepts | 取得 KG vs Vector vs GraphRAG 對照與抽取方法 |
| 治理與維護 | docs/governance | 確認 Hawksight AI 維護、MIT、開放治理 |
| 合規宣稱 | docs/faq | 確認 HIPAA/SOX/GDPR/FDA 21 CFR Part 11 目標 |
| 成熟度證據 | CHANGELOG | 確認審計軌跡/時態/抹除機制持續強化 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| metadata 取得 | (A) gh repo view (B) 僅 webfetch | A | GitHub repo 標的，gh api 最直接且含 license/語言/更新時間 |
| 子文件範圍 | (A) 僅 README (B) README＋ARCHITECTURE＋concepts＋governance＋faq＋CHANGELOG | B | 標的定位「可審計 AI 系統」，需架構（ARCHITECTURE）、概念（concepts）、治理（governance）、合規（faq）、成熟度（CHANGELOG）五面向才足以支撐報告 |
| 背景脈絡補查 | (A) 本輪即做網路搜尋 (B) 留待 C2 | B | C1 聚焦一手文件；替代方案（Palantir、GraphRAG、向量庫、agent memory 等）與外部背景留給 C2 網路補查，避免 C1 過長 |
| 下一步 C2 方向 | (A) 直接撰寫報告 (B) 補查替代方案與背景 | B | 報告 §4 需 2～4 個替代方案（Palantir、GraphRAG、向量庫、agent memory 等）並給 DA 表，需 C2 網路補查 |
