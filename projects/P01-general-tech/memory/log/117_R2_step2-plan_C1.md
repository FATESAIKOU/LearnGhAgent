# 117_R2_step2-plan_C1.md

## 狀況理解

R2 使用者提出 3 個具體追問：
- **Q1**：DeepSpec 與 DFlash 的關係 — 是否為 DFlash 的 wrapping？
- **Q2**：DeepSpec 是「可直接使用的套件」還是「演算法」？
- **Q3**：若是套件，如何使用？

Step 2 C1 的任務：取得 repo metadata、README、關鍵子文件，並對照 106 報告，為 Q1-Q3 建立事實基礎。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view deepseek-ai/DeepSpec --json ...` | 取得 repo metadata | 確認 stars, license, language, 描述 | 6079 stars, MIT, Python, 描述為「full-stack codebase for training/evaluating draft models for speculative decoding」 |
| `gh api repos/.../readme` → base64 decode | 擷取 README.md 全文 | 了解 workflow、演算法、使用方式 | 取得完整 README：3 階段 workflow（Data Prep → Training → Evaluation）、3 種演算法（DSpark/DFlash/Eagle3）、released checkpoints |
| `gh api repos/.../contents` | 列出 repo 根目錄結構 | 確認是否有 setup.py/pyproject.toml | 無 setup.py/pyproject.toml；有 config/、deepspec/、scripts/、eval_datasets/ |
| `gh api repos/.../contents/scripts/data/README.md` | 擷取 data preparation 子文件 | 了解資料準備的詳細步驟 | 3-step pipeline：download → regenerate answers (SGLang) → build target cache（~38TB） |
| `gh api repos/.../contents/requirements.txt` | 檢查依賴管理方式 | 確認是否為 pip package | 純 requirements.txt，無 package metadata |
| `gh api repos/.../contents/deepspec/__init__.py` | 檢查 Python package 結構 | 確認是否為可 import 的套件 | `__all__ = []`，空 package，非設計為 pip install 使用 |
| 讀取 106_dflash-speculative-decoding-mtp.md | 對照既有 DFlash 報告 | 確認 DFlash 在既有分析中的定位 | 106 報告明確指出 DFlash 是 speculative decoding 框架下的一種實作方案（sibling of MTP） |
| 讀取 117_DeepSpec.md §3 | 回顧 R1 報告中 DeepSpec 架構 | 確認 DeepSpec 與 DFlash 的關係描述 | §3.3 指出 DFlash 是 DeepSpec 支援的三種演算法之一 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Q1 事實基礎 | DeepSpec 與 DFlash 的關係 | DeepSpec 是**框架**（training/evaluation codebase），DFlash 是**框架內的一種演算法**。不存在「DFlash 的 wrapping」關係。 |
| Q2 事實基礎 | 是否為 pip-installable 套件 | **否**。無 setup.py/pyproject.toml，`deepspec/__init__.py` 為空，無法 `pip install`。DeepSpec 是**需 clone 後直接執行 script 的 codebase**。 |
| Q3 事實基礎 | 使用方式 | 使用方式為：clone repo → `pip install -r requirements.txt` → 依序執行 `scripts/data/`、`scripts/train/train.sh`、`scripts/eval/eval.sh`。非 `import deepspec` 的 library 用法。 |
| 106 報告對照 | DFlash 在既有分析中的定位 | 106 報告 §3 Q1 已建立「speculative decoding 為上層框架，DFlash 與 MTP 為 sibling 實作」的架構。DeepSpec 是這個架構的**訓練/評估基礎設施**，不是 DFlash 的 wrapper。 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| Q1 回答策略 | (a) 僅引用 117 報告 (b) 同時引用 106 報告建立對照 | 同時引用兩份報告 | 使用者明確參照 106 報告，需建立「DeepSpec 框架 vs DFlash 演算法」的層級關係 |
| Q2 判斷依據 | (a) 僅看 README 描述 (b) 檢查 package 結構 | 檢查 package 結構 | README 未明確說是否可 pip install，需從 setup.py/pyproject.toml/__init__.py 的實際存在與否判斷 |
| 資訊呈現方式 | (a) 直接回答 (b) 先給事實再給結論 | 先給事實再給結論 | 使用者偏好可驗證的結構化資訊，需讓使用者能自行驗證判斷依據 |
