# DFlash / Speculative Decoding / Multi-Token Prediction (MTP)

> 本報告解析三個相互關聯的 LLM 推論加速技術：speculative decoding（上層框架）、DFlash（基於 block diffusion 的實作）、MTP（基於多頭預測的實作）。

---

## 1. 這個技術解決什麼問題？

**LLM 自回歸解碼（autoregressive decoding）的推論速度瓶頸。**

LLM 生成文字時，一次只能產生一個 token，且每個 token 都需要完整執行一次 forward pass。這導致：
- 輸出延遲與輸出長度成正比
- GPU 計算利用率低落（memory-bound，而非 compute-bound）
- 即時應用（chat、code completion）的用戶體驗受限

Speculative decoding、DFlash、MTP 三者的共同目標：**在不降低生成品質的前提下，減少 LLM 解碼所需的 forward pass 次數**。

### 三者關係總覽

```
上層框架：Speculative Decoding（草稿 → 驗證）
  ├── 實作方案 A：DFlash
  │     Draft 機制：外部 block diffusion 模型（非自回歸，平行）
  │     Verify 機制：target LLM 一次 forward pass（平行）
  │
  └── 實作方案 B：MTP（Multi-Token Prediction）
        Draft 機制：模型自身的 MTP heads（多頭平行預測）
        Verify 機制：target LLM 一次 forward pass（平行）
```

- **Speculative decoding** 是上層框架，定義了「先快速產生草稿 → 再平行驗證」的兩階段流程
- **DFlash** 與 **MTP** 都是 speculative decoding 框架下的具體實作，差異僅在「draft 階段用什麼機制產生草稿」
- 不存在「DFlash 包含 MTP」或「MTP 包含 DFlash」的關係，兩者是 sibling（兄弟）關係，上層是 speculative decoding

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 自回歸解碼的本質限制

LLM（decoder-only Transformer）的生成過程是逐 token 進行的：

```
給定 prompt "The capital of France is"
Step 1: 計算 P(paris | "The capital of France is") → 輸出 "paris"
Step 2: 計算 P(. | "The capital of France is paris") → 輸出 "."
...
```

每一步都依賴上一步的輸出，無法平行化。這不是實作問題，而是**演算法層面的序列依賴**。

### 2.2 GPU 計算特性 mismatch

- LLM forward pass 是 **memory-bound**：瓶頸在於從 HBM 讀取模型權重（~100GB/s），而非實際計算（~1000 TFLOPS）
- 單 token 生成時，計算量小但權重讀取量大，GPU 利用率極低（通常 < 10%）
- 若能一次處理多個 token，計算/記憶體存取比提升，利用率隨之上升

### 2.3 文章明確提到的背景

- Speculative decoding 的理論基礎由 Leviathan & Chen (2023) 與 Stern et al. (2018) 建立
- DFlash 論文（arXiv 2602.06036）明確指出「自回歸解碼的序列瓶頸」為其要解決的問題
- Meta 的 MTP 論文（arXiv 2404.19737）提出 MTP 最初作為訓練階段的 auxiliary task，後續研究將其延伸至推論加速

---

## 3. 這個技術是如何解決該問題的？

### 3.1 Speculative Decoding（上層框架）

**核心機制：draft-then-verify（草稿 → 驗證）**

```
輸入: prompt
  │
  ▼
┌─────────────────────────────────────┐
│  Stage 1: Draft（草稿生成）          │
│  使用一個較小的 draft model（如 1B）   │
│  快速產生 γ 個候選 token              │
│  例如: ["Paris", "is", "a", "city"]  │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│  Stage 2: Verify（平行驗證）          │
│  使用 target LLM（如 70B）一次 forward │
│  pass 計算所有候選 token 的機率        │
│  保留符合 rejection sampling 條件的   │
│  最長前綴                             │
└─────────────────────────────────────┘
  │
  ▼
輸出: 一次接受多個 token（平均 > 1）
```

**關鍵特性：**
- **lossless**：輸出的機率分布與原始 target LLM 完全一致（rejection sampling 保證）
- **draft model 可任意選擇**：可以是小模型、n-gram、或任何能快速產生 token 的機制
- **加速倍率**：通常 2x-3x，取決於 draft model 與 target model 的吻合度

**虛擬碼：**

```
def speculative_decoding(target_model, draft_model, prompt, gamma=5):
    # Stage 1: Draft
    draft_tokens = draft_model.generate(prompt, n_tokens=gamma)

    # Stage 2: Verify
    target_logits = target_model.forward(prompt + draft_tokens)

    # Rejection sampling
    accepted = []
    for i in range(gamma):
        q = draft_model.p(draft_tokens[i] | prompt + accepted)
        p = target_logits[i]
        if random() < min(1, p / q):
            accepted.append(draft_tokens[i])
        else:
            accepted.append(sample_from_corrected(p, q))
            break

    return accepted  # 平均長度 > 1
```

---

### 3.2 DFlash（基於 Block Diffusion 的 Speculative Decoding）

**核心機制：使用輕量 block diffusion 模型取代傳統 draft model，一次產生整段候選 token。**

DFlash 是 speculative decoding 框架下的一個具體實作，其創新在於 draft 階段的設計：

```
傳統 speculative decoding:
  draft model (小 LLM) → 逐 token 產生 γ 個候選
  └─ 仍為自回歸，只是模型較小

DFlash:
  block diffusion model → 一次產生整段 γ 個候選
  └─ 非自回歸，完全平行
```

**DFlash 的 block diffusion 如何運作：**

```
Step 1: 從純雜訊開始（γ 個 token 的 noise）
  [noise, noise, noise, noise, noise]

Step 2: 迭代去噪（通常 4-8 步）
  [noise, noise, noise, noise, noise]
  → [t1,   noise, noise, noise, noise]  (step 1)
  → [t1,   t2,    noise, noise, noise]  (step 2)
  → [t1,   t2,    t3,    noise, noise]  (step 3)
  → [t1,   t2,    t3,    t4,    noise]  (step 4)
  → [t1,   t2,    t3,    t4,    t5]     (step 5, 完成)

Step 3: 送入 target LLM 平行驗證（同 standard speculative decoding）
```

**關鍵特性：**
- **draft 階段完全平行**：diffusion 的每步去噪可平行處理所有位置
- **輕量模型**：block diffusion 模型參數量遠小於 target LLM（~300M vs 70B）
- **lossless**：驗證階段使用 rejection sampling，保證分布一致
- **宣稱加速**：6x lossless acceleration（論文 arXiv 2602.06036）
- **支援框架**：vLLM、SGLang、Transformers、MLX

**DFlash 與傳統 speculative decoding 的差異：**

| 面向 | 傳統 Speculative Decoding | DFlash |
|---|---|---|
| Draft 模型類型 | 小 LLM（自回歸） | Block Diffusion（非自回歸） |
| Draft 階段計算 | γ 次 forward pass | 4-8 次 diffusion step（可平行） |
| Draft 速度 | O(γ) | O(1)（平行） |
| 典型加速倍率 | 2x-3x | 4x-6x |
| 模型大小 | 通常 target 的 1/10 | 可更小（~300M） |
| 支援硬體 | 任何 GPU | 任何 GPU |

---

### 3.3 Multi-Token Prediction (MTP)

**核心機制：讓 LLM 自身具備一次預測多個 token 的能力，用於訓練與推論。**

MTP 有兩個不同的應用階段，需明確區分：

#### 3.3.1 訓練階段的 MTP（Meta 2024 原始提案）

```
傳統 LLM 訓練：
  "The capital of France is Paris"
  輸入: "The capital of France is"
  目標: "Paris"（只預測下一個 token）

MTP 訓練（n=3）：
  輸入: "The capital of France is"
  目標 1: "Paris"    (head 1, 標準 next-token)
  目標 2: " is"      (head 2, 預測下下個)
  目標 3: " beautiful" (head 3, 預測下下下個)
```

- 在 Transformer 頂部疊加 n 個獨立的 prediction heads
- 每個 head 負責預測不同偏移量的未來 token
- 總 loss = main loss + λ * auxiliary losses
- **效果**：提升樣本效率，模型學到更長程的語意表徵

#### 3.3.2 推論階段的 MTP（用於 Speculative Decoding）

MTP heads 在推論時可取代外部 draft model：

```
Step 1: target LLM 產生 token t1
Step 2: MTP head 1 預測 t2（平行於 main head）
Step 3: MTP head 2 預測 t3
Step 4: MTP head 3 預測 t4
...
Step γ: 得到 γ 個候選 token
Step γ+1: target LLM 一次 forward 驗證所有候選
```

**關鍵特性：**
- **無需外部 draft model**：使用模型自身的 MTP heads
- **訓練與推論一致**：MTP heads 在訓練時已學到如何預測未來 token
- **記憶體節省**：不需載入第二個模型
- **實作**：DeepSeek V2/V3 使用 MTP 作為其 speculative decoding 方案

**MTP vs DFlash 的 draft 方式對比：**

| 面向 | DFlash | MTP |
|---|---|---|
| Draft 來源 | 外部 block diffusion 模型 | 模型自身的 MTP heads |
| Draft 方式 | 非自回歸（diffusion） | 自回歸（但多 head 平行） |
| 額外參數 | 完整 diffusion 模型（~300M） | 數個 linear heads（~幾 M） |
| 訓練需求 | 需額外訓練 draft model | 需在預訓練時加入 MTP loss |
| 適用場景 | 已部署的 LLM（無需重新訓練） | 從頭訓練或 fine-tune 的 LLM |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **KV Cache + PageAttention** | 將歷史 KV 值快取於 GPU memory，避免重複計算；PageAttention 以 page 為單位管理 KV cache 減少碎片 | 需 vLLM 或類似推論框架 | GPU memory 消耗隨序列長度線性成長 | 2x-5x throughput 提升（主要受益於 memory 管理而非減少 forward pass） |
| **Quantization（INT4/INT8/FP8）** | 將模型權重從 FP16 量化為更低精度，減少 memory bandwidth 需求 | 需支援量化 kernel 的硬體（如 NVIDIA Ada/Ampere+） | 精度損失（通常 < 1% perplexity 增加） | 2x-4x memory bandwidth 效率提升，間接加速 decode |
| **Medusa** | 在 LLM 頂部疊加多個 prediction heads（類似 MTP），推論時用 tree attention 平行驗證多個候選路徑 | 需對模型做 fine-tune 加入 Medusa heads | 需 fine-tune（約 1 天 on 8 GPU）；heads 數量影響 memory | 2x-3x 加速（無需外部 draft model） |
| **Lookahead Decoding** | 使用 Jacobi iteration 將自回歸解碼轉換為非自回歸的固定點迭代 | 無需修改模型或訓練 | 收斂不保證；對長序列效果遞減 | 1.5x-2x 加速（實作簡單） |
| **Prompt Lookup Decoding** | 從 prompt 中直接複製重複出現的 token 序列作為 draft | 輸入中需有重複模式（如 code completion 中的 boilerplate） | 僅對特定場景有效 | 1.5x-3x 加速（零成本，無需額外模型） |

### 4.2 各方案切入點差異

```
問題：自回歸解碼的序列瓶頸

解法分類：
├── 減少 forward pass 次數（speculative decoding 家族）
│   ├── 外部 draft model（傳統 SD）
│   ├── 外部 diffusion model（DFlash）
│   ├── 內部 heads（MTP / Medusa）
│   └── 輸入複製（Prompt Lookup）
│
├── 加速單次 forward pass
│   ├── Quantization（降低 memory bandwidth 需求）
│   ├── KV Cache（避免重複計算）
│   └── FlashAttention（優化 attention 計算）
│
└── 改變解碼演算法
    ├── Lookahead Decoding（Jacobi iteration）
    └── Parallel Decoding（非自回歸架構）
```

### 4.3 關鍵取捨總結

| 取捨面向 | 選項 A | 選項 B |
|---|---|---|
| 是否需要額外模型 | DFlash / 傳統 SD（需要） | MTP / Medusa（不需要） |
| 是否需要重新訓練 | Prompt Lookup / DFlash（不需要） | MTP / Medusa（需要） |
| 是否 lossless | 全部都是（rejection sampling 保證） | — |
| 實作複雜度 | Prompt Lookup（最低）→ DFlash（中等）→ MTP（高，需訓練） | — |
| 加速倍率上限 | DFlash（6x）> MTP/Medusa（3x）> Prompt Lookup（3x）> 傳統 SD（2x） | — |
