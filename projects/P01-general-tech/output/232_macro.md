# macro 技術分析報告

> 調研標的：https://github.com/macro-inc/macro
> 開源團隊工作台（team workspace）＋ 團隊級記憶系統（team-level memory）
> 3,199 stars · AGPL-3.0 · Rust 為主 · main 分支 · 2026-08-15 更新 · 314 forks
> 授權：AGPLv3（2026-05-31 由 BSL 轉全開源）

---

## 1. 這個技術解決什麼問題？

**macro 解決的是「公司／團隊的運作資訊無法被單一系統計算」的問題——把 email、聊天、文件、任務、CRM、Agent 全部收進一個以「雙向連結圖」為底層的 all-in-one workspace，讓團隊的知識與工作流成為可被 Agent 讀取、檢索、自動化的單一資料源。**

官方定位一句話：**「Companies are not computable.」**（公司不可計算）——團隊的資訊散落在 email、Slack、Notion、Jira、CRM 等彼此隔離的工具裡，沒有一個系統能把它們當成一個整體來查詢或運算。macro 的解法是把這些全部收進單一系統，並以「一切皆 block ＋ @mention 雙向連結」建立可計算的知識圖。

具體拆成兩層問題：

| 問題層 | 具體表現 |
|---|---|
| **工作台碎片化** | email、聊天、文件、任務、CRM 分屬不同工具，Agent 無法跨工具搬運上下文；人要在工具間切換 |
| **團隊級記憶缺失** | 團隊的決策、偏好、專案脈絡散落在各 session 與各工具，Agent 每次都要重新理解，無法累積 |

**模糊之處**：
- 「團隊級記憶」的邊界定義模糊——官方同時宣稱「個人 vs 團隊記憶」兩層，但「團隊」的規模（2 人 vs 200 人）與治理需求差異很大，官方未區分。
- 「公司不可計算」是行銷式命題，官方未給出可量化的「計算」定義（是檢索？是自動化？是推理？），也無第三方 benchmark 驗證其記憶品質。
- 記憶由「每晚 cron 合成一次」產生，官方未說明合成失敗、衝突、過期資訊的處理機制（見 §3）。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **工具碎片化**：官方對比 Notion / Superhuman / Slack，指出團隊資訊散落在不同工具，沒有一個系統能把它們當成整體計算。這是「all-in-one workspace」的直接動機。
- **Agent 需要統一上下文**：官方定位 agents 從「unified memory」工作，而非各自從零理解。Agent 要能像人類同事一樣參與 email、聊天、任務，就需要一個共享的、可檢索的記憶層。
- **記憶需要被合成**：官方明確說明記憶由「每晚 cron 從 email/messages/tasks/docs/calls 合成一次」，即記憶不是即時寫入，而是定期從各來源聚合。

### 通用技術背景（文章中未明確提及）

- **LLM Agent 的無狀態本質**：每次對話結束後 context 即消失，Agent 無法跨 session 記住團隊脈絡。這是所有「Agent 記憶系統」要解決的共同根源（與使用者第二大腦中已評估的 EverOS、TencentDB-Agent-Memory 同源）。
- **Context Window 的物理限制**：無法把全部歷史塞進 context，記憶系統必須在「存多少」與「取多少」之間取捨。macro 用「每晚合成一次 + markdown 儲存 + 按需檢索」回應。
- **CRDT 即時協作**：macro 用 Loro CRDT + Cloudflare Durable Objects 做文件即時協作，這是「多人同時編輯同一份資料」的技術前提，也是「一切皆 block」能成立的底層。
- **開源授權轉變**：macro 2026-05-31 由 BSL 轉 AGPLv3，反映「開源團隊工作台」從商業閉源走向全開源的趨勢，但 AGPLv3 對 self-host 與商業整合有 copyleft 限制。

---

## 3. 這個技術是如何解決該問題的？

### 整體架構：一切皆 block ＋ 雙向連結圖 ＋ 每晚合成記憶

```
┌─────────────────────────────────────────────────────────────────────┐
│                    macro 架構                                          │
│                                                                       │
│  資料模型：一切皆 block（email/chat/doc/task/CRM/call）                │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  @mention 建立雙向 References（@linked 圖）                    │    │
│  │  Loro CRDT + Cloudflare Durable Objects（即時協作）            │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  團隊級記憶（unified memory）                                          │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  每晚 cron 從 email/messages/tasks/docs/calls 合成一次          │    │
│  │  個人 vs 團隊記憶兩層                                           │    │
│  │  markdown 儲存（人可讀、可版本化）                              │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  Agent 層                                                             │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  agents 從 unified memory 工作                                │    │
│  │  @Macro 進 channel（像同事一樣參與）                          │    │
│  │  automation 排程（定時任務）                                   │    │
│  │  MCP server（對外工具介面）                                   │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  技術棧：Rust 微服務 · MacroDB(Postgres)+ContactsDB+S3+Redis+         │
│          OpenSearch+DynamoDB · SolidJS 前端                           │
└─────────────────────────────────────────────────────────────────────┘
```

### 核心機制拆解

**1. 一切皆 block（資料模型）**
- email、聊天、文件、任務、CRM、通話全部抽象成統一的 block 單位。
- `@mention` 在 block 之間建立**雙向 References**（@linked 圖），形成可計算的知識圖。
- 用 **Loro CRDT + Cloudflare Durable Objects** 做即時協作，多人可同時編輯同一份資料。

**2. 團隊級記憶（unified memory）**
- 記憶不是即時寫入，而是**每晚 cron 從 email/messages/tasks/docs/calls 合成一次**。
- 分**個人記憶**與**團隊記憶**兩層。
- 以 **markdown 儲存**——人可讀、可版本化、可被 Agent 檢索。

**3. Agent 層**
- agents 從 unified memory 工作，而非各自從零理解。
- `@Macro` 進 channel，像人類同事一樣參與討論。
- automation 支援排程任務。
- 提供 **MCP server** 作為對外工具介面。

**4. 授權與 self-host**
- AGPLv3（2026-05-31 由 BSL 轉全開源）。
- self-host 非主要 focus（官方 FAQ 明示），主要走雲端 SaaS。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

> 本節對照使用者第二大腦（FATESAIKOU/MyBrain）的既有判定。**第二大腦中沒有 macro 的評估紀錄**（判定總表 88 筆中無此條目），但同屬「團隊級記憶／人與 Agent 協作工作台」領域已評估多個工具，以下對照其既有立場。

### 4.1 使用者既有判定的同類工具（對照第二大腦）

| 工具 | 使用者判定 | 判定理由（第二大腦） | 信任層級 |
|---|---|---|---|
| **TencentDB-Agent-Memory** | Reject | 團隊級 Agent 記憶系統；重點不是架構設計，而是讓資訊隨組織自我維護更新；沒有防腐化機制的大腦等同必定過期的文件 | `process:learn-gh-agent` / `draft`（AI 草稿，未 review） |
| **Buzz** | Reject | Block 的人與 Agent 協作工作台；規模過大難以採用且採用效果未知，個人使用不必要 | `process:learn-gh-agent` / `draft`（AI 草稿，未 review） |
| **Delta** | Reject | Zed 的 agent 協作環境；vendor 綁定、只是開發過程紀錄機制可自己兜、團隊效果難驗證 | `process:learn-gh-agent` / `draft`（AI 草稿，未 review） |
| **EverOS** | Reject | 團隊/組織級記憶治理；機制複雜規模大但無自組織驗證手段；泛用但未專門化 | `human:fatesaikou` / `stable` |
| **MyBrain**（自建） | 日常在用 | 個人級記憶系統；「人 review 當品質守門員」模型 | `human:fatesaikou` / `stable` |

> 信任層級說明：判定總表本身為 `draft`（`generated.by: ollama-cloud/deepseek-v4-flash`）。TencentDB-Agent-Memory、Buzz、Delta 三檔皆為 `process:learn-gh-agent` 產出且 `status: draft`——**是未經使用者 review 的 AI 草稿**，轉述時須保留餘地。EverOS 為 `human:fatesaikou` 本人撰寫且 `stable`，可直接當成其結論。

### 4.2 與使用者既有立場的衝突點（本節最有價值處）

**⚠️ 明確衝突：macro 同時涵蓋使用者已 Reject 的兩個問題域——「人與 Agent 協作工作台」（Buzz）與「團隊級記憶」（TencentDB-Agent-Memory / EverOS）。**

| 使用者已 Reject 的判定 | macro 對照 |
|---|---|
| **Buzz Reject**：規模過大難以採用、採用效果未知、個人使用不必要 | macro 是 all-in-one workspace，規模同樣大；且 self-host 非主要 focus，個人使用更難落地 |
| **TencentDB-Agent-Memory Reject**：重點不是架構設計，而是讓資訊隨組織自我維護更新；沒有防腐化機制的大腦等同必定過期的文件 | macro 的記憶由「每晚 cron 合成一次」產生，官方未說明合成失敗、衝突、過期資訊的處理機制——**與 TencentDB 被批的「無防腐化機制」同型** |
| **EverOS Reject**：機制複雜規模大、無自組織驗證手段、泛用未專門化 | macro 同時宣稱 email/chat/docs/tasks/CRM/agents，泛用而未專門化；無第三方 benchmark 驗證記憶品質 |

**這代表：若照使用者既有判準，macro 很可能落入與 Buzz / TencentDB-Agent-Memory / EverOS 相同的 Reject 模式。** 但依「技術取捨準則」原則三（Reject ≠ 沒價值），其「需求理解」與「方案方向」仍值得抽取：

- **「一切皆 block ＋ @mention 雙向連結」** 是比「檔案化記憶」更貼近「可計算知識圖」的資料模型——這正是使用者 MyBrain 的「判定總表 + 骨幹索引」想達成的「讓資訊可被檢索」的延伸。
- **「每晚 cron 合成記憶」** 是「讓資訊隨組織自我維護」的一種嘗試，但缺「防腐化」閘門（見 §3 模糊之處）——與使用者 MyBrain 的「append-only log 檢查 + validate/reindex CI」程式化防腐化模型不對等。

**與使用者自建 MyBrain 的關係**：MyBrain 是個人級記憶（日常在用），macro 是團隊級工作台＋記憶，兩者層級不同。依「技術取捨準則」原則二（MVP→Feature 唯一閘門是能否影響個人 workflow），macro 的團隊治理功能對使用者個人 workflow 的直接影響有限。但 macro 的「@linked 雙向圖」資料模型，與使用者進行中的「個人 AiAgent 入口」專案（執行環境未定）有可對照處——若個人入口要讓 Agent 讀取跨工具脈絡，macro 的「統一 block + 雙向連結」是比「散落檔案」更結構化的起點。

### 4.3 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **macro** | 一切皆 block + @mention 雙向連結圖 + 每晚 cron 合成團隊記憶 + Agent 層（@Macro/MCP/automation） | 需接受 all-in-one 規模；AGPLv3 copyleft；self-host 非主要 focus（走雲端） | 規模大、採用效果未知；記憶無防腐化機制；泛用未專門化 | 單一可計算知識圖，Agent 跨工具搬運上下文；團隊記憶累積 |
| **TencentDB-Agent-Memory**（使用者 Reject） | 四類記憶資產 + L0-L3 分層 + Memory Hub 治理（ACL/版本/配給） | 需部署四服務；團隊或多角色 Agent 場景 | 部署運維成本高；無防腐化機制 | 跨 session 與跨 Agent 經驗累積，冷啟動成本降低 |
| **Buzz**（使用者 Reject） | 蜂群思維統一事件流 + 權限控制，整合需求/程式碼/CI/CD/任務 | 團隊協作工作台需求 | 規模過大、採用效果未知 | 人與 Agent 在同一 Workspace 共享上下文 |
| **EverOS**（使用者 Reject） | 仿生物銘印記憶生命週期（情節→語意→重建）+ 混合檢索 | 團隊/組織級記憶治理需求 | 機制複雜規模大、無自組織驗證 | 跨 session 記憶演化，但導入規模與專案年紀不符 |
| **MyBrain**（自建，日常在用） | 個人級記憶；「人 review 當品質守門員」+ append-only log + validate/reindex CI | 個人級記憶需求 | 個人級，無團隊治理 | 個人脈絡可被 Agent 讀取，且具程式化防腐化 |

### 4.4 各方案切入點差異

| 切入點 | 代表方案 | 差異 |
|---|---|---|
| **all-in-one 工作台**（email/chat/docs/tasks/CRM 收進單一系統） | macro | 唯一把「工作台」當核心的，Agent 從 unified memory 工作 |
| **記憶資產治理**（誰能用、哪個版本、配給誰） | TencentDB-Agent-Memory | 把「治理層」當核心，ACL/版本/配給是主軸 |
| **人與 Agent 協作工作台**（統一事件流） | Buzz | 強調人與 Agent 在同一 Workspace 共享上下文 |
| **記憶生命週期**（情節→語意→重建） | EverOS | 強調記憶如何演化，但缺治理與驗證 |
| **個人級記憶 + 防腐化** | MyBrain | 個人級，以「人 review + 程式化驗證」當品質守門員 |

---

## 5. User Q&A

> 本節為使用者對 macro 提出質問後追加。R2 使用者已基本偏向 Reject，改問「能借鑑什麼、怎麼套用、可用性矩陣」三題。以下 QA 承接 R1 的 macro 機制與第二大腦既有判定。

### Q1：如果這東西能讓我借鑑，最可能借鑑的地方與借鑑方式為何？

**A**：macro 最值得借鑑的不是「工作台」本身（那正是你已 Reject 的 Buzz 問題域），而是它的**資料模型原語**與**記憶合成方向**。依「技術取捨準則」原則三（Reject ≠ 沒價值，仍抽取需求理解與方案方向），可借鑑點如下：

| 借鑑點 | macro 的做法 | 借鑑方式（套到你的 MyBrain / 個人 AiAgent 入口） | 對照你既有判定 |
|---|---|---|---|
| **一切皆 block** | email/chat/doc/task/CRM/call 統一抽象成 block 單位 | 把 MyBrain 的「判定總表＋骨幹索引」從「檔案＋frontmatter」升級為「可被 Agent 當成單一資料源讀取的結構化節點」 | 與你 Reject 的 OKF「結構太固定」不同——block 是「統一原語」而非「固定 schema」，保留擴張性 |
| **@mention 雙向連結** | block 之間建立雙向 References（@linked 圖） | 讓「判定總表 ↔ 個別評估檔 ↔ 日誌」的關聯可被 Agent 反向追蹤，而非靠 grep 單向找 | 對照你 Reject 的 OKF「知識圖譜需要擴張與自適應性」——雙向連結正是擴張性的來源 |
| **統一 property 系統** | STRING/NUMBER/BOOLEAN/DATE/SELECT/ENTITY/LINK 跨 block 共用 | 把 MyBrain frontmatter 的 `generated.by`/`status`/`verified` 統一成可被驗證器讀取的欄位型別 | 與你 MyBrain 的 validate.py 程式化防腐化相容，不衝突 |
| **跨 block 單一 tag 命名空間** | 單一 tag 跨所有 block，Any/All 過濾 | 把「骨幹 tag」從「grep 標記」升級為「跨檔可過濾的索引原語」 | 對照你現行 grep＋骨幹 tag 的確定性檢索，是它的結構化延伸 |
| **每晚 cron 合成記憶** | 每晚從 email/messages/tasks/docs/calls 合成一次 | 方向可借：定期聚合各來源；但**必須補上防腐化閘門**（見下） | 與你 Reject 的 TencentDB「無防腐化機制」同型，借方向、不借機制 |

**⚠️ 借鑑的界線（反證表）**：

| 借鑑點 | 可借 | 不可借 | 理由 |
|---|---|---|---|
| 資料模型原語 | ✅ block＋雙向連結＋property＋tag | — | 是「可計算知識圖」的結構化起點，與你 MyBrain 想達成的「讓資訊可被檢索」同向 |
| 記憶合成 | ✅ 「定期聚合」的方向 | ❌ 「每晚 cron 一次、無防腐化閘門」的機制 | 你 Reject TencentDB 的核心判準正是「沒有防腐化機制的大腦等同必定過期的文件」；macro 的 cron 合成沒有 dedup／衝突合併／回滾描述，與被批同型 |
| 工作台整合 | — | ❌ all-in-one 收 email/chat/CRM | 正是你 Reject Buzz 的「規模過大、個人使用不必要」 |

**結論**：借 macro 的「統一 block＋雙向連結＋統一 property＋跨 block tag」資料模型原語，套到 MyBrain 與個人 AiAgent 入口的結構化改造；不借「all-in-one 工作台」與「無防腐化的 cron 合成記憶」——後兩者分別踩中你已 Reject 的 Buzz 與 TencentDB 判準。

---

### Q2：如果要進一步套用到我的個人 workflow，最可能如何活用？可能有幾種 pattern？

**A**：依「技術取捨準則」原則二（MVP→Feature 唯一閘門＝能否影響個人 workflow），macro 的團隊治理功能對你個人 workflow 的直接影響有限，但它的**資料模型原語**可對照你進行中的「個人 AiAgent 入口」與日常在用的 MyBrain。套用 pattern 如下：

| Pattern | 活用方式 | 對照你現有 workflow | 影響個人 workflow 的程度 |
|---|---|---|---|
| **P1：統一 block 資料層** | 把個人 AiAgent 入口的 ChatSession 記錄、MyBrain 的判定、Feedly 摘要統一成「可被 Agent 讀取的結構化節點」，而非散落檔案 | 個人 AiAgent 入口（進行中，卡在執行環境）；MyBrain（日常在用） | 高——直接解決「Agent 讀取跨工具脈絡」的結構化起點 |
| **P2：雙向連結索引** | 讓「判定總表 ↔ 個別評估 ↔ 日誌」可被 Agent 反向追蹤，取代單向 grep | MyBrain 現行 grep＋骨幹 tag 確定性檢索 | 中——是現行檢索的結構化延伸，非替換 |
| **P3：統一 property 防腐化** | 把 frontmatter 的 `generated.by`/`status`/`verified` 統一成驗證器可讀的型別，強化 validate.py | MyBrain 的 validate.py＋reindex.py＋append-only log 檢查 | 中——與你既有程式化防腐化相容，是強化非新增 |
| **P4：定期聚合（借方向）** | 借「定期從各來源聚合」的方向，但**補上防腐化閘門**（人 review＋程式化驗證） | MyBrain「人 review 當品質守門員」模型 | 低——你已有更嚴格的防腐化，macro 只是方向印證 |

**⚠️ 不建議的 pattern（反證表）**：

| Pattern | 為何不建議 | 對照你既有判定 |
|---|---|---|
| 導入 macro 本體當工作台 | all-in-one 規模大、self-host 非 focus、AGPLv3 copyleft | 踩中 Buzz Reject「規模過大、個人使用不必要」 |
| 用 macro 的 cron 合成記憶 | 無防腐化閘門，等同必定過期的文件 | 踩中 TencentDB Reject「無防腐化機制」 |
| 把團隊治理功能搬進個人 workflow | 團隊功能對個人 workflow 無直接影響 | 違反原則二「MVP→Feature 閘門＝能否影響個人 workflow」 |

**結論**：最可能活用的是 P1（統一 block 資料層）與 P2（雙向連結索引）——套到進行中的個人 AiAgent 入口與 MyBrain，讓 Agent 讀取跨工具脈絡的結構化起點；P3 是既有防腐化的強化；P4 只是方向印證。不導入 macro 本體。

---

### Q3：這東西對「利用範圍（個人／團隊／公司）× 利用領域（日常業務／程式開發／非日常業務）」的可用性、應用方式、判定理由為何？

**A**：依 macro 的定位（all-in-one 工作台＋團隊級記憶）、self-host 可行性（非 focus）、授權（AGPLv3 copyleft）與你既有判定，可用性矩陣如下：

| 利用範圍 | 利用領域 | 可用性 | 應用方式 | 判定理由 |
|---|---|---|---|---|
| **個人** | 日常業務 | 低 | 收 email/chat/task 進單一系統，Agent 從 unified memory 工作 | 你 Reject Buzz「個人使用不必要」；all-in-one 規模對個人過重；self-host 非 focus 走雲端，個人難落地 |
| **個人** | 程式開發 | 低 | 個人 coding 用 Agent 讀取跨工具脈絡 | 你 Reject Delta「只是開發過程紀錄機制可自己兜」；個人 coding 已有 opencode＋MyBrain 覆蓋 |
| **個人** | 非日常業務 | 低 | 個人專案管理、生活事務收進工作台 | 個人層級無團隊治理需求；macro 的團隊記憶功能用不上 |
| **團隊** | 日常業務 | 中 | 團隊 email/chat/docs/tasks 統一，Agent 共享上下文 | 這是 macro 的核心定位；但記憶無防腐化機制，踩中你 Reject TencentDB 判準 |
| **團隊** | 程式開發 | 中 | 團隊 coding 協作，Agent 參與 PR/issue | 你 Reject Buzz「規模過大、採用效果未知」；Delta「團隊效果難驗證」；需全員理解機制才能沉澱正確資訊 |
| **團隊** | 非日常業務 | 中 | 團隊專案管理、跨部門知識累積 | 團隊級記憶是 macro 強項；但無防腐化閘門，長期只剩雜音 |
| **公司** | 日常業務 | 中 | 全公司 email/chat/CRM 統一，Agent 跨部門搬運上下文 | 對應「公司不可計算」命題；但規模與治理需求遠超 macro 目前驗證範圍，無第三方 benchmark |
| **公司** | 程式開發 | 中 | 公司級 coding 協作與知識治理 | 你 Reject EverOS「機制複雜規模大、無自組織驗證」；macro 泛用未專門化，導入規模與專案年紀不符 |
| **公司** | 非日常業務 | 低 | 公司級非技術知識管理 | 泛用未專門化；AGPLv3 copyleft 對商業整合有限制；self-host 非 focus |

**判定理由的橫向歸納**：

| 判定軸 | 個人 | 團隊 | 公司 |
|---|---|---|---|
| **規模匹配** | 過重（Buzz Reject） | 中等 | 過大（EverOS Reject） |
| **記憶防腐化** | 無此需求 | 缺閘門（TencentDB Reject） | 缺閘門＋無驗證（EverOS Reject） |
| **self-host/授權** | 非 focus、難落地 | 走雲端、AGPL copyleft | AGPL copyleft 對商業整合受限 |
| **個人 workflow 影響** | 低（原則二閘門） | 團隊功能非個人 workflow | 非個人 workflow |

**結論**：macro 的可用性集中在「團隊 × 日常業務／程式開發」——那是它的核心定位，但記憶無防腐化機制踩中你 Reject TencentDB 的判準；「個人」層級因規模過重與 self-host 非 focus 而低可用；「公司」層級因規模過大、無自組織驗證與 AGPL copyleft 而受限。對你個人 workflow 的直接可用性低，可借鑑的是資料模型原語（見 Q1/Q2）。
