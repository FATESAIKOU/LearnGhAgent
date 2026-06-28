# news-fetch SKILL.md

> 新聞爬取與分析 skill，供 Step 2 執行時使用。

## 目的

從指定科技新聞來源爬取最新文章，進行結構化整理與趨勢分析。

## 支援的來源

| 來源 | URL | 爬取方式 | 注意事項 |
|------|-----|----------|----------|
| TechCrunch | https://techcrunch.com | webfetch | 首頁文章列表 |
| Hacker News | https://news.ycombinator.com | webfetch | 首頁 30 則 |
| The Verge | https://www.theverge.com | webfetch | 首頁文章列表 |
| Ars Technica | https://arstechnica.com | webfetch | 首頁文章列表 |

## 執行步驟

1. **確認來源清單**：從 Step 1 意圖理解取得使用者指定的來源
2. **依序爬取**：對每個來源執行 webfetch，取得首頁文章列表
3. **結構化整理**：將每篇文章整理為（標題、來源、連結、摘要）
4. **趨勢歸納**：閱讀所有文章，歸納 2～4 個主要趨勢
5. **產出報告**：依 AGENTS.md 摘要報告格式產出

## 反爬處理

- 優先使用一般 webfetch
- 若遭遇 CAPTCHA 或 403，改用 CDP（port 9222）
- 若仍失敗，在報告中註明該來源無法存取
