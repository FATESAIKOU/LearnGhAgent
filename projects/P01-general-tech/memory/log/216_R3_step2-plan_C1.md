# 216_R3_step2-plan_C1.md

## 狀況理解

R3 是 R1（採用評估）＋R2（月費/多模態/benchmark）後的第三輪追問，從「要不要」轉為「**怎麼動手試**」層級。C1 針對 R3 兩問補資料，非重新調研：

1. **能否用 opencode 接 Muse Spark 1.2、訂哪個 tier、一步步指令**——R1 已下「Muse Spark 可 drop-in opencode（僅換 base_url）」，R3 要落地成**可執行指令**並含 **Contributor tier**（使用者明言可接受貢獻）。缺：官方 opencode config 原始碼、Contributor 折扣/條件限制、設定步驟。
2. **MuseCode（harness）vs opencode（harness）優勢與量化影響**——R3 問句是 harness 層對比（非 R2 已答的模型層）。缺：MuseCode harness 官方定位與特性，以及能否量化。

MuseCode 與 Muse Spark 均為 Meta 商業產品**非 GitHub repo**，SKILL.md 的 `gh repo view` 流程不適用；唯一開源 repo 是官方 cookbook `meta-models/meta-model-cookbook`（MIT、85 stars），提供 opencode 設定原始碼可佐證。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view meta-models/meta-model-cookbook` | 取得官方 cookbook metadata | 佐證 opencode 整合與取得一手 config | ✅ MIT、85 stars、default `main`、更新 2026-08-14；description 明載「drop-in 相容 OpenAI/Anthropic SDK 與 OpenCode/Claude Code」 |
| 讀 cookbook `03_use_cases/11_github_repo_agent/opencode.json` | 抓官方 opencode config 原始碼 | 得到可直接套用的 provider 設定 | ✅ 取得完整 `@ai-sdk/openai-compatible` 版 config（baseURL `https://api.meta.ai/v1`、model `muse-spark-1.1`） |
| `curl` dev.meta.ai/docs/quickstart.md | 抓官方 opencode 設定教學 | 取得一步步指令＋兩版 adapter 差異 | ✅ 取得「官方建議 `@ai-sdk/openai` 走 Responses API」版 config（含 reasoning/modalities/limit），與 `@ai-sdk/openai-compatible` 版 tradeoff |
| `curl` dev.meta.ai/docs/pricing-rate-limits.md | 確認兩 tier 牌價與條件 | 精確答「訂哪 tier、折扣多少」 | ✅ Standard $1.25/$0.15/$4.25、Contributor $0.10/$0.002/$0.20（-92%）；無長文加價；rate limits Standard 3000RPM/4MTPM、Contributor 100RPM/3MTPM，**per team 非 per key** |
| `curl` dev.meta.ai/docs/models.md | 確認模型/模態/tier 對應 | 補 Contributor 適用模型與模態 | ✅ 三 model ID 同屬 Muse Spark family、皆 1M context；表格列 text/image/video/PDF，**audio 未入表格** |
| `curl` dev.meta.ai/docs/muse-code.md + auth.md | 取得 MuseCode harness 官方定位 | 答 harness 層對比（問 2） | ✅ MuseCode＝terminal+CI coding agent、內建 approvals/sandbox/sessions/multi-agent、安裝指令 `curl -fsSL https://dev.meta.ai/install.sh \| sh`、browser sign-in 或 API key、usage-based billing |
| OpenRouter `/api/v1/models` ＋ models.dev | 交叉驗證價格與規格 | 確認 pricing 一致性 | ✅ 交叉一致；並發現 `meta/muse-glimmer-30b`（開源 30B 多模態，非 Spark） |

**關鍵一手/半手發現（供報告與 Step3 使用）：**

- **opencode 兩種接法（官方 quickstart 明載 tradeoff）**：
  - 建議版 `@ai-sdk/openai`（Responses API）：啟用原生多模態輸入（image/PDF）+ 跨 turn 加密 reasoning 續傳（`include:["reasoning.encrypted_content"]`），避免每 turn 從零推理、多步 tool loop 失焦。
  - 簡化版 `@ai-sdk/openai-compatible`（Chat Completions）：較簡單，但不保證 reasoning 續傳、無原生 PDF 輸入。→ 官方預設用 Responses 版。
- **Contributor tier 條件（此處與 R1/R2 的「select countries」敘述有出入）**：本輪抓到的官方 pricing/models 文件**皆未再提「select countries 地區限制」**，僅說「heavily discounted pricing in exchange for permission to use your prompts and completions to train future Meta models」。R1/R2 的「限地區」可能源自較早或二級來源；C1 標註為**待 Step3 驗證的歧義**（官方現行文件未載明地區限制）。
- **MuseCode harness 官方自述特性**：terminal+CI、approvals＋OS sandbox 首啟即開、interactive(`muse`)＋headless(`muse exec "…"`)、slash commands（/login 等）、MCP/skills/hooks、AGENTS.md 相容、durable project memory、browser sign-in 或 API key、usage-based billing（無月費）。
- **billing 模式**：usage-based、按 token 計、達 payment threshold 或每月 1 號扣款；無固定月費。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| opencode 接入可行 | 官方 cookbook UC11 opencode.json ＋ quickstart | ✅ 兩版 config 皆有官方原始碼，可直接套用 |
| Contributor tier | 官方 pricing/models | ✅ 折扣 -92%（$1.25→$0.10 in、$4.25→$0.20 out、$0.15→$0.002 cached）；rate limits 100RPM/3MTPM |
| Contributor 地區限制 | 官方現行文件 | ⚠️ 未載明；與 R1/R2 引用敘述不一致，需標註歧義 |
| MuseCode harness 對比素材 | 官方 muse-code.md | ✅ 有 install/interactive/headless/安全/billing 特性 |
| 多模態 audio | models.md 表格 | ⚠️ 表格列 text/image/video/PDF，audio 僅 prose 提及（同 R2 發現） |
| 非 repo 判定 | gh search | ✅ 無官方 MuseCode GitHub repo；唯一開源為 cookbook |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否套 gh repo view | 套（誤判為 repo） vs 認作商業產品走 docs | **走官方 docs＋cookbook** | MuseCode 無 GitHub repo；官方 cookbook 提供一手 opencode config 可作 repo 動作替代 |
| opencode 接法 | 只給一種 vs 給兩版 adapter 與 tradeoff | **兩版並列，建議 Responses 版** | 官方明載 tradeoff（reasoning 續傳/多模態）；使用者要可執行步驟，需給最適合日常 harness 的建議 |
| Contributor 地區題 | 沿用 R1 的「select countries」 vs 以本輪官方文件為準 | **標註為歧義** | 本輪官方 pricing/models 未載明地區限制，與 R1/R2 引用衝突；不硬下結論，留 Step3 驗證 |
| 量化第二問 | 找 benchmark 硬套 vs 標明 harness 層無直接量化 | **保留質性＋成本面量化，明確標註限制** | MuseCode vs opencode 是 harness 層，無官方並排量化；只能就「模型相同、成本＝token 計費 vs 月費」做可計算部分 |
| C1→C2 分工 | C1 全部收完 vs 拆 C2 收斂 | **C1 已足，進 Step3** | 兩問所需一手資料已取得；R3 為操作落地，不需再拆 sub-step |
