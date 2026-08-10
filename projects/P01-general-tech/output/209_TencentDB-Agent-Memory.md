# TencentDB-Agent-Memory 技術分析報告

> 調研標的：https://github.com/TencentCloud/TencentDB-Agent-Memory
> 騰訊雲開源的「團隊級 Agent 記憶系統」（Team-level Memory Hub for AI Agents）
> 18,612 stars · MIT License · 預設分支 `feat/server_team` · 2026-08-09 更新

---

## 1. 這個技術解決什麼問題？

**TencentDB-Agent-Memory 解決的是「AI Agent 團隊的經驗無法累積、跨 session 與跨 Agent 重複勞動」的問題。**

具體拆成三層：

| 問題層 | 具體表現 |
|---|---|
| **重複工作** | 專案 context 已經解釋過，新 session 又要重講；文件已經讀過，每個 Agent 都要從第一頁重讀；跑通的 workflow 下次要重新摸索 |
| **記憶無法治理** | 記憶散落在各 Agent 各自的 context 或 chat log 裡，沒有「誰能用、哪個版本有效、該配給哪個 Agent」的治理 |
| **冷啟動成本** | 新 Agent 或新成員加入時，要重新學習整個專案，無法從既有經驗直接開始 |

官方用一句話總結：**「Existing information → Reusable memory assets → Fewer turns → Less rework → More stable results and higher efficiency」**（既有資訊 → 可重用記憶資產 → 更少回合 → 更少返工 → 更穩定的結果與更高效率）。

**模糊之處**：
- 「團隊級」的邊界定義模糊——官方同時宣稱適用「一人公司」（One-Person Company）的多角色 Agent 團隊，也宣稱適用多人團隊，但兩者的治理需求（ACL、角色、審查）規模差異很大，官方未區分。
- 官方宣稱「跨框架可攜」（OpenClaw / Hermes / Claude Code / CodeBuddy / SDK），但 README 的 Notes 也承認「更廣泛的跨框架遷移仍在 roadmap 上」，即目前並非所有框架都完整支援。
- PersonaMem benchmark（48%→76%, +59%）只測「Agent 能否正確理解並套用使用者資訊」，未涵蓋 Skill / Wiki / CodeGraph 三類資產的效益，也無獨立第三方重現。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **LLM Agent 的無狀態本質**：每次對話結束後 context 即消失，模型無法跨 session 記住使用者資料、偏好、工作脈絡與歷史。這是所有 Agent 記憶系統要解決的共同根源。
- **RAG 的不足**：官方明確對照「標準 RAG」——RAG 只回答「找得到什麼」（what can be found），不回答「誰能用、哪個版本有效、該配給哪個 Agent」（who can use it, which version is valid, which Agent should receive it）。RAG 對「跨 session 使用者理解」「可執行的經驗」「文件結構與關係」「程式碼呼叫圖與影響範圍」都只有部分或沒有覆蓋。
- **Agent 團隊化的興起**：官方提出的「一人公司」play style（Scout / Builder / Reviewer / Agent Memory 多角色分工）反映 Agent 從單一工具走向多角色協作團隊的趨勢，團隊需要共享的記憶基礎設施。

### 通用技術背景（文章中未明確提及）

- **Context Window 的物理限制**：LLM 的 context window 有限且昂貴，無法把全部歷史塞進去。記憶系統必須在「存多少」與「取多少」之間取捨，這正是 L0-L3 分層與「按需呼叫」設計的動機。
- **Agent 記憶領域的兩條路線**：一條是「個人級」記憶（單一使用者的偏好、事實、決策），另一條是「團隊/組織級」記憶治理（多 Agent、多成員、權限、版本、審查）。TencentDB-Agent-Memory 明確走後者，這與使用者第二大腦中已評估的 EverOS（同樣團隊/組織級）屬同一層級。
- **既有開源資產的組合**：官方 Acknowledgements 明列其 Wiki 層受 Karpathy 的「LLM Wiki」啟發、CodeGraph 資產模組直接使用 colbymchenry/codegraph 的程式碼、Skill 資產管理使用 Hermes Agent 的部分 Skill 程式碼並在此基礎上優化。這說明該專案是「組合既有開源方案 + 自建治理層」的產物，而非從零自研。

---

## 3. 這個技術是如何解決該問題的？

### 整體架構：四類記憶資產 + 四服務組件

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TencentDB-Agent-Memory 架構                        │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐             │
│  │  MemoryCore   │   │ MemoryKnowledge│  │  MemoryPanel  │            │
│  │  (記憶核心)    │   │ (知識服務)     │   │ (控制台)      │            │
│  │  :8420        │   │ :8421 /v3     │   │ :8123        │            │
│  │  L0-L3 儲存    │   │ Wiki+CodeGraph│   │ 團隊/資產管理  │            │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘             │
│         │                  │                  │                     │
│         └──────────────────┼──────────────────┘                     │
│                            ▼                                        │
│  ┌──────────────────────────────────────────────┐                   │
│  │              MemoryProxy (LLM 代理)           │                   │
│  │              :8096 透明注入                    │                   │
│  │  session init / context injection / write-back │                   │
│  └──────────────────────────────────────────────┘                   │
│                            │                                        │
│                            ▼                                        │
│  OpenClaw · Hermes · Claude Code · CodeBuddy · SDK                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 核心機制一：四類記憶資產（Memory Assets）

| 資產 | 內容 | 解決的問題 |
|---|---|---|
| **Chat Memory** | 偏好、事實、決策、互動歷史 | 跨 session 記住「人與脈絡」 |
| **Skill** | 從對話與工具呼叫中抽取的可重用技能（含版本、資源檔、觸發邊界、執行步驟、驗證規則） | 累積「可執行的經驗」，而非只是 prompt 片段 |
| **Wiki** | 把文件轉成結構化頁面 + 連結圖（受 Karpathy LLM Wiki 啟發） | 讓 Agent 不必先讀完所有文件清單才開始工作 |
| **CodeGraph** | 索引程式碼符號、檔案、呼叫關係、影響路徑（使用 colbymchenry/codegraph 程式碼） | 不只告訴 Agent「程式碼在哪」，還告訴它「改這裡會影響哪些」 |

### 核心機制二：L0-L3 記憶分層

對話先存為 L0，再由非同步 pipeline 精煉成多層粒度：

| 層 | 存什麼 | 主要用途 |
|---|---|---|
| **L0 Conversation** | 原始對話（含完整 context） | 驗證確切措辭、時間戳、來源 |
| **L1 Atom** | 從對話抽取的事實、偏好、約束、事件 | 精確召回可行動資訊 |
| **L2 Scenario** | 圍繞專案或場景組織的知識區塊 | 快速恢復工作 context |
| **L3 Core / Persona** | 長期 profile、穩定模式、高層認知 | 讓 Agent 快速進入使用者與團隊 context |

**生成與檢索都分層**：一般情況用 L2/L3 快速 bootstrap context；需要特定事實時，用 BM25 + vector 檢索 + RRF（Reciprocal Rank Fusion）回退到 L1/L0。結果再以「條目數、字元預算、逾時」上限封頂，防止記憶淹沒 context window。

### 核心機制三：Memory Hub 治理（Fixed Binding + ACL）

四類資產統一註冊為 Memory Assets。Memory Hub 用 **Fixed Binding + ACL** 決定某個 Agent 能用哪些資產：先依 Team / User / Agent / visibility 收斂權限範圍，再依當前 query 檢索。

| 可見度 | 語意 |
|---|---|
| `private` | 只有 Owner 能讀，連 team admin 都不能 |
| `team` | 團隊成員可讀，Owner / Admin 可管理 |
| `restricted` | 透過 User / Role / Agent ACL 精確授權 |
| `agent` | 針對同團隊內特定 Agent 配給 |

**新 Chat Memory 與 Skill 預設 private，分享是明確動作而非預設洩漏。** 角色分兩層：全域 System Admin（管使用者與團隊）與 Team-level 角色（Admin / Member）。

### 核心機制四：知識按需呼叫，而非整包注入

文件組織成可搜尋的 Wiki 頁（支援連結圖下鑽），程式碼索引成 CodeGraph 資產。Agent 先透過 `/v3/tools/list` 發現能力，再用 `/v3/tools/call` 讀取相關頁面、原始碼或影響路徑。**文件與程式碼成為記憶的一部分，但只在真正需要時才進入 context。**

### 核心機制五：MemoryProxy 透明注入（免改碼接入）

MemoryProxy（:8096）是透明 LLM 請求代理，處理 session init、context injection、write-back、auth、rate-limit。L0/L1 走 toolize、L2/L3 走 inject，支援 Claude Code / CodeBuddy 免改碼接入。

### Benchmark

| Benchmark | 未啟用 | 啟用後 | 相對提升 |
|---|---|---|---|
| **PersonaMem** | 48% | 76% | +59% |

PersonaMem 測試 Agent 在長時間互動後能否正確理解並套用使用者資訊。

### 已知限制（README Notes）

- Wiki 與 CodeGraph 非同步建置，需等待處理時間才到 `ready` 狀態。
- CodeGraph 目前優先支援公開 HTTPS repo，private repo 與 SSH credentials 支援仍在完善。
- Hub 支援手動資產綁定，全自動記憶路由仍在迭代。
- 目前支援 OpenClaw / Hermes / Claude Code / CodeBuddy / SDK，更廣泛的跨框架遷移在 roadmap。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

> 本節對照使用者第二大腦（FATESAIKOU/MyBrain）的既有判定。**第二大腦中沒有 TencentDB-Agent-Memory 的評估紀錄**（判定總表 79 筆中無此條目），但同屬「Agent 記憶」領域已評估 8+ 個工具，以下對照其既有立場。

### 4.1 使用者既有判定的同類工具（對照第二大腦）

| 工具 | 使用者判定 | 判定理由（第二大腦） | 信任層級 |
|---|---|---|---|
| **EverOS** | Reject | 團隊/組織層級記憶治理；機制複雜規模大但無自組織驗證手段；泛用但未專門化；此規模導入對應專案年紀還不夠 | `human:fatesaikou` / `stable` |
| **OpenHuman** | 未判定 | 筆記為技術分析報告，僅描述機制與比較替代方案，未給個人採用結論 | `process:learning-agent` / `stable` |
| **planning-with-files** | Reject | 控管 Scope 不足（跨 session 但無記憶分層）；彈性不足（過度工程化風險） | `human:fatesaikou` / `stable` |
| **codebase-memory-mcp** | Reject | 問題域是重造輪子；技術複雜但效果難驗證，skip | `human:fatesaikou` / `stable` |
| **HermesAgent** | Adopt | 全機式自主記憶 AI Agent，含自動 Context 抽取與維護；browser 比 opencode 強 | `human:fatesaikou` / `stable` |
| **LeanCtx** | Accept | context 治理層，解決重複讀取、shell 噪音、跨會話記憶三個浪費 | `human:fatesaikou` / `stable` |
| **Headroom** | Accept | context window 內容感知壓縮工具 | `human:fatesaikou` / `stable` |
| **context-mode** | 觀望 | MCP server，context 治理中間層；寫了完整分析報告理解本質，但未提及導入，處於研究階段 | `process:learning-agent` / `stable` |

> 信任層級說明：判定總表本身為 `draft`（`generated.by: ollama-cloud/deepseek-v4-flash`），但各工具原檔多為 `human:fatesaikou` 本人撰寫且 `stable`，故上表以原檔信任層級為準。判定總表是 AI 彙整的索引，個別判定理由以原檔為準。

### 4.2 與使用者既有立場的衝突點（本節最有價值處）

**⚠️ 明確衝突：TencentDB-Agent-Memory 與使用者已 Reject 的 EverOS 屬同一層級（團隊/組織級記憶治理），且具備 EverOS 被拒的三個特徵。**

| EverOS 被拒理由 | TencentDB-Agent-Memory 對照 |
|---|---|
| 機制複雜、規模大 | 四服務組件（Core/Knowledge/Panel/Proxy）+ 四類資產 + L0-L3 分層 + ACL，規模同樣大 |
| 無自組織驗證手段 | 官方僅提供單一 PersonaMem benchmark，無第三方重現，無自組織驗證 |
| 泛用但未專門化 | 同時宣稱一人公司與多人團隊，跨框架支援仍在 roadmap，泛用而未專門化 |

**這代表：若照使用者既有判準，TencentDB-Agent-Memory 很可能落入與 EverOS 相同的 Reject 模式。** 但依「技術取捨準則」原則三（Reject ≠ 沒價值），其「需求理解」與「方案方向」仍值得抽取——尤其它把「治理層（ACL/版本/配給）」與「知識層（Wiki/CodeGraph）」分離的設計，正是 EverOS 被批「無自組織驗證」時所缺的。

**正相關點（與既有 Adopt 一致）**：
- TencentDB-Agent-Memory 的 **Skill 資產管理直接使用 Hermes Agent 的程式碼**，而 HermesAgent 是使用者 Adopt 的。這代表其 Skill 機制與使用者已接受的方案同源。
- TencentDB-Agent-Memory 的 **CodeGraph 資產模組使用 colbymchenry/codegraph 的程式碼**，而使用者對 CodeGraph 判「試用」（值得嘗試，比 GitNexus 全自幹更善用生態系、對開發流程侵入性更小）。兩者共享同一 CodeGraph 基礎。

**與使用者自建 MyBrain 的關係**：使用者自建 MyBrain 是「個人級」記憶系統（日常在用），TencentDB-Agent-Memory 是「團隊級」記憶 hub，兩者層級不同。依「技術取捨準則」原則二（MVP→Feature 唯一閘門是能否影響個人 workflow），TencentDB-Agent-Memory 的團隊治理功能對使用者個人 workflow 的直接影響有限，但其中「把既有文件/程式碼/對話轉成可重用資產」的冷啟動思路，與使用者 MyBrain 的「讀寫分離 + 判定總表」設計有可對照處。

### 4.3 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **TencentDB-Agent-Memory** | 四類記憶資產（Chat Memory/Skill/Wiki/CodeGraph）+ L0-L3 分層 + Memory Hub 治理（ACL/版本/配給）+ MemoryProxy 透明注入 | 需部署四服務（Core/Knowledge/Panel/Proxy）；需兩組 LLM 參數；Node ≥ 22.16；團隊或多角色 Agent 場景 | 部署與運維成本高；Wiki/CodeGraph 非同步建置需等待；CodeGraph 暫不支援 private repo；跨框架遷移未完整 | 跨 session 與跨 Agent 經驗累積，冷啟動成本降低；PersonaMem 48%→76%（+59%） |
| **EverOS**（使用者 Reject） | 仿生物銘印記憶生命週期（情節→語意→重建），BM25+Vector+RRF 混合檢索 | 團隊/組織層級記憶治理需求；可接受大型自組織系統 | 機制複雜規模大、無自組織驗證手段、泛用未專門化 | 跨 session 記憶演化，但使用者判定導入規模與專案年紀不符 |
| **HermesAgent**（使用者 Adopt） | 全機式自主記憶 AI Agent，自動 Context 抽取與維護 | 需要一個具自主記憶的完整 Agent（非記憶基礎設施） | 綁定特定 Agent 框架；記憶與 Agent 本體耦合 | 單一 Agent 具備自主記憶與自動 Context 抽取，browser 能力強 |
| **LeanCtx / Headroom**（使用者 Accept） | context 治理層：壓縮 + 記憶 + 路由 + 治理（LeanCtx）；內容感知壓縮（Headroom） | 解決 context window 成本與跨會話記憶喪失 | 屬 context 治理而非完整記憶資產管理；無團隊 ACL/版本治理 | 降低 token 消耗、跨會話記憶恢復，但無團隊共享與權限治理 |
| **planning-with-files**（使用者 Reject） | 用檔案系統做 Agent 持久化記憶，Hook 系統驅動 | 跨 session 工作狀態持久化 | 無記憶分層（控管 Scope 不足）；過度工程化風險 | 跨 session 恢復工作狀態，但無法治理記憶資產 |

### 4.4 各方案切入點差異

| 切入點 | 代表方案 | 差異 |
|---|---|---|
| **記憶資產治理**（誰能用、哪個版本、配給誰） | TencentDB-Agent-Memory | 唯一把「治理層」當核心的，ACL/版本/配給是主軸 |
| **記憶生命週期**（情節→語意→重建） | EverOS | 強調記憶如何演化，但缺治理與驗證 |
| **Agent 本體自主記憶** | HermesAgent | 記憶內建於單一 Agent，非獨立基礎設施 |
| **context 治理**（壓縮/路由/記憶） | LeanCtx / Headroom | 聚焦 token 效率與跨 session 恢復，非團隊共享 |
| **檔案化持久化** | planning-with-files | 最輕量，但無分層與治理 |

---

## 5. User Q&A

> 本節為 R2 輪使用者「接近 Reject 前」的三個質問（issue #208 追問）的構造化回答。既有 §1-§4 內容不刪改，本節按序號接續。

### Q1：這東西跟我的 MyBrain 比，在「解決的問題」「解決問題的方式」上比較如何？

**A**：兩者解決的是不同層級的問題，機制不可互換。MyBrain 是個人級記憶基礎設施，TencentDB-Agent-Memory 是團隊級記憶 hub；前者是「我一個人的判斷與偏好」，後者是「多 Agent／多成員的共享資產與治理」。

| 面向 | MyBrain（使用者自建） | TencentDB-Agent-Memory | 本質差異 |
|---|---|---|---|
| **解決的問題層級** | 個人級：讓 agent 有使用者個人上下文，避免推薦脫離處境 | 團隊級：讓跨 session、跨 Agent 的經驗累積且可治理 | 一對一 vs 多對多 |
| **要解決的具體問題** | agent 不知道哪些選項已評估、結論是什麼、現職/投資/價值觀脈絡 | 專案 context 重講、文件重讀、workflow 重摸索、記憶無治理 | 個人脈絡缺失 vs 團隊經驗重複與失序 |
| **解決方式：記憶內容** | 判斷準則、價值觀、職涯、金融、專案現況（三問線索庫） | Chat Memory / Skill / Wiki / CodeGraph 四類資產 | 存「人」vs 存「團隊資產」 |
| **解決方式：檢索/接入** | `mybrain-read` skill（先讀骨幹再 grep，15 場景觸發） | L0-L3 分層 + BM25+vector+RRF + MemoryProxy 注入 | 規則式情境判讀 vs 全自動分層檢索 |
| **寫入門檻** | PR 人 review 才合併（寫入僅本人可叫） | Skill 層 review 後才可 team 分享，Chat Memory 預設 private | 兩者都有 review 概念，但覆蓋範圍不同 |

**對照表（信任層級：`human:fatesaikou`/`stable`）**：

| 面向 | MyBrain | TencentDB-Agent-Memory |
|---|---|---|
| 記憶等級 | 個人級（日常在用） | 團隊級 |
| 人 Review | 寫入走 PR、本人 review 才合併（`技術取捨準則`五） | 僅 Skill 層需 review 才 team 分享，其餘資產未見同等強制 |
| 存取規則 | 唯讀鏡像 `/tmp/mybrain`、寫入僅本人可叫 | ACL 四可見度 + 雙層角色 + ownership |
| 腐化防護 | append-only log 檢查 + validate/reindex CI | 無 dedup/衝突合併/回滾機制文件 |

**切入點差異**：MyBrain 的寫入閘門是「人」，TencentDB 的寫入閘門是「pipeline＋ACL」。前者以「本人的理解」作為品質守門員，後者以「LLM 抽取 prompt＋權限模型」作為守門員——這正好是 Q3 的焦點。

**結論**：兩者不構成競爭。MyBrain 解決「我一個人怎麼讓 agent 懂我」，TencentDB 解決「一個團隊怎麼讓 agent 共享並治理經驗」。照使用者既有判準，MyBrain 屬個人日常 workflow（進 Feature 的候選），TencentDB 屬團隊治理基礎設施（與已 Reject 的 EverOS 同層級）。

---

### Q2：這算組織層級的知識庫是吧？但它肯定需要人類 Review 和建立存取規則，它有做嗎？怎麼處理的？最終效果如何？

**A**：算團隊（組織）層級知識庫，且存取規則做得完整，但人類 Review 只覆蓋 Skill 一層，未覆蓋全部資產——這是「有做但做一半」。

**存取規則（有做，且完整）**：

| 機制 | 內容 | 覆蓋範圍 |
|---|---|---|
| ACL 四可見度 | `private`（僅 Owner 可讀，連 team admin 都不能）/ `team`（成員可讀，Owner/Admin 管理）/ `restricted`（User/Role/Agent ACL 精確授權）/ `agent`（配給特定 Agent） | 全部資產 |
| 雙層角色 | 全域 System Admin（管使用者/團隊）+ Team-level Admin/Member | 全部資產 |
| Ownership | Asset 由 Owner 持有，Owner 自動具管理權 | 全部資產 |
| 預設安全 | 新 Chat Memory 與 Skill 預設 `private`，分享是明確動作而非預設洩漏 | Chat Memory / Skill |

**人類 Review（有做，但只做一層）**：

| 資產 | 有無人 Review | 第一手證據 |
|---|---|---|
| **Skill** | ✅ 有 | 根 README 原句「Personal Skills are private by default; **after review**, they can be shared with the team and assigned to other Agents」——Review 是 Skill 從 private 升級為 team 的門檻 |
| **Chat Memory** | ❌ 未見同等強制 | 文件未描述 Chat Memory 的人類驗證閘門 |
| **Wiki** | ❌ 未見 | 非同步建置，未見人驗證閘門 |
| **CodeGraph** | ❌ 未見 | 非同步建置，未見人驗證閘門 |

**最終效果評估**：

| 面向 | 評估 |
|---|---|
| 存取規則效果 | 好：private 預設＋四可見度＋雙層角色＋ownership 構成完整權限模型，明確動作才分享 |
| 人類 Review 效果 | 部分：僅 Skill 層有強制 review，Chat Memory/Wiki/CodeGraph 靠 LLM 抽取 pipeline 而無人閘門 |
| 未覆蓋資產的風險 | 高：Chat Memory（使用者偏好/事實/決策）與 Wiki/CodeGraph（知識）未經人 review，錯誤或過時內容可能直接進入 team 資產 |

**結論**：存取規則建立完整（ACL 模型），人類 Review 僅建立於 Skill 一層，其餘三類資產無人驗證閘門——「知識庫的權限治理」做了，「知識庫的內容品質治理」只做了一層。

---

### Q3：這東西不像把東西處理後只存最高層級不同面向，反而把 raw session 重複抽象總結好幾層各自放入快取？但誰規定什麼該留在哪一層、什麼該排除？誰、如何驗證？如何避免腐化？

**A**：你觀察正確——它確實是「raw 對話（L0）重複抽象成 L1/L2/L3 多層」，而不是只存最高層級。誰規定留取、誰驗證、如何防腐化，這三問官方文件給的回答如下。

**分層機制（確認是逐層精煉，非只存高層）**：

```
L0 Conversation（raw 對話）
   │ 非同步 pipeline 逐層精煉
   ▼
L1 Atom（事實/偏好/約束/事件）
   ▼
L2 Scenario（專案/場景知識區塊）
   ▼
L3 Persona（長期 profile / 穩定模式）
```

- 生成需 LLM credential（「memory extraction and aggregation require valid credentials」），pipeline state 在 process 內維護。

**① 誰規定什麼留哪一層、排除什麼？——由抽取用 LLM prompt 決定，無人類規則。**

| 面向 | 官方文件回答 |
|---|---|
| 分層「留什麼/排除什麼」 | 由**抽取用的 LLM prompt** 決定 |
| 是否有顯式人類規則 | **無顯式人類驗證閘門** |
| 分層 prompt 品質 | ROADMAP v2.0.1 原句：「Memory extraction quality depends on domain context… **A single hard-coded prompt cannot serve both**」；且「Editing custom prompts from the Memory Hub panel is **not supported yet**」——官方自承單一硬編碼 prompt 是瓶頸、尚未支援面板改 prompt |

**② 誰、如何驗證？——無獨立驗證機制，官方靠單一 pipeline 內建。**

- 文件未見對抽取結果的獨立驗證（無 L1/L2/L3 之間的一致性檢查、無與 L0 的對帳描述）。
- ROADMAP 規劃 Wiki 建置改為 bounded-concurrency pipeline（失敗頁獨立重試、進度可視），反證現行建置有黑箱與串行問題。
- 唯一 benchmark（PersonaMem 48%→76%）只測「Agent 能否套用使用者資訊」，未測分層留取品質。

**③ 如何避免腐化？——文件未見完整答案。**

| 腐化防護機制 | MyBrain（使用者既有） | TencentDB-Agent-Memory |
|---|---|---|
| dedup（去重） | 未查證 | 文件未見 |
| 衝突合併 | 未查證 | 文件未見 |
| 回滾 | 未查證 | 文件未見 |
| append-only log / CI | ✅（validate.py + reindex.py + log append-only 檢查） | 未見 |

**對照 MyBrain 的腐化防護（`human:fatesaikou`/`stable`）**：MyBrain 以「append-only log 檢查 + validate/reindex CI」程式化防腐化（`技術取捨準則`五：約束在 harness 不在權限）；TencentDB 的文件對 dedup/衝突合併/回滾皆無描述，官方反而自承「單一硬編碼 prompt」是分層品質瓶頸——即分層留取品質完全依賴未可調、未驗證的單一 prompt。

**結論**：分層「留什麼/排除什麼」由單一硬編碼 LLM prompt 決定，無人類規則、無獨立驗證閘門、無 dedup/衝突合併/回滾文件；官方 ROADMAP 自承該 prompt 是品質瓶頸且尚未支援修改。腐化防護在文件層面缺項，與使用者 MyBrain 的「append-only + CI 驗證」模型不對等。

---

## 附錄：調研來源

- 官方 README（feat/server_team 分支）：https://github.com/TencentCloud/TencentDB-Agent-Memory
- 官方 ROADMAP（v2.0.1 自承單一硬編碼 prompt 瓶頸、面板編輯未支援、Wiki bounded-concurrency 規劃）：https://github.com/TencentCloud/TencentDB-Agent-Memory
- 使用者第二大腦（FATESAIKOU/MyBrain）：判定總表、技術取捨準則、EverOS/OpenHuman/planning-with-files/codebase-memory-mcp/HermesAgent/LeanCtx/Headroom/context-mode 評估檔、專案現況表
