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

## 附錄：調研來源

- 官方 README（feat/server_team 分支）：https://github.com/TencentCloud/TencentDB-Agent-Memory
- 使用者第二大腦（FATESAIKOU/MyBrain）：判定總表、技術取捨準則、EverOS/OpenHuman/planning-with-files/codebase-memory-mcp/HermesAgent/LeanCtx/Headroom/context-mode 評估檔
