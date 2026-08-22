# Switchyard — 大模型路由工具 技術分析報告

> 標的：NVIDIA-NeMo / Switchyard（https://github.com/NVIDIA-NeMo/Switchyard）
> 本報告依「技術解析助理」Step 3 產出，僅回答 5 個問題，不延伸。
> 資料來源：repo README / core_concepts / routing overview / llm_classifier / stage_router / getting_started（2026-08-21 快照），並對照第二大腦 FATESAIKOU/MyBrain 的既有判定。

---

## 1. 這個技術解決什麼問題？

Switchyard 解決的是 **「既要保持 coding agent 原生 API 語法、又要能把流量導到開放模型後端」的雙重隔離問題**。具體拆成三個被解決的子問題：

1. **協議不通**：既有 coding agent（Claude Code、Codex）各自講「自己的 API 語法」（Anthropic Messages / OpenAI Chat / OpenAI Responses）。要把它們導到 vLLM、NVIDIA NIM、Ollama 等開放模型後端時，語法對不上，agent 得改 client，或後端得自己實作多套協議。
2. **流量怎麼分**：同一個請求到底該送給弱/強模型、還是送給哪個後端，需要一個「可描述、可比較、可換演算法」的路由決策層，而不是寫死在每個 app 裡。
3. **營運可觀察**：跨多後端的請求數、錯誤、延遲、token 消耗、路由本身的額外開銷沒有統一度量。

若「問題描述含糊」之處：README 宣稱「Not for production use、pre-alpha」，因此「它解決的問題」在**生產環境語境下尚未被證明有效**——目前的問題定義是「能不能把 agent 指到開放模型並做路由」，而非「已在生產規模下被驗證的路由」。

---

## 2. 這個問題為什麼會發生？（背景）

分「文章中明確提到」與「通用技術背景」兩類。

### 文章中明確提到的

- **Coding agent 綁定自家 API**：Claude Code 與 Codex 各走 Anthropic Messages 與 OpenAI Chat/Responses 格式。要轉向開放模型，agent 端不想改，後端則難同時兼顧多格式（README「agent keeps speaking its native API while served by vLLM/NIM/Ollama」）。
- **路由決策成本高**：一個 agent session 大量 turn 都叫 LLM，若每次都由「LLM judge」再叫一次模型來決定，成本與延遲爆炸。stage_router 的文件說明這是關鍵動機——用 tool-result 訊號代替每個 turn 的額外分類呼叫。

### 通用技術背景（非文章明說）

- **模型能力價差分化**：同一類任務，弱模型夠用、強模型更貴。需要「能力取捨」層，把 routine 工作送弱模型、把 hard/error-recovery 送強模型。
- **API 格式碎片化**：OpenAI、Anthropic、各開源 inference server（vLLM/Ollama）的 request/response schema 不互通，促使「Provider 中立中間層」的需求。
- **自託管開放模型的興起**：本地 vLLM / NIM 提供 OpenAI 相容 endpoint，但要從外部以單一語法接進一群 agent，仍需一層做協議翻譯與路由。

---

## 3. 這個技術是如何解決該問題的？

### 核心機制總覽

兩個 runtime surface 共用同一組 Rust 路由核心：

- `switchyard-server`：獨立 HTTP proxy，吃 native TOML deployment，暴露 OpenAI Chat / OpenAI Responses / Anthropic Messages 三個 endpoint。
- `switchyard-libsy`：可嵌入的 Rust library，**演算法「只做決策、不自己 call model」**——選出 target 後把 model call 交還給 host app，讓它 drop 進已有的 proxy / gateway / agent runtime。

### 三層抽象（TOML deployment）

| 層 | 定義 | 例 |
|---|---|---|
| **LLM client** | 上游 base_url、wire format（openai_chat / openai_responses / anthropic_messages）、credential env var、retry | `[llm_clients.openrouter]` |
| **Target** | 一個上游 model id + 呼叫它的 client | `[targets.weak]` |
| **Route** | client 可見的 model id + 路由演算法 | `[routes.smart]` |

重點：**provider transport 與 routing policy 分離**。多個 target 可共用一個 client，多個 route 可重用同一 target。Credential 只走 env var（`api_key_env`），不進 TOML。route 的 `id` 是 client 送進 `model` 欄的 ID；server 用 `GET /v1/models` 列 route ID，且帶 Codex 相容的 `models` array。

### 路由演算法集合（C1 已列，此處註明決策機制）

| 演算法 | type | 決策機制 | 成本/副作用 |
|---|---|---|---|
| passthrough | `passthrough` | 不做決策，固定一 target | 最低 |
| random | `random` | 依權重固定流量拆分（A/B、基線） | 最低 |
| LLM classifier | `llm_classifier` | 用 classifier target 回傳結構化 verdict（`p_solve` / `capability_boundary`），`p_solve ≥ threshold` 走 weak，否則 strong；有 `classify_trigger`（every_request / user_turn / new_session）控制 judge 何時跑 | **每次 judge 多一個 model call**；verdict 需 schema-valid JSON，失敗 fail-open 到 strong |
| stage_router | `stage_router` | 由 conversation 的 **tool-result history** 推論 agent 處於哪一 stage：wrong（severity/spinning/exploring）→ capable，progress（recent_production_intensity）→ efficient；`confidence_threshold` 門檻，corroborative scoring，critical-error 硬覆寫 | 多數 turn 不加額外 model call，只加分類訊號；`capable_first` picker 是 experimental |
| escalation_router | `llm_classifier`（mode=escalation） | 全部先 weak，judge 讀答案決定是否 escalation 到 strong | 每次 escalation 多一個 judge call |
| advisor_gate | `advisor` | 一個 model 服全部 turn，強 reviewer 核准其「done」或退回 redo plan | 每次 done 多一個 judge call |
| subagent | `passthrough`/`stage_router` 加 `subagents` | 讓 sub-agent 用跟 parent 不同的路由政策 | 需 session 識別 |

### 協議中立與翻譯

- `switchyard-protocol`：定義 provider-neutral 的 request/response/message/content block/tool call/usage/streaming types，演算法在這些 type 上運作，而非 provider SDK 物件。
- `switchyard-translation`：在 openai_chat / openai_responses / anthropic_messages 之間轉換。client 保持原生 API，target 可用不同 upstream 協議。
- 支援 self-hosted target（vLLM 等 OpenAI-compatible），Switchyard 只送請求、不啟動/管理 model server。

### 營運度量

- Prometheus metrics：requests / errors / latency / tokens / routing overhead。
- 每個 response 帶 `x-model-router-selected-model` 路由標頭；`/v1/stats` 回報 stage-router 的 decision_source（override / tests_passed / dimensions / llm-classifier / fall_open）。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

Switchyard 屬「LLM 流量 proxy / API Gateway / Model Routing」問題域。以下是同級替代方案與 DA 表，並**對照第二大腦 FATESAIKOU/MyBrain 的既有判定**。

### 第二大腦對照（重要）

| 標的 | 第二大腦判定 | 信任層級 / 時間 | 對本報告 §4 的影響 |
|---|---|---|---|
| **Switchyard** | **無任何評估紀錄**（grep「switchyard」零命中） | 查無 | 無法引用個人判定，只依 repo 事實與通則 |
| **OmniRoute** | **Accept**——「本質是 LLM Provider 解耦層（API Gateway），因解耦所以有學習必要，MVP 階段導入」 | AI draft（opencode/deepseek-v4-pro, status: draft）2026-07-26 | 已拍板「LLM gateway 解耦要學」，Switchyard 屬同域，需與之並列 |
| **LiteLLM / OpenRouter / Portkey** | 無獨立評估，但在「下一步清單」被列為 OmniRoute 的「對照組」，標明「MVP 階段要比較多個應用，那個比較還沒做」 | draft｜2026-08-11 | 對照組選用與第二腦一致，建議納入比較 |
| **DeepSeek V4** | **human 本人 stable**：「**降低 Model Routing 研究優先級**——不要把心力花在『如何精準路由不同 LLM』的 legacy 機制上，把精力集中在 Domain 領域知識（AxrossRecipe 商業邏輯）」 | human:fatesaikou, **stable**｜2026-04-26 | **與本標的直接衝突**（見下「衝突聲明」） |

#### ⚠️ 衝突聲明（對照最有價值之處）

**Switchyard 就是「如何精準路由不同 LLM」的模型路由器**，而使用者本人（human, stable）在 DeepSeek V4 明確講「不要把心力花在 Model Routing 的 legacy 機制上」。這是**直接衝突**：照此準則，Switchyard 的路由演算法價值應被降級看待——它的「解決問題」即便成立，也可能踩在「使用者判定不該優先研究」的軌道上。本報告 §4 因此把 Switchyard 定位成「**已拍板（OmniRoute, Accept）的 decoupling 路線上的『路由細化層』補充，而非新的研究方向**」，並在替代方案以「解耦 / 路由分層」的用途切開，避開與「他要集中精力在 Domain」的衝突。

另註：OmniRoute 判定是 **AI draft（未經 review）**，且該檔的「結論」是 `process:learn-gh-agent` 產出後歸入的（frontmatter status: draft）。故「Accept」是他可推翻的草稿結論，不是他本人 review 過的定稿；引述時我標「draft」。

### DA 表（替代方案）

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Switchyard（本標的）** | Rust proxy/libsy，協議翻譯（OpenAI↔Anthropic）+ 多演算法路由 + Prometheus metrics | 有 Rust 工具鏈；接受 pre-alpha/API 未到 v1.0；需自建/自備後端 | 每次 judge（llm_classifier/escalation/advisor）多一個 model call 與 schema 依賴；capable_first 未經 bench；不 production-ready | 既有 agent 不改語法即可接開放模型，同一個 proxy 內做 A/B、訊號路由、自寫演算法 |
| **OmniRoute**（第二：Accept, draft） | 本機開源，統一 OpenAI 兼容 endpoint，**340 Provider / 90+ free / 1200+ models / 43 provider pools / ~1.53B 免費 token/月**（2026-08-22 live metadata，v3.8.50，53k★） | 個人自機環境；要統一 Endpoint 切 Provider；「解耦」優先於「細路由」 | 需開機常駐 proxy；免費額度來源變動；僅「解耦/切換」非「細路由決策」 | app 與 provider 解耦，切換/cost 優化；無需自己兜 gateway |
| **LiteLLM**（第二腦：對照組, 未評） | Python SDK/Proxy，100 Provider 統一接，round-robin/fallback 等基礎路由 | Python 專案；要 SDK 彈性而非 standalone proxy；接受輕度路由 | 路由演算法偏 basic，少「能力分階/訊號驅動」；要自己寫進既有 app | 統一 Provider 存取 + 基礎切換/fallback，適合嵌入 app |
| **OpenRouter**（第二腦：對照組, 未評） | 商業 SaaS，單一 endpoint 掛大量模型，request/response 一致 | 接受第三方 SaaS 集中路由與定價；不在乎資料出本機 | 資料經第三方；固定費用 markup；不適合自託開放模型 | 免架設即用多模型，聚焦「切模型」而非自建 infra |
| **（思考方式）自兜一層 LLM client wrapper** | 自己寫個薄抽象層，讓 app 只 call 一個 local endpoint，切 target | 專案夠小；不介意 handle 各 provider 的細微差別 | 每個 provider 的怪異都要自己處理；重造輪子 | 與「理解優先/先自己兜」準則一致，學到本質但不疊演算法 |

### 各替代切入點差異

- **Switchyard** 最特別在「**協議翻譯 + 細粒路由演算法**」兩者同體，且提供 **libsy 可嵌入**（決策與 call 分離）。切入點：給「已有 harness/gateway」補一層決策。
- **OmniRoute / LiteLLM / OpenRouter** 屬「**統一切換**」導向——把「接哪些 Provider」這層解耦，但路由決策較薄。切入點：單一 endpoint 對多 Provider。
- **自研 wrapper** 切入點：最小化、理解本質、不引入第三方層。

與使用者決策的落點：若依 DeepSeek V4「降低 Model Routing 優先級」+ 準則「先自己兜、MVP→Feature 看是否影響 workflow」，**Switchyard 不應被當「新研究方向」投入，而是作為已 Accept 的 OmniRoute（decoupling）路線上的「細部路由補強」選項**，且其 pre-alpha 狀態正好符合「不夠穩定→先自己兜」的觸發條件（但「自己兜」指的是自己寫一層，而非導入一套 pre-alpha 依賴）。

**結論**：Switchyard 解決「agent 原生語法 ↔ 開放模型 + 多模型路由」的解耦與路由問題；但其「精準 Model Routing」主體與使用者 stable 判定「降低 Model Routing 優先級」直接衝突，故正確用法是把它當 OmniRoute 路線的補充（第二腦的 decoupling 目的），不是新的研究方向。導入前須先明確「解耦（已 Accept）」與「細路由（他降優先）何者是要做」。

---

## 5. User Q&A

> 本節收錄使用者對本技術的追問（Round R2，2026-08-22）。既有 QA 不可刪改，僅可追加。

### Q1：這東西跟 OmniRoute 比，支援 Model 廣度有沒有差異？我 Accept OmniRoute 是因為他聚合很多免費額度

**A**：**有，而且是結構性的差異，不是數字大小的差異。** 兩者「支援 Model 廣度」的來源根本不是同一層，直接比 Provider 數量會誤判。

| 面向 | Switchyard（NVIDIA-NeMo） | OmniRoute（diegosouzapw） |
|---|---|---|
| Provider 目錄 | **無內建**。必須使用者手寫 TOML 逐個 `base_url`＋`api_key_env` 指定 | **內建聚合**。340 Provider / 90+ free / 1200+ models / 43 provider pools / ~1.53B 免費 token/月 |
| 免費額度聚合 | **無**。不收集任何免費來源 | **有，是核心賣點**。聚合 90+ 免費 Provider 與 40+ pool |
| 廣度來源 | 使用者的手動 route 清單 | repo 內建維護的 provider 資料庫 |
| 更新方式 | 你自己改 TOML | 官方 3.8.50 持續更新（v3.8.47→3.8.50 由 250+ 升到 340） |
| 資料基準 | 需自備 API Key/額度 | 開箱即有免費 pool |

```
你的採納動機「聚合免費額度」
        │
        ▼
OmniRoute: 內建 → 開箱即用 ✅ 正中你動機
Switchyard: 無 → 你得自己把每一家免費額度寫進 TOML，等於你親自當 aggregation 層
```

**與第二大腦判定對照**（§4 已詳列）：第二腦 `OmniRoute.md` 判定為 Accept，理由是「本質是 LLM Provider 解耦層，有學習必要」，引用快照數字 250+ Provider（draft，未經你 review）。本次抓到官方 repo live metadata 為 **340 Provider / 1200+ models / 53k★ / 3.8.50**，廣度比快照更大。Switchyard 在第二腦 grep「switchyard」**零命中**，無既有判定。

**在「Model 廣度 / 免費額度」這條你真正在意的軸上：OmniRoute 完勝，Switchyard 是空白。**

**結論**：若你的採納判準是「聚合很多免費額度」，Switchyard 在這一項不構成對 OmniRoute 的替代——它根本沒有聚合層，Model 廣度要你手動拼。兩者不在同一層比較。

### Q2：我想要安裝這東西讓我的 claudecode 跟 opencode 能用，一步步的步驟為何（我已有 OllamaCloud / Claude 訂閱）

**A**：先講承接關係，再給一一步驟。**你的既有訂閱（OllamaCloud / Claude）就是 Switchyard 的「上游 client」**——你要在 `routes.toml` 裡把它們定義成 llm client + target，然後把 opencode 指到 `/v1`、claude code 指到 Anthropic endpoint。

**承接兩側的關鍵**：

| 工具 | 走什麼協定 | 指到 Switchyard 哪個 endpoint | 注意 |
|---|---|---|---|
| opencode | OpenAI 兼容 | `http://localhost:4000/v1` | 用 OpenAI Chat/Responses 口 |
| claude code | Anthropic Messages | `ANTHROPIC_BASE_URL=http://localhost:4000` | **不加 `/v1`**；auth 用 `forward_auth=true` 或 `api_key_env`+token |

**一階步驟（Switchyard，port 4000）**：

```bash
# 1. 安裝（Rust native server，pre-alpha）
cargo install --locked switchyard-server

# 2. 寫 routes.toml（把既有訂閱註冊成 llm_client + target + route）
cat > routes.toml <<'TOML'
[llm_clients.ollama_cloud]
type = "openai_chat"
base_url = "https://<你的 OllamaCloud endpoint>"
api_key_env = "OLLAMA_KEY"
[llm_clients.claude]
type = "anthropic_messages"
api_key_env = "ANTHROPIC_AUTH_TOKEN"
[targets.weak]
model = "deepseek-.../把你想走的 model id"
client = "ollama_cloud"
[targets.strong]
model = "claude-.../"
client = "claude"
[routes.smart]
targets = ["weak","strong"]
# 路由演算法（passthrough / random / stage_router ...）
TOML

# 3. 啟動 server
switchyard-server --config routes.toml --host 127.0.0.1 --port 4000

# 4a. opencode → 指到 OpenAI 口
# opencode.json:
#   "provider": { "baseURL": "http://localhost:4000/v1", ... }  ← 實際 model ID 填 route 的 id

# 4b. claude code → 指到 Anthropic 口
# 環境變數：
#   ANTHROPIC_BASE_URL=http://localhost:4000   （不加 /v1）
#   ANTHROPIC_AUTH_TOKEN=<你的 token>           （或 server 端 forward_auth=true）
```

**必須注意的坑**：
1. **`cargo install` 編譯**需 Rust toolchain，非一鍵 npm。
2. **`routes.toml` 你必須自己寫**——Switchyard 不給你 Provider 目錄，`base_url`/`api_key_env` 全要你填。
3. **pre-alpha**：README 明示 Not for production；API 到 v1.0 前還會大改。
4. 你的 Claude 訂閱走 `ANTHROPIC_AUTH_TOKEN`，OllamaCloud 走各自的 `api_key_env`——token 不進 TOML，只走 env。

**結論**：可行，但「讓 claudecode/opencode 能用」這一步沒有官方一鍵 setup，全部手動寫 TOML＋設 env，且預設只做 `passthrough` 才算「能用」，要路由再疊演算法。**你已「完整整理成功」claude/opencode 的 Hook/Skill/MCP 環境（MyBrain：追加功能/整理 claudecode-opencode 環境.md, human stable），導入 Switchyard 是再疊一層本地 proxy。**

### Q3：另外如果我想要安裝使用 OmniRoute 讓我的 claudecode 跟 opencode 能用，一階步驟？給我指令（我已有 OllamaCloud / Claude 訂閱）

**A**：OmniRoute 有**原生整合指令**，與 Switchyard 完全相反——它**開箱即用**，幾乎零 TOML 設定。它 boot 在 `localhost:20128`，且提供 `setup-opencode` / `setup-claude` 一鍵寫 config。

**承接關係**：opencode 走 OpenAI 兼容口，claude code 走 Anthropic 口，都指到 `localhost:20128`。你的 OllamaCloud/Claude 訂閱可透過 `omniroute` 的 provider pool 一起納入或走 `api_key` 手動註冊。

**步驟（OmniRoute，v3.8.50）**：

```bash
# 1. 安裝（npm global）
npm install -g omniroute

# 2. 啟動（boot localhost:20128，零 config 即用）
omniroute
#   或指定 profile
#   omniroute launch --profile <name>

# 3a. 一鍵接 opencode（自動寫 ~/.config/opencode/opencode.json）
omniroute setup-opencode
#    產生 provider: omniroute, npm:@ai-sdk/openai-compatible,
#    baseURL: http://localhost:20128/v1

# 3b. 一鍵接 claude code
omniroute setup-claude --profile <name>
#    寫 ~/.claude/profiles/<name>/settings.json
#    + 注入 ANTHROPIC_AUTH_TOKEN
#   （或手動 ANTHROPIC_BASE_URL=http://localhost:20128，不加 /v1）

# 4. 設定 model：直接填 auto / auto/coding 或 combo 名
#   opencode 側 model 填 auto
#   claude 側 model 填 auto
```

**與「你已接受 OmniRoute」的銜接**：第二腦 `下一步清單` 有「LLM APIGateway 試用（解耦）——OmniRoute」，對照組 LiteLLM/OpenRouter/Portkey，**尚未 MVP 驗證**；`OmniRoute.md` 判定 `Accept`（draft）。你現在是在執行那條下一步。

**坑**：
1. **節點開機常駐**（proxy 需要一直在跑），switchyard 一樣。
2. 免費 pool 來源會變動；部分是 OAuth/Cookie 型 executor，不是每個都純 API key。
3. `setup-claude` 是 profile 綁定，要 profile 名對齊。

**結論**：OmniRoute 對 claudecode/opencode 的接入**有官方一鍵 setup**，比 Switchyard 的「全手動 TOML+env」少很多步，且直接把免費/訂閱 pool 聚合好，正中你的採納動機。兩者都要求本地常駐 proxy，但 OmniRoute 的「廣度」是內建、Switchyard 是手動拼。

### Q3 附：Switchyard vs OmniRoute 對「我的 claudecode/opencode」落地難度對照

| 面向 | Switchyard | OmniRoute |
|---|---|---|
| 安裝 | cargo 編譯（Rust 需環境） | npm global（零編譯） |
| 設定 opencode | 手動寫 opencode.json + env | `omniroute setup-opencode`（自動寫） |
| 設定 claude | 手動 `ANTHROPIC_BASE_URL` + env | `omniroute setup-claude` + launch |
| config 檔 | 手寫 `routes.toml`（必填 base_url/目標） | 零 config 或 dashboard 圖形 |
| Model 廣度 | 手動建 list | 內建 340/90+ free/1200+ |
| 免費額度 | 無聚合 | 聚合 90+ free / ~1.53B token/月 |
| 就緒狀態 | pre-alpha, API 到 v1.0 前會大改 | release v3.8.50（53k★） |

**結論**：以「我要讓 claudecode/opencode 能用＋我要免費額度」為判準，OmniRoute 的落地路徑更短、廣度內建、直接命中你 Accept 它的理由；Switchyard 是「細路由/協定翻譯」強者，但不是「廣度/免費」工具，落地要全手動。**你的採納動機（聚合免費額度）指向 OmniRoute；Switchyard 只能當 OmniRoute 上的細部路由補強，單獨導入它不會帶給你免費額度。**
