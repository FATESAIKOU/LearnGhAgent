# 251_R2_step1-intent

## 狀況理解

- 本輪 R2 為使用者對 R1 報告（`output/251_freellmapi.md`）的**追問**，含兩個子題：
  1. **評價標準**：以 a.免費額度網羅程度 b.私有訂閱可否登錄 c.能否簡單自擴調度規則 d.無多餘 GUI/TUI、專注核心邏輯、輕量 e.維護者/穩定度 五面向，把第二大腦中**所有類似技術全部拉入深入比較**。
  2. **接上個人 AI 入口**：基於 1，若要接上他的「個人 AiAgent 入口」，給一步一步做法（含指令解說），並判定 **GAS / Serverless / VPS / 私有機器** 哪個好。
- 這不是新標的調研，而是把 R1 的 freellmapi 放進「他個人的 LLMGateway 選型」脈絡做橫向比較＋落地建議。意圖核心是**選型決策**與**部署環境決策**，不是純技術分析。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 R2 追問文字 | 拆解兩個子題與五個評價面向 | 掌握追問意圖 | 兩子題：①五面向橫向比較 ②接入口＋部署環境判定 |
| mybrain-read：更新鏡像、讀骨幹 | 定調前掌握既有立場 | 確認已評估技術、相關專案、取捨準則 | 見下方發現 |
| grep 第二大腦 gateway/router/聚合相關 | 撈出「所有類似技術」 | 建立比較清單 | 見下方發現 |

### 第二大腦查詢發現（每則帶 URL 與信任層級）

1. **OmniRoute** — 開源 LLM API Gateway，統一 Endpoint 切換 250+ Provider 並聚合免費額度，判定「採用」，本質是 LLM Provider 解耦層，MVP 導入。**與 freellmapi 最直接同域**。
   - URL: https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OmniRoute.md
   - 信任層級：`opencode/deepseek-v4-pro`、`draft`（AI 產出、未 review）、首見 2026-07-26
2. **Switchyard** — NVIDIA-NeMo Rust LLM 路由 proxy，依任務繁重/品質/成本切 endpoint，判定「試用」，定位為**路由政策層**（與 OmniRoute 不同層）。
   - URL: https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Switchyard.md
   - 信任層級：`opencode/deepseek-v4-flash`、`draft`、首見 2026-08-23
3. **LiteLLM / OpenRouter / Portkey** — 無獨立評估紀錄，僅在 OmniRoute.md 與下一步清單第 71 條作為對照組被提及（LiteLLM Python SDK ~100 Provider、OpenRouter SaaS ~50、Portkey 商業 ~30）。
   - URL: https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md
   - 信任層級：`claude-code/opus-5`、`draft`、2026-08-11
4. **個人 AiAgent 入口（進行中專案）** — app＋拆開後端，卡在「執行環境三選項」：自架實體 / 自架雲端 / 跑在終端；另有 GAS 白嫖路線（gas-aiagent-core）。**子題 2 的落地對象**。
   - URL: https://github.com/FATESAIKOU/MyBrain/blob/main/技術/靈感/個人%20AiAgent%20入口.md
   - 信任層級：`claude-code/opus-5`、`draft`、2026-08-11（08-14/08-16/08-30 更新）
5. **gas-aiagent-core** — GAS 上可複用 AI Agent 內核，LLM Provider 抽象＋Tool Registry＋Loop Driver；**Exec Provider 只有介面無實作**，不能跑程式碼。GAS 白嫖路線的產出。
   - URL: https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/gas-aiagent-core.md
   - 信任層級：`claude-code/opus-5`、`draft`、2026-08-16
6. **技術取捨準則（骨幹）** — 理解優先（不穩定/不熟悉先自己兜，MVP 是理解驗證點）；MVP→Feature 唯一閘門是「能否影響個人 workflow」；Reject≠沒價值；汰換看上游死沒死、不追新。
   - URL: https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md
   - 信任層級：`claude-code/opus-5`、`draft`、2026-08-01

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 比較清單完整性 | grep 第二大腦 gateway/router/聚合 | 撈出 OmniRoute、Switchyard、LiteLLM/OpenRouter/Portkey（對照組）；freellmapi 為本標的 |
| 落地對象 | 個人 AiAgent 入口＋gas-aiagent-core | 子題 2 的接入口與部署環境判定有明確既有脈絡（執行環境三選項＋GAS 白嫖路線） |
| 取捨準則 | 骨幹技術取捨準則 | 已取得：理解優先、workflow 閘門、Reject≠沒價值、不追新 |
| 五面向對應 | 對照既有評估 | 五面向（a-e）需對照 OmniRoute/Switchyard/freellmapi 等逐一打分，並補「私有訂閱登錄」「輕量無 GUI」等既有評估未明列的面向 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 比較範圍 | ① 只比 freellmapi vs OmniRoute ② 拉入第二大腦所有類似技術 | ② 全拉入 | 使用者明言「把第二大腦有的類似技術全部拉入深入比較」；含 OmniRoute、Switchyard、LiteLLM/OpenRouter/Portkey 對照組 |
| 五面向處理 | ① 沿用既有判定 ② 依五面向重新打分 | ② 依五面向重新打分 | 五面向（a-e）是使用者新給的評價軸，既有評估未按此打分，需重做 |
| 子題 2 定位 | ① 純技術建議 ② 對照個人 AiAgent 入口既有脈絡給落地建議 | ② 對照既有脈絡 | 接入口與部署環境判定須接上「執行環境三選項」與 gas-aiagent-core 的 GAS 路線，不能脫離既有專案空談 |
| 部署環境判定 | ① 直接給單一答案 ② 依五面向＋既有三選項表給對照 | ② 對照既有三選項表 | 個人 AiAgent 入口已有 08-14 三選項表與 GAS 白嫖路線，判定應與之對齊，避免與既有立場衝突 |
