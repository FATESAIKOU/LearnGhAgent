# 251_R1_step2-plan_C1

## 狀況理解

- 本 sub-step 為 Step 2 的第一個調研動作：取得 freellmapi 的 repo metadata 與主要文件，作為後續分析（C2 收斂、C3 背景脈絡）的原料。
- 標的：`tashfeenahmed/freellmapi`，issue #250 描述「免费模型资源聚合路由」。Step 1 已定調：與使用者第二大腦中已判「採用」的 OmniRoute 同問題域，且與進行中的「Model Router 線」重疊。
- 本 sub-step 只做「取得資料」，不做分析收斂（那是 C2/C3 的事）。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view tashfeenahmed/freellmapi --json ...` | 取得 repo metadata | 掌握 stars、license、語言、更新時間、描述 | 見下方「metadata 摘要」 |
| `gh api .../contents/` 列根目錄 | 盤點 repo 結構 | 找出關鍵子文件 | 見 `docs/`、`server/`、`client/`、`desktop/`、`cli/` 等 |
| 抓取 README.md（raw） | 取得主要文件 | 掌握定位、功能、快速上手 | 482 行，內容完整（見下方摘要） |
| 抓取 docs/architecture.md | 取得架構與內部機制 | 掌握路由、rate-limit、限制、ToS | 112 行，含路由流程圖、6 策略、限制、ToS 表 |
| 抓取 docs/api.md | 取得 API 面 | 掌握 OpenAI/Anthropic/Gemini 相容面 | 357 行，含各 endpoint 與 fusion 等 |

### metadata 摘要

| 欄位 | 值 |
|---|---|
| nameWithOwner | tashfeenahmed/freellmapi |
| 建立時間 | 2026-04-21 |
| 最近更新 | 2026-08-30（活躍） |
| stars | 22,237 |
| license | MIT |
| 預設分支 | main |
| 主要語言 | TypeScript |
| description | 7.4B tokens/月、34 個免費 LLM provider、635 個免費 model endpoint、單一 /v1 endpoint、smart routing、automatic failover、encrypted keys、僅供個人實驗 |

### README 關鍵內容摘要

- **定位**：把數十個 provider 的免費額度聚合到單一 OpenAI 相容 `/v1` endpoint；router 依 rate-limit 挑最佳可用模型，429/5xx 自動 failover 到下一個 provider，並追蹤 per-key 用量以不超過各免費額度上限。
- **規模**：34 providers、474 model families、635 免費 endpoint（584 chat、41 embeddings、7 transcription、3 video）、約 7.4B tokens/月。
- **相容面**：OpenAI 全表面（chat/responses/completions/images/videos/audio/embeddings/models）、Anthropic Messages API（`/v1/messages`）、Gemini 原生 `/v1beta`、Ollama 模擬。
- **特色**：Fusion 多模型合成、tool calling、6 種 routing 策略、unified models、per-key rate tracking、自更新 signed catalog、sticky sessions、prompt compression、AES-256-GCM 加密 key、admin dashboard、MCP server。
- **商業模式**：router 本身 MIT 免費；Premium（$19/yr 或 $49 終身）只賣「live catalog」即時更新（免費版落後 30 天）。
- **限制**：無 frontier 模型、延遲變異大、無 SLA、晚間智慧度下降（頂級模型日額度耗盡後降級）、免費額度隨時變動。

### architecture.md 關鍵內容摘要

- **路由流程**：Express proxy → Router（挑最高優先且 key 健康、未超 rate-limit 的模型 → 解密 key → 呼叫 provider → 429/5xx 冷卻並重試下一個，最多 20 次）。
- **6 策略**：priority / balanced / smartest / fastest / reliable / custom，底層用 Thompson-sampling bandit。
- **rate-limit ledger**：per (platform, model, key) 的 RPM/RPD/TPM/TPD 計數器，並從 provider 回報的錯誤 body/quota header 自動學習上限。
- **限制**：quota 是天花板而非模型等級；晚間智慧度下降；無 SLA；local-first 單使用者。
- **ToS 表**：逐 provider 審查（Google ⚠️、Groq ✅、Cerebras ✅、Mistral ✅、OpenRouter ✅、Cloudflare ⚠️、NVIDIA ⚠️、GitHub Models ⚠️、Cohere ❌、Zhipu ✅、Z.ai ⚠️、Ollama Cloud ✅、OVH ✅、AI Horde ✅）。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| metadata 完整性 | gh repo view 回傳 JSON | 完整：stars/license/語言/時間/描述 |
| 主要文件取得 | README + architecture + api 三份 raw | 全部成功，內容完整 |
| 與 OmniRoute 同域確認 | README「How it compares」對照 OpenRouter/LiteLLM/Portkey | 確認屬 LLM API Gateway 聚合域，與 OmniRoute 同類 |
| 反爬阻擋 | 全程用 gh api / raw，未觸發 CAPTCHA | 無需 CDP |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 抓取哪些子文件 | ① 只 README ② README+architecture+api ③ 全 docs | ② | architecture 提供路由/限制/ToS（分析核心），api 提供相容面；其餘（install/clients/compression）對「解決什麼問題」貢獻低，留待需要時補 |
| 是否用 CDP | ① 一般 gh api/raw ② CDP | ① | 全程未遇 CAPTCHA/反爬，gh api 與 raw 皆成功，符合「僅必要時用 CDP」原則 |
| 是否下載 repo 原始碼 | ① 只讀文件 ② clone 看 server/src | ① | C1 目標是「取得 metadata 與主要文件」；原始碼細節留待 C2 若需驗證機制時再補 |
