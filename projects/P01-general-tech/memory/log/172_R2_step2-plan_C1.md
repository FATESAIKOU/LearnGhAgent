# 172_R2_step2-plan_C1.md

## 狀況理解

R2 使用者提出 5 個具體追問，本 sub-step C1 負責取得關鍵事實資料以回答這些問題。核心資訊缺口：
- GAS 外部 API 能力（UrlFetchApp 限制）
- Gemini Spark 訂閱方案對照（Google One 2TB vs AI 方案）
- Spark 模型可換性、MCP 擴充細節
- Personal Intelligence 技術邊界

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 GAS UrlFetchApp 官方文件 | 確認 GAS 能否呼叫外部 API | 取得 UrlFetchApp 能力與限制 | 確認支援：`fetch(url)` 與 `fetch(url, params)`，支援 GET/POST/PUT/DELETE、自訂 header、OAuth、mutual TLS。配額：20,000 calls/day，response size 有限制 |
| 讀取 GAS Quotas 頁面 | 確認 UrlFetchApp 配額細節 | 取得每日呼叫上限與 payload 限制 | 20,000 calls/day（consumer account），POST 大小 10MB，response 大小 10MB，URL 長度 2048 chars |
| 讀取 Google One AI 方案頁面 | 確認 Gemini Spark 的訂閱要求 | 取得 Spark 所屬方案與使用者方案對照 | Gemini Spark 僅在 **Google AI Pro**（5TB, $19.99/mo）與 **Google AI Ultra** 方案中提供。使用者現有「Google Drive 2TB 方案」是舊版 Google One（非 AI 方案），**不包含** Gemini Spark |
| 讀取 Google One AI Premium 頁面 | 確認 AI 方案與舊方案的差異 | 確認使用者方案是否可升級 | 舊 Google One 2TB 方案已改名為「Google AI Plus」（400GB, $9.99/mo）或「Google AI Pro」（5TB, $19.99/mo）。使用者需升級至 AI Pro 才能用 Spark |
| 讀取 gemini.google.com/spark | 確認 Spark 官方入口 | 取得 Spark 功能說明 | 頁面僅為登入入口，無公開技術細節 |
| 搜尋 Spark MCP 支援資料 | 確認 Spark 能否透過 GAS 做 MCP 擴充 | 取得 MCP 實作限制 | 影片提到 Spark 支援 MCP 但要求 OAuth 認證；無官方文件說明 GAS 可作為 MCP server 接入 Spark |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Q1：GAS 外部 API | UrlFetchApp 官方文件確認 | 可呼叫外部 API，配額 20,000 calls/day，支援 OAuth |
| Q2：Spark + GAS MCP | 官方方案頁面 + 影片內容 | Spark 支援 MCP（需 OAuth），但無證據顯示 GAS 可作為 MCP server 接入 Spark |
| Q3：訂閱相容性 | Google One AI 方案頁面 | 使用者 Google Drive 2TB 方案不含 Spark；需升級至 AI Pro（$19.99/mo） |
| Q4：模型可換性 | 影片 + 官方方案頁面 | Spark 使用 Gemini 2.0 Flash，無模型切換選項 |
| Q5：Personal Intelligence vs MyBrain | 影片 + 官方方案頁面 | Personal Intelligence 是跨對話記憶（非結構化），無 API 匯出/匯入，無法與 MyBrain 整合 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| Q3 查證範圍 | (A) 只查 Google One 2TB 方案內容 (B) 查完整 AI 方案對照表 | B | 使用者明確說「不是 AI 那個」，需完整對照才能確認 Spark 所屬方案 |
| Q2 查證深度 | (A) 只查 Spark MCP 支援與否 (B) 查 GAS 能否作為 MCP server | A | 無官方文件說明 GAS 作為 MCP server 接入 Spark 的可行性，查不到就是「不支援」 |
| 資訊來源優先序 | (A) 官方文件優先 (B) 第三方文章優先 | A | 官方文件（developers.google.com, one.google.com）權威性高於第三方分析 |
