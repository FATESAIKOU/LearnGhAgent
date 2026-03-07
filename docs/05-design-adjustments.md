# 05 - 基本設計調整報告

## 調整背景

根據 Step 4（PoC 驗證）的結果，基本設計（03）與系統設計（02）中有數處假設與實際行為不符，需要修正。

## 調整一覽

| # | 調整項目 | 原設計 | PoC 發現 | 修正內容 |
|---|---------|--------|---------|---------|
| 1 | Dockerfile copilot 安裝 | `gh copilot -- --version \|\| true`（runtime 安裝） | 互動式 TTY 提示無法在 container 自動化 | 改為 build time 從 `github/copilot-cli` repo curl 下載 |
| 2 | Dockerfile 系統套件 | 無 `python3` | agent_loop.py 需要 Python | 加入 `python3` |
| 3 | Auth mount 方式 | `./auth:/root/.config/gh:ro` | gh CLI config migration 需寫入，ro mount 會失敗 | 改為 `./auth/hosts.yml:/auth-src/hosts.yml:ro`，entrypoint copy 到可寫位置 |
| 4 | hosts.yml 格式 | 直接複製 `~/.config/gh/hosts.yml` | macOS token 在 Keychain，hosts.yml 無 token；且需舊版單帳號格式 | setup-auth.sh 改用 `gh auth token` 取得 token 自行產生 |
| 5 | entrypoint.sh | 直接驗證 auth | 需先從 ro mount copy auth 到可寫位置 | 新增 auth copy 邏輯 |
| 6 | entrypoint.sh copilot 驗證 | 失敗時自動安裝 (`echo "y" \| gh copilot`) | 不可靠，copilot 已在 build time 安裝 | 改為僅驗證，失敗直接報錯退出 |
| 7 | setup-auth.sh | 提供互動式 login 或 paste token 兩種選擇 | macOS 無法直接複製 hosts.yml | 簡化為：確認已登入 → `gh auth token` 取 token → 產生 hosts.yml |
| 8 | 錯誤處理表 | 「gh copilot 未安裝 → entrypoint 自動安裝」 | build time 已處理 | 改為「entrypoint 報錯退出」 |

## 影響範圍

### 02-system-design.md

- **Docker Mount 結構**：auth 路徑從 `./auth/ → /root/.config/gh/ (ro)` 改為 `./auth/hosts.yml → /auth-src/hosts.yml (ro)`
- **認證設定工具流程**：6 步驟重寫（加入 token 取得、格式說明）
- **所需認證檔案**：移除 `config.yml`，新增 hosts.yml 格式範例
- **安全考量**：auth mount 說明加入「entrypoint copy 到可寫位置」
- **專案檔案結構**：docs/ 新增 03、04

### 03-basic-design.md

- **Section 1 Dockerfile**：全面重寫（加 python3、curl 下載 copilot、移除 `|| true`）
- **Section 2 docker-compose.yml**：volumes auth 行更新
- **Section 3 entrypoint.sh**：新增 auth copy 邏輯、copilot 改為僅驗證
- **Section 5 setup-auth.sh**：職責說明、流程、虛擬碼全面重寫
- **Section 8 錯誤處理表**：copilot 未安裝的處理方式更新

## 未調整項目

以下項目經 PoC 驗證後確認與原設計一致，無需調整：

- **agent_loop.py 主迴圈邏輯**：Python subprocess + timeout 方式如設計所述
- **gh copilot 呼叫方式**：`gh copilot -p "..." --yolo -s --no-ask-user` 確認可用
- **state.json 格式**：無變更
- **agents/ 角色目錄結構**：無變更
- **日誌設計**：無變更
- **元件互動序列圖**：流程不變（僅 entrypoint 內部多了 auth copy，不影響序列）
