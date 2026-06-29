# 102_R1_step2-plan_C1.md

## 狀況理解

使用者要求解析三個名詞：dflash、speculative decoding、mtp。Step 2 C1 的任務是取得 repo metadata 與主要文件。三個名詞彼此關聯：speculative decoding 是上層概念，dflash 與 mtp 是其實現方法。需從 GitHub 與 arxiv 取得核心 repo 的 README 與論文摘要。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| GitHub 搜尋 `dflash llm` | 定位 dflash 的主要 repo | 找到 z-lab/dflash（5.3k stars） | 成功，確認 dflash 為 z-lab 的 block diffusion 方案 |
| GitHub 搜尋 `speculative decoding`（依 stars 排序） | 定位 speculative decoding 的主要 repo | 找到 z-lab/dflash（5.3k）、NVIDIA/Model-Optimizer（3k）、deepseek-ai/DeepSpec（1.9k）等 | 成功，確認 top repo 分布 |
| GitHub 搜尋 `mtp llm`（依 stars 排序） | 定位 MTP 的主要 repo | 找到 Awesome-Multi-Token-Prediction（159 stars）、MTPLX（867 stars）等 | 成功，確認 MTP 相關 repo |
| 讀取 z-lab/dflash README | 取得 dflash 的完整說明 | 了解 dflash 是 block diffusion 用於 speculative decoding | 成功，取得安裝方式、支援模型列表、論文連結 |
| 讀取 deepseek-ai/DeepSpec README | 取得 speculative decoding 訓練框架說明 | 了解 DeepSpec 支援 DFlash、Eagle3、DSpark 三種演算法 | 成功，取得演算法對照表與 released checkpoints |
| 讀取 Xiaohao-Liu/Awesome-Multi-Token-Prediction README | 取得 MTP 的論文列表與定義 | 了解 MTP 是讓模型一次預測多個 token 的訓練/推理範式 | 成功，取得完整論文時間線與分類 |
| 讀取 youssofal/MTPLX README | 取得 MTP 實作專案的說明 | 了解 MTPLX 是 Apple Silicon 上的 native MTP 推論引擎 | 成功，取得 MTP 在推論端的實際應用方式 |
| 讀取 arxiv 2602.06036（DFlash 論文摘要） | 取得 dflash 的學術定義 | 了解 dflash 使用輕量 block diffusion 模型做平行 draft | 成功，確認 6x lossless acceleration 宣稱 |
| 讀取 arxiv 2404.19737（Meta MTP 論文摘要） | 取得 MTP 的學術起源 | 了解 MTP 最初由 Meta 提出作為訓練輔助任務 | 成功，確認 MTP 的訓練階段與推論加速雙重用途 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| dflash 核心 repo | 確認 z-lab/dflash 為官方實作 | 5.3k stars，MIT license，支援 vLLM/SGLang/Transformers/MLX |
| speculative decoding 定義 | 確認其為「用 fast draft model 產生候選 token，再由 target LLM 平行驗證」的加速技術 | 已有成熟論文脈絡（Leviathan & Chen 2023） |
| MTP 定義 | 確認 MTP 有兩個面向：訓練階段（Meta 2024 提出多頭預測 auxiliary loss）與推論階段（用 native MTP heads 做 speculative decoding） | MTP 可同時用於訓練（提升樣本效率）與推論（加速 decode） |
| 三者關係 | dflash 是 speculative decoding 的一種實現；MTP 是另一種實現（使用模型自身的 MTP heads 而非外部 draft model） | 三者非平行概念，而是「speculative decoding 為上層框架，dflash 與 mtp 為其下具體演算法」 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否使用 gh api 取得 repo metadata | 1. gh api 2. web fetch | web fetch | 環境中 gh 可能未認證，web fetch 可直接取得 README 全文 |
| 是否讀取論文全文 | 1. 只讀摘要 2. 讀全文 | 只讀摘要 | C1 階段只需取得 metadata 與文件定位，論文細節留給 C2 |
| 三個名詞的調研順序 | 1. 依字母 2. 由上層到下層 | 由上層到下層（speculative decoding → dflash → mtp） | 三者有包含關係，先理解上層概念有助於定位下層 |
