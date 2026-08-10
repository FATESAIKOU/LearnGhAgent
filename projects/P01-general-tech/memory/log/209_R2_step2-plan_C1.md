# 209_R2_step2-plan_C1.md

## 狀況理解

R2 是使用者「接近 Reject 前的最後追問」，三問分別是：①與自建 MyBrain 在解決問題/方式上如何比較；②是否算組織級知識庫、有無人 Review＋存取規則、效果如何；③誰規定 raw session 該在哪一層留/排除、誰驗證、如何避免腐化。R1 報告已含四資產、L0-L3、ACL 概要，但 Q2/Q3 屬 R1 未深挖的「治理細節」（人 Review 機制、分層留取規則、驗證/腐化防護），故本 C1 需針對這三問補查官方文件第一手證據，而非重做 R1 的標的概覽。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 R1 report 與 R1 C1 log | 掌握已覆蓋範圍，避免重做 | 定位 Q2/Q3 的資訊缺口 | 確認 R1 已含四資產/L0-L3/ACL 概要，但缺「Review 具體做法」「分層誰規定」「腐化防護」細節 |
| 讀取 R2 step1 log 與 review | 承接 R2 意圖與 QA 觸發條件 | 確認本輪範圍 | 三問皆質問型句構，觸發 §5 Q&A；Q2/Q3 須補查官方治理細節 |
| `gh repo view` 取得最新 metadata | 確認 repo 現況 | 掌握 stars/分支/更新 | 19,182 stars、License=other（非 R1 所記 MIT）、TypeScript、預設分支 `feat/server_team`、2026-08-10 更新 |
| 列出 repo 樹中所有 .md 文件 | 定位治理相關文件 | 選定 C1 抓取範圍 | 除四服務 README 外，另有 INSTALL/ROADMAP/CHANGELOG/遷移腳本等 |
| 抓取根 README + MemoryCore/Panel/Proxy/Knowledge README + ROADMAP | 補查治理、分層、驗證一手法 | 回答 Q2/Q3 所需 | 取得：人 Review 流程、ACL 四可見度、L0-L3 分層機制、pipeline 非同步、ROADMAP 承認抽取品質瓶頸 |

**Q2（人 Review＋存取規則）第一手證據**：
- 根 README：「Personal Skills are private by default; **after review**, they can be shared with the team and assigned to other Agents」→ 人 Review 是 Skill 從 private 升級為 team 的門檻。
- Memory Hub 角色：global System Admin + Team-level Admin/Member；Asset ownership 由 Owner 持有（Owner 自動具管理權）。
- ACL 四可見度：`private`（僅 Owner 可讀，連 team admin 都不能）/ `team`（成員可讀，Owner/Admin 管理）/ `restricted`（User/Role/Agent ACL 精確授權）/ `agent`（配給特定 Agent）。新 Chat Memory 與 Skill 預設 `private`，分享是明確動作。

**Q3（誰規定分層留取、誰驗證、如何避免腐化）第一手證據**：
- 分層生成：L0 Conversation → L1 Atom → L2 Scenario → L3 Persona，由**非同步 pipeline** 逐層精煉，抽取需 LLM credential（「memory extraction and aggregation require valid credentials」），pipeline state 在 process 內維護。
- 分層「留什麼/排除什麼」：由**抽取用的 LLM prompt** 決定，**無顯式人類驗證閘門**；文件未提 dedup/衝突合併/回滾機制。
- **ROADMAP 自承弱點**：v2.0.1 規劃「User- and team-level custom prompts」——官方原句「Memory extraction quality depends on domain context… A single hard-coded prompt cannot serve both」，且「Editing custom prompts from the Memory Hub panel is **not supported yet**」→ 官方承認分層抽取品質受限於單一硬編碼 prompt，且尚未支援面板編輯。
- ROADMAP v2.0.1 亦規劃 Wiki 建置改為 bounded-concurrency pipeline（失敗頁獨立重試、進度可視），暗示現行建置有黑箱與串行問題。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 人 Review 是否存在 | 根 README Skill review 流程 | 存在於 Skill 層（private→team 需 review），但 Chat Memory/Wiki/CodeGraph 未見同等強制 human review |
| 存取規則是否建立 | ACL 四可見度 + 雙層角色 + ownership | 有完整 ACL 模型，private 預設、分享需明確動作 |
| 誰規定分層留取 | 抽取機制描述 + ROADMAP | 由非同步 pipeline＋LLM 抽取 prompt 決定；無人類驗證閘門；ROADMAP 承認單一硬編碼 prompt 品質瓶頸且未支援面板改 |
| 腐化防護 | grep dedup/衝突/回滾 | 文件未見 dedup/衝突合併/回滾機制描述 |
| metadata 是否更新 | gh repo view | stars 增至 19,182，License 標為 `other`（需在 C2 釐清 R1 所記 MIT 是否過時），仍活躍 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| C1 抓取範圍 | (A) 僅根 README (B) 連同各服務 README + ROADMAP | B | Q2/Q3 問「有無人 Review、存取規則、誰規定分層、如何防腐化」，皆需跨 Core/Panel/Proxy/ROADMAP 的治理細節，僅根 README 不足 |
| 是否讀原始碼 | (A) 讀 pipeline src (B) 以 README/ROADMAP 為準，原始碼留待 C2 視需要 | B | C1 目標是確立官方聲稱的治理模型；ROADMAP 自承弱點已足供回答 Q3，原始碼細節（如實際有無 dedup）留待 C2 對照腐化防護時再深入 |
| R1 所記 License=MIT 與現 metadata 標 `other` 衝突 | (A) 沿用 R1 (B) 於 C2 釐清 | B | 屬事實性差異，需在 C2 品質保證時確認，避免報告矛盾 |
