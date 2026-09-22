# i-have-adhd — 讓 AI 編程助手輸出更直接的 system-prompt skill

> 調研標的：https://github.com/ayghri/i-have-adhd
> 本報告依 know/AGENTS.md「分析報告格式」撰寫，只回答 5 個問題。
> 對照基準：使用者第二大腦（FATESAIKOU/MyBrain）已判「試用」的同類 **Caveman**。

---

## 1. 這個技術解決什麼問題？

**被解決的具體問題**：AI coding agent 的回覆「廢話太多、先繞圈子、不直接給動作」。常見症狀是把回答埋在冗長前言、過度修飾、反覆重述裡，使用者必須往下滑才知道「到底要做什麼、第一步做什麼、多久做完」。

repo 自身描述為 **「stop your coding agent from burying the answer」**（別讓你的 coding agent 把答案埋起來）。

`i-have-adhd` 以一套 system-prompt 規則（10 條）約束 agent 的輸出格式：**先給動作 → 編號步驟 → 具體時限 → 去掉問候與填充**。效果可從 repo 的 Before/After 對照看出：

| 維度 | Before（未套用） | After（套用） |
|---|---|---|
| 開頭 | 鋪陳式前言（"Sure, let me explain…"） | 直接給動作指令 |
| 步驟 | 條列但無明確順序 | 編號步驟 |
| 時限 | 無 | 每步給具體時間（如 5 min） |
| 修飾 | 問候、緩衝語、反覆 | 全數移除 |

> **模糊之處**：問題描述（「輸出更直接」）本身是**程度性**的，repo 沒有定義「直接」的客觀邊界，而是用 10 條規則近似。因此這是一套**風格約束**，不是可量化的正確性改進——其效果只能透過人工盲評近似評估（見 §3 的 evals）。

---

## 2. 這個問題為什麼會發生？（背景）

分兩層：**repo 內文明確提到的（ADHD 認知理由）** 與 **通用技術背景（未在 repo 內文、由本報告補充）**。

### 2.1 文章中明確提到：ADHD 認知特徵的動機

SKILL.md 內文自述其規則源自《The Adult ADHD Tool Kit》，並列了 5 個 ADHD 閱讀/執行事實作為設計理由：

| ADHD 事實（內文列舉） | 對輸出風格的推論 |
|---|---|
| working memory 有限 | 冗長前言與分點會耗盡短時記憶，直接給動作才讀得動 |
| starting friction 高 | 沒有「第一步做什麼」時無法啟動，故要編號步驟 |
| dopamine 需求 | 過長的鋪陳推遲「得到答案」的獎勵，要快速給結論 |
| 分心風險 | 修飾語、題外話會引開注意力，要全數去除 |
| 時限模糊導致拖延 | 沒有明確時間框時容易無限擱置，故每步給時限 |

> 這是 repo 作者把**自己（或目標使用者）的 ADHD 認知特性**轉譯成 prompt 規則的證據。**此為內文證據，非本報告臆測。**

### 2.2 通用技術背景（本報告補充，repo 內文未寫）

根本原因是 **LLM 的統計預設（statistical default）**：以 next-token 預測訓練的模型，其輸出分布偏向「禮貌、完整、四平八穩」的通用 prose，因為訓練語料裡這樣寫的文本佔絕大多數。結果是：

- **冗長是預設**，直接是特例——不注入約束，agent 傾向給最「穩妥」的完整回答。
- **單一 system prompt 只作用一次**，agent 在長會話中會漂移回統計預設，需要持續注入或觸發提醒（見 §3 的 persistence 機制）。
- **跨 runtime 不一致**——不同 coding agent（Claude Code、Codex、Cursor…）對 prompt 的載入點與權重不同，同一套規則要各自 adapter 才有一致效果（見 §3 的 AGENTS.md 架構）。

> **區分**：ADHD 動機是 repo 作者給「為什麼值得這樣做」的敘事；通用背景是「為什麼不這樣做就必然冗長」的機制。前者是選擇理由，後者是成因。

---

## 3. 這個技術是如何解決該問題的？

`i-have-adhd` 是 **system-prompt skill**（非 fine-tune、非模型修改），機制分三層：**規則內容、注入/持久化、跨平台擴散、實證評估**。

### 3.1 規則內容（SKILL.md 為真相來源）

`skills/i-have-adhd/SKILL.md` 是 **source of truth**，定義：

- **10 條規則**：先給動作、編號步驟、給時限、無問候、無填充、具體而非模糊、保留技術正確性、等。
- **「何時打破規則」**：當壓縮本身造成技術歧義、或涉及不可逆/安全操作時，恢復正常 prose。
- **pre-send check**：輸出前自我檢查是否符合規則。

frontmatter 標示 `disable-model-invocation: true`，需以 `/i-have-adhd` 觸發（隨選），觸發後在**會話內持續**至 `stop adhd mode`。

### 3.2 注入與持久化機制（以 OpenCode plugin 為例）

`.opencode/plugins/i-have-adhd.mjs` 提供兩種模式：

| 模式 | 觸發 | 機制 |
|---|---|---|
| **隨選（on-demand）** | 註冊 skills + `/i-have-adhd` command | 使用者敲 command 後注入規則 |
| **always-on** | `~/.config/opencode/.i-have-adhd-always` 檔案存在 | **每 turn** 把規則體附加到 system prompt |

注入時 **strip 掉 frontmatter** 只留規則體，避免模型被 YAML 干擾。

### 3.3 跨平台擴散（AGENTS.md 架構）

```
        skills/i-have-adhd/SKILL.md   ← 單一真相來源（source of truth）
                    │
        ┌───────────┼───────────┬──────────────┐
        ▼           ▼           ▼              ▼
   Claude/Codex  Cursor/Gemini  Qwen/Kimi    OpenCode  Pi/OMP
   (plugin.json) (plugin.json) (plugin.json)  (.mjs)   (extensions/)
                    │
        └──────────── mirror / adapter ─────────────┘
```

- 支援 10 個 runtime：Claude、Codex、Cursor、Gemini、Qwen、Kimi、OpenCode、Grok、Pi、OMP。
- 每個 runtime 有**獨立 entry point**，其餘平台檔是 SKILL.md 的 **mirror/adapter**，不各自維護一份規則。

### 3.4 實證評估（evals/RESULTS.md）

repo 附 **3-trial / 14-case 盲評**（blind evaluation）：

| 指標 | candidate（套用） | baseline（未套用） | Δ |
|---|---|---|---|
| 加權總分 | 4.473 | 4.045 | **+0.427** |
| Concision（簡潔度） | — | — | **+1.143** |
| Actionability（可執行性） | — | — | **+0.714** |

candidate 全面勝出，但 **release gate 仍 FAILED**（有 3 個 blocking findings；repo 規則寫死「有任何 blocker 即失敗」）。意即：**效果方向正確，但尚未到可發布的品質門檻。**

### 3.5 與第二大腦已判「試用」的 Caveman 對照

| 面向 | Caveman（已判「試用」） | i-have-adhd（本標的） |
|---|---|---|
| 解法本質 | system-prompt skill（壓縮輸出） | system-prompt skill（輸出直接化） |
| 認知理由化 | 無（純語言風格壓縮） | **有（ADHD 認知事實 + 工具書來源）** |
| 跨平台基建 | 有（30+ agent、curl 安裝） | **有（10 runtime、plugin/extension）** |
| 強度分級 | 六級（lite~wenyan-ultra） | 無分級，單一規則集 |
| 實證 | 無量化評估 | **有盲評 + release gate** |
| 觸發 | `/caveman [等級]` + hooks | `/i-have-adhd`（隨選 / always-on 兩模式） |

**差異結論**：i-have-adhd 與 Caveman 解同一個問題軸，但 i-have-adhd 多了「ADHD 認知理由化」與「盲評 + release gate」兩項 Caveman 沒有、也與使用者 workflow 判準相關的元件（見 §4 的 workflow 閘門）。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

先說明**查詢基準**：本節替代方案不照通則空列，而是先查使用者第二大腦（FATESAIKOU/MyBrain）對這些工具已下的判定，再給 DA 表。**信任層級與時間座標依 mybrain-read 規範標注。**

### 4.0 使用者對「本標的」的現況（第二大腦查證結果）

- **第二大腦沒有 i-have-adhd 的評估記錄**（grep `adhd/ayghri` 無命中）——本標的尚未被判定。
- 但同一問題軸（讓 coding agent 輸出更直接/更省 token）已有 **Caveman** 被判定 **「試用」**（`stable`、`human:fatesaikou`、2026-07-12）。Caveman 的判定理由是「可採用、成本低、反正先安裝看看」。
- 「下一步清單」第 69 行列了 **Caveman/context-mode/LeanCtx/Headroom 與 rtk 比較**——使用者已把五個 context 治理工具放進同一比較軸，`rtk` 是每天在用的對照組。i-have-adhd 屬同一問題軸。

> **與本報告結論的關聯**：i-have-adhd 對照 Caveman 是「同問題軸」；但 i-have-adhd 多了「ADHD 認知理由化 + evals」兩元件，這兩個元件**正好對應使用者技術取捨準則的兩個判準**（見 4.2）。

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **i-have-adhd**（本標的） | system-prompt skill；10 條規則直接化輸出 + ADHD 認知理由 | coding agent 支援 plugin/skill 注入（Claude/Codex/Cursor/OpenCode 等） | release gate 未過；單一規則集無分級，可能過度壓縮 | 輸出直接、可執行性與簡潔度提高（evals +0.427） |
| **Caveman**（使用者已判「試用」，`stable`/human/2026-07-12） | system-prompt skill；六級壓縮強度 + auto-clarity 例外 | 需 curl 安裝 + hooks；30+ agent 支援 | 純語言壓縮，無認知理由化；無實證評估 | 輸出極簡（69→19 tokens）；省 output token |
| **context-mode**（使用者已判「觀望」，`stable`/process/2026-06-13） | MCP server 中間層；工具輸出隔離 + FTS5 session 延續 | 需作為 MCP server 掛載 | 只處理**輸入 context 治理**，不處理輸出風格 | 降低工具輸出噪音，session 可延續 |
| **LeanCtx**（使用者已判「採用」，`stable`/human/2026-06-06） | Rust 單一二進位；MCP server + shell hook；壓縮/記憶/路由/治理四層 | 需二進位部署；MCP + zshenv hook | 偏重輸入/context 治理，非輸出風格 | 重複讀取 ~2000→~13 tokens；git status 800→120 |
| **Headroom**（使用者已判「採用」，`stable`/human/2026-06-06） | context window 內容感知壓縮；CacheAligner+ContentRouter+CCR | 需本地 process + MCP | 偏重輸入壓縮；CCR 可逆壓縮有取回成本 | 60–95% token 減省；可逆取回 |
| **rtk**（使用者已判「不採用」，`stable`/human/2026-05-31；每日使用對照組） | CLI 中間層過濾/轉換輸出給 AIAgent | 需自兜一套；業務導入需評估安全性 | 太貴；安全性考量 | 過濾無效 CLI 輸入，省 token |

### 4.2 各方案切入點差異

| 方案 | 切入點（解的是哪一層） |
|---|---|
| i-have-adhd / Caveman | **輸出端風格**——壓縮/直接化 agent「說」的方式 |
| context-mode / LeanCtx / Headroom | **輸入端 context 治理**——壓縮/過濾送進 LLM 的資料 |
| rtk | **輸入端 CLI 噪音**——過濾工具呼叫輸出 |

**本質差異**：前兩者改「agent 怎麼表達」，後三者改「LLM 收到什麼」。i-have-adhd 與 Caveman 是**輸出側**，其餘是**輸入側**——所以 i-have-adhd 與 Caveman 是同類，與 LeanCtx/Headroom/context-mode 屬**互補**而非競爭。

### 4.3 對照使用者技術取捨準則的立場

使用者「技術取捨準則」（骨幹、`draft`、claude-code/opus-5、2026-08-01）有兩個直接相關的判準：

1. **「MVP → Feature 唯一閘門 = 能否影響個人 workflow」**（`draft`）。Caveman 已被判「試用」且「反正先安裝」，i-have-adhd 若僅與 Caveman 同軸，判定會落在相同位置；但 i-have-adhd 的「ADHD 理由化 + evals」提供了**額外的可驗證元件**——這正對應使用者「要補驗證機制而非加審核關卡」的準則。
2. **「Reject ≠ 沒價值」**（`draft`）。rtk 被判「不採用」不代表該問題域無價值，使用者仍抽出「夾 CLI 中間層」的方向——同理，若 i-have-adhd 被判 Reject，其「輸出直接化規則」仍可被抽取。

> **衝突提示**：使用者「不追新」（技術取捨準則 §四：汰換看上游死沒死，不看有沒有更好的）。i-have-adhd 與已判「試用」的 Caveman **高度重疊**，若照「不追新」原則，i-have-adhd 不構成對 Caveman 的汰換理由；但 i-have-adhd 的 evals 元件是 Caveman 沒有、且 Caveman 判定時未考慮的——這使 i-have-adhd 有獨立評估價值，而不只是「另一個 Caveman」。此為本報告與「不追新」準則之間的**潛在張力點**，交使用者判斷。

> **信任層級註記**：技術取捨準則為 AI 草稿（`draft`、claude-code/opus-5），**尚未經使用者本人 review**，引用時僅作參考方向，非其定稿結論。

---

## 5. User Q&A

（本輪無使用者提問，無此章節）
