# 117_R1_step2-plan_C1.md

## 狀況理解

Step 1 確認技術標的為 DeepSpec（deepseek-ai/DeepSpec），一個 speculative decoding 的訓練與評估框架。C1 任務為取得 repo metadata、README、關鍵子文件，並補查背景脈絡。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh api repos/deepseek-ai/DeepSpec` | 取得 repo metadata | 獲得 stars/forks/license 等 | stars=6078, forks=512, MIT, Python, 2026-06-26 建立 |
| `gh api .../readme` | 取得 README.md | 理解專案全貌 | 確認 3 演算法（DSpark/DFlash/Eagle3）、3 階段工作流（Data→Train→Eval） |
| `gh api .../contents/` | 列出根目錄結構 | 了解專案組織 | config/, deepspec/, scripts/, eval_datasets/, train.py, eval.py |
| 遞迴讀取 config/ 下各演算法配置 | 取得訓練超參數 | 理解各演算法設定 | DSpark: block_size=7, num_anchors=512, markov_rank=256, ce_loss_alpha=0.1, l1_loss_alpha=0.9 |
| 讀取 deepspec/modeling/dspark/common.py | 理解 DSpark 核心機制 | 掌握 anchor sampling / attention mask | 確認 anchor 取樣策略、flex attention mask、eval mask 累積邏輯 |
| 讀取 deepspec/modeling/dspark/markov_head.py | 理解 Markov head 設計 | 掌握 draft head 架構 | 3 種 head: Vanilla/Gated/RNN，支援 block-level 自迴歸取樣 |
| 讀取 deepspec/modeling/dspark/loss.py | 理解 DSpark loss | 掌握訓練目標 | CE loss + L1 distribution matching + confidence head BCE |
| 讀取 deepspec/modeling/eagle3/common.py | 理解 Eagle3 核心機制 | 掌握 flex attention / TTT | Eagle3 v1 使用 5 層 target features，flex attention 編譯最佳化 |
| 讀取 deepspec/modeling/eagle3/loss.py | 理解 Eagle3 loss | 掌握 TTT 蒸餾 | Triton fused soft cross-entropy，逐 step 衰減權重，local_mean 歸一化 |
| 讀取 deepspec/trainer/base_trainer.py | 理解訓練框架 | 掌握 FSDP / checkpoint | FSDP (full/hybrid/no_shard)、BF16Optimizer、suspend/resume |
| 讀取 scripts/data/README.md | 理解資料管線 | 掌握 data pipeline | 3 步驟: download→regen→cache，target cache 約 38TB |
| 讀取 requirements.txt | 理解依賴 | 掌握技術棧 | torch 2.9.1, transformers 5.10.2, triton 3.5.1, datasets, openai |
| 讀取 config/dspark/dspark_qwen3_4b.py | 理解預設配置 | 掌握訓練參數 | lr=6e-4, global_batch_size=512, bf16, no_shard FSDP, torch_compile |
| 搜尋 DFlash 論文 (arxiv 2602.06036) | 補查背景 | 理解 DFlash 原理 | Block diffusion model, 6x speedup, ICML 2026 |
| 搜尋 Eagle3 論文 (arxiv 2503.01840) | 補查背景 | 理解 Eagle3 原理 | Direct token prediction + TTT, 6.5x speedup |
| 搜尋 DSpark 論文 (repo 內 PDF) | 補查背景 | 理解 DSpark 原理 | repo 內含 DSpark_paper.pdf，待 C2 深入 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Repo 可存取性 | `gh api` 回傳正常 | 可正常存取，非 fork，活躍更新 |
| 文件完整性 | 比對 README 目錄與實際 API 回傳 | 一致，無遺漏關鍵目錄 |
| 演算法覆蓋 | 確認 3 種演算法皆有對應目錄與實作 | DSpark/DFlash/Eagle3 皆有完整 modeling/trainer/eval 程式碼 |
| 背景資料 | 論文摘要可取得 | DFlash/Eagle3 論文摘要已取得，DSpark PDF 待讀 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件讀取深度 | 只讀 README / 讀到 source code 層級 | 讀到 source code 層級 | 報告需描述「如何解決問題」，需理解核心機制 |
| 背景查詢範圍 | 只查 repo 內文件 / 查論文摘要 | 查論文摘要 | README 對演算法原理說明不足，需論文補足 |
| C2 方向 | 深入 DSpark PDF / 查 speculative decoding 背景 / 查替代方案 | 三者皆需 | 報告 §2 需背景、§3 需機制、§4 需替代方案 |
