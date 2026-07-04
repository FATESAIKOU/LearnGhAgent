# DeepSpec 分析報告

> 技術標的：DeepSpec（deepseek-ai/DeepSpec）— speculative decoding 的訓練與評估全端框架
> 調研日期：2026-07-04
> Repo 狀態：stars=6079, forks=512, MIT License, Python, 建立於 2026-06-26

---

## 1. 這個技術解決什麼問題？

DeepSpec 解決的是 **大型語言模型（LLM）推理延遲過高** 的問題。

具體來說：自迴歸 LLM 在推理時逐 token 生成，每個 token 的計算依賴前一個 token 的輸出，無法平行化。這導致 GPU 的平行計算能力被嚴重浪費，推理速度成為部署瓶頸。例如 Qwen3-4B 在單卡 A100 上生成速度約 20-40 tokens/s，遠低於 GPU 的理論吞吐量。

DeepSpec 採用 **speculative decoding（推測解碼）** 策略：訓練一個輕量 draft model 快速產生候選 token 序列，再由原始 target model 平行驗證並接受符合條件的 token，達到 **無損加速**（輸出分佈與 target model 一致）。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 自迴歸生成的本質限制

Transformer-based LLM 的生成過程是逐 token 的馬可夫鏈：

```
output = []
for t in range(max_tokens):
    logits = model(input_ids + output)
    next_token = sample(logits[-1])
    output.append(next_token)
```

每個 step 都需要一次完整的 forward pass，且 step t+1 必須等待 step t 完成。這在 GPU 上意味著：
- 每次 forward pass 只產生 1 個 token
- GPU 的矩陣運算單元在 batch_size=1 時利用率極低（通常 < 10%）
- 記憶體頻寬成為瓶頸（memory-bound）

### 2.2 模型規模增長加劇問題

隨著模型參數從 7B 增長到 70B、405B，單次 forward pass 的計算量線性增加，但生成 token 數不變。推理延遲與模型大小成正比，而使用者對即時性的要求不變。

### 2.3 Speculative Decoding 的既有限制

Speculative decoding 的核心想法是：用一個小模型（draft model）快速生成候選序列，再用大模型（target model）平行驗證。但既有方法存在以下限制：

| 限制 | 說明 |
|---|---|
| Draft model 仍為自迴歸 | 如 EAGLE-1/2 的 draft model 仍需逐 step 生成，雖然每 step 較快，但仍是序列化 |
| 特徵預測瓶頸 | EAGLE-1/2 預測 target model 的 top-layer feature，限制了 draft model 從更多訓練資料中受益的能力 |
| 訓練與推理不一致 | 訓練時 draft model 只做單步預測，但推理時需多步自迴歸，導致分佈偏移 |
| 驗證效率 | 傳統 rejection sampling 需要逐 token 比對分佈，無法充分利用 GPU 平行性 |

### 2.4 資料規模擴張的趨勢

LLM 社群正朝向更大規模的訓練資料前進（如 open-perfectblend 等資料集），但既有 speculative decoding 方法無法有效利用更多資料來提升 draft model 品質。這是一個「資料多但 draft model 學不動」的矛盾。

---

## 3. 這個技術是如何解決該問題的？

DeepSpec 提供三種 draft model 演算法，共用同一套訓練/評估基礎設施。以下分別說明。

### 3.1 整體架構

```
┌─────────────────────────────────────────────────────────┐
│                    DeepSpec Workflow                      │
├─────────────┬──────────────────┬────────────────────────┤
│  Data Prep  │    Training       │      Evaluation        │
├─────────────┼──────────────────┼────────────────────────┤
│ download    │ target cache →    │ draft model +          │
│ prompts     │ draft model       │ target model           │
│             │ (FSDP + BF16)     │                        │
│ regenerate  │ loss: CE + L1    │ metrics: accept rate,   │
│ answers     │ + confidence     │ speedup, τ             │
│             │                  │                        │
│ build       │ checkpoint:      │ benchmarks: gsm8k,     │
│ target      │ ~/checkpoints/   │ math500, aime25,       │
│ cache       │                  │ humaneval, mbpp, ...    │
└─────────────┴──────────────────┴────────────────────────┘
```

### 3.2 DSpark（論文見 repo 內 DSpark_paper.pdf）

DSpark 是 DeepSpec 的核心演算法，採用 **block-level speculative decoding** 搭配 **anchor sampling**。

**核心機制：**

```
輸入序列: [t0, t1, t2, ..., tn]
                ↓
Step 1: Anchor Sampling
  - 從序列中隨機取樣 num_anchors=512 個 anchor 位置
  - 每個 anchor 對應一個 block（block_size=7）
  - 只取 loss_mask 中第一個 target 有效的 anchor

Step 2: Context Feature Extraction
  - 從 target model 的指定層提取 hidden states
  - target_layer_ids = [1, 9, 17, 25, 33]（共 5 層）
  - 拼接成 context feature

Step 3: Block-level Draft Generation
  - 對每個 anchor block，draft model 預測 block_size 個 token
  - 使用 Markov head 進行 block 內自迴歸取樣
  - 支援 3 種 Markov head：
    ┌─────────┬─────────────────────────────────────┐
    │ Vanilla │ W1(prev_token) → W2 → bias           │
    ├─────────┼─────────────────────────────────────┤
    │ Gated   │ sigmoid(W_g([h; W1(x)])) * W1(x)    │
    ├─────────┼─────────────────────────────────────┤
    │ RNN     │ GRU-like state across block positions│
    └─────────┴─────────────────────────────────────┘

Step 4: Loss Computation
  Loss = α_ce * CE_loss + α_l1 * L1_loss + α_conf * BCE_loss
  - CE_loss: cross-entropy on draft predictions
  - L1_loss: |P_draft - P_target| 分佈匹配
  - Confidence loss: 預測每個位置的 accept rate
  - loss_decay_gamma=4.0: 位置越遠權重越低
```

**注意力遮罩設計：**

```
Query positions (draft blocks)
    │
    ▼
┌─────────────────────────────────────┐
│ Context tokens  │  Draft block k    │
│ (0 ~ anchor-1)  │  (same block only)│
└─────────────────────────────────────┘
         ▲                ▲
   可關注所有     只可關注同 block 內
    context token  的 draft token
```

每個 draft block 只能關注：
1. 所有 context token（位置 < anchor）
2. 同 block 內的其他 draft token

這保證了 draft model 在推理時的行為與訓練一致。

**訓練配置（dspark_qwen3_4b）：**

| 參數 | 值 | 說明 |
|---|---|---|
| block_size | 7 | 每個 anchor 預測 7 個 token |
| num_anchors | 512 | 每條序列取樣 512 個 anchor |
| markov_rank | 256 | Markov head 的嵌入維度 |
| markov_head_type | vanilla | 使用最簡 Markov head |
| ce_loss_alpha | 0.1 | CE loss 權重 |
| l1_loss_alpha | 0.9 | L1 分佈匹配權重 |
| confidence_head_alpha | 1.0 | Confidence head 權重 |
| loss_decay_gamma | 4.0 | 位置衰減係數 |
| lr | 6e-4 | 學習率 |
| global_batch_size | 512 | 全局 batch size |
| sharding_strategy | no_shard | 無 FSDP 分片（模型小於單卡記憶體） |
| torch_compile | True | 啟用 torch.compile |

### 3.3 DFlash（論文 arxiv 2602.06036, ICML 2026）

DFlash 使用 **block diffusion model** 取代自迴歸 draft model，實現單次 forward pass 平行生成整個 block。

**核心機制：**

```
傳統自迴歸 draft:     DFlash block diffusion:
t0 → t1 → t2 → t3     [t0, t1, t2, t3] 一次性生成
     (序列化)                (平行化)
```

DFlash 的關鍵差異：
- 使用 diffusion process 一次性生成 block_size 個 token
- 不需要 Markov head（markov_rank=0）
- 不需要 confidence head（confidence_head_alpha=0.0）
- Loss 僅使用 CE（ce_loss_alpha=1.0, l1_loss_alpha=0.0）
- 訓練框架與 DSpark 共用（使用 Qwen3DSparkTrainer）

**加速效果：** 論文報告 >6x lossless acceleration，比 EAGLE-3 快 2.5x。

### 3.4 Eagle3（論文 arxiv 2503.01840）

Eagle3 是 EAGLE 系列的第三代，核心改進為 **direct token prediction** + **training-time test (TTT)**。

**與前代 EAGLE-1/2 的差異：**

```
EAGLE-1/2:                    Eagle3:
預測 top-layer feature        直接預測 token
↓                              ↓
feature → draft model →       token → draft model →
draft tokens                  draft tokens
(間接)                         (直接)
```

**Training-Time Test (TTT)：**

Eagle3 在訓練時模擬推理階段的多步生成過程：

```
Step 0: draft model 預測 step 0 的 token
Step 1: 將 step 0 的輸出作為輸入，預測 step 1
Step 2: 同上，預測 step 2
...
Step 6: 預測 step 6（ttt_length=7）

每個 step 的 loss 以 step_loss_decay=0.8 衰減：
  total_loss = Σ(0.8^step * loss_step)
```

這解決了訓練/推理不一致的問題：訓練時 draft model 學會處理自己產生的 token，而非總是依賴 ground truth。

**Triton Fused Soft Cross-Entropy：**

Eagle3 的 loss 使用 Triton 實作的 fused soft cross-entropy kernel，避免在 autograd 中保留完整的 [B, T, V] fp32 log-probs 張量，顯著降低記憶體使用。

**訓練配置（eagle3_qwen3_4b）：**

| 參數 | 值 | 說明 |
|---|---|---|
| ttt_length | 7 | TTT 步數 |
| step_loss_decay | 0.8 | 逐 step loss 衰減 |
| draft_num_hidden_layers | 1 | Draft model 僅 1 層 transformer |
| target_layer_ids | [1,9,17,25,33] | 5 層 target features |
| lr | 6e-4 | 學習率 |
| torch_compile | False | Eagle3 不使用 torch.compile |

**加速效果：** 論文報告 up to 6.5x speedup，比 EAGLE-2 提升約 1.4x。

### 3.5 共用基礎設施

**資料管線（3 步驟）：**

```
Step 1: download_and_split.py
  mlabonne/open-perfectblend → train.jsonl + eval_datasets/

Step 2: generate_train_data.py
  SGLang server 服務 target model → 重新生成 assistant answers
  8 個 worker, ports 30000-30007

Step 3: prepare_target_cache.py
  預計算 target model 的 hidden states
  輸出：~/.cache/deepspec/qwen3_4b_target_cache（約 38TB）
```

**訓練框架（BaseTrainer）：**

- FSDP 支援：full_shard / hybrid_shard / no_shard
- BF16 混合精度訓練
- BF16Optimizer：BF16 參數 + FP32 優化器狀態
- Suspend/Resume：支援中斷後續傳
- 自動 checkpoint：每 3000 step 儲存一次
- CUDA prefetcher：非同步資料載入

**評估框架：**

支援的 benchmark：gsm8k, math500, aime25, humaneval, mbpp, livecodebench, mt-bench, alpaca, arena-hard-v2

評估指標：accept rate（逐位置）、τ（預期接受長度）、speedup

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Medusa** | 在 target model 最後一層添加多個預測頭（multiple heads），每個 head 預測不同偏移位置的 token，搭配 tree attention 平行驗證 | 需要修改 target model 架構（添加 heads）；需額外訓練 heads | 多 head 增加記憶體用量；tree attention 增加計算複雜度；需實作 tree 驗證邏輯 | 2-3x speedup，無需獨立 draft model |
| **Lookahead Decoding** | 使用 n-gram 快取從歷史生成中擷取候選 token 序列，搭配 Jacobi iteration 平行驗證 | 需要足夠的歷史生成作為 n-gram 池；適合批次推理場景 | n-gram 快取隨生成增長而增大；首次生成無歷史可用時無加速效果；長序列時快取命中率下降 | 1.5-2x speedup，無需訓練 |
| **Self-Speculative Decoding** | 利用 target model 自身的 early exit 機制：在淺層 layer 提前輸出作為 draft，再經完整 forward pass 驗證 | target model 需支援 early exit（或可插入 exit head）；需訓練 exit head | 增加模型大小（exit head）；early exit 的 draft 品質取決於 exit layer 位置；需權衡加速比與準確率 | 1.5-2.5x speedup，無需獨立 draft model |
| **Blockwise Parallel Decoding** | 使用樹搜尋（tree search）同時探索多條候選路徑，再透過平行驗證選取最優路徑 | 需要設計樹結構與剪枝策略；需實作樹驗證 kernel | 樹寬度增加時計算量指數增長；需平衡探索深度與寬度；實作複雜度高 | 2-4x speedup，適合高吞吐場景 |

### 4.2 切入點差異分析

| 面向 | DeepSpec (DSpark/DFlash/Eagle3) | Medusa | Lookahead | Self-Speculative |
|---|---|---|---|---|
| Draft model 來源 | 獨立訓練的輕量模型 | Target model 附加 head | 無（使用歷史） | Target model 自身 |
| 是否需要額外訓練 | 是（draft model） | 是（heads） | 否 | 是（exit head） |
| 平行化粒度 | Block-level（7 tokens） | Tree-level（多路徑） | Token-level（Jacobi） | Token-level（early exit） |
| 驗證方式 | Target model 平行 forward | Tree attention | Jacobi iteration | 完整 forward pass |
| 加速比 | 3-6.5x | 2-3x | 1.5-2x | 1.5-2.5x |
| 部署複雜度 | 需載入 2 個模型 | 需修改 target model | 無需修改模型 | 需修改 target model |
| 適用場景 | 生產部署，追求最高加速 | 無法載入第二個模型時 | 無訓練資源時 | 無法載入第二個模型時 |

### 4.3 關鍵權衡

DeepSpec 的 draft model 方法在加速比上領先，但代價是：
1. **額外記憶體**：需同時載入 target model 與 draft model（draft model 約為 target 的 5-10% 參數量）
2. **訓練成本**：draft model 需要專用訓練流程與資料（38TB target cache）
3. **資料依賴**：draft model 的品質高度依賴訓練資料的品質與覆蓋範圍

相比之下，Lookahead Decoding 無需訓練但加速比有限，Medusa 無需獨立模型但需修改 target model 架構。選擇取決於部署環境的約束條件（記憶體、訓練預算、延遲要求）。
