# 22_R2_step2-plan_C1.md

## 狀況理解

使用者要求調研 GitHub repo `anthropics/courses`。Step 1 已確認技術標的為該 repo，無附帶條件。本 sub-step C1 依 SKILL.md 標準調研動作執行：取得 repo metadata、擷取 README.md 與關鍵子文件、補查背景脈絡。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view anthropics/courses --json ...` | 取得 repo metadata | 取得 stars、license、default branch、更新時間、描述 | 成功取得：stars=21930, forks=2325, license=Other, defaultBranch=master, language=Jupyter Notebook, 描述="Anthropic's educational courses" |
| `webfetch` README.md (raw) | 擷取主要文件 | 取得 repo 說明與課程列表 | 成功取得：5 門課程（API fundamentals、Prompt engineering、Real world prompting、Prompt evaluations、Tool use） |
| `webfetch` GitHub API `/contents/` | 取得 repo 目錄結構 | 確認目錄層級與子目錄 | 成功取得：5 個課程子目錄 + LICENSE + .gitignore |
| `webfetch` 各子課程 README.md (x5) | 擷取關鍵子文件 | 了解各課程內容範圍 | 全部成功取得，各課程範圍明確 |
| `webfetch` GitHub repo page (HTML) | 補查背景脈絡 | 確認 repo 頁面資訊（releases、contributors、languages） | 成功取得：無 release、Jupyter Notebook 99.9% + Python 0.1%、59 commits |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Repo metadata 完整性 | 確認 stars、forks、license、language、description、default branch | 完整取得，無缺失 |
| 主要文件完整性 | README.md 內容可讀且完整 | 5 門課程列表與描述完整 |
| 子文件完整性 | 5 個子目錄 README.md 皆可取得 | 全部成功，無 404 |
| 背景脈絡 | 語言分布、commits 數、releases | 無 release、59 commits、主要為 Jupyter Notebook |
| 反爬狀況 | 所有 webfetch 請求 | 無遭遇 CAPTCHA 或反爬，無需使用 CDP |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| README.md 抓取分支 | `main` 或 `master` | `master` | GitHub API 回傳 defaultBranchRef 為 `master` |
| 子文件範圍 | 僅 README.md 或深入各課程 notebook | 僅各子目錄 README.md | SKILL.md 要求「關鍵子文件」，README 已涵蓋課程範圍與結構，notebook 內容為實作細節，留待 Step 2 C2 分析時視需要深入 |
| 背景脈絡補查方式 | 搜尋 Anthropic 官方文件或僅依 repo 內容 | 僅依 repo 內容 | repo 本身即為教育課程，README 已提供足夠背景；Anthropic API 與 Claude 模型背景可於 Step 2 C2 分析時補查 |
