# OpenStock — 開源股票看板（Open-Dev-Society/OpenStock）

> 調研標的：https://github.com/Open-Dev-Society/OpenStock
> 調研日期：2026-10-05（repo metadata 實查日）
> 一句定位：**OpenStock 是「昂貴市場平台」的開源替代品，用 Next.js 自架一個含即時報價、關注清單、公司資訊與價格警示的股票看板，程式碼以 AGPL-3.0 公開。**
> 血緣：README 明載源自 Adrian Hajdin（JavaScript Mastery）的 Stock Market App 教學專案，再由社群擴充成獨立專案。

## 全報告的資料限制（必讀）

| 限制 | 內容 | 影響 |
|---|---|---|
| 影片逐字稿不可得 | 來源為 GitHub 一周熱點 133 期（https://youtu.be/gv9IGo9qqZM），該影片 **無可取得字幕軌（transcripts disabled）** | 本報告不含影片的觀點與示範內容；亦無法確認影片實際展示了哪些功能 |
| 影片描述連結被截斷 | PR body 原文只列名稱與被截斷連結 | repo 全名由搜尋補齊為 Open-Dev-Society/OpenStock |
| 數字時序 | PR body 記 19,680 stars；本報告 2026-10-05 實查為 **19,686 stars**（差異來自查詢時間差） | 引用 stars 時標註實查日 |

**repo metadata（2026-10-05 實查 GitHub API）：**

| 項目 | 值 |
|---|---|
| 描述 | OpenStock is an open-source alternative to expensive market platforms. Track real-time prices, set personalized alerts, and explore detailed company insights — built openly, for everyone, forever free. |
| 主要語言 | TypeScript（約 93.4%） |
| Stars / Forks | 19,686 / 2,412 |
| License | AGPL-3.0 |
| 建立 / 最新 push | 2025-09-28 / 2026-10-01 |
| Release / Tag | 0 / 0 |
| Contributors | 17（主導帳號 ravixalgorithm） |
| 官網 | openstock-ods.vercel.app |
| Topics | nextjs、shadcn-ui、tailwindcss、stock-market、inngest、coderabbit |

---

## 1. 這個技術解決什麼問題？

**OpenStock 要解決的是「專業市場資訊平台價格高昂、且封閉」的問題。** 具體而言：Bloomberg Terminal、Wind 一類專業終端以年費數萬美元提供即時行情、公司資料與分析工具；對個人使用者而言，這個價格帶不可及。OpenStock 主張以開源、自架、免費的方式，提供一個可用的替代入口。

**它提供的具體能力：**

| 能力 | 內容 |
|---|---|
| 即時報價 | 美股＋加密貨幣報價（Finnhub 免費源）；其餘市場由 TradingView 嵌入 widget 呈現 |
| 關注清單 | 個人 watchlist，per-user unique symbol 儲存於 MongoDB |
| 公司深度資訊 | 個股頁含 TradingView 圖表、技術指標、公司財務 |
| 價格警示 | 股價觸及目標價時發送通知 |
| 市場總覽 | heatmap、quotes、top stories |
| 個人化 | onboarding 問卷（國家／目標／風險／偏好產業）驅動 AI 歡迎信與週報 |

### 問題描述中含糊或與一手實況不符之處

| 宣稱 | 一手實況（來自 repo 文件與原始碼） | 需釐清處 |
|---|---|---|
| alternative to **expensive** market platforms | 未指明對標對象與價格帶；公開免費源（Finnhub free、TradingView embed）本身有覆蓋與延遲限制 | 「昂貴」的比較基準未定義 |
| for everyone, **forever free** | 公開站為 `cached` 模式（報價每小時更新、**無 email 警示**）；`realtime`（15 秒報價、股價警示）屬 **OpenStock Cloud（$5/月，coming soon）**，或自架並帶自有 Finnhub key | 「免費」需區分公開站層與 Cloud 層，兩者功能不同 |
| Track **real-time** prices | 非美國市場即時資料延遲 15 分鐘以上；Finnhub 免費源只有 US 股票與 crypto 可報價（其他交易所回 403） | 「real-time」的市場範圍限於美國與加密貨幣 |
| 影片觀點 | 影片逐字稿不可得 | 無法確認影片示範了哪些功能 |

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 repo 文件明確提到的背景

| 背景因素 | 出處 | 說明 |
|---|---|---|
| 行情資料本身是授權商品 | README、MARKET_SUPPORT.md | 免費 API（Finnhub free）只覆蓋美國股票與加密貨幣；其他交易所報價回 403 |
| TradingView 嵌入的限制 | MARKET_SUPPORT.md | 免費嵌入對新興市場（如印度 NSE）封鎖；倫敦、東京、香港、韓國、台灣等地 K 線圖被 block，僅財務／技術／profile 可用 |
| 非美即時資料延遲 | README | 「Market data may be delayed based on provider rules and your configuration」 |
| 專業平台成本高 | README 定位句 | 直接以「替代昂貴市場平台」為立項理由 |
| 社群專案非券商 | README | 「community-built and not a brokerage… Nothing here is financial advice」 |
| 資金需自籌 | README | GitHub Sponsors 分級（$5/$25/$100/$500）＋ OpenStock Cloud 訂閱補貼主機；曾由 Siray.ai 贊助 |

### 2.2 通用技術背景

| 面向 | 說明 |
|---|---|
| 金融行情是分層付費市場 | 交易所向資料供應商收取授權費，供應商再分層販售（延遲報價免費／即時報價付費）。這是免費源普遍延遲或覆蓋不足的結構原因 |
| TradingView widget 的商業邊界 | 免費嵌入版本在可用指標、市場與外觀上受限，且對部分交易所封鎖，屬供應商策略而非技術限制 |
| 看板類產品的成本結構 | 行情 API、主機、email 發送、背景排程皆有邊際成本；「永遠免費」在無收入來源時不可持續，故出現訂閱／贊助模式 |
| 開源替代運動 | 以 AGPL 授權搭配自架，讓使用者自行承擔主機與 API key 成本，換取不綁定供應商與可審計的程式碼 |
| 教學專案轉社群專案 | 由既有教學模板（JavaScript Mastery）起家的專案，功能增補往往快於架構整併，且缺乏長期維護保證 |

---

## 3. 這個技術是如何解決該問題的？

### 3.1 技術棧與架構

```
┌─────────────────────────────────────────────────────────────┐
│ 前端  Next.js 15 App Router + React 19 + TypeScript 93.4%    │
│       Tailwind CSS v4 + shadcn/ui + Radix                    │
├─────────────────────────────────────────────────────────────┤
│ 認證  Better Auth（email/password，MongoDB adapter）          │
├─────────────────────────────────────────────────────────────┤
│ 資料  MongoDB Atlas + Mongoose                                │
│       collections：users / watchlists / alerts               │
├─────────────────────────────────────────────────────────────┤
│ 自動化 Inngest（cron + event）                                 │
│       4 個 serverless function                                │
├─────────────────────────────────────────────────────────────┤
│ 外部  行情 Finnhub  ／ 圖表 TradingView embed                 │
│       AI Gemini 2.5 Flash Lite →（fallback）Siray.ai Ultra    │
│       信件 Nodemailer ／ 行銷 Kit(ConvertKit)                 │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心機制

#### 機制一：兩種資料模式（cached vs realtime）

行情存取以模式旗標切換，這是「免費」與「付費」的功能分界線：

```text
cached   模式：報價快取 3600 秒（每小時更新），無 email 警示
                → 公開站（openstock-ods.vercel.app）使用
realtime 模式：報價 15 秒刷新，股價警示可用
                → OpenStock Cloud（$5/月）或自架並帶自有 Finnhub key
```

個股頁在有 Finnhub 報價時顯示完整 header（即時價、日內區間、市值）；無報價的市場改由 TradingView quote panel 呈現。

#### 機制二：Inngest 背景流程（4 個 function）

| ID | 觸發型態 | 排程／事件 | 用途 |
|---|---|---|---|
| `sign-up-email` | Event | `app/user.created` | 依 onboarding 問卷結果生成個人化歡迎信 |
| `weekly-news-summary` | Cron | `0 9 * * 1`（週一 09:00） | 彙整財經頭條並對全體使用者廣播 |
| `check-stock-alerts` | Cron | `*/5 * * * *`（每 5 分鐘） | 比對使用者目標價與即時行情 |
| `check-inactive-users` | Cron | `0 10 * * *`（每日 10:00） | 找出逾 30 天未活躍者並發送喚回信 |

#### 機制三：AI 多供應商路由（免中斷）

生成式功能不依賴單一供應商，主供應商失敗時自動切換：

```text
User Action / Cron
      │
      ▼
  Inngest Function
      │
      ▼
  Primary = Gemini 2.5 Flash Lite
      │  Error / Rate Limit
      ▼
  Fallback = Siray.ai Ultra
      │
      ▼
  Email / Notification
```

#### 機制四：認證與資料模型

| 元件 | 做法 |
|---|---|
| 認證 | Better Auth，email/password，MongoDB adapter |
| 使用者資料 | `users`（含 onboarding 偏好） |
| 關注清單 | `watchlists`（per-user unique symbol） |
| 警示 | `alerts`（目標價，供 `check-stock-alerts` 比對） |

#### 機制五：部署與自架

README 提供 Quick Start 與 Docker Setup 兩條路徑；環境變數含 `NEXT_PUBLIC_FINNHUB_API_KEY`、MongoDB URI、`KIT_API_KEY`／`KIT_API_SECRET` 等。自架者需自備 Finnhub key、MongoDB 與排程環境，才能在自架環境開啟 realtime 模式與警示。

### 3.3 功能分層總表

| 類別 | 公開站（免費） | OpenStock Cloud／自架 realtime |
|---|---|---|
| 報價更新 | 每小時（cached，3600s） | 15 秒（realtime） |
| 關注清單 | 有 | 有 |
| 公司資訊 | 有（TradingView 嵌入） | 有 |
| 價格警示 | **無** | 有（US 股票＋crypto） |
| 市場總覽 | 有 | 有 |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Yahoo Finance / Google Finance** | 入口網站直接呈現延遲行情、圖表、新聞與基本財務，廣告制免費 | 瀏覽器；無需自架、無需 API key | 廣告與追蹤；覆蓋與欄位受供應商政策限制；無法自訂或自架 | 零成本取得夠用的延遲看盤與公司資訊 |
| **Bloomberg Terminal / Wind / LSEG** | 付費專業終端，提供最完整的即時行情、資料與分析工具 | 年費數萬美元；需專業訓練 | 成本極高；學習曲線陡峭；分析深度仍取決於使用者 | 資料最完整、延遲最低、覆蓋最廣，專業機構標準 |
| **Ghostfolio** | 開源自架投資組合追蹤器，聚焦持倉績效與資產配置分析 | 自架（Docker）＋資料庫；需自行輸入或串接交易資料 | 需維護主機；非即時看盤定位；功能面與行情看板重疊有限 | 以持倉與配置為核心的個人財務追蹤，資料主權在自己手上 |
| **自建 FinDashboard／SBI 投資決策 Dashboard** | 從券商（SBI）網頁 dump 個人持股資料，自行計算 1M/3M/6M/12M 差額，做成寬螢幕鎖定的個人決策儀表板 | 需自寫抓取與呈現；綁定特定券商帳戶 | 需自行維護抓取腳本；僅覆蓋自己的持倉 | 直接解決「查閱券商網站困擾」，貼合個人實際持倉 |

### 4.2 切入點差異

| 方案 | 切入點 | 與 OpenStock 的層次關係 |
|---|---|---|
| Yahoo／Google Finance | **通用延遲行情入口** | 同為免費看盤，但為廣告制託管服務、不可自架。OpenStock 的差異在可自架、可改碼、可自帶 API key 開 realtime |
| Bloomberg／Wind | **即時＋深度資料終端** | OpenStock 明確的對標對象。兩者差距在資料授權（即時、覆蓋、延遲）與分析深度，非只價格 |
| Ghostfolio | **持倉與配置追蹤** | 與 OpenStock 互補而非競爭：Ghostfolio 管「我持有什麼、績效如何」，OpenStock 管「市場現在如何」。目標不同層 |
| 自建 FinDashboard／SBI Dashboard | **個人持倉決策** | 兩者皆為自建，但 OpenStock 解「市場總覽」，自建解「我的持倉」。可並存，唯需回答是否值得維護兩套 |
| （同軸延伸）AI Berkshire | **投資決策分析**：多 Agent（四大師視角）＋精確計算強制給結論 | 與 OpenStock 不同層：AI Berkshire 是「分析與決策」，OpenStock 是「行情與資訊呈現」。同屬金融工具軸，可並存 |

### 4.3 第二大腦對照與衝突

**本標的本身：** `Open-Dev-Society/OpenStock` 在第二大腦（FATESAIKOU/MyBrain，鏡像 @ c3319a0，2026-10-05）中**查無任何評估紀錄**；`技術/技術評估/判定總表.md`（118 筆索引）中亦無。以下同軸紀錄僅供對照，不得升格為他對本標的的既有判定。同樣地，Yahoo Finance、Google Finance、Ghostfolio、Bloomberg、TradingView、Finnhub 於第二大腦中**均查無一手評估**，本節不代填判定。

| 標的 | GitHub URL | 信任層級 | 判定／內容 | 與本標的關係 |
|---|---|---|---|---|
| 建立投資決策Dashboard | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/建立投資決策Dashboard.md | `human:fatesaikou`／stable（首見 2026-07-05、2026-07-11 更新） | 已自建 SBI 投資決策 Dashboard，dump 券商網頁資料、支援寬螢幕鎖定、計算 1M/3M/6M/12M 差額；結論「非常好，已基本可用」 | **最直接的同軸前例**：他解的是「自己持倉的決策」，與 OpenStock「市場看盤」不同層，但同為個人投資 dashboard |
| 專案現況表 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/專案現況表.md | `ollama-cloud/deepseek-v4-flash`／**draft（AI 草稿，未經他 review）** | 投資 Dashboard 列「日常在用（4）」 | 該自建線為每天在用的 workflow |
| FinDashboard systemdesign | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/FinDashboard%20systemdesign.md | `process:learning-agent`／stable | 「解決 SBI 證券自動投資功能的靈活性與運用性限制，開發個人專用的投資組合管理 CLI 工具」 | 同軸自建線的系統設計 |
| AI Berkshire | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/AI%20Berkshire.md | `human:fatesaikou`／stable（首見 2026-07-04） | **試用**：多 Agent 投資分析系統，四大師視角＋精確計算強制給結論；「先丟 opencode request 看他評價再定案」 | 金融工具軸已採用（試用）的一條線，但層次為「分析決策」非「行情看盤」 |
| 技術取捨準則 | https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md | `claude-code/opus-5`／**draft（AI 草稿，未經他 review）** | ①「解決方案不夠穩定或不熟悉就先自己兜，理解本質後才決定下一步」；②MVP→Feature 的唯一閘門＝**能否影響個人 workflow**；③「用現成的比較快」打不動他 | 判準層，直接決定 OpenStock 該不該進 workflow |
| 投資紀律 | https://github.com/FATESAIKOU/MyBrain/blob/main/日常/金融/投資紀律.md | `claude-code/opus-5`／**draft（AI 草稿，未經他 review）** | 唯一鐵則「定期定額，不因行情調整」；投資部位「基本不動」；投資偏好「怕損失既有」 | 紀律層，決定「盯盤型工具」對他是否有價值 |
| 核心價值觀 | https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/價值觀/核心價值觀.md | `claude-code/opus-5`／**draft（AI 草稿，未經他 review）** | 價值序列：產出形態（會動的機制 > 判斷材料）→ 自主性 → 金錢 | 上位判準：靜態看板屬「判斷材料」側的消費型工具 |
| 下一步清單 | https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md | `claude-code/opus-5`／**draft（AI 草稿，未經他 review）** | 現無 OpenStock 或看盤工具相關待辦；技術線在跑 AiStorage、LLM 推論骨架等 | 無排程位置 |

**明確指出的衝突：**

| # | 衝突／張力 | 內容 |
|---|---|---|
| 1 | **「用現成開源看板」與「自建 dashboard」方向相反** | 他對同軸需求已自建（`human:fatesaikou`／stable，且列日常在用）。依技術取捨準則（AI 草稿）「不夠穩定或不熟悉就先自己兜」，他處理這類需求的手段是自建而非採用現成。**但這非價值否定**：OpenStock 的市場總覽維度是他的自建版未覆蓋的，兩者不同層。是否改採需由他判定 |
| 2 | **MVP→Feature 閘門推得「不進 workflow」** | 技術取捨準則（AI 草稿）記唯一閘門為「能否影響個人 workflow」。OpenStock 服務的是美股即時報價與價格警示，而他的部位以日股／定投為主、並「基本不動」。依此準則，OpenStock 的可影響面低。此為 AI 草稿，尚未經他 review |
| 3 | **看盤型工具與投資紀律相抵** | 投資紀律（AI 草稿）的鐵則是「定期定額，不因行情調整」、部位「基本不動」、偏好「怕損失既有」。即時報價與價格警示服務的是「盯盤」，與該紀律方向相反。⚠️ 投資紀律為 draft，且其中「錢的功能是抗風險緩衝」一節引用他原話；轉述時須區分 |
| 4 | **與 AI Berkshire 的分工未定** | 金融工具軸已有 AI Berkshire（`human:fatesaikou`／stable，試用）。OpenStock 為行情呈現、AI Berkshire 為決策分析，層次不同可並存；但兩者同屬金融工具，若同時進 workflow 需先回答分工與時間排擠 |
| 5 | **屬「判斷材料」側，與價值序列最上層的「會動的機制」不合** | 核心價值觀（AI 草稿）的價值序列以「會動的機制」優先於「判斷材料」。OpenStock 為消費型看板，不產出可運轉的機制。此為 AI 草稿判準，需他本人確認是否套用 |
| 6 | **AGPL-3.0 與自架前提** | OpenStock 為 AGPL（部署為 web service 須開源）。技術層面第二大腦幾乎無硬拒絕（見不做清單，AI 草稿），授權屬採用障礙而非價值否定；自架需自備 Finnhub key、MongoDB 與排程環境，是落地門檻 |
| 7 | **查無既有判定** | OpenStock、Yahoo Finance、Google Finance、Ghostfolio、Bloomberg、TradingView、Finnhub 於第二大腦均查無一手評估紀錄；本報告不代填判定 |

---

## 附錄：資料來源

- repo README（全文）、`API_DOCS.md`、`MARKET_SUPPORT.md`、`package.json`
- 核心原始檔：`lib/market-data.ts`、`lib/markets.ts`、`lib/market-session.ts`、`lib/inngest/functions.ts`
- repo metadata／檔案樹／commits／contributors／releases：`gh api repos/Open-Dev-Society/OpenStock`（2026-10-05 實查）
- 第二大腦（FATESAIKOU/MyBrain，鏡像 @ c3319a0，2026-10-05）：`技術/技術評估/判定總表.md`、`技術/技術評估/AI Berkshire.md`、`技術/動手做/建立投資決策Dashboard.md`、`技術/動手做/專案現況表.md`、`技術/動手做/FinDashboard systemdesign.md`、`抽象理解/本質洞察/技術取捨準則.md`、`日常/金融/投資紀律.md`、`抽象理解/價值觀/核心價值觀.md`、`專案/下一步清單.md`
- 影片來源：https://youtu.be/gv9IGo9qqZM（**無可取得字幕軌，逐字稿不可得**）
