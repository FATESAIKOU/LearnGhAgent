# sub2api 技術解析報告

> 標的：`Wei-Shaw/sub2api`（GitHub: https://github.com/Wei-Shaw/sub2api）
> 定位：AI API Gateway Platform for Subscription Quota Distribution（訂閱額度分發平台）
> 統計（2026-09-15 快照）：Go 為主、LGPL-3.0、約 41.6k stars / 8.7k forks、建立於 2025-12-18、當日活躍
> 來源：repo README（英/中/日三語）、`docs/`（PAYMENT、COMPOSITE_GROUPS、ASYNC_IMAGE_TASKS、PLUGIN_DEVELOPMENT 等）、`backend/internal` 結構、openspec changes。凡「作者未明寫、為通用技術背景或推測」處，皆於文中標明。

---

## 1. 這個技術解決什麼問題？

**一句話**：sub2api 把「一個或多個 AI 產品的付費訂閱帳號（subscription）的額度」，轉成「一個標準 OpenAI 相容 API 端點 + 多把 API Key」，讓多個下游使用者共用這批訂閱額度，並由平台負責認證、計費、排程與轉發。

具體來說，它解決的是以下複合問題：

- **單一訂閱額度只能被單一帳號使用**：Anthropic、OpenAI、Gemini、Grok 等產品的訂閱方案通常以「單一登入使用者」為單位，訂閱者的用量額度無法直接以 API 形式拆分給別人。
- **訂閱與 API 計費是兩種不同的計價模型**：訂閱（subscription）通常在額度內是固定月費（邊際成本 0），而官方 API 按 token 計費。兩者無法直接互通，sub2api 把它們橋接起來。
- **多人共用訂閱時，缺乏治理**：誰用了多少、怎麼公平排程、怎麼防止單一使用者霸佔額度、怎麼避免觸發上游風控（單一帳號被同時大量並發），都需要一個中間層處理。
- **多供應商帳號分散**：團隊或「拼車（拼車共享成本）」經營者手上往往有多個供應商的訂閱帳號，需要一個統一入口把這些帳號聚合成單一 API 服務對外提供。

**模糊之處（作者未明寫、需使用者注意）**：
1. 「解決」的邊界含糊——repo 自己註記「使用本專案可能違反 Anthropic 等上游供應商的服務條款」，也就是說它解決的是**技術上的額度分發問題**，但同時是**服務條款上的灰色地帶**。README 在「Important Notice」明確把 ToS 風險與法律風險丟給使用者自負。
2. 「拼車共享」是 description 中出現的商業情境，但 README 功能面沒有把「拼車」定義為一個第一等公民的產品形態，而是散落在多帳號管理、計費、支付等機制裡。
3. 它同時被宣稱是「gateway platform」，但**它跟「LLM API Gateway」是不同層的東西**——它不做 provider 協定抽象與自由切換 250+ provider，而是管理**固定的少數供應商訂閱池**（詳見 §4 對照）。這個詞的選用容易讓人誤會。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章中明確提到的背景

- **訂閱與 API 雙軌制**：AI 產品同時存在「訂閱（consumer product）」與「API（developer product）」兩條通路。訂閱對重度使用者更划算（額度內固定費用），API 則按量計費。使用者想要「用訂閱的價格、走 API 的形態」，兩者中間沒有官方橋。
- **Grok / xAI 的訂閱 proxy 機制**：README 明確提到 Grok 訂閱帳號走 `cli-chat-proxy.grok.com` 這個訂閱 proxy，也就是說某些供應商**自己就提供了把訂閱變 HTTP API 的通道**。sub2api 是去對接這種既有通道，而非發明新協定。
- **ToS 風險**：README 直接聲明「使用本專案可能違反 Anthropic 等上游供應商的服務條款」。這說明問題本身存在於「供應商禁止但技術可行」的區域——多數供應商明確不允許分享訂閱額度，這正是需求與條款衝突的來源。

### 2.2 通用技術背景（作者未明寫，屬背景補足）

- **OAuth vs API Key 兩類憑證**：訂閱帳號多數透過 OAuth 授權取得（使用者登入即授予平台以他的身分呼叫），而開發者 API 用靜態 API Key。sub2api 把兩者都納入「帳號」抽象，正是要處理這個憑證異構。
- **token 級計費需要可觀測的中間層**：官方 API 的回應不一定帶「這個請求消耗多少訂閱額度」的明細；sub2api 必須自己攔截、統計、換算成可計費的數字，這是「代理型 gateway」天然要承擔的職責。
- **並發與風控**：供應商對單一帳號有 rate limit / 風控（例如 Grok 的 `429` 與 quota header）。多人共用同一個帳號會瞬間觸發風控，所以需要「智慧排程 + sticky session」把同一使用者的請求釘在同一個帳號上，減少切換造成的風控風險。README 特別提醒 Nginx 要開 `underscores_in_headers on` 否則 `session_id` header 會被丟掉、sticky routing 失效——這是真實運維痛點。
- **「拼車」是供需失衡下的自然產物**：訂閱價格對個人偏高、而訂閱額度常有人用不滿。共享成本（拼車）是市場化的解法，但缺乏現成的治理工具，於是出現 sub2api 這類工具填補（此為通用背景推測，非 repo 明寫）。

---

## 3. 這個技術是如何解決該問題的？

只描述「怎麼做」，不評論好壞。

### 3.1 總體架構

```
     使用者端（client）
        │  OpenAI 相容協定 /v1/*
        ▼
   ┌─────────────  sub2api  ─────────────┐
   │  Handler 層（HTTP 路由、協定相容）       │
   │  Service 層（認證、計費、排程、帳號管理）  │
   │  Gateway 核心（請求轉發、額度扣減）     │
   │  資料層：PostgreSQL（持久化）          │
   │          Redis（快取 / 並發鎖 / session）│
   └────────────────┬───────────────────┘
                     ▼ 轉發
        上游訂閱 proxy / 官方 API
        （cli-chat-proxy.grok.com、api.x.ai、
          Anthropic、Gemini、OpenAI 等）
```

### 3.2 核心機制拆解

| 機制 | 做法 |
|---|---|
| **多帳號管理** | 支援 OAuth（Grok / OpenAI / Gemini / Claude）與 API Key 兩類上游帳號；每帳號存 `access_token`、`refresh_token`、`base_url`、`subscription_tier`、`entitlement_status` 等欄位；OAuth 走 PKCE 流程不需 commit 密鑰 |
| **API Key 配發** | 平台產生 `sk-` 前綴的 API Key 給下游使用者；Key 綁定到 group（提供者池），用於認證與 ACL（`api_key_prefix`、`trust_forwarded_ip_for_api_key_acl`） |
| **token 級計費** | 攔截上游回應統計 token 用量，換算成可計費數字；`default.rate_multiplier` 調整倍率；有 circuit breaker（`billing.circuit_breaker`）在計費錯誤時 fail-closed |
| **智慧排程 + sticky session** | 依帳號可排程性（額度、並發、rate limit、`429`/`401`/`403` 回應）選帳號；sticky session 把同一使用者釘在同帳號，靠 `session_id` header 維持；`401` 暫移除、`403` 視為權限失敗、`429` 進 cooldown |
| **並發 / 速率限制** | per-user 與 per-account 並發上限（`user_concurrency`）、rate limiting；OpenAI Responses WebSocket ingress 另設 session 生命週期與連線數上限（`max_ingress_connections_per_api_key`） |
| **Composite Groups** | 管理員路由層：依請求的 model 選具體供應商（exact/prefix match、endpoint、priority），可內建偵測（`claude-*`→Anthropic、`gemini-*`→Gemini 等）；不明 model fail-closed 不猜 |
| **內建支付** | EasyPay（Alipay/WeChat）、Alipay Direct、WeChat Pay Direct、Stripe；使用者自助儲值，不需另部署支付服務；前端只暴露 Alipay / WeChat 兩按鈕，admins 各選一來源 |
| **Admin 儀表板** | 使用者 / 帳號 / 計費 / 監控管理；支援 iframe 嵌入外部系統（如 ticketing） |

### 3.3 具體供應商對接例：Grok / xAI

```
Grok OAuth 帳號 ──► cli-chat-proxy.grok.com/v1（訂閱 proxy）
Grok API Key 帳號 ──► https://api.x.ai/v1/responses
兩者統一以 OpenAI 相容 Responses 對外：
  /v1/responses、/responses、/backend-api/codex/responses
另有 /v1/messages（Anthropic 相容）、/v1/chat/completions
媒體：/v1/images/generations、/v1/images/edits、/v1/videos/...
```

- 對 OAuth 帳號走訂閱 proxy；對 API-key 帳號走官方 API。
- xAI quota 是**被動**的：sub2api 不發明額度值，而是記錄上游回應的 rate-limit header；在第一次可用回應前顯示「unknown」。
- Grok 媒體請求有 media-eligibility 探測，避免用無媒體權限的帳號送圖/影片請求。

### 3.4 關鍵設計約束

- **fail-closed**：計費錯誤時關閉（circuit breaker）、不明 model 時關閉，避免「帳算錯還繼續放行」。
- **安全硬體化**：URL allowlist（可限 HTTPS-only）、response header 過濾、CSP、forwarded IP 信任邊界（`trusted_proxies` vs legacy raw header）、TLS fingerprint profile（`tlsfingerprint`）。README 用長篇幅警告 HTTP 明文風險。
- **模式**：`RUN_MODE=simple` 隱藏 SaaS 計費，供個人 / 內部團隊用；`SIMPLE_MODE_CONFIRM` 保護正式環境。

> 以上屬「機制層」描述。作者未明寫之處（例如具體排程演算法是 round-robin 還是權重）未在此展開，屬資料不足。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 與第二大腦的對照結果（重要）

**查詢方式**：以 mybrain-read skill 讀取 `/tmp/mybrain`（FATESAIKOU/MyBrain 鏡像）的骨幹檔（`技術/技術評估/判定總表.md`、`抽象理解/本質洞察/技術取捨準則.md`），並 grep `new-api`、`one-api`、`LiteLLM`、`subconverter`、`clash`、`sing-box`、`subscription`、`gateway`、`拼車` 等關鍵詞。

**結論一：第二大腦沒有 sub2api、也沒有任何「訂閱額度分發 / 拼車」類工具**（new-api、one-api、subconverter 皆 0 命中；clash/sing-box 也無關）。→ 直接聲明：此主題在第二大腦中**無記錄**，以下替代方案不冒充他的舊結論。

**結論二：第二大腦有「LLM API Gateway」一類工具的判定，且是「不採用」——這與 sub2api 自稱 gateway 有語意衝突，是對照最有價值處**：

| 檔案 | 判定 | 關鍵理由 |
|---|---|---|
| [OmniRoute](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OmniRoute.md) | 不採用（2026-09-06 推翻先前採用） | 名目 250+ provider，零憑證實測只有 4 個模型能回話；限制是每日 IP 額度而非 RPM，並行 agent 會燒光整天額度 |
| [freellmapi](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/freellmapi.md) | 不採用 | 檢討後結論是「不做 LLMGateway／免費聚合這一層」：真正握 GPU 的供給者只有個位數 |
| [Switchyard](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Switchyard.md) | 不採用 | 整條 Model Router 線放棄，為個位數做路由政策層，抽象成本高於省下的切換成本 |

> 以上三份皆 `generated.by: opencode/claude-code + status: draft`（**AI 草稿，未經使用者 review**）。引用僅說明「第二大腦有無此類判定」，不是使用者拍板過的結論。
> URL：https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OmniRoute.md（同目錄下 freellmapi.md、Switchyard.md、判定總表.md）

**衝突說明**：sub2api 用「gateway」這個詞，但他的第二大腦已經判定「LLM Gateway／provider 聚合」整條線不採用，理由集中在「**真正供給只有少數實體，聚合抽象放大的是名目數量不是實際供給**」。**然而 sub2api 與那條線不是同一件事**：sub2api 聚合的是「訂閱額度」而非「免費 provider」、供給來源是「使用者自己持有的付費訂閱」，不是免費聚合。所以不能直接拿「LLM Gateway 不採用」當成「sub2api 也不該看」。這個區分必須講清楚，否則會錯誤地關掉一個他沒評估過的主題。

**結論三：他的技術取捨準則（`技術取捨準則.md`，骨幹 tag，AI draft）適用於評估 sub2api 的「要不要自己兜」**：
- 原則一「理解優先」：不夠穩定或不熟就**先自己兜**，MVP 是理解的驗證點。「用現成的比較快」打不動他。
- 原則二「MVP→Feature 唯一閘門」：**能不能影響他個人 workflow** 才是進 Feature 的判準。
- 原則三「Reject≠沒價值」：被拒的工具仍可抽取需求理解與方案方向。

**套用**：sub2api 是**年輕專案（2025-12-18 建立）、單人作者（Wesley Liddick）**——依其原則一，「單人維護 / 太年輕」反而是「先自己兜」的觸發條件，不是「直接採用」的理由。若他要碰這塊，照他的判準會傾向自己兜一個理解 MVP，而非直接部署 sub2api。此為推測性引伸，非他本人對 sub2api 的結論。

---

### 4.2 替代方案與 DA 表

以下方案**第二大腦均無既有判定**（grep 無命中），屬通用技術知識層：

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **New API / one-api**（開源 AI 渠道管理 / 聚合 gateway） | 集中管理多個「渠道」（provider 帳號 / 訂閱），提供統一 OpenAI 相容 API Key 與 token 計費，類似 sub2api 的管理面 | 需要自己維運後端（多為 Go + DB）；要對上游帳號池負責 | 與 sub2api 同屬 ToS 灰色地帶；渠道池風控需自行維護；專案間維護者品質差異大 | 得到一個「多帳號 + 統一 API Key + 計費」的自管 gateway |
| **LiteLLM**（LLM API 抽象 / 轉發層，Python） | 統一 OpenAI 相容介面，對 100+ provider 做協定翻譯、路由、fallback、計費代理 | 需要 Python 環境；適合「協定層抽象」而非「訂閱額度共享」 | 不做訂閱帳號 OAuth 管理與支付；主要處理 API Key provider | 快速把多個 API provider 對齊到單一介面，但不解決訂閱拆分 |
| **subconverter（subconverter / acl4ssr 系）** | 把 Clash / sing-box 等訂閱連結格式轉換為另一種訂閱格式（節點層面） | 面向「代理節點訂閱」而非「AI API 額度」；使用者用的是機場/節點 | 與 AI API 額度分發是**不同問題域**，無法直接替代 | 只做訂閱格式轉換，不做 API 計費與共享 |
| **直接自兜 MVP（對應他的理解優先準則）** | 用最少程式碼（如一個 Go/Python 反向代理）接單一訂閱 proxy，記錄用量、給有限 API Key | 需要理解目標供應商訂閱 proxy 的協定；能接受 MVP 即止 | 不穩定、功能單一；但依其準則這正是「理解本質」的目的 | 以最低成本理解「訂閱→API 額度」的本質，再決定下一步 |

### 4.3 各方案切入點差異

- **sub2api / New API 系**：切入點是「**額度治理與商業化**」——把訂閱額度當成可配發、可計費、可排程的資源池。最接近 sub2api 的定位。
- **LiteLLM**：切入點是「**協定抽象**」——統一介面，但不碰「訂閱額度共享」與「支付」。它解決的是 API 的多樣性，不是訂閱的分配。
- **subconverter**：切入點是「**格式轉換**」——完全不同問題域（代理節點 vs AI API），列出來是為了劃清界線，避免名稱混淆（「sub2api」易被誤會與「subscription 轉換」同類）。
- **自兜 MVP**：切入點是「**理解**」——對照他的準則，這是他個人最可能採取的路徑。

### 4.4 與第二大腦的衝突彙整

| 我的結論（§4） | 第二大腦既有 | 衝突 / 說明 |
|---|---|---|
| sub2api 是「gateway」 | LLM Gateway / provider 聚合判定為不採用 | **表面衝突，實為不同層**——sub2api 聚合訂閱額度而非免費 provider；不可直接套用「不採用」 |
| sub2api 適合直接部署使用 | 原則一「不穩定或不熟先自己兜」+ 原則三「單人維護觸發自兜」 | **實際衝突**——年輕 + 單人作者，照他的判準傾向自己兜 MVP，而非部署現成 |

---

## 附錄：資料來源與信任層級

| 來源 | 內容 | 信任層級 |
|---|---|---|
| sub2api README（英） | Overview / Features / Grok / Simple Mode / 部署 / 安全 | repo 作者明寫，屬「文章內容」 |
| sub2api docs/PAYMENT.md、COMPOSITE_GROUPS.md | 支付 / 路由層細節 | repo 作者明寫 |
| sub2api backend/internal 結構 | 模組分工（handler/service/domain/payment/pkg） | 由程式結構觀察 |
| MyBrain 判定總表.md、OmniRoute/freellmapi/Switchyard.md | LLM Gateway 線判定 | AI 草稿，未 review |
| MyBrain 技術取捨準則.md | 理解優先 / Reject≠沒價值 / MVP 閘門 | AI 草稿（含「原話」為本人直接引用） |
