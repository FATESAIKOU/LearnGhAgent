# 289_R2_step2-plan_C1.md

## 狀況理解

R2 為 QA 追加輪，兩題質問 OpenStock：**Q1「價值是有效渠道的選定與整合，還是只寫個好看的 app」**；**Q2「投入金額、維護方靠不靠譜」**。R1 報告已含功能／架構／資料源／替代方案，但未量化「價值落點」與「資金／維護者永續性」。本 C1 定向補查兩類一手證據，不重做 R1：①由 repo metadata、contributors、commits、README／MARKET_SUPPORT 判斷工程價值究竟在資料整合還是 UI 包裝；②由 FUNDING.yml、sponsor 頁、維護者 profile、org、活動頻率推估投入規模與 bus factor。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` / `gh api repos/...` | 取最新 metadata | 更新 R1 數字 | stars **19,723**、forks 2,414、open issues 37、pushed 2026-10-01、AGPL-3.0、discussions 開啟 |
| contributors／stats/contributors／commits 取樣 | 量化 bus factor（Q2） | 判定維護集中度 | 見下表，主導者佔 ~72–77% |
| `.github/FUNDING.yml`、README sponsor 節、`/sponsor` 頁 | 取資金模型（Q2） | 得知誰收錢、錢去哪 | 見 Q2 證據 |
| 維護者 profile + org repos | 評估維護方可信度（Q2） | 查其身份與其他專案 | 見 Q2 證據 |
| README 全文 + MARKET_SUPPORT.md | 判定價值落點（Q1） | 確認資料源是否自建 | 資料全數外包第三方，見 Q1 證據 |

**metadata（2026-10-05 實查）：** created 2025-09-28、releases 0、tags 0、has_wiki、org=Open Dev Society（2024-08-01 建立、12 public repos、317 followers）。

**Q2 證據 — 維護者與資金：**

| 面向 | 一手事實 |
|---|---|
| 資金去向 | FUNDING.yml：`github: [ravixalgorithm]`、`buy_me_a_coffee: ravixalgorithm` → 收款人是**個人 Ravi**，非 org。sponsor 頁：錢付給 Ravi Pratap Singh |
| 資金用途 | sponsor 頁明列 5 項：Vercel 主機（已超免費額度）、Finnhub keys、MongoDB Atlas、Gemini＋email、**維護時間** |
| 資金規模 | 目標 **1/1000 monthly sponsors**（剛起步）；分級 $5/$25/$100/$500；「Current sponsors: 你的 logo 放這」→ **目前無具名贊助者**；**2026 曾由 Siray.ai 贊助** |
| 商業化 | OpenStock Cloud $5/月（coming soon，realtime＋警示）；宣稱 13,000+ 註冊用戶 |
| 維護者 | ravixalgorithm＝Ravi，21 歲、CS 在學、**Onto 創辦人**（company: Onto、bio「fixing how AI reads the web」）、Open Dev Society 創辦人、85 public repos、179 followers、帳號 2023-10 建立 |
| 維護集中度 | 17 contributors；commits 計數：ravixalgorithm 138（另一統計 91，claude 24、coderabbitai 16、keshav-005 12）；近 100 commits 中 ravixalgorithm 名下（含 Ravi/Mr. Algorithm/Algorithm）**約 72%** |
| 活動量 | 41 merged PR、53 closed PR、45 issues、37 open；最新 push 2026-10-01；2026-09-25 單日大量提交 |
| 專案成熟度 | repo 未滿一年、**0 release／0 tag**、無版本化歷程 |

**Q1 證據 — 價值落點：**

| 面向 | 一手事實 | 判定 |
|---|---|---|
| 行情資料 | 全部來自 **Finnhub 免費源**（symbols/profile/news）與 **TradingView embed**；MARKET_SUPPORT 自承 Finnhub 免費只覆蓋 US 股票＋crypto，其餘僅能靠 TradingView | 資料**非自建**，價值不在資料取得 |
| 資料整合 | README 明列整合 Finnhub、TradingView、Adanos（sentiment）、Inngest、Better Auth、Gemini/MiniMax/Siray（AI）、Nodemailer、shadcn | 工程重心＝**多源選定＋串接** |
| 自建機制 | 自建部分：Better Auth 認證、MongoDB watchlist/alerts 持久化、Inngest 4 個背景 function（警示比對／週報／喚回）、多供應商 AI fallback、cached/realtime 模式切換 | 有**可運轉機制**（非純靜態） |
| 包裝 | Next.js 15＋Tailwind v4＋shadcn/Radix，README 強調 UI polish、dark theme、Cmd+K | 包裝重，但非全部 |
| 護城河 | 無專有資料、無演算法壁壘；替代品可用同一批免費源重做 | 無資料護城河 |

## 動作結束後的現狀

- **Q1 可回答**：價值主體落在「**免費源選定＋整合＋帳號化＋自動化流程＋UI 交付**」的組合，**不是**單純好看的 app（有 auth、持久化、背景排程、AI router）；但**也不是**資料面的價值（行情與圖表皆外包，無自建資料／演算法）。警示與 realtime 正被移入 Cloud 付費層。
- **Q2 可回答**：無公開財報；投入＝**個人贊助＋一次性捐款＋未來 Cloud 訂閱**，目前無具名贊助者（曾由 Siray.ai 贊助）。維護**極度集中於單一 21 歲在學、同時經營 Onto 新創**的作者，bus factor≈1，專案未滿一年、0 release，但近期仍活躍。
- **待 C2／Step3**：以「技術取捨準則 §三／§四」檢驗 Q2 的維護風險定性；Q1 對接其「資訊源分級與整併」「核心價值觀：會動的機制>判斷材料」；確認 stars 由 R1 的 19,686 增至 19,723、contributors 由 17 之計數差異。
- 影片逐字稿仍不可得（不變）。

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| Q1 價值二分法 | 直接答「整合」或「好看的 app」／拆成能力層矩陣 | 拆成「資料／整合／自建機制／包裝」四層各自舉證 | 兩極皆為過度簡化，逐層舉一手事實才能支撐其質問 |
| Q2 資金證據來源 | 只引 README／兼查 FUNDING.yml 與 sponsor 頁 | 兼查兩者 | FUNDING 顯示收款人為個人而非 org，sponsor 頁明列用途，皆為 R1 未載的關鍵事實 |
| bus factor 量化方式 | contributors 總數／commit 佔比 | commit 佔比＋近 100 筆抽樣 | 總數 17 會低估集中度；佔比約 72% 才反映風險 |
| 維護者可信度定性 | 直接下「不靠譜」／只陳列事實留待 Step3 | 只陳列事實並標註 AI 草稿判準 | 避免越權代他下價值判斷，Q2 判準交由其「技術取捨準則」對接 |
