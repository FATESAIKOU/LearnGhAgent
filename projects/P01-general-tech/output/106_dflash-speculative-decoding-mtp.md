# DFlash / Speculative Decoding / Multi-Token Prediction (MTP)

> 本報告針對 R3 使用者 4 個具體提問重新組織，以提問為綱，逐一回答。

---

## 1. 這個技術解決什麼問題？

**LLM 自回歸解碼（autoregressive decoding）的推論速度瓶頸。**

LLM 生成文字時，一次只能產生一個 token，每個 token 都需要完整執行一次 forward pass。這導致：
- 輸出延遲與輸出長度成正比
- GPU 計算利用率低落（memory-bound，而非 compute-bound）

Speculative decoding、DFlash、MTP 三者的共同目標：**在不降低生成品質的前提下，減少 LLM 解碼所需的 forward pass 次數**。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 自回歸解碼的本質限制

LLM（decoder-only Transformer）的生成過程是逐 token 進行的：

```
給定 prompt "The capital of France is"
Step 1: 計算 P(paris | "The capital of France is") → 輸出 "paris"
Step 2: 計算 P(. | "The capital of France is paris") → 輸出 "."
```

每一步都依賴上一步的輸出，無法平行化。

### 2.2 GPU 計算特性 mismatch

- LLM forward pass 是 **memory-bound**：瓶頸在於從 HBM 讀取模型權重（~100GB/s），而非實際計算（~1000 TFLOPS）
- 單 token 生成時，計算量小但權重讀取量大，GPU 利用率極低（通常 < 10%）
- 若能一次處理多個 token，計算/記憶體存取比提升，利用率隨之上升

---

## 3. 這個技術是如何解決該問題的？

### Q1：speculative decoding / dflash / mtp 到底誰是誰的上層概念？

**Speculative decoding 是上層框架，DFlash 與 MTP 是該框架下的兩種實作方案。**

```
上層框架：Speculative Decoding（定義「先快速產生草稿 → 再平行驗證」的兩階段流程）
  │
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

**類比（工程師用語）：**

| 概念 | 類比 |
|---|---|
| Speculative decoding | 一個 **interface**（定義了 `draft()` + `verify()` 兩個方法） |
| DFlash | 一個 **class** 實作了這個 interface，`draft()` 用 block diffusion |
| MTP | 另一個 **class** 實作了這個 interface，`draft()` 用多頭預測 heads |

---

### Q2：這三個概念各自解決甚麼問題？如何解決問題？

| 概念 | 解決的問題 | 如何解決 | 核心機制 |
|---|---|---|---|
| **Speculative decoding**（框架） | 自回歸解碼的序列瓶頸 | 定義「快速草稿 → 平行驗證」兩階段流程，減少 target LLM 的 forward pass 次數 | Draft model 產生 γ 個候選 token → target LLM 一次 forward 驗證全部 → rejection sampling 保證 lossless |
| **DFlash**（實作） | 傳統 speculative decoding 的 draft 階段仍為自回歸（小 LLM 仍需逐 token 生成） | 用 block diffusion 模型一次平行產生整段候選 token，draft 階段從 O(γ) 降為 O(1) | 從雜訊開始，經 4-8 步去噪（每步平行處理所有位置），一次輸出 γ 個 token |
| **MTP**（實作） | 傳統 speculative decoding 需要載入額外的外部 draft model（增加記憶體開銷） | 在 LLM 自身疊加多個 prediction heads，讓模型自身具備一次預測多個 token 的能力 | 訓練時加入 auxiliary heads 預測未來 token；推論時用這些 heads 產生草稿，無需外部模型 |

**三者的加速原理對比：**

```
傳統自回歸（無加速）：
  Step 1: forward → token A
  Step 2: forward → token B
  Step 3: forward → token C
  Step 4: forward → token D
  總計：4 次 forward pass，4 個 token

Speculative decoding（通用框架）：
  Step 1: draft model 快速產生 [A', B', C', D']（草稿）
  Step 2: target LLM 一次 forward 驗證全部 → 接受 [A, B, C]（丟棄 D'）
  總計：1 次 target forward + 1 次 draft，3 個 token

DFlash（draft 用 diffusion）：
  Step 1: block diffusion 一次平行產生 [A', B', C', D']（非自回歸）
  Step 2: target LLM 一次 forward 驗證全部
  總計：1 次 target forward + 1 次 diffusion（4-8 步但可平行），3-4 個 token

MTP（draft 用自身 heads）：
  Step 1: target LLM 產生 token A
  Step 2: MTP head 1 預測 B', head 2 預測 C', head 3 預測 D'（平行）
  Step 3: target LLM 一次 forward 驗證 [B', C', D']
  總計：2 次 target forward，3-4 個 token
```

---

### Q3：dflash 聽起來是 diffusion 應用，感覺跟字串不一樣吧？

**正確。DFlash 的 block diffusion 不是在字串（token 序列）上操作，而是在連續向量空間（continuous embedding space）上操作。**

這是理解 DFlash 最關鍵的一點。以下是 token 在 DFlash 中的完整資料流：

```
階段 1：Token → Embedding（離散 → 連續）
  token 序列 ["Paris", "is", "a", "city"]
  → lookup embedding table
  → 連續向量矩陣 [[0.23, -0.45, ...], [0.12, 0.67, ...], ...]
  → shape: (γ, d_model)

階段 2：Block Diffusion（在連續空間中操作）
  初始：純雜訊矩陣（高斯 noise），shape 同為 (γ, d_model)
  去噪 step 1: noise → 接近目標的向量
  去噪 step 2: 更接近
  ...
  去噪 step 4-8: 得到最終連續向量矩陣

階段 3：Embedding → Token（連續 → 離散）
  連續向量矩陣 → 與 embedding table 做 nearest neighbor search
  → 離散 token 序列 ["Paris", "is", "a", "city"]
```

**Python 虛擬碼展示：**

```python
# DFlash 的 block diffusion 流程（簡化）

# 詞彙表大小 V，embedding 維度 d
embedding_table = nn.Embedding(V, d)  # 將 token ID 映射到連續向量

# === 階段 1：將 prompt 的最後 γ 個 token 轉為 embedding ===
prompt_tokens = tokenizer("The capital of France is")  # [101, 205, 512, ...]
context_embed = embedding_table(prompt_tokens[-1])  # shape: (d,)

# === 階段 2：Block Diffusion（在連續空間操作）===
# 初始化：γ 個高斯雜訊向量
noise = torch.randn(gamma, d)  # shape: (γ, d)

# 迭代去噪（4-8 步），每一步平行處理所有 γ 個位置
x = noise
for step in range(4):
    # 條件：以 context_embed 為條件，預測雜訊
    predicted_noise = block_diffusion_model(x, context_embed)
    # 去噪：x = x - predicted_noise
    x = x - predicted_noise
    # x 的 shape 始終為 (γ, d)，所有位置同時更新

# x 現在是 γ 個連續向量，每個向量應接近某個 token 的 embedding
# shape: (γ, d)

# === 階段 3：將連續向量離散化為 token ID ===
# 對每個位置，找 embedding table 中最近的向量
draft_token_ids = []
for i in range(gamma):
    # x[i] shape: (d,)
    # embedding_table.weight shape: (V, d)
    distances = cosine_similarity(x[i], embedding_table.weight)  # shape: (V,)
    nearest_token_id = argmax(distances)
    draft_token_ids.append(nearest_token_id)

# draft_token_ids = [512, 103, 789, 456]  # 對應 ["Paris", "is", "a", "city"]
```

**關鍵結論：**

| 面向 | 說明 |
|---|---|
| Diffusion 操作的對象 | 連續向量（embedding），**不是**離散 token 字串 |
| 為什麼可以平行 | 因為 diffusion 的每一步可以同時對所有 γ 個位置的向量做去噪，沒有序列依賴 |
| 為什麼 diffusion 步驟少（4-8 步） | 因為 block diffusion 只需要產生「夠好的草稿」即可，不需要像 image diffusion 那樣高品質 |
| 與 image diffusion 的差異 | Image diffusion 在像素空間操作（連續），DFlash 在 embedding 空間操作（也是連續），本質相同 |

---

### Q4：這三個方法平行化跟串列化的地方都一樣？

**不一樣。以下是三者在「哪些環節平行、哪些環節串列」的完整對照：**

```
傳統自回歸（無加速）：
  [串列] token 1 → token 2 → token 3 → token 4
  無任何平行化

Speculative decoding（通用框架）：
  [串列] draft model 逐 token 產生草稿（仍是自回歸）
  [平行] target LLM 一次 forward 驗證所有候選 token
  瓶頸：draft 階段仍為串列

DFlash：
  [平行] block diffusion 一次產生整段草稿（非自回歸）
  [平行] target LLM 一次 forward 驗證所有候選 token
  兩階段皆平行

MTP：
  [串列] target LLM 先產生第一個 token（自回歸）
  [平行] MTP heads 同時預測第 2, 3, ..., γ 個 token
  [平行] target LLM 一次 forward 驗證所有候選 token
  第一階段部分串列（1 個 token），其餘平行
```

**流程圖對照：**

```
傳統自回歸：
  t1 ──→ t2 ──→ t3 ──→ t4
  全部串列，4 次 forward

Speculative Decoding（傳統，用小 LLM 做 draft）：
  draft:  t1' ──→ t2' ──→ t3' ──→ t4'    （串列，小模型 4 次 forward）
  verify:        一次驗證全部 ──→ [t1, t2, t3]  （平行，大模型 1 次 forward）
  總計：小模型 4 次（串列）+ 大模型 1 次（平行）

DFlash：
  draft:  [t1', t2', t3', t4'] 一次產生     （平行，diffusion 4-8 步但每步平行）
  verify: 一次驗證全部 ──→ [t1, t2, t3, t4]  （平行，大模型 1 次 forward）
  總計：diffusion 1 次（平行）+ 大模型 1 次（平行）

MTP：
  step 1: target LLM 產生 t1                    （串列，1 次 forward）
  step 2: MTP heads 同時預測 t2', t3', t4'       （平行，無需 forward）
  step 3: target LLM 一次驗證 [t2', t3', t4']    （平行，1 次 forward）
  總計：大模型 2 次 forward（1 次串列 + 1 次平行）
```

**平行化程度排名：**

| 方法 | Draft 階段 | Verify 階段 | 總 forward 次數（γ=4） | 理論加速 |
|---|---|---|---|---|
| 傳統自回歸 | 串列 | 串列 | 4 次 | 1x（baseline） |
| 傳統 SD（小 LLM draft） | 串列（小模型） | 平行 | 小模型 4 次 + 大模型 1 次 | 2-3x |
| MTP | 部分串列（1 token）+ 平行（heads） | 平行 | 大模型 2 次 | 2-3x |
| DFlash | 完全平行 | 平行 | 大模型 1 次 + diffusion 1 次 | 4-6x |

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

---

## 5. User Q&A

### Q1：speculative decoding / dflash / mtp 到底誰是誰的上層概念？

**A**：Speculative decoding 是上層框架，DFlash 與 MTP 是該框架下的兩種實作方案。

| 層級 | 角色 | 類比 |
|---|---|---|
| Speculative decoding | 上層框架（定義 `draft()` + `verify()` 介面） | Java interface |
| DFlash | 實作方案 A（`draft()` 用 block diffusion） | 實作該 interface 的 class A |
| MTP | 實作方案 B（`draft()` 用多頭預測 heads） | 實作該 interface 的 class B |

- 不存在「DFlash 包含 MTP」或「MTP 包含 DFlash」的關係
- 兩者是 sibling（兄弟）關係，上層是 speculative decoding

**結論**：Speculative decoding 是框架，DFlash 與 MTP 是該框架下的兩種實作。

---

### Q2：這三個概念各自解決甚麼問題？如何解決問題？請做表比較

**A**：

| 概念 | 解決的問題 | 如何解決 | 核心機制 |
|---|---|---|---|
| **Speculative decoding**（框架） | 自回歸解碼的序列瓶頸 | 定義「快速草稿 → 平行驗證」兩階段流程 | Draft model 產生 γ 個候選 → target LLM 一次 forward 驗證 → rejection sampling |
| **DFlash**（實作） | 傳統 SD 的 draft 階段仍為自回歸 | 用 block diffusion 一次平行產生整段草稿 | 在 embedding space 做 4-8 步去噪，draft 從 O(γ) 降為 O(1) |
| **MTP**（實作） | 傳統 SD 需要載入外部 draft model | 用模型自身的 MTP heads 產生草稿 | 訓練時加入 auxiliary heads，推論時用 heads 預測未來 token |

**結論**：三者目標相同（減少 forward pass 次數），差異在 draft 階段的實作方式。

---

### Q3：dflash 聽起來是 diffusion 應用，感覺跟字串不一樣吧？

**A**：正確。DFlash 的 block diffusion 不是在字串（token 序列）上操作，而是在連續向量空間（continuous embedding space）上操作。

```
Token 序列（離散）           Embedding 空間（連續）          Token 序列（離散）
["Paris", "is", ...]  ──→  [[0.23, -0.45, ...],    ──→  ["Paris", "is", ...]
                            [0.12, 0.67, ...], ...]
                            ↑ diffusion 在此空間操作 ↑
```

| 面向 | 說明 |
|---|---|
| Diffusion 操作的對象 | 連續向量（embedding），**不是**離散 token 字串 |
| 為什麼可以平行 | 因為 diffusion 的每一步可以同時對所有 γ 個位置的向量做去噪，沒有序列依賴 |
| 與 image diffusion 的差異 | Image diffusion 在像素空間（連續），DFlash 在 embedding 空間（也是連續），本質相同 |

**結論**：DFlash 的 diffusion 在連續 embedding 空間操作，與 image diffusion 在本質上相同，只是操作的對象從像素換成 token embedding。

---

### Q4：這三個方法平行化跟串列化的地方都一樣？

**A**：不一樣。以下是三者在「哪些環節平行、哪些環節串列」的完整對照：

| 方法 | Draft 階段 | Verify 階段 | 總 forward 次數（γ=4） | 理論加速 |
|---|---|---|---|---|
| 傳統自回歸 | 串列 | 串列 | 4 次 | 1x（baseline） |
| 傳統 SD（小 LLM draft） | 串列（小模型） | 平行 | 小模型 4 次 + 大模型 1 次 | 2-3x |
| MTP | 部分串列（1 token）+ 平行（heads） | 平行 | 大模型 2 次 | 2-3x |
| DFlash | 完全平行 | 平行 | 大模型 1 次 + diffusion 1 次 | 4-6x |

```
傳統自回歸：  t1 ──→ t2 ──→ t3 ──→ t4                   全部串列
傳統 SD：     draft: t1'─→t2'─→t3'─→t4'  verify: 一次驗證  draft 串列，verify 平行
MTP：         t1 → heads 平行預測 t2',t3',t4' → 一次驗證  部分串列，其餘平行
DFlash：      draft: 一次產生全部  verify: 一次驗證        全部平行
```

**結論**：三者的平行化程度不同。DFlash 是唯一 draft 與 verify 兩階段皆完全平行的方法；MTP 需先串列產生第一個 token；傳統 SD 的 draft 階段仍為串列。
