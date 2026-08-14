# 220_R1_step1-intent.md

## 狀況理解

使用者給定一篇窓の杜新聞（2026-08-13）介紹 Zed 團隊推出的「Delta」與其後端「DeltaDB」。Delta 是「人類與 agent 一起寫程式」的多玩家協作環境，DeltaDB 把 Git commit、前置編輯、agent chat 綁在一起記錄「程式碼＋意圖」，支援即時同步、Web 版（WASM）、第三方程 harness（首波 Claude Code）連動。R1 是第一輪，使用者明列三個他想釐清的點：①Delta 對「我個人工作流」是加成還是替換關係；②它是 harness 還是 tool，還是「團隊營運大一統 culture」；③與其他類似方案相比有沒有本質突破（沒有就自己幹）。

這是技術評估類任務，標的是「Delta / DeltaDB」。使用者語氣是「幫我調研」＋「沒有就乾脆自己幹」，落在他的技術評估判定框架（Judge→MVP→Feature）內，需回報為一份分析報告並可能落到技術評估判定。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 更新第二大腦鏡像並讀骨幹檔 | 定調前先確認「他是誰、在評估過什麼」 | 拿到判定準則與現況 | 讀到：技術取捨準則（理解優先／MVP→Feature 唯一閘門是個人 workflow／Reject＝不採用≠沒價值）、判定總表、專案現況表、下一步清單 |
| 查「Delta／DeltaDB／Zed」 | 確認是否已評估過 | 若有舊判定可直接銜接 | 有 Zed 舊判定（Reject，見下）。Delta 本身無既有評估 |
| 查同域工具（Aionui、Buzz、EverOS、TencentDB、OpenHuman、GitNexus） | 找出「團隊協作／agent 記憶／意圖管理」相近的既有判定 | 建立對照基準 | 全數命中，各有採用／觀望／不採用判定 |
| 查 Harness Engineering 與 AI-DLC | 對照使用者對 harness／agent 治理的既有準則 | 判斷 Delta 屬性的參考框架 | Harness 關鍵五問（memory/read/action/permission/verify）、AI-DLC 分工（工程師主司需求折衝、品質担保，AI 實作）已確立 |

**第二大腦查得內容（含 URL 與信任層級）：**

| 標的 | 結論 | GitHub URL | 信任層級 | 時間 |
|---|---|---|---|---|
| Zed（編輯器本體） | → Reject，「他要解的問題不是我的問題」 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Zed.md | human:fatesaikou / stable | 2026-05-31 |
| Aionui（多 agent 桌面協作、ACP 協定） | → Accept，在意 OfficeCLI 連動、MultiAgent、私人 Agent 系統（input data/workenv/communication-channel） | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Aionui.md | human:fatesaikou / stable | 2026-07-12 |
| Buzz（人與 agent 工作台、Hivemind） | → Reject，規模過大、採用效果未知；個人使用不必要 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Buzz.md | opencode/deepseek-v4-pro / draft | 2026-07-26 |
| EverOS（團隊級 agent 記憶） | → Reject，機制複雜無自組織驗證、泛用未專門化 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/EverOS.md | human:fatesaikou / stable | 2026-05-31 |
| TencentDB-Agent-Memory（團隊級記憶） | → Reject，核心判準是「資訊隨組織自我維護更新」＋無防腐化機制 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/TencentDB-Agent-Memory.md | process:learn-gh-agent / draft | 2026-08-10 |
| 個人 AiAgent 入口（進行中構想） | 未決：GAS vs 自架伺服器跑 opencode；卡在執行環境 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/靈感/個人%20AiAgent%20入口.md | claude-code/opus-5 / draft | 2026-08-11 |

**第二大腦無此主題：** Delta、DeltaDB 本身無既有評估記錄。此為新標的。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 需求類型 | 新技術調研（R1） | 技術評估任務，非追問輪 |
| 技術標的 | 新聞指涉 | 「Delta」＋「DeltaDB」，屬 Zed 團隊新專案，與已 Reject 的 Zed 編輯器本體不同層次 |
| 使用者三問 | ①②③ | ①加成 vs 替換（個人 workflow）；②harness/tool/團隊大一統 culture 的歸類；③與類似方案的本質突破有無 |
| 對照基準 | 第二大腦既有判定 | Zed 本體 Reject；Aionui Accept；Buzz/EverOS/TencentDB Reject；個人 AiAgent 入口未決 |
| 個人工作流切入點 | 判準 | 「能否影響個人 workflow」是進 Feature 唯一閘門；Delta 預設是「團隊」協作工具，需對照他目前是個人＋少量專案、非大型團隊情境 |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 標的界定 | 視為 Zed 延續（沿用 Reject）／視為獨立新標的 DeltaDB | 獨立新標的 | 新聞明示 DeltaDB 是為「脫離 Zed 包袱」另建；其核心價值是「程式碼＋意圖」資料層，與 Zed 編輯器效能問題無關 |
| 分析框架 | 純技術拆解／掛上他的判定框架 | 掛上判定框架 | 使用者三問全部指向「要不要用／怎麼歸類／值不值得自己幹」，必須用他的技術取捨準則收斂 |
| 對照組選定 | 編輯器類／agent 協作類／團隊記憶類 | 三類都要 | ②歸類需要 harness/tool 光譜對照，③本質突破需要 agent 協作（Aionui）＋團隊記憶（EverOS/TencentDB）雙軌對照 |
| 個人工作流比重 | 略過個人情境／深挖個人適用性 | 深挖 | ①與②使用者都掛「個人」前綴，而 Delta 本質是團隊工具，須正面回答「個人情境下是否成立」這條張力 |
