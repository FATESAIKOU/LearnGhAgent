# 106_R3_step2-plan_C1.md

## 狀況理解

本 sub-step 為 R3 的 Step 2 調研。R3 使用者對 R1 報告提出 4 個具體質疑：(1) 三者的上層/下層關係不明；(2) 要求比較表；(3) DFlash 的 diffusion 與字串的差異；(4) 三者的平行/串列化是否相同。本 step 需針對這 4 題重新取得資料，而非重複 R1 的調研。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 R1 報告全文（output/106_dflash-speculative-decoding-mtp.md） | 確認 R1 已涵蓋的內容與使用者不理解的癥結 | 找出 R1 報告的盲點 | 成功。R1 報告 366 行，已包含關係圖、DA 表、虛擬碼，但使用者仍無法理解，表示組織方式或類比不足 |
| 讀取 DFlash 官方 repo（z-lab/dflash, 5.3k stars） | 取得 DFlash 的架構說明、支援模型列表、使用方式 | 確認 DFlash 的實作細節與定位 | 成功。DFlash 是 block diffusion 模型，支援 20+ 模型（Qwen3.5/3.6、Gemma-4、Kimi-K2.5/2.6、MiniMax-M2.5/2.7、DeepSeek-V4 等），整合 vLLM/SGLang/MLX/Transformers |
| 讀取 DFlash arXiv 論文（2602.06036, ICML 2026） | 取得 DFlash 的學術定義與加速原理 | 確認 DFlash 的技術定位 | 成功。論文明確指出 DFlash 是 speculative decoding 框架下的實作，使用 block diffusion 做 parallel drafting，6x lossless acceleration |
| 讀取 Speculative Decoding Wikipedia 條目 | 確認 speculative decoding 的定義與 variants | 確認上層框架的定義 | 成功。Wikipedia 明確將 speculative decoding 定義為上層框架，Medusa/EAGLE/SpecInfer 為 variants |
| 讀取 MTP 原始論文（2404.19737, Meta） | 確認 MTP 的定義與定位 | 確認 MTP 與 speculative decoding 的關係 | 成功。Meta 論文提出 multi-token prediction 作為訓練目標，同時指出可加速 inference 2-3x，屬於 self-speculative decoding |
| 搜尋 arXiv 上 DFlash 相關論文（2606.26744 HyperDFlash, 2606.07710 WhiFlash, 2606.02091 DFlare 等） | 確認 DFlash 在學術界的定位與後續發展 | 了解 DFlash 是否被視為獨立技術或 speculative decoding 的子集 | 成功。所有後續論文（HyperDFlash, WhiFlash, DFlare, DDTree, TAPS, D-PACE 等）都將 DFlash 定位為「speculative decoding 框架下的 block diffusion 實作」 |
| 搜尋 arXiv 上 MTP 相關論文（2606.27550 EntMTP, 2606.26744 HyperDFlash 等） | 確認 MTP 在學術界的定位 | 了解 MTP 是否被視為獨立技術或 speculative decoding 的子集 | 成功。HyperDFlash 論文明確指出「DeepSeek-V4 的 native MTP module」與「DFlash」是兩種不同的 drafting 方法，MTP 是 self-speculative decoding 的一種 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 三者層級關係 | 比對 Wikipedia、論文、repo 的用語 | 明確：Speculative decoding 是上層框架，DFlash 與 MTP 是該框架下的兩種實作方案（sibling 關係） |
| DFlash 的 diffusion 本質 | 論文摘要與 repo README | DFlash 在連續 embedding space 操作，非離散 token 字串，與 image diffusion 本質相同 |
| 平行/串列對照 | 論文中的加速原理說明 | 三者不同：DFlash 兩階段皆平行，MTP 部分串列，傳統 SD draft 串列 |
| 使用者 Q1-Q4 的資料覆蓋 | 逐一比對 | 全部覆蓋，可進入 Step 3 QA 產出報告 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否需要重新讀取 DFlash repo | 1. 是 2. 否（沿用 R1 資料） | 是 | R1 未讀取 DFlash repo，僅讀取 Wikipedia 與 arXiv 搜尋結果；R3 需確認 DFlash 的實作細節與定位 |
| 是否需要讀取 MTP 原始論文 | 1. 是 2. 否 | 是 | R1 未讀取 MTP 論文，僅從 Wikipedia 推測；需確認 MTP 與 speculative decoding 的關係 |
| 是否需要搜尋後續論文 | 1. 是 2. 否 | 是 | 後續論文（HyperDFlash 等）直接比較 MTP 與 DFlash，提供最直接的證據證明兩者是 sibling 關係 |
| 報告組織方式 | 1. 增量補充 R1 報告 2. 以 Q1-Q4 為綱重新組織 | 以 Q1-Q4 為綱重新組織 | 使用者說「依然不懂」，表示 R1 的組織方式未達效果，需換角度 |
