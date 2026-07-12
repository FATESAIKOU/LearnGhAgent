# AI Job Search — 技術分析報告

> 分析標的：MadsLorentzen/ai-job-search（GitHub, MIT License, 20.9k stars, 6.1k forks）
> 核心定位：基於 Claude Code 的 AI 求職應用框架

---

## 1. 這個技術解決什麼問題？

**解決的問題：** 求職過程中大量重複性、高客製化需求的文書工作——針對每個職缺手動調整履歷、撰寫求職信、評估職缺匹配度、準備面試——這些工作耗時且容易出錯，且每次應用都需要重複相同流程。

具體而言，該框架針對以下子問題：

| 子問題 | 具體痛點 |
|--------|---------|
| 履歷客製化 | 每份職缺需要重新排列經歷、調整關鍵字、控制頁數（2頁），手動做耗時且易遺漏 |
| 求職信撰寫 | 每封求職信需針對公司與職位撰寫開場、連結自身經歷，格式與語氣需一致 |
| 職缺匹配評估 | 求職者常花時間投遞不適合的職缺，缺乏結構化評估框架 |
| 面試準備 | 面試前需回顧職缺、公司背景、準備 STAR 範例，資訊分散 |
| 求職進度追蹤 | 多個職缺的投遞狀態、面試階段、結果缺乏系統性記錄 |
| PDF 排版驗證 | LaTeX 編譯後的 PDF 常有分頁錯誤、字型問題，手動檢查費時且易遺漏 |
| ATS 相容性 | 求職系統（Applicant Tracking System）讀取 PDF 文字層而非渲染畫面，LaTeX 產生的 PDF 常出現文字層損毀 |

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **LaTeX 分頁行為不可預測**：`.tex` 檔案看起來正確，但編譯後可能出現職稱孤行（title 在頁底、bullet 在次頁）、求職信溢出到第 2 頁、項目符號字型與內文不一致等問題。這是 LaTeX 排版引擎的固有特性，無法在編譯前完全預測。
- **ATS 讀取文字層而非渲染層**：LaTeX 可能產生 PDF 文字層損毀——圖示字型（icon glyph）提取為 `MOBILE-ALT`、`Envelope` 等字型名稱而非實際文字，多欄排版導致閱讀順序錯亂，聯絡資訊僅存在於超連結目標中而對 ATS 不可見。
- **求職流程的結構化缺失**：多數求職者缺乏系統性的職缺評估框架，導致時間花費在不適合的職缺上。

### 通用技術背景（文章中未明確提及但為必要脈絡）

- **LLM 作為工作流引擎的興起**：Claude Code 等 CLI 工具讓 LLM 不僅是對話介面，而是可執行多步驟工作流的 agent。透過 `.claude/commands/` 與 `.claude/skills/` 可定義自訂指令與技能，使 LLM 能操作檔案系統、執行 shell 指令、編譯 LaTeX、讀寫 PDF。
- **fork-and-own 模式**：求職工具本質上需要高度個人化（個人資料、市場特定職缺平台），上游維護通用模板、下游 fork 加入個人資料與市場特定整合，是此類專案常見的架構模式。
- **LaTeX 在學術/技術領域的普及**：許多技術人員的履歷使用 LaTeX（moderncv 等模板），但 LaTeX 的編譯流程（.tex → PDF）需要特定工具鏈（lualatex、xelatex）與套件管理，且不同發行版（MiKTeX、TeX Live）行為不一致。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 整體架構

```
使用者 fork repo → /setup 建立個人檔案 → /scrape 搜尋職缺 → /rank 排序 → /apply 投遞 → /interview 面試準備 → /outcome 記錄結果 → 回饋至 /setup 校準
```

框架以 **Claude Code** 為執行引擎，透過 `.claude/commands/` 定義 10 個自訂指令（`/setup`, `/scrape`, `/apply`, `/rank`, `/interview`, `/outcome`, `/expand`, `/upskill`, `/add-template`, `/add-portal`, `/reset`），每個指令對應一個 `.md` 檔案，內含 LLM 可執行的逐步工作流。

### 3.2 核心機制：/apply 的 drafter-reviewer 工作流

`/apply` 是框架的核心，採用 **雙 agent 協作** 模式：

```
Step 0: Parse Input
  └─ URL → WebFetch 取得職缺內容 / 純文字直接使用
  └─ 提取：公司名、職稱、部門、地點、語言

Step 1: DRAFTER - Evaluate Fit
  └─ 讀取 01-candidate-profile.md + 04-job-evaluation.md
  └─ 執行 salary_lookup.py（若設定）
  └─ 產出：技能匹配 / 經驗匹配 / 行為匹配 / 薪資基準 / 整體分數
  └─ 詢問使用者是否繼續

Step 2: DRAFTER - Draft CV + Cover Letter
  └─ 讀取 03-writing-style.md + 05-cv-templates.md + 06-cover-letter-templates.md
  └─ 產生客製化 LaTeX 檔案（cv/main_<company>.tex + cover_letters/cover_<company>_<role>.tex）
  └─ CV：英文、moderncv/banking 格式、2 頁
  └─ 求職信：與職缺語言一致、cover.cls 模板、1 頁

Step 3: REVIEWER - Research & Critique
  └─ 以 Agent tool 產生第二個 Claude agent（全新 context）
  └─ 研究公司背景（WebSearch + WebFetch）
  └─ 讀取 01~04 技能檔案（不含模板檔案）
  └─ 回傳：Part A（結構化編輯 JSON）+ Part B（敘述性建議）

Step 4: DRAFTER - Revise
  └─ 直接套用 Part A 的 Edit 指令
  └─ 依 Part B 建議手動調整

Step 5: Compile & Inspect PDFs（強制執行）
  └─ lualatex 編譯 CV、xelatex 編譯求職信
  └─ 視覺檢查：頁數、孤行、字型一致性
  └─ 迭代修正直到通過
  └─ ATS 驗證：pdftotext 提取文字層，檢查關鍵字覆蓋率

Step 6: Present Final Output
  └─ 執行完整驗證清單
  └─ 摘要關鍵客製化決策
```

### 3.3 關鍵技術細節

#### PDF 驗證迴圈

```
編譯 → Read PDF（視覺檢查）→ 發現問題 → 編輯 .tex → 重新編譯 → 再次檢查 → 通過
```

常見問題與對應修正：

| 問題 | 修正方式 |
|------|---------|
| CV 職稱孤行 | `\needspace{5\baselineskip}` 置於 `\cventry` 前 |
| CV 溢出第 3 頁 | `\enlargethispage{2-3\baselineskip}` 或 relevance-weighted cutting |
| 求職信溢出第 2 頁 | 依相關性權重裁切內容 |
| 項目符號字型不一致 | 關閉 `\lettercontent{}`，以 `\fontspec` 包裹 `itemize` |
| 編譯失敗 | 修正 LaTeX 語法錯誤後重新編譯 |

#### Relevance-weighted cutting

當 CV 超過 2 頁時，不機械地從「最舊經歷」開始裁切，而是對每個條目評分：

```
score = w1 * relevance_to_posting + w2 * uniqueness_in_doc + w3 * narrative_load
```

- `relevance_to_posting`：該條目命中職缺關鍵字的程度
- `uniqueness_in_doc`：該條目是否在其他地方重複出現
- `narrative_load`：求職信是否依賴該條目

裁切最低分條目，不考慮所屬章節。

#### ATS 驗證

```
pdftotext -layout main_<company>.pdf → main_<company>.txt
```

檢查項目：

1. **文字層完整性**：無 `(cid:NNN)` 標記、無 `�` 替代字元
2. **聯絡資訊可讀性**：Email 與電話以純文字存在（非僅圖示或超連結）
3. **閱讀順序**：提取文字順序與視覺順序一致
4. **關鍵字覆蓋率**：比對職缺關鍵字在提取文字中的出現情況

關鍵字覆蓋率報告格式：

| 關鍵字 | 優先級 | 狀態 | 備註 |
|--------|--------|------|------|
| Python | required | covered | 出現於 experience bullets |
| Kubernetes | preferred | missing (gap) | 誠實標記為缺口 |
| CI/CD | preferred | synonym-only | 使用 "automated deployment" |

#### 雙 agent 分離的 token 效率設計

- Reviewer agent 以 inline 方式接收草稿內容，不重新讀取檔案
- 驗證清單僅在最後執行一次，不重複
- Reviewer 專注於內容 critique，不執行驗證

### 3.4 個人檔案系統（7 個 skill 檔案）

| 檔案 | 內容 | 用途 |
|------|------|------|
| `01-candidate-profile.md` | 學歷、經歷、技能、證照、出版 | 履歷與求職信素材 |
| `02-behavioral-profile.md` | PI/DISC/性格評估 | 確保求職信語氣與個人特質一致 |
| `03-writing-style.md` | 語氣、結構、Do/Don't | 維持文件風格一致 |
| `04-job-evaluation.md` | 評分框架（技能/經驗/文化/地點/職涯） | 職缺匹配度評估 |
| `05-cv-templates.md` | LaTeX CV 結構 + 客製化規則 | 履歷產生 |
| `06-cover-letter-templates.md` | LaTeX 求職信模板 | 求職信產生 |
| `07-interview-prep.md` | STAR 範例 + 面試框架 | 面試準備 |

### 3.5 三種 onboarding 路徑（/setup）

| 路徑 | 適用情境 | 運作方式 |
|------|---------|---------|
| Path A: Documents folder | 已有 CV、LinkedIn 匯出、文憑等素材 | 讀取 `documents/` 內檔案，交叉比對一致性，合併至 skill 檔案 |
| Path B: Single CV import | 只有一份 CV | 讀取單一 CV，提取結構化資料，追問遺漏部分 |
| Path C: Interview mode | 從零開始 | 逐步問答收集所有資訊 |

### 3.6 貢獻政策（fork-and-own 模式）

```
上游（MadsLorentzen/ai-job-search）
  ├─ 通用模板（universal template）
  ├─ 市場無關的功能（/add-template, /add-portal）
  └─ 穩定性修正、CI、文件

下游（使用者的 fork）
  ├─ 個人資料（placeholders → 實際資料）
  ├─ 市場特定職缺平台整合
  └─ 客製化模板
```

合併標準：只合併 universal 功能，市場特定內容導向 fork。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|---------|-------------|---------------|-----------------|
| **ChatGPT / Claude 對話式 prompt** | 使用者手動複製職缺描述、貼上履歷、撰寫 prompt 要求 LLM 產生客製化履歷與求職信 | 有 LLM 帳號、能撰寫有效 prompt | 每次需手動複製貼上、無自動化流程、無 PDF 驗證、無 ATS 檢查、無結構化評估框架 | 可產生客製化內容，但品質取決於 prompt 品質，流程無重複性保證 |
| **Rezi.ai / Kickresume / 其他 AI 履歷工具** | SaaS 平台：上傳履歷 → 輸入職缺連結 → AI 自動客製化履歷與求職信 | 付費訂閱、上傳個人資料至第三方伺服器 | 資料隱私風險（履歷上傳至外部伺服器）、模板選擇受限、無法自訂 LaTeX 排版、無面試準備整合 | 一鍵產生客製化履歷，但缺乏端到端工作流（搜尋→評估→投遞→追蹤） |
| **Auto-Job-Apply / Simplify.jobs / 自動投遞工具** | 自動化腳本：監控職缺 → 自動填寫申請表 → 自動投遞 | 需處理各求職平台的反爬機制、需維護登入狀態 | 違反多數求職平台 ToS、帳號可能被封鎖、投遞品質無法控制、無客製化 | 大量投遞但品質低，適合數量優先策略 |
| **手動 LaTeX 模板 + 版本控制** | 維護多份 `.tex` 檔案（每職缺一份），手動編輯與編譯 | 熟悉 LaTeX、有版本控制習慣 | 耗時、容易遺漏關鍵字、無結構化評估、無 ATS 驗證、無面試準備整合 | 完全控制排版，但流程效率低 |

### 切入點差異分析

| 面向 | ai-job-search | ChatGPT prompt | Rezi.ai | Auto-Job-Apply | 手動 LaTeX |
|------|--------------|---------------|---------|---------------|-----------|
| **自動化程度** | 高（端到端工作流） | 低（每次手動） | 中（單一功能） | 高（但品質低） | 低 |
| **客製化深度** | 高（drafter-reviewer + PDF 驗證） | 中（取決於 prompt） | 中（模板限制） | 低（批量模板） | 高（完全控制） |
| **資料隱私** | 高（本地執行） | 中（API 傳輸） | 低（上傳至 SaaS） | 低（需登入各平台） | 高（本地檔案） |
| **ATS 相容性** | 有（pdftotext 驗證） | 無 | 有（平台內建） | 無 | 無（需手動檢查） |
| **面試準備** | 有（/interview） | 無 | 無 | 無 | 無 |
| **求職追蹤** | 有（/outcome + tracker） | 無 | 部分（平台內） | 有（投遞記錄） | 無 |
| **學習成本** | 中（需 Claude Code + LaTeX） | 低 | 低 | 低 | 中高 |
| **市場特定** | 需自行整合（/add-portal） | 無限制 | 全球（平台內建） | 各平台支援 | 無限制 |

### 核心差異總結

ai-job-search 的獨特定位在於：

1. **本地執行**：所有資料與處理都在使用者機器上，無第三方伺服器儲存個人資料
2. **端到端工作流**：從職缺搜尋、匹配評估、文件產生、PDF 驗證、ATS 檢查、面試準備到結果追蹤，完整覆蓋求職生命週期
3. **PDF 驗證迴圈**：不僅產生 `.tex`，還編譯、視覺檢查、迭代修正，確保最終 PDF 符合排版要求
4. **ATS 文字層驗證**：直接檢查 ATS 解析器實際看到的內容，而非僅檢查渲染畫面
5. **fork-and-own 模式**：上游維護通用框架，下游 fork 加入個人資料與市場特定整合，避免 PR 氾濫
