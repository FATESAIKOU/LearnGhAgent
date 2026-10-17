# 303_R1_step2-plan_C1

## 狀況理解

Step 2 C1：取得標的 repo metadata 與主要文件。標的＝`hugohe3/ppt-master`（GitHub repo，Python），R1 首輪、非追問。來源影片無字幕軌，逐字稿不可得，故不引用影片觀點。C1 需盤點：repo 定位與時序、README 與關鍵子文件、架構與執行流程、安裝契約、發佈節奏、文件地圖，供 C2 收斂「問題／背景／解法」並補替代方案 DA 表。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh api repos/hugohe3/ppt-master` | 取 repo metadata | stars/license/時序/主題 | 見下表；MIT、Python、branch `main` |
| `gh api .../git/trees/main?recursive=1` | 盤點檔案結構 | 目錄地圖／檔案數 | 13,098 blobs；`docs/`、`skills/ppt-master/{workflows,references,templates,scripts}` |
| 抓 `README.md`（441 行）＋`SKILL.md`＋routing.md | 取定位與路由契約 | 一手核心文件 | 三層路由、安裝、輸出契約齊 |
| 抓 `getting-started.md`／`why-ppt-master.md`／`project-positioning.md`／`technical-design.md`（967 行） | 取架構與邊界 | pipeline／定位／限制 | 取得 SVG→DrawingML 架構與非目標 |
| `gh api .../releases/latest`＋列表 | 取版本節奏 | 發佈頻率 | v6.7.1（10-16）；近 5 版約每週至兩週 |
| 讀 `requirements.txt`＋`scripts/README.md` | 取依賴與工具鏈 | 執行前提 | 多為 stdlib；選用含 AGPL 元件 |

**repo metadata（2026-10-17 實查）**

| 面向 | 值 |
|---|---|
| 全名／描述 | `hugohe3/ppt-master`；「AI turns documents or topics into real, native PowerPoint decks」 |
| 授權 | MIT（選用 PDF 轉檔 `PyMuPDF` 為 **AGPL-3.0**） |
| 語言／分支 | Python；預設分支 `main` |
| Stars／Forks | 62,871★／4,982 forks（API 值，與 issue 62,844 誤差在時序內正常） |
| 建／推 | created 2025-12-10；pushed 2026-10-16；open issues 1；subscribers 123；size≈138 MB |
| topics | ai-agent, aippt, office, powerpoint, powerpoint-generation, ppt, pptx, presentation, slide, slides |
| 作者 | Hugo He（財金專業 CPA·CPV·投資諮詢工程師）；另參與 microsoft/ResearchStudio |
| 貢獻 | hugohe3 2,079；其餘 kevindesuyo 17、WodenJay 13、shenqili 11、shandianchengzi 4 |

**架構與流程（technical-design.md 一手）**

| 層 | 內容 |
|---|---|
| 定位 | 「native depth」為差異軸：可編輯已是大宗門檻，真問題是原生物件深度；北極星＝持續收斂到 PowerPoint 本身 |
| 形式 | 是「skill／workflow」，跑在任意 agent-capable AI 工具內；確定性 Python 工具負責轉檔/驗證/封裝；模型決定品質上限 |
| 核心路徑 | **受限 SVG 中介語言 → DrawingML 編譯**（`svg_to_pptx.py`）；非任意 SVG 轉檔，契約封閉允許元素/屬性/單位 |
| 既有檔路徑 | **直接 OOXML 操作**保留既有 .pptx（Edit Native 的 roundtrip 工作區，未改頁 byte-for-byte） |
| 主 pipeline | `source_to_md.py` → `project_manager.py init` → `import-sources`/intake → 範本候選 → **Strategist**（`design_spec.md`＋`spec_lock.md`）→ 影像取得 → **Executor**（P01–P05 先過 early 品質閘，其餘連續產 `svg_output/`，再過 final 閘）→ notes → chart 校準 → 後處理（`finalize_svg.py`→`svg_to_pptx.py`） |
| 輸出 | `exports/<name>_<ts>.pptx`（原生 DrawingML）＋`svg_final/` 預覽＋`validation/`（quality report、postflight）；圖表/表格預設為可編輯 shape，`--native-charts-and-tables` 才出資料驅動 Chart/Table；公式編譯成 OMML；SmartArt 為刻意排除 |
| 品質閘 | `svg_quality_checker.py --stage early/final`（final 須 0 error）；`svg_to_pptx.py` 防禦性驗證＋讀回 postflight |

**三條頂層路由（routing.md）**：① Generate PPTX（含 Codex-only 的 image-to-pptx、beautify-pptx、ordinary default/quick profile）② Create Template（brand/style/layout/deck 四子工作流）③ Edit Native PPTX（保原生設計填新內容）。

**安裝契約**：Python 3.10+；`git clone`／下載 ZIP／Claude Code plugin marketplace（`npx skills add hugohe3/ppt-master`）；`pip install -r requirements.txt`。發佈：v6.7.1（2026-10-16，asset `ppt-master-skill-v6.7.1.zip`≈22.56 MB）、v6.7.0(10-08)、v6.6.0(09-19)、v6.5.0(09-16)、v6.4.0(09-12)。**依賴**：多數用 stdlib；選用 `python-pptx`、`XlsxWriter`、`skia-pathops`、`uharfbuzz`、`edge-tts`、`mammoth`、`markdownify`、`PyMuPDF`(AGPL) 等。

**文件地圖**：README/README_CN；`docs/`＝getting-started、why-ppt-master、project-positioning、technical-design、faq、animations、audio-narration、powerpoint-svg-mapping、templates-guide/architecture、roadmap、what-is-ppt、windows-installation；`skills/ppt-master/`＝SKILL.md、workflows/、references/（187 preset 形狀、native-shape-authoring、image-generator 等）、templates/（brands/styles/layouts/decks/charts/icons）、scripts/。

**待 C2 補**：具體「問題／背景」收斂（native depth 相對於 SaaS 生成工具的痛點）、PowerPoint↔SVG 邊界表細節、替代方案（Marp／python-pptx／pptxgenjs／Gamma 等）DA 表、roadmap 未完成項、FAQ 成本與限制細節。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata | gh api（stars/license/語言/時序/主題/貢獻者） | 完整；MIT、Python、main |
| 檔案結構 | recursive tree（13,098 blobs） | 已得目錄地圖與關鍵路徑 |
| 核心文件 | raw 抓 README/SKILL/routing/positioning/why/technical-design | 一手文件齊 |
| 架構與流程 | technical-design pipeline 段 | 取得 SVG→DrawingML 與 3 路由 |
| 安裝與發佈 | README＋releases API | 版本節奏與安裝三路徑確認 |
| 依賴與邊界 | requirements.txt、why 的「不適合」表 | 取得選用依賴與限制 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 資料來源 | clone 全 repo／gh api＋raw 逐檔／只讀 README | gh api metadata＋raw 抓 README 與關鍵子文件 | 免 clone 138 MB 開銷；metadata 與核心文件足以支撐 C1 |
| 文件取捨 | 全 docs 讀完／取定位＋架構＋流程 | 取 README、SKILL、routing、positioning、why、technical-design、getting-started | C1 目標為盤點，深度內容留 C2 收斂 |
| 影片缺口 | 臆測影片觀點／標為待補 | 標為待補、不臆測 | 影片內容屬不可得事實 |
| SVG 路徑定性 | 視為通用 SVG→PPTX／視為專案受限中介語言 | 依官方定位記為「受限 SVG 中介語言」 | technical-design 明示「SVG 適應 PPT Master，非反之」 |
| 替代方案 | C1 一併做／留 C2 | 留 C2 | C1 專注 metadata 與主要文件 |
