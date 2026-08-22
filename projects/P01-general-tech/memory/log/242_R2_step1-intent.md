# 242_R2_step1-intent.md

## 狀況理解

R2 是針對 R1 產出的 Switchyard 分析報告（`output/242_switchyard.md`）的追問。使用者丟出 3 個明確操作型需求：

1. **對照**：Switchyard 與 OmniRoute 相比，支援 Model 廣度有沒有差異。並明講他的採納動機：「我 Accept OmniRoute 是因為他聚合很多免費額度」——即他要的不是「路由演算法」，而是「免費額度聚合 / Provider 廣度」。
2. **安裝操作**：把 Switchyard 裝起來，讓他的 claudecode 與 opencode 能用。要「一步一步的步驟＋指令」。
3. **安裝操作**：把 OmniRoute 裝起來，讓 claudecode 與 opencode 能用。要「一步一步的步驟＋指令」。

兩個安裝需求都有既有限制條件：**現在已有 OllamaCloud / Claude 訂閱**。

本輪意圖＝不只是「再解釋一次技術」，而是「對比 Provider 廣度 + 兩套工具的實際落地安裝指引」。Step 2 需產出：(a) Model 廣度對照表，(b) Switchyard 安裝手順，(c) OmniRoute 安裝手順，且 (b)(c) 都要收斂到「claudecode / opencode 各要改哪些 config、指到哪個 endpoint、模型 ID 怎麼填」。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `mybrain-read` 更新鏡像並掃目錄/骨幹 | 確認標的是否已評估、與手上專案的關係、有無取捨準則 | 拿到個人判定與專案脈絡 | 見下方「第二大腦查詢結果」 |
| grep 二腦「switchyard」 | 查本標的既有評估 | 確認是否已判過 | **第二大腦無此主題**（grep 零命中） |
| 讀 OmniRoute 判定、判定總表、下一步清單、claudecode/opencode 環境整理、142 報告 | 掌握 OmniRoute 判定與導入動線、及既有的 claudecode/opencode 環境 | 銜接導入實務 | 見下方「第二大腦查詢結果」 |
| 讀本輪 R1 產出 `output/242_switchyard.md` | 承接前一輪分析，避免重做 | 確認 §4 已有與 OmniRoute 的 DA 對照 | R1 已把 Switchyard 定位為「OmniRoute 解耦路線的細部路由補充」，但**未做 Provider 廣度量化對照、未做安裝手順** |

## 動作結束後的現狀

**第二大腦查詢結果（每則帶信任層級）：**

| 標的/主題 | 第二大腦內容 | GitHub URL | 信任層級 |
|---|---|---|---|
| **Switchyard** | **無任何評估紀錄**（grep「switchyard」零命中） | 查無 | 查無 |
| **OmniRoute** | **Accept**：本機開源 AI 網關，統一 250+ LLM Provider 單一 Endpoint（含 90+ 免費來源）；本質是 LLM Provider 解耦層，有學習必要，MVP 階段導入 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OmniRoute.md | AI draft（opencode/deepseek-v4-pro, status: draft, 2026-07-26），非本人 review 定稿 |
| **OmniRoute 導入狀態** | 在「下一步清單」：`LLM APIGateway 試用（解耦）——OmniRoute`，判定為採用但**尚未 MVP 驗證**，對照組 LiteLLM/OpenRouter/Portkey，「那個比較還沒做」 | https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md | AI draft（claude-code/opus-5, status: draft, 2026-08-11） |
| **claudecode/opencode 環境** | 已有穩定整理的 Hook（rtk）/Skill（officeCLI、mnv、ai-berkshire）/MCP（chrome-devtools）環境，claude 與 opencode 均「完整整理成功」 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/追加功能/整理%20claudecode-opencode%20環境.md | **human:fatesaikou, stable**（2026-07-13） |
| **Model Routing 判準** | DeepSeek V4 判定：「降低 Model Routing 研究優先級——不要把心力花在『如何精準路由不同 LLM』，集中在 Domain 知識」 | 日誌 2026-04-26 | **human, stable**（本人定稿） |

**結論：** 使用者接受的是 OmniRoute 的「免費額度聚合 / Provider 廣度」這個價值，不是「路由演算法」本身。Switchyard 主打的是「協議翻譯 + 路由演算法」，Provider 廣度上是弱項。本輪 Step 2 要以「Model 廣度」與「免費額度」為主軸對照，並各給 claudecode / opencode 的實際安裝 config 手順。導向性判準：若路由細化衝突到「降低 Model Routing」的 stable 判定，要以「接入免費/現有訂閱後端」為主要目的，路由當次要。

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 本輪對照主軸 | 功能全面對照 / **Provider 廣度 + 免費額度** | 取 Provider 廣度 + 免費額度 | 使用者開宗明義說接受 OmniRoute 的動機是「聚合免費額度」，廣度對照最切中他的判準 |
| 安裝範圍 | 只做其中一套 / **Switchyard 與 OmniRoute 兩套都做** | 兩套都做 | 需求明列 2、3 兩題，都是「claudecode + opencode」；各自給手順不偏廢 |
| Switch 的定位 | 當新研究方向 vs **OmniRoute（已 Accept）解耦路線上的補充** | 補充定位 | 沿用 R1 §4 結論 + DeepSeek V4（human stable）「降低 Model Routing」判準 |
| 是否查二腦 | 不查直接回答 vs **查完再回答** | 查完再答 | AGENTS.md + mybrain-read 強制，且命中也得導入狀態與環境整理，對安裝手順關鍵 |
