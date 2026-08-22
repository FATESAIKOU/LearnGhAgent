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
| **OmniRoute**（第二腦：Accept, draft） | 本機開源 AI gateway，單一 OpenAI 相容 endpoint，統一 250+ Provider，聚合免費額度 | 個人/本機環境；要統一 Endpoint 切 Provider；「解耦」優先於「細緻路由」 | 需開機常駐 proxy；免費額度來源變動；僅「解耦/切換」非「細路由決策」 | app 與 provider 解耦，切換/cost 優化；無需自己兜 gateway |
| **LiteLLM**（第二腦：對照組, 未評） | Python SDK/Proxy，100 Provider 統一接，round-robin/fallback 等基礎路由 | Python 專案；要 SDK 彈性而非 standalone proxy；接受輕度路由 | 路由演算法偏 basic，少「能力分階/訊號驅動」；要自己寫進既有 app | 統一 Provider 存取 + 基礎切換/fallback，適合嵌入 app |
| **OpenRouter**（第二腦：對照組, 未評） | 商業 SaaS，單一 endpoint 掛大量模型，request/response 一致 | 接受第三方 SaaS 集中路由與定價；不在乎資料出本機 | 資料經第三方；固定費用 markup；不適合自託開放模型 | 免架設即用多模型，聚焦「切模型」而非自建 infra |
| **（思考方式）自兜一層 LLM client wrapper** | 自己寫個薄抽象層，讓 app 只 call 一個 local endpoint，切 target | 專案夠小；不介意 handle 各 provider 的細微差別 | 每個 provider 的怪異都要自己處理；重造輪子 | 與「理解優先/先自己兜」準則一致，學到本質但不疊演算法 |

### 各替代切入點差異

- **Switchyard** 最特別在「**協議翻譯 + 細粒路由演算法**」兩者同體，且提供 **libsy 可嵌入**（決策與 call 分離）。切入點：給「已有 harness/gateway」補一層決策。
- **OmniRoute / LiteLLM / OpenRouter** 屬「**統一切換**」導向——把「接哪些 Provider」這層解耦，但路由決策較薄。切入點：單一 endpoint 對多 Provider。
- **自研 wrapper** 切入點：最小化、理解本質、不引入第三方層。

與使用者決策的落點：若依 DeepSeek V4「降低 Model Routing 優先級」+ 準則「先自己兜、MVP→Feature 看是否影響 workflow」，**Switchyard 不應被當「新研究方向」投入，而是作為已 Accept 的 OmniRoute（decoupling）路線上的「細部路由補強」選項**，且其 pre-alpha 狀態正好符合「不夠穩定→先自己兜」的觸發條件（但「自己兜」指的是自己寫一層，而非導入一套 pre-alpha 依賴）。

**結論**：Switchyard 解決「agent 原生語法 ↔ 開放模型 + 多模型路由」的解耦與路由問題；但其「精準 Model Routing」主體與使用者 stable 判定「降低 Model Routing 優先級」直接衝突，故正確用法是把它當 OmniRoute 路線的補充（第二腦的 decoupling 目的），不是新的研究方向。導入前須先明確「解耦（已 Accept）」與「細路由（他降優先）何者是要做」。
