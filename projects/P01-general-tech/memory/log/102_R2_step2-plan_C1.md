# 102_R2_step2-plan_C1.md

## 狀況理解

R2 使用者提出 4 個質問：(1) 三者的上下層概念關係 (2) 各自解決什麼問題與解法比較表 (3) DFlash 的 diffusion 應用在離散 token 上的合理性 (4) 三者在平行化/串列化上的異同。本 sub-step C1 為資訊收集階段，目標是取得 DFlash 論文、MTP 論文、speculative decoding 原始論文的核心資訊，以及 DFlash 的 GitHub repo 與 project page 細節，為後續回答提供原始資料。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 R1 報告 | 確認已覆蓋範圍，避免重複 | 理解 R1 不足之處 | R1 已涵蓋基本定義但未釐清上下層關係、diffusion 在離散 token 的合理性、平行/串列分析 |
| 讀取 R2 Step 1 log | 確認 R2 意圖 | 確認 4 個質問的具體需求 | 已確認 |
| 搜尋 DFlash 論文 (arXiv 2602.06036) | 取得 DFlash 核心機制描述 | 理解 block diffusion 如何作用於離散 token | 成功取得：DFlash 使用 block diffusion 模型一次產生整段 draft token，conditioning 在 target model 的 hidden features 上；論文宣稱 6x lossless acceleration，ICML 2026 accepted |
| 搜尋 MTP 論文 (arXiv 2404.19737) | 取得 MTP 原始定義 | 理解 MTP 的訓練與推論機制 | 成功取得：Meta 2024 論文，提出 multi-token prediction 作為 auxiliary training task，使用 n 個 independent output heads；推論時可達 3x 加速 |
| 搜尋 Speculative Decoding 原始論文 (arXiv 2302.01318) | 取得 speculative decoding 的理論基礎 | 理解 draft-then-verify 框架 | 成功取得：DeepMind 2023 論文，提出 speculative sampling，使用 draft model 產生候選 token 後由 target model 平行驗證，2-2.5x 加速 |
| 讀取 DFlash GitHub repo (z-lab/dflash) | 取得實作細節與支援模型列表 | 理解 DFlash 的實際部署方式 | 成功取得：支援 vLLM、SGLang、Transformers、MLX 四種 backend；支援 20+ 模型（Qwen3/3.5/3.6、Gemma-4、LLaMA-3.1、DeepSeek-V4 等）；5.3k stars |
| 讀取 DFlash project page (z-lab.ai) | 取得 DFlash 的設計原理說明 | 理解 diffusion drafting 為何優於 autoregressive drafting | 成功取得：關鍵 insight 是「target model 的 hidden features 已包含未來 token 資訊」，DFlash 將 target features 注入每個 draft layer 的 KV cache；diffusion 的 drafting cost 與 block size 無關（flat），而 autoregressive 的 cost 線性成長 |
| 搜尋 arXiv 上 DFlash 相關論文 | 了解 DFlash 的後續改進與學術定位 | 確認 DFlash 在學術界的影響力 | 成功取得：至少 10 篇後續論文（HyperDFlash、WhiFlash、DFlare、DDTree、CaDDTree、TAPS、Draft-OPD、Graft、D-PACE、Test-Time Speculation），均以 DFlash 為 baseline 進行改進 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| DFlash 論文核心機制 | 確認 block diffusion 的運作方式 | DFlash 使用 block diffusion 模型，conditioned on target model hidden features，一次 forward pass 產生整段 draft token（block size 16），單一 denoising step |
| MTP 論文核心機制 | 確認 MTP 的訓練與推論方式 | MTP 在訓練時疊加 n 個 independent prediction heads，每個 head 預測不同偏移量的未來 token；推論時可用 heads 產生 draft token 後由 target model 驗證 |
| Speculative Decoding 框架 | 確認 draft-then-verify 的理論基礎 | 使用 rejection sampling 保證 lossless；draft model 可為任何能快速產生 token 的機制 |
| DFlash 的 diffusion 在離散 token 的應用 | 確認 diffusion 如何處理離散 token | DFlash 的 block diffusion 在 continuous latent space 中操作（非直接在離散 token 上），透過 embedding 將離散 token 映射到連續空間，去噪後再透過 LM head 映射回離散 token |
| 三者的上下層關係 | 從論文與實作確認 | Speculative decoding 是上層框架（draft-then-verify）；DFlash 是使用 block diffusion 作為 draft 機制的實作；MTP 是使用多頭預測作為 draft 機制的實作。兩者都是 speculative decoding 框架下的具體方案 |
| 平行/串列維度 | 從論文與實作確認 | Draft 階段：傳統 SD 串列（autoregressive）、DFlash 平行（diffusion）、MTP 可平行（多 head 同時預測）。Verify 階段：三者皆平行（一次 forward pass 驗證所有候選） |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否需額外搜尋 diffusion 在離散 token 的技術背景 | 1. 搜尋 block diffusion / diffusion LLM 論文 2. 從 DFlash 論文與 project page 已足夠 | 從 DFlash 論文與 project page 已足夠 | DFlash project page 已清楚說明 block diffusion 在 continuous latent space 操作，且 DFlash 論文引用 block diffusion 相關文獻（Arriola et al. 2025, Block Diffusion） |
| 是否搜尋 EAGLE-3 作為對照 | 1. 搜尋 2. 不搜尋 | 不搜尋 | 使用者問題聚焦於 SD/DFlash/MTP 三者關係，EAGLE-3 為 autoregressive draft 的代表但非使用者提問範圍；R1 報告已涵蓋 Medusa 作為對照 |
| 是否搜尋 DeepSeek 的 MTP 實作 | 1. 搜尋 2. 不搜尋 | 不搜尋 | R1 報告已提及 DeepSeek V2/V3 使用 MTP；使用者問題聚焦於概念關係而非特定實作 |
