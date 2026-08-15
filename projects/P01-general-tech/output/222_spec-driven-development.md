# 仕様駆動開発（Spec-Driven Development, SDD）的消費期限

> 調研標的：watany（NTTテクノクロス）於 AI Native Dev Night Tokyo 的簡報《仕様駆動開発の消費期限》
> 來源：https://speakerdeck.com/watany/expiration-date-of-sdd （登壇 2026/8/6，8.2k views，提供 PDF）
> 使用者提問標題寫「賞味期限」，簡報實際標題為「**消費期限**」——兩者用字不同，本報告以簡報的「消費期限」為準，並在 §3 說明其意涵。

---

## 1. 這個技術解決什麼問題？

**SDD（Spec-Driven Development，仕様駆動開発）解決的是：在 AI 生成程式碼的時代，如何讓「人」在 agent 高速產出之下，仍然能理解、審查、並長期掌握系統的實際行為。**

具體拆成兩個被解決的子問題（簡報 slide 8、11、15 明示）：

| 子問題 | 內容 |
|---|---|
| **AI workflow 框架** | agent 需要一套「步驟」才能穩定產出。SDD 把流程固定成「仕様 → 設計 → タスク化」，讓 agent 照著走，避免它跳過規格直接寫 code |
| **agent 的長期記憶文件管理** | agent 的 context window 有限，跨 session 會忘。spec 檔案作為「版本管理、人可讀的 super prompt」，是 agent 的長期記憶載體 |

**問題描述是否含糊？** 是。SDD 這個詞在 2025/7 由 AWS 隨 IDE「Kiro」發表而提唱，但「仕様駆動開発」的定義在社群中被擴張（簡報 slide 9 引用日經書評與 hdkworks 文章，各自給出「3 技術要素／4 原則／7 工程」等不同框架）。簡報作者自己收斂為「retro-ronym」——即 Vibe Coding 之後，為了區別「實作前先做仕様書」這個做法而事後造出的詞。因此「SDD 到底指什麼」本身就有歧義，本報告以簡報作者的收斂定義為準。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章中明確提到的背景

**（a）Vibe Coding 之後的產物。** SDD 是「實作前先做仕様書」的 retro-ronym（slide 8）。Vibe Coding 讓 agent 直接生成程式碼，但人無法理解、無法審查、無法維護——於是「先寫規格」被重新包裝成一個有名字的方法論。

**（b）LLM 自走性能的轉折點。** SDD 的 workflow「仕様→設計→タスク化」成形於 2025/7〜9（slide 19），距今約一年。當時主流模型是 Claude Sonnet 4 / Opus 4.1、GPT-4o/4.1/o3、DeepSeek V3.1 等。其後 2025/11 的 GPT-5.2 與 Opus 4.5 被視為真正的轉折點（slide 20，引用 Karpathy），agent 自走性能大幅提升。

**（c）「事前做任務清單再實作」已普遍化。** 這個做法被併入 coding agent 的 **Plan Mode**（slide 21-22），成為「當紅的當紅」——SDD 的 spec-first 風格與 Plan Mode 合流，不再是 SDD 獨有。

**（d）認知負債與認知負荷。** 簡報引用 Thoughtworks Radar 的「codebase cognitive debt」與 2026 年 arXiv 研究（207 名學生 8 週日誌）的「Comprehension Debt」（slide 41-42）：agent 生成物若人無法理解，就變成負債；而 agent 速度（500 PR/day）遠超團隊審查能力（10 PR/day），形成瓶頸（slide 43）。

### 2.2 通用技術背景（簡報未明說，補查）

- **Context Window 是硬限制。** LLM 能參考的總 token 數受限（slide 40），agent 無法在單一 session 記住整個專案，因此需要外部文件作為「長期記憶」。
- **「守破離」框架。** 簡報用日本武術的「守破離」來定位 SDD：先守型、再破型、最後離型。AI 驅動開發目前「守」的型尚未確立（slide 30），SDD 是作者選定的「守」的型。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 核心機制：把「規格」當成 workflow 的骨架

SDD 的實質核心是「**仕様 → 設計 → タスク化**」的 workflow（slide 14）。不同實作（Kiro、Spec-Kit、OpenSpec）只是這個骨架的變體：

| 實作 | 流程 |
|---|---|
| Kiro | Requirements → Design → Tasks |
| Spec-Kit | Specify → Plan → Tasks |
| OpenSpec | Proposal → Specs → Design → Tasks |

### 3.2 spec 實作的三種模式（slide 15-16）

| 模式 | 做法 | 是否實用 |
|---|---|---|
| **spec-first** | 先寫 spec 開發，任務完成後**破棄** spec | ✅ 實用 |
| **spec-anchored** | 任務完成後**保留** spec，持續更新供維護 | ✅ 實用 |
| **spec-as-source** | spec 為唯一來源，code 由 spec 生成，人**不直接編輯** code | ❌ 作者註明實務上幾乎沒人用 |

> 作者特別標註：**實務上只有前兩種被實際使用**（slide 16）。spec-as-source 是理想型，但實務上不可行。

### 3.3 「消費期限」的意涵（使用者問題 2 的核心）

簡報標題「消費期限」不是指 SDD 會「壞掉」，而是指**「破型的時機」**（slide 50）。作者用「守破離」框架定位：

```
守（SDD 作為型）──→ 破（遇到課題）──→ 離（進到下一步）
```

**消費期限＝型該被破掉的時間點。** 判斷標準是：

- **遇到課題之前**：SDD 易懂、好用，是好的「守」的型
- **已知課題浮現時**（slide 50）：
  1. coding → review 的瓶頸（agent 產出太快，人審不完）
  2. spec 檔案群的 drift 管理（多份 spec 之間的一致性）
  3. 被 spec 語言束縛，無法發揮 LLM 性能（最新 LLM 的 best practice 是「減少 prompt」）
- **團隊全員都覺得消費期限到了**：就該進到下一步，不要硬守

> 一句話：**「消費期限」不是 SDD 的缺點，而是它作為「型」的設計意圖——型是拿來破的，不是拿來守一輩子的。**

### 3.4 作者實際的選型決策（作為「守」的型）

作者在團隊導入時比較了幾個框架（slide 30-47）：

| 候選 | 判定 | 理由 |
|---|---|---|
| **AI-DLC** | 捨棄 | 重厚長大，導入後 sank cost / lock-in 風險高，理念與 workflow 導入期間上太難（slide 34） |
| **Skills 堆疊**（superpowers 等） | 捨棄 | 個別流程好，但「無型」，無法作為標準化 harness（slide 37） |
| **Spec-Kit** | 捨棄 | 生成的文檔重厚長大，認知負荷過高（slide 47） |
| **OpenSpec** | **採用** | 輕量、有 `/opsx:verify`（spec 與實作一致性檢查）與 `/opsx:archive`（實作後同步回主 spec）等好用的命令（slide 47） |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

> 本節對照使用者的第二大腦（FATESAIKOU/MyBrain）既有判定。**SDD 本身在第二大腦中沒有被評估過**（判定總表 86 筆無此主題），但 SDD 的替代方案——OpenSpec、superpowers、mattpocock、OKF、AI-DLC——**全部都被他評估過**，且與簡報作者的結論高度重疊。以下 DA 表與對照皆以 MyBrain 判定為準。

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **OpenSpec**（Fission-AI） | 以 `openspec/` 目錄 + Proposal→Specs→Design→Tasks 流程，把 spec 當長期沈澱資產，`/opsx:archive` 把 delta 併回主 spec | 每個專案要 `openspec init`；擔保者是人（品質取決於人有沒有盯） | 短期實作無強制機制；spec 檔案群需 drift 管理 | 長期規格會累積成「系統真相」，三個月後讀 specs 就有答案 |
| **superpowers**（obra） | 1 句話啟動，8 個 skill 自動串（brainstorming→worktree→plans→subagent→TDD→review→verify→finish），流程強制擔保品質 | 團隊場景（「我不信任執行者」的假設成立）；有 deadline | 成本高（28 subagent / $0.12）；plan 比 design 大 4 倍，個人開發是純成本；沈澱不整合 | 單次交付高品質、低操作負擔、比案 A 快一倍 |
| **mattpocock skills** | 零件盒，`/grill-with-docs` 逼問使用者、邊做邊寫 CONTEXT.md + docs/adr/ | 插在別人骨架上用；不接管流程 | 跳過 `/setup` 則 CONTEXT.md 不產生 | 開工前對齊有效，14 題採納推薦 11/14 |
| **OKF**（Open Knowledge Format） | 用目錄樹 Markdown + YAML frontmatter 標準化 agent 知識表示 | 需要跨系統、跨供應商、跨工具的知識互通 | 結構太固定，知識圖譜需要擴張與自適應性 | 知識可互通、可版本管理 |
| **AI-DLC**（AWS） | 完整 AI 驅動開發生命週期框架，含理論與 workflows | 需要大幅調整既有開發流程、與公司標準對齊 | 重厚長大，導入 sank cost / lock-in 高 | 完整生命週期覆蓋，但導入成本高 |

### 4.2 對照第二大腦的既有判定（含 GitHub URL 與信任層級）

| 替代方案 | MyBrain 判定 | 信任層級 | 時間 | 與簡報作者的異同 |
|---|---|---|---|---|
| **OpenSpec** | **採用（Accept）**，個人開發主力之一 | `claude-code/opus-5` 草稿，未經本人 review | 2026-08-02 | **一致**。簡報作者也選 OpenSpec（捨 Spec-Kit） |
| **superpowers** | **保留（Reserve）**，留給團隊場景 | `claude-code/opus-5` 草稿，未經本人 review | 2026-08-02 | **一致**。簡報作者也認為 Skills 堆疊「無型」不適合個人 |
| **mattpocock skills** | **採用（Accept）**，個人開發對齊主力 | `claude-code/opus-5` 草稿，未經本人 review | 2026-08-02 | 簡報作者未單獨評估，但簡報引用了 mattpocock 的 grill-with-docs 做法（slide 24） |
| **OKF** | **不採用（Reject）**：結構太固定，應定義 meta data 而非結構 | `human:fatesaikou` 本人，`stable` | 2026-07-25 | 簡報把 OKF 列為「spec 以外的 agent 記錄方法」之一（slide 25），但使用者已 Reject |
| **AI-DLC** | **採用（Accept）**：要導入，且定義了各階段 AI 與人的分工 | `human:fatesaikou` 本人，`stable` | 2026-05-10 | **衝突**。簡報作者捨棄 AI-DLC（重厚），但使用者判定要導入 AI-DLC |

**來源：**
- OpenSpec / superpowers / mattpocock 判定：https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/AI開發workflow方案比較.md 與 https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/AI開發workflow實測.md （`claude-code/opus-5` 草稿，未經本人 review）
- OKF 判定：https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OKF.md （`human:fatesaikou`，`stable`）
- AI-DLC 判定：https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/理解%20AI-DLC%20決斷要不要導入.md （`human:fatesaikou`，`stable`）
- 判定總表（86 筆索引）：https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md （`ollama-cloud/deepseek-v4-flash` 草稿）

### 4.3 與既有判定的衝突（對照最有價值處）

**衝突點：AI-DLC。** 簡報作者明確捨棄 AI-DLC（「重厚長大」），但使用者在 2026-05-10 判定**要導入 AI-DLC**，且已定義各階段分工（企画/要件定義/開発/デリバリー 中 AI 與人的角色）。這是一個真實的張力：

| 面向 | 簡報作者（watany） | 使用者（MyBrain） |
|---|---|---|
| AI-DLC | 捨棄（重厚、sank cost、lock-in） | 採用（要導入，已定義分工） |
| 個人 vs 團隊 | 團隊導入場景 | 個人開發場景 |
| 時間點 | 2026/8 評估 | 2026/5 判定 |

**解讀：** 兩者不必然矛盾。簡報作者是在「團隊導入」場景下嫌 AI-DLC 重；使用者的 AI-DLC 判定也是「導入」但著重在**分工定義**（誰主司哪階段），而非完整導入整套 workflows。且使用者後續（2026-08-02）在個人開發場景實際採用了更輕量的 OpenSpec + mattpocock 組合——這與簡報作者的「捨 AI-DLC、選 OpenSpec」方向一致。**換言之：使用者的「AI-DLC 導入」判定停留在 2026/5 的理論層，而 2026/8 的實作層已走向與簡報作者相同的輕量路線。** 此為 AI 草稿與本人 stable 判定之間的潛在張力，值得在 QA 中釐清。

### 4.4 切入點差異

- **OpenSpec**：切入點是「**長期沈澱**」——spec 是會累積的資產，回答「系統現在怎麼運作」。
- **superpowers**：切入點是「**流程強制**」——用硬規則封死 agent 偷懶路徑，人退到核可位。
- **mattpocock**：切入點是「**開工前對齊**」——逼問使用者把決策與術語寫下來。
- **OKF**：切入點是「**知識表示標準化**」——跨系統互通，而非單一專案的開發流程。
- **AI-DLC**：切入點是「**完整生命週期**」——從企画到 Ops 全覆蓋，最重也最全。

### 4.5 對使用者個人工作流的影響（使用者問題 3）

對照使用者的技術取捨準則（https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md，`claude-code/opus-5` 草稿）：

| 準則 | 對 SDD 的意涵 |
|---|---|
| **理解優先**：不穩定或不熟悉先自己兜，MVP 是理解驗證點 | SDD 的 spec-first 本質就是「先理解需求再實作」，與他的理解優先原則同構 |
| **MVP → Feature 唯一閘門**：能否影響個人 workflow | SDD 是否進 Feature，取決於它能否影響他的日常 workflow——他目前個人開發主力已是 OpenSpec + mattpocock，SDD 的「spec-first」已被這組合涵蓋 |
| **Reject ≠ 沒價值**：抽取需求理解與方案方向 | 即使不採用 SDD 這個詞，其「規格作為長期記憶」的方向已被 OpenSpec 承接 |
| **約束在 harness 不在權限**：要 verify 不要人工審核 | SDD 的 `/opsx:verify`（spec 與實作一致性檢查）正是他要的「你怎麼知道自己做對了」的驗證機制 |

**結論：** 對使用者而言，SDD 不是一個需要「新導入」的技術——他 2026-08-02 已實測並採用的 OpenSpec + mattpocock 組合，正是 SDD 的「spec-anchored」模式實作。SDD 對他的價值在於**提供了一個「消費期限」的判斷框架**：當他遇到 coding→review 瓶頸、spec drift、或被 spec 語言束縛時，就是該「破型」的時機。這與他「MVP 達成理解後即停止」的準則一致——型是拿來破的。

---

## 附錄：簡報引用來源

- Kiro：https://kiro.dev/ 、https://kiro.dev/blog/kiro-and-the-future-of-software-development/
- GitHub Blog（SDD toolkit）：https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/
- Martin Fowler（SDD 三工具）：https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html
- OpenSpec：https://github.com/Fission-AI/OpenSpec
- Karpathy LLM Knowledge Base：https://dev.classmethod.jp/articles/karpathy-llm-knowledge-base/
- OKF：https://cloud.google.com/blog/ja/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/
- Thoughtworks Radar（cognitive debt）：https://www.thoughtworks.com/radar/techniques/codebase-cognitive-debt
- arXiv（Comprehension Debt）：https://arxiv.org/abs/2604.13277
- AI-DLC：https://aws.amazon.com/jp/blogs/news/ai-driven-development-life-cycle/
- Context Engineering：https://blog.langchain.com/context-engineering-for-agents/
