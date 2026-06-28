# 95_R2_step1-intent.md

## 狀況理解

本輪（R2）為 P02-code-quality-check project 的修正輪。使用者回報 R1 產出的 workflow 中 `PROJECT_DIR` 路徑錯誤，要求修正為 `projects/P02-code-quality-check`。無需建立新 project，僅需修正既有 workflow 的 path 變數。

## 執行的動作與結果

| 動作 | 目的 | 結果 |
|------|------|------|
| 解析使用者 feedback | 確認修正需求 | 成功：`PROJECT_DIR` 路徑需修正 |
| 確認 project 範圍 | 判斷是否需新建 project | 不需新建，P02 已存在，僅修正 workflow |

## 動作結束後的現狀

- **project：** P02-code-quality-check（已存在，無變動）
- **待修正檔案：** `.github/workflows/P02-code-quality-check.yml` 內的 `PROJECT_DIR` 變數
- **正確值：** `projects/P02-code-quality-check`

## 其中的決斷點

| 決斷面向 | 選擇 | 理由 |
|----------|------|------|
| 是否新建 project | 否 | 僅需修正既有 workflow 的 path 變數 |
| 修正範圍 | 僅 `PROJECT_DIR` | 使用者明確指出此一問題，其餘無需變動 |
