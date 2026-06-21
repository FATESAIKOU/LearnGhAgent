# document skill

> 本 project（技術解析）的核心 skill：對給定技術標的執行結構化文件調研。

## 可用工具

- `webfetch`：抓取公開網頁（優先使用）
- `gh api` / `gh repo view`：取得 GitHub repo metadata（stars、license、預設分支、更新時間）
- `bash` + `curl`：抓取 raw 檔案、API endpoint
- CDP（port 9222）：遭遇 CAPTCHA / 反爬機制時使用，速度較慢，僅在必要時

## 標準調研動作

1. **取得 repo metadata**（若是 GitHub repo）
   - `gh repo view <owner>/<repo> --json nameWithOwner,stargazerCount,licenseInfo,defaultBranchRef,updatedAt,description`
2. **擷取主要文件**
   - README.md（raw）
   - 關鍵子文件（如 SKILL.md、docs/、spec/ 等，視結構而定）
3. **補查背景脈絡**
   - 從網路搜尋技術背景、歷史因素、替代方案
4. **收斂撰寫**
   - 依 AGENTS.md 的分析報告格式（5 點）撰寫

## 反爬應對

- 一般場景：`webfetch` + `curl`
- 遭遇 CAPTCHA / 反爬：改用 CDP（port 9222）繞過
- CDP 速度慢，僅在 `webfetch` / `curl` 失敗時使用