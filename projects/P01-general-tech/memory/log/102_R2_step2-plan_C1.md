# 102_R2_step2-plan_C1.md

## 狀況理解

R2 使用者提出 4 個追問，核心問題是「R1 報告已涵蓋但使用者未吸收」。R2 不需大規模新搜尋，而是需要：(1) 重新檢視論文原文確認關鍵論述無誤；(2) 從論文與 repo 中尋找更直觀的圖示、程式碼範例、或實作細節，以便在 Step 3 用不同角度重新解釋。本 sub-step C1 負責取得 DFlash 論文全文、MTP 論文摘要、DFlash GitHub repo 資訊。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 R1 報告 output/102_llm-inference-acceleration.md | 確認 R1 已涵蓋內容，避免重複 | 判斷 R2 需補充的方向 | 成功。R1 已涵蓋三者關係圖、比較表、diffusion 連續空間說明、平行/串列分析 |
| 讀取 DFlash 論文 arXiv 頁面（2602.06036） | 取得論文 metadata 與摘要 | 確認 DFlash 的定位與宣稱 | 成功。論文標題明確指出 DFlash 是「Block Diffusion for Flash Speculative Decoding」，屬於 SD 框架下的實作 |
| 讀取 DFlash 論文 HTML 全文 | 取得方法論細節，特別是 block diffusion 如何作用於離散 token | 確認 diffusion 在連續空間操作的具體機制 | 成功。論文 §4.1 明確說明：hidden features → KV injection → block diffusion（在 embedding 連續空間）→ LM head 映射回離散 token |
| 讀取 DFlash GitHub repo（z-lab/dflash） | 取得 README、支援模型列表、安裝方式、使用範例 | 確認實作細節與生態系 | 成功。repo 5.3k stars，支援 Transformers/SGLang/vLLM/MLX 四種後端，提供完整使用範例 |
| 讀取 MTP 論文 arXiv 頁面（2404.19737） | 取得 MTP 論文摘要 | 確認 MTP 的定位 | 成功。Meta 2024 論文，提出 multi-token prediction 作為 auxiliary training task，推論時可達 3x 加速 |
| 讀取 R1 step logs | 確認 R1 的決策邏輯與搜尋範圍 | 了解 R1 為何未能讓使用者吸收 | 成功。R1 報告結構偏學術（先總覽再細節），使用者需要更口語、更逐步的解釋 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| DFlash 論文是否支援 R1 報告的論述 | 比對論文摘要與 R1 §3.2 內容 | 一致。論文明確說 DFlash 是 speculative decoding 框架下的實作，使用 block diffusion 做 parallel drafting |
| DFlash 的 diffusion 機制是否如 R1 所述在連續空間操作 | 比對論文 §4.1 與 R1 Q3 回答 | 一致。論文說明：target hidden features → KV injection → block diffusion（embedding space）→ LM head → discrete tokens |
| MTP 論文是否支援 R1 報告的論述 | 比對論文摘要與 R1 §3.3 內容 | 一致。論文提出 multi-token prediction 作為 auxiliary training task，推論時可達 3x 加速 |
| 三者關係是否如 R1 所述 | 比對論文定位與 R1 §1 關係圖 | 一致。DFlash 論文自稱「speculative decoding framework」，MTP 論文自稱「multi-token prediction for training & inference」，兩者皆為 SD 框架下的實作 |
| 是否需要補充搜尋 | 判斷 R2 是否需要新資訊 | 不需要。R1 報告已涵蓋所有必要資訊，R2 重點在於重新組織與換角度解釋 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| R2 的搜尋策略 | 1. 重新搜尋所有論文 2. 只驗證 R1 報告的正確性 3. 搜尋更多教學資源 | 只驗證 R1 報告的正確性 | R1 報告已涵蓋足夠資訊，使用者問題在於理解而非資訊不足 |
| 是否需要搜尋中文教學資源 | 1. 需要 2. 不需要 | 不需要 | 使用者是工程師，英文論文與技術文件即可；問題在於解釋角度而非語言 |
| 是否下載論文 PDF 全文 | 1. 需要 2. 不需要 | 不需要 | HTML 全文已提供足夠細節，不需 PDF |
| 是否查詢 EAGLE-3 作為對照 | 1. 需要 2. 不需要 | 不需要 | 使用者未問 EAGLE-3，R1 報告已涵蓋 Medusa 等替代方案 |
