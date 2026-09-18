# 256_R2_step2-plan_C1.md

## 狀況理解

本輪為 R2，意圖是「把 sub2api 套用到使用者**實際訂閱持有組合**（個人 Claude + OllamaCloud + Antigravity，公司另有一份 Claude）上，評估三件事」：**(Q1) 適用性與具體手續、 (Q2) harness（claudecode/opencode/agy）間能否自由切換、 (Q3) 合約風險與被停號案例**。

R1 已建立「機制/架構/替代方案」基線。因此本 sub-step C1 不重做 R1 的「這是什麼」，而是**針對 R2 三問，重新掃 repo 中與「供應商帳號型態／協定支援／harness 整合／OAuth 流程」相關的 metadata 與子文件**——特別是他手上三種訂閱對應的 platform（Anthropic、Antigravity、Ollama Cloud），以及 ToS／合規／停號線索。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view Wei-Shaw/sub2api --json ...` | 重新取得 metadata（R2 時點快照） | 確認 stars/license/語言/活躍度 | Go、LGPL-3.0、**41917 stars / 8780 forks**、created 2025-12-18、updated 2026-09-18（當日活躍）；description「Claude/OpenAI/Gemini/Grok 訂閱統一接入、拼車共享」 |
| 抓 README.md（905 行）＋README_CN.md | 定位供應商支援範圍與 harness 設定 | 回答 Q1/Q2 的「哪些訂閱能接、如何設定 harness」 | **關鍵命中**：`## Antigravity Support`（Claude Code 設定 `ANTHROPIC_BASE_URL=.../antigravity` + `ANTHROPIC_AUTH_TOKEN=sk-xxx`；Hybrid Scheduling 選配）、`## Grok/xAI Support`（OAuth 訂閱走 `cli-chat-proxy.grok.com`、API-key 走官方 API；**Use Key 頁面提供 Grok CLI 與 OpenCode 設定**） |
| 抓 `backend/internal/domain/constants.go` | 確認平台白名單與帳號型態、協定列舉 | 對應到使用者的訂閱組合 | **取得 5+ 平台**：`anthropic`、`openai`、`gemini`、`antigravity`、`grok`＋國產（kimi/zhipu/deepseek/minimax）＋`opencode_go`。**帳號型態**：`oauth` / `setup-token` / `apikey` / `upstream` / `bedrock` / `service_account`。**協定**：`chat_completions`（OpenAI）、`anthropic`（Claude Code 專用）、`responses`（Codex） |
| 抓 `docs/ANTIGRAVITY_ATTRIBUTION_429.md` | 取得 Antigravity 一手排障記錄 | 回答 Q2/Q3 的「切換後會不會出問題」 | **關鍵命中**：Claude Desktop/Claude Code 經 CC Switch→Sub2API→Antigravity→Google 會帶 `x-anthropic-billing-header` attribution 元資料，在 Google 上游觸發 429；官方已修復（Antigravity 轉換器移除該行）；並警示「不要全域關閉 attribution，原生 Anthropic OAuth 相反會 429」 |
| 抓 `backend/internal/service/*ollama*`（ollama_cloud_usage.go、anthropic_apikey_auth_ollama_test.go） | 確認 OllamaCloud 支援方式 | 回答 Q1 的 OllamaCloud 適用性 | **關鍵命中**：Ollama Cloud 官方 Anthropic 相容端點只認 `Authorization: Bearer`（sub2api 強制 Bearer）；**OllamaCloud 需在 dashboard 設定 web session（`https://ollama.com/settings`）才能顯示用量/自動刷新**；另有 `ollama_cloud_messages_max_tokens`、`openai_gateway_ollama_cloud_*` 等專屬適配 |
| 抓 `docs/legal/admin-compliance.zh.md` | 取得運營方合規承諾與風險條文 | 回答 Q3 的合約風險證據 | 取得：README 明載「使用可能違反 Anthropic 等上游 ToS，風險自負」；legal 文件要求部署者自審上游 ToS/AUP/轉售限制/風控。**無「明確被停號」案例**——repo 與 docs 均無此類一手紀錄 |
| 掃 backend tree（git/trees recursive） | 確認有無 Claude subscription OAuth／停號相關專屬實作 | 補 Q1/Q3 事實 | 有 `claude_token_provider.go`、`gateway_claude_oauth_body.go`、`anthropic_session.go`、`gateway_anthropic_passthrough.go` 等；平台白名單列 `anthropic`。但**未見「Claude 訂閱額度分發」的專屬 proxy 對接**（Anthropic 無 Grok 那類 `cli-chat-proxy` 的公開訂閱通道），需在 C2 確認 |
| 抓 commits（15 筆） | 觀察近期變動方向 | 佐證活躍度與功能熱點 | 2026-09-17 密集合併；含 `fix/antigravity-attribution-429`、deepseek native responses、codex upstream chat role 等，顯示 Antigravity／Codex 為當前開發熱點 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Q1 供應商對應 | constants.go 平台白名單 | Anthropic / Antigravity / (OllamaCloud 掛 Anthropic 平台) 均有 platform 支援；OllamaCloud 走 Bearer + web session 用量同步 |
| Q1 具體手續 | README Antigravity / Grok 設定、ollama_cloud_usage | 有明確設定：Claude Code 用 `ANTHROPIC_BASE_URL`+`ANTHROPIC_AUTH_TOKEN`；Antigravity 需 OAuth 授權；OllamaCloud 需設 web session；API Key 於 admin dashboard 產出 |
| Q2 harness 切換 | README Antigravity / Grok「Use Key」+ 協定列舉 | sub2api 對外提供 OpenAI 相容＋Anthropic `/v1/messages`＋Responses 多協定；README 明確給 Grok CLI 與 OpenCode 設定；Claude Code 以 Anthropic 協定接入。**agy 無明示**，需 C2 依協定泛化推斷 |
| Q3 合約風險／停號 | README Important Notice、legal 文件、repo 全文 | 有明確 ToS 風險聲明（含 Anthropic），但**無一手停號案例**。需 C2 以公開案例＋各訂閱方案 ToS 補，並與「他的結論」切割 |
| 本 step 產出 | memory/log/256_R2_step2-plan_C1.md | 已產出，含 4 section，<6000 字 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| C1 範圍 | 重掃全部 repo；**只掃與 R2 三問（供應商/協定/harness/ToS）相關的 metadata 與子文件** | 後者 | R2 是落地評估非機制重述；機制基線已在 R1，避免浪費並控制字數 |
| OllamaCloud 歸屬 | 當獨立平台；**當作掛在 Anthropic 平台的 API Key 帳號** | 後者 | 程式碼實作如此（`newOllamaCloudAnthropicAuthAccount` 掛 `PlatformAnthropic`，走 Anthropic 協定 Bearer），貼合實作事實 |
| Claude 訂閱對接 | 比照 Grok 有公開 proxy；**查證後以「無公開 Claude 訂閱 proxy」處理** | 後者 | 程式碼顯示 Anthropic 走 OAuth/API-key/passthrough，未見 Grok 式 `cli-chat-proxy`；此推測須於 C2 標明 |
| Q3 停號案例 | 只用 repo 內容；**repo＋公開 ToS/案例，且標明信任層級** | 後者 | repo 明確聲明風險但無案例，必須外部補，且不可冒充他的舊結論 |
| Antigravity 429 記錄 | 忽略；**列為 Q2/Q3 關鍵一手資料** | 後者 | 直接對應「切到 Antigravity 用 Claude Code」會踩到的坑＋上游風控面，與 R2 高度相關 |
