# 289_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1：取得 `Open-Dev-Society/OpenStock` 的 repo metadata 與主要文件。標的為 Next.js 全端股票看板（Web app，非 skill）。R1 尚無前輪。C1 目標：metadata、檔案結構、README/API_DOCS/MARKET_SUPPORT 三大文件、架構與資料來源，盤點齊全供 C2 補背景與替代方案。PR body 已知影片無字幕，報告須標記此限制。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh api repos/...` | 取 metadata | stars/license/時序 | 19,686★、2,412 forks、37 open issues、105 watchers、AGPL-3.0、created 2025-09-28、pushed 2026-10-01、size 2599KB、default main、homepage `openstock-ods.vercel.app` |
| topics 查詢 | 定位技術棧 | 標籤清單 | nextjs / shadcn-ui / tailwindcss / stock-market / inngest / coderabbit |
| `git/trees/main?recursive=1` | 取完整結構 | 確認 app 組成 | 202 路徑、未截斷；app/(auth)(root)(marketing)、components、database、lib、scripts、`__tests__`（7 測試檔 vitest） |
| `.../readme`（全文 25,229 字） | 取主文件 | 定位/功能/安裝/資料源 | 見下方整理 |
| `API_DOCS.md`（3,586 字） | 取架構圖 | Inngest 與 AI routing | 4 個 serverless function、Gemini→Siray fallback |
| `MARKET_SUPPORT.md` | 取市場覆蓋 | 一手限制 | 30+ 交易所；免費源僅 US+crypto 可報價 |
| `package.json` | 取依賴/scripts | 版本與指令 | Next 15.5.7、React 19.1、better-auth、mongoose、inngest、nodemailer、vitest |
| `lib/market-data.ts`、`lib/markets.ts`、`lib/market-session.ts` | 讀核心邏輯 | 資料模式與市場定義 | `cached`(3600s) vs `realtime`(15s)；市場陣列；NYSE session 狀態機 |
| `lib/inngest/functions.ts` | 讀自動化 | 確認背景流程 | 歡迎信、週報、股價警示、喚回不活躍用戶 |
| commits/contributors/releases | 活躍度與治理 | 協作規模 | 17 contributors；0 release、0 tag；最新 2026-10-01 merge PR #110 |

**關鍵事實整理**

| 面向 | 內容 |
|---|---|
| 一句定位 | 「昂貴市場平台」的開源替代：即時報價、關注清單、公司資訊、警示，AGPL 永遠免費 |
| 技術棧 | Next.js 15 App Router + React 19 + TS（93.4%）+ Tailwind v4 + shadcn/Radix；Better Auth（email/password + MongoDB adapter）；MongoDB+Mongoose；Inngest（cron/事件/Gemini AI）；Nodemailer；TradingView 嵌入 widget；Finnhub 行情 |
| 核心功能 | 搜尋+Cmd/Ctrl+K、個人 watchlist、個股頁（TradingView 圖表/技術指標/公司財務）、市場總覽（heatmap/quotes/top stories）、個人化 onboarding（國家/目標/風險/偏好產業）、AI 歡迎信、週報 email、深色主題 |
| 免費 vs 付費 | 公開站為 `cached` 模式（報價每小時更新、**無 email 警示**）；`realtime`（15 秒報價、股價警示）屬 **OpenStock Cloud（$5/月，coming soon）** 或自架帶自有 Finnhub key |
| 自動化 | `sign-up-email`（event）、`weekly-news-summary`（cron 週一 09:00）、`check-stock-alerts`（cron */5）、`check-inactive-users`（cron 10:00）；AI 走 Gemini → Siray.ai fallback |
| 市場覆蓋 | 30+ 交易所；Finnhub 免費僅 US 股票+crypto 可報價（其他 403）；TradingView 免費對新興市場（NSE 等）有封鎖；非美即時資料延遲 15+ 分 |
| 資料模型 | MongoDB collections：`users`、`watchlists`、`alerts`；watchlist 為 per-user unique symbol |
| 治理/授權 | AGPL-3.0（含 web service 部署須開源）；17 contributors（主導 ravixalgorithm）；無 release/tag；有資安揭露信箱 |
| 資金模式 | GitHub Sponsors 分級 $5/$25/$100/$500；OpenStock Cloud 訂閱補貼主機；曾由 Siray.ai 贊助 |
| 血緣 | README 明載源自 Adrian Hajdin（JavaScript Mastery）Stock Market App 教學 |

**需在報告標記的點**

| 項目 | PR body／影片說法 | 一手實況 | 判定 |
|---|---|---|---|
| 「永遠免費」 | forever free | 公開站免費但為 hourly cached；realtime+警示屬 $5/月 Cloud | 免費與付費功能須並列，不可只寫 forever free |
| 影片觀點 | 影片來源 133 期 | transcripts disabled，逐字稿不可得 | 報告標記限制，不臆測影片內容 |
| 替代昂貴平台 | alternative to expensive platforms | 免費源本身延遲、非美資料受限，需自有 key | §1 問題描述須指出「資料品質」界線 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Metadata 完整性 | stars/license/語言/時序/topics/releases/contributors | 完整（無 release/tag） |
| 文件覆蓋率 | README + 2 子文件 + tree + 5 核心原始檔 | 足以支撐報告 §1–§3 |
| 機制理解 | 資料模式 cached/realtime、Inngest 4 流程、AI fallback、市場 session | 清晰 |
| 免費/付費界線 | README + market-data.ts 交叉核對 | 已釐清（hourly vs 15s；警示屬 Cloud） |
| 背景脈絡 | 通用領域背景、替代方案（Yahoo Finance、Ghostfolio 等） | 留 C2 |
| 影片資料 | PR body 聲明 | 確認逐字稿不可得，待報告標記 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件深度 | 只讀 README／加讀子文件與核心碼／逐頁精讀 | README + API_DOCS + MARKET_SUPPORT + 5 核心檔 | C1 為 metadata 與主要文件盤點，深入邏輯留 C2 |
| 是否 clone 執行程式 | 執行驗證／純靜態閱讀 | 純靜態 | 需 Finnhub key 與 MongoDB，非 C1 必要 |
| 免費宣稱的處理 | 照抄 forever free／並列 cached vs Cloud | 並列 cached 與 Cloud 兩層 | 一手碼證實功能分層，避免誤導 |
| 「替代昂貴平台」定位 | 全盤接受／指出資料源限制 | 以 MARKET_SUPPORT 補上界線 | 一手文件明確列出免費源延遲與封鎖 |

## 交接給 C2

- 補通用背景：免費行情 API 的延遲/授權限制、TradingView embed 商業條款、Better Auth/Inngest 在 OSS 專案的角色。
- 補替代方案：Yahoo Finance / Google Finance、Ghostfolio、Maybe、自有 SBI Dashboard（MyBrain 同軸）、付費 Terminal（Bloomberg）做 DA 表。
- 已可用來源：MARKET_SUPPORT 覆蓋表、API_DOCS 架構圖、MyBrain 投資 Dashboard 對照組。
