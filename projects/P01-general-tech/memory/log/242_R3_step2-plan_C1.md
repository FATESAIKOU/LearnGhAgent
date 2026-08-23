# 242_R3_step2-plan_C1.md

## 狀況理解

R3 意圖（Step 1 已收斂）：把 OmniRoute 的「免費 Provider 聚合 + fallback 規則」餵給 Switchyard，做到「用量用完自動 fallback」。使用者給出想像指令 `omniroute gen-switchyard.toml` / `switchyard update opencode|claudecode`，明講「預設沒有也沒事」，可接受 AI 產確定性 wrapping。C1 任務＝對齊「思想是否對上」：查證兩套在「用量用完自動 fallback」這件事上各自真正的能力邊界，以及轉換指令是否存在。這是 R3 專屬調研，不重做 R1 的路由演算法分析。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view`/`api` Switchyard metadata | 更新 repo 狀態 | 掌握時效與 CLI 面貌 | 2026-08-22 更新；languages=Rust；僅 `switchyard-server` 二進位，**無 `switchyard` update/setup 指令** |
| 抓 `cli_reference.md` + `routing_algorithms/overview.md` | 確認 CLI 與路由能力 | 確認有無 update/一鍵 setup | 只有 `switchyard-server --config <toml>`；route id 對應 `/v1/models`；**無 update 指令、無 provider 目錄 autodiscovery** |
| 抓 `reference/toml_schema.md` | 查 failover / fallback / retry 機制 | 確認 Switchyard 如何「fallback」 | `max_retries`（llm_client 層）；judge fail-open 到 strong；**無 quota/health 感知的跨 provider fallback、無 circuit breaker、無健康檢查** |
| 抓 OmniRoute `docs/OMNIROUTE_PROVIDER_FAILOVER.md` + `QUOTA_TELEMETRY.md` + `ROUTING_POLICY.md` | 確認「用量用完自動 fallback」在 Omni 端是否原生存在 | 判斷思想對不上的關鍵 | Provider Failover（circuit closed/open/half_open、跨 provider 最多 3 次 attempt、rate limit/timeout retry）+ Quota Telemetry（`exhausted`→**ineligible**、circuit open 不可選）+ routing（窮盡 quota/open circuit 排除）——**這正是使用者要的「用量用完自動 fallback」，原生在 OmniRoute** |
| 列 OmniRoute `bin/cli/commands/` | 確認 `gen-switchyard.toml` 是否存在 | 確認使用者想像指令 | **無 `gen-switchyard`、無任何 switchyard export**；只有 `setup-*`（opencode/claude 等）、`auth export`、`policy export/import`、`sync bundle` |
| 更新後 metadata 對照（OmniRoute README） | 校準廣度數字 | 與 R2 對齊 | 348 providers / 90+ free / ~1.51B tokens/月 / 495 models；免費池會每兩週重算、可上可下 |

## 動作結束後的現狀

| 驗證面向 | 驗證方式 | 結果 |
|---|---|---|
| `switchyard update opencode/claudecode` | 查 CLI 文件與 crates | **不存在**——Switchyard 只有 server binary，無 setup/update 指令 |
| `omniroute gen-switchyard.toml` | 列 bin/cli/commands | **不存在**——OmniRoute 無 switchyard 格式匯出 |
| 「用量用完自動 fallback」能力在誰 | 對照兩端 failover/quota 機制 | **在 OmniRoute**：circuit + quota exhausted→ineligible；Switchyard 只有 retry + judge fail-open，無 quota 感知 |
| 「思想是否對上」核心結論 | 兩套能力層 | **「聚合免費 + quota failover」是 OmniRoute 原生，Switchyard 無此機制**；使用者想像的「餵 Switchyard 去做 fallback」方向顛倒——Switchyard 根本沒有可承接「用量用完切 provider」的機制 |

**整合方向判定（供 C2 撰寫）：**
- 可行的真正銜接是**反向**：Switchyard 的 `[llm_clients.<name>]` 把 `base_url` 指向 OmniRoute 本機 endpoint（localhost:20128，R2 已證），讓 OmniRoute 原生做「免費聚合 + quota failover」，Switchyard 只做「路由政策（weak/strong/classifier）」；Switchyard 不需也不懂免費額度。
- 使用者想像的「OmniRoute→Switchyard TOML 匯出 + Switchyard 承載 fallback」不成立：方向反、能力缺、指令不存在。要做須自行兜一層（AI wrapping），但兜出來的東西會重複實作 OmniRoute 已原生擁有的 quota/failover，無收益。

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| C1 調研主軸 | 重調路由演算法 / 查 failover+quota 兩端能力 | 查 failover+quota 兩端能力 | R3 核心是「結合+fallback」，不是路由演算法；R1 已做演算法 |
| 「思想對上」判準 | 依使用者想像方向 / 反證兩端機制 | 以機制反證 | 先確認兩端各自真的有哪些 fallback 機制，再評使用者方向是否成立 |
| 使用者想像指令 | 當存在 / 實際查證 | 實際查證 | `gen-switchyard.toml`、`switchyard update` 皆不存在，須明示「預設沒有」成立 |
| 整合方向 | 使用者方向（O→S）/ 反向（S 吃 O endpoint） | 採反向 | 反向維持 OmniRoute 原生 quota failover，Switch 只疊路由政策，才符「思想對得上」 |
