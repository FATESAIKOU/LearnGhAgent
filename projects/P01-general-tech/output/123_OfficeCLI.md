# OfficeCLI 技術分析報告

> 調研標的：https://github.com/iOfficeAI/OfficeCLI
> 分析日期：2026-07-11
> 版本：v1.0.135（2026-07-10 發布）
> 授權：Apache 2.0

---

## 1. 這個技術解決什麼問題？

**OfficeCLI 解決的核心問題：AI agent 無法以程式化方式可靠地讀取、建立、修改 Office 文件（.docx / .xlsx / .pptx）。**

具體而言，現狀下 AI agent 要操作 Office 文件面臨以下障礙：

| 障礙 | 說明 |
|------|------|
| 缺乏 CLI 介面 | Office 檔案格式（OOXML）是 ZIP 包裹的 XML，無標準 CLI 工具可直接操作 |
| 依賴 Office 安裝 | 傳統方案（python-docx、openpyxl、python-pptx）需 Python 環境；Microsoft Office / LibreOffice 需完整桌面安裝，無法在 headless / CI / Docker 環境運作 |
| 非結構化輸出 | 既有工具輸出格式不統一（Python dict、XML、DOM），agent 需自行解析，增加 token 消耗與錯誤率 |
| 無視覺回饋 | Agent 操作文件後無法「看到」渲染結果，只能從 DOM 推測版面是否正確（文字溢出、形狀重疊等） |
| 多格式碎片化 | Word / Excel / PowerPoint 各自有不同函式庫，agent 需切換多套 API |

OfficeCLI 以「單一二進位檔 + 統一 CLI + 內建渲染引擎」的方式，讓 AI agent 用一行命令就能對三種 Office 格式執行讀、寫、改、看。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 Office 檔案格式的封閉歷史

- Microsoft Office 長期使用封閉二進位格式（.doc / .xls / .ppt），直到 Office 2007 才轉向 Open XML（OOXML，ECMA-376 / ISO 29500）
- OOXML 本質是 ZIP 壓縮包內含多個 XML 檔案，規範文件超過 6,000 頁，實作門檻極高
- 第三方實作（python-docx、openpyxl、python-pptx、Apache POI）各自覆蓋部分規範，但無一完整實作全部功能

### 2.2 AI agent 的運作模式與傳統工具不匹配

- AI agent（Claude Code、Cursor、GitHub Copilot、Codex）以 CLI 為主要介面，透過 stdout/stdin 交換結構化資料
- 傳統 Office 操作方案要求：
  - Python 直譯器與 pip 套件管理（python-docx 等）
  - COM / Add-in 架構（Microsoft Office）
  - UNO API（LibreOffice）
- 這些方案皆非 agent 原生可消費的介面

### 2.3 Agent 缺乏視覺感知能力

- LLM 本質上是文字模型，無法直接理解版面布局
- 操作 Office 文件時，agent 需要「看到」渲染結果才能判斷文字是否溢出、形狀是否重疊、顏色是否正確
- 既有方案無內建渲染能力，agent 只能猜測

### 2.4 上述背景在 README 中的對應

| 背景 | README 中明確提及 | 通用技術背景（推測補充） |
|------|-----------------|----------------------|
| OOXML 規範複雜度 | 未直接提及 | ✓ 通用背景 |
| 傳統方案需 Python 環境 | ✓（比較表） | |
| Agent 以 CLI 為介面 | ✓（AI-native CLI） | |
| Agent 缺乏視覺感知 | ✓（rendering engine 章節） | |
| 多格式碎片化 | ✓（比較表） | |

---

## 3. 這個技術是如何解決該問題的？

### 3.1 總體架構：三層抽象（L1 → L2 → L3）

```
┌─────────────────────────────────────────────────────┐
│                    AI Agent                          │
│  (Claude Code / Cursor / Copilot / Codex / MCP)     │
└──────────────────────┬──────────────────────────────┘
                       │ CLI / JSON-RPC
┌──────────────────────▼──────────────────────────────┐
│                  OfficeCLI Binary                    │
│  ┌─────────────────────────────────────────────────┐ │
│  │ L1: Read (語意層)                                │ │
│  │   view outline / text / annotated / stats       │ │
│  │   view html / screenshot / issues                │ │
│  ├─────────────────────────────────────────────────┤ │
│  │ L2: DOM (元素操作層)                              │ │
│  │   get / query / set / add / remove / move / swap│ │
│  │   路徑定址: /slide[1]/shape[2]                   │ │
│  ├─────────────────────────────────────────────────┤ │
│  │ L3: Raw XML (原始 XML 層)                        │ │
│  │   raw / raw-set / add-part / validate            │ │
│  │   XPath 直接操作 OOXML                           │ │
│  └─────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────┐ │
│  │ 內建引擎                                         │ │
│  │  • HTML 渲染引擎（→ 瀏覽器 / PNG 截圖）            │ │
│  │  • 公式引擎（350+ Excel 函數，自動求值）           │ │
│  │  • 樞紐分析引擎（原生 OOXML 樞紐表）               │ │
│  │  • 範本合併引擎（{{key}} 取代）                   │ │
│  │  • 文件轉儲引擎（dump → batch JSON）              │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │ 單一二進位檔（內嵌 .NET runtime）
                       │ 無需 Office 安裝
                       │ 跨平台（Win/Mac/Linux/ARM）
```

### 3.2 核心機制

#### 3.2.1 路徑定址系統

OfficeCLI 為文件中的每個元素賦予穩定路徑，語法類似檔案系統路徑：

```
/                          → 文件根
/slide[1]                  → 第一張投影片
/slide[1]/shape[2]         → 第一張投影片的第二個形狀
/body/p[5]/r[2]            → 第五段落的第二個 run
/Sheet1                    → 名為 Sheet1 的工作表
/Sheet1/A1:B10             → Sheet1 的 A1:B10 範圍
```

- 索引從 1 開始（非 0）
- 元素名稱使用 OOXML 本地名稱（非 XPath 完整路徑）
- 支援 CSS-like selector：`paragraph[style=Heading1]`、`run:contains(TODO)`
- Excel 支援 boolean selector：`row[Salary>5000 and Region=EMEA]`

#### 3.2.2 內建 HTML 渲染引擎

這是 OfficeCLI 的關鍵差異點。引擎從零實作，將 OOXML 轉譯為 HTML，涵蓋：

- 形狀、圖表（趨勢線、誤差線、瀑布圖、燭台圖、迷你圖）
- 方程式（OMML → LaTeX → KaTeX 渲染）
- 3D .glb 模型（Three.js）
- 變形轉場（morph transition）
- 投影片縮放（slide zoom）
- 形狀特效

三種輸出模式：

| 模式 | 命令 | 用途 |
|------|------|------|
| HTML | `view deck.pptx html` | 獨立 HTML 檔案，資源內嵌，任何瀏覽器可開 |
| 截圖 | `view deck.pptx screenshot` | 逐頁 PNG，供多模態 agent 讀取 |
| 即時預覽 | `watch deck.pptx` | 本機 HTTP 伺服器，每次編輯自動重新整理瀏覽器 |

這讓 agent 可以執行「渲染 → 觀察 → 修正」循環，即使是在 CI / Docker / 無顯示器的環境中。

#### 3.2.3 常駐模式（Resident Mode）

```
officecli open report.docx    ← 文件載入記憶體
officecli set report.docx ... ← 操作在記憶體中執行（近零延遲）
officecli set report.docx ...
officecli close report.docx   ← 寫回磁碟
```

- 文件在記憶體中保持開啟，後續命令無需重新解析
- 支援自動 flush（閒置 2-10 秒後寫回）
- 可設定 `OFFICECLI_RESIDENT_FLUSH=each` 讓每次 mutation 立即寫回磁碟

#### 3.2.4 批次模式（Batch Mode）

```json
[
  {"command": "set", "path": "/slide[1]/shape[1]", "props": {"text": "Hello"}},
  {"command": "set", "path": "/slide[1]/shape[2]", "props": {"fill": "FF0000"}}
]
```

- 單次傳遞執行多個操作
- 預設繼續執行（continue-on-error），可設 `--stop-on-error`
- 支援 stdin、`--input` 檔案、`--commands` 內嵌 JSON

#### 3.2.5 範本合併（Template Merge）

```
officecli merge invoice-template.docx out-001.docx '{"client":"Acme","total":"$5,200"}'
```

- 取代文件中的 `{{key}}` 佔位符
- 支援 .docx / .xlsx / .pptx
- 跨段落、表格儲存格、形狀、頁首頁尾、圖表標題
- 用途：agent 設計一次版面，生產程式填入 N 次（節省 token，確保版面一致）

#### 3.2.6 文件轉儲（Round-trip Dump）

```
officecli dump existing.docx -o blueprint.json    ← 整份文件
officecli dump existing.docx /body/tbl[1] -o tbl.json  ← 子樹
officecli batch new.docx --input blueprint.json   ← 回放
```

- 將既有文件序列化為可回放的 batch JSON
- 支援子樹層級（單一段落、表格、投影片、工作表）
- 用途：agent 從人類製作的樣本學習，讀取結構化規格而非原始 OOXML XML

#### 3.2.7 MCP Server

```
officecli mcp claude    ← 註冊為 Claude Code 的 MCP 工具
officecli mcp cursor    ← 註冊為 Cursor 的 MCP 工具
officecli mcp vscode    ← 註冊為 VS Code / Copilot 的工具
```

- 透過 JSON-RPC 暴露所有文件操作
- agent 無需 shell 存取即可操作文件

### 3.3 命令分類總表

| 類別 | 命令 | 說明 |
|------|------|------|
| 建立 | `create` | 建立空白 .docx / .xlsx / .pptx |
| 讀取 | `view` | 多種檢視模式（outline / text / annotated / html / screenshot / issues） |
| 讀取 | `get` | 取得元素及其子元素（`--depth N`、`--json`） |
| 讀取 | `query` | CSS-like 查詢，支援 boolean and/or |
| 修改 | `set` | 修改元素屬性 |
| 修改 | `add` | 新增元素（支援 `--from <path>` 複製） |
| 修改 | `remove` | 刪除元素 |
| 修改 | `move` | 移動元素（`--to`、`--index`、`--after`、`--before`） |
| 修改 | `swap` | 交換兩個元素 |
| 驗證 | `validate` | 驗證 OOXML schema |
| 驗證 | `view issues` | 列舉文件問題（文字溢出、公式錯誤等） |
| 批次 | `batch` | 單次傳遞多操作 |
| 轉儲 | `dump` | 序列化為可回放 JSON |
| 合併 | `merge` | 範本合併（`{{key}}` 取代） |
| 預覽 | `watch` | 即時 HTML 預覽（自動重新整理） |
| 整合 | `mcp` | MCP server |
| 原始 | `raw` / `raw-set` | 直接 XPath 操作 OOXML XML |
| 常駐 | `open` / `close` | 常駐模式 |
| 安裝 | `install` | 安裝 binary + skills + MCP |
| 設定 | `config` | 取得/設定組態 |

### 3.4 JSON 輸出格式

所有命令支援 `--json`，輸出格式一致：

**單一元素：**
```json
{"tag": "shape", "path": "/slide[1]/shape[1]", "attributes": {"name": "TextBox 1", "text": "Hello"}}
```

**元素列表：**
```json
[
  {"tag": "paragraph", "path": "/body/p[1]", "attributes": {"style": "Heading1", "text": "Title"}},
  {"tag": "paragraph", "path": "/body/p[5]", "attributes": {"style": "Heading1", "text": "Summary"}}
]
```

**錯誤：**
```json
{
  "success": false,
  "error": {
    "error": "Slide 50 not found (total: 8)",
    "code": "not_found",
    "suggestion": "Valid Slide index range: 1-8"
  }
}
```

錯誤碼：`not_found`、`invalid_value`、`unsupported_property`、`invalid_path`、`unsupported_type`、`missing_property`、`file_not_found`、`file_locked`、`invalid_selector`

### 3.5 技術棧

| 層面 | 內容 |
|------|------|
| 主要語言 | C#（13.7 MB） |
| 執行環境 | .NET（內嵌 runtime，單一二進位檔） |
| 支援平台 | Windows x64/ARM64、macOS Intel/Apple Silicon、Linux x64/ARM64 |
| 安裝方式 | curl/irm 腳本、Homebrew、Scoop、npm、手動下載 |
| 授權 | Apache 2.0 |
| 專案年齡 | 2026-03-15 建立，約 4 個月 |
| 活躍度 | 5,784 commits，最新 release 2026-07-10（v1.0.135） |
| 社群 | 14.9k stars、1,020 forks、Discord |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|---------|-------------|---------------|-----------------|
| **python-docx / openpyxl / python-pptx** | Python 函式庫，各自操作 .docx / .xlsx / .pptx | Python 3.x + pip 安裝 | 需管理三個獨立套件；無統一 API；無渲染能力；無 CLI 介面；agent 需自行解析輸出 | 可在 Python 環境中程式化操作 Office 檔案 |
| **Apache POI** | Java 函式庫，操作 OOXML 與 OLE2 格式 | Java Runtime + Maven/Gradle | Java 環境依賴；API 複雜（低階 DOM 操作）；無 CLI 介面；無渲染能力 | 可在 Java 環境中操作 Office 檔案 |
| **LibreOffice UNO API** | 透過 UNO 介面程式化控制 LibreOffice | LibreOffice 安裝 + 對應語言綁定 | 需完整安裝 LibreOffice（數百 MB）；UNO API 學習曲線高；headless 模式有限；啟動延遲高 | 可透過 LibreOffice 引擎操作 Office 檔案 |
| **Microsoft Office COM / Add-in** | 透過 COM 介面或 VSTO 控制 Microsoft Office | Microsoft Office 安裝 + Windows | 僅 Windows；需 Office 授權費用；COM 介面複雜；不適合 headless / CI 環境 | 可透過 Office 引擎操作 Office 檔案 |
| **OfficeCLI** | 單一二進位 CLI + 三層抽象 + 內建引擎 | 無（單一 binary） | 無顯著副作用 | 一行命令操作三種格式，含渲染與結構化輸出 |

### 4.2 切入點差異分析

| 面向 | python-docx 等 | Apache POI | LibreOffice | Microsoft Office | OfficeCLI |
|------|---------------|-----------|-------------|-----------------|-----------|
| 安裝複雜度 | 中（Python + pip） | 中（Java + Maven） | 高（數百 MB 安裝） | 高（數 GB 安裝 + 授權） | 低（單一 binary） |
| CLI 原生 | ✗ | ✗ | ✗（需包裝） | ✗（需 COM） | ✓ |
| 結構化 JSON 輸出 | ✗（需自行轉換） | ✗（需自行轉換） | ✗ | ✗ | ✓ |
| 內建渲染 | ✗ | ✗ | 部分（GUI 模式） | ✓（需 GUI） | ✓（headless） |
| 路徑定址 | ✗ | ✗ | ✗ | ✗ | ✓ |
| 三格式統一 API | ✗（三個獨立套件） | ✓（單一套件） | ✓ | ✓ | ✓ |
| 常駐模式 | ✗ | ✗ | ✗ | ✗ | ✓ |
| 範本合併 | ✗（需自行實作） | ✗（需自行實作） | ✗ | ✗ | ✓ |
| 文件轉儲回放 | ✗ | ✗ | ✗ | ✗ | ✓ |
| MCP 整合 | ✗ | ✗ | ✗ | ✗ | ✓ |
| 自動安裝 skills | ✗ | ✗ | ✗ | ✗ | ✓ |
| headless / CI | ✓ | ✓ | 部分 | ✗ | ✓ |
| 跨平台 | ✓ | ✓ | ✓ | Windows/Mac | ✓ |

### 4.3 思考方式差異

| 思考方式 | 說明 | 與 OfficeCLI 的對比 |
|---------|------|-------------------|
| **函式庫嵌入**（python-docx 模式） | 將 Office 操作能力嵌入程式語言，開發者撰寫程式碼控制 | OfficeCLI 反其道而行：將操作抽象為 CLI 命令，任何語言皆可呼叫，不需綁定特定程式語言 |
| **應用程式自動化**（COM/UNO 模式） | 透過既有 Office 應用程式的自動化介面控制 | OfficeCLI 完全脫離 Office 應用程式，從零實作 OOXML 規範，無需安裝 Office |
| **文件即資料**（OfficeCLI 模式） | 將 Office 文件視為可透過路徑定址的樹狀結構，操作方式類似檔案系統 | 這是 OfficeCLI 的核心設計哲學，其他方案無對等概念 |

---

## 附錄：專案 metadata

| 項目 | 值 |
|------|-----|
| GitHub | https://github.com/iOfficeAI/OfficeCLI |
| Stars | 14,924 |
| Forks | 1,020 |
| 主要語言 | C# |
| 授權 | Apache 2.0 |
| 建立時間 | 2026-03-15 |
| 最新更新 | 2026-07-11 |
| 最新版本 | v1.0.135（2026-07-10） |
| Commits | 5,784 |
| Topics | agent, ai, cli, office, skills, docx, pptx, xlsx, excel, word, presentation |
| 網站 | https://officecli.ai |
| 社群 | Discord |
