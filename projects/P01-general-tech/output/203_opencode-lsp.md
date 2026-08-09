# opencode 的 LSP（Language Server Protocol）整合

> 調研標的：opencode（anomalyco/opencode）的 LSP 整合能力，以 Claude Code 為對照組。
> 資料來源：opencode 官方文件（docs/lsp、docs/config）、Claude Code 官方文件（llms.txt、vs-code.md、settings）、opencode repo metadata。
> 調研日期：2026-08-09

---

## 1. 這個技術解決什麼問題？

**opencode 的 LSP 整合解決「coding agent 在編輯程式碼時，缺乏編譯器／語言工具鏈等級的即時診斷回饋」的問題。**

一個 CLI coding agent 在修改或補全程式碼時，主要靠兩種訊號判斷自己寫得對不對：

1. **執行程式後的結果**（編譯錯誤、測試失敗、runtime error）——但這要跑一輪才知道，且非所有問題都會在執行期顯現（型別不匹配、未使用變數、lint 錯誤）。
2. **程式碼本身的靜態訊號**——正是語言 server（LSP server）產生的東西：語法錯誤、型別錯誤、lint 警告、跳轉到定義、補全候選。

沒有 LSP，agent 只能靠「執行後錯誤」或「自己讀程式碼猜」，前者慢、後者靠模型幻覺。opencode 的 LSP 整合讓 agent 在**開啟檔案時**就拿到語言 server 的診斷（diagnostics），把「程式碼對不對」這件事的判斷交給確定性的語言工具鏈，而非純靠 LLM 猜。

**模糊之處（issue 描述本身含糊的部分）：**

- 「實際幫助」沒有量化定義——是改善補全品質、降低錯誤、還是加快除錯？官方文件只說「以 diagnostics 作為 feedback」，未給指標。
- 「支援哪些 LSP」依賴使用者環境：30+ 內建清單中，只有部分能自動下載安裝，其餘（gopls、rust-analyzer、pyright 等）需要環境裡**已經有**對應命令。也就是「開箱即用」的程度因語言而異。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的部分

opencode 官方文件（docs/lsp）直接承認 LSP「並非永遠淨正面」，並列出具體理由：

- **失同步**：LSP server 可能與實際檔案狀態不同步，給出過時診斷。
- **佔用記憶體**：每個啟用的語言 server 都是一個常駐背景程序。
- **因版本／專案而異**：同語言不同專案設定可能導致不同行為。
- **拖慢工作流**：spawn 與等待 server 有開銷。

因此官方建議：**多數專案改用 agent 直接跑 lint／typecheck CLI，把錯誤餵回 agent loop，並把命令寫進 AGENTS.md／skills**。

### 通用技術背景（文章中未寫，從 LSP 技術脈絡補上）

- LSP（Language Server Protocol）由 Microsoft 於 2016 年提出，設計初衷是**「編輯器與語言 server 解耦」**——一個 server 供所有編輯器（VS Code、JetBrains、Neovim、Emacs）共用，避免每個 IDE 各做一套語言支援。它是**給「IDE／編輯器」用的協定**，不是給「agent」設計的。
- coding agent（opencode、Claude Code 等）是後來才出現的使用者，他們要的是「把診斷送進 agent loop」，但 LSP 的互動模型（client 主動 request、server 被動回覆、server 常駐）是為「人用編輯器」設計的，並非為「agent 大量、快速、確定性地拉取訊號」設計。opencode 把這個「為編輯器而生的協定」接進 agent 的決定性診斷管線，屬於**把既有工具轉作他用**。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 opencode 的 LSP server 管理機制

`lsp` 是 opencode config 的獨立頂層 key，有四種設定型態：

```
lsp: true     # 啟用全部內建 server
lsp: false    # 關閉全部（預設）
lsp: {}       # 保留內建 + 可 override/自訂
lsp: { <server>: { ... } }   # 針對特定 server override 或新增
```

每個 server entry 支援的欄位：

| 欄位 | 作用 |
|---|---|
| `command` | 啟動該 server 的指令 |
| `extensions` | 對應的副檔名清單（決定何時啟動） |
| `env` | 注入的環境變數 |
| `initialization` | 初始化參數 |
| `disabled` | 是否停用 |

**內建 30+ server 清單**（依官方文件）：

- **可自動下載安裝**：astro、bash、clangd、kotlin-ls、lua-ls、php（intelephense）、svelte、terraform、tinymist、vue、yaml-ls
- **需環境既有命令**：gopls、rust（rust-analyzer）、pyright、csharp、clojure-lsp、dart、deno、elixir-ls、eslint、fsharp、gleam、hls、jdtls、julials、nixd、ocaml-lsp、oxlint、prisma、razor、ruby-lsp、sourcekit-lsp、typescript、zls

**啟動機制**：啟用後，開啟檔案時比對副檔名 → 若對應 server 尚未執行則啟動之 → 取得該語言 server 的診斷。

**補充控制項**：`OPENCODE_DISABLE_LSP_DOWNLOAD=true` 環境變數可停用自動下載 server。

### 3.2 LSP 對 agent 的實際幫助（依官方文件）

```
opencode LSP 的幫助路徑：

開啟檔案
   │  比對副檔名
   ▼
spawn 對應語言 server（若尚未執行）
   │
   ▼
取得 diagnostics（診斷：語法錯誤／型別錯誤／lint）
   │
   ▼
作為 agent 的 feedback 餵進 loop
```

即：LSP 提供的價值是「**確定性的診斷訊號**」——把「這行程式碼有沒有問題」從 LLM 的猜測，變成語言工具鏈的確定答案。這正是「verify 自己做得對不對」的機械可驗證部分。

### 3.3 與 Claude Code 的對比

| 面向 | opencode | Claude Code |
|---|---|---|
| 是否原生管理 LSP server | **是**。內建 30+ server 清單、可自動安裝、直接 spawn | **否**。CLI 不 spawn／不管理 LSP server |
| 官方是否有 LSP 專頁 | 有（docs/lsp） | **無**（llms.txt 索引中查無 LSP 專頁） |
| 診斷從哪來 | 自己 spawn 的 LSP server 產生的 diagnostics，進 agent loop | **委外給宿主 IDE**：透過 VS Code extension 內建 MCP server（名 `ide`）的 `mcp__ide__getDiagnostics` tool，讀 **VS Code Problems panel** 的 language-server diagnostics（可限定單檔） |
| server 的生命週期 | opencode 自己管理 spawn／常駐／停止 | 由宿主 IDE（VS Code／JetBrains）管理，opencode 側只是「拉」既有結果 |
| 設定方式 | config 的 `lsp` key（true／false／物件） | settings 僅一處提及（pluginConfigs 注入 LSP config），無 CLI 原生 server 管理 |

**一句話結論：**
> opencode＝**原生內建**（自帶 server 清單、可自動安裝、自己 spawn、診斷直接進 agent loop）；
> Claude Code CLI＝**委外**（不 spawn server，靠宿主 IDE 的 LSP，透過內建 `ide` MCP 的 `getDiagnostics` 拉診斷）。

---

## 4. 是否存在解決類似問題的其他技術／框架／思考方式？

「解決『agent 缺乏程式碼結構與診斷訊號』」這個問題域，第二大腦（FATESAIKOU/MyBrain）已有若干評估記錄。以下先列出**他實際判定過的**替代方案，再補通用方案。

### 4.1 第二大腦查到的判定（依相關性排序，附 URL 與信任層級）

| 技術 | 第二大腦判定 | 信任層級 | URL | 與本主題的關係 |
|---|---|---|---|---|
| **codebase-memory-mcp** | **Reject（skip）**。理由「問題域是重造輪子，技術複雜但效果難驗證」 | `human:fatesaikou`／`stable`，2026-06-27 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/codebase-memory-mcp.md | 用 tree-sitter＋LSP＋SQLite 建程式庫結構理解，與 LSP 同為「把程式庫結構訊號送進 agent loop」，屬最直接可比 |
| **CodeGraph** | **Accept（可嘗試）**。理由「比 GitNexus 全自幹更善用既有生態系、對開發流程侵入性更小」 | `human:fatesaikou`／`stable`，2026-05-31 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/CodeGraph.md | 程式碼知識圖譜，同為結構理解方案 |
| **Understand-Anything** | **Accept**。理由「用於讓人能 Review AI 產出」 | `human:fatesaikou`／`stable`，2026-05-31 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Understand-Anything.md | 多代理管線轉互動式知識圖譜 |
| **GitNexus** | **無結論**。「還沒試用過」，未判定 | `human:fatesaikou`／`stable`，2026-03-20 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/學習%20GitNexus.md | 靜態分析＋MCP 給 LLM，目的正是「提升 InputToken 效率、降低幻覺」 |
| **OpenCode（本標的）** | **採用**。理由「大致堪用，Ollama 整合帶來自由度、避免綁定」 | `human:fatesaikou`／`stable`，2026-05-01 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OpenCode.md | opencode 已採用，但**該筆判定不含 LSP** |
| **技術取捨準則（骨幹）** | ⚠️ AI draft（`claude-code/opus-5`／`draft`，未經他 review，2026-08-01） | AI draft | https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md | 關鍵準則：「理解優先」「Reject≠沒價值」「MVP 升 Feature 的唯一閘門＝能否影響個人 workflow」 |

**⚠️ 信任層級提醒**：`技術取捨準則` 整份是 `claude-code/opus-5` 產出的 AI 草稿、`status: draft`、**他尚未 review**，其內容（含 Reject 語意、MVP 閘門）應視為「未經本人拍板的草稿」，不是他已定稿的結論。其餘各筆判定（codebase-memory-mcp、CodeGraph、GitNexus、OpenCode）皆為 `human:fatesaikou` 本人寫、`stable`，可直接當作他的結論。

### 4.2 與我的結論衝突的地方（查詢最有價值處）

- **「Reject（重造輪子）的判準」與 opencode 的 LSP 本質是相容的，不衝突，反而相互支持。** codebase-memory-mcp 被 Reject 是因為「自己重造結構理解輪子、效果難驗證」。opencode 的 LSP 整合**不是重造輪子**——它直接呼叫現成的語言 server（gopls、rust-analyzer、pyright…），是**重用既有工具鏈**。這恰好符合他 Accept CodeGraph 的理由「善用既有生態系、降低侵入性」。因此 opencode LSP 不落入 codebase-memory-mcp 的 Reject 理由。
- **真正值得注意的衝突**：opencode 官方文件自己警告「LSP 非永遠淨正面」，建議「多數專案直接跑 lint／typecheck CLI 餵回 agent loop」。這與他「理解優先」＋「機械可驗證（verify）」的傾向一致——lint／typecheck CLI 是比 LSP diagnostics 更確定、更少常駐資源的驗證方式。**因此「啟用 opencode LSP」不必然優於「不啟用 LSP、改把 lint/typecheck 命令寫進 AGENTS.md」**——後者正是 opencode 官方對多數專案的建議，也符合他「約束放 harness」的準則。

### 4.3 DA 表（替代方案 vs opencode LSP）

| 技術 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **opencode LSP 整合**（本標的） | 內建 30+ server，依副檔名 spawn，診斷進 agent loop | 語言 server 可自動安裝或環境已有；config `lsp:true` | 常駐記憶體、可能失同步、因專案而異、拖慢工作流（官方自述） | agent 開啟檔案即獲確定性診斷，補全／除錯品質上升 |
| **lint／typecheck CLI 餵回 agent loop**（opencode 官方對多數專案的建議） | 把 `eslint`／`tsc`／`gopls check` 等命令寫進 AGENTS.md／skills，agent 跑完把錯誤餵回 loop | 專案有對應 lint／typecheck 命令；命令可重複執行 | 每次要跑一輪 CLI、較慢；只覆蓋命令覆蓋的檢查範圍 | 確定性驗證、無常駐 server 記憶體、可控、可寫死進 harness |
| **codebase-memory-mcp**（⚠️ 他已 Reject：skip） | tree-sitter＋LSP＋SQLite 預算呼叫鏈／介面歸屬，省 grep/read token | 工具成熟且效果可驗證（他判「難以驗證」） | 重造輪子、技術複雜、效果難量化驗證 | 減少反覆 grep/read 的 token 浪費 |
| **CodeGraph**（✅ 他 Accept） | 程式碼知識圖譜，善用既有生態系，供 agent／人查結構 | 既有生態系可組合；侵入性要低 | 需維護圖譜、可能 drift | 降低流程侵入性、快速掌握程式庫結構 |
| **Understand-Anything**（✅ 他 Accept） | 多代理管線把程式碼庫轉互動式知識圖譜 | 目標是「人 Review AI 產出」而非 agent 內部即時診斷 | 多代理管線成本、非即時 | 加速人理解陌生程式庫 |

### 4.4 各替代方案的切入點差異（簡述）

- **opencode LSP**：切入點是「**即時、逐檔、語言層**的診斷回饋」——在 agent 編輯當下給確定性訊號。
- **lint／typecheck CLI**：切入點是「**整專案、可重複、無常駐**的驗證」——把驗證寫死進 harness，符合「約束放 harness、機械可驗證」。
- **codebase-memory-mcp／CodeGraph／Understand-Anything**：切入點是「**跨檔結構**（呼叫鏈、介面歸屬、依賴）」——解決 LSP 逐檔診斷不觸及的「程式庫整體結構」層次。其中 codebase-memory-mcp 被他判 Reject（重造輪子、難驗證），CodeGraph／Understand-Anything 被 Accept。

---

## 附錄：主要資料來源

- opencode docs/lsp：https://opencode.ai/docs/lsp/
- opencode docs/config：https://opencode.ai/docs/config/
- opencode repo：https://github.com/anomalyco/opencode（195,195 stars、MIT、預設分支 dev、更新 2026-08-09）
- Claude Code llms.txt：https://code.claude.com/docs/llms.txt
- Claude Code vs-code.md：https://code.claude.com/docs/en/vs-code.md
