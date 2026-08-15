# 216_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認標的＝**MuseCode（Meta 2026-08-05 發表的 terminal coding agent）＋ Muse Spark 1.2**，定位為「個人採用評估」，非 GitHub repo（官方頁在 developer.meta.com 與 dev.meta.ai）。使用者三大焦點：**性價比**、**Meta 拿資料訓練的範圍**、**是否切換訂閱配置**。

本 sub-step C1 為調研第一階段：取得官方 metadata、產品/架構文件、定價與資料使用條款、以及與使用者現有棧（Claude Code / opencode）的相容性。非 GitHub repo，故不套 `gh repo view`，改以官方 docs + 新聞原文 + 二級分析交叉。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `webfetch` research.meta.ai 官方 blog | 抓架構、co-training、benchmark 宣稱 | 拿到 MuseCode 核心機制與 Muse Spark 1.2 更新點 | 取得：async background agents（session 級持久）、append-only local event log（replay-exact / restart-safe）、bundled skills（/plan /grill /goal）、co-training with Muse Code、長時程訓練、kernel case study（1000+ tool calls / 24h） |
| `curl` dev.meta.ai/docs/pricing-rate-limits.md（官方 pricing） | 取得正式定價與 rate limit | 精確的兩 tier 單價與額度 | Standard $1.25 in / $0.15 cached / $4.25 out；Contributor $0.10 / $0.002 / $0.20；Web grounding $2.50/1000 搜尋；no long-context premium |
| `curl` dev.meta.ai/docs/muse-code/permissions.md | 取得 sandbox 與 approval 機制 | 確認安全邊界（影響採用） | Seatbelt(mac)/bubblewrap(Linux) OS sandbox、on-request/untrusted/never 三種 approval、stage-by-stage 命令審查、`--yolo` 關閉雙層防護 |
| `curl` meta-model-cookbook README | 確認與現有棧相容性 | 驗證能否取代/併入 Claude Code + opencode | 官方宣稱 Model API **drop-in 相容 OpenAI SDK / Anthropic SDK / OpenCode / Claude Code**；base_url `https://api.meta.ai/v1`；Use case 11 為「OpenCode + Muse Spark」GitHub repo agent |
| `webfetch` OpenRouter meta/muse-spark-1.2 | 取得模型規格與第三方單價 | 交叉驗證價格與規格 | 確認 $1.25/$4.25、1M context、released 2026-08-05、多模態輸入（text/image/video/audio/PDF）→ text 輸出 |
| `webfetch` agentpedia.codes developer guide | 二級分析補 benchmark 對照與 data terms 細節 | 補齊官方未明說的對照/疑慮 | 拿到 Terminal-Bench 2.1=82.9%(Muse Code) vs Opus5+Claude Code=86.7%、DeepSWE 1.1=59.3% vs 65.0%、內建 70.6% vs Opus5 79.4%；確認 contributor tier 的 data-training 條款 |

**關鍵事實（供報告用）：**

- **兩種計價 tier 的資料條款是使用者核心疑慮的直接答案**：Standard tier（`muse-spark-1.2`）「prompts and completions **not** used to train Meta models」；Contributor tier（`muse-spark-1.2-contributor`，-92% 價）「exchange for permission to use prompts and completions to train future Meta models」，且僅 select countries。→ 想「不給 Meta 訓練」選 Standard、要便宜選 Contributor。
- **相容性**：Muse Spark 1.2 可透過 OpenAI/Anthropic SDK、OpenCode、Claude Code 直接接（drop-in），意味對使用者不需換 harness，只換 base_url + model。MuseCode CLI 本身才是獨立 harness。
- **價格對照（現行組合 vs MuseCode）**：使用者現行 Claude Code $22/月＋Ollama Cloud；MuseCode 無月費、純 token 計費。1M context 無長文加價。output $4.25/M 高於多数 coding model，但 cached input 僅 $0.15。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 產品定位 | 官方 blog + OpenRouter | MuseCode＝terminal agent（beta）；Muse Spark 1.2＝coding-focused model，1M ctx，多模態輸入 |
| 架構機制 | official blog | persistent async background agents + replay-exact event log + /plan /grill /goal |
| 定價 | 官方 pricing-rate-limits.md | 兩 tier 單價、rate limits、web grounding、無長文加價 |
| 資料訓練條款 | 官方 pricing + agentpedia | Standard 不訓練；Contributor 訓練換折扣、限地區 |
| 安全邊界 | official permissions.md | OS sandbox + staged approvals；`--yolo` 危險 |
| 現有棧相容 | cookbook README | drop-in 相容 OpenCode/Claude Code/OpenAI/Anthropic SDK |
| benchmark | official blog + agentpedia 對照 | Meta 宣稱 82.9% TB2.1 / 59.3% DeepSWE；對照 Opus5 系統仍落後 |
| 是否 GitHub repo | 官方來源 | 非 repo；採官方 docs 調研 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研來源 | 只用 CNET 新聞 vs 官方 docs 為主＋二級交叉 | **官方 docs 為主** | 定價、資料條款、sandbox、相容性都需官方一手文件，新聞只提供發布時間與背景 |
| GitHub repo 流程 | 套 gh repo view vs 跳過改官方 docs | **跳過 gh repo view** | MuseCode 非 GitHub repo（Meta 未開源 harness），SKILL.md 的 gh 步驟不適用 |
| Contributor tier 資料題 | 只列官方一句話 vs 拆解兩 tier 對照 | **拆解兩 tier 對照** | 使用者核心疑慮正是「給 Meta 訓練坐到啥地步」；Standard/Contributor 是明確的二分答覆 |
| 相容性佐證 | 只信官方宣稱 vs 用 cookbook 佐證 | **cookbook 佐證** | 官方「drop-in 相容 OpenCode/Claude Code」是採用評估關鍵，需 cookbook 具體 recipe 支持 |
| 下一步 C2 | 直接寫報告 vs 補查使用者棧對照成本 | **補查對照成本** | 性價比需量化 MuseCode 與現行 Claude Code＋Ollama Cloud 組合；需 Opus5/DeepSeek 單價與訂閱 vs token 計費對照 |
