# 264_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認標的為 **OpenMAIC（THU-MAIC，多智能體互動式課堂）**，全新未評估標的、與使用者既有專案無直接關聯。C1 是 Step 2 的第一個 sub-step，任務為：取得 repo metadata、擷取 README 與關鍵子文件、補查背景脈絡。此 sub-step 產出的是「素材收集」，不直接寫最終分析報告（屬 Step 3），C1 只負責把 repo 的「官方說法」抓齊並做初判，供後續 C2（機制深掘）與替代方案收斂使用。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view THU-MAIC/OpenMAIC --json` | 取得 repo metadata | 確認名稱/描述/授權/星數/主語言/更新時間 | 見下方「metadata 初判」；主語言 TypeScript、MIT、37.8k star、5.9k fork、2026-09-18 活躍更新、非 archived |
| `curl` 抓 README.md（約 1000 行） | 擷取官方完整說明 | 取得定位、功能、架構、使用場景 | 完整取得；見下方「文件擷取摘要」 |
| `curl` 抓 README-zh.md 前段 | 交叉比對中文官方定位 | 確認中文版是否有額外背景 | 定位與英文一致：開源 AI 互動課堂平台、多智能體生成 |
| `gh api` 列 `lib/orchestration/` 與 repo 根目錄 | 盤點關鍵子文件/原始碼結構 | 鎖定架構核心檔供 C2 深掘 | 鎖定 `director-graph.ts`（LangGraph 多智能體調度核心）|
| `curl` 抓 `director-graph.ts` 頭 60 行 | 初讀調度拓樸 | 確認多智能體架構的官方實作切入點 | 確認使用 LangGraph StateGraph，single-round 拓樸：START→director→agent_generate→END |
| `curl` 抓 LICENSE | 確認授權 | 判斷採用門檻 | MIT（2026-06-28 v0.3.0 由 AGPL-3.0 改 MIT）|

### metadata 初判（repo view 結果）

| 欄位 | 值 |
|---|---|
| name / 描述 | OpenMAIC — Open Multi-Agent Interactive Classroom「one click 沉浸式多智能體學習」 |
| primaryLanguage | TypeScript（Next.js 16 / React 19 / LangGraph 1.1 / Tailwind 4）|
| license | MIT（歷史曾為 AGPL-3.0，v0.3.0 轉 MIT）|
| stargazerCount / forkCount | 37,819 / 5,937 |
| createdAt / pushedAt | 2026-03-11 / 2026-09-18（活躍）|
| homepageUrl / archived | 空 / false |

### 文件擷取摘要（README 核心事實）

- **定位**：把任意主題或文件轉成互動課堂，由 AI 教師與 AI 同學授課/白板/即時討論。
- **生成管線（官方兩階段）**：`Outline`（AI 分析輸入產出結構化大綱）→ `Scenes`（每個大綱項目產出 scene：slides / quiz / interactive / PBL）。
- **場景元件**：Slides、Quiz（單多選/簡答+即時評分）、互動 HTML 模擬、PBL（角色扮演+里程碑）、3D 視覺化/遊戲/思維導圖/線上程式（v0.2.0 深度互動模式）。
- **多智能體互動**：課堂討論、圓桌辯論、Q&A 模式、白板即時繪製；由 AI teacher 主動操作 UI 引導。
- **技術棧/架構**：Next.js App Router + `lib/orchestration`（LangGraph director graph）+ `lib/generation`（兩階段管線）+ playback state machine + action engine；`packages/@openmaic/*` SDK（dsl/renderer/editor/importer/generation/storage）。
- **Provider 中立**：支援 OpenAI/Azure/Anthropic/Bedrock/Gemini/DeepSeek/Qwen/Kimi/MiniMax/Grok/GLM/Ollama 等 LLM，TTS/ASR/圖片/影片/搜尋各自可換；可完全在地端（Lemonade、FunASR、VoxCPM2）。
- **持久化**：預設 browser storage，可選 Postgres（server-backed persistence）＋S3/Postgres 資產層。
- **匯出**：`.pptx`、互動 HTML、課堂 ZIP、MP4 影片；離網/內網 inline 化 CDN 資產為 `data:` URI。
- **Agent 整合**：`skills/openmaic/` SKILL.md 套件，支援 OpenClaw/Codex/DeepSeek/WorkBuddy，可從飛書/Slack/Telegram 直接生成課堂。
- **其他**：12 種語系 i18n、ACCESS_CODE 認證、多 agent 調度為「單輪 director→agent」無 maxTurns 上限（client 序列化多請求驅動討論）。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo 存在與存活性 | `gh repo view` 非 404、pushedAt 距今 1 天 | 存在且活躍（37.8k star）|
| 授權適用性 | LICENSE 讀取 | MIT，低採用門檻（曾為 AGPL）|
| 官方定位是否清楚 | README 全文讀取 | 清楚：AI 互動課堂平台，兩階段生成 + 多智能體 + 可換 provider |
| 多智能體架構切入點 | `lib/orchestration/director-graph.ts` 初讀 | 已鎖定：LangGraph StateGraph，single-round topology，director 依 agent 數切換 LLM/純 code 策略 |
| 背景脈絡待補 | 有無需網路補查的「問題為什麼發生」 | 有：edtech / AI 生成式教學的歷史背景、與「多智能體課堂」同類替代方案（見 C2）|

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 抓取文件範圍 | 僅 README / README + 原始碼核心 | README + `director-graph.ts` 初讀 | 多智能體調度是本技術核心，需從實作確認「怎麼做」，非僅靠 README 描述 |
| 中文 vs 英文 README | 只讀一種 / 雙語交叉 | 雙語交叉比對 | 確認中英官方定位一致，避免翻譯偏差；中文版無額外背景 |
| C1 是否寫最終報告 | 直接產報告 / 只做素材收集 | 只做素材收集 | 依 AGENTS.md，分析報告屬 Step 3 產出；C1 收斂素材、C2 做機制深掘 |
| 背景脈絡深度 | 全在此步補 / 留給 C2 | 留給 C2 | README 已含大量背景（版本歷史、授權變遷、架構），「問題為何發生」需與替代方案併做，放 C2 較聚焦 |
