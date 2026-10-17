# ppt-master：把文件或主題編譯成原生 PowerPoint 的工作流

> 標的：`hugohe3/ppt-master`（GitHub repo；Python 專案，MIT，2026-10-17 API 實查 62,871★／4,982 forks）
> 來源：GitHub 一周熱點 135 期（影片）——**該影片無可取得字幕軌（YouTube transcripts disabled），逐字稿不可得；本報告不引用影片觀點，影片僅作標的引入**
> 分析：技術解析助理，2026-10-17
> 前置查證：第二大腦（FATESAIKOU/MyBrain）**無 `ppt-master`／`hugohe` 之獨立技術評估**（全 bundle grep 0 命中）。本報告事實以 repo 的 README、`docs/why-ppt-master.md`、`docs/technical-design.md`、releases metadata 為主。

---

## 1. 這個技術解決什麼問題？

用一句話：**AI 產出的簡報若要可編輯，多半只是淺層可編輯；ppt-master 要讓 AI 直接編譯出帶原生 PowerPoint 物件模型（母版、原生圖案、資料驅動圖表／表格、OMML 公式、轉場與動畫）的 `.pptx`。**

repo 自述的差異軸是 **native depth（原生物件深度）**，而非「可否編輯」——後者在其定位文件裡被明列為「已是大宗門檻」。

被解的問題再拆成數個操作級子問題：

| # | 子問題 | 具體要求 |
|---|---|---|
| P1 | 從來源生成整份新簡報 | 吃 PDF／DOCX／XLSX／PPTX／EPUB／HTML／LaTeX／URL／Markdown／純文字／主題文字 |
| P2 | 產出真原生可編輯物件 | 原生圖案（含調整控點）、連接線、母版／版面繼承、原生圖表／表格、OMML 公式 |
| P3 | 保留既有成品檔的原生設計 | 對既有 `.pptx` 填新內容，未改頁面 byte-for-byte 還原 |
| P4 | 抽取出可重用範本 | Brand／Style／Layout／Deck 四類工作區蒸餾 |
| P5 | 投影片外的交付物 | speaker notes 轉語音旁白、轉場與逐物件動畫、多畫布格式（16:9／A4／9:16 等） |
| P6 | 執行前提與邊界 | 只裝 Python 3.10+；跑在任意 agent-capable AI 工具內；資料留本地 |

### 問題描述中的模糊之處

- **「native depth」的邊界未在標題定義**：標題只說「real, native PowerPoint decks」。實際邊界由 `docs/powerpoint-svg-mapping.md` 逐項定義為 native／approximate／bake-required／unsupported，並非標題可推得。SmartArt 屬**刻意排除**。
- **「documents or topics」範圍過廣**：來源清單涵蓋文件、網頁、WeChat 文章、純主題文字，未在使用者介面區分「文件改寫」與「主題研究」兩種品質責任。
- **未定義「完成」的品質標準**：repo 自述輸出是「high-quality editable draft, not a sealed final deck」，最後一哩留給使用者；「多好才算可交付」由使用者判定，非工具保證。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 repo 文件明確提到的背景

- **可編輯已不是差異點，深度才是**：`why-ppt-master.md` 開宗明義寫「Editable is already table stakes」，真問題是「how deep the editability goes」——是把投影片當成一張可編輯的皮，還是完整套用 PowerPoint 的原生物件模型。
- **好簡報的成本是多層耦合，不是畫圖時間**：文件列舉受眾與目的定義、證據選擇與驗證、論證與敘事成形、視覺系統、原生文件建構、交付／審閱／重用準備，且這些層互相耦合——改訊息就要改大綱、設計、原生物件與驗證。現有 AI 工具只壓縮其中一層。
- **AI 生成簡報的既有格式選項各有結構性障礙**（`technical-design.md` 的「Why SVG?」）：
  - **直接生成 DrawingML**：極度冗長（一個圓角矩形要數十行巢狀 XML），AI 訓練資料遠少於 SVG，輸出不可靠且肉眼難除錯。
  - **HTML/CSS**：世界觀不符——HTML 描述**文件**（元素位置由內容流決定），PowerPoint 描述**畫布**（每個元素是絕對定位、無流的獨立物件）。即使解決瀏覽器排版引擎問題，HTML `<table>` 對一組獨立 shape 仍無自然映射。
  - **WMF/EMF**：與 DrawingML 同源、轉換損失小，但 AI 訓練資料近乎零。
  - **SVG 當圖片嵌入**：最簡單，但直接消滅可編輯性（shape 變像素、文字不可選）。
- **模型決定品質上限**：repo 反覆聲明 `harness + model = agent`，工具只擁有 workflow，模型決定上限；建議搭大 context（~1M tokens）模型與 AI 生圖。

### 2.2 通用技術背景（補充）

| 背景項 | 內容 |
|---|---|
| **OOXML 的形態** | `.pptx` 是 ZIP 包裹的一組 XML（DrawingML + PresentationML）；原生可編輯物件與「圖片化投影片」在檔案結構上是兩種東西 |
| **原生 vs 圖片化的分野** | 圖片化輸出的每個 element 是點陣圖，文字不可選、顏色不可改；原生輸出才有可點選的 shape／文字框 |
| **AI 簡報工具的三種典型輸出** | ① HTML 渲染後轉圖；② 圖片／PDF；③ 可編輯但只到文字框層級（thin editable skin）。三者皆非「原生深度」 |
| **context window 與一致性** | 逐頁序列生成以維持跨頁視覺一致性，代價是生成時間；這是 repo 自述 10 頁需 10–20 分鐘（SaaS 數秒）的技術成因 |
| **本地 vs 託管** | 本地 pipeline 換取資料不外流與無平台綁定，代價是需要安裝 Python 與 agent 工具 |

### 2.3 情境脈絡（第二大腦）

| 來源 | 內容 | 信任層級 | 時間 |
|---|---|---|---|
| [嘗試使用 OfficeCLI.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E5%8B%95%E6%89%8B%E5%81%9A/%E5%98%97%E8%A9%A6%E4%BD%BF%E7%94%A8%20OfficeCLI.md) | `officecli watch x.pptx` 編輯金融簡報，結果記為「完美」，產出為 FinDashboard 的美股加碼判定報告投影片 | `human:fatesaikou`／stable | 2026-07-14 |
| [整備 claude web chat.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E5%8B%95%E6%89%8B%E5%81%9A/%E6%95%B4%E5%82%99%20claude%20web%20chat.md) | 「officeCLI 這種需要外裝工具的基本不能用 → 內部被自動換成 pptxgenjs」 | `human:fatesaikou`／stable | 2026-07-14 |
| [建立投資決策Dashboard.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E5%8B%95%E6%89%8B%E5%81%9A/%E5%BB%BA%E7%AB%8B%E6%8A%95%E8%B3%87%E6%B1%BA%E7%AD%96Dashboard.md) | FinDashboard 為「日常在用」四專案之一；金融簡報動線是既有的 deck 產出場景 | `ollama-cloud/deepseek-v4-flash`／**draft（AI 草稿，未經他 review）** | 2026-07-05 |

**判讀**：使用者的既有 deck 動線集中在「操作既有成品檔」（OfficeCLI）與「嵌入式編輯器 SDK」（Univer），**無「從文件自動生成整份原生 PPT」之同類評估**；本標的是第三種切入點。

---

## 3. 這個技術是如何解決該問題的？

ppt-master 的做法是：**以「受限 SVG 中介語言」為頁面設計權威，由確定性 Python 腳本將 SVG 編譯成 DrawingML，產出原生 `.pptx`；模型負責設計與內容，腳本負責轉換、驗證與封裝。**

### 3.1 三條頂層路由（`workflows/routing.md`）

```
輸入請求
  ├─ ① Generate PPTX      來源文件／主題 → 生成全新原生 PPTX
  │     ├─ default / quick profile
  │     ├─ beautify-pptx  profile（保留頁數／順序／用字 1:1，僅改版面）
  │     └─ image-to-pptx  profile（須 Codex；把圖片頁框還原成分層可編輯頁）
  ├─ ② Create Template    Brand / Style / Layout / Deck 四子工作流 → 可重用工作區
  └─ ③ Edit Native PPTX   既有 .pptx 保留原生設計、只填新內容（round-trip 工作區）
```

路由選擇的判別：**重新設計可見頁面 → Generate；保留原生 deck 只編輯 → Edit Native PPTX**。其中 `beautify-pptx` 進一步以「是否保留頁數／順序／用字」區分於一般 Generate。

### 3.2 核心機制：受限 SVG → DrawingML 編譯

不是任意 SVG 轉檔。`svg_output/` 用的是**專案自訂的 SVG 中介語言**：借用 SVG 的 XML 語法與二維圖形模型，但**契約封閉**了允許的元素、屬性、單位、metadata 與映射。方向明確為「**SVG 適應 PPT Master，而非 PPT Master 擴張以跟隨整個 SVG 標準**」。

編譯的可行性來自 SVG 與 DrawingML 共享世界觀（皆為絕對座標二維向量格式）：

| SVG | DrawingML |
|---|---|
| `<path d="...">` | `<a:custGeom>` |
| `<rect rx="...">` | `<a:prstGeom prst="roundRect">` |
| `<circle>` / `<ellipse>` | `<a:prstGeom prst="ellipse">` |
| `transform="translate/scale/rotate"` | `<a:xfrm>` |
| `linearGradient` / `radialGradient` | `<a:gradFill>` |
| `fill-opacity` / `stroke-opacity` | `<a:alpha>` |

中介語言把輸入分成三態，各自有處理：

| 狀態 | 定義 | 處理 |
|---|---|---|
| Canonical authoring input | prompts／templates／examples 產生的唯一建議寫法 | 依註冊映射驗證並編譯，無 alias warning |
| Compatible input | 有明文記載、且只有一種安全確定性正規化的歷史／手寫寫法 | checker 發非阻斷 warning；converter 在編譯邊界正規化 |
| Invalid / unsupported | 無映射、語意不明、結構契約破壞，或會產生無效 DrawingML/PPTX | checker 報 error 並阻斷標準流程 |

### 3.3 主 pipeline（Generate 預設流）

```
來源（PDF/DOCX/XLSX/PPTX/URL/Markdown/主題文字）
   ↓  source_to_md.py 依型別分派；純主題或關鍵事實缺口 → topic-research
   ↓  project_manager.py init <name>
   ↓  import-sources：歸檔來源 → pptx_intake 產 analysis/*.json（identity/slide_library）
   ↓  Step 3 準備 Brand/Style/Layout/Deck 候選（不開 UI、不安裝）
   ↓  Strategist：讀來源 → 定核心訊息與敘事 mode → design_spec.md + spec_lock.md
   ↓  Image Acquisition（AI 生圖／網路搜尋／切圖）
   ↓  Executor：逐頁手寫 svg_output/
   │     ├─ P01–P05 → svg_quality_checker.py --stage early（≤6 頁名冊略過）
   │     ├─ 其餘頁連續產出（中途不呼叫 checker）
   │     ├─ svg_quality_checker.py --stage final（強制，0 error；warning 非阻斷）
   │     ├─ （條件）speaker notes → notes/total.md
   │     └─ （條件）verify-charts 校準資料圖表座標
   ↓  後處理：total_md_split.py（notes）→ finalize_svg.py → svg_to_pptx.py
   ↓  輸出 exports/<name>_<ts>.pptx + svg_final/ + validation/ + backup/
```

**敘事 mode** 有五種（`pyramid` 結論先行說服／`narrative` 故事／`instructional` 教學／`showcase` 展示／`briefing` 中性資訊），與 18 種內建**視覺風格**（`swiss-minimal`／`editorial`／`dark-tech`／`brutalist`／`ink-wash` 等）為兩個獨立軸，任一對任一可組合，於確認階段鎖定後跨頁維持。

**quick-generate** 是另一條顯式路徑：跳過 Strategist 規劃／確認與 `finalize_svg.py`，由當前 agent 在 active context 內一次決定 mode／style／內容／頁面／載體，手寫 SVG，過一個無鎖的最終品質閘，再匯出。**不可續跑，context 遺失即重來。**

### 3.4 品質閘（確定性程式）

| 元件 | 責任 | 明確非責任 |
|---|---|---|
| `svg_quality_checker.py` | 對 authoring 狀態強制專案契約；error 阻斷、warning 放行 | 不靜默改寫頁面、不猜設計意圖 |
| `svg_to_pptx.py` | 防禦性驗證映射與封裝、正規化 compatible 形式、要求當輪 final report 才正式發佈 | 不重跑完整 checker、不以「檔案產生」當成上游品質閘通過的證明 |
| `workflow_transcript.py` / `workflow_log.py` | 記錄專案範圍的 Python 指令封套與有界結果，並追加重要非 Python 稽核事件 | 不保留完整 console、不推論 readiness |

### 3.5 輸出契約

| 產出 | 內容 |
|---|---|
| 預設 `.pptx` | 原生 DrawingML；文字與向量 shape 為可編輯原生物件，點陣資產複製為圖片 media（非整頁扁平化） |
| `--native-charts-and-tables` | 另出 `_native_charts_tables.pptx`，圖表／表格為帶 **Edit Data** 工作簿的資料驅動 Chart/Table 物件 |
| 預設圖表／表格 | 以 SVG 衍生的 DrawingML shape 呈現，跨 PowerPoint／Keynote／LibreOffice／WPS 渲染一致；作者可二選一 |
| 公式 | 編譯為可編輯 OMML（PowerPoint 2010+）；M365 文件化的 LaTeX／mhchem 輸入向前編譯，超出 profile 者 fail closed |
| 旁白 | speaker notes 可轉語音旁白 → `_narrated.pptx` |
| `svg_final/` | 由 `svg_output/` 衍生的視覺預覽；不是第二條匯出路徑 |
| `validation/` | workflow 稽核 log、SVG quality report、postflight package 稽核 |

**刻意排除**：SmartArt（封閉脆弱的物件模型）、WordArt／變形文字、reflection／soft edge 等裝飾效果、OLE／video／巨集等嵌入物件。

### 3.6 安裝與依賴

| 面向 | 內容 |
|---|---|
| 安裝三路徑 | `git clone`（推薦）／下載 ZIP／Claude Code plugin marketplace（`npx skills add hugohe3/ppt-master`） |
| 唯一前提 | Python 3.10+；之後 `pip install -r requirements.txt` |
| 依賴 | 多數為 stdlib；選用含 `python-pptx`、`XlsxWriter`、`skia-pathops`、`uharfbuzz`、`edge-tts`、`mammoth`、`markdownify` 等 |
| 授權 | MIT；**選用 PDF 轉檔 `PyMuPDF` 為 AGPL-3.0** |
| 文件轉檔例外 | Pandoc 僅用於 `.doc`／`.odt`／`.rtf`／`.tex` 等長尾格式 |
| 發佈節奏 | v6.7.1（2026-10-16）／v6.7.0(10-08)／v6.6.0(09-19)／v6.5.0(09-16)／v6.4.0(09-12)，約每週至兩週一版 |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 第二大腦查證結果

先讀骨幹索引與個案。**第二大腦無 `ppt-master` 的獨立技術評估**；同軸（AI × Office/PPT 生成、設計產物產出）他已有數筆判定：

| 標的 | 判定 | 判定理由 | 來源／信任層級 |
|---|---|---|---|
| **OfficeCLI**（AI agent 操作 Office 文件的 CLI） | **試用** | 「單一二進位檔 CLI，accept 基本 OK，可單獨執行且有 HTML 預覽，想在 terminal 先試」 | [OfficeCLI.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/OfficeCLI.md)（`human:fatesaikou`＋`stable`，**他本人定案**，2026-07-12） |
| **OpenDesign**（coding agent 產出設計產物：prototype／deck／template／image／video） | **採用** | 「可以在 Local 嘗試，甚至之後會需要在公司電腦嘗試」 | [OpenDesign.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/OpenDesign.md)（`human:fatesaikou`＋`stable`，**他本人定案**，2026-06-06） |
| **Univer**（可嵌入產品的開源 Office SDK） | **不採用** | 「我沒有寫編輯器的需求」——需求層不成立；抽取為「嵌入式 Office 編輯器 SDK」類別方向 | [Univer.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/Univer.md)（`process:learn-gh-agent`／`draft`，**AI／流程草稿，未經他 review**，2026-10-06） |
| **diagram-design**（出版級圖表設計 Skill） | **不採用** | 「用不到如此重型的圖像技能；目的是理解抽象概念（它是出版工具不是思考工具）」 | [diagram-design.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/diagram-design.md)（`process:learn-gh-agent`／draft，**AI 草稿未經他 review**，2026-08-16） |
| **HyperFrames**（HTML+CSS+animation 逐幀渲染為確定性 MP4） | **採用** | 「免費、將確定性 HTML 轉影片有價值，比多模態更穩定且成本更低」 | [HyperFrames.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/HyperFrames.md)（`process:…`／draft，**AI 草稿未經他 review**） |

**判準來源（骨幹）**：

| 檔案 | 關鍵準則 | 信任層級 |
|---|---|---|
| [技術取捨準則.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%BD%E8%B1%A1%E7%90%86%E8%A7%A3/%E6%9C%AC%E8%B3%AA%E6%B4%9E%E5%AF%9F/%E6%8A%80%E8%A1%93%E5%8F%96%E6%8D%A8%E6%BA%96%E5%89%87.md) | ①理解優先（不穩定或不熟悉先自己兜）②MVP→Feature 唯一閘門＝能否影響個人 workflow ③Reject≠沒價值④汰換看上游死沒死，不追新⑤約束放 harness、要補驗證機制而非加審核關卡 | `claude-code/opus-5`／`draft`（**AI 草稿未經他 review**；檔內「原話：」引號內為本人結論） |
| [判定總表.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/%E5%88%A4%E5%AE%9A%E7%B8%BD%E8%A1%A8.md) | 索引；採採用／試用／觀望／不採用／未判定五級，明寫「不採用不等於沒價值」 | `ollama-cloud/deepseek-v4-flash`／`draft`（**AI 草稿未經他 review**） |
| [專案現況表.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E5%8B%95%E6%89%8B%E5%81%9A/%E5%B0%88%E6%A1%88%E7%8F%BE%E6%B3%81%E8%A1%A8.md) | FinDashboard 金融簡報動線為「理解已達成」；deck 產出既有場景 | `ollama-cloud/deepseek-v4-flash`／`draft`（**AI 草稿未經他 review**） |

### 4.2 替代方案與 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **ppt-master（本標的）** | 受限 SVG 中介語言作頁面權威，Python 腳本編譯成 DrawingML；模型只做設計與內容 | Python 3.10+＋任意 agent-capable 工具；品質上限由模型與 context 決定 | 10 頁需 10–20 分鐘；無協作、無完整自由畫布；單一維護者 bus factor≈1；PDF 轉檔含 AGPL 元件 | 產出帶原生圖案／母版／原生圖表／OMML／動畫與旁白的 `.pptx`；資料本地；無平台綁定 |
| **pptxgenjs／python-pptx（程式庫）** | 由呼叫端寫程式呼叫固定 API 建立 OOXML 物件 | 需能用 JS／Python 寫程式；物件層級需自行編排 | 需自行處理版面計算、字型、圖表資料與一致性；agent 直接寫大量建構碼 | 完全可程式化、原生可編輯；控制粒度最細，但設計／敘事層全靠呼叫端 |
| **Marp／Slidev（Markdown 導向）** | Markdown 撰寫 → 渲染為 HTML／PDF 投影片 | 需接受其版面語法；原生輸出非 `.pptx` 物件 | 與 PowerPoint 物件模型脫鉤，`.pptx` 需另轉（多為圖片或非原生） | 撰寫快、版控友好、可網頁瀏覽；換取的是原生深度 |
| **託管式 AI 簡報 SaaS（Gamma 等）** | 上傳來源→雲端模型生成→平台內編輯 | 需帳號與訂閱；資料離機 | 供應商綁定、按量或訂閱計費、資料不在本地 | 零安裝、數秒生成、協作與分享開箱即用 |

### 4.3 各方案切入點差異

- **ppt-master**：切入點是「**用受限中介語言換取原生深度**」。把 AI 的生成可靠性（SVG 訓練資料多）與交付的原生性（DrawingML）用一層確定性編譯解耦。
- **pptxgenjs／python-pptx**：切入點是「**用程式庫 API 直接建 OOXML**」。原生性同級，但把設計與一致性責任完全交給呼叫端的程式碼。
- **Marp／Slidev**：切入點是「**Markdown 即投影片**」。犧牲原生 PowerPoint 物件模型，換取撰寫與版控效率。
- **託管 SaaS**：切入點是「**外包生成與維護**」。以資料離機與訂閱換取零安裝與即時協作。

### 4.4 與第二大腦既有判定的衝突（對照最有價值處）

| 衝突點 | 第二大腦既有立場 | 本標的的情形 | 判定 |
|---|---|---|---|
| **「外裝工具基本不能用」** | [整備 claude web chat.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E5%8B%95%E6%89%8B%E5%81%9A/%E6%95%B4%E5%82%99%20claude%20web%20chat.md)（`human:fatesaikou`／stable，**他本人定案**）：officeCLI「這種需要外裝工具的基本不能用 → 內部被自動換成 pptxgenjs」。 | ppt-master 的形態正是「skill／workflow 跑在 agent 內、由外部 Python 腳本執行」——與 officeCLI 同屬**需要外裝工具**的模式。 | **明確衝突（最高價值）**。這是他對「agent 內呼叫外裝工具」的既有否定。但該判定成立於 **claude web chat（託管 web 環境）**，其模型會自行以內建套件取代外掛工具；本標的官方支持的是 Claude Code／Codex／Cursor 等可讀寫檔案與執行指令的 agent，兩者環境不同。**若在 claude web chat 這類「模型會靜默改用內建工具」的環境使用，會正面撞上此結論。** |
| **MVP→Feature 閘門** | [技術取捨準則.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%BD%E8%B1%A1%E7%90%86%E8%A7%A3/%E6%9C%AC%E8%B3%AA%E6%B4%9E%E5%AF%9F/%E6%8A%80%E8%A1%93%E5%8F%96%E6%8D%A8%E6%BA%96%E5%89%87.md)（`draft`）：升 Feature 的唯一閘門＝**能否影響個人 workflow**。 | 他的既有 deck 產出場景是 FinDashboard 金融簡報動線，目前走「操作既有成品檔」（OfficeCLI）。 | **需注意而非直接衝突**。ppt-master 解的是「從文件生成整份新簡報」，與他現行「編輯既有成品檔」是不同切入點；是否進 workflow 取決於他是否有「從來源文件生成整份 deck」的需求，本報告不代為判定。 |
| **不追新／汰換看上游死沒死** | [技術取捨準則.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%BD%E8%B1%A1%E7%90%86%E8%A7%A3/%E6%9C%AC%E8%B3%AA%E6%B4%9E%E5%AF%9F/%E6%8A%80%E8%A1%93%E5%8F%96%E6%8D%A8%E6%BA%96%E5%89%87.md)（`draft`）：不追新；汰換看上游是否停更。 | repo created 2025-12-10（約 10 個月），主要貢獻者 hugohe3 2,079 commits，其餘貢獻者個位數——**年輕＋單人維護**。 | **觸發「先自己兜」而非拒絕**。依準則，專案年輕或單人維護是「不穩定／不熟悉 → 先自己兜」的觸發條件，不是價值否定。**與 62,871★ 的熱度並存的事實是：單一維護者的 bus factor≈1。** |
| **與 OfficeCLI 的關係** | [OfficeCLI.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/OfficeCLI.md)（`human:fatesaikou`／stable）：判定**試用**，方向是「操作既有成品檔」。 | ppt-master 的 Edit Native PPTX 路由同樣操作既有 `.pptx`，但其主線是「從來源生成整份原生 deck」。 | **不互相取代，非衝突**。此判讀與他 [Univer.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/Univer.md) 內「操作成品檔 vs 提供編輯能力，不互相取代」的切題原則一致；ppt-master 屬第三類。 |
| **與 OpenDesign 的關係** | [OpenDesign.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/OpenDesign.md)（`human:fatesaikou`／stable）：判定**採用**，是「讓 coding agent 產出設計產物（含 deck）」的平台。 | 兩者都產出設計產物且都跑在既有 coding agent 上；OpenDesign 為完整平台（web＋daemon＋desktop），ppt-master 為精簡 skill／workflow。 | **同軸但形態不同**。他既已採用 OpenDesign，本標的可視為同軸的「輕量 skill 路線」對照；不構成否定，也不構成替代（OpenDesign 不限於 PPT，ppt-master 專攻原生 PPTX）。 |
| **重型工具判準** | [diagram-design.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/diagram-design.md)（draft）：出版級圖表 skill 判「用不到如此重型」。 | ppt-master 依賴多（skia-pathops／uharfbuzz／PyMuPDF），文件體系龐大（`docs/`＋`skills/ppt-master/references/`）。 | **需注意**。其「重型」程度介於 diagram-design 與純 SDK 之間；是否觸發「用不到」取決於實際需求，本報告不代為判定。 |

### 4.5 可抽取的方向與結論

即使不採用，本輪仍有兩個可抽取的方向：

1. **「受限中介語言 → 原生格式編譯」的分層**：把「AI 生成（可靠性優先）」與「交付原生性」用一層確定性編譯解耦。此結構可轉移到任何「AI 產出需落在某原生格式」的場景。
2. **「內容契約 vs 機器事實」的雙通道**：`sources/` 內容檔為內容契約、`analysis/*.json` 為機器抽取事實，兩者責任分明，避免設計契約與事實混在同一份 artifact。

> **結論**：`ppt-master` 解的是「AI 生成**原生深度** PowerPoint」的第三種切入點（有別於 OfficeCLI 的操作成品檔、Univer 的編輯器 SDK）。其在第二大腦**無獨立評估**，但有一條**明確衝突**：[整備 claude web chat.md](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E5%8B%95%E6%89%8B%E5%81%9A/%E6%95%B4%E5%82%99%20claude%20web%20chat.md)（`human:fatesaikou`／stable，**他本人定案**）判「需要外裝工具的基本不能用」，而 ppt-master 正是外裝工具模式——**該衝突成立於託管 web 環境，不必然適用於可讀寫檔案與執行指令的 agent 環境**。另需注意的是其單一維護者 bus factor≈1，依其準則觸發「先自己兜」而非拒絕。本報告僅作技術解析，不作採用判定。

---

## 附錄：資料來源

| 來源 | 用途 |
|---|---|
| `README.md`（repo，2026-10-17） | 定位、安裝、輸出契約、贊助與作者背景 |
| `docs/why-ppt-master.md` | native depth／logic first／成本／隱私／不適用的邊界 |
| `docs/technical-design.md`（967 行） | 架構、SVG 中介語言、pipeline、route 表、不變式 |
| `skills/ppt-master/workflows/routing.md` | 三條頂層路由 |
| GitHub API（repos／trees／releases，2026-10-17） | metadata、檔案結構、發佈節奏、貢獻者分布 |
| FATESAIKOU/MyBrain（`/tmp/mybrain` @ ac9eaa2，2026-10-17） | 技術取捨準則、判定總表、專案現況表、OfficeCLI／Univer／OpenDesign 判定 |

> 影片來源（GitHub 一周熱點 135 期）無可取得字幕軌，逐字稿不可得，本報告不引用其觀點。
