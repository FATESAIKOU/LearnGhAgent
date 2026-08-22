# needle — 端側的超小型工具調用模型

> 分析範圍：cactus-compute/needle（https://github.com/cactus-compute/needle），Apache-2.0，8,425 stars
> 版本：Needle 2，45M 參數，14MB 單一二進位，28MB RAM（全 session）
> 資料來源：README.md、doc/apis.md、doc/finetuning.md、llms.txt、arXiv:2607.18363（Simple Attention Network）

---

## 1. 這個技術解決什麼問題？

**needle 解決的問題：在資源極度受限的端側硬體（記憶體 28MB 等級、單一 14MB 二進位）上，跑一個能執行「工具調用（tool calling）」與「結構化抽取（structured extraction）」的 LLM。**

具體子問題：

| 子問題 | 具體表現 |
|---|---|
| **端側記憶體硬上限** | 主流工具調用模型（7B 級）權重動輒數 GB，28MB RAM 的裝置（小型 MCU、耳機、鍵盤、感測器節點）根本載不進去 |
| **工具調用需要「結構化、可驗證」輸出** | 端側設備靠 LLM 決定呼叫哪個工具、填哪些參數，若輸出是自由文字，下游無法安全解析；錯誤的工具呼叫會觸發不可控的副作用 |
| **離線／氣隙（air-gapped）部署** | 端側場景不能依賴雲端 API，推理必須完全本地、不聯網 |
| **單檔可攜部署** | 端側部署維運者要的是「丟一個檔就動」，不是帶一串 PyTorch 依賴與 checkpoint 目錄 |

**模糊之處**：needle 的「工具調用」範疇是「單輪呼叫（call 一個工具並取得參數）」為主，README 描述的 `tool` API 聚焦「決定呼叫哪個工具、填好參數」，是否支援多輪 agent loop（呼叫→拿結果→再決策）在 apis.md 中未明示——多輪工具代理的能力邊界需要實測才能確認。「超小型」的定義以「模型參數 45M」為準，但「端側」目標裝置的下限（是 MCU、還是 28MB RAM 的微 Linux）文件沒有給出明確硬體清單，這是評估時需自行設定的前提。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到

- 模型權重以 FP16 儲存時，每 10 億參數約需 2GB 記憶體；45M 參數的模型在 INT8 下約 45MB，再壓到更低位寬才落在 14MB 單一二進位——needle 的「超小型」是刻意把參數量壓到 MCU 等級可載入的規模。
- README 明確把「工具調用」「裝置使用（device use）」「結構化抽取」列為三種能力，把「能呼叫工具」當成端側 LLM 的核心需求，而非通用對話能力。

### 通用技術背景（文章中未明確提及）

- **工具調用（Function Calling）已成為 Agent 落地的標準介面**：2023 年後 OpenAI、Anthropic、DeepSeek 等都把「以結構化 JSON/XML 輸出呼叫外部工具」納為模型原生物能。但這些能力綁在大模型身上，且以雲端 API 或高階硬體為前提。
- **記憶體牆（Memory Wall）**：LLM 生成是 memory-bound——每生成一個 token 都要反覆讀權重。模型越大，在低記憶體裝置上越跑不動。端側 LLM 必須從「縮小模型 + 限制上下文」兩方向同時下手。
- **Transformer 的 FFN 佔比大**：傳統 transformer 中 FFN（前饋網路）的權重常佔總參數的一半以上，且逐 token 都要完整運算。刪除 FFN 的「attention-only」架構（needle 背後的 SAN 論文主張）能在犧牲部分表達能力下大幅削減參數與計算量——這是 Small-Model 從「縮小」到「換架構」的轉折點。
- **KV cache 是記憶體的另一大消耗**：長上下文時 KV cache 隨 token 線性成長，對低記憶體裝置是負擔。needle 用 bounded memory（sliding window + KV sinks）來封頂。
- **端側部署的工程化維化**：MCU 端很少能跑 Python/transformers 生態，單檔、無依賴、可離線的 binary 是能真正落地的前提。

---

## 3. 這個技術是如何解決該問題的？

needle 的解法分兩層：**架構層**（把模型做小、做省記憶體）與**介面層**（讓小模型也能穩定地做工具調用與結構化抽取）。核心是五個機制。

### 3.1 整體定位（README）

```
Needle 2
├── 45M 參數（INT8 量化）
├── 14MB 單一二進位（自含）
├── 28MB RAM（全 session，含 KV cache）
└── 三能力：
     ├── tool calling（工具呼叫）
     ├── device use（裝置操作）
     └── structured extraction（結構化抽取）
```

**self-contained（自含）**：整個模型 + 運行時打成單一 14MB 的 `.cact` 二進位，不需 Python、不需雲端、不需外部依賴，隨取隨掛。

### 3.2 架構：Simple Attention Network（SAN，attention-only）

needle 的基礎是 attention-only transformer，即刪除 FFN。這來自論文 arXiv:2607.18363：

```
Traditional Transformer:      SAN（Needle 的骨架）:
   Attention + FFN              Attention（保留）
     ↕                           ↕
  → 參數多、計算重           FFN 移除
                              └ Hadamard MLP（在 attention 內做輕量混合）
                              └ GQA（Grouped Query Attention，省 KV）
                              └ engram KV memory（可寫入的記憶層）
                              └ multi-lane hyper-connections（多通道跳連）
```

| SAN 元件 | 作用 |
|---|---|
| **移除 FFN** | 直接削減最大宗的參數與計算量，讓 45M 規模變可行 |
| **Hadamard MLP** | 用點乘混合取代 FFN，保留特徵轉換能力但更輕 |
| **GQA** | 多 query 共享 KV head，降低 KV cache 記憶體 |
| **engram KV memory** | 在 KV cache 上外掛可寫記憶，支援「記住前面步驟的工具結果」而不用塞進完整 context |
| **multi-lane hyper-connections** | 平行跳接提升小型模型的有效深度 |

### 3.3 五個解決問題的核心機制

```
① 自包含       → 14MB 單一 binary，零依賴、可離線
② grammar-constrained JSON
                → 工具參數輸出被文法約束成合法 JSON，從架構上排除語法錯誤
③ confidence 門控 → 低信心就不輸出工具呼叫，改用文字回覆，避免亂呼叫
④ tool retrieval → 工具數量多時先檢索相關工具再呼叫，省 context
⑤ bounded memory → 256-token sliding window + KV sinks，context 上限，記憶體封頂
```

**④ grammar-constrained JSON**：模型不是「自由產生文字再祈禱它變 JSON」，而是 decode 階段被 grammar 限制在合法 JSON 語法內。這把「工具參數解析失敗」從機率事件變為幾乎不可能（只要文法本身正確）。

**⑤ tool 門控**：模型對「要不要呼叫工具」輸出信心值，只在信心夠高時才進入工具呼叫路徑，否則以文字回答。避免小模型在該回答時硬編一個工具呼叫。

**⑥ 256-token sliding window + KV sinks**：封住最大 context 用記憶量，配合 GQA 讓全 session 記憶體穩定在 28MB 內，不隨對話變長爆炸。

### 3.4 程式介面（簡化偽碼）

```
tool = Needle()                      # 建立模型，載入 14MB binary
tool.add(Field(name="path", type="string"))
tool.add(Field(name="mode",  type="string"))
calls = tool.complete("列出 /tmp 下所有檔")   # 決定是否呼叫 + 填參數

ext = Needle()
ext.add(Field("date", "date"))
ext.add(Field("amount", "number"))
extract = ext.extract("5/15 刷了 120 元")   # 結構化抽取，輸出合法 JSON
```

### 3.5 微調與部署

- **微調**：以 LoRA 為主要途徑，資料格式為「任務描述 + 對應工具/欄位」成對；`finetune` 後 `build` 導出單一 `.cact`。
- **後端**：模型定義在 JAX 上，訓練/微調與導出都走 JAX，導出後成為獨立、可離線跑的 binary。
- **部署**：offline / air-gapped 完整支援——export 出來的單一 binary 不聯網即可執行，符合端側離線前提。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

needle 處理的是「端側資源受限場景的工具調用」。同級替代方案主要從三個切入點差異：**端側推理引擎**（縮小模型/優化推理）、**雲端大模型直接工具調用**（不自建端側，把難度丟給雲端）、**通用小模型 + 自兜 harness**（用現有小模型搭配約束邏輯）。

> 下方「使用者判定」對照 MyBrain。第二大腦對「端側超小型工具調用模型」此一標的**沒有既有評估**（grep 零命中），但對「在消費級硬體跑 LLM」與「模型品質型的小型模型」有一批相關判定，下面列出。

### DA 表：替代方案比較

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|----------|--------------|----------------|------------------|
| **llama.cpp + 通用小型量化模型（Qwen2.5-1.5B / Phi-3-mini 等）** | 端側推理引擎 + 縮小版通用模型，跑 tool calling；GGUF 量化削參數 | 需消費級 CPU/GPU（數百 MB 記憶體），此為需求又沒有常駐大模型；無法塞進 MCU 級 28MB 記憶體 | 記憶體需求仍比 needle 大一個量級；通用模型「能 tool call 但非為此設計」，多輪代理可用性因機模型而異 | 成熟生態、多平台、可離線；適合「幾百 MB」等級的邊緣裝置而非 MCU |
| **Ollama（本地/雲端跑模型）** | 本地/雲端 LLM 執行框架，包模型 + 提供 OpenAI 相容 API，可直接接多種 tool-calling 模型 | 需硬體（PC/雲端節點）載入數 GB 模型；不是「超小型單一 binary」定位 | 記憶體需求遠超 28MB；端側極限裝置裝不了 | 易用、生態成熟、多模型可換；適合個人筆電/雲端而非 MCU |
| **雲端 API 直接工具調用（如 DeepSeek 的 XML tool calling）** | 不自建端側模型，由雲端大模型原生支援工具調用，端側只發 HTTP + 解析回傳 | 需網路連線；違反「air-gapped 離線」前提；需送資料給第三方 | 資料外流、需費用、需網路；無法服務無網/氣隙端側裝置 | 品質最高、最省；但完全不適用離線端側場景 |
| **自兜：通用小模型 + grammar 約束 harness** | 用現有微型 transformer + 自寫 grammar-constrained decoder + 簡單 KV 控制，組自己的工具調用 | 需掌握模型架構與 decode 控制；需自己處理量化與單檔封裝；開發與維化成本高 | 自己要維護 decoder、量化、部署三層；效果驗證費時 | 依「理解優先」原則可深度理解本質；貼合「MVP 是理解驗證點」的框架 |

### 各方案切入點差異

- **llama.cpp / Ollama**：把「通用模型」硬塞進端側的推理。切入點是「**縮小模型 + 優化推理引擎**」，專注「怎麼把模型跑起來」，不把「工具呼叫」當作模型訓練標的。
- **雲端 API**：把「端側問題」直接升級成「不需要端側」，工具調用交由大模型原生處理；切入點是「**把困難外包給雲端**」。
- **needle**：切入點是「**設計一個為工具呼叫而生的小模型**」——不只用現有架構縮小，而是從 SAN 架構、文法約束、confidence 門控、bounded memory 一整套為「MCU 端穩定工具呼叫」設計，與上面三個「拿通用模型硬塞」不同。
- **微型自兜**：把 need 的每一項機制（文法約束、KV 控制、量化打包）當成可理解的元件自己組；切入點是「理解優先、把機器當理解裝置」。

### 第二大腦對照（信任層級註明）

| 引用來源 | GitHub URL | 信任層級 | 與本報告的關係 |
|---|---|---|---|
| 技術取捨準則 | https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md | `claude-code/opus-5`，`draft`（**未經他 review 的 AI 草稿**） | 理解優先、MVP→Feature 唯一閘門是「能否影響個人 workflow」、Reject≠沒價值——這是評斷 need 時對照的判準 |
| 技術評估判定總表 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md | `deepseek-v4-flash`，`draft`（**未經 review 的 AI 草稿**） | 列 llm.cpp/Ollama/AirLLM/Kimi 等既有判定（見下） |
| 個人 AiAgent 入口 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/靈感/個人%20AiAgent%20入口.md | `claude-code/opus-5`，`draft` | 執行環境（自架實體 vs 自架雲端 vs 跑在終端）未定案；need 的「端側」定位與此未決題相關 |
| llama.cpp / vLLM 判定 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/llama.cpp%20-%20vllm.md | `human:fatesaikou`，`stable` | **Reject(Reserve)**：目前環境挺極限的，感覺目前用不上，保留未來根據需要選用 |

**關鍵：第二大腦沒有 needle / 端側小型工具調用模型 的既有評估。** 以下是與 this 標的相關的既有判定（供對照，**不是**對 need 的判定）：

| 既有判定 | 內容 | 信任度 |
|---|---|---|
| **Ollama（採用）** | 本地/雲端 LLM 執行框架，個人開發強烈推薦 Ollama Cloud | 判定總表（AI draft） |
| **llama.cpp / vLLM（不採用-Reserve）** | 「目前環境挺極限的，感覺目前用不上」，保留未來需求時再用 | `stable`（本人 human 判定） |
| **AirLLM（不採用）** | 太慢用不了、沒硬體；保留「逐層 offload + per-expert streaming」思路 | `draft`（AI 草稿） |
| **Kimi K3（不採用）** | 純模型品質改善，有更低價且品質滿足的替代方案 | `draft`（AI 草稿） |

**與既判定相符的點**：needle 也屬於「小型模型類」與「端側推理」的交集，使用者對「跑 LLM 的環境」目前多次判「環境極限用不上」。若採用取向是「自架某個能跑 LLM 的硬體」，needle 的 28MB 記憶體需求比 llama.cpp/Ollama 的低一個量級，是「真正塞進 MCU/極端端側」的方向——這與他「ROOK 3C 1GB 記憶體跑不來 agent」的顧慮（個人 AiAgent 入口）恰好相反：need 的記憶體需求不到該顧慮的 3%，反而是他可負擔的方向。

**結論**：needle 以「為工具呼叫而設計的小模型 + 文法約束 + 低記憶體」填補了「llama.cpp/Ollama（模型太大）與雲端 API（不能離線）」之間的「MCU 級、離線、工具呼叫」空窗。就其「能否進個人 workflow」的閘門而言：與「個人 AiAgent 入口的執行環境未定案」直接相關，但 need 的價值高度依賴「執行環境的硬體真的被限定到 28MB 級」——若執行環境仍落在筆電/雲端（數百 MB 以上），那 need 的極端記憶體優勢就無從彰顯，此時 llama.cpp+量化小模型或 Ollama 反而更實務。這是採用前需先答的那一題。

---

## 附錄：名詞對照

| 名詞 | 意思 |
|---|---|
| `cact` | Needle 導出的單一 self-contained binary |
| `Field` | 結構化抽取/工具參數的欄位定義（type 型） |
| `LoRA` | 低秩適配微調，用少量資料微調大模型 |
| `GQA` | Grouped Query Attention，多 query 共享 KV head，省記憶 |
| `engram` | 可寫的 KV 記憶層，SAN 讓模型「記住」工具/步驟資訊 |
