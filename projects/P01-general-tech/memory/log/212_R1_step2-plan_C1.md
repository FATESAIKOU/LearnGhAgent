# 212_R1_step2-plan_C1.md

## 狀況理解

R1 首次調研，標的為 `firecrawl/pdf-inspector`（Firecrawl 開源的 PDF 分類與抽取工具）。C1 為 Step 2 第一個 sub-step：取得 repo metadata 與主要文件，作為後續 C2（背景脈絡、替代方案）與 C3（收斂撰寫報告）的資料基礎。此階段純取資料，不評判好壞。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 do/skills/document/SKILL.md | 確認標準調研動作流程 | 依規範順序執行 | 流程確認：metadata → 主要文件 → 背景脈絡 → 收斂 |
| `gh repo view firecrawl/pdf-inspector --json ...` | 取得 repo metadata | 確認語言、license、stars、更新時間 | 13753 stars、940 forks、MIT、主要語言 Rust（2928558 bytes，遠超其餘）、created 2026-02-06、default branch main、desc：Fast Rust library for PDF inspection/classification/extraction |
| `gh api .../contents/` 與 `/docs` `/src` | 盤點 repo 結構 | 定位關鍵子文件 | 根：README、Cargo.toml、docs/、examples/、src/、napi/、wasm/、pyproject.toml；docs/ 含 rust-api、python、benchmarking、publishing、debugging；src/ 含 detector.rs、types.rs、extractor/、tables/、markdown/、process_mode.rs、tounicode.rs、glyph_names.rs、bin/ |
| `curl` 抓取 README.md、src/types.rs、src/detector.rs、docs/benchmarking.md | 擷取主要文件內容 | 掌握功能、架構、分類機制、API | README 275 行：架構圖、分類機制（Tj/TJ 與 Do 運算子掃描）、Markdown 轉換規則表、benchmark 對照表（pdf-inspector 0.875 居首）、smart routing 流程；types.rs 414 行：TextItem/TextLine/PdfRect/ItemType、bold/italic/underline/strikeout 幾何偵測；detector.rs 3709 行：分類與 scan strategy；benchmarking.md 62 行：paired harness 說明 |
| `gh api .../languages` 與 `/releases` | 補查語言占比與版本 | 佐證主要語言、確認活躍度 | languages：Rust 為絕對多數；releases 查無輸出（可能無 release 標籤或 API 限制，不阻礙調研） |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo 身份 | `gh repo view` 欄位 | 已確認 owner/repo、desc、license(MIT)、語言(Rust)、stars(13753)、更新(2026-08-09) |
| 核心文件完整性 | 讀取 README + types.rs + detector.rs + benchmarking | 架構、分類原理、API（Python/Node/WASM/Rust/CLI）、benchmark 資料齊備 |
| 技術邊界 | 從 README/desc | 純 Rust、無 ML 模型、單一依賴 lopdf；「不靠 OCR」為核心賣點；偵測 300+ 頁在毫秒級 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 抓取範圍 | (A) 僅 README (B) README + src 關鍵檔 + docs | B | README 已含架構與分類機制，但需 src/types.rs 補 TextItem 細節、detector.rs 補分類實作、benchmarking.md 補驗證方法，才能支撐報告 §1-4 |
| 是否抓全文 repo | (A) 全 clone (B) 針對性抓 raw 檔 | B | C1 只需 metadata 與關鍵文件，targeted raw 抓取節省時間；完整 source 留待 C2/C3 有需要再補 |
| 資料落地 | (A) 直接寫 log (B) 暫存 /tmp/opencode 供後續 step 用 | B | README/types/detector/benchmark 暫存 /tmp/opencode，後續 C2/C3 直接讀取，避免重複抓取 |
