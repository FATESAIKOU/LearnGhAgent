# prime-agent — Prime Intellect 開源的自進化 RLM 程式設計與研究 Agent

> 調研標的：https://github.com/PrimeIntellect-ai/prime-agent
> 定位：general / long-running 的 coding & research agent，核心賣點是「自進化（self-improving）＋ RLM（Recursive Language Model，遞迴語言模型）＋ Continual Harness（持續式 harness）」。

---

## 1. 這個技術解決什麼問題？

**一句話**：解決「AI coding / research agent 無法勝任長時程、跨 session 的自主任務」——具體是三個疊加的問題：

1. **context window 有限**：單一模型一次能「看到」的上下文有上限，長任務（多輪、多檔案、多子任務）會把 context 塞爆，導致 agent 忘掉前面的決策與工作狀態。
2. **agent 是無狀態的**：每次對話結束，工作狀態、已探索的結果、可重用的操作模式全部消失，下次要從冷啟動重來。
3. **agent 不會自己變好**：傳統 coding agent 的「能力」寫死在 system prompt 與工具集裡，任務做完就結束，不會把這次學到的可重用模式沉澱下來供下次使用。

prime-agent 把這三個問題當成同一個問題解：**讓 agent 的「工作狀態」與「可重用能力」以程式化、可持久化、可自我改進的形式存在，而不是存在一次性的對話裡**。

**模糊之處**：官方定位是「general and long-running work」，但「general」的邊界沒有明確定義——它宣稱適用 coding 與 research，實際驗證數據（見 §3）集中在 coding 與特定 research 環境，泛用性宣稱大於已驗證範圍。另外「self-improving」指的是**改進 harness 狀態（prompt / memory / skill / subagent 規格）**，不是改進模型權重——這與「自進化」一詞可能帶給人的「模型自己變強」直覺不同，需先釐清。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章中明確提到的背景

- **RLM 的起源**：RLM（Recursive Language Model）由 Alex Zhang 於 2025-10 提出，定位是 **inference-time scaling 範式**——在推理階段用「遞迴」與「程式化執行」來擴展能力，而不是靠更大的模型或更長的訓練。它把 context 當成「變數」（prompt-as-a-variable）、把工具與子 agent 當成「函式呼叫」（programmatic tool / subagent calling），在一個 persistent REPL 裡執行。
- **Continual Harness 的起源**：源自「Gemini Plays Pokemon」這類 reset-free 自改進 harness 研究（arXiv 2605.09998）。核心主張：agent 應該在執行中交替「act（做事）」與「refine（改進自己的 prompt / sub-agents / skills / memory）」，形成一個線上 process-reward co-learning loop，而不是每次從固定 prompt 開始。
- **長任務的工程需求**：README 明列「Built for Long-Running Work」——daemon 背景執行、heartbeat、schedule、persistent goals、autonomous mode、retained subagents，這些都是為了讓任務能跨 turn、跨 terminal session 持續推進。

### 2.2 通用技術背景（非文章明講，屬既有脈絡）

- **LLM 的 context window 是硬上限**：這是 transformer 架構的固有限制。長任務的 token 累積速度遠快於模型能「記住」的速度，因此所有長程 agent 都必須面對「context 治理」——壓縮、摘要、外部記憶、子任務隔離。
- **agent 的無狀態性**：LLM 本身是 stateless 的函式，每次呼叫只看到這次的輸入。跨 session 的「記憶」必須由外部 harness 提供（檔案、資料庫、向量庫、MCP server 等），這是整個「agent memory」研究領域的起點。
- **coding agent 的既有做法**：主流 coding agent（Claude Code、Cursor、Copilot 等）把能力綁在「工具集 + system prompt」上，靠「讀檔 → 改檔 → 跑測試」的回合迴圈工作。它們的長任務能力受限於 context 治理，且「學到的東西」不會自動沉澱成可重用能力。

---

## 3. 這個技術是如何解決該問題的？

prime-agent 用**兩個核心抽象**疊加解決上述問題：**RLM 程式設計模型**（解決 context 與無狀態）＋ **Continual Harness**（解決「不會自己變好」）。

### 3.1 RLM 程式設計模型：把 agent 當成「會寫程式的程式」

核心機制：**模型在一個 persistent IPython kernel 裡工作，所有能力都用「寫 Python 程式」的方式組合**，而不是靠一堆獨立的內建工具。

```
Task + working context
        │
        ▼
   Parent model ──IPython call──▶ Persistent IPython kernel
        ▲                            │
        │                            ├─▶ Files · data · shell commands
        │                            ├─▶ Python-backed skills
        │                            └─▶ rlm(...) child agents
        │
   Answer / next turn
```

**四個核心不變量（Core Invariants）**：

| 不變量 | 機制 | 解決的問題 |
|---|---|---|
| **1. 執行是程式化的** | 唯一內建模型工具是 `ipython`。讀檔、改檔、跑命令、轉換結果、呼叫 skill、委派子任務，全部從 persistent kernel 出發。Python 狀態（變數、import、函式、解析結果）跨 tool call 與 compaction 存活 | context 不再被「每次工具呼叫的完整輸出」塞爆；工作狀態存在 kernel 變數裡，而非對話歷史裡 |
| **2. 子 agent 是原生 RLM 呼叫** | `rlm(...)` 是 kernel 內預載的可呼叫物件。`handle = await rlm("...", name="auth-reviewer")` 立即回傳 child handle，子 agent 有獨立 context 與 session，結果透過 `agent_message` 或檔案回傳，**不是** `rlm()` 的回傳值 | 子任務只拿到自己需要的 context，父 agent 的 context 保持聚焦；可平行、可背景、可遞迴 |
| **3. Skill 是程式化能力** | 支援 Agent Skills markdown 格式，並擴充 Python-backed skills（Python package 安裝進 kernel，以 import name 暴露）。`report = await release_audit(repository=".", target_version="0.4.0")` | 可重用能力是「可執行的程式」，不是「一段提示詞」；skill 本身也能呼叫 `rlm(...)` 遞迴委派 |
| **4. 狀態設計成跨 turn 存活** | 自動 compaction 摘要舊 context、daemon worker 在 client 斷線後續跑、child registry 可恢復、heartbeat/schedule 可重新進入 session、persistent goals 持續到完成、autonomous mode 有界續跑 | 長任務跨 turn、跨 terminal session 持續推進，不因 UI 關閉而中斷 |

**Host Bridge**：Python skill 需要「權威狀態在 kernel 之外」的能力（goal、agent_message、heartbeat、compact）時，透過 `rlm.host_request(...)` 呼叫 TypeScript host，由 host 驗證並擁有狀態轉移。這把 credentials、provider 執行、transcript 寫入、worker 路由、排程留在 host，Python 只保留程式化介面。

### 3.2 Continual Harness：讓 agent 能自我改進

核心機制：**把「補充的 prompt、記憶、skill 描述、可重用 subagent 規格」存成 durable state，agent 可以透過 `/refine` 用「小步、有證據支持的更新」改進這些狀態**。

- `/refine` 回顧目前的 trajectory，套用小的、可 review 的更新到補充 harness 狀態。
- **永不改寫不可變的 base system prompt**——只改補充層。
- 記錄 refinement history，snapshot 支援 rollback。
- 預設 local to session（不自動外洩到全域）。

```
Continual Harness（durable state）
├─ supplemental prompts
├─ memories
├─ skill descriptions
├─ reusable subagent specifications
└─ refinement history（可 rollback）
        ▲
        │  /refine（小步、evidence-backed 更新）
        │
   Agent 交替 act（做事）↔ refine（改進 harness）
```

### 3.3 系統架構：daemon / worker / kernel 分層

```
Interactive TUI / headless clients
        │  AgentConnection（client-side execution boundary）
        ▼
   Daemon supervisor（routing · attachments · recovery）
        │
        ▼
   Session worker（one root session tree）
   ├─ AgentSessionRuntime
   ├─ Root AgentSession（provider calls · compaction · goals · child lifecycles）
   ├─ Scheduler
   ├─ Root IPython kernel
   └─ RLM child runtimes（session + optional kernel）
        │
        ▼
   Model providers / Session storage（JSONL + artifacts）
```

- **client 只負責渲染與輸入，不擁有執行**。
- **supervisor** 負責 discovery、routing、attachments、worker health、跨 agent 訊息傳遞。
- **每個 worker** 擁有一個 root runtime、scheduler、kernels 與所有後代。
- **AgentSession** 擁有 provider calls、queues、tools、compaction、goals、child lifecycles、transcript 寫入。
- **IPython 是 model-facing 的 control environment**。

> ⚠️ **信任模型（重要）**：README 與 architecture 都明講——**worker 與 kernel 是分開的 process，目的是 lifecycle 隔離與失敗恢復，不是安全沙箱**。IPython kernel 以 worker 的 OS 權限執行 model 產生的 Python 與專案命令。官方建議：untrusted code 要放外部 sandbox 或受限環境。

### 3.4 效果數據（RLM 論文 arXiv 2512.24601）

RLM 是 inference-time scaling 範式，可處理超出 context window 兩數量級的工作。median 提升（相對於既有方法）：

| 對照 | 提升 |
|---|---|
| vs compaction | +26% |
| vs CodeAct | +130% |
| vs Claude Code | +13% |
| RLM-Qwen3-8B vs 底層模型 | +28.3% |

RLM 提升長上下文與 token 效率，但**增加時間**（遞迴與程式化執行有額外開銷），且需 RL 訓練才能釋放潛力。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

「解決類似問題」在此指：**讓 coding / research agent 能處理長任務、跨 session 記憶、並自我改進**。以下替代方案分兩類：**同問題域的 agent 記憶 / context 治理方案**，與**同問題域的 coding agent 產品**。

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **EverOS**（LLM 長期記憶作業系統） | 仿生物銘印的記憶生命週期：對話流 → MemCell（情節軌跡＋原子事實）→ MemScene（主題化語意鞏固）→ 重建式召回（BM25＋向量＋RRF） | 需要跨 session 維持一致行為與狀態追蹤的長期互動 agent | 機制複雜、規模大、無自組織驗證手段；泛用但未專門化 | 讓 agent 跨 session「記住、理解、持續演化」 |
| **LeanCtx**（context 治理層） | 在 coding agent 與 LLM 之間插入四維治理層：壓縮（10 種讀取模式＋AST＋熵過濾）、記憶（session/knowledge/property graph 三層）、路由（自動匹配讀取精度）、治理（RBAC＋預算＋loop detection） | 想降低重複讀取、shell 噪音、跨會話記憶喪失三個 token 浪費 | 需在 agent 與 LLM 間架一層；本機 ONNX embedding 有 CPU 成本 | 重複讀取 ~2000→~13 tokens、`git status` ~800→~120 tokens |
| **Headroom**（context 內容感知壓縮） | 在 tool output 到達 LLM 前做內容感知壓縮（60–95% token 減省），CCR 可逆壓縮讓 LLM 隨時取回原始資料 | 想降低 context window 成本、避免低價值資訊佔滿 context | 壓縮有延遲與失真風險（需可逆機制補償） | 60–95% token 減省，context 只留高價值資訊 |
| **Muse Code**（Meta 終端 coding agent） | 長時程 async background agents（session 內常駐）、append-only local event log（crash 後 replay-exact）、`/plan`→`/grill`→`/goal` 規劃 skill、approval＋OS sandbox | 想要長時程背景 agent 與 crash 後可承接的長任務 | beta 未穩定；換 harness 撞「不追新」；Contributor tier 授權 Meta 訓練 | 可承接 24 小時長任務、restart-safe |
| **Kimi Code**（Moonshot 終端 agent） | 自主跨檔案重構、多步驟開發、shell 操作、網頁抓取、ACP/IDE 整合、MCP 生態、子 agent 並行 | 想要開源模型＋終端 agent 的長程程式設計 | 模型品質改善但已有更低價替代 | 長程程式設計、百萬 token 上下文 |
| **OpenCode**（AI 輔助編碼 CLI） | 透過 Ollama 整合多模型後端，避免綁定特定供應商 | 想要可自由切換模型的 coding CLI | 大致堪用但無長任務自我改進機制 | 多模型自由度、避免供應商綁定 |
| **HermesAgent**（全機式自主記憶 AI Agent） | 自主記憶＋自動 context 抽取與維護；browser 操作強 | 想要有自主記憶的全機式 agent | 記憶抽取是工程抉擇，需維護 | 跨 session 自主記憶、自動 context 抽取 |

### 4.2 各方案切入點差異

- **prime-agent** 的切入點是**「程式化」**：把 agent 的能力全部變成「寫 Python 程式」，工作狀態存在 kernel 變數，可重用能力變成 Python-backed skill，自我改進靠 `/refine` 改 harness 狀態。它同時解決 context（程式化執行省 token）、無狀態（persistent kernel＋daemon）、自我改進（Continual Harness）三件事。
- **EverOS / OpenHuman** 的切入點是**「記憶」**：專注解決無狀態，用記憶生命週期（情節→語意→重建）讓 agent 跨 session 記住。不處理「自我改進能力」，也不把執行程式化。
- **LeanCtx / Headroom** 的切入點是**「context 治理」**：專注解決 context 塞爆，用壓縮＋記憶＋路由讓 token 更省。不處理「自我改進」，也不改變 agent 的執行模型。
- **Muse Code / Kimi Code / OpenCode / HermesAgent** 的切入點是**「agent 產品」**：提供可直接用的 coding agent，各有長任務、記憶、多模型等賣點，但**沒有「自我改進 harness」這層**——它們的能力是固定的，不會在執行中自己變好。

### 4.3 對照第二大腦（FATESAIKOU/MyBrain）的判定

> 以下為查詢第二大腦的結果。信任層級依 `generated.by` 與 `status` 標注；AI draft 為未經本人 review 的草稿。

**第二大腦沒有 prime-agent / RLM / self-evolving 的既有評估**——`技術/技術評估/判定總表.md`（88 筆）無此主題，grep `prime|RLM|self-evolv|reinforcement` 無命中。此標的對他是全新的。

**相關替代方案他判定過的部分**（來源：`技術/技術評估/判定總表.md`，`generated.by: ollama-cloud/deepseek-v4-flash`、`status: draft`，AI 草稿未 review）：

| 方案 | 他的判定 | 理由（總表） | 與本報告的關係 |
|---|---|---|---|
| **EverOS** | **不採用** | 機制複雜規模大、無自組織驗證、泛用未專門化、導入規模與專案年紀不符 | 同為「agent 記憶」問題域；他拒的是「記憶作業系統」這條路，不是「長任務 agent」本身 |
| **OpenHuman** | 未判定（分析報告） | 僅描述機制與比較替代方案，未給個人採用結論 | 同為「跨服務持久記憶」問題域 |
| **LeanCtx** | **採用** | 直接解決重複讀取、shell 噪音、跨會話記憶三個浪費 | 他接受的是「context 治理層」這條路 |
| **Headroom** | **採用** | 應嘗試壓縮效率與 lean-ctx | 同上，context 治理 |
| **Muse Code** | **試用**（模型層） | 用 opencode 接 Muse Spark 1.2 Contributor 試效能；換 harness 暫緩（撞不追新＋已覆蓋需求） | 同為「coding agent 產品」；他對「換 harness」持保守態度 |
| **Kimi Code** | **不採用** | 模型品質改善，已有更低價且品質滿足的替代 | 同為「coding agent 產品」 |
| **OpenCode** | **試用** | 大致堪用，Ollama 整合帶來自由度避免綁定 | 他現行的 coding harness |
| **HermesAgent** | **採用** | 有自主記憶與自動 context 抽取，browser 比 opencode 強 | 同為「自主記憶 agent」 |

**與本報告結論的衝突點（查詢最有價值處）**：

1. **「自我改進 harness」vs 他的「不追新」**：prime-agent 的 Continual Harness（`/refine` 自我改進）是它與所有替代方案最大的差異點。但第二大腦的技術取捨準則（`抽象理解/本質洞察/技術取捨準則.md`，`generated.by: claude-code/opus-5`、`status: draft`，AI 草稿未 review）明載他**「不追新」**——「出現更好的替代」不構成汰換理由。prime-agent 是 2026-05 才創建的新 repo（16k stars、MIT、TypeScript），屬「太年輕」一類，依他的準則這反而是「先自己兜」的觸發條件，而非直接採用。**本報告不建議他直接採用 prime-agent，而建議抽取其「程式化執行＋自我改進 harness」的需求理解與方案方向**——這正符合他「Reject ≠ 沒價值，會抽取需求理解與方案方向」的準則。

2. **「程式化執行」vs 他的「理解優先」**：prime-agent 把 agent 能力全部程式化（persistent IPython），這與他「先自己兜、理解本質」的準則（`技術取捨準則.md`）方向一致——他自己也傾向自兜 harness。但 prime-agent 的「自我改進」是**自動的**（`/refine` 自己改 harness），而他的 Harness Engineering（`抽象理解/本質洞察/Harness Engineering.md`，`generated.by: human:fatesaikou`、`status: stable`，本人定稿）強調「AI Guardrails：驗證規則程式化（Linter／Test＋CI／技術債定期清理／可動權限）」——**他要的是「你怎麼知道自己做對了（verify）」，不是「agent 自己改自己」**。prime-agent 的 `/refine` 有 refinement history 與 rollback，但「自我改進」的驗證機制是否足夠，與他「不要建議加人工審核關卡、要補驗證機制」的立場需要對照——這是他 review 時最值得追問的點。

3. **「長任務 agent」vs 他的「個人 AiAgent 入口」專案**：第二大腦 `技術/靈感/個人 AiAgent 入口.md`（`generated.by: claude-code/opus-5`、`status: draft`，AI 草稿未 review）顯示他有一個進行中的新專案「個人 AiAgent 入口」，卡在**執行環境未定**（自架實體 vs 自架雲端 vs 跑在終端）。prime-agent 屬同問題域（AI agent 形態），其 daemon-backed 長任務架構與「跑在終端」選項的常駐性需求相關，但**第二大腦無直接引用**，此為間接關聯，非本報告主體。

**查不到的**：第二大腦沒有 prime-agent 的既有評估、沒有 RLM 的既有評估、沒有「自我改進 agent」的既有判定。以上替代方案判定均為既有評估，prime-agent 本身無判定。

---

## 5. User Q&A

> 本節為 R2 追問輪沉澱。使用者對 R1 報告提出 5 個連貫澄清性質問，核心是把 RLM 定位對照他自己的架構（LearnGhAgent harness、MyBrain 外置大腦）講清楚，並收斂到「這東西對他的 AiAgent 入口／workflow 到底改善什麼」。以下依序回答。

### Q1：RLM 到底是 AiCoding Agent？還是 AiCodingAgent＋harness（類 LearnGhAgent）？還是 AiCodingAgent＋harness＋外置大腦（類 MyBrain）？

**A**：RLM 是**「AiCodingAgent＋harness」這一層**，不是單獨的 AiCoding Agent，也不是「＋外置大腦」。用你自己的 Harness Engineering 五問（`抽象理解/本質洞察/Harness Engineering.md`，`generated.by: human:fatesaikou`、`status: stable`，本人定稿）拆層對照：

| 層 | prime-agent 的對應 | 你的 LearnGhAgent | 你的 MyBrain |
|---|---|---|---|
| **AiCoding Agent（模型＋工具迴圈）** | 底層模型在 persistent IPython kernel 裡工作 | 底層模型＋工具集 | 不屬於 harness，是資料庫 |
| **harness（五問）** | RLM 程式設計模型＋Continual Harness | LearnGhAgent 的 4-step workflow、AGENTS.md、judge/ | 不屬於 harness |
| **外置大腦（跨 session 記憶庫）** | **無**——記憶存在 kernel 變數與 durable harness 狀態，不是獨立外置知識庫 | 無 | MyBrain（OKF bundle） |

**RLM 的「記憶」與 MyBrain 的「記憶」是兩種東西**：

| 面向 | prime-agent（RLM） | MyBrain |
|---|---|---|
| 記憶的載體 | kernel 變數、durable harness 狀態（prompt/memory/skill/subagent 規格） | 檔案系統上的 OKF markdown bundle |
| 記憶的用途 | 讓**單一 agent 的長任務**跨 turn 存活 | 讓**你本人**跨 session 查「我是誰／在哪／要去哪」 |
| 誰在讀 | 模型（程式化存取） | 你＋agent（透過 mybrain-read skill） |
| 是否自我改進 | 是（`/refine` 改 harness 狀態） | 否（寫入需你 review，`status: draft`→`stable`） |

**結論**：RLM 落在「AiCodingAgent＋harness」層。它沒有「外置大腦」這層——它的記憶是 harness 內部的程式化狀態，不是像 MyBrain 那樣獨立的知識庫。若你要對照，prime-agent ≈ 你的 LearnGhAgent（harness）＋ 一個把「記憶」內建在 harness 裡的機制，而非 LearnGhAgent＋MyBrain 的組合。

---

### Q2：RLM 的特點是比起一般 AiCoding Agent 只多了「自我改善」而已？

**A**：不是。RLM 的差異是**三件事疊加**，「自我改善」只是其中一件，而且它改的是 harness 狀態、不是模型權重：

| 差異點 | 一般 AiCoding Agent | prime-agent（RLM） |
|---|---|---|
| **執行模型** | 靠一堆獨立內建工具（讀檔、改檔、跑命令各自為政） | 唯一內建工具是 `ipython`，所有能力用「寫 Python 程式」組合，狀態存在 kernel 變數 |
| **context 治理** | 靠對話歷史＋手動摘要 | 程式化執行省 token＋自動 compaction，工作狀態在 kernel 變數而非對話歷史 |
| **自我改善** | 無，能力寫死在 system prompt 與工具集 | `/refine` 小步、evidence-backed 更新 durable harness 狀態（prompt/memory/skill/subagent 規格），可 rollback |

**「自我改善」的邊界（重要）**：`/refine` 改的是**補充 harness 狀態**，永不改寫不可變的 base system prompt，也**不更新模型權重**。所以「自進化」不是「模型自己變強」，是「agent 的 harness 設定會自己變好」。

**結論**：RLM 的差異是「程式化執行＋context 治理＋自我改善 harness」三件一起，不是只多一個「自我改善」。若只看到「＋自我改善」，會漏掉它把 agent 能力全部程式化這個更根本的差異。

---

### Q3：之前看到的 deepseekharness 是不是跟這東西是競品？

**A**：**不是競品，是正交的兩件事**。deepseekharness＝你在第二大腦已判定的 **DeepSeek-Reasonix**（`技術/技術評估/DeepSeek-Reasonix.md`，`generated.by: human:fatesaikou`、`status: stable`，本人定稿，**你已 Reject**）。兩者解決的問題不同：

| 面向 | prime-agent（RLM） | DeepSeek-Reasonix |
|---|---|---|
| 要解決的問題 | 長任務的 context 塞爆＋無狀態＋不會自我改進 | 長會話 token 費用過高（DeepSeek prefix cache hit 率低） |
| 切入點 | **能力**：把 agent 程式化＋自我改進 harness | **成本**：維持 byte layout 穩定以命中 DeepSeek 磁碟快取 |
| 核心機制 | persistent IPython kernel＋`/refine` | Cache-First Loop 三分區（ImmutablePrefix／AppendOnlyLog／VolatileScratch） |
| 你的判定 | 無（本報告不建議直接採用，建議抽取需求理解） | **Reject**：在沒有成功率基線的保障下做成本優化沒有意義 |

**兩者關係**：Reasonix 假設「agent 能力已固定，只優化成本」；prime-agent 假設「agent 能力要能自我改進」。Reasonix 的 cache-first loop 是**成本優化層**，prime-agent 的 RLM 是**能力層**——兩者可以疊加（在 prime-agent 上套 cache-first loop 省 token），不是互斥的競品。

**結論**：deepseekharness（DeepSeek-Reasonix）不是 prime-agent 的競品。Reasonix 優化成本、prime-agent 優化能力，切入點正交。你對 Reasonix 的 Reject 判定（無成功率基線做成本優化無意義）不影響 prime-agent 的評估——後者根本不在做成本優化。

---

### Q4：套用這東西，對我是改善「AiAgent 入口」，還是改善「我的 workflow」？

**A**：**兩者都不是直接改善，而是「先卡在執行環境未定」**。你的「個人 AiAgent 入口」專案（`技術/靈感/個人 AiAgent 入口.md`，`generated.by: claude-code/opus-5`、`status: draft`，**AI 草稿，未經你 review**）卡在**執行環境未定**（自架實體 vs 自架雲端 vs 跑在終端，2026-08-14 展開三選項未定案）。prime-agent 的落點要先看它屬於哪一層：

| 你的專案層 | prime-agent 的對應 | 是否被 prime-agent 改善 |
|---|---|---|
| **入口（前端 app＋後端）** | 無對應——prime-agent 是 terminal/headless agent，不是 app 入口 | 否 |
| **執行環境** | daemon-backed 長任務架構，與「跑在終端」選項的常駐性需求相關 | 間接相關，但**執行環境未定，無從套用** |
| **workflow（你日常怎麼用 agent）** | RLM 的程式化執行＋自我改進 harness | 需先有執行環境才談得上 |

**關鍵**：你的專案**先決問題是執行環境**，不是 agent 形態。prime-agent 屬「AI agent 形態」問題域，但**第二大腦無直接引用**，此為間接關聯。在執行環境定案前，套用 prime-agent 沒有落點——它既不是你的入口，也進不了你的 workflow。

**結論**：套用 prime-agent 對你**既不是改善入口、也不是改善 workflow**，因為你的「個人 AiAgent 入口」卡在執行環境未定，prime-agent 的落點（terminal agent 形態）要等執行環境定案後才談得上。它對你目前是「可抽取的需求理解與方案方向」，不是「可套用的改善」。

---

### Q5：承上，改善的是「維運成本」還是「AI 的產出效果」？

**A**：**prime-agent 改善的是「AI 的產出效果」，不是維運成本**——而且這正是它與你已 Reject 的 DeepSeek-Reasonix 的關鍵分野：

| 面向 | prime-agent（RLM） | DeepSeek-Reasonix（你已 Reject） |
|---|---|---|
| 改善的標的 | **產出效果**：長任務能跨 turn 存活、agent 能自我改進 harness | **維運成本**：token 費用 |
| 改善的機制 | 程式化執行省 token＋自我改進 harness | cache-first loop 命中 DeepSeek 磁碟快取 |
| 你的判定 | 無（本報告不建議直接採用） | **Reject**：無成功率基線做成本優化無意義 |

**對照你的取捨準則**（`抽象理解/本質洞察/技術取捨準則.md`，`generated.by: claude-code/opus-5`、`status: draft`，**AI 草稿，未經你 review**）：你對 Reasonix 的 Reject 理由是「在沒有成功率基線的保障下做成本優化沒有意義」——你**不把成本優化當成獨立價值**。prime-agent 不做成本優化，它做的是「讓 agent 產出更好」（長任務不中斷、能力會自我改進），這與你的準則方向一致。

**但**：prime-agent 的「自我改進」是**自動的**（`/refine` 自己改 harness），而你的 Harness Engineering（stable，本人定稿）強調「AI Guardrails：驗證規則程式化（Linter／Test＋CI／技術債定期清理／可動權限）」——你要的是「**你怎麼知道自己做對了（verify）**」，不是「agent 自己改自己」。prime-agent 的 `/refine` 有 refinement history 與 rollback，但「自我改進」的驗證機制是否足夠，與你「不要建議加人工審核關卡、要補驗證機制」的立場需要對照——這是你 review 時最值得追問的點。

**結論**：prime-agent 改善的是**產出效果**（長任務能力＋自我改進 harness），不是維運成本。這與你對 Reasonix 的 Reject（成本優化無意義）不衝突，因為兩者切入點正交。但 prime-agent 的「自動自我改進」與你「verify 優先」的 harness 準則存在張力——它改 harness 的驗證機制是否足夠，是你要追問的點。

---

## 附錄：調研資料來源

| 來源 | 內容 |
|---|---|
| repo README | 定位、兩大抽象、長任務功能、信任模型、license（MIT） |
| `packages/coding-agent/docs/rlm.md` | RLM 程式設計模型、4 個核心不變量、trust model |
| `packages/coding-agent/docs/architecture.md` | daemon/worker/kernel 分層架構 |
| Prime Intellect RLM blog | RLM 起源、context folding 定位、4 環境消融 |
| arXiv 2512.24601 | RLM 正式定義、median 提升數據 |
| arXiv 2605.09998 | Continual Harness 定位、reset-free 自改進 harness |
| repo metadata（gh） | 16,145 stars、1,733 forks、MIT、TypeScript、created 2026-05-08、updated 2026-08-15 |
