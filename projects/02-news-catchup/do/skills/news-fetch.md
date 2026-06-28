# news-fetch skill

> 本 project（新聞分析）的核心 skill：對指定新聞來源執行結構化抓取。

## 可用工具

- `webfetch`：抓取公開網頁（優先使用）
- `bash` + `curl`：抓取 RSS feed、API endpoint
- CDP（port 9222）：遭遇 CAPTCHA / 反爬機制時使用，速度較慢，僅在必要時

## 標準抓取動作

1. **TechCrunch**
   - 首頁：`https://techcrunch.com/`
   - RSS feed：`https://techcrunch.com/feed/`
   - 抓取最新 10～20 則文章標題、摘要、連結

2. **Hacker News**
   - 首頁：`https://news.ycombinator.com/`
   - API：`https://hacker-news.firebaseio.com/v0/topstories.json`
   - 抓取 top 30 文章標題、分數、連結

3. **其他來源**
   - 依使用者指定補充（如 The Verge、Ars Technica、Wired 等）
   - 優先使用 RSS feed，其次為網頁抓取

## 反爬應對

- 一般場景：`webfetch` + `curl`
- 遭遇 CAPTCHA / 反爬：改用 CDP（port 9222）繞過
- CDP 速度慢，僅在 `webfetch` / `curl` 失敗時使用
