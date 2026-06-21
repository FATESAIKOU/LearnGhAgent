# 22_R1_step2-plan_C1.md

## 狀況理解

使用者要求調研 GitHub repo `anthropics/courses`。Step 1 已確認技術標的為該 repo，無附帶條件。本 sub-step 需取得 repo metadata、README 與關鍵子文件，並補查背景脈絡。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view anthropics/courses --json ...` | 取得 repo metadata | 獲得 stars、license、分支、更新時間、描述 | stars=21930, license=Other, defaultBranch=master, updatedAt=2026-06-21, description="Anthropic's educational courses" |
| `gh api repos/.../contents/README.md` + base64 decode | 取得 README.md 內容 | 了解 repo 整體說明 | 確認 5 門課程：API fundamentals、Prompt engineering、Real world prompting、Prompt evaluations、Tool use |
| `gh api repos/.../contents/` | 列出 repo 根目錄結構 | 了解文件組織方式 | 5 個課程目錄 + LICENSE、.gitignore、README.md |
| 逐一列出 5 個課程子目錄內容 | 了解各課程內部結構 | 確認各課程包含 README.md 與多個 Jupyter notebook | 每個課程均有 README.md 與多個 .ipynb 檔案 |
| `curl` 取得 5 個課程的 README.md | 取得各課程詳細說明 | 了解各課程範圍與學習目標 | 全部取得成功，內容涵蓋課程目標、章節結構、前置需求 |
| `webfetch` 嘗試 Anthropic docs | 補查 Anthropic 技術背景 | 了解 Claude API 生態系 | 404（docs.anthropic.com 路徑變更），未取得 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Repo metadata | `gh repo view` JSON 輸出 | 完整取得（21930 stars, master branch, 2026-06-21 更新） |
| README.md | 內容解析 | 5 門課程，建議依序學習 |
| 子文件結構 | 目錄列表 | 5 個課程目錄，每目錄含 README.md + .ipynb 檔案 |
| 各課程 README | 內容解析 | 全部取得，涵蓋 API 基礎、提示工程、真實世界提示、評估、工具使用 |
| Anthropic 背景 | webfetch docs.anthropic.com | 404，需另尋來源 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 子文件擷取範圍 | 全部 notebook 內容 vs 僅 README | 僅 README | README 已涵蓋課程範圍與目標，notebook 為實作細節，Step 2 後續可視需要補抓 |
| 背景查詢方式 | webfetch docs.anthropic.com vs 搜尋引擎 | 先試 docs.anthropic.com | 官方文件為最可靠來源，但 404 表示路徑已變更，後續需改用搜尋引擎補查 |
