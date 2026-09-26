# Univer 技術分析報告

> 調研標的：https://github.com/dream-num/univer
> 官網／文件：https://univer.ai/ ｜ https://docs.univer.ai
> 來源：GitHub 一週熱點 132 期（https://youtu.be/q7HMQLM93qY）；issue #275，PR #280（R1）
> 對齊版本：v1.0.2（2026-09-24 發布）；metadata 取自 2026-09-24 pushed、18,824 stars、Apache-2.0、TypeScript
> 產出時間：2026-09-26

---

## 1. 這個技術解決什麼問題？

**Univer 解決的是「開發者要在自己的產品裡內建試算表／文件／簡報編輯能力，卻得從零處理公式引擎、Canvas 渲染、插件體系與權限」這個問題。**

它提供的不是一個可安裝的 Office 應用，而是一套**可嵌入的 Office SDK 與 runtime**：開發者在自己頁面掛載 Univer，用插件組合出所需的編輯表面，並在 Node.js 端以同一套架構跑無介面的內容處理。

| 被解決的具體痛點 | 說明 |
|---|---|
| 編輯器從零實作成本高 | 公式引擎、渲染、選取、剪貼、國際化、主題、權限皆需自建 |
| SaaS／內部工具需要「像 Excel 的元件」 | 既有 data grid 只能「顯示表格」，不含公式與文件語意 |
| 瀏覽器與伺服器邏輯割裂 | 前端編輯與後端批次處理常需兩套模型；Univer 以同構（isomorphic）架構統一 |
| AI agent 需要可程式化操作的 Office 內容 | 提供結構化 API、檢查機制與隔離草稿流程（此部分多落在 Pro／Web SDK） |

> **模糊之處**：官方標語為「The Office Harness for AI Agents」，但 repo 本體（OSS 核心）是**瀏覽器端可嵌入編輯 SDK**；「Agent harness」所需的協作、import/export、Worktree 等能力依 README 屬 **Univer Pro**。標語描述的是產品家族全貌，不是此 repo 的授權範圍，兩者需分開閱讀。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章中明確提到的背景（repo 一手文件）

| 背景 | 出處 |
|---|---|
| 開發者只想在自己的產品內嵌入編輯能力，不想被綁進一個 hosted app 或固定 UI | README「What is Univer?」 |
| 同一份內容要在瀏覽器與 Node.js 都能處理（伺服器端自動化） | README「Isomorphic by design」、`docs/ISOMORPHIC.md` |
| 功能需可按需組合、替換、延遲載入，而非一次吃下整套 | README「Plugin-first architecture」 |
| AI agent 與人要在同一份檔案上工作，且需要可驗證的產出 | README「Office Workflows for AI Agents」 |
| 前身 Luckysheet 已封存，能力整併進 Univer | `dream-num/Luckysheet`（archived，desc：「Luckysheet upgraded to Univer」） |

### 2.2 通用技術背景

| 背景 | 說明 |
|---|---|
| Web Office 的歷史門檻 | 瀏覽器端試算表需處理大數據量渲染、公式依賴圖、增量重算；Google Sheets／Excel Online 長期是封閉服務 |
| 渲染路線分歧 | DOM 表格在十萬格以上效能崩潰；Canvas 渲染是大型可編輯表面的主流取捨（Univer 採此路線） |
| OOXML 與檔案格式 | .xlsx/.docx/.pptx 為 ZIP＋XML（ECMA-376）；與其相容涉及 import/export，屬高成本模組（Univer 將此列 Pro） |
| Agent 時代的內容介面 | LLM 需要結構化 API 與視覺回饋才能可靠編輯版面；這是 Univer 2026 重新定位「AI Agent harness」的脈絡 |

> **區分**：2.1 為 repo 文件明示；2.2 為通用脈絡補充，非 Univer 獨有主張。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 總體架構

```
┌──────────────────────────────────────────────────────────┐
│  使用端                                                    │
│  Browser（React/Vue/Web Component）   Node.js（headless）  │
└───────────────┬───────────────────────────┬──────────────┘
                │  同一套 Facade API          │
┌───────────────▼───────────────────────────▼──────────────┐
│  @univerjs/presets（curated 組合）                         │
│  ────────────────────────────────────────────────         │
│  plugin 層（60+ 套件）                                     │
│   core ─ engine-formula ─ engine-render ─ ui              │
│   sheets / sheets-ui / sheets-formula / sheets-numfmt /   │
│   sheets-filter / sheets-table / data-validation /        │
│   conditional-formatting / thread-comment / docs /        │
│   docs-ui / slides / slides-ui / network / rpc-node ...    │
│  ────────────────────────────────────────────────         │
│  機制：command / mutation / service ＋ DI ＋ Facade API    │
└──────────────────────────────────────────────────────────┘
```

### 3.2 四項核心機制

| 機制 | 做法 | 支撐文件 |
|---|---|---|
| **Plugin-first** | 每個能力是一個插件；邏輯與 UI 分離（如 `sheets-filter`／`sheets-filter-ui`）。可組合、替換、lazy-load | `docs/ISOMORPHIC.md` |
| **Canvas 渲染引擎** | 以共享渲染層支撐大型可編輯表面，非 DOM 表格 | README「Canvas rendering engine」 |
| **公式引擎** | 獨立 engine-formula 套件，處理公式解析與計算 | README；`packages/engine-formula` |
| **同構 runtime** | 邏輯插件（models/commands/mutations/services）不讀 UI 狀態，可在 Node.js 執行；MUTATION command 不得依賴瀏覽器 | `docs/ISOMORPHIC.md` |

### 3.3 兩種導入模式

| 模式 | 做法 | 適用 |
|---|---|---|
| **Preset Mode** | `pnpm add @univerjs/presets @univerjs/preset-sheets-core`，`createUniver({ presets:[...] })` | 快速搭出可用的 Sheets／Docs／Node |
| **Plugin Mode** | 逐一 `pnpm add` 所需套件，手動 `registerPlugin`、載入 CSS 與 locale、掛 Facade | 需精細控制、縮小 bundle、深度整合 |
| **Headless Mode** | Node.js ≥18.17 無介面執行，用於伺服器端計算與自動化 | 後端批次處理、agent |

```ts
// Preset Mode 最小示例
import { UniverSheetsCorePreset } from '@univerjs/preset-sheets-core'
import { createUniver, LocaleType } from '@univerjs/presets'
import '@univerjs/preset-sheets-core/lib/index.css'

const { univerAPI } = createUniver({
  locale: LocaleType.EN_US,
  presets: [UniverSheetsCorePreset({ container: 'app' })],
})
univerAPI.createWorkbook({})
```

### 3.4 AI Agent 工作流（docs/ai）

```
load/edit Unit ──▶ Office file import/export ──▶ visual inspection ──▶ Worktree 隔離編輯＋人工 review ──▶ Runtime reuse / Daemon
   Facade 程式碼        Exchange (Pro)           Screenshot＋Layout Lint   agent 草稿 → 人決定 Merge/Reopen      池化／常駐
```

- **AI SDK** 是 TypeScript SDK，提供 Node.js CLI 入口，讓 agent 載入、理解、修改、檢查 Unit；CLI 命令名、身分授權、輸出、部署由業務應用自行擁有。
- **視覺檢查**：Screenshot（渲染截圖）＋ Layout Lint（結構化版面診斷），補結構化輸出無法描述版面之不足。
- **Worktree**：agent 在隔離草稿反覆編輯檢查，人於 Web review 後選 Merge 或 Reopen。

### 3.5 授權邊界（影片注意點，已核對）

以 repo 內一手文件（README「Open Source and Pro」表＋`DREAMNUM.md`）為準：

| 類別 | 開源（Apache-2.0，本 repo） | Univer Pro／商業 |
|---|---|---|
| 基礎 | Core SDK、插件系統、渲染引擎、公式引擎、Facade API、主題、i18n、框架轉接 | Pro presets、企業部署包 |
| Sheets | 試算表編輯、公式、數字格式、篩選排序、資料驗證、條件格式、註解、表格、尋找取代、繪圖 | **即時協作、編輯歷史、import/export、列印、圖表、樞紐分析、sparkline、外框、圖形、資料連接器、server-side 計算** |
| Docs | 文件模型與編輯 UI、清單、超連結、註解 | 協作、import/export、列印、進階表格、形狀 |
| Slides | OSS 簡報模型與 UI（**under active development**） | Pro 簡報模型、import/export、圖表／表格 |
| Bases | 可擴展插件架構 | Base 資料庫核心、workbench UI、field editor |
| Server／Runtime | Node.js headless runtime、RPC/Web Worker | 協作 server、collaboration client、SSR、server-side 計算 |

- 影片所述「部分協作與轉換能力需 Pro」**成立**：協作、import/export（轉換）、列印、圖表、pivot、server-side 計算皆非 OSS。
- **行銷頁未標 Pro**：`univer.ai/capabilities` 齊列六工具能力，未逐項標示 OSS/Pro；選型須以 README 表為準。
- 另註：`docs.univer.ai/guides/pro` 連結 **404**（README 連結失效），Pro 定價與條款本次未取得。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Univer**（本案） | 可嵌入 SDK：插件體系＋Canvas 渲染＋公式引擎＋同構 runtime ＋統一 Facade API | npm/pnpm 前端工程；Node ≥18.17（headless）；須自行組裝插件或 preset | 60+ 套件學習曲線高；**協作／import-export／列印／圖表／pivot 屬 Pro**（額外授權）；Slides 未成熟；API 穩定性文件自稱 pre-1.0 | 在自有產品內嵌試算表／文件編輯，瀏覽器與 Node 同構 |
| **ONLYOFFICE Docs / DocumentServer** | 自託管完整線上 Office 套件，以 iframe／embed 嵌入，內建 OOXML 原生編輯與即時協作 | 需自架 DocumentServer（Docker）；前端以 API 嵌入 | AGPL-3.0（衍生服務需開源或購商業授權）；iframe 整合、樣式與宿主頁隔離；客製深度受限 | 以最低開發成本嵌入完整 Office 編輯與協作 |
| **Handsontable** | JS data grid，外觀與操作近似試算表，支援 React/Angular/Vue | npm 安裝；授權為 dual（非商業免費、商業需購） | 只是 grid，非完整試算表：**無公式引擎、無文件語意**；授權需核對 | 在自家頁面高效顯示／編輯大型表格資料 |
| **Grist（grist-core）** | 關聯式試算表（relational spreadsheet），把表格當資料庫並附公式欄位 | 自託管（Docker）；Apache-2.0 核心 | 定位是資料庫型試算表，非通用 Office 編輯器；部分企業功能另授權 | 以試算表介面承載結構化資料與關聯 |
| **OfficeCLI** | 單一二進位 CLI，讓 agent 以命令操作既有 .docx/.xlsx/.pptx（讀寫改看＋HTML 預覽＋MCP） | 安裝單一 binary；不需 Office | 方向是「操作成品檔」而非「提供編輯能力」；無 GUI 編輯器 | AI agent 在終端／CI 程式化操作 Office 檔案 |

> 對照：**Google Sheets＋Apps Script**（hosted，含協作與公式，封閉、綁 Google 生態）為另一條「不自建」路線；**Luckysheet**（MIT，已 archived）是 Univer 前身，不再維護。

### 4.2 切入點差異

| 面向 | Univer | ONLYOFFICE | Handsontable | Grist | OfficeCLI |
|---|---|---|---|---|---|
| 產品形態 | 嵌入 SDK | 自架完整套件 | 前端元件 | 自架資料庫型表 | agent CLI |
| 是否有公式引擎 | ✓ | ✓ | ✗ | ✓（欄位公式） | ✓（讀寫既有公式） |
| 是否含 GUI 編輯 | ✓（自行組裝） | ✓（完整） | 編輯但不含文件 | ✓ | ✗（僅 CLI／HTML 預覽） |
| 協作 | Pro | 內建 | ✗ | 內建 | ✗ |
| OOXML import/export | Pro | 原生 | xlsx 讀寫（另購） | 匯入匯出（部分） | ✓ |
| 部署 | 嵌進自有 app | 自架 server | 嵌進自有 app | 自架 server | local binary |
| 授權 | Apache-2.0（核心）＋Pro | AGPL-3.0／商業 | dual（商業需購） | Apache-2.0（核心） | Apache-2.0 |

### 4.3 與第二大腦（FATESAIKOU/MyBrain）對照

> 查詢方式：`mybrain-read` skill，鏡像 `/tmp/mybrain` @ d2aeff7（2026-09-26 同步）。以下附 GitHub URL、信任層級與時間座標（首見＝日誌首次連結日）。

| 條目 | MyBrain 判定 | 信任層級 | 時間座標 | 與 Univer 的關係 |
|---|---|---|---|---|
| **Univer 本身** | **查無此主題** | — | — | 第二大腦無 Univer 任何評估；不得以通用知識冒充其舊結論 |
| [OfficeCLI](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OfficeCLI.md) | **試用** | `human:fatesaikou` / `stable`（**本人結論**） | 2026-07-12 | 最接近的相鄰判定。同為「AI agent × Office」，但**方向不同**：OfficeCLI＝操作成品檔（CLI），Univer＝提供編輯能力（嵌入式 SDK） |
| [嘗試使用 OfficeCLI](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/嘗試使用%20OfficeCLI.md) | 已落地使用（`officecli watch` 編輯 pptx，結論「完美」） | `human:fatesaikou` / `stable` | 2026-07-14 | 他**真正的 agent-office workflow 已由 OfficeCLI 覆蓋** |
| [Aionui](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Aionui.md) | **採用** | `human:fatesaikou` / `stable`（**本人結論**） | 2026-07-12 | 理由明寫「特別在意 OfficeCLI 連動與 MultiAgent」——辦公＋agent 整合軸的上位脈絡 |
| [技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md) | 理解優先；MVP→Feature 唯一閘門＝**能否影響個人 workflow**；**不用技術優劣評估工具** | `claude-code/opus-5` / `draft`（**AI 草稿，未經他 review**） | 首見 2026-08-01，更新 2026-09-13 | 評估 Univer 的主判準：是否有要嵌入編輯器的自有產品存在 |
| [判定總表](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md) | 117 筆：採用 17／試用 19／觀望 8／不採用 65／未判定 8 | `ollama-cloud/deepseek-v4-flash` / `draft`（**AI 草稿，未經他 review**） | 首見 2026-08-01，更新 2026-08-22 | 大型／包太多的方案多有「不採用」前例 |
| [munder-difflin](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/munder-difflin.md) | **不採用**：理由「**還太早而且包太多**」 | `process:learn-gh-agent` / `draft`（**自動流程產出，未經他 review**） | 2026-08-30 | 與 Univer 同屬「大而全平台」，為最接近的否決型前例 |
| [Gemini Spark](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Gemini%20Spark.md) | **不採用**：擴展性不足，不如自己兜 workflow（自建 MCP／自己買 LLM，Google 資源用 GAS） | `opencode/deepseek-v4-pro` / `draft`（**AI 草稿，未經他 review**） | 2026-08-02 | 顯示他對「整合型便利平台」的預設傾向是自兜 |
| [下一步清單](https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md) | **無 Univer 條目**，亦無以「嵌入式 Office SDK」為題的下一步 | `claude-code/opus-5` / `draft`（**AI 草稿，未經他 review**） | 首見 2026-08-09 | 目前不存在需要嵌入編輯器的自有產品 |
| [專案現況表](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/專案現況表.md) | 20 專案：日常在用 4／進行中 1／理解已達成 10／索引 5；**無編輯器 SDK 類專案** | `ollama-cloud/deepseek-v4-flash` / `draft`（**AI 草稿，未經他 review**） | 首見 2026-08-01 | 其「Office 內容產出」是 agent 產檔（pptx/xlsx 對人溝通），不是嵌入編輯 |

#### 明確指出的衝突

| # | 衝突點 | 說明 |
|---|---|---|
| C1 | **行銷定位 vs OSS 實質** | 影片與標語主打「The Office Harness for AI Agents」，但他已實際在用的 agent-office 路徑是 **OfficeCLI（CLI 操作成品檔，試用，human/stable）**；Univer OSS 核心是**瀏覽器端嵌入 SDK**，agent 相關的 Worktree／協作／import-export 反在 Pro。以此 repo 的 OSS 範圍，**並不直接服務他現有的 agent-office workflow**。 |
| C2 | **重型 vs 他的既有否決模式** | `munder-difflin`（不採用，理由「包太多」）、`Buzz`、`Semantica` 皆因「太重型」被拒。Univer 為 60+ 套件的完整框架，同屬重型候選；依 [技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md)（draft），**是否採用取決於有無要嵌入編輯器的自有產品**，而非技術優劣。第二大腦目前**無此類產品**。 |
| C3 | **判準層級** | 依技術取捨準則，**「會不會進日常 workflow」強於技術優劣**。Univer 需要一個宿主產品；`下一步清單`（draft）無此條目，故現階段不具備進入 Feature 的條件。 |

> **結論**：第二大腦無 Univer 判定；相鄰判定中，**OfficeCLI（試用／human stable）方向不同但已覆蓋其 agent-office 需求，Aionui（採用／human stable）** 為辦公＋agent 整合脈絡。若要採用 Univer，觸發條件是「出現需要嵌入編輯器的自有產品」，而非本輪調研的「agent 操作 Office 檔」。

---

## 附錄：專案 metadata

| 項目 | 值 |
|---|---|
| GitHub | https://github.com/dream-num/univer |
| Stars / Forks | 18,824 / 1,609 |
| 授權 | Apache-2.0（核心）；Pro 為商業層 |
| 主要語言 | TypeScript |
| 建立 | 2022-09-29；default branch `dev` |
| 最新版本 | v1.0.2（2026-09-24，v1.0.0/1/2 同日發布；前版 v0.25.2 為 2026-09-17） |
| npm 月下載 | `@univerjs/core` ≈ 1,621,054；`@univerjs/sheets` ≈ 1,508,516 |
| 前身 | Luckysheet（MIT，已封存，16,641 stars） |
| 生態 | univer-workspace、univer-cli、univer-sdk-skills、univer-mcp、dsh-univer-office |
| 未取得 | Pro 定價與授權條款（`guides/pro` 連結 404）；Slides 成熟度（README 標 under active development） |
