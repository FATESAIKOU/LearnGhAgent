# Caveman — AI Agent 輸出壓縮 Skill

> 調研標的：https://github.com/JuliusBrussee/caveman
> 88k stars / 5k forks / MIT License / 2026-04 建立

---

## 1. 這個技術解決什麼問題？

Caveman 解決的是 **AI coding agent 輸出過於冗長、消耗過多 output token 的問題**。

具體來說：
- AI agent（Claude Code、Codex、Gemini CLI、Cursor 等）在回答技術問題時，傾向於使用完整句子、禮貌用語、過渡句、解釋性填充（如 "Sure! I'd be happy to help you with that."、"The reason your React component is re-rendering is likely because..."）
- 這些填充內容對技術正確性沒有貢獻，但消耗 output token，直接轉化為 API 成本
- 在長 session 中，output token 累積量可達數萬至數十萬 token，對應顯著的 API 費用

Caveman 號稱減少 **65% output token**（基於 10 組 prompt 的 Claude API 實測，範圍 22–87%）。

**模糊之處**：README 的 65% 數字是 output token 節省率，不是總 token 節省率。Caveman 本身會增加 ~1–1.5k input token/turn（因 SKILL.md 規則注入），且不影響 reasoning token。因此 session 級總節省遠小於 65%，在短回覆場景甚至為 net-negative。此區別在 HONEST-NUMBERS.md 中有誠實說明，但 README 首屏未強調。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的原因

- **LLM 的預設輸出風格傾向於 verbose**：模型在沒有明確約束的情況下，傾向於生成完整、禮貌、帶過渡句的回覆。這是訓練資料中人類對話模式的反映。
- **2026 年 3 月 arXiv 論文 (2604.00025) 發現**：大型模型存在「自發性尺度相關冗長」（spontaneous scale-dependent verbosity），即參數越大的模型越容易過度解釋，反而在部分 benchmark 上表現更差。約束大型模型輸出簡短可提升準確率達 26 個百分點。

### 通用技術背景

- **Token 計價模型**：主流 LLM API（Anthropic、OpenAI、Google）按 token 計費，input 和 output token 價格不同（通常 output 比 input 貴 3–4 倍）。減少 output token 直接降低每次 API 呼叫的成本。
- **Agentic coding 的 token 消耗特徵**：在 agent 工作流中，input token（程式碼、上下文、文件）通常遠大於 output token。因此 output 節省的百分比在 session 總 token 中佔比較小。
- **System prompt 注入的成本**：任何 system-prompt skill 都會增加每輪的 input token 消耗。Caveman 的 SKILL.md 約 5 KB，加上 skill-list 條目，合計 ~1–1.5k input token/turn。這是一個固定開銷，在短 session 中可能抵消 output 節省。

---

## 3. 這個技術是如何解決該問題的？

Caveman 是一個 **system-prompt skill**（非 fine-tune、非模型修改），透過以下機制運作：

### 3.1 核心機制：system prompt 注入

安裝時將 `skills/caveman/SKILL.md` 注入 agent 的 system prompt。該 prompt 的核心指令：

```
Respond terse like smart caveman. All technical substance stay. Only fluff die.
```

具體規則：
- 刪除冠詞（a/an/the）、填充詞（just/really/basically/actually/simply）、禮貌用語（sure/certainly/of course/happy to）、模糊修飾（hedging）
- 使用片段句（fragments），非完整句子
- 使用短同義詞（big 而非 extensive, fix 而非 "implement a solution for"）
- 不敘述工具呼叫過程、不使用裝飾性表格/emoji、不傾倒原始錯誤日誌（除非被要求）
- 標準技術縮寫可用（DB/API/HTTP），但不可自創縮寫（cfg/impl/req/res/fn）— 因為 tokenizer 對這些縮寫的分詞與全詞相同，無 token 節省且降低可讀性
- 保留使用者語言：使用者寫葡萄牙文 → agent 以葡萄牙文 caveman 回覆，不強制英文
- 技術術語、程式碼區塊、錯誤訊息保持原樣

輸出模式範例：

```
[thing] [action] [reason]. [next step].
```

Before/After 對照：

| 正常 agent（69 tokens） | Caveman（19 tokens） |
|---|---|
| "The reason your React component is re-rendering is likely because you're creating a new object reference on each render cycle..." | "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`." |

### 3.2 六級強度

| 等級 | 行為 |
|---|---|
| **lite** | 無填充/模糊修飾。保留冠詞 + 完整句子。專業但緊湊 |
| **full**（預設） | 刪冠詞、片段句、短同義詞。經典 caveman |
| **ultra** | 刪連接詞（若因果關係仍明確）、一字夠用時用一字、每個事實只說一次 |
| **wenyan-lite** | 半文言文。刪填充但保留語法結構，古典語域 |
| **wenyan-full** | 全文言文。80–90% 字元減少。古典句式（動賓結構、主語省略、之/乃/為/其） |
| **wenyan-ultra** | 極致壓縮，保持文言感 |

### 3.3 Auto-Clarity 例外規則

在以下情境自動恢復正常 prose：
- 安全警告
- 不可逆操作確認
- 多步驟序列中片段順序或省略連接詞可能導致誤讀
- 壓縮本身造成技術歧義
- 使用者要求澄清或重複提問

恢復後自動回到 caveman 模式。

### 3.4 安裝與分發機制

- **單一安裝命令**：`curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash`
- 自動偵測機器上所有支援的 agent（30+），為每個 agent 執行對應的安裝路徑
- 支援 Claude Code（plugin + hooks）、Codex（plugin）、Gemini CLI（extension）、Cursor/Windsurf/Cline/Copilot（`npx skills add`）、opencode（native plugin）、OpenClaw（workspace skill）等
- 對 Claude Code 額外安裝 hooks（SessionStart 自動注入規則、UserPromptSubmit 追蹤模式切換、statusline badge）

### 3.5 Hook 系統（Claude Code 專用）

```
SessionStart hook ──寫入 "full"──▶ .caveman-active 旗標檔 ◀──寫入模式── UserPromptSubmit hook
                                            │
                                         讀取
                                            ▼
                                   statusline badge
                                   [CAVEMAN] / [CAVEMAN:ULTRA]
```

- `SessionStart hook`：session 啟動時寫入預設模式到旗標檔，並將規則集以 stdout 注入 system context
- `UserPromptSubmit hook`：解析 `/caveman` slash command 和自然語言觸發詞（"activate caveman"、"talk like caveman"），寫入對應模式到旗標檔；每輪輸出小量 reminder 防止其他 plugin 覆蓋
- 旗標檔寫入使用 `safeWriteFlag()`：symlink-safe、atomic temp + rename、`O_NOFOLLOW`，防止本地攻擊者利用可預測路徑做 symlink clobber

### 3.6 輔助命令

| 命令 | 功能 |
|---|---|
| `/caveman [lite\|full\|ultra\|wenyan]` | 設定壓縮等級 |
| `/caveman-commit` | Conventional Commit 訊息，≤50 字 subject |
| `/caveman-review` | 單行 PR comment：`L42: 🔴 bug: user null. Add guard.` |
| `/caveman-stats` | 顯示 session token 用量、終身節省、USD 估算 |
| `/caveman-compress <file>` | 將記憶檔案（如 CLAUDE.md）重寫為 caveman 風格，平均減少 ~46% input token |
| `caveman-shrink` | MCP middleware，壓縮 MCP server 的 tool descriptions |

### 3.7 隱私與安全

- 零 telemetry、零 analytics、零 accounts
- 安裝後零 network calls
- 安裝時僅從 GitHub/npm/agent registry 下載必要檔案
- 支援 air-gapped 環境（clone repo 後離線安裝）

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Caveman** | System-prompt skill 壓縮 output 風格，刪除填充詞、使用片段句 | Agent 支援 skill/plugin/hook 系統；Node ≥18 | 每輪 +~1–1.5k input token；短回覆場景 net-negative；wenyan 模式需使用者懂文言文 | Output token 減少 65%（平均）；session 總 token 節省 14–21%（output-heavy 場景） |
| **手動 system prompt 簡潔指令** | 在 system prompt 中寫 "Answer concisely." 或 "Be brief." | 任何可自訂 system prompt 的 agent | 無額外 input token 開銷；效果較弱（無結構化規則、無等級切換、無 auto-clarity） | Output token 減少 ~20–40%（推估，無公開 benchmark） |
| **Fine-tune 壓縮模型** | 對基礎模型進行 fine-tune，使其天生輸出簡短（如 cavegemma） | 需要 GPU 資源、訓練資料、模型部署基礎設施 | 模型行為固化後難以調整壓縮等級；需重新 fine-tune 才能改變風格；部署成本高 | 無 input token 開銷（無需 system prompt 注入）；output 壓縮效果取決於訓練資料品質 |
| **Token-level 後處理壓縮** | 在 agent 輸出後以演算法壓縮 token 序列（如 token 合併、摘要提取） | 需要能攔截 agent 輸出的 middleware 層 | 可能破壞程式碼語法或技術術語；需額外解壓縮步驟；即時性要求高 | 理論上可達最高壓縮率，但技術正確性風險大 |
| **Brevity Constraints（論文方法）** | 在 prompt 中加入明確長度限制（如 "Answer in ≤50 words"） | 任何 LLM API | 過於嚴格的長度限制可能導致資訊遺失；無等級切換；無 auto-clarity 保護 | 論文顯示可提升大型模型準確率 ~26 百分點，同時減少 token 消耗 |

### 切入點差異

- **Caveman vs 手動簡潔指令**：Caveman 提供結構化規則（6 級強度、auto-clarity、wenyan 模式）、slash command 切換、hook 自動注入、輔助工具（stats/compress/review/commit），是一個完整的產品化方案。手動簡潔指令是零成本的替代方案，但效果較弱且無生態系支援。
- **Caveman vs Fine-tune**：Caveman 是純 prompt 方案，無需訓練、部署成本為零、可隨時切換等級。Fine-tune 方案（如 cavegemma）無 input token 開銷，但靈活性低、維護成本高。兩者不互斥 — caveman 生態系同時提供 fine-tune 方案。
- **Caveman vs 後處理壓縮**：Caveman 在生成階段壓縮，不破壞程式碼結構。後處理壓縮在生成後進行，壓縮率可能更高但技術正確性風險大。
- **Caveman vs Brevity Constraints**：論文方法證明「簡潔約束」本身可提升準確率，Caveman 是此方法的具體產品化實作。Caveman 的 auto-clarity 機制解決了論文未處理的「何時不該簡潔」問題。

### 反證表：Caveman 的適用邊界

| 場景 | Caveman 效果 | 原因 |
|---|---|---|
| 長篇技術解釋（1k+ output token） | 顯著節省（50–87%） | 填充詞佔比高，壓縮空間大 |
| 短 Q&A（~150 output token） | 可能 net-negative | 節省 ~70–100 token，但每輪 +~1k input token |
| 按請求計費的 agent（Copilot 等） | 無節省 | 短回覆 = 同一個 request，價格不變 |
| 需要完整句子的場景（文件生成、API 文件） | 不適用 | Caveman 風格不符合文件規範 |
| 多輪長 session（output-heavy） | session 級節省 14–21% | Input token 佔比大，稀釋 output 節省率 |
| 安全敏感操作 | 自動恢復正常 prose | Auto-clarity 機制保護 |

---

## 5. User Q&A

*（無 — 首次產出，尚無使用者提問）*
