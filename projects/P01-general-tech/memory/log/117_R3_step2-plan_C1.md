# 117_R3_step2-plan_C1.md

## 狀況理解

R3 使用者追問：DeepSpec 的 training script 是訓練 LLM 本體（主模型），還是訓練 speculative decoding 用的 submodel（草稿模型）？本 sub-step 從 repo 原始資料確認訓練目標。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view deepseek-ai/DeepSpec --json ...` | 取得 repo metadata | 確認描述、語言、star 數 | Python 為主，6091 stars，描述明確寫 "training and evaluating draft models" |
| `gh api .../readme` + base64 decode | 取得 README.md 全文 | 確認 workflow 與 training 說明 | README 開頭即寫 "training and evaluating **draft models** for speculative decoding" |
| `gh api .../contents` 列出根目錄 | 確認 repo 結構 | 了解目錄布局 | 含 `config/`（dflash/dspark/eagle3）、`deepspec/`（modeling/trainer）、`train.py`、`scripts/train/train.sh` |
| 讀取 `train.py` | 確認 training entry point | 了解訓練流程 | 載入 config → 初始化 trainer → `trainer.train()` |
| 讀取 `scripts/train/train.sh` | 確認預設執行方式 | 了解 config 路徑與參數 | 預設指向 `config/dspark/dspark_qwen3_4b.py`，config 可透過 `--opts` 覆蓋 |
| 讀取 `config/dflash/dflash_qwen3_4b.py` | 確認 config 結構 | 了解訓練對象的模型架構參數 | config 的 `model` 區塊含 `target_model_name_or_path`（主模型）、`block_size`、`num_draft_layers`、`target_layer_ids`——這些是 draft model 架構參數，非主模型參數 |
| 列出 `deepspec/modeling/` 與 `deepspec/trainer/` | 確認實作結構 | 了解 draft model 實作 | `modeling/` 下只有 `dspark/` 與 `eagle3/`（draft model 實作）；`trainer/` 下有 `dspark_trainer.py`、`eagle3_trainer.py` |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| README 對訓練目標的陳述 | 搜尋 "draft model" 關鍵字 | 明確：DeepSpec 是 "training and evaluating draft models for speculative decoding" |
| config 中 model 參數的語意 | 讀取 `config/dflash/dflash_qwen3_4b.py` | `target_model_name_or_path` 指向主模型（Qwen/Qwen3-4B），其餘參數（`block_size`, `num_draft_layers`, `target_layer_ids`）定義 draft model 結構 |
| 已釋出 checkpoint 的性質 | README "Released Checkpoints" 表格 | 所有 checkpoint 皆為 draft model（如 `deepseek-ai/dflash_qwen3_4b_block7`），非主模型 |
| workflow 順序 | README "Workflow" 段落 | Data Preparation → **Training (draft model)** → Evaluation，主模型僅作為 target 被調用（inference），不被訓練 |

**結論：DeepSpec 的 training script 訓練的是 speculative decoding 用的 draft model（草稿模型），不是 LLM 本體（主模型）。** 主模型（如 Qwen3-4B）在 pipeline 中僅作為 frozen target，用於產生 target cache（推理輸出），draft model 則學習擬合這些輸出。

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研範圍 | 僅讀 README / 深入 config + source code | 深入 config + source code | 使用者問題需要 config 層級證據才能確證訓練對象 |
| 是否讀取 paper PDF | 是 / 否 | 否 | README + config 已提供足夠證據，paper 為演算法細節，與訓練對象問題無關 |
