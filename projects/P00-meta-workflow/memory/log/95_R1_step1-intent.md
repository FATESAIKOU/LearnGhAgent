# 95_R1_step1-intent.md

## 狀況理解

使用者（#94 issue）需要建立一個新 project，功能為自動檢查程式碼品質，涵蓋 ESLint、Prettier、TypeScript 型別檢查、測試覆蓋率。agent 角色為「程式碼品質審查員」。這是 R1，意圖單純明確。

## 執行的動作與結果

| 動作 | 目的 | 預期效果 | 實際結果 |
|------|------|----------|----------|
| 讀取 PR body | 確認 project 需求 | 取得 project 名稱、描述、角色 | 成功：ESLint/Prettier/TS/覆蓋率，角色為程式碼品質審查員 |
| 檢查 memory/log/ | 確認無前輪紀錄 | 確認 R1 無需參考前輪 | 目錄僅有 .gitkeep，無前輪紀錄 |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 驗證結果 |
|----------|---------------|----------|
| project_name | 從需求推導：P02-code-quality-check | 合理，符合 P<編號>-<名稱> 格式 |
| project_description | 一句話描述：自動執行 ESLint、Prettier、TypeScript 型別檢查與測試覆蓋率檢查的程式碼品質審查 project | 明確 |
| project_role | 程式碼品質審查員，負責自動化程式碼品質檢查 | 明確 |
| 輪次 | 無既有 log 檔 | 確認為 R1 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|----------|----------|----------|----------|
| project 編號 | P01（已佔用）或 P02 | P02 | P01 已被 general-tech 使用，依序遞增 |
| project 名稱 | code-quality-check / code-reviewer / lint-ts-coverage | code-quality-check | 簡潔且涵蓋所有檢查面向（lint + type + coverage） |
