# 234_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認調研標的為 **diagram-design**（cathrynlavery/diagram-design）——「給 AI Agent 使用的出版級圖表設計 Skill」。使用者僅給 repo 名稱與一句定位，無附帶條件。本 sub-step C1 依 document skill 標準動作執行：取得 repo metadata → 擷取主要文件（README、SKILL.md、ADR）→ 補查背景脈絡。C1 目標：掌握此 Skill 的技術本質（27 種視覺型、semantic pattern、品牌 onboarding、draw.io/Mermaid 匯入、靜態 HTML 輸出），供 C2 收斂成報告並補查替代方案。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 do/skills/document/SKILL.md | 確認標準調研流程 | 依規範執行 | 確認：metadata → 主要文件 → 背景脈絡；repo 標的用 gh api / gh repo view |
| `gh repo view cathrynlavery/diagram-design --json ...` | 取得 repo metadata | 掌握 stars、license、更新時間、語言 | 取得：18,112 stars、MIT、default branch=main、primaryLanguage=HTML、created 2026-04-16、updated 2026-08-15、description「29 editorial diagram types for Claude Code. Self-contained HTML + SVG. No shadows, no Mermaid-slop.」 |
| `gh api .../contents/` 列根目錄 | 掌握 repo 結構 | 定位關鍵子文件 | 取得：skills/、docs/、commands/、prompts/、scripts/、.claude-plugin/、.codex-plugin/、.agents/ 等 |
| 抓取 README.md（raw） | 取得主要文件全文 | 掌握定位、安裝、onboarding、匯入、架構 | 取得全文：Why I built it、27 種視覺型、安裝（Claude Code/Codex/Pi）、品牌 onboarding 流程、draw.io/Mermaid 匯入四 dials、SVG/PNG 匯出、progressive disclosure 架構、設計系統、primitives、when-not-to-use |
| 抓取 skills/diagram-design/SKILL.md | 取得核心 skill 規格 | 掌握哲學、選型、anti-patterns、設計系統 | 取得：哲學「最高品質的動作通常是刪除」、target density 4/10、semantic pattern→type 路由表、27 型選型表、universal anti-patterns（AI slop 清單）、style-guide gate、確認後才繪製 |
| 抓取 docs/adr/ 清單與 ADR 0001 | 取得設計決策脈絡 | 掌握「靜態預設」等關鍵決策 | 取得 6 個 ADR；ADR 0001 說明「靜態無 script 為預設、motion 僅允許單一 pinned controller 且 byte-match 驗證」的資安與 review 考量 |

**關鍵技術事實（供 C2 收斂）：**
- **定位**：給 Claude Code / Codex / Pi 的 Agent Skill，產出「editorial 品質」的圖表，自含 HTML+SVG，無 build step、無 JS、無外部圖片依賴。
- **作者動機**：Cathryn Lavery（BestSelf.co 創辦人、littlemight.com 作者）——每次要圖表，Claude 回傳「generic rounded-box」與網站風格不符，與 Figma 搏鬥 30 分鐘或乾脆跳過，故自建 skill。
- **27 種視覺型**：architecture、flowchart、sequence、state、ER、timeline、swimlane、quadrant、radar、loop、nested、tree、org-chart、layers、venn、pyramid、bar、line、gantt、scatter、process、medallion、data-flow、DP integration、DP security matrix、IT current-state、high-level。每型 3 種靜態變體（minimal light / minimal dark / full-editorial）。
- **semantic pattern 路由**：行為語意（fan-in queue、policy trace、trust boundary 等 7 種）先選 pattern 再選最近視覺型，不擴充型別數量。
- **品牌 onboarding**：60 秒從網站抓 dominant palette + font stack，映射到 paper/ink/muted/accent/link 語意 token，寫入 style-guide.md；自動做 WCAG AA 對比檢查；first-run gate 強制客製化。
- **匯入**：可 redraw draw.io（.drawio/.drawio.xml/.drawio.png/.drawio.svg）與 Mermaid（.mmd/.fenced block），四 dials＝format×size×detail×audience，輸出附 fidelity ledger。
- **設計系統**：1 accent、1–2 focal elements、3 字型（Instrument Serif/Geist sans/Geist Mono）、1px hairline、無 shadow、max radius 10px、所有座標/寬/間距可被 4 整除（避免 AI 感）。
- **靜態預設**：motion 為選配（none/reveal/step/loop），預設 none；motion 僅允許單一 pinned controller 且 SHA-256/字串雙重驗證（ADR 0001）。
- **a11y**：每 SVG 有 role="img"、aria-labelledby、title/desc；prefers-reduced-motion 顯示完整靜態幀。
- **CI 驗證**：lint-skin、verify-geometry、verify-motion、verify-drawio-import、verify-mermaid-import、verify-docs-sync 等多重 gate。
- **metadata 版本**：SKILL.md metadata version 2.4；README 提到 2.0 Loop、2.3 semantic patterns + accessible motion。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata | gh repo view | 取得 stars/license/branch/language/時間，確認活躍（updated 2026-08-15） |
| 主要文件 | README + SKILL.md 全文 | 取得完整定位、機制、架構、設計系統 |
| 設計決策脈絡 | docs/adr/ | 取得 6 個 ADR，讀 ADR 0001 理解靜態預設動機 |
| 資訊缺口 | 對照 AGENTS.md 5 點 | 需 C2 補查：①「出版級」的圖表設計方法論背景（data-ink ratio、視覺編碼）②替代方案（Mermaid、draw.io、Excalidraw、wiretext、mermaid-cli、D2、Graphviz 等）③與 MyBrain 已判項目（OpenDesign、DESIGN.md、HyperFrames、Hallmark）的對照 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| metadata 取得方式 | (A) gh repo view (B) 僅 webfetch | A | repo 標的，gh 提供結構化 metadata（stars/license/語言/時間） |
| 主要文件範圍 | (A) 僅 README (B) README＋SKILL.md＋ADR | B | SKILL.md 是核心規格（哲學/選型/anti-patterns），ADR 補設計決策脈絡；README 已含架構樹 |
| 是否讀全部 27 個 type-*.md | (A) 全讀 (B) 只讀 SKILL.md 選型表 | B | SKILL.md 已含完整 27 型選型表與 anti-patterns；逐型細節對 C2 收斂報告非必要，避免過度調研 |
| 背景脈絡來源 | (A) 僅 repo 自述 (B) 補查圖表方法論與替代方案 | B | AGENTS.md 要求「出版級」「AI Agent Skill」需背景與對照；C2 網路補查 |
| 下一步 C2 方向 | (A) 直接撰寫報告 (B) 補查替代方案（Mermaid/draw.io/Excalidraw/wiretext/D2/Graphviz）＋圖表設計方法論＋MyBrain 已判項目對照 | B | 使用者標的為「Skill」，替代方案比較是 AGENTS.md 第 4 點核心；MyBrain 已判項目（OpenDesign 等）可作對照素材 |
