# 203_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認標的為 **opencode 的 LSP 整合**（對照組：Claude Code），三個子題：① LSP server 管理 ② 對 agent 補全／診斷的實際幫助 ③ 與 Claude Code 對比。本 sub-step C1 的任務是：取得 opencode repo metadata、擷取其官方 LSP 文件、並補查 Claude Code 的 LSP 支援，為後續分析收集原始資料。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view anomalyco/opencode` | 取得 repo metadata | star/fork/license/預設分支/更新時間 | 195,195 stars、MIT、預設分支 `dev`、description「The open source coding agent」、更新 2026-08-09 |
| `webfetch opencode.ai/docs/lsp/` | 擷取 opencode LSP 官方文件 | 理解 LSP server 管理機制 | ✅ 完整取得（見下方整理） |
| `webfetch opencode.ai/docs/config/` | 確認 `lsp` 設定在 config schema 中的位置 | 補足 LSP 設定上下文 | ✅ `lsp` 為獨立頂層 key；省略＝關閉、`true`＝開全部內建、物件＝override/自訂 |
| `webfetch code.claude.com/docs/llms.txt` | 取得 Claude Code 文件索引 | 確認是否有專屬 LSP 頁 | ✅ 索引中**無任何 LSP 專頁** |
| `webfetch code.claude.com/docs/en/vs-code.md` | 查 Claude Code 如何取得 diagnostics | 理解對照組的 LSP 支援 | ✅ 找到關鍵機制：VS Code extension 的內建 MCP server 提供 `mcp__ide__getDiagnostics` tool（讀 VS Code Problems panel 的 language-server diagnostics） |
| grep Claude Code settings 全文 | 確認 CLI 端是否有 LSP server 管理 | 判斷 Claude Code 是否原生 spawn LSP | ✅ 僅一處提及（pluginConfigs 注入 LSP config），無 CLI 原生 LSP server 管理 |

**opencode LSP 機制整理（來自 docs/lsp）：**

1. **管理**：`lsp` 預設關閉。`lsp:true` 啟用全部內建、`lsp:{}` 保留內建＋可 override/自訂、`lsp:false` 關閉。每個 server entry 支援 `command`／`extensions`／`env`／`initialization`／`disabled`。
2. **內建 30+ server**：astro、bash、clangd、csharp、clojure-lsp、dart、deno、elixir-ls、eslint、fsharp、gleam、gopls、hls、jdtls、julials、kotlin-ls、lua-ls、nixd、ocaml-lsp、oxlint、php intelephense、prisma、pyright、razor、ruby-lsp、rust、sourcekit-lsp、svelte、terraform、tinymist、typescript、vue、yaml-ls、zls。部分自動安裝（astro、bash、clangd、kotlin-ls、lua-ls、php、svelte、terraform、tinymist、vue、yaml-ls）；其餘需環境既有命令（gopls、rust-analyzer、pyright 等）。
3. **啟動機制**：啟用後開啟檔案時比對副檔名 → 啟動對應 server（尚未執行者）。
4. **目的**：以 diagnostics 作為 agent 的 feedback；開啟檔案時取得語言 server 診斷。
5. **官方注意**：LSP 非永遠淨正面——server 可能失同步、佔記憶體、因版本/專案而異、拖慢工作流。文件建議多數專案改用 agent 直接跑 lint/typecheck CLI，把錯誤餵回 agent loop，並把命令寫進 AGENTS.md/skills。
6. **額外**：`OPENCODE_DISABLE_LSP_DOWNLOAD=true` 可停用自動下載 server。

**Claude Code 對照組整理：**

- 官方文件**無 LSP 專頁**；CLI 本身**不原生 spawn 或管理 LSP server**。
- LSP 診斷的取得路徑是 **IDE 整合**：VS Code extension 啟動時跑一個內建 MCP server（名 `ide`），暴露給模型的唯二 tool 之一為 `mcp__ide__getDiagnostics`——直接讀 VS Code Problems panel 的 language-server diagnostics（可限定單檔）。Jupyter 的 `mcp__ide__executeCode` 為另一 tool。
- 即：Claude Code 把 LSP server 的管理與運行**外包給宿主 IDE**（VS Code/JetBrains），自身不負責 spawn server，僅透過 IDE MCP 拉取已產生的 diagnostics。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| opencode metadata | gh repo view | 完整。195k stars、MIT、dev 分支 |
| opencode LSP server 管理 | docs/lsp + docs/config 交叉 | 完整。30+ 內建、4 種設定型態、自動安裝機制 |
| LSP 對 agent 的幫助 | docs/lsp 的 How It Works/Best Practices | 完整。以 diagnostics 作 feedback；官方明示其取捨 |
| Claude Code LSP 對照 | llms.txt 索引 + vs-code.md + settings | 完整。CLI 無原生 LSP，走 IDE MCP `getDiagnostics` |
| 是否需 CDP | 檢查反爬 | 未觸發，webfetch 全程可用 |

**關鍵對比已成形：** opencode＝**原生**（自帶 30+ server 清單、可自動安裝、直接 spawn、診斷進 agent loop）；Claude Code CLI＝**委外**（不 spawn server，靠 VS Code/JetBrains 宿主 IDE 的 LSP，透過內建 `ide` MCP 的 `getDiagnostics` 拉診斷）。此對比足以支撐子題③。

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| Claude Code 對照資料來源 | (a) 假設其有 LSP 專頁並 fetch (b) 先看文件索引再定位 | (b) | llms.txt 直接顯示無 LSP 專頁，避免浪費 fetch；改從 vs-code.md 找到 `getDiagnostics` 這條真實機制 |
| 是否深挖 opencode 原始碼 LSP 實作 | (a) 只讀官方文件 (b) 讀 packages 原始碼 | (a) | 官方文件已涵蓋「管理／啟動／設定／取捨」，足以支撐三子題；原始碼細節屬 C2+ 之需，非 C1 範圍 |
| 補查方向 | (a) 只查 opencode (b) opencode＋Claude Code 平行查 | (b) | 子題③明確要求對比，需同時取得兩邊原始資料 |
