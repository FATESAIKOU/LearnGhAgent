# AirLLM — 低顯存運行大模型的推理工具

> 分析範圍：lyogavin/airllm（https://github.com/lyogavin/airllm），Apache-2.0，30k+ stars
> 核心主張：70B 模型跑在單張 4GB 顯卡、405B 跑 8GB、DeepSeek-V3(671B) 跑 ~12GB、Kimi K3(2.8T) 跑 <4GB

---

## 1. 這個技術解決什麼問題？

**AirLLM 解決的問題：** 在極低 VRAM（4GB 等級）的消費級 GPU 上，運行參數量遠超顯存容量的超大語言模型（70B、405B、671B、2.8T）的推理。

具體子問題：

| 子問題 | 具體表現 |
|---|---|
| **VRAM 容量硬上限** | 70B FP16 模型需 ~140GB VRAM，消費級 GPU（RTX 4090 24GB、筆電 GPU 4-8GB）根本載不進去 |
| **「載不進去」＝「完全不能用」** | 傳統框架要求整顆模型常駐顯存，顯存不足就直接 OOM，沒有降級路徑 |
| **MoE 超大模型（671B / 2.8T）** | 總參數量已達 TB 級，任何單卡都無法整顆載入，但每 token 實際只啟動一小部分 expert |
| **本地隱私 / 離線需求** | 雲端 API 需把資料送第三方，部分場景要求本地推理，但本地硬體又跑不動大模型 |

**模糊之處：** 「低顯存」的宣稱數字（4GB 跑 70B）是「能跑」而非「跑得快」。AirLLM 靠逐層 offload 換取極低 VRAM，代價是**極低的吞吐與極高的延遲**——它解決的是「能不能跑」的可行性問題，不是「跑得快不快」的效能問題。README 的數字是可行性下限，不是效能指標。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到

- 模型權重以 FP16 儲存時，每 10 億參數約需 2GB 記憶體；70B 即 ~140GB，遠超消費級硬體
- 傳統推理框架（transformers 原生）要求整顆模型常駐 GPU 顯存，顯存不足即無法執行
- MoE 模型（Kimi K3、DeepSeek-V3）總參數達 TB 級，但每 token 只路由到少數 expert，存在「總量巨大、單次用量小」的結構性落差

### 通用技術背景

- **記憶體牆（Memory Wall）：** LLM 生成是 memory-bound 而非 compute-bound——每生成一個 token，GPU 都要把權重從 HBM 搬到 SRAM。權重越大，搬運越慢，這正是「模型越大越難在低端硬體跑」的根本原因。
- **Scaling Law 的副作用：** 模型效能隨參數量冪律成長，但硬體 VRAM 成長跟不上，兩者落差持續擴大。
- **MoE 的稀疏性：** Mixture of Experts 讓總參數量可以極大，但每 token 只啟動部分 expert。這為「只載入需要的部分」提供了結構基礎——AirLLM 正是利用這點。
- **消費級硬體普及：** 個人開發者、學生、邊緣裝置使用者有本地推理需求，但沒有資料中心等級的 GPU。

---

## 3. 這個技術是如何解決該問題的？

AirLLM 的核心策略是**「一次只把一層權重放進顯存」**——用時間（反覆的磁碟↔顯存搬運）換空間（極低 VRAM 常駐量）。它不靠量化、蒸餾或剪枝縮小模型，而是改變權重的**駐留方式**。

### 3.1 核心機制：meta device + forward hook 逐層流式載入

```
磁碟 checkpoint（per-layer shard）
        │
        ▼
真實 transformers 模型在 meta device 實例化（不佔記憶體）
        │  forward / generation 邏輯仍由 transformers 驅動
        ▼
對每個大模組掛 forward hook：
   ┌────────────────────────────────────────────┐
   │ 執行前：把該模組權重 disk → GPU            │
   │ 執行中：該模組在 GPU 上計算                │
   │ 執行後：釋放該模組權重（GPU → 清空）       │
   └────────────────────────────────────────────┘
        │
        ▼
prefetching：worker thread 預載下一個模組，與當前計算重疊
```

關鍵點：

| 元件 | 作用 |
|---|---|
| **meta device 實例化** | 用 transformers 建立完整模型結構但不分配記憶體，forward/generation 邏輯完全由 transformers 驅動，不需重寫模型 |
| **forward hook 逐層 stream** | 對 embed、每個 decoder layer、final norm、lm_head 掛 hook：執行前載入、執行後釋放，任一瞬間顯存只駐留一層 |
| **prefetching** | worker thread 預先載入下一個模組，與當前層計算重疊，隱藏部分搬運延遲 |
| **per-expert streaming（MoE）** | 對 MoE 模型只載入 token 實際路由到的 expert。Kimi K3 一層 experts 展開 ~55GB，但單 token 只碰 ~1GB |
| **block-wise quantization（選配）** | 4bit/8bit 壓縮磁碟分片以加速載入；v3.0 支援 FP8 |

### 3.2 運作流程（虛擬碼）

```
載入模型：
  for layer in model.layers:
      layer.to('meta')            # 結構建立，不佔記憶體
  model = AirLLMLlama2(...)       # 包裝 transformers 模型

生成 token：
  for step in range(max_tokens):
      for layer in model.layers:
          load_layer(layer)       # disk → GPU（prefetch 已預載）
          output = layer(input)   # GPU 計算
          clean_memory(layer)     # GPU → 清空
      next_token = sample(logits)
```

### 3.3 支援模型

Llama 2/3/3.1/3.3/4、Qwen 1/2/2.5/3、DeepSeek V2/V3/R1、Mistral/Mixtral、Phi、Gemma、ChatGLM、Baichuan、InternLM、Yi。

### 3.4 代價（反證）

| 代價 | 影響 |
|---|---|
| **吞吐極低** | 每層都要磁碟↔顯存搬運，生成速度遠低於整顆常駐的方案 |
| **依賴磁碟 I/O** | 搬運速度受磁碟頻寬限制，SSD 是必要條件 |
| **不適合高併發 / 生產服務** | 設計目標是「單一使用者、可行性」，非高吞吐 API 服務 |
| **KV cache 仍需記憶體** | 長上下文時 KV cache 本身會佔用記憶體，極低 VRAM 下長序列受限 |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 第二大腦既有評估（先對照，再列方案）

| 既有評估 | 判定 | 信任層級 | 與 AirLLM 的關係 |
|---|---|---|---|
| [llama.cpp - vllm](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/llama.cpp%20-%20vllm.md) | **Reject(Reserve)**，理由「目前環境挺極限的，感覺目前用不上」 | `human:fatesaikou` / `stable` | 同屬「低 VRAM 跑 LLM」領域，是 AirLLM 最直接的替代方案 |
| [LLM降本增效（Ollama）](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/LLM降本增效.md) | **採用**，個人開發強烈推薦 Ollama Cloud | `human:fatesaikou` / `stable` | 使用者已採用 Ollama 作為本地/雲端 LLM 執行框架 |
| [技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md) | 理解優先、MVP→Feature 閘門、Reject≠沒價值 | `claude-code/opus-5` / `draft`（AI 草稿，未 review） | 決定 AirLLM 該如何被看待的判準框架 |

**衝突點（查詢最有價值處）：** 使用者對 llama.cpp/vllm 的判定是 **Reject(Reserve)**，理由是「目前環境挺極限的，感覺目前用不上」。AirLLM 與 llama.cpp 解決的是**同一個問題**（低 VRAM 跑 LLM），且 AirLLM 的硬體需求比 llama.cpp 更低（4GB 即可）。若照通則推薦「AirLLM 值得採用」，會與他既有的「目前用不上」判定**直接衝突**。依技術取捨準則，Reject 不等於沒價值——AirLLM 的「逐層 offload + per-expert streaming」是**可抽取的需求理解與方案方向**，這才是對他有價值的部分，而非「導入 AirLLM 本身」。

### 4.2 DA 表：替代方案對照

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|----------|--------------|----------------|------------------|
| **AirLLM** | meta device + forward hook 逐層 stream 權重，MoE 走 per-expert streaming；選配 block-wise quantization | 需磁碟空間放 checkpoint；SSD 加速搬運；單一使用者、可接受極低吞吐 | 吞吐極低、依賴磁碟 I/O、不適合高併發/生產服務 | 極低 VRAM（4GB）即可跑 70B+，解決「能不能跑」的可行性 |
| **llama.cpp** | 純 C/C++ 推理引擎 + GGUF 量化（Q2_K~Q8_0），CPU/GPU 皆可，權重量化壓縮 | 需量化後的 GGUF 檔；量化會損失精度 | 量化精度損失；超大模型（671B）量化後仍可能超單卡 VRAM | 消費級硬體跑中小模型（≤70B）效率高，生態成熟 |
| **Ollama** | 基於 llama.cpp 的封裝，一鍵安裝、模型管理、OpenAI 相容 API | 需本地硬體或雲端；模型需量化 | 底層仍是 llama.cpp，超大模型同樣受限 | 使用者已採用；個人開發強烈推薦 Ollama Cloud |
| **vLLM** | PagedAttention + continuous batching，高吞吐生產服務 | 需資料中心級 GPU；多 GPU 分散式 | 硬體需求高、部署複雜 | 高吞吐、低延遲的生產環境推理，非低 VRAM 場景 |
| **MLC LLM** | 編譯式優化，將模型編譯到多平台（含手機、WebGPU） | 需編譯流程；模型需轉換 | 編譯複雜度、平台特定優化 | 邊緣裝置（手機、瀏覽器）推理 |

### 4.3 切入點差異

- **AirLLM** 的切入點是**「改變權重駐留方式」**——不縮小模型，而是讓模型「一次只放一層進顯存」。這是它與所有量化方案的根本差異。
- **llama.cpp / Ollama** 的切入點是**「縮小模型」**——透過 GGUF 量化把權重壓縮到能塞進顯存。對 70B 以下有效，但對 671B/2.8T 級模型，量化後仍可能超單卡 VRAM。
- **vLLM** 的切入點是**「提高吞吐」**——解決的是「跑得快、服務多人」，不是「跑得動」。
- **MLC LLM** 的切入點是**「多平台編譯」**——把模型編譯到手機/瀏覽器等非 NVIDIA 平台。

### 4.4 反證表：AirLLM 的已知限制

| 限制 | 影響 | 緩解方式 |
|---|---|---|
| 吞吐極低 | 每層磁碟↔顯存搬運，生成速度遠低於整顆常駐 | 用 SSD + prefetch 降低搬運延遲；接受低吞吐場景 |
| 依賴磁碟 I/O | 搬運速度受磁碟頻寬限制 | 使用 NVMe SSD；block-wise quantization 壓縮分片 |
| 不適合生產/高併發 | 設計目標是單一使用者可行性 | 生產場景改用 vLLM |
| 長上下文受限 | KV cache 仍需記憶體 | 控制序列長度；選配量化壓縮 |

---

## 5. User Q&A

（本輪無使用者提問，此節暫缺。）
