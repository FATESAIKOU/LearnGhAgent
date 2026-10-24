# 304_R1_step1-intent

## 狀況理解

本輪為 **R1、全新主題**（Original Issue #299，`Closes #299`），非追問或質疑。

- **技術標的**：`OpenRig`（[github.com/mvschwarz/openrig](https://github.com/mvschwarz/openrig)），TypeScript、Apache-2.0、7,569 stars。自述：「Build your own network of agents from Claude Code, Codex and Pi: persistent teams with roles, shared context and owned work.」
- **來源**：GitHub 一週熱點 135 期影片；**影片無字幕軌（transcripts disabled）**，逐字稿與影片觀點取不到——此為明確的資訊缺口。
- **使用者已附 repo 概況表**（描述／語言／stars／forks／license），意即 basic metadata 不必重查，要的是**內容解析**。
- **期待產物**：依 `know/AGENTS.md` 的標準 5 段分析報告（問題／背景／解法／替代方案 DA 表／Q&A），主題聚焦「多個 CLI agent 如何被組織成團隊」。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| refresh MyBrain 鏡像並讀骨幹 | 取得他的既有立場 | 得知準則與判定語意 | 鏡像 @ac9eaa2 更新成功 |
| grep `openrig`／`多 agent`／`orchestrat`／`claude code`／`codex` 等 | 找既有評估與關聯專案 | 確認標的與專案 | `openrig` 零命中；同問題域命中數檔 |

第二大腦查得（皆附 URL 與信任層級）：

1. **標的是否評估過：`OpenRig` 本身零命中——「第二大腦無此主題」。** 不得以通用知識冒充他的舊結論。
2. **同問題域近親：** [munder-difflin](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/munder-difflin.md)（`process:learn-gh-agent`／`draft`／首見 2026-08-30、更新 1 次）——把 Claude Code／Codex／Gemini 包成「AI 辦公室」的多 agent 協作殼，**判不採用**：①基於 GUI、不想被 UI 綁住；②它是「多 Agent 協作的一種拓樸」、而他要的是可自由切換的拓樸；③時序上排在「個人 AI 入口／MyBrain／LLMGateway／AI 共通執行環境」之後，「太早且包太多」。⚠️ 依 [技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md)「Reject≠沒價值」，此判不構成對 OpenRig 的結論。
3. [Aionui](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Aionui.md)（`human:fatesaikou`／`stable`／2026-07-12）——多 AI agent 統一桌面協作平台，**Accept**（catchup 理解整合 GUI 觀點，特別在意 MultiAgent）。是與 OpenRig 最同軸的已採用項。
4. **關聯進行中專案：** [個人 AiAgent 入口](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/個人%20AiAgent%20入口.md)（`claude-code/opus-5.5`／`draft`）＋ [Ai公司架構](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/Ai公司架構.md)（`claude-code/opus-5.5`／`draft`）＋ [herdr 配置](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/herdr%20配置.md)（`claude-code/opus-5`／`draft`）——他本人在 Mac 用 herdr 開 PM／Impl／Test／Review 四 pane 跑多 agent 開發，這正是 OpenRig 想解場景的**現行手工版**。
5. **取捨準則（骨幹）：** [技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md)（`tags:[骨幹]`／`claude-code/opus-5`／`draft`）——理解優先、Reject≠沒價值、MVP→Feature 唯一閘門是「能否影響個人 workflow」、agent 約束放 harness 不放權限。

**缺口**：影片觀點（為何推這支、示範了什麼）與 OpenRig 細部機制、與 munder-difflin／Aionui／herdr 的實測差異，第二大腦查無，須靠 repo 與網路補。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 標的判定 | grep `openrig` 全 bundle | 零命中，第二大腦無此主題 |
| 同軸參照 | 讀 munder-difflin／Aionui | 一不採用（draft）一採用（stable） |
| 專案關聯 | 讀個人 AiAgent 入口、Ai公司架構、herdr 配置 | 對應多 agent 開發 workflow 與機器池架構 |
| 準則 | 讀骨幹技術取捨準則 | 理解優先、Reject≠沒價值、影響 workflow 才是閘門 |
| 本輪性質 | 對照 issue 與既有 QA | R1 全新，非追問 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 本輪定位 | R1 新主題／R2 追問 | **R1 新主題** | issue 為 `Closes #299` 的原始需求 |
| 技術標的邊界 | OpenRig 全系統／只比對 herdr 手工流程 | **全系統評估** | 使用者附了 repo 概況，要的是內容解析 |
| 報告型態 | 技術評估（DA 表判定）／操作教學 | **標準 5 段分析報告** | 依 know/AGENTS.md 格式 |
| 既有「不採用」的用法 | 沿用 munder-difflin 結論／僅作同問題域背景 | **僅作背景** | OpenRig 命題（network＋persistent teams）與 munder-difflin（GUI 辦公室）不同 |
| 影片缺口處理 | 自行猜測影片內容／標明缺口並靠 repo 補 | **標明缺口、外部補齊** | 不得以通用知識填空冒充既有結論 |
