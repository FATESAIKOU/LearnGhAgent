# Univer 技術分析報告

> 調研標的：https://github.com/dream-num/univer
> 官網／文件：https://univer.ai/ ｜ https://docs.univer.ai
> 來源：GitHub 一週熱點 132 期（https://youtu.be/q7HMQLM93qY）；issue #275，PR #280（R1 初版、R2 追加 Q&A）
> 對齊版本：v1.0.2（2026-09-24 發布）；metadata 取自 2026-09-24 pushed、18,824 stars、Apache-2.0、TypeScript（R2 複查：18,993 stars／1,618 forks）
> 產出時間：2026-09-26（R2 更新）

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

### 4.4 R2 補充對照：第二大腦新增判定與衝突更新

> 查詢方式：`mybrain-read` skill，鏡像 `/tmp/mybrain` @ `530133b`（2026-09-26 同步）。R1 對照見 §4.3，本節只追加 R2 新讀到的檔案與衝突列。

| 條目 | MyBrain 判定 | 信任層級 | 時間座標 | 與 Univer 的關係 |
|---|---|---|---|---|
| [整備 claude web chat](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/整備%20claude%20web%20chat.md) | 實測：`officeCLI` 在 Claude web chat 環境「需要外裝工具的基本不能用」，內部自動改用 `pptxgenjs` | `human:fatesaikou` / `stable`（**本人紀錄**） | 2026-07-14 | **反面證據**：他對 CLI 型 office 工具有環境限制的實測，並非無條件偏好 |
| [AI 產出的人類 Review 策略](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/AI%20產出的人類%20Review%20策略.md) | 四層級 review 粒度：依「壞了的影響」決定 review 深度，並盡量把變更推向低影響層 | `ollama-cloud/deepseek-v4-flash` / `draft`（**AI 草稿，未經他 review**） | 2026-08-15 | 他明確認定人類仍需 review，且需要「能 verify」的機制；對應 Univer 的 Worktree／Viewer 人審段 |
| [DeepSeek Harness](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/DeepSeek%20Harness.md) | **觀望**（重型，機制可參考入口設計） | `process:learn-gh-agent` / `draft`（**自動流程產出，未經他 review**） | 2026-08-16 | Univer 是 DSH 的官方 Office 插件來源（`dsh-univer-office`），兩者在生態上相鄰 |
| [Buzz](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Buzz.md) | 規模過大難以採用；統一工作平台值得觀察 | `process:learn-gh-agent` / `draft`（**未經他 review**） | 2026-07-26 | 「大而全」前例 |
| [Semantica](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Semantica.md) | **Reject**：對個人過度重型 | `process:learn-gh-agent` / `draft`（**未經他 review**） | 2026-08-16 | 「重型＝不採用」前例 |
| [macro](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/macro.md) | **Reject**：太重型 | `process:learn-gh-agent` / `draft`（**未經他 review**） | 2026-08-16 | 同屬重型否決 |
| [判定總表](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md) | 117 筆：採用 17／試用 19／觀望 8／不採用 65／未判定 8 | `ollama-cloud/deepseek-v4-flash` / `draft`（**未經他 review**） | 2026-08-22 | 不採用佔比最高，重型方案多次落此區 |

#### 明確指出的衝突（R2 追加）

| # | 衝突點 | 說明 |
|---|---|---|
| C4 | **「更該用 OfficeCLI」與本人實測衝突** | Q3 的預設（OfficeCLI 更精確因而更該用）與 [整備 claude web chat](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/整備%20claude%20web%20chat.md)（human/stable）記載的「officeCLI 在 Claude web chat 基本不能用」相衝。精確性只在可操作的環境成立；跨宿主環境的可用性未定。 |
| C5 | **「人類只負責最終確認」與其 review 策略衝突** | Q3 假設人類只做形式確認，但他的 [AI 產出的人類 Review 策略](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/AI%20產出的人類%20Review%20策略.md)（draft）明定依影響分四層級、且要能 verify。純形式確認與此定見不符；人審需要「看得見、改得動、可回滾」的介面，而 Worktree 屬 Pro。 |
| C6 | **重型方案的否決前例** | Buzz、Semantica、macro、munder-difflin 皆因「太重型／規模過大／包太多」落於不採用或觀望。Univer 為 60+ 套件的完整框架，同屬重型候選；依技術取捨準則（draft），是否採用取決於有無宿主產品，而非技術優劣。 |

> **結論**：R2 追加對照並未改變 R1 結論，且強化兩點——(1) 他對 CLI 型 office 工具有環境限制的實測，Q3 的預設不成立於所有環境；(2) 他明確認定人類 review 仍需要，且需要 verify 機制，故「看得見、改得動」的編輯介面在其判準下有位置，但該位置的完整形態依賴 Univer Pro。

---

## 5. User Q&A

> R2 追加。使用者對 R1 提出三則質問型追問，拆為 Q1～Q3（一子題一 QA）。既有 §1～§4 內容保留，僅補充 §4.4 對照。

### Q1：「這東西到底想解決什麼問題？是在自有網頁中搞出一個 Office365 編輯頁面的意思？」

**A**：方向成立，但命題需拆成三層才精確。Univer 解的是「**自建可編輯 Office 介面**」的問題，不是「取得一個 Office365」。

| 面向 | Office365 編輯頁面 | Univer |
|---|---|---|
| 形態 | hosted 完整應用（連微軟伺服器） | 可嵌入 SDK／runtime（裝進你的 app） |
| 整合方式 | 開網頁使用；被他人嵌入靠 iframe | 開發者給容器 `div`，SDK 在頁面內掛載；README 明示「Without forcing you into a hosted app or a fixed UI」 |
| 產出歸屬 | 微軟的產品 | 開發者自己的編輯表面（README：「a framework for building your own productivity surface」） |
| 工具範圍 | Excel／Word／PowerPoint 網頁版 | 六工具一 runtime：Sheets／Docs／Slides／Canvas／Relational Tables ＋ PDF（規劃中） |
| 協作／import-export | 內建 | 屬 Univer Pro |

三個層次：

1. **它是不是 hosted app？** 不是。開發者提供容器，SDK 掛載；不強制連 Univer 的伺服器。
2. **它是不是 iframe 嵌入？** 不是。iframe 是嵌入一個現成完整應用；Univer 是提供零件，由開發者組出編輯器。
3. **它是否只做編輯頁面？** 不止。同構 runtime 讓同一套邏輯在 Node.js 無介面執行（伺服器端批次處理）；這是 Office365 沒有的層。

反證表：

| 若需求是 | 則 |
|---|---|
| 只是顯示一份 `.xlsx` | Univer 過重，file viewer 即可 |
| 要完整協作 Office 套件 | OSS 核心不足，需 Pro 或改用 ONLYOFFICE Docs |
| 要 agent 操作既有成品檔 | 方向不同，屬 OfficeCLI／univer-cli 類 |

**結論**：是「在自己的網頁內掛載出可編輯 Office 介面」的意思，但**非 hosted、非 iframe、範圍大於單一編輯頁**。

### Q2：「這東西看起來根本踩微軟紅線，難道其實有官方背景？或維護團隊夠大、亦或年紀很長？」

**A**：先給結論——**無微軟官方背景，但非個人專案**。四項命題逐一查證，資料取自 GitHub API 與官網／docs footer。

| 提問 | 查證結果 | 來源 |
|---|---|---|
| 有官方背景？ | 無微軟關聯。DreamNum 為獨立公司；但與 DeepSeek Harness 等有官方合作（`dsh-univer-office` 為 DSH 官方 Office 插件） | `gh api orgs/dream-num`；`gh api repos/dream-num/dsh-univer-office` |
| 維護團隊夠大？ | 是。GitHub org 建於 **2020-02-25**、90 public repos；**8 位公開成員**；實名 contributors **68 人**（含匿名 78）。Top：`jikkai` 1177、`DR-Univer` 623、`wzhudev` 574、`Dushusir` 547、`wpxp123456` 534 commits | members／contributors API |
| 年紀很長？ | Univer repo 首 commit **2022-12-30**（約 4 年）；前身 **Luckysheet 2020-05-15**（約 6 年，2025-08 封存併入）；官網「10+ yrs」自 Luckysheet 血緣與團隊更早工作起算 | commits API；`gh api repos/dream-num/Luckysheet` |
| 公司實體 | 官網 footer「© 2026 **DreamNum Inc.**」；docs footer「© 2026 **DreamNum Co., Ltd.**」 | 官網／docs |

為何外觀像踩紅線：

| 觀察 | 事實 |
|---|---|
| 功能對標 Excel／Word／PPT | 對標的是公開檔案格式標準 **OOXML（ECMA-376／ISO/IEC 29500）**，非微軟私有源碼 |
| 似乎需官方背景才做得到 | 瀏覽器端試算表、公式引擎、Canvas 渲染為公開技術領域；Luckysheet、Handsontable、Grist 皆為獨立實作前例 |
| 相容 Office 格式的授權風險 | 核心 Apache-2.0；C1 未發現複製微軟源碼或相依的跡象；檔案格式相容與獨立實作本身不構成侵權 |

⚠️ **範圍界定**：專利、商標、Trade dress 等法律判斷超出本次調研。上表為可查事實，非法律結論。Step 2 review 建議的法源層（C2）本輪未執行，正式採用前須專業複核。

**結論**：身世為公司化營運、68 貢獻者、血緣可溯 2020；**無微軟官方背景**。可查事實層面未見紅線，法律層面須專業複核。

### Q3：「如果 office 成品基本上都是 AI 在編輯、人類只負責最終確認，那這東西會不會其實沒用、更該用 OfficeCLI？」

**A**：這題要先拆前提，再分機制。AI 編輯＋人類確認不是單一能力，而是三段：

```
AI 產生／修改內容 ──▶ 人類確認（看得見＋改得動） ──▶ 定稿交付
      CLI 即可           需要可視化／可回饋介面         檔案操作
```

OfficeCLI 與 Univer 解的不是同一題：

| 面向 | OfficeCLI | Univer |
|---|---|---|
| 定位 | 操作既有成品檔（.docx／.xlsx／.pptx）的 CLI | 提供編輯能力＋人類協作 UI 的可嵌入 SDK |
| 切入點 | 直接對 OOXML 元素 `get`／`set`／`query`（可到 XPath 層） | 自有 document model ＋同構 runtime |
| 人能看／改？ | CLI ＋ HTML 預覽（`watch`） | 完整 GUI 編輯器（可組裝）＋ Worktree Viewer 人審 |
| agent 路徑 | 有（CLI／MCP） | 家族另有 `univer-cli`；Worktree 審查在 Pro |
| 精確修改既有檔 | 強（元素層） | 需 import／export（Pro） |

第二大腦對照（附 URL 與信任層級）：

| 條目 | 判定 | 信任層級 | 對 Q3 的意義 |
|---|---|---|---|
| [OfficeCLI](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OfficeCLI.md) | 試用 | `human:fatesaikou` / `stable`（**本人結論**） | 已在 terminal 使用 |
| [嘗試使用 OfficeCLI](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/嘗試使用%20OfficeCLI.md) | `officecli watch` 編 pptx，結論「完美」 | `human:fatesaikou` / `stable` | 產檔用途實證可用 |
| [整備 claude web chat](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/整備%20claude%20web%20chat.md) | officeCLI「需要外裝工具的基本不能用」，被自動換 `pptxgenjs` | `human:fatesaikou` / `stable` | **與「更該用 OfficeCLI」直接衝突** |
| [Aionui](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Aionui.md) | 採用 | `human:fatesaikou` / `stable` | 在意 OfficeCLI 連動與 agent 整合 |
| [AI 產出的人類 Review 策略](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/AI%20產出的人類%20Review%20策略.md) | 四層級 review，放棄逐行看 code | `ollama-cloud/deepseek-v4-flash` / `draft`（**未經他 review**） | 人類仍要 review，且需能 verify |
| [技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md) | 不用技術優劣評估；進 Feature 閘門＝影響 workflow | `claude-code/opus-5` / `draft`（**未經他 review**） | Univer 需宿主產品 |

反證表：

| Q3 的論點 | 反證 |
|---|---|
| 更該用 OfficeCLI，因為更精確 | 他實測 OfficeCLI 在 Claude web chat 環境不可用（被換 `pptxgenjs`）；「精確」只在其能操作的環境成立 |
| AI 編輯後 Univer 沒用 | 他的 review 策略顯示人類仍需分層 review；確認階段需要可視化／可改介面，Univer 提供的正是這一段 |
| Univer 與 OfficeCLI 二選一 | 兩者解不同題；Univer 家族自身也提供 `univer-cli`（同 OfficeCLI 類），可並存 |

**結論**：若流程為「agent 產檔 → 自動驗證 → 交付」（人可信任、不需人工檢視），OfficeCLI 類 CLI 足夠，Univer 的 GUI 無用武之地。若人類仍需依影響分層 review（他有此定見），則「看得見、改得動」的編輯介面有位置——此時 Univer 與 OfficeCLI 分工：CLI 負責精確操作、Univer 負責人審介面；但此分工以 Univer Pro（Worktree／協作）為前提，OSS 核心單獨不足以支撐。

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
