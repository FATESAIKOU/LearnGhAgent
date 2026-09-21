# OpenMAIC — Open Multi-Agent Interactive Classroom（多智能體互動式課堂）

> 調研標的：https://github.com/THU-MAIC/OpenMAIC（清單編號 3，issue #259）
> 資料來源：repo README/README-zh、`lib/orchestration/director-graph.ts` 初讀、LICENSE、repo metadata。
> 產出時間：2026-09-19（R1）。

---

## 1. 這個技術解決什麼問題？

**OpenMAIC 解決的是「把任意主題或文件，一鍵轉成由 AI 教師與 AI 同學共同授課、可即時互動的線上課堂」這個問題。** 它不是一個單一工具，而是一整套「內容 → 互動課堂」的生成與播放平台。

具體被解決的痛點：

- **靜態教材沒有互動性**：傳統把一份 PDF／文章／筆記丟給學習者自己讀，是單向的「閱讀」，沒有提問、沒有討論、沒有當場測驗與回饋。
- **產生優質互動教材的成本高**：要人工編寫投影片、測驗題、模擬互動、角色扮演劇本，工作量大且不可規模化。
- **多智能體「課堂」缺少現成可用的殼**：要做「AI 教師授課、AI 同學參與討論」的形態，需要把多個 LLM 角色、狀態機、播放控制、白板、語音/視訊、持久化串成一套可跑的系統，工程複雜。

OpenMAIC 把上述問題收斂為兩階段生成管線（Outline → Scenes）＋ 多智能體調度（director graph）＋ 播放引擎（playback state machine / action engine），做到「提供一份輸入，得到一門能上的課」。

> **模糊之處**：官方定位「one-click immersive multi-agent learning」是行銷語言，未定義「沉浸式」的量測標準；「課堂」的規模邊界（多少人、多長課時、多複雜主題）也未明確。這不影響理解其機制，但會影響「它到底多接近一門真課」的評估。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章中明確提到的背景

- **AI 生成內容的基礎成熟**：LLM（OpenAI/Azure/Anthropic/DeepSeek/Qwen/Kimi/Gemini 等）已可穩定產出結構化課程大綱、投影片文字、測驗題與角色對話，這是兩階段管線可行的前提。
- **多智能體（multi-agent）互動形態的興起**：OpenMAIC 的「AI teacher + AI classmates 討論、圓桌辯論、Q&A、白板」依賴「多角色 LLM 協作」這個當下流行的架構形態。
- **授權變遷**：repo 由 AGPL-3.0 於 v0.3.0 轉為 MIT，反映項目從「防商業利用」走向「廣納採用」的定位調整——是採用門檻的背景而非技術問題成因。

### 2.2 通用技術背景（網路補查）

- **生成式 AI 教育（GenAI in Education / edtech）**：ChatGPT 之後，學界與產業大量投入「AI 助教／AI 陪讀」，但多停在「單一 chatbot 問答」；把多個 AI 角色組織成有課程結構、有播放節奏的「課堂」，是較晚出現的進階形態。OpenMAIC 是這個方向的代表性開源實作。
- **內容自動化管線（content automation）**：把長文件拆成大綱再逐節生成多媒體資產，是 NLP／教育科技的通用做法（講義 → 章節 → 投影片 → 題庫），並非 OpenMAIC 獨創，只是它以「課堂場景元件」封裝。
- **多智能體編排（multi-agent orchestration）**：OpenMAIC 用 **LangGraph** 的 StateGraph 做調度——這是 agent 框架（LangChain 生態）近年把「流程控制」圖形化的通用趨勢，用來替代硬編碼的 If-Else 腳本。

> **區分**：以上 2.1 是 repo 明確提到的；2.2 是通用的技術脈絡，非 OpenMAIC 的獨有主張。

---

## 3. 這個技術是如何解決該問題的？

OpenMAIC 用**五層機制**把「靜態輸入」變成「互動課堂」：

```
輸入（主題／文件／URL）
   │
   ▼
① 生成管線（兩階段）── lib/generation
   Outline（AI 分析輸入 → 結構化大綱）
     └─▶ Scenes（每個大綱項目 → scene 資產）
             ├─ Slides（投影片）
             ├─ Quiz（單/多選/簡答 + 即時評分）
             ├─ Interactive HTML 模擬
             ├─ PBL（角色扮演 + 里程碑）
             └─ 3D 視覺化 / 遊戲 / 思維導圖 / 線上程式（v0.2.0 深度互動）
   │
   ▼
② 多智能體調度 ── lib/orchestration/director-graph.ts
   LangGraph StateGraph，single-round topology：
     START → director → agent_generate → END
   director 依 agent 數切換「LLM 策略」或「純 code 策略」；
   無 maxTurns 上限，靠 client 序列化多請求驅動討論
   │
   ▼
③ 播放引擎 ── playback state machine + action engine
   AI teacher 主動操作 UI（切投影片、叫白板、發討論）引導課程節奏
   │
   ▼
④ 互動模式
   課堂討論 / 圓桌辯論 / Q&A 模式 / 白板即時繪製
   │
   ▼
⑤ 持久化與匯出
   browser storage（預設）/ Postgres（server-backed）
   + S3/Postgres 資產層
   匯出：.pptx / 互動 HTML / 課堂 ZIP / MP4
   （離網/內網把 CDN 資產 inline 成 data: URI）
```

### 3.1 生成管線（核心「怎麼做」）

- **Outline**：輸入任意主題或文件，由 LLM 分析後產出結構化課程大綱。
- **Scenes**：大綱的每一項各自產出一門 scene，scene 是多種「課堂元件」的組合（投影片、測驗、互動 HTML、PBL、3D 視覺化等）。
- 場景元件是**可替換、可擴充**的資產類型，不只是文字，還含互動與遊戲類。

### 3.2 多智能體調度（實作層面）

從 `director-graph.ts` 初讀確認：

- 用 **LangGraph `StateGraph`** 定義狀態轉移，而非手寫流程。
- 拓樸為 **single-round**：`START → director → agent_generate → END`。
- `director` 節點依 agent 數量，在「LLM 動態策略」與「純 code 策略」之間切換——agent 少時用 code 直接排程，agent 多時交給 LLM 決定。
- **無 `maxTurns` 上限**：討論循環由 client 端序列化多請求驅動，而非在 graph 內設固定回合數。

### 3.3 Provider 中立與本地化

- LLM 供應商中立：OpenAI / Azure / Anthropic / Bedrock / Gemini / DeepSeek / Qwen / Kimi / MiniMax / Grok / GLM / Ollama 等皆可換。
- 多模態可換：TTS / ASR / 圖片 / 影片 / 搜尋各自可抽換。
- 可**完全在地端**（Lemonade、FunASR、VoxCPM2），不依賴雲端。

### 3.4 Agent 整合與 SDK 化

- `skills/openmaic/` 提供 SKILL.md 套件，支援 OpenClaw / Codex / DeepSeek / WorkBuddy，可從飛書 / Slack / Telegram 直接生成課堂。
- `packages/@openmaic/*` 拆成 SDK（dsl / renderer / editor / importer / generation / storage），把能力開放給自訂整合。

### 3.5 技術棧

TypeScript；Next.js 16 App Router / React 19 / LangGraph 1.1 / Tailwind 4；MIT；37.8k star；2026-09-18 仍活躍更新。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

「把多個 AI 角色組織成有結構的協作／教學形態」這個問題，不同方案切入點不同。以下對照**第二大腦（FATESAIKOU/MyBrain）**已評估過的項目，並補一個同級開源替代。

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **OpenMAIC**（本次標的） | 兩階段生成管線 + LangGraph 多智能體調度 + 播放狀態機，把輸入變成一門可互動的課 | 要自架/部署整套 Next.js 平台；要有 LLM 額度；要「課堂」這個具體應用場景 | 平台重；多智能體 token 成本隨討論回合數上升；「課堂」範式限制其泛用性 | 直接得到可播放、可互動、可匯出的課堂 |
| **munder-difflin** | Electron 桌面 app，把多個 CLI coding agent 包成一間視覺化「AI 辦公室」，每 agent 有座位/記憶/信箱，GOD agent 分派任務 | 想用「多 agent 分工」形態、且接受桌機 GUI | 基於 GUI 被鎖 UI；是多 agent 協作的一種拓樸，不自由 | 得到多 agent 分工殼，但非自由拓樸 |
| **DeerFlow** | 多智能體框架，LLM 動態決定下一步工具呼叫 | 想要彈性、開放性的 workflow | 無審計性、除錯成本高、流程控制由 LLM 擔當致幻覺連環爆 | 高泛用的彈性 workflow，但難審計 |
| **Understand-Anything** | 多代理管線 + Tree-sitter/LM 混合分析，把程式碼庫轉成互動式知識圖譜 | 有「讓 AI 產出可被人 review」的需求 | 需建 dashboard，屬代碼理解領域 | 互動式知識圖譜，人可探索/提問/審查 |
| **通用「LLM 單 chatbot 問答」**（非 repo） | 單一 agent 直接問答，無課程結構 | 只需問答、不要課堂形態 | 無互動課堂；無播放節奏 | 低成本的陪讀/助教，但非「課堂」 |

### 4.1 第二大腦的對照判定（依信任層級標注）

以下結論來自 MyBrain `技術/技術評估`，**皆為 draft 級 AI/process 產出，未經使用者本人 review**，引用時視為線索而非其拍板結論：

| 替代方案 | 第二大腦判定 | 理由（摘錄） | 信任層級 | 與本報告 §3/§4 的關係 |
|---|---|---|---|---|
| **munder-difflin** | **不採用** | 基於 GUI、只是多 agent 協作的一種拓樸、還太早且包太多；「實際需要的是能自由切換的拓樸」 | draft（`generated.by: process:learn-gh-agent`，[GitHub](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/munder-difflin.md)） | **衝突點**：OpenMAIC 的 director graph 也是「固定 single-round 拓樸」，與他「多 agent 拓樸要能自由切換」的判準同向；他會傾向把 OpenMAIC 也讀成「一種固定拓樸」，非他要的自由拓樸 |
| **DeerFlow** | **觀望**（不優先學習） | 動態 workflow 無審計性、除錯成本高，LLM 擔流程控制致幻覺風險高 | stable（`generated.by: human:fatesaikou`，2026-03-20，[GitHub](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/DeerFlow%20學習紀錄.md)） | OpenMAIC 的多智能體討論同樣是「LLM 驅動流程」，與他對 DeerFlow「無審計性」的擔憂同構 |
| **Understand-Anything** | **採用**（公司場景試） | 多代理管線轉程式碼為知識圖譜，「讓人能 review AI 產出」 | stable（`generated.by: human:fatesaikou`，2026-05-31，[GitHub](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Understand-Anything.md)） | 唯一他明確採用的多代理方案，但領域是「代碼理解/審查」，非「課堂」——不直接可套用 |

**技術取捨準則的適用**（`抽象理解/本質洞察/技術取捨準則.md`，draft，`generated.by: claude-code/opus-5`，[GitHub](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md)）：

- **理解優先**：OpenMAIC 平台偏重、包很多，若「不熟悉/不穩定」，他的傾向是先自己兜一個能理解的 MVP，而非直接採用整套平台。
- **MVP → Feature 閘門**：能不能影響他個人 workflow，是唯一升 Feature 的閘門。目前他無課堂/教學類進行中專案（`技術/動手做/專案現況表.md` 無教育類），OpenMAIC 進他日常 workflow 的機率低。
- **多 agent 拓樸自由切換**：他的判準是要「可自由切換的拓樸」，而 OpenMAIC 與 munder-difflin 都是「固定一種拓樸」——這是與他既有結論最直接的正向衝突，也是查詢最有價值處。

> **與結論衝突之處**：本報告 §3.2 指出 OpenMAIC 用 LangGraph single-round 固定拓樸調度多智能體。這正落在使用者「多 agent 拓樸要能自由切換，不要被單一拓樸鎖死」的反面。**若照通則（「多智能體互動課堂很值得試」）推薦，會推到他已表明反對的方向**。正確的讀法是：OpenMAIC 可抽取的是「兩階段生成管線 + 場景元件 + provider 中立」這套對教育內容的理解，而非「它本身是可採用的課堂平台」。

---

## 附錄：資料來源

- repo：https://github.com/THU-MAIC/OpenMAIC（37.8k star / 5.9k fork / MIT / 2026-09-18 更新）
- `lib/orchestration/director-graph.ts`（LangGraph 多智能體調度核心，初讀）
- 第二大腦：`技術/技術評估/判定總表.md`、`munder-difflin.md`、`Understand-Anything.md`、`DeerFlow 學習紀錄.md`、`抽象理解/本質洞察/技術取捨準則.md`（皆 draft/stable，信任層級見 §4.1）
