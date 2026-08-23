# 242_R4_step2-plan_C1.md

## 狀況理解

R4 是 R3 後的追問，標的仍為 Switchyard（NVIDIA-NeMo）。使用者質疑「反向接法」（Switchyard 指到 OmniRoute）的價值：**既然 Switchyard 只是把 base_url 指到 OmniRoute，那用 Switchyard 的意義在哪？** 他給出 2 個候選猜測：① 是不是因為 OllamaCloud/ClaudeCode 訂閱掛不進 OmniRoute？② 還是效能議題？

本 C1 的調研目標不是重做 R1 的 repo 全貌，而是**針對 R4 意圖**補查：Switchyard 的「fallback / 路由 / 協議翻譯 / metrics」能力邊界，以及 OmniRoute 能否承接 Claude/OllamaCloud 訂閱（驗證猜測①）。Step 1 已定調：逐一驗證 2 個猜測再收斂「意義」。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view NVIDIA-NeMo/Switchyard --json ...` | 取得 repo metadata | 掌握 stars/license/更新 | 2219★、Apache-2.0、main、2026-08-22 更新、pre-alpha |
| `gh api .../contents/` 列根目錄 | 盤點文件結構 | 定位關鍵子文件 | 有 docs/、crates/、README、AGENTS.md、CHANGELOG |
| 抓 README.md | 掌握定位與 maturity | 確認「pre-alpha、Not for production」 | 確認；server/libsy 雙路徑、協議翻譯、多演算法 |
| 抓 docs/core_concepts / getting_started / architecture / cli_reference | 掌握三層抽象與 CLI | 確認 TOML 結構、無 update/setup 指令 | 確認 llm_client/target/route 三層；CLI 僅 `--config` 等，無 provider 目錄 autodiscovery |
| 抓 routing_algorithms/overview + server README + toml_schema | 精確界定 Switchyard 的「fallback」能力 | 驗證 R3 結論「fallback 不在 Switchyard」 | 見下方「fallback 能力邊界」 |
| 讀 output/142_OmniRoute.md | 驗證猜測①（訂閱能否掛進 OmniRoute） | 確認 Claude/OllamaCloud 訂閱承接 | OmniRoute Tier 1 Subscription 含 Claude Code/Codex/Copilot，OllamaCloud 走 API key tier——**訂閱可掛進 OmniRoute** |

**Switchyard 的 fallback 能力邊界（本 C1 關鍵補查）：**
- `max_retries`（llm_client 層，預設 2）：僅 transport failure / timeout / HTTP 408/429 / 5xx 的**重試**，非跨 provider 切換。
- judge fail-open：llm_classifier 的 judge 失敗時 fail-open 到 strong_target，非「切到另一家免費」。
- `POST /v1/decision`：回傳「selected target + ordered fallbacks」——但這是**路由決策的 fallback 清單**，不是「用量用完自動切 provider」。
- **無 quota 感知、無 circuit breaker、無跨 provider failover**。與 R3 結論一致。

**OmniRoute 承接訂閱（驗證猜測①）：**
- 142_OmniRoute.md §3.1：Tier 1 = Subscription（Claude Code、Codex、Copilot）；Tier 2 = API Key（DeepSeek、Groq 等）。OllamaCloud 屬 API key tier。
- 結論：**Claude 訂閱與 OllamaCloud 都能掛進 OmniRoute**，猜測①（「訂閱掛不進 OmniRoute」）不成立。

## 動作結束後的現狀

- 已取得 R4 所需關鍵事實：Switchyard 的 fallback 僅限 retry + judge fail-open + `/v1/decision` 決策清單，無 quota/circuit/failover；OmniRoute 可承接 Claude/OllamaCloud 訂閱。
- 猜測①（訂閱掛不進 OmniRoute）**證偽**：Claude 訂閱（Tier 1）與 OllamaCloud（API key）皆可掛進 OmniRoute。
- 猜測②（效能議題）尚未驗證，需在 C2 補查：Switchyard 疊在 OmniRoute 上是否引入額外延遲/成本（協議翻譯 + 路由決策 overhead）。
- 待 C2 收斂「Switchyard 在反向架構下的真實價值」：路由政策（weak/strong/classifier/stage_router）+ 協議翻譯 + metrics，並對齊 DeepSeek V4「降低 Model Routing 優先級」準則。

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| C1 調研範圍 | 重做 R1 全貌 / 針對 R4 意圖補查 | 針對 R4 意圖 | R2+ 依 AGENTS.md 只做本輪意圖調研，不重做 R1 |
| 猜測①驗證方式 | 只查 Switchyard / 查 OmniRoute 承接 | 查 OmniRoute 承接 | 猜測①是「訂閱能否掛進 OmniRoute」，須查 OmniRoute 的 tier 結構 |
| fallback 界定 | 依 README 宣稱 / 查 toml_schema+server README | 查 schema+server README | 精確界定「fallback」語意，避免把 `/v1/decision` 的決策清單誤當跨 provider failover |
| 是否查效能 | 本 C1 查 / 留 C2 | 留 C2 | 猜測②（效能）需延遲/overhead 資料，屬 C2 補查範圍 |
