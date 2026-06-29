# 102_R2_step2-plan_C1.md

## 狀況理解

R2 使用者提出 4 個追問：(1) 三者的上下層關係（仍不懂）(2) 要求做表比較各自解決什麼問題與如何解決 (3) DFlash 的 diffusion 與字串的差異 (4) 三者的平行/串列化是否相同。R1 報告已有 §5 Q&A（Q1-Q12）涵蓋這 4 個問題，但使用者仍不滿意，表示解釋方式需要調整。C1 任務為取得 repo metadata 與主要文件，針對 R2 的意圖補查新資料，而非重做 R1 的事。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 DFlash 論文全文（arXiv HTML） | 取得 DFlash 的完整技術細節，特別是 KV injection 機制、block diffusion 訓練方式、loss weighting | 理解 DFlash 的 diffusion 如何在連續空間操作，以及與傳統 SD 的本質差異 | 成功。取得關鍵資訊：(1) DFlash 使用 KV injection 而非 input fusion，每層 draft layer 都注入 target hidden features (2) block diffusion 在 embedding 連續空間操作，單步去噪 (3) loss weighting 對 block 內早期位置加權 (4) acceptance length 隨 draft layer 深度線性成長 |
| 讀取 DFlash 官方 blog（z-lab.ai） | 取得更直觀的架構圖與設計理念 | 理解「the target knows best」的核心洞察 | 成功。確認 DFlash 的關鍵 insight：target LLM 的 hidden features 已隱含多個 future token 的資訊，draft model 只需做 diffusion adapter |
| 讀取 DeepSpec repo README | 確認 DFlash 在業界生態中的定位 | 了解 DFlash 與其他 speculative decoding 演算法的關係 | 成功。DeepSpec 將 DFlash、Eagle3、DSpark 並列為三種 draft model 演算法，使用統一訓練框架。DFlash 已從獨立 repo 升級為業界標準方案之一 |
| 讀取 Awesome-MTP repo README | 確認 MTP 的完整研究脈絡 | 了解 MTP 不只是 Meta 的論文，而是一個研究領域 | 成功。MTP 最早可追溯到 2018（UC Berkeley Blockwise Parallel Decoding），2024 Meta 論文為里程碑，2025 有 19 篇論文。DFlash 被歸類在「Speculative Decoding + MTP」分類下 |
| 讀取 Meta MTP 論文摘要 | 確認 MTP 原始定義 | 了解 MTP 的訓練階段與推論加速雙重用途 | 成功。Meta 論文提出 MTP 作為 auxiliary training task，提升 sample efficiency，推論時可達 3x 加速 |
| 比對 R1 報告 §5 Q&A 與 R2 問題 | 確認 R1 已涵蓋哪些內容，R2 需要補充什麼 | 判斷 R2 的解釋方式需要調整而非內容不足 | 成功。R1 的 Q1-Q12 已涵蓋 R2 的 4 個問題，但使用者仍不滿意。問題不在內容不足，而在：(1) 報告太長（719 行）難以消化 (2) 需要更精簡的對照表而非文字段落 (3) 需要從「問題鏈」視角而非「名詞定義」視角解釋 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| DFlash 論文關鍵技術細節 | 確認 KV injection vs input fusion 的差異 | DFlash 將 target hidden features 注入每層 draft layer 的 KV cache，而非像 EAGLE-3 只在 input layer 融合。這是 DFlash 能達到 6x 加速的核心原因 |
| DFlash 的 diffusion 操作空間 | 確認 block diffusion 在 embedding 連續空間操作 | DFlash 的 diffusion 在 token embedding 的連續 float32 空間操作，單步去噪後透過 LM head 映射回離散 token。與影像 diffusion 在 pixel 連續空間操作的邏輯相同 |
| MTP 的研究脈絡 | 確認 MTP 不是單一論文而是一個研究領域 | MTP 最早 2018（Blockwise Parallel Decoding），2024 Meta 論文為關鍵里程碑，2025 有 19 篇論文。DFlash 被歸類在 MTP 相關的 speculative decoding 方案下 |
| DFlash 在業界的定位 | 確認 DFlash 已被 DeepSpec 整合為標準演算法之一 | DeepSpec 支援 DFlash、Eagle3、DSpark 三種演算法，使用統一訓練框架。DFlash 已從學術論文進入生產級部署 |
| R2 需要補充的方向 | 判斷 R2 的解釋策略 | (1) 從「問題鏈」視角解釋，不要從名詞定義開始 (2) 用更精簡的對照表取代文字段落 (3) 用使用者熟悉的程式語言類比（Python 資料型別、async/await）(4) 用具體數值範例取代抽象描述 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否讀取 DFlash 論文全文 | 1. 只讀摘要 2. 讀全文 | 讀全文 | R2 使用者對 diffusion 與字串的差異有具體疑惑，需要論文原文的技術細節來澄清。摘要不足以回答「diffusion 如何在連續空間操作離散 token」 |
| 是否讀取 DeepSpec repo | 1. 需要 2. 不需要 | 需要 | DeepSpec 是 DFlash 被業界採用的關鍵證據，且顯示 DFlash 與 Eagle3、DSpark 的並列關係，有助於回答「誰是誰的上層概念」 |
| 是否讀取 Awesome-MTP repo | 1. 需要 2. 不需要 | 需要 | 使用者對 MTP 的理解可能僅限於 Meta 論文，需要展示 MTP 是一個更大的研究領域，DFlash 只是其中一個應用方向 |
| C1 後是否需要 C2 | 1. 需要 2. 不需要 | 需要（C2） | C1 已取得足夠的技術細節，但 R2 的 4 個問題需要重新組織解釋方式。C2 應聚焦於：(1) 從問題鏈視角重新解釋三者關係 (2) 用 Python 資料型別類比 diffusion 與字串的差異 (3) 用 async/await 類比平行/串列化 |
