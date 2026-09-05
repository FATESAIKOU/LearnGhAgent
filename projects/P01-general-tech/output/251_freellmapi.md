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

### 4.5 依使用者五面向（a–e）的橫向比較（R2 追加）

使用者 R2 追問給出五個評價面向，要求把第二大腦所有類似技術拉入深入比較。以下對照 freellmapi（本標的）、OmniRoute（採用，draft）、Switchyard（試用，draft）、LiteLLM/OpenRouter/Portkey（無獨立評估，僅對照組）。

| 面向 | freellmapi（本標的） | OmniRoute（採用，draft） | Switchyard（試用，draft） | LiteLLM/OpenRouter/Portkey（無獨立評估） |
|---|---|---|---|---|
| **a. 免費額度網羅** | 34 providers、635 免費 endpoint、7.4B tokens/月；自更新 signed catalog（免費版落後 30 天、Premium 即時） | 250+ Provider、90+ free、1200+ models | 無 Provider 目錄，廣度＝手動 route 清單 | LiteLLM ~100、OpenRouter ~50、Portkey ~30 |
| **b. 私有訂閱登錄** | 可：custom provider 指到任何 OpenAI 相容 endpoint（llama.cpp/LM Studio/vLLM/本地 Ollama/遠端 gateway） | 可：Claude Tier1、OllamaCloud API key 皆可掛（見 Switchyard QA） | 可：手動 route 清單可指到 Claude/OllamaCloud | 依方案而定 |
| **c. 自擴調度規則** | 6 種 routing 策略＋命名 fallback-chain profile＋dashboard/PUT API 切換；**新增 provider 需改程式碼**（Platform union＋adapter＋catalog），非純設定 | 18 種路由策略（priority/cost-optimized/auto 等） | 路由政策層，手動 route 清單 | 依方案而定 |
| **d. 輕量/無多餘 GUI** | Express proxy＋React dashboard（admin 用）；~40MB RSS idle；可跑 Node 20+ 任何處（含 ARM SBC）；dashboard 屬管理面非強制 | 本機單一 Endpoint | Rust proxy，無 GUI | 依方案而定 |
| **e. 維護者/穩定度** | 24.3k stars、3314 forks、2026-04 建立、活躍（2026-09-05 更新）、MIT、單人主導但社群大 | 採用（draft，未 review） | 試用（draft，未 review）、pre-alpha | 無獨立評估 |

**五面向下的定位結論**：
- 以 a（免費網羅）與 c（自擴調度）看，**OmniRoute 全面優於 freellmapi**（Provider 廣度 250+ vs 34、策略 18 vs 6）。
- freellmapi 的相對優勢集中在 **b（私有訂閱登錄的彈性）與 d（輕量、可跑 ARM SBC）**，以及 R1 已指出的 per-key 上限管理與 ToS 審查。
- 以 e（維護者/穩定度）看，freellmapi 社群活躍度（24.3k stars）高於 Switchyard（pre-alpha），但兩者皆為 AI draft 判定、未 review。

---

## 5. User Q&A

### Q1：這類 LLMGateway 對我的評價標準是 a–e 五面向，憑什麼把第二大腦所有類似技術拉進來比？

**A**：依你給的五面向（a.免費額度網羅 b.私有訂閱登錄 c.能否簡單自擴調度規則 d.無多餘 GUI/TUI、輕量 e.維護者/穩定度），把第二大腦中所有類似技術拉入比較。比較清單與判定來源如下：

| 技術 | 第二大腦判定 | 信任層級 | 來源 |
|---|---|---|---|
| OmniRoute | 採用 | `opencode/deepseek-v4-pro`、`draft`（未 review） | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OmniRoute.md |
| Switchyard | 試用 | `opencode/deepseek-v4-flash`、`draft`（未 review） | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Switchyard.md |
| LiteLLM/OpenRouter/Portkey | 無獨立評估 | 僅在 OmniRoute.md 與下一步清單第 71 條作對照組 | https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md |
| freellmapi | 無評估紀錄 | 本報告（draft） | — |

**五面向逐項對照**（詳見 §4.5 表格）：

| 面向 | 最強 | 次強 | 最弱 |
|---|---|---|---|
| a. 免費網羅 | OmniRoute（250+/90+ free） | freellmapi（34/635） | Switchyard（無目錄） |
| b. 私有訂閱登錄 | freellmapi（custom provider 指任意 OpenAI 相容 endpoint） | OmniRoute（Claude/OllamaCloud 可掛） | Switchyard（手動 route） |
| c. 自擴調度 | OmniRoute（18 策略） | freellmapi（6 策略＋profile，但新增 provider 需改碼） | Switchyard（手動） |
| d. 輕量/無 GUI | Switchyard（純 Rust proxy） | freellmapi（~40MB、可跑 ARM SBC） | OmniRoute（功能多、較重） |
| e. 維護者/穩定度 | freellmapi（24.3k stars、活躍） | OmniRoute（採用判定） | Switchyard（pre-alpha） |

**反證表（避免只看單一面向）**：

| 若只看 | 會誤判成 | 但 |
|---|---|---|
| a（免費網羅） | OmniRoute 完勝 | freellmapi 在 b/d 與 per-key 管理上仍有差異價值 |
| e（stars 數） | freellmapi 最穩 | stars 高不等於已 review；OmniRoute/Switchyard 判定皆為未 review 的 AI draft |
| c（策略數） | OmniRoute 最好擴 | freellmapi 的「新增 provider 需改程式碼」是 c 面向的硬傷 |

**結論**：以五面向綜合看，OmniRoute 在 a/c 領先、freellmapi 在 b/d 有相對優勢、Switchyard 是不同層（路由政策層）的搭配而非替代；LiteLLM/OpenRouter/Portkey 在你的第二大腦中無獨立評估，僅作對照組。

---

### Q2：基於 1，要接上我的個人 AI 入口該怎麼做（一步一步＋指令）？GAS/Serverless/VPS/私有機器哪個好？

**A**：先講關鍵前提——**freellmapi 是 Node/Express 常駐 proxy，需要一個能長期跑 Node 20+ 程序的環境**。這直接決定 GAS/Serverless/VPS/私有機器哪個可行。

**你的個人 AI 入口既有脈絡**（來源：https://github.com/FATESAIKOU/MyBrain/blob/main/技術/靈感/個人%20AiAgent%20入口.md，`claude-code/opus-5`、`draft`、2026-08-11，08-14/08-16/08-30 更新）：
- 專案卡在「執行環境三選項」：自架實體 / 自架雲端 / 跑在終端，尚未定案。
- GAS 白嫖路線（gas-aiagent-core）的**殼已完成，但 Exec Provider 只有介面無實作，不能執行程式碼**。
- 下一步清單第 79 條：MultiProvider 機制方向（接既有 LLMGateway / 自建 / App 內嵌）**尚未比較**。

**四種環境對照（DA 表）**：

| 環境 | 能否跑 freellmapi | 技術解法 | 使用前提 | 使用副作用 | 預期效果 |
|---|---|---|---|---|---|
| **GAS** | ❌ 不能 | GAS 是 gas-aiagent-core 的宿主，非 Node 常駐 proxy 的宿主 | 需把 freellmapi 換成 GAS 可跑的形態（不可行，Express 需常駐） | 無法承載 Node/Express 常駐程序 | 不適用於跑 freellmapi |
| **Serverless** | ⚠️ 勉強 | 無狀態函式＋外部持久化（DB/Redis）存 rate-limit ledger 與 bandit 狀態 | 需重構 freellmapi 為無狀態、冷啟動可接受 | 狀態外移、冷啟動延遲、bandit 學習狀態需持久化 | 可跑但偏離 freellmapi 的 local-first 設計 |
| **VPS** | ✅ 可以 | 常駐 Node 20+ 跑 Express proxy | 需一台 VPS；**與你判 Openship 時「我用 VPS 不是為了開服務」的立場衝突** | 月費、維運、常駐 | 最直接可跑 freellmapi |
| **私有機器** | ✅ 可以 | 常駐 Node 20+ 跑 Express proxy | 需一台常開機的機器（如 N100 mini-PC）；**與執行環境三選項的「自架實體」同題** | 需常開機、耗電/噪音、維運 | 可跑，但依賴機器常在線 |

**一步一步接上個人 AI 入口**（以 VPS/私有機器為例，因 GAS 不可行）：

```
1. 準備環境（Node 20+）
   node -v   # 需 >= 20

2. 取得 freellmapi 並安裝
   git clone https://github.com/tashfeenahmed/freellmapi.git
   cd freellmapi
   npm install

3. 設定 Provider 金鑰（含私有訂閱，指向你的 OpenAI 相容 endpoint）
   # 依 README 的 Keys 頁，把 chat/embedding/image/audio 指到你的 endpoint
   # 例：本地 Ollama / vLLM / 遠端 gateway

4. 啟動 proxy（常駐）
   npm start   # 預設監聽 /v1，OpenAI 相容

5. 把個人 AI 入口的 LLM Provider 指到 freellmapi 的 /v1
   # 你的 app 後端（gas-aiagent-core 的 LLM Provider 抽象）改 base_url 到 freellmapi
   # 即「接既有 LLMGateway」方向（下一步清單第 79 條三選一之一）
```

**與你既有立場的衝突點（明確指出）**：
- **GAS 路線與 freellmapi 不相容**：gas-aiagent-core 的 Exec Provider 無實作、不能跑程式碼，且 GAS 無法承載 Node/Express 常駐 proxy。若你的入口走 GAS 白嫖路線，freellmapi 不適用——兩者是不同執行環境。
- **VPS 與你「不是為了開服務」的立場衝突**：你判 Openship 時明講「我用 VPS 不是為了開服務」。選 VPS 跑 freellmapi 需重新評估是否違反該立場。
- **私有機器與執行環境三選項同題**：跑 freellmapi 的「自架實體」正是你尚未定案的三選項之一，ROCK 3C（1GB SBC）已 Reject，需另選機型。
- **MultiProvider 方向未定**：下一步清單第 79 條三方向（接既有 LLMGateway / 自建 / App 內嵌）尚未比較。freellmapi 屬「接既有 LLMGateway」方向，但你的第二大腦已判 OmniRoute 採用，接 freellmapi 與接 OmniRoute 是同一方向的兩個候選。

**結論**：GAS 不能跑 freellmapi（執行環境不相容）；Serverless 需重構且偏離 local-first 設計；VPS 與私有機器皆可跑，但前者與你「不是為了開服務」的立場衝突、後者與執行環境三選項同題。**在執行環境三選項與 MultiProvider 方向（第 79 條）定案前，接 freellmapi 的落地應先解這兩題，而非直接選環境。**
