# scientific-agent-skills — 面向科學研究的 Agent Skills 技能庫分析報告

> 調研標的：`K-Dense-AI/scientific-agent-skills`（https://github.com/K-Dense-AI/scientific-agent-skills）
> 資料來源：repo 本身（README EN 971 行、docs/skills.md 250 行、AGENTS.md、plugin.json、pyproject.toml、pkpd-modeling/SKILL.md）＋ arXiv:2609.00065 論文摘要。
> 信任說明：repo 事實（stars、結構、skill 數）直接來自 gh/github 抓取；論文量測數據來自 arXiv 摘要。第二大腦相關判定另以表格標註 URL 與信任層級。

---

## 1. 這個技術解決什麼問題？

scientific-agent-skills 解決的具體問題是：**通用 AI agent（如 Claude、GPT 等 coding agent）在面對科學研究任務時，缺乏把「特定領域的專用工具、資料庫存取、實驗方法、監管規範」以結構化、可版本化、可安全載入的方式傳授給 agent 的手段，因此科學家得用零散、口語、不可重用的 prompt 反覆教 agent，agent 卻仍常走錯領域方法、用錯 API、碰錯資料。**

具體拆成三個子問題：

| 問題面向 | 描述 |
|---|---|
| 領域知識無法可靠傳遞 | 生物資訊、化學資訊、藥理、蛋白質、材料等領域各有專用套件（70+ Python 套件）與資料庫（100+），通用 agent 不會知道，需要人反覆教 |
| 知識常駐佔 token | 把整套領域知識放進 system prompt 會吃掉大量 context window，且「一次全塞」造成成本浪費 |
| 安全與正確性缺乏保障 | agent 直接呼叫生物／臨床資料庫與 LIMS 等真實基礎設施，若無規範，可能誤用工具、越權存取、產生不可信結果 |

模糊之處（問題描述本身的含糊點）：
- **「AI Scientist」的宣稱未量化**——repo 口號「把任意 agent 變 AI Scientist」，但論文只有「skill 數／token 佔比／workflow 覆蓋」的靜態量測，**沒有 task-level 成功率、沒有 agent 實際選用 skill 的命中率（host selection rate）**。「變成科學家」的「變成」缺乏可驗證基準。
- **skill 的「品質」無判準**——166 個 skill 每個只有 name/description/rules/scripts，沒有跨 skill 的品質或成效 benchmark。

結論：本 repo 的核心主張是 **「把科學領域專用知識結構化成一組可獨立載入、按需觸發的 Agent Skills，並以標準化格式（Agent Skills spec）打包（Agent Plugins 1.0.0）」，讓任意通用 agent 只需載入需要的 skill 即獲得該領域的操作能力。**

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章中明確提到的背景（repo README / 論文）

- **Agent 只會通用能力，不會領域能力**：README 定位為「把任意 AI agent 變 AI Scientist」——前提是現成 agent 具備通用推理與工具呼叫，但缺少科學專用知識。
- **skill 按需載入的動機**：論文明確以「常駐 description 佔 200k token window 的 7.1%」做量化——即「只放常駐摘要、真正內容按需載入」是為了節省 token。
- **Agent Skills 標準**：AGENTS.md 說明每個 skill 遵循 Anthropic 定義的 Agent Skills spec（一個目錄＋一個 SKILL.md 檔，含 frontmatter 的 name/description/license/allowed-tools＋body 的 rules 與 scripts 表），並以 Agent Plugins 1.0.0 manifest（plugin.json）打包成可發布的 plugin。
- **安全機制**：README 提供 Security 章節——用 Cisco AI Defense Skill Scanner 每週掃描、發布 security-report、並建議使用者自行 review 每個 skill。

### 2.2 通用技術背景（文章未明說，由調研補上）

- **Agent Skills 生態的興起**：2025 下半年起，Anthropic 定義了 Agent Skills 與 Agent Plugins 規範——把「技能」從口語 prompt 提升為「有 frontmatter、有許可、有結構、可版本化、可打包發布的目錄結構」。scientific-agent-skills 是這套規範在科學領域的最大應用（166 skill）。
- **領域知識的碎片化**：科學軟體生態長期碎片化（每個資料庫、套件各有一套 API），沒有統一的「agent 介面層」，導致知識散落在文件、部落格、論文中。
- **LLM context 成本**：長上下文模型雖可行，但「一次塞全部領域知識」在 token 成本、上下文污染、過期風險上都不利，「按需載入」是回應 context 成本問題的結構化做法。
- **vendored 上游**：docx/pdf/pptx/xlsx 等文件轉換 skill 直接上游 vendored 自 Anthropic 官方 skills repo，非本 repo 原創——說明它大量採納既有 skill，並以自己的科學分類包裝。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 整體結構

```
scientific-agent-skills/
├── skills/                  # 166 個 skill 目錄（每目錄一個 SKILL.md）
│   └── <skill>/SKILL.md     #   name/description/license/allowed-tools (frontmatter)
│                            #   + rules + scripts 表（body）
│       ├── references/      #   （選）補充文件，按需載入
│       ├── scripts/         #   （選）可執行的輔助腳本
│       └── assets/          #   （選）靜態資源
├── docs/                    # skills.md（skill 總表）、examples.md、security-report
├── plugin.json               # Agent Plugins 1.0.0 manifest（打包發布）
└── pyproject.toml            # 版本管理（version 2.69.0）
```

### 3.2 skill 分類（docs/skills.md，25 小節）

| 大類 | 內容 |
|---|---|
| Scientific Databases & Data Access | 100+ 科學資料庫（生物、化學、基因、藥物發現等） |
| Scientific Integrations | LIMS、雲端、實驗室自動化、ELN、Workflow、顯微鏡、Protocol 等 9 項科學整合 |
| Scientific Packages | 70+ Python 套件（生物資訊、化學資訊、藥理、蛋白質、ML/DL、材料、工程、數據分析、演化、Agent 框架、科學寫作、文件轉換、監管標準） |
| Scientific Thinking | 方法論、決策分析、Web 檢索等思考型 skill |

### 3.3 核心機制：按需載入（論文量測）

```
agent 收到任務 ──▶ 掃描所有 skill 的「常駐 description」──▶ 命中 → 載入該 skill 的 SKILL.md body
                     │                                             （references/ 才真正展開）
                     ▼
              常駐 description 只佔 200k window 的 7.1%（163 skill）
              單一 workflow 載入的 body 中位數約佔 window 23.9%
```

量測重點（arXiv:2609.00065）：
- **163 個 skill 的常駐 description 合計僅佔 200k token window 的 7.1%**——即「常駐放摘要、內容按需載入」是刻意設計，避免知識全塞。
- **median workflow 佔 window 23.9%**——但 29/46 個 workflow 若把 references 全載入會 overflow，**論文據此主張「只載入被觸發 skill 的相關片段」的必要性**（也是其對「長上下文」方案的直接辯護）。

### 3.4 skill 內部格式（以 pkpd-modeling 為例）

```
frontmatter: name, description, license, allowed-tools
body:
  - rules（3 條：如何建模、如何驗證、如何回報）
  - scripts 表（可用於建模的腳本）
```

即每個 skill = **「給 agent 的領域操作說明＋工具白名單＋輔助腳本」的單元**。agent 只在任務觸發時載入，載入後獲得：要做什麼（rules）、能用什麼（allowed-tools）、怎麼算（scripts）。

### 3.5 安全層

- Cisco AI Defense Skill Scanner 每週自動掃描、發布 security-report。
- README 明確建議使用者在正式環境自行 review 每個 skill。

### 3.6 核心機制一句話

```
166 個領域專用 skill（每個 = SKILL.md 的 rules + allowed-tools + scripts）
        │  以 Agent Skills spec 結構化、以 Agent Plugins 打包
        ▼
  常駐只留 description（佔 200k window 7.1%）
        │
agent 依任務觸發 ──▶ 按需載入該 skill body（佔 window ~24%）
        │
        ▼
  獲得該領域「怎麼做／能用什麼工具／怎麼算」
```

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

> 對照第二大腦：以下替代方案在 `FATESAIKOU/MyBrain` 的判定，以表格標註 URL 與信任層級。**AI draft 標明為未經他 review 的草稿。** 第二大腦中「無任何對本 repo（scientific-agent-skills）的評估紀錄」——此標的為首見（Step 1 已確認）。

### 4.0 第二大腦既有判準（決定我怎麼看待這些替代方案）

讀取骨幹 `技術取捨準則.md`（generated.by `claude-code/opus-5`，status draft——AI 草稿未定稿）關鍵準則：

| 準則 | 內涵 | 對本節的影響 |
|---|---|---|
| 理解優先 | 不穩定或不熟悉 → 先自己兜，MVP 是理解驗證點 | 「直接導入 166 個 skill」vs「抽取其 skill 結構後自己兜」——傾向往後者 |
| Reject≠沒價值 | 被拒仍抽取需求理解與方案方向 | 下方被 Reject／觀望的方案，仍抽取其「結構化 skill 目錄」方向 |
| MVP→Feature 唯一閘門 | 能否影響個人 workflow | 本 repo 是否進 workflow，取決於他是否真有科學研究流程需求 |
| 不追新 | 汰換看上游死沒死，不看有沒有更好的 | 「有更多 skill」不構成採用理由 |

⚠️ 骨幹檔為 `draft`（AI 草稿），上述準則以「他在 interview 中陳述、AI 整理」層級引用，非本人親筆定稿。但與 `判定總表`（status draft）一致，可作判準依據。

### 4.1 判定總表現況：第二大腦無本 repo 的直接判定

grep `scientific-agent-skills`、`AI Scientist`、`科學 skill`、`scientific skill` 於全 bundle：**第二大腦無此標的的任何評估紀錄。** 此為首見。

最相近的「skill 庫 / 領域專用 skill」既有判定：

| 主題 | 判定 | 理由 | URL | 信任層級 |
|---|---|---|---|---|
| **agent-skills**（Addy Osmani 工程紀律 skill 框架） | 觀望 | 判定成立但未排入下一步清單（2026-08-11 由採用降級），沒有實際導入；開發工作流實際承載者是 mattpocock skills＋OpenSpec | [連結](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/agent-skills.md) | generated.by `human:fatesaikou` · status stable |
| **academic-research-skills**（學術研究 workflow/agent prompt 集） | 不採用 | 領域專用的 workflow/agent prompt 集，他用不到；階段式 pipeline＋integrity gate 的編排架構 | [連結](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/academic-research-skills.md) | generated.by `human:fatesaikou` · status stable |
| **awesome-gpt-image-2**（Agent Skill 資源庫） | 不採用 | 目前無大量生圖需求、無 benchmark、無法擴張到其他 image model | [連結](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/awesome-gpt-image-2.md) | generated.by `process:learn-gh-agent` · status draft |
| **andrej-karpathy-skills**（四原則結對編程 skill） | 不採用 | 認知負債不該由人類逐行承擔，與他對認知負債的理解方向相反 | [連結](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/理解%20andrej-karpathy-skills.md) | generated.by `human:fatesaikou` · status stable |
| **Taste Skill**（覆寫 AI 生成風格的 skill） | 不採用 | 過分偏向設計師，知識儲備不足 | [連結](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Taste%20Skill.md) | generated.by `human:fatesaikou` · status stable |

### 4.2 替代方案清單

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **同質：其他科學 skill 庫**（如 academic-research-skills、其它 AI-Scientist 專案） | 把學術/科學流程拆成 pipeline＋agents＋integrity gate | 有明確的學術研究全流程需求 | 領域專用、難泛用到個人 workflow；流程綁死特定研究方法 | 對學術研究者有效；對無此流程者無用 |
| **同質：自建 skill（抽取結構自兜）** | 依 Agent Skills spec 自己寫需要的少數 SKILL.md | 已理解自己的科學/研究流程需求；有時間自建 | 需維護 frontmatter/rules/scripts；初期成本高 | 完全貼合個人 workflow；對應「理解優先」準則 |
| **替代架構：長上下文全塞（長 context 方案）** | 不分割 skill，把領域知識全放進 context window | 有長 context 模型且不介意成本 | token 成本高、上下文污染、知識過期要整份更新 | 免去按需載入機制；但成本與污染隨知識量線性上升 |
| **替代架構：MCP server / 工具伺服器** | 把領域能力包成 MCP 工具，agent 透過 protocol 呼叫 | 需要工具呼叫與伺服器部署 | 每個工具是獨立實作，仍需領域知識；維護面比純 prompt skill 重 | 提供真實執行能力（呼叫資料庫/API）；但「怎麼做」的領域知識仍需 prompt 或文件 |
| **思考方式：領域 workflow 編排**（academic-research-skills 路線） | 定義階段式 pipeline＋agent persona＋integrity gate | 需要可拆解成固定階段的流程 | 編排層重、領域綁定 | 對固定流程有效；對開放探索性任務過重 |

### 4.3 切入點差異

- **scientific-agent-skills**：在「**skill 內容層**」解決——把大量領域知識結構化成可獨立載入的 skill 單元，強調**按需載入＋標準化打包**，可掛到任意通用 agent 上。
- **academic-research-skills**：在「**流程編排層**」解決——定義研究全流程的 pipeline＋agents＋integrity gate，是「領域 workflow 系統」而非「skill 庫」。
- **agent-skills**：在「**工程紀律層**」解決——定義軟體開發生命週期的 7 命令×6 階段，與科學領域無關，是同一個「skill 框架」慣例在工程領域的姊妹作。
- **長上下文方案**：在「**context 管理層**」解決——不分割知識，用更大的 window 直接裝下，省去載入機制但付出成本。
- **MCP server**：在「**執行能力層**」解決——提供真實工具呼叫，但領域知識仍需要另外傳遞。

### 4.4 與第二大腦判準的對照與潛在衝突

- **直接相關的既有判定（academic-research-skills 不採用）**：使用者對「領域專用 workflow/agent prompt 集」的態度是「他用不到」。本 repo 屬同一類「領域專用 skill 庫」——**若照此先例，存在同樣的「領域綁定、難進個人 workflow」傾向**。此為與「本 repo 值得深用」的潛在衝突，須明示。
- **「理解優先、先自己兜」衝突**：使用者準則強調不熟悉就先自己兜以理解本質。本 repo 直接提供 166 個現成 skill，**照通則他更可能抽取其「skill 結構＋按需載入＋Agent Skills spec」方向後自行客製，而非整套導入**。
- **閘門判斷**：`下一步清單`（draft）與 `專案現況表` 中**無任何科學研究 skill 庫相關的進行中專案**（Step 1 已確認）。按「進 Feature 唯一閘門＝能否影響個人 workflow」準則，此 repo 現階段**無直接進入他 workflow 的依據**，傾向停留在理解層。
- **同向支持**：repo 的「常駐 description＋按需載入 body」與他對 context/token 效率的關切一致（對應其採用 LLM 降本增效、LeanCtx/Headroom 等 context 治理工具的取向）；其「Agent Skills spec 標準化」也與他「skill 類框架」（agent-skills 觀望）同一條路。

> ⚠️ 上述 §4.4 的對照是**我（LLM）依其準則的推演**，非他本人對本 repo 的判定。第二大腦沒有本 repo 的任何判定紀錄。

---

## 5. User Q&A

（本輪 R1 為初次分析，使用者尚無追問，暫無此節。）
