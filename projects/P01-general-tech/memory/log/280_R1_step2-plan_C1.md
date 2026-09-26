# 280_R1_step2-plan_C1.md

## 狀況理解

C1 為 Step 2 第一個 sub-step，對 `dream-num/univer` 執行「標準調研動作」前段：取得 repo metadata、擷取 README 與關鍵子文件、補查背景脈絡。Step 1 已確認：第二大腦無 Univer 主題，僅有方向不同的相鄰判定 OfficeCLI（agent 操作成品檔）。故 C1 重點在建立可支撐報告 §1～§4 的一手事實，並**優先核對影片的授權注意點**（OSS Apache-2.0 vs Pro 協作／轉換）。擷取範圍：metadata、README（英）、docs/ 架構文件、官網 capability 矩陣、AI SDK 文件、npm 使用量、前身 Luckysheet。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` + REST `/repos` | 取得基礎 metadata | 定位 repo 屬性 | `dream-num/univer`；**18,822 stars／1,609 forks／146 open issues／267 watchers**；Apache-2.0；TypeScript（56.8M LOC 中 56.8M）;default branch `dev`;created 2022-09-29;pushed 2026-09-24;latest release **v1.0.2（2026-09-24）**;未封存;homepage docs.univer.ai;topics 含 excel/spreadsheet/doc/ppt/pdf/collaboration/sdk |
| 讀 release list | 判斷成熟度節奏 | 確認版本現況 | v1.0.0、v1.0.1、v1.0.2 **全在 2026-09-24 同日發布**;前版 v0.25.2（2026-09-17）。正式 1.0 為調研前一天才切 |
| 列 repo 根目錄＋結構 | 了解專案佈局 | 找出關鍵子文件 | `packages/`（60+）、`presets/`（18 preset）、`examples/`、`common/`、`tests/`、`docs/`、`DREAMNUM.md`、`CHANGELOG.md`、turbo/vitest workspace |
| 讀 README.md（英） | 掌握定位與功能邊界 | 取得官方問題陳述 | 自稱「**The Office Harness for AI Agents**」;開源嵌入式 Office SDK;六工具：Spreadsheets/Docs/Slides/Canvas/Bases/Relational Tables／PDF（coming soon）;強調 isomorphic（browser＋Node.js 同架構）、plugin-first、Canvas 渲染、公式引擎、統一 Facade API |
| 讀 README 的 **Open Source and Pro** 表 | 核對影片授權注意點 | 逐項確認 OSS/Pro 分界 | **確認**：OSS＝Apache-2.0 核心＋編輯/公式/篩選排序/驗證/註解/繪圖/尋找取代;**Pro＝即時協作、編輯歷史、import/export、列印、圖表、PivotTable、Sparkline、形狀、資料連接器、server-side calculation**;Docs/Slides/Bases/Server 同樣切分 |
| 讀 docs/API_STABILITY.md | 了解 API 承諾 | 判斷導入風險 | 分 Stable/Experimental/Internal/Deprecated;**內文寫「Univer is currently pre-1.0」卻已有 v1.0.2**，兩處不一致（疑文件未同步） |
| 讀 docs/ISOMORPHIC.md | 理解同構架構 | 支撐 §3 機制 | 要求邏輯與 UI 拆成兩個 plugin（如 sheets-filter／sheets-filter-ui）;Facade API 需 server/client 共用;MUTATION command 不得讀 UI 狀態 |
| 列 `packages/` | 驗證插件體系 | 量化模組拆分 | 含 core、engine-formula、engine-render、docs/docs-ui、sheets/sheets-ui/sheets-formula/sheets-numfmt/sheets-filter/sheets-table、slides/slides-ui、ui、ui-adapter-vue3、ui-adapter-web-component、network、rpc/rpc-node、data-validation、conditional-formatting、thread-comment、watermark 等 |
| 讀 docs/tldr 目錄 | 找架構 TLDR | 取得引擎設計 | formula-engine-architecture、web-worker-architecture、permission、selection-architecture、object-architecture（*.tldr 為 tldraw JSON，內容以圖形節點記錄 FormulaEngine 管線） |
| `webfetch` univer.ai 官網 | 取行銷面宣稱 | 對照 README | 宣稱 10M cell 渲染、500+ 函式、31 圖表、180+ 形狀、Rust 公式 runtime、19 語言、**SpreadsheetBench #1 68.86%（低於 Human 71.3%）**、200 concurrent editors（spreadsheet-specific OT）;「30k+ stars（含 Luckysheet）」 |
| `webfetch` univer.ai/capabilities | 取完整能力矩陣 | 區分工具成熟度 | 六工具能力齊列，惟多屬全產品家族宣稱，**README 明文 charts/pivot/import-export 為 Pro**，行銷頁未標示 Pro，二者需並列注意 |
| `webfetch` docs.univer.ai/ai | 取得 AI 整合機制 | 支撐「AI agent」賣點 | AI SDK＝Node.js CLI 入口;流程：load/edit Unit→import/export→visual inspection（Screenshot＋Layout Lint）→**Worktree（agent 隔離草稿＋人類 review、Merge/Reopen）**→Runtime reuse/Daemon |
| `webfetch` docs/guides/pro、/guides/skills | 取 Pro 明細 | 驗證連結 | **皆 404**（README 連結失效，路徑疑已更動）;無法取得 Pro 定價 |
| `gh repo view` Luckysheet | 確認歷史淵源 | 補背景 | `dream-num/Luckysheet` **已封存**（archived）、16,641 stars、MIT、desc「Luckysheet upgraded to Univer」;佐證官網「30k+（含 Luckysheet）」為家族加總 |
| `gh repo view` univer-sdk-skills／univer-cli | 確認 AI 生態 | 補 §3／§4 | sdk-skills：Apache-2.0，agent 用整合指引;univer-cli：Apache-2.0，agent 本地 CLI 工作區;另有 univer-workspace、dsh-univer-office、univer-mcp |
| `npm downloads` @univerjs/core、sheets | 量化採用度 | 客觀佐證 | 近月 core ≈ **1,621,054**、sheets ≈ **1,508,516** 次下載 |
| 讀 CHANGELOG／DREAMNUM.md | 取得維護與邊界 | 補責任範圍 | CHANGELOG 記錄 1.0.0-beta 系列;DREAMNUM.md 自述 repo 擁有 OSS runtime、plugin、引擎、presets，**明言不擁有 Pro 的協作/轉換/server 能力**;依賴 univer-icons、verso |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 技術標的 | metadata | Univer，18.8k stars，Apache-2.0，TypeScript，2026-09-24 剛發 v1.0.2 |
| 定位 | README＋官網 | 嵌入式開源 Office SDK，2026 重新定位為「AI Agents 的 Office Harness」，六工具一 runtime |
| 架構機制 | README＋ISOMORPHIC＋packages | plugin-first（60+ 套件）＋Canvas 渲染＋公式引擎＋依賴注入 command/mutation/service＋統一 Facade API＋browser/Node 同構 |
| AI 整合 | docs/ai | Node CLI entrance＋inspection（截圖/layout lint）＋Worktree 隔離草稿＋人工 review；生態含 sdk-skills/CLI/MCP |
| **授權邊界（影片注意點）** | README OSS vs Pro 表＋DREAMNUM.md | **已確認**：協作、import/export（轉換）、列印、圖表、pivot、server-side 計算為 Pro 商業層;OSS 核心 Apache-2.0。行銷頁未標 Pro，須並列提醒 |
| 成熟度落差 | release＋API_STABILITY | 1.0 僅發布一天;API_STABILITY 仍自稱 pre-1.0，文件與版本不一致;Pro 文件連結 404 |
| 社群／採用 | npm＋Luckysheet | npm 月下載各約 150 萬;前身 Luckysheet 已封存（16.6k stars）併入 Univer |
| 未取得項 | — | Pro 定價與授權條款細節（文件 404）;Slides 實際成熟度（README 標 under active development） |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 授權查證來源 | 只信行銷頁／以 README＋DREAMNUM 為準 | 以 README Open Source and Pro 表＋DREAMNUM 為準 | 該表逐工具逐能力明確標示 OSS/Pro 分界，且是 repo 內一手文件;行銷頁未標 Pro，不足以判定 |
| 官方部落格宣稱 vs repo | 全採信／全丟棄 | 採信但標註分歧 | 官網宣稱多屬「全產品家族」，repo 為此 repo 範圍;二者差異本身即報告選型風險的證據 |
| 架構文件取捨 | 逐一讀 60+ 套件／讀頂層文件 | 讀 README＋ISOMORPHIC＋API_STABILITY＋packages 列表 | C1 需先建立全貌，套件細節留待 C2 對照替代方案時再細化 |
| AI 賣點驗證 | 只引官網口號／讀 docs/ai 機制 | 讀 docs/ai 機制 | 「與 AI agent 結合」是影片與標題核心，須落到實作（CLI/inspection/Worktree）才算驗證 |
| 前身關聯處理 | 忽略 Luckysheet／補查 | 補查 | 官網「30k+ 含 Luckysheet」易誤導；查證可釐清 star 數字組成與產品血緣 |
| Pro 文件 404 的處理 | 以推測補定價／如實記錄未取得 | 如實記錄未取得 | 不臆造 Pro 授權條款;列入 C2 待補或報告據實標示 |
