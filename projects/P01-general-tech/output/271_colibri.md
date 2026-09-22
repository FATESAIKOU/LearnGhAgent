# colibri — 消費級與異構硬體上運行前沿 MoE 模型

> 標的：https://github.com/JustVugg/colibri（Apache-2.0，純 C、零依賴、MoE 推理引擎）
> 資料來源：repo README（775 行）、`docs/benchmarks.md`、`docs/GPU_BACKENDS.md`、`gh api` metadata；背景與替代方案對照 FATESAIKOU/MyBrain 既有評估。

---

## 1. 這個技術解決什麼問題？

**被解決的具體問題：** 讓「前沿等級、數百 B 到數 T 參數」的 MoE（Mixture-of-Experts）模型，能在**消費級與異構硬體**（單張消費級 GPU、系統 RAM、甚至僅 NVMe SSD，以及 CPU / CUDA / Metal / Vulkan 混搭的機器）上運行，而不需要租用或購置數十張企業級 GPU。

具體拆成三個子問題：

| 子問題 | 具體表現 | colibri 的對應宣稱 |
|---|---|---|
| **模型放不下** | GLM-5.2/5.3（744B）、Inkling（975B）、Kimi K3（2.8T）FP16 需 TB 級記憶體，消費級單卡（如 12–24GB VRAM）完全無法 fit | int4 後 744B 僅需 ~370GB NVMe + ~9.9GB RAM 常駐即可跑 |
| **硬體多樣化/異構** | 使用者的機器可能是「消費級 GPU + 大 RAM + NVMe」的混合，而非整齊的企業 GPU farm | VRAM / RAM / NVMe 統一視為同一推理層級，CPU/CUDA/Metal/Vulkan 共用單一 runtime |
| **速度/語意取捨** | 以往要嘛塞不下、要嘛為了 fit 而過度量化或縮小模型 | 宣稱 placement 只影響速度、**不影響 router/精度**（無 SLA on speed、有 hard guarantee on semantics） |

**問題描述的模糊之處（README 未完全量化）：**
- 「前沿模型」的實際體驗速度依硬體差異極大——冷啟動 decode 落在 0.05–0.1 tok/s（見 §3），這對「對話」場景接近不可用，但對「批次生成/離線推理」可接受。README 不給單一速度承諾，只給「placement 決定速度」的相對保證。
- 「hardware you already own」的門檻（最低要幾 GB RAM / 幾張 NVMe / 哪個 GPU）沒有在 README 給出單一的硬性清單，落在 tuning 與各後端文件。
- 「異構」的實際收益沒有統一的 benchmark 對照表（不同後端同模型的吞吐對比分散在各後端文件）。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章中明確提到的背景

README 明確點出 MoE 的結構性矛盾：

```
MoE 模型規模 vs 實際啟動量
┌─────────────────────────────────────────────┐
│ 參數總數       744B（int4 約 370GB）          │
│ 每 token 啟動   ~40B                          │
│ 其中 routed    ~11GB（每 token 變動的專家）   │
└─────────────────────────────────────────────┘
```

- **MoE 總參數 vs 活躍參數差距巨大。** 744B 模型每 token 只啟動約 40B，其中 routed experts 每 token 只換約 11GB。也就是說「整個模型」與「每次推理真正需要的權重」是兩個數量級。
- 由此 README 提出核心主張：**不需要把模型「fit」在快速記憶體，只需要「placement」**——把每次要用的權重擺對地方即可。這直接推翻「模型必須塞進 VRAM 才能跑」的慣例。
- 文中明列受啟發的研究與工程：REAP/EASY-EP、SERE/ReMoE、MC-SMoE、MoBE/D²-MoE、HybriMoE/ScMoE/OD-MoE（研究面）；safetensors、tiktoken、llama.cpp（GBNF/Metal）、vLLM（輸出語意）、transformers（oracle）、DietGPU、rocWMMA（工程重實作面）。

### 2.2 通用技術背景（非文章明講，但為理解此問題所需）

- **前 2020s 的 LLM 主流是 dense 模型**——每一層、每一參數在每次推理都會被用到，因此「模型大小 ≈ 每次推理需要的記憶體」，這讓「要跑大模型就要大顯存」成為普遍直覺。
- **MoE 打破了這個等式。** MoE 把 FFN 層拆成大量獨立「expert」，router 每 token 只挑少數專家啟動。總參數爆漲但**活躍參數成長遠低於總參數**，為「權重不需要全部常駐」打開了空間。
- 消費級硬體的「記憶體天花板」是硬限制：單張消費級 GPU 的 VRAM（8–24GB）與系統 RAM（32–128GB）遠小於前沿 MoE 的權重總量。要跑前沿模型，傳統路線只有兩條：**租用企業 GPU farm**（成本高），或 **量化縮小模型**（會掉精度）。
- 企業 GPU 與消費級硬體的另一個落差是**異構性**：企業環境是整齊的 NVIDIA farm；消費環境常是「一張 NVIDIA + 內建 GPU + 大 RAM + NVMe」的混搭，傳統推理框架假設單一 GPU，無法善用混搭硬體。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 核心機制總覽

```
colibri 三層階層（multitiering）
┌──────────────────────────────────────────────────────────────┐
│  NVMe（disk）              RAM（int4）          VRAM（GPU）   │
│  ~370GB routed experts     dense 部分常駐        可選 hot     │
│  19,456 個 expert           ~9.9GB               expert store │
│  （隨需串流）               attention/shared/   （加速層）    │
│                              embedding ~17B                    │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 機制分解（「怎麼做」，不評論好壞）

1. **MoE 稀疏性轉為「placement」問題。** 744B 每 token 只啟動 ~40B，其中 routed experts 每 token 只換 ~11GB。因此核心不是「把 370GB 塞進記憶體」，而是「把每次要用的 ~11GB 擺在快的地方」。

2. **三層記憶體階層，視為同一推理層級。** VRAM / RAM / NVMe 不是三種不同裝置，而是同一條頻寬與延遲階層。
   - dense 部分（attention、shared experts、embedding，約 17B）常駐 RAM，int4 後約 9.9GB。
   - 19,456 個 routed experts（75 個 MoE layers × 256，int4 各約 19MB）放在 disk（約 370GB），**隨需串流**進快層。

3. **JIT for weights（以 routing 驅動的快取）。**
   - **routing heat 驅動 per-layer LRU**：哪些 expert 最近被路由到、就優先留在熱層。
   - **learned pinned hot-store**：學習哪些 expert 長期高頻，固定釘在快速記憶體。
   - **一層前視 prefetch**：利用 routing 的可預測性（README 稱 71.6% 可預測）提前載入下一層要用的 expert，隱藏搬運延遲。

4. **I/O 引擎化。** 針對「從 disk 大量讀取」做工程優化：
   - **batch-union**：把一批 token 要讀的 experts 合併成較大的讀取，減少 I/O 次數。
   - **overlap read+compute**：讀取與計算重疊執行。
   - **O_DIRECT**：繞過頁快取，直接 DMA。
   - **dual-SSD strip**：同一模型放兩份到兩顆 SSD，讀寬翻倍。

5. **異構執行（單一 runtime）。** CPU、CUDA、Metal、Vulkan、NUMA memory、partial/full expert residency 共用同一套 runtime；單一 `.cu` 經 `backend_gpu_compat.h` 編給 CUDA/HIP，Metal/Vulkan 另有後端。這讓同一份模型能在混搭硬體上各取其長。

6. **語意保證（設計承諾）。** placement 只影響速度、不影響 router 或精度；**無 SLA on speed、有 hard guarantee on semantics**。也就是「放哪裡」不改變輸出的語意一致性，只改變生成速度。

### 3.3 量測數據（`docs/benchmarks.md`，原始 dev box）

| 情境 | 數值 |
|---|---|
| 模型 | GLM-5.2/5.3 744B、int4 |
| resident（常駐 RAM） | ~9.9GB |
| cold decode（權重需從 disk 載入） | ~11GB/token、0.05–0.1 tok/s |
| 全駐留（6×RTX 5090） | 6.84 tok/s |

> 冷啟動（0.05–0.1 tok/s）與全駐留（6.84 tok/s）的落差正是「placement 決定速度」的具體化——權重放得越快，生成越快；但兩者語意一致。

### 3.4 支援模型（一族一個 `.c`）

GLM-5.2/5.3（744B）、Inkling（975B）、Kimi K3（2.8T）、DeepSeek V4/V4.1 Flash、Qwen3.8/3.6、OLMoE，共九族。每族獨立一個 `.c`，代表對應架構需手工對接。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 DA 表（同級/替代方案）

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **colibri** | 三層階層 + JIT-for-weights + I/O 引擎 + 異構 runtime，讓權重「placement」而非「fit」 | 有大容量 NVMe（~370GB）、系統 RAM（~10GB 起）、可選消費級 GPU；願接受冷啟動極低速 | 冷啟動極慢（0.05–0.1 tok/s）、需大量 disk 頻寬、每族模型需手工 `.c` 對接、模型版本/後端支援範圍受限 | 無企業 GPU 也能跑 744B–2.8T 級 MoE，語意正確但速度受限 |
| **AirLLM** | meta device + forward hook 逐層 stream 權重，MoE 走 per-expert streaming（只載入被路由 expert） | Python/transformers 生態；需能承受逐層搬運的極低吞吐 | 每層都 disk↔GPU 搬運，吞吐極低；對使用者實測 0.03–0.1 tok/s | 能載入 671B/2.8T 級模型，但太慢、實務不可用 |
| **llama.cpp** | GGUF 量化（縮小模型）使其 fit 消費級硬體；CPU/CUDA/Metal/Vulkan 多後端 | 消費級 GPU + 系統 RAM；模型須可量化到 GGUF | 量化掉精度；只能跑「縮小後能 fit 的」模型，無法處理 744B/2.8T 這類超大 MoE 的完整權重 | 邊緣/消費級硬體流暢跑中大型 dense 模型，但無法碰前沿超大型 MoE |
| **vLLM** | PagedAttention 分頁管理 KV cache + continuous batching，優化 GPU 吞吐 | 有較大 GPU（企業/多卡）；面向生產高吞吐 | 記憶體與效能優化鎖定 NVIDIA/高階 GPU，消費級異構不討好 | 高併發、高吞吐服務大模型，但不解決「權重放不下消費級硬體」的核心矛盾 |

### 4.2 第二大腦既有判定對照（FATESAIKOU/MyBrain）

| 技術 | 判定 | 判定語意 | GitHub URL | 信任層級 | 時間 |
|---|---|---|---|---|---|
| **AirLLM** | 不採用 | per-expert streaming 太慢用不了、無硬體；可抽取「只載入被路由 expert」思路 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/AirLLM.md | `process:learn-gh-agent` + `draft` | 2026-08-10 |
| **llama.cpp / vllm** | 不採用（Reserve） | 目前環境極限用不上，保留未來選用空間；可抽取 PagedAttention/GGUF 思路 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/llama.cpp%20-%20vllm.md | `human:fatesaikou` + `stable` | 2026-07-04 |
| **omlx** | 不採用 | 硬體前提不成立（需 Apple Silicon Mac）；tiered KV cache 思路可抽取 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/omlx.md | `process:learn-gh-agent` + `draft` | 2026-08-22 |
| **freellmapi** | 不採用 | 不做 LLMGateway／免費聚合層，因真正握有 GPU 的供給者只有個位數 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/freellmapi.md | `process:learn-gh-agent` + `draft` | 2026-09-05 |

> ⚠️ **信任層級註記**：上述除 llama.cpp/vllm 為 `human:fatesaikou`+`stable`（他本人定稿）外，AirLLM、omlx、freellmapi 三則均為 **AI 產出的 `draft`（未經他本人 review）**。轉述其判定為「不採用」時，應視為「AI 草稿結論」而非他拍板的決定。colibri 本身在第二大腦判定總表（112 筆）**查無評估紀錄**，屬首次調研。

### 4.3 各方案切入點差異

| 切入點 | colibri | AirLLM | llama.cpp | vLLM |
|---|---|---|---|---|
| 核心對象 | 超大 MoE（744B–2.8T） | 超大 MoE（逐 expert） | 中大 dense（量化 fit） | 中大模型（高吞吐） |
| 權重處理 | 三層階層 placement | 逐層/逐 expert streaming | GGUF 量化縮小 | KV cache 分頁 + 高階 GPU |
| 硬體假設 | 消費級異構（NVMe+RAM+GPU） | 低顯存（meta device 掛任意卡） | 消費級單卡/CPU | 高階 NVIDIA farm |
| 語意保證 | 明確：placement 不影響語意 | 未強調 | 量化有損 | 未強調 |
| 上手/對接成本 | 每族模型手工 `.c` | 靠 transformers 掛 hook（較通用） | 生態成熟、格式統一（GGUF） | 生態成熟、OpenAI 相容 |

### 4.4 與使用者既有判準的對照與潛在衝突

- **與 AirLLM 判定的對照**：colibri 與 AirLLM 都主打「超大 MoE 不需 fit、只需串流」。AirLLM 被判「不採用」的核心理由是**太慢（0.03–0.1 tok/s）**。colibri 冷啟動也是 0.05–0.1 tok/s（同一數量級），**技術面結論與既有 AirLLM 判定存在直接張力**——若「太慢用不了」是拒 AirLLM 的主因，colibri 冷啟動並未解決這個量級問題，只有「權重放越快越快」的相對保證。
- **與他的硬體現實的對照**：他的技術取捨準則（`generated.by: claude-code/opus-5`、`draft`，2026-08-01）與 omlx 附錄的硬體研判顯示，他的主力環境是 NVIDIA/Linux 體系（RTX 2070S 8GB 等級、正考慮 5070），**沒有 370GB 等級 NVMe / 大容量系統 RAM 的設備**。colibri 的最低資源前提（~370GB NVMe + ~10GB RAM 才能跑 744B）與他現有硬體存在落差。
- **與「理解優先/自兜」準則的潛在衝突**：他的準則傾向「不穩定或不熟悉先自己兜」。colibri 是純 C 開源、零依賴，架構具學習價值（三層階層 + JIT-for-weights + I/O 引擎），**這與他「手寫 LLM 推論骨架」的進行中專案方向同質**——colibri 可作為該學習線的參考對照，而非直接採用的部署方案。
- **「Reject ≠ 沒價值」的抽取角度**：即便不採用 colibri，仍可抽取三層階層（VRAM/RAM/NVMe 統一為一層）、routing-heat 驅動的 JIT 權重快取、overlap read+compute 的 I/O 引擎化——這些方案方向與他 AirLLM/llama.cpp/omlx 已抽取的「只載入被路由 expert」「tiered cache」「PagedAttention」思路同源且互補。

> **結論**：colibri 是「超大 MoE 的 placement 引擎」，與已 Reject 的 AirLLM 同問題域、且冷啟動速度同量級，技術面未解決「太慢」這個核心拒因；硬體前提（大 NVMe/大 RAM）與他現有環境有落差。最大價值在可抽取的架構方向（三層階層、routing 驅動權重快取、I/O 引擎化），與他「手寫 LLM 推論骨架」的學習線互補。

---

## 附錄：信任與來源註記

- 本報告 §1–§3 的技術內容來自 colibri repo（README / benchmarks / GPU_BACKENDS），為**一手資料**，未經使用者 review。
- §4 的第二大腦判定（AirLLM / llama.cpp-vllm / omlx / freellmapi）標註來源、信任層級與時間；除 llama.cpp-vllm 為 `human:stable` 外，其餘為 `process/...` + `draft` 的 **AI 草稿，未經本人 review**。
- 使用者技術取捨準則引用自 https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md（`claude-code/opus-5` + `draft`，2026-08-01）。
