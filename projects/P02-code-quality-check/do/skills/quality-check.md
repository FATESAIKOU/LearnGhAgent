# quality-check skill

> 本 project（程式碼品質審查）的核心 skill：對給定專案執行結構化品質檢查。

## 可用工具

- `bash`：執行 ESLint、Prettier、TypeScript、測試覆蓋率等命令
- `glob`：尋找專案中的設定檔（`.eslintrc*`、`.prettierrc*`、`tsconfig.json`、`jest.config.*` 等）
- `grep`：搜尋設定檔中的特定規則

## 標準檢查動作

1. **檢查專案設定**
   - 確認專案根目錄是否存在 `package.json`、`.eslintrc*`、`.prettierrc*`、`tsconfig.json`、測試設定檔
   - 若無 `package.json`，檢查是否有其他語言對應的設定（`Cargo.toml`、`build.gradle` 等）

2. **執行 ESLint**
   - `npx eslint . --format json` 或 `npx eslint <target_dir> --format json`
   - 若 ESLint 未安裝，跳過並註記

3. **執行 Prettier**
   - `npx prettier --check .` 或 `npx prettier --check <target_dir>`
   - 若 Prettier 未安裝，跳過並註記

4. **執行 TypeScript 型別檢查**
   - `npx tsc --noEmit` 或 `npx tsc --noEmit --project tsconfig.json`
   - 若 `tsconfig.json` 不存在或 TypeScript 未安裝，跳過並註記

5. **執行測試覆蓋率**
   - 根據測試框架執行：`npx jest --coverage` / `npx vitest --coverage` / `pytest --cov`
   - 若無測試框架設定，跳過並註記

## 注意事項

- 所有命令在專案根目錄執行
- 若命令執行失敗（exit code != 0），仍應收集 stdout/stderr 作為結果
- 覆蓋率閾值預設 80%，低於此值應在報告中標記
