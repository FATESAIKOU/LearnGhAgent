# 232_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1 的任務是取得 macro 的 repo metadata 與主要文件。標的為 `macro-inc/macro`——開源團隊工作台＋團隊級記憶系統。此為 R1 首輪調研，無前輪對話。Step 1 已定調：需釐清 macro 實際側重「工作台」還是「記憶系統」，並與第二大腦既有的 4 個 Reject 判定（TencentDB-Agent-Memory、Buzz、Delta、EverOS）對照。C1 聚焦「取得事實」，不評論好壞。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view macro-inc/macro` | 取得 repo metadata | 確認 stars、license、語言、更新時間 | 3,199 stars、AGPL-3.0、Rust 為主、main 分支、2026-08-15 更新、homepage macro.com |
| `gh api repos/macro-inc/macro` | 補 metadata | 確認 topics、forks | 314 forks；topics 含 agent/ai/mcp/crm/email/workspace/slack-alternative 等 20 個 |
| 抓 README.md（raw） | 理解產品定位與功能 | 掌握「解決什麼問題」與核心機制 | 完整 README：all-in-one workspace（email+chat+docs+tasks+agents+CRM），@linked 雙向圖、團隊級記憶、AGPLv3 |
| 抓 repo 根目錄清單 | 了解程式結構 | 判斷關鍵子文件 | 80+ crates 的 Rust Cargo workspace；docs/ 僅 4 個內部文件（RUNNING_LOCALLY 等） |
| 抓 AGENTS.md（CLAUDE.md） | 了解架構 | 確認技術棧與資料層 | Rust 微服務；MacroDB(Postgres)+ContactsDB+S3+Redis+OpenSearch+DynamoDB |
| webfetch docs.macro.com/llms.txt | 取得文件索引 | 盤點官方文件 | 完整索引：product/、concepts/、AI/mcp/、integrations/、account/、changelog/ |
| webfetch product/agents | 理解 agent 與記憶 | 確認團隊級記憶機制 | agents 從 unified memory 工作；@Macro 進 channel；automation 排程；MCP server |
| webfetch product/unified-memory | 理解記憶核心 | 確認記憶如何生成 | 每晚 cron 從 email/messages/tasks/docs/calls 合成一次；個人 vs 團隊記憶；markdown 儲存 |
| webfetch concepts/blocks | 理解資料模型 | 確認 @link 與 CRDT | 一切皆 block；Loro CRDT + Cloudflare Durable Objects；雙向 References |
| webfetch faq | 理解定位與授權 | 確認比較對象與 self-host | 對比 Notion/Superhuman/Slack；AGPLv3（2026-05-31 由 BSL 轉全開源）；self-host 非主要 focus |
| webfetch product/docs | 理解 docs 機制 | 確認 CRDT 協作細節 | markdown-native、CRDT 即時協作、版本歷史/fork、agent 可編輯 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata | gh repo view / api | 3,199 stars、AGPL-3.0、Rust、main、2026-08 更新、314 forks |
| 產品定位 | README + FAQ | all-in-one workspace；「公司不可計算」→ 單一系統重設計 |
| 核心機制 | README + blocks + docs | 一切皆 block；@mention 建立雙向圖；CRDT 即時協作；channel-based 權限 |
| 團隊級記憶 | unified-memory + agents | 每晚 cron 合成一次；個人 vs 團隊記憶；markdown 儲存；MCP 對外 |
| 授權與 self-host | FAQ | AGPLv3（2026-05-31 由 BSL 轉）；self-host 非主要 focus |
| 技術棧 | AGENTS.md | Rust 微服務；Postgres+S3+Redis+OpenSearch+DynamoDB；SolidJS 前端 |
| 與既有 Reject 方案關係 | 對照 Step 1 | macro 同時涵蓋 Buzz(工作台)＋TencentDB-Agent-Memory(團隊記憶)＋EverOS(跨 session 記憶) 的問題域 |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 資料來源優先級 | 官方文件 / 第三方文章 / 社群討論 | 官方文件優先 | README + docs.macro.com 提供最權威、最新的定位與機制描述 |
| 記憶機制來源 | README 一句話 / 專屬 unified-memory 頁 | 專屬頁 | 記憶是標的的核心，需完整機制（cron 合成、個人 vs 團隊、markdown 儲存） |
| 是否查 self-host | 是 / 否 | 是 | 使用者重視「資訊隨組織自我維護」，self-host 可行性影響採用判準 |
| 是否查授權 | 是 / 否 | 是 | AGPLv3 是採用重大前提，且 2026-05 才由 BSL 轉全開源，屬關鍵事實 |
| 是否深入 MCP 工具清單 | 是 / 否 | 否（留 C2） | C1 只需定位；MCP 工具面（agents 對外能力）留待 C2 補查 |
