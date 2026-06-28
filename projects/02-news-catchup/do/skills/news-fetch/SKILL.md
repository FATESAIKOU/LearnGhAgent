# news-fetch SKILL.md

> 新聞抓取 skill：定義如何從各科技新聞來源取得內容。

## 支援的來源與方法

| 來源 | 方法 | 備註 |
|------|------|------|
| Hacker News | `https://hacker-news.firebaseio.com/v0/topstories.json` (API) + 逐篇抓取 item | 免費、無反爬 |
| TechCrunch | `https://techcrunch.com/wp-json/wp/v2/posts` (REST API) 或 RSS `https://techcrunch.com/feed/` | API 有限速 |
| The Verge | RSS `https://www.theverge.com/rss/index.xml` | 標準 RSS |
| Ars Technica | RSS `https://feeds.arstechnica.com/arstechnica/index` | 標準 RSS |

## 通用流程

1. 確認來源可用性（HTTP 200）
2. 抓取文章列表（最近 24h 或指定時間範圍）
3. 對每篇文章抓取標題、連結、摘要、發布時間
4. 若 API/RSS 不可用，嘗試 webfetch 首頁
5. 若 webfetch 被阻擋，使用 CDP（port 9222）
