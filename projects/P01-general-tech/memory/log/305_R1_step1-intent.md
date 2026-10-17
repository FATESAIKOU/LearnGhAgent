# 305_R1_step1-intent

## 狀況理解

本輪為 **R1、全新主題**（Original Issue #298），非追問或質疑。

- **技術標的**：`wheresryan22/anatomy`——一個 **Agent Skill**，生成「真實機械與複雜系統」的**互動式等角（isometric）技術圖解**；輸出 polished SVG，可選 WebGL shader 與 3D 效果。
- **標的概況**（issue 內 2026-10-17 API 實查）：JavaScript、14,132★／1,068 forks、MIT。
- **來源**：GitHub 一周热点 135 期影片（YouTube 端 transcripts disabled，逐字稿取不到，影片觀點待補）。
- **使用者要的 5 塊**（依 AGENTS.md 報告格式）：①這技術解決什麼問題 ②問題背景 ③如何解決（機制）④替代技術 DA 表（2～4 個）⑤Q&A。**附帶條件**：中文、表格／圖示／階層結構、含反面論證、不用比喻與情緒性語言。
- **資訊缺口**：影片逐字稿不可得；repo 尚未實查，目前只有 API 概況——標的機制須靠網路補。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| refresh MyBrain 鏡像並讀骨幹 | 取得既有立場與準則 | 得知判定語意與取捨準則 | 鏡像 @ac9eaa2 更新成功 |
| grep `anatomy`／`isometric`／`圖解`／`illustration`／`skill`／`SVG`／`WebGL` | 找標的既有評估、關聯專案、準則 | 確認三件事 | 見下 |

第二大腦查得（皆附 URL 與信任層級）：

1. **標的是否評估過：無此主題。** grep `anatomy` 全 bundle **0 命中**——Anatomy 本體從未評估，其功能細節（等角 ISOMETRIC 渲染、SVG/WebGL 輸出）無既有結論，不得當成他的舊結論。**同軸對照**：[archify](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/archify.md)（`process:learn-gh-agent`／`status: draft`／首見 2026-09-19）＝「生成**可信架構圖**的 Agent Skill」，判定**採用**；[diagram-design](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/diagram-design.md)（`process:learn-gh-agent`／`draft`／2026-08-16）＝出版級圖表 Skill，判定**不採用**。⚠️ 依 [判定總表](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md)（`ollama-cloud/deepseek-v4-flash`／`draft`），「不採用 ≠ 沒價值」。
2. **關聯進行中專案：[個人 AiAgent 入口](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/個人%20AiAgent%20入口.md)**（`claude-code/opus-5.5`／`status: draft`）——2026-09-23 起 **Harness 的 prompt／skill／tool 歸 AiStorage 的 Atelier 管理**。Anatomy 是「agent skill」，正落在這條 skill 管理軸上。
3. **取捨準則（骨幹）：[技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md)**（`claude-code/opus-5`／`draft`／`tags: [骨幹]`、`generated.at 2026-08-01`）——「**理解優先**」、「MVP→Feature 唯一閘門＝能否影響個人 workflow」、「Reject≠沒價值」。可抽取的判準：diagram-design 結論明載他目的是「**解構／理解抽象概念**」，**思考工具 vs 出版工具**是分岔軸——Anatomy 的定位（教學式圖解）偏思考工具側，但須自行驗證。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 標的判定 | grep `anatomy` 全 bundle | 無獨立評估，屬首次調研 |
| 同軸對照 | 讀 archify、diagram-design | 圖表／視覺 skill for agent 軸：採用 vs 不採用各一 |
| 專案關聯 | 讀「個人 AiAgent 入口」 | 對應 AiStorage/Atelier 的 skill 管理軸 |
| 準則 | 讀骨幹「技術取捨準則」 | 理解優先、思考工具/出版工具分岔、Reject≠沒價值 |
| 本輪性質 | 對照 issue 與既有 QA | R1 全新，非追問 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 本輪定位 | R1 新主題／R2 追問 | **R1 新主題** | issue 為 `Closes #298` 的原始需求 |
| 標的邊界 | Anatomy 全生態／Skill 本體與圖解產出機制 | **Skill 本體＋產出機制** | issue 標的明確為「生成互動式技術圖解的 Skill」 |
| 與既有判定的關係 | 沿用 archify 採用作結論／diagram-design 拒作結論／僅作同軸對照 | **僅作同軸對照，另行判研** | 三者問題域相近但產出型態不同，不可直接套用他人判定 |
| 缺口處理 | 以通用知識補影片觀點／明列缺口待外部補 | **明列缺口，靠網路補** | 影片逐字稿不可得，不得揣測影片立場 |
