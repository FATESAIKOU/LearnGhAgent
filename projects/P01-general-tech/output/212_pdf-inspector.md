# pdf-inspector（Firecrawl 開源的快速 PDF 分類與抽取工具）

> 調研標的：https://github.com/firecrawl/pdf-inspector
> 調研日期：2026-08-09 ｜ 版本：pdf-inspector 0.2.6（benchmark 對照版本）
> 主要語言：Rust（MIT license，13,753 stars，單一依賴 `lopdf`）

---

## 1. 這個技術解決什麼問題？

pdf-inspector 解決的是**「在本地、不靠 OCR、毫秒級」地判斷一份 PDF 是文字型還是掃描型，並把文字型 PDF 轉成帶位置資訊與結構的 Markdown** 的問題。

具體拆成三個子問題：

| 子問題 | 具體內容 |
|---|---|
| **分類（classification）** | 判斷 PDF 是 `TextBased`（有文字層）、`Scanned`（純影像）、`ImageBased`、`Mixed`（混合），並給出信心分數（0.0–1.0）與「哪些頁需要 OCR」的清單 |
| **抽取（extraction）** | 從文字型 PDF 抽出帶 X/Y 座標、字型、字號、粗斜體等屬性的 `TextItem`，並自動處理多欄閱讀順序 |
| **轉換（Markdown）** | 把抽取結果轉成結構化 Markdown：標題（H1–H4）、清單、程式碼區塊、表格、粗斜體、超連結、頁碼過濾等 |

**問題描述是否含糊？** 有兩處需注意：

1. 「快速」的邊界：README 宣稱分類約 10–50ms、文字型抽取約 150ms、300+ 頁毫秒級偵測。這些數字是**特定硬體（Apple M4 Pro）與特定語料（opendataloader-bench 200 份 PDF）**下的結果，不是通用保證。
2. 「不靠 OCR」的邊界：它**只處理有文字層的 PDF**。對掃描型 PDF，它只負責「偵測出來並回報哪些頁需要 OCR」，本身不做 OCR——這是設計上的刻意分工，不是缺點。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章明確提到的背景

- **PDF 有兩種本質不同的型態**：一種內嵌文字層（text-based，文字以字元碼＋字型資訊儲存），一種是掃描影像（scanned，整頁就是一張圖）。兩者的處理方式完全不同——前者可直接讀取字元碼，後者必須靠 OCR 把影像轉成文字。
- **Firecrawl 的實務觀察**：約 **54%** 的 PDF 是文字型、不需要 OCR。但既有 pipeline 常「一律送 OCR」，造成不必要的成本與延遲。
- **OCR 是昂貴且慢的**：一次 OCR 約 2–10 秒，且通常要呼叫外部服務（付費、有延遲、有資料外送疑慮）。對文字型 PDF 做 OCR 是浪費。

### 2.2 通用技術背景（文章未明說，補自通用知識）

- **PDF 的內容流（content stream）是「繪圖指令」而非「文字」**：PDF 用 `Tj`/`TJ`（文字運算子）與 `Do`（影像運算子）等低階運算子描述頁面。要判斷「這頁有沒有文字」，本質是掃描內容流裡有沒有文字運算子——這不需要載入整份文件。
- **PDF 沒有「段落／標題／表格」的語意結構**：不像 HTML 有 `<h1>`、`<table>` 標籤，PDF 只記錄字元的位置與字型。要還原結構（標題層級、表格、閱讀順序）必須靠**幾何與字型啟發式**推測。
- **字元編碼問題**：PDF 字型常用 CID（Type0/Identity-H）編碼，字元碼與 Unicode 之間需要 ToUnicode CMap 對照表才能解出正確文字。這是抽取正確性的關鍵瓶頸。
- **既有工具慢的原因**：多數 PDF 轉 Markdown 工具（如 PyMuPDF4LLM、MarkItDown）是 Python 實作，且常對每頁做完整物件載入與版面分析，導致 200 份文件要 16–17 秒。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 核心架構：偵測與抽取分離，文件只載入一次

```
PDF bytes
  │
  ├─► detector         → PdfType (TextBased / Scanned / ImageBased / Mixed)
  │
  └─► extractor
        ├─ fonts        → font widths, encodings
        ├─ content_stream → walk PDF operators → TextItems + PdfRects
        ├─ xobjects     → Form XObject text, image placeholders
        ├─ links        → hyperlinks, AcroForm fields
        └─ layout       → column detection → line grouping → reading order
              ├─► tables
              └─► markdown
```

關鍵設計：**文件透過 `load_document_from_path` / `load_document_from_mem` 只解析一次**，偵測與抽取共用同一份解析結果，避免重複 I/O。

### 3.2 分類機制（detector.rs）

1. 解析 xref 表與頁樹（**不載入完整物件**）
2. 依 `ScanStrategy` 選取要掃描的頁
3. 在內容流中找 `Tj`/`TJ`（文字運算子）與 `Do`（影像運算子）
4. 依文字運算子在各取樣頁的出現與否分類

**ScanStrategy 四種模式：**

| 策略 | 行為 | 適用 |
|---|---|---|
| `EarlyExit`（預設） | 掃全部頁，遇到第一頁非文字即停 | 把 TextBased 路由到快速抽取的 pipeline |
| `Full` | 掃全部頁，不提早退出 | 精確區分 Mixed vs Scanned |
| `Sample(n)` | 均勻取樣 n 頁（首、中、尾） | 超大 PDF，速度優先 |
| `Pages(vec)` | 只掃指定頁 | 呼叫端已知要檢查哪些頁 |

產出含 `pages_needing_ocr`——**逐頁**列出缺文字的頁，讓呼叫端能做「逐頁 OCR 路由」而非全有全無。

### 3.3 抽取機制（extractor/）

- **content_stream**：走訪 PDF 運算子，產出 `TextItem`（含 text、x、y、width、height、font、font_size、page、is_bold、is_italic、is_underline 等）與 `PdfRect`（`re` 運算子產生的矩形，用於表格邊界）。
- **fonts**：解析字型寬度表與編碼表；`tounicode.rs` 處理 CID 字型的 ToUnicode CMap 解碼（UTF-16BE、UTF-8、Latin-1）。
- **layout**：欄偵測 → 行分組 → 閱讀順序。支援多欄（報紙式）、RTL 文字。
- **粗斜體偵測**：PDF 沒有 underline 字型旗標，underline 是「baseline 下方的規則線／細矩形」——靠幾何偵測（見 types.rs 註解）。

### 3.4 表格偵測（tables/）——雙模式

| 模式 | 原理 |
|---|---|
| **Rectangle-based** | 從 PDF 繪圖運算子（`re`）偵測矩形邊界，用 union-find 合併成表格網格 |
| **Heuristic** | 從文字對齊（X 座標）推測欄位結構 |

處理金融表格（合併數字 token）、跨頁續表、註腳。

### 3.5 Markdown 轉換（markdown/）

| 元素 | 偵測方式 |
|---|---|
| 標題 H1–H4 | 字號層級（相對正文），0.5pt 聚類 |
| 粗斜體 | 字型名稱模式（Bold、Italic、Oblique） |
| 項目符號清單 | `•`、`-`、`*`、`○`、`●`、`◦` 前綴 |
| 編號清單 | `1.`、`1)`、`(1)` 模式 |
| 程式碼區塊 | 等寬字型（Courier、Consolas、Monaco 等）＋關鍵字偵測 |
| 表格 | 矩形偵測＋文字對齊啟發式 |
| 超連結 | 轉成 Markdown link |
| 連字號 | 跨行斷字重接 |
| 頁碼 | 從輸出過濾 |
| Drop caps | 大寫首字與後續文字合併 |
| Dot leaders | TOC 式點線收斂為 ` ... ` |

### 3.6 使用案例：smart PDF routing

```
PDF arrives
  → pdf-inspector classifies it (~20ms)
  → TextBased + high confidence?
      YES → extract locally (~150ms), done
      NO  → send to OCR service (2-10s)
```

對約 54% 的文字型 PDF 省下 OCR 成本與延遲。

### 3.7 多語言綁定

Rust 核心 + PyO3（Python）、napi-rs（Node.js/Bun）、wasm-bindgen（瀏覽器 WebAssembly，內嵌 CMaps、無伺服器往返）、CLI（`pdf2md`、`detect-pdf`）。

### 3.8 Benchmark 對照（opendataloader-bench，200 份 PDF，OCR 關閉，0–1 越高越好）

| Engine | Overall | Reading Order (NID) | Tables (TEDS) | Headings (MHS) | Speed (200 docs) |
|---|---|---|---|---|---|
| **pdf-inspector** | **0.875** | **0.915** | **0.814** | 0.788 | **0.470s** |
| liteparse | 0.873 | 0.913 | 0.693 | **0.811** | 0.750s |
| opendataloader | 0.831 | 0.902 | 0.489 | 0.739 | 2.569s |
| pymupdf4llm | 0.735 | 0.886 | 0.401 | 0.424 | 17.117s |
| markitdown | 0.589 | 0.844 | 0.273 | 0.000 | 16.165s |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 對照第二大腦的既有判定

**pdf-inspector 本身在第二大腦中沒有評估紀錄**（判定總表 79 筆無此條目）。但它的直接替代方案 **MarkItDown** 有：

- **MarkItDown（Microsoft）**：`技術/技術評估/Github 一週熱點 112.md` 判定為 **Accept**，理由「感覺不錯用」，`generated.by: human:fatesaikou`、`status: stable`，首見 2026-04-26。→ **這是使用者本人定稿的採用判定**（信任層級：本人寫、stable）。
  - 但注意：該判定是 2026-04-26 對 MarkItDown 0.1.x 的早期版本。pdf-inspector 的 benchmark 顯示 MarkItDown 0.1.5 在 Overall（0.589）、Tables（0.273）、Headings（0.000）明顯落後，且速度慢（16.165s）。**這與使用者「MarkItDown 感覺不錯用」的舊判定存在張力**——舊判定基於早期版本與主觀印象，未含結構化 benchmark 對照。

**與使用者技術取捨準則的對照**（`抽象理解/本質洞察/技術取捨準則.md`，`generated.by: claude-code/opus-5`、`status: draft`，⚠️ 此檔為 AI 草稿，未經本人 review）：

- **原則一「理解優先」**：pdf-inspector 是「不穩定或不熟悉就先自己兜」的典型觸發對象——PDF 抽取是成熟但繁瑣的領域，使用者若想理解本質，會傾向自己兜 MVP 而非直接採用現成工具。**這與「直接採用 pdf-inspector」的結論衝突**，需明確指出。
- **原則二「MVP → Feature 唯一閘門」**：能否進 Feature 取決於「能否影響個人 workflow」。使用者現有 workflow（自動閱讀 Feedly、LearnGhAgent、投資 Dashboard）**沒有 PDF 分類/抽取的進行中專案**（專案現況表 20 筆無此類），因此 pdf-inspector 目前**不具備進 Feature 的閘門條件**。
- **原則三「Reject ≠ 沒價值」**：即使不採用，仍可抽取其「需求理解」與「方案方向」——例如「先分類再決定要不要 OCR」的 smart routing 思路。

### 4.2 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **pdf-inspector**（本標的） | Rust 原生，內容流運算子掃描分類＋幾何/字型啟發式抽取＋Markdown 轉換，單一 `lopdf` 依賴 | 純文字型 PDF；需 Rust 工具鏈或對應語言綁定；接受「掃描型需另接 OCR」 | 對掃描型 PDF 無抽取能力；表格/標題為啟發式，複雜版面可能誤判；專案較新（2026-02 建立） | 文字型 PDF 毫秒級分類與抽取，Overall 0.875、200 份 0.470s |
| **MarkItDown**（Microsoft） | Python 多格式轉 Markdown（PDF/Office/HTML 等），非 PDF 專精 | 需多格式統一轉換；接受較慢速度與較低結構品質 | 表格/標題品質低（TEDS 0.273、MHS 0.000）；200 份 16.165s | 多格式通用轉換；PDF 結構品質與速度皆遜於 pdf-inspector |
| **PyMuPDF4LLM** | Python，基於 MuPDF 的 PDF 轉 Markdown | 需 Python；接受較慢速度 | 表格品質低（TEDS 0.401）；200 份 17.117s | 成熟穩定、API 豐富；結構品質中等 |
| **OCR 服務（Tesseract / 雲端 OCR）** | 影像→文字辨識，處理掃描型 PDF | 掃描型/影像型 PDF；接受 2–10s 延遲與外部服務成本 | 對文字型 PDF 是浪費；有資料外送與成本 | 能處理 pdf-inspector 無法處理的掃描型 PDF |

### 4.3 切入點差異

- **pdf-inspector**：切入點是「**先分類、再決定要不要 OCR**」——用極快的內容流掃描把 54% 的文字型 PDF 留在本地，只把少數掃描型送 OCR。這是成本/延遲優化導向。
- **MarkItDown**：切入點是「**多格式統一**」——一個工具吃 PDF/Office/HTML 等，犧牲單一格式的深度。
- **PyMuPDF4LLM**：切入點是「**成熟穩定**」——基於久經考驗的 MuPDF，API 豐富，但速度與結構品質非最佳。
- **OCR 服務**：切入點是「**覆蓋掃描型**」——解決 pdf-inspector 刻意不碰的影像型 PDF。

### 4.4 對使用者的建議（依其取捨準則）

- 若目的是**理解 PDF 抽取本質**：依「理解優先」原則，自己兜 MVP 更符合其學習策略；pdf-inspector 的架構（detector/extractor 分離、內容流掃描、幾何啟發式）是很好的理解藍圖。
- 若目的是**直接進 workflow**：目前無對應進行中專案，不具備進 Feature 閘門；且 MarkItDown 已被本人 Accept，若要換，需先確認 pdf-inspector 的結構品質優勢（Overall 0.875 vs 0.589）是否值得取代既有採用。
- **衝突點**：pdf-inspector 的 benchmark 顯示 MarkItDown 在 PDF 結構品質上明顯落後，與使用者「MarkItDown 感覺不錯用」的舊判定張力——但舊判定基於早期版本與主觀印象，且 pdf-inspector 專案較新，需實測後才能定論。

---

## 附錄：資料來源

- README：https://github.com/firecrawl/pdf-inspector
- src/types.rs、src/detector.rs（調研時抓取）
- docs/benchmarking.md
- 第二大腦：`技術/技術評估/Github 一週熱點 112.md`（MarkItDown Accept，本人 stable）、`抽象理解/本質洞察/技術取捨準則.md`（AI draft）、`技術/動手做/專案現況表.md`（AI draft）
