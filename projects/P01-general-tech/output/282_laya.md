# Laya — 開源 System 1 決策引擎 技術分析報告

> 標的：`NandhaKishorM/laya`（https://github.com/NandhaKishorM/laya）／HF `convaiinnovations/laya`
> 本報告依「技術解析助理」Step 3 產出，僅回答 5 個固定問題，不延伸。
> 資料來源：repo README／BENCHMARKS.md／HF model card／AGENTS.md／pyproject.toml／tests/test_training.py（2026-09-26 快照），並對照第二大腦 FATESAIKOU/MyBrain 的既有判定。
> 本輪為 R1，無使用者提問，故無 `## 5. User Q&A`。

---

## 1. 這個技術解決什麼問題？

Laya 解決的是 **「軟體需要的是判斷，而 LLM 給的是文字」這個形態錯配**。具體拆成三個被解決的子問題：

1. **判斷被包在生成裡**：用生成式模型做分類／路由／打分時，模型產生的是散文或 JSON 字串，程式端必須解析、重試 schema、處理格式破裂。Laya 直接回傳**型別化的答案＋機率分布**，不生成任何文字，因此沒有東西可解析、也沒有東西可幻覺。
2. **判斷的延遲與成本結構不對**：一次決策要走完整 LLM 生成（或多次 judge call），延遲與 token 成本都綁在生成長度上。Laya 是**單次 forward pass**（T4 上單題 32.8 ms，批次 7.2 ms/題），把「判斷」壓成與生成脫鉤的固定成本。
3. **小模型判斷零件缺乏可下載、可微調、可在地部署的載體**：Jev（TypeSafe AI, 2026-09-15）把 System 1 模型做成 hosted API 與封閉權重。Laya 發布的是**訓練自己決策模型的程式碼與 Apache-2.0 權重**，外加 Router、CLI、HTTP（相容 Jev `POST /v1/systemone`）、MCP、LangChain、Docker、Nix 等接入面。

**問題描述中含糊、需指出的地方**（來自來源與影片觀點）：

| 模糊處 | 具體說明 |
|---|---|
| 「零幻覺」的範圍 | 只保證**不產生型別外的值**，不保證判斷正確。選項集合若寫錯，模型照樣在錯的選項裡選。這與影片觀點「格式保證正確、答案不保證正確」一致。 |
| 「快 N 倍」的基準 | README 的 Jev 數字（p50 236–276 ms）為**第三方量測**（AbdelStark、nibzard），Laya 自陳「never measured here、sample sizes and prompts differ」。雙方未在統一基準上測試。 |
| 「比 Jev 準」的範圍 | 是**argmax accuracy** 上的局部勝出（typed-decisions 0.766 vs 0.727）；在 **soft accuracy（0.471 vs 0.580）與原始 ECE（0.213 vs 0.144）**上仍是 Jev 領先。單看一方宣稱會誤判。 |
| 「開源復刻」的語意 | Laya 不是 Jev 原版權重，而是沿用 choice／score／noul 三原語的**同型回答形式**，權重來自 ModernBERT／mmBERT 骨幹＋自訓決策頭。它復刻的是「回答形態」，不是模型本體。 |

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的

- **生成模型與決策輸出的錯配**：軟體流程需要的是可依賴的型別化判斷（選哪個、幾分、成不成立），生成模型回傳的是文字；把文字解析回程式可依賴的東西需要 schema 重試與容錯。
- **System 1 vs System 2 的分工**：Jev 把「不做文字生成、直接回傳型別化判斷」定位為 System 1；Laya 沿用此定位，官方描述為 *keep control flow, deterministic rules, and side effects in code*、*avoid agent while loops when a software workflow can express the same behavior*，自稱 **「smart if statements」**。
- **封閉權重的採用障礙**：Jev 是 early access 的 hosted API、權重封閉；要在地部署、自行微調、或避開資料出境的場景無法用它。Laya 的動機之一正是補上這塊（Apache-2.0＋可微調）。
- **多語文脈的空白**：公開 benchmark 與可用性多以英文為主；Laya 以 mmBERT-base 骨幹覆蓋 100+ 語言，並內建 router 處理「英文 checkpoint 讀不了非拉丁文字」的問題。

### 通用技術背景（非文章明說）

- **Encoder 與 decision head 的組合早於 LLM 生成範式**：對「文字 → 標籤／分數」這類判斷，雙向 encoder（BERT 系）在延遲與成本上本就有結構優勢；生成式 LLM 做同類任務是把生成能力當成判斷的載體。
- **proper scoring rule 與校準**：要讓模型的機率「統計上有意義」，訓練目標必須是 strictly proper scoring rule，否則最佳策略不是誠實報機率。Laya 的 RLCD 正是把 reward 設成 proper scoring rule（log／spherical／RPS），使「報誠實機率」成為最大化 reward 的唯一方式。
- **高基數標籤空間的 token 預算限制**：把 N 個選項塞進固定 prompt 預算時，每標籤可用 token 數隨 N 下降，選項文字一旦短到無法區辨，準確度就掉。這是架構性限制，不是能力差距。

---

## 3. 這個技術是如何解決該問題的？

### 核心機制總覽

```
state（文字／email／ticket／JSON）
        │
        ▼
Router ── 偵測 script／language（<0.5 ms 純 Python，forward 前即決定）
        │
        ├─ English  → laya            (ModernBERT-large, 421M, 512 ctx)
        ├─ 非英文   → laya-multilingual(mmBERT-base, 322M, 1024→8192 ctx)
        └─ 領域特化 → laya-typed-decisions (421M, 1024 ctx)
        ▼
雙向 encoder → 決策頭（2 層 transformer + option-marker scorer + act/escalate head）
        │   每個選項於自身 [MASK] 位置打分後 softmax
        ▼
typed answers：choice／score／noul ＋ 機率分布 ＋ confidence／answer_confidence
```

### 三原語

| Primitive | 回傳 | 典型用途 |
|---|---|---|
| `choice` | 最高標籤、各選項機率、confidence | 分類、路由、選動作 |
| `score` | 序位尺度的期待值、分布、confidence | 輕重緩急、風險級別 |
| `noul` | P(true)（0.0–1.0） | 釣魚／垃圾／越獄／流失風險偵測 |

三種問題對**同一個 state、平行且彼此隔離**地評估；一次 forward pass 完成。

### 訓練法（RLCD）

- **目標**：reward 為 strictly proper scoring rule（log ＋ spherical ＋ RPS 的組合），演算法為 REINFORCE ＋ group-mean baseline（GRPO-style）。
- **可驗證性**：repo 內 `tests/test_training.py` 對 `proper_reward` 的「properness」做檢驗——若 reward 能被「非真分布」最大化，README 的校準宣稱就不成立。這是把宣稱變成可確定性驗證的設計。
- **微調是價值所在**：base checkpoint zero-shot 近隨機（0.362／0.352 對 majority 0.461）；在 typed-decisions 上微調後達 0.766。官方立場明講：**Laya 是「快速可特化的底座」，不是 zero-shot 決策引擎**。微調 notebook 跑在 Kaggle 免費 2xT4，約 4–5 小時、4 epochs、~30k questions。

### 部署與接入面

| 面 | 內容 |
|---|---|
| 套件 | `pip install laya`（Python ≥ 3.10）；extras：`serve`／`fast`／`mcp`／`onnx`／`langchain` |
| CLI | `laya "..."`、`--predict`、`--preset triage|email|guard|moderation|router`、互動模式 |
| HTTP | `laya-serve`，暴露 Jev 相容的 `POST /v1/systemone`，既有 Jev client 只需改 `baseUrl` |
| MCP | `laya-mcp-server`（stdio）供 Claude Desktop／Cursor 等呼叫 |
| 框架 | LangChain／LangGraph 的 `LayaRouter`、`LayaGuardrail`、`LayaTriage` |
| 部署 | Docker、Nix flake／NixOS module、ONNX Runtime、TileLang GPU 快路（fused kernels ＋ CUDA graph） |
| 內建 presets | Intelligent Model Router、Prompt Guardrails、Moderation、Support Ticket Triage |

### 校準機制

- `confidence`（choice／score）＝ **1 − 正規化熵**，是分布集中度，**不是答對率**。
- `answer_confidence` ＝ 所報答案的機率；官方建議用單一閾值時 gate 在它。
- 兩個 checkpoint **出廠皆 over-confident**，`laya-multilingual` 甚至無 fitted temperature；需在自己的 held-out 資料上 fit temperature（`laya` ECE 0.466→0.081、`multilingual` 0.314→0.106）。閾值是**在自己資料上選的政策**，不是模型屬性。

### 官方自我揭露的限制（Honest limits）

| 限制 | 事實 |
|---|---|
| base zero-shot 近隨機 | 0.362／0.352 對 majority 0.461 |
| 高基數選項崩 | Banking77（77 選項）0.425 vs Jev 0.870；選項共用 `head_max_len` 預算（English 192／其他 256 tokens），77 標籤每項僅 ~3–4 tokens |
| `noul` 可能跟標籤而非 state | English checkpoint 最明顯（#156） |
| `score` 最弱 | SST-5 0.372；`laya-multilingual` 對 score 有首位偏誤（#131） |
| 英文 checkpoint 非英文崩且仍高信心 | Khmer 0.000 accuracy @ 0.952 confidence → 故 router 在 forward 前判語言 |
| 模態 | state 只收字串／JSON／陣列，不支援影像 |
| `act.act_probability` 無訊號 | #185，幾乎恆為 1.0、AUROC 0.30 |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

Laya 屬「**非生成式／小模型結構化決策**」問題域。以下替代方案先對照第二大腦 FATESAIKOU/MyBrain 的既有判定，再給 DA 表。

### 第二大腦對照（重要）

| 標的 | 第二大腦判定 | 信任層級 / 時間 | 對本報告的影響 |
|---|---|---|---|
| **Jev**（TypeSafe AI） | **試用（Accept(Weak)）**。使用者原話：「我構築個人 workflow 常常遇到太確定性的寫法缺乏彈性、全部放給 AI 又有可能整個跑不起來；所以構想是我給出各種場景的可選動作以及給出文脈，讓 AI 自適化地選擇最適合的選項執行。」Jev 的 Choice（可選動作集合）＋ state（文脈）＋機率幾乎就是這個構想；⚠️ 它是**判斷零件不是執行者** | `generated.by: agent:personal-assistant` ＋ `status: draft` → **AI 草稿，未經他 review**；首見 `日誌/2026-09-22.md` | **直接對照標的**。Laya 是同一構想的「可下載／可微調版」，且能解掉 Jev 那條「hosted 在美國、先只餵公開資料」的去隱私界線 |
| **needle**（cactus-compute） | **不採用**。45M／28MB 端側工具調用模型（SAN＋grammar-constrained JSON＋confidence 門控）；理由為「沒有在極限環境跑 LLM 的需求」，28MB 優勢只在 MCU 級成立 | `generated.by: process:learn-gh-agent` ＋ `status: draft`；首見 2026-08-22 | 同問題域的**極端端側**版本。⚠️ 依 [`技術取捨準則`](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md)：**不採用 ≠ 沒價值**，其 grammar-constrained JSON＋confidence 門控方向仍可抽取 |
| **DeepSeek V4** | **human 本人 stable**：「**降低 Model Routing 研究優先級**——不要把心力花在『如何精準路由不同 LLM』的 legacy 機制上，把精力集中在 Domain 領域知識」 | `generated.by: human:fatesaikou` ＋ `status: stable`；2026-04-26 | **與 Laya 的內建 `router_questions()` preset（Intelligent Model Router：把請求路由到 small vs frontier models）直接衝突**，見下 |
| **Switchyard / OmniRoute / Model Router 線** | Switchyard、OmniRoute 皆已於 2026-09-06 翻為**不採用**；整條 Model Router 線放棄，理由為「真正握有 GPU 的供給者只有個位數，為個位數做路由政策層成本高於收益」 | Switchyard：`opencode/deepseek-v4-flash` draft；OmniRoute：判定總表 draft；皆為 AI 草稿 | 同上的衝突源：Laya 的**語言 router 不是**這條線（它是 checkpoint 選擇），但它的 **model-router preset** 是 |
| **技術取捨準則** | 骨幹。**理解優先**：「不夠穩定或我不夠熟悉 → 先自己兜，理解本質（MVP）之後才決定下一步」；**MVP→Feature 唯一閘門＝能否影響個人 workflow**；Reject≠沒價值 | `claude-code/opus-5` ＋ `status: draft`（含「原話：」引用） | 決定 §4 落點：Laya 的正確用法是**「先自己兜」的底座**，不是導入一套服務 |
| **統一的兩端稅** | 骨幹。「不要用同一套機制同時管確定性執行與語意判斷」——確定的留 code、語意的切給模型 | `claude-code/opus-5` ＋ `status: draft` | Laya 是這條洞察在控制流上的**機制化版本**：它只做語意判斷，不執行 |

#### ⚠️ 衝突聲明（對照最有價值之處）

1. **Laya 的 Model Router preset 撞上他本人 stable 判定。** Laya README 內建「Intelligent Model Router（routes to small vs. frontier models）」，這正是他本人在 [`DeepSeek V4`](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/DeepSeek%20V4.md) 判定「降低 Model Routing 研究優先級」、且在 Switchyard／OmniRoute 連帶關閉中「整條 Model Router 線放棄」所欲避免的方向。**但必須區分**：Laya 的 `Router` 本體是依**語言／script** 挑 checkpoint（forward 前決定），不是依任務難度挑不同 LLM；衝突只落在 `router_questions()` 這個 preset，不落在 Laya 的核心機制。
2. **「測試 Jev 能力邊界」的下一步不能用 Laya 兌現。** [`下一步清單`](https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md) 有一條低優先度動作「測試 Jev 的能力邊界」（判試用、知曉即結束）。Laya **不是 Jev 權重**，用它測不到 Jev 的中文／日文精度與 confidence 校準；它測的是**同一個構想**在另一組權重上的表現。兩者不可互相替代。
3. **「快 6–7×」不可搬進他的情境。** Jev 的 p50（236–276 ms）與 Laya 的硬體（T4）都與他的環境不同；這與 [`Jev`](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Jev.md) 中既有的警告一致——「倍率來自官方自選工作流、不要直接拿來估自己的情境」。
4. **它仍是判斷零件，不是機制本體。** 依 [`核心價值觀`](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/價值觀/核心價值觀.md) 的「產出形態：會動的機制 vs 判斷材料」，Laya 與 Jev 同級——只提供判斷，執行、控制流、副作用仍留在程式碼。採用它不會自動產生「會動的機制」。

### DA 表（替代方案）

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Laya（本標的）** | 雙向 encoder＋決策頭，RLCD（proper scoring rule reward）訓練；三 checkpoint＋語言 Router；Apache-2.0 權重與微調碼；Jev 相容 HTTP／MCP／CLI | Python 3.10+；接受 base zero-shot 近隨機、需自行微調與 fit temperature；>20 選項需調 `head_max_len` 或 shortlist；無影像輸入 | 需自備權重與執行環境；base 出廠 over-confident；`score` 弱、`noul` 標籤敏感；模型與權重自行維護 | 本地／雲端皆可跑，延遲與成本與生成脫鉤；可微調成領域決策頭；與 Jev client 可直接換 `baseUrl` |
| **Jev（TypeSafe AI）** | hosted System One API：state＋questions → 型別化判斷＋校準機率；Choice 上限 255 選項；並行評估多題 | 接受 hosted、early access、權重封閉、hosted 在美國；須處理資料邊界 | 單一供應商；保存期間未明；重要路徑需 fail-open／fail-closed 分法 | 免自建、開箱即用；官方宣稱端到端 70–500 ms；判斷形態與 Laya 同型 |
| **needle（端側工具調用）** | 45M SAN attention-only、grammar-constrained JSON、confidence 門控、bounded memory、單一 14MB binary | 記憶體極限環境（MCU 級）；接受 45M 的效能衰減 | 工具調用準確度與推理深度明顯低於一般模型；筆電／雲端場景優勢不成立 | 在離線、MCU 級硬體上做工具調用與結構化抽取；28MB 記憶體封頂 |
| **自兜：frozen encoder ＋ 自訓決策頭／分類器** | 用既有 sentence encoder（或 Laya 的 encoder）凍結後接自訓 head／logistic regression；資料自己標 | 有領域標註資料；接受自行處理資料清洗與校準 | 需自建訓練與評估迴路；無現成 preset 與校準 | 與「理解優先、先自己兜」準則完全一致；Laya 微調路徑即此形態（`stuntd` 同型：frozen encoder ＋ per-decision head） |

### 各替代切入點差異

- **Laya**：切入點是「**可下載、可微調、可在地部署的判斷底座**」——把 Jev 的問題形態開源化，並用語言 Router 覆蓋多語。它的核心價值在**微調後的特化**，不是 zero-shot。
- **Jev**：切入點是「**免自建的 hosted 判斷零件**」——放棄權重與訓練控制，換取零維運與現成 API 形狀。
- **needle**：切入點是「**極端端側**」——以參數量換取 MCU 級可部署性，犧牲判斷品質。
- **自兜 encoder＋head**：切入點是「**理解本質後自行構建**」——不引入第三方模型，用最小機制驗證「小模型負責判斷」這件事。

### 落點（對照第二大腦）

依 [`技術取捨準則`](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md) 的兩條主軸：

| 判準 | 對 Laya 的回答 |
|---|---|
| 不夠穩定或不熟悉 → 先自己兜？ | **符合。** Laya 是 2026-09-18 建立、8 天大的專案，且有 30 contributors、Apache-2.0、可微調——它正是「自己兜一個來理解」的低成本底座，而不是要導入的生產依賴。 |
| MVP→Feature 閘門＝能否影響個人 workflow？ | **目前未驗證。** 要驗的是「寫死 if 很脆的判斷點」是否能改用 Laya，且在中文／日文文脈上精度與校準堪用。這與他對 Jev 的下一步（測試能力邊界）同構。 |
| 統一的兩端稅 | **對齊。** Laya 只切出語意判斷，確定性執行留在 code——正是「不同的兩端不要用同一套機制」。 |
| Model Routing 優先級 | **衝突（僅 preset）。** `router_questions()` 的「小模型 vs 前沿模型路由」踩在他 stable 判定上；Laya 的語言 Router 不在此列。 |

**結論**：Laya 解決「判斷被包在生成裡」的形態錯配，做法是用非生成式 encoder＋決策頭＋proper scoring rule 訓練，並以 Apache-2.0 開源權重與微調碼，使「小模型負責判斷」這套模式可下載、可特化、可在地部署。對照第二大腦：它與 `Jev` 判試用的**構想**同型，且能解掉 Jev 的 hosted 資料邊界；正確用法是當「先自己兜」的底座去驗證能力邊界，**不是**當生產依賴，也**不是**拿它的 model-router preset 去重啟已被放棄的 Model Routing 線。
