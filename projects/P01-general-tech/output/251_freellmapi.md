# freellmapi 技術分析報告

> 調研標的：`tashfeenahmed/freellmapi`（https://github.com/tashfeenahmed/freellmapi）
> 定位（issue #250 描述）：免费模型资源聚合路由
> 分析日期：2026-08-30
> 資料來源：repo metadata、README（482 行）、docs/architecture.md（112 行）、docs/api.md（357 行）；均取自 GitHub main branch。
> 信任層級：本報告為 AI（opencode/deepseek-v4-flash）產出之草稿，`status: draft`，未經本人 review。第二大腦中的對照判定一律另行標註信任層級。

---

## 1. 這個技術解決什麼問題？

freellmapi 解決的具體問題是：**「免費 LLM 額度分散在多個 Provider，各自有自己的 base URL、金鑰、模型 id、格式與 rate-limit 上限，開發者無法單一接入，也無法在不超過各免費上限的前提下可靠取用」**。

它把數十個 Provider 的免費額度聚合到單一 OpenAI 相容 `/v1` endpoint，由 router 依 rate-limit 自動挑選可用模型、429/5xx 自動 failover，並追蹤 per-key 用量以不超過各免費額度上限。

**問題描述中的模糊之處**：
- 「免費模型資源」未限定為 LLM chat——實際含 chat / embeddings / transcription / video 四類 endpoint（584 chat、41 embeddings、7 transcription、3 video）。只看 issue 描述會誤以為只聚合聊天模型。
- 「聚合路由」可解讀為「只是轉發」或「含智慧決策」——實際兩者皆有（routing 策略 + failover + 用量追蹤），描述未點出決策層。
- 「免費」的保固程度未定義——實際免費額度隨時變動，且 router 只做額度上限追蹤，不保證各 Provider 持續提供免費服務。

---

## 2. 這個問題為什麼會發生？（背景）

以下區分「文章中明確提到」與「通用技術背景」兩類。

### 文章中明確提到（README / architecture / api）

1. **Provider 數量爆炸**：2026 年當下，34 providers、474 model families、635 免費 endpoint、約 7.4B tokens/月。每個 Provider 免費額度是「天花板而非模型等級」——同一 Provider 的不同模型共享一個免費配額池，超出即拒。
2. **額度與上限是動態的**：免費額度由各 Provider 單方面調整，無統一公告；頂級模型日額度耗盡後只能降級（晚間智慧度下降）。
3. **格式不統一**：OpenAI / Anthropic / Gemini / Ollama 各有原生格式，需協議翻譯。
4. **金鑰分散且敏感**：每個 Provider 一把 key，總量可觀，需加密存放（AES-256-GCM）。
5. **單一 Provider 不可靠**：429/5xx 時需要 fallback 到別家，否則單點失敗。

### 通用技術背景（文章中未逐條明講，補自外部脈絡）

1. **LLM Provider 市場碎片化**：2024 年後開放免費額度的 Provider（Google、Groq、Cerebras、Mistral、NVIDIA、GitHub Models、Zhipu 等）各自提供限時免費額度作為獲客手段，形成「免費額度遍地、但沒人幫你統一管理」的市場結構。
2. **API 標準化未統一**：OpenAI 的 `/v1/chat/completions` 事實上是事實標準，但 Anthropic（`/v1/messages`）與 Gemini（`/v1beta`）各自獨立，需要兼容層。
3. **個人 / 實驗使用者的成本結構**：對個人實驗、side-project 開發者而言，訂閱高端模型成本高，免費額度若能無縫聚合可大幅降低成本，但手動維護每個 Provider 的帳號、金鑰、限額管理成本極高。

---

## 3. 這個技術是如何解決該問題的？

以下描述核心機制「怎麼做」，不評論好壞。

### 3.1 整體架構

```
     應用程式 (任何 OpenAI 相容 client)
                 │  單一 /v1 endpoint
                 ▼
        ┌─────────────────────────────┐
        │   Express proxy（本地/自託管） │
        │  ├ Router（選模型）          │
        │  ├ Key vault（AES-256-GCM）  │
        │  ├ rate-limit ledger         │
        │  └ 協議翻譯層                │
        └──────────────┬──────────────┘
              failover  │ 路由到選定 provider
                       ▼
      ┌────┬────┬────┬────┬────────┐
      │Google│Groq│Cerebras│Mistral│…34 providers│
      └────┴────┴────┴────┴────────┘
```

- **單一入口**：對應用程式只暴露 OpenAI 相容 `/v1`（chat / responses / completions / images / videos / audio / embeddings / models），另提供 Anthropic `/v1/messages` 與 Gemini `/v1beta` 原生面、Ollama 模擬。
- **router**：在每個請求時選「最高優先 且 key 健康 且未超 rate-limit」的模型，解密 key → 呼叫 provider → 429/5xx 時冷卻並重試下一個，最多 20 次。
- **6 種 routing 策略**：priority / balanced / smartest / fastest / reliable / custom；底層為 Thompson-sampling bandit 來估計各模型實際成功率。
- **rate-limit ledger**：per `(platform, model, key)` 維護 RPM/RPD/TPM/TPD 計數器，並從 provider 回報的錯誤 body / quota header **自動學習**上限（即自更新 signed catalog 的一部分）。
- **per-key 用量追蹤**：記錄每個金鑰用了多少，確保不超過免費額度天花板。
- **Fusion 多模型合成**：可把多個模型輸出合成，用於 tool calling / 多模型對比等。
- **其他**：sticky sessions、prompt compression、unified models、admin dashboard、MCP server。

### 3.2 路由與 failover 流程（architecture.md）

```
request → Router 挑 (highest priority ∧ key healthy ∧ 未超 rate-limit)
         → 解密 key → 呼叫 provider
         → 成功 → 回傳
         → 429/5xx → 冷卻該 (provider,key) → 重試下一個，最多 20 次
```

### 3.3 商業模式如何支撐「免費」

- router 本身 **MIT 免費**。
- **Premium**（$19/yr 或 $49 終身）只賣 **live catalog 即時更新**——免費版目錄落後 30 天。這解決「免費額度隨時變動，目錄必須持續維護」這個維持免費聚合的營運成本。

### 3.4 明確限制（文章明講）

- 無 frontier（頂級閉源）模型。
- 延遲變異大；無 SLA。
- 晚間智慧度下降（頂級模型日額度耗盡後降級到較弱模型）。
- 免費額度隨時變動，聚合本身無法保固。
- local-first、單使用者取向。

### 3.5 ToS 逐 Provider 審查（文章明講）

| 判定 | Provider |
|---|---|
| ✅ 允許 | Groq、Cerebras、Mistral、OpenRouter、Zhipu、Ollama Cloud、OVH、AI Horde |
| ⚠️ 有疑慮 | Google、Cloudflare、NVIDIA、GitHub Models、Z.ai |
| ❌ 禁止聚合 | Cohere |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

此節對照使用者第二大腦 FATESAIKOU/MyBrain 之既有評估，非僅列通則。

**先講結論**：freellmapi 與他第二大腦中已判「採用」的 **OmniRoute** 屬同問題域（LLM API Gateway 聚合免費額度）；與已判「試用」的 **Switchyard** 屬不同層（路由政策層）。本標的在他的第二大腦中**無任何評估紀錄**（grep `freellmapi` 查無）。

> ⚠️ 以下標為 AI draft 的 OmniRoute、Switchyard 判定均為 `status: draft`（`generated.by: opencode/…`），**尚未經本人 review**，轉述時僅作參考、不當作已定稿。

### 4.1 他的既有取捨準則（骨幹，AI draft，未 review）

來源：https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md（`generated.by: claude-code/opus-5`、`status: draft`、2026-08-01）

- **理解優先**：不穩定或不熟悉的解決方案會「先自己兜」，MVP 是理解達成的驗證點，不是效率計算。
- **MVP→Feature 唯一閘門**：能否影響他個人的 workflow。
- **Reject ≠ 沒價值**：被拒的工具仍可抽取「對需求的理解」與「方案方向」。
- **汰換看上游死沒死**，出現更好的替代不構成汰換理由（不追新）。

### 4.2 同級 / 替代方案清單（含 DA 表）

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **OmniRoute**（第二大腦已判「採用」，draft） | 本機開源 AI 網關，單一 OpenAI 相容 Endpoint 統一 250+ Provider（含 90+ 免費），含 18 路由策略、10 引擎 token 壓縮、三層 resilience、MCP server | 能安裝並運行本機服務；需要聚合免費額度與 Provider 解耦 | 需維護本機服務；提供方聚合目錄同樣隨時變動 | 應用程式與 Provider 解耦，成本與 fallback 集中管理 |
| **freellmapi**（本標的，無評估紀錄） | Express proxy 聚合 34 provider 免費額度到單一 `/v1`，6 種 routing 策略、自動 failover、per-key 用量追蹤、AES-256-GCM 加密 key；MIT 免費、Premium 賣 live catalog | 能運行 Node/Express 本機服務；接受「無 frontier 模型、晚間降級、無 SLA」 | 免費額度隨 provider 變動；頂級模型日額度耗盡後降級 | 免費額度聚合、429/5xx 自動 fallback、per-key 上限管理 |
| **Switchyard**（第二大腦已判「試用」，draft） | NVIDIA-NeMo 的 Rust LLM 路由 proxy＋協議翻譯；依任務繁重程度、過去輸出品質與成本（含切換成本）切到最適 endpoint | 有既有的 route 清單；需要的是「路由政策層」而非 Provider 聚合 | 無 Provider 目錄、無 quota 感知、pre-alpha 僅手動接 proxy | 依任務/品質/成本自動切 model 的路由政策 |
| **LiteLLM / OpenRouter / Portkey**（第二大腦中無獨立評估紀錄，僅在 OmniRoute / 下一步清單中作為對照組被提及） | 三者皆為 LLM API Gateway 聚合方案（LiteLLM 為 Python SDK 約 100 Provider；OpenRouter 為 SaaS 約 50 Provider；Portkey 為商業方案約 30 Provider） | 需要統一 Provider 接入 / 聚合 | OpenRouter、Portkey 為第三方服務，需經第三方；LiteLLM 為 SDK 需程式整合 | 統一 Provider 接入與 fallback |

> 對照來源（均在第二大腦）：
> - OmniRoute：https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OmniRoute.md（`opencode/deepseek-v4-pro`、`draft`、2026-07-26）
> - Switchyard：https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Switchyard.md（`opencode/deepseek-v4-flash`、`draft`、2026-08-23）
> - LiteLLM / OpenRouter / Portkey：僅在 OmniRoute.md 與 專案/下一步清單.md 第 71 條作為對照組被提及，**無各自獨立評估紀錄**。見 https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md（`claude-code/opus-5`、`draft`、2026-08-11）

### 4.3 各自解決問題的切入點差異

- **OmniRoute**：切入「Provider 解耦 + 免費額度聚合」。它不只路由，還內建 token 壓縮、resilience、MCP，Provider 目錄廣（250+/90+ free）。與 freellmapi 最直接競爭，且他的第二大腦已判採用、進入 Model Router 線。
- **freellmapi**：切入「免費額度聚合 + per-key 上限管理」。差異點在「以自更新 signed catalog 追蹤各 provider 免費額度的動態上限、以 per-key 用量避免超限」，並明確做 ToS 逐 provider 審查。但 Provider 廣度（34）與 token 能力遠小於 OmniRoute，且無 token 壓縮。
- **Switchyard**：切入「路由政策層」——不聚合 Provider、無免費額度感知，專注依任務繁重度 / 品質 / 成本切 model。與 freellmapi / OmniRoute **不同層**，是搭配而非替代。
- **LiteLLM / OpenRouter / Portkey**：切入「統一 Provider 接入」，屬最常見的 gateway 泛用方案，但免費額度聚合能力不如 freellmapi / OmniRoute 專精。

### 4.4 與他第二大腦既有判定的關係與潛在衝突

| 對照項 | 第二大腦既有判定 | 與本報告結論的關係 |
|---|---|---|
| OmniRoute | 採用（draft），Model Router 線已排 | **最直接重疊**：freellmapi 與 OmniRoute 高度同域。以他的取捨準則，若 OmniRoute 已判採用且正試玩，freellmapi 的額外價值僅在「per-key 上限管理 + ToS 審查」差異，重複度高 |
| Switchyard | 試用（draft），作為路由政策層 | 不同層，無直接衝突，可視為 OmniRoute/Switchyard 組合線的補充 |
| 下一步清單 Model Router 線（第 71 條） | 未定，待試玩 | freellmapi 屬「免費/低端掛 OmniRoute」的同一子題；若導入會取代/與 OmniRoute 免費聚合角色競爭 |
| 汰換準則（不追新） | 出現更好的替代不構成汰換 | **潛在衝突**：依此準則，即使 freellmapi 在「per-key 管理」上更細緻，也不構成汰換已判採用的 OmniRoute 的理由；除非 OmniRoute 上游死亡 |

**明確指出與本報告結論的衝突**：
- 本報告從「純技術面」看，freellmapi 在「per-key 免費額度上限管理 + ToS 審查」上優於 OmniRoute（OmniRoute 以 model 層級做 quota，freellmapi 以 key 層級做）。
- 但他的取捨準則（理解優先、不追新、MVP→Feature 看 workflow）會傾向「不因此替換已判採用的 OmniRoute」，而是抽取 freellmapi 的「per-key 上限管理 + ToS 審查」作為可借鑑方案方向。此為技術面結論與個人取捨準則之間的衝突點。
- 兩者的 OmniRoute / Switchyard 判定皆為 **AI draft、未 review**，本報告不將之當成定稿結論；若後續 QA，宜以他本人 review 後的判定為準。

---

*（本輪 R1 無使用者追問，無 ## 5. User Q&A 章節。）*
