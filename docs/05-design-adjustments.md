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
- **gh copilot 呼叫方式**：`gh copilot -p "..." --yolo --no-ask-user --output-format json` 確認可用
- **agents/ 角色目錄結構**：無變更
- **日誌設計**：無變更
- **元件互動序列圖**：流程不變（僅 entrypoint 內部多了 auth copy，不影響序列）

---

## 調整二：Workflow 多階段系統（觸發規則改版）

### 調整背景

原設計僅使用 `role:xxx` label 作為簡單的角色分派，完成後需手動管理 label。為支援多角色自動串接的工作流程，進行以下大幅重構。

### 調整一覽

| # | 調整項目 | 原設計 | 修正內容 |
|---|---------|--------|---------|
| 1 | 觸發條件 | 任何 open issue、無 role label 用 DEFAULT_ROLE | 必須有 `role:xxx` label 才觸發，且 `xxx` 對應 `agents/` 子目錄 |
| 2 | 角色啟用 | 所有角色都啟用 | 新增 `ENABLED_AGENTS` 環境變數，可限制只啟用部分角色 |
| 3 | 預設角色 | default, manager/architect/coder/qa 為「未來」 | 4 個角色全部實作：manager, architect, coder, qa |
| 4 | 完成後行為 | 不管理 label | 自動移除當前 `role:xxx` + `phase:xxx`，加上下一階段的 label |
| 5 | Workflow 系統 | 無 | 新增 Workflow YAML 定義檔，支援多階段任務串接 |
| 6 | Model 優先順序 | `config.json` > `COPILOT_MODEL` | Workflow phase `llm-model` > `COPILOT_MODEL`（移除 config.json） |
| 7 | Agent 設定 | `config.json`（model, extra_flags） | 移除 `config.json`，model/flags 集中在 Workflow YAML |
| 8 | Docker 映像 | 無 python3-yaml | 新增 `python3-yaml` 到 apt install |
| 9 | Volume mount | 無 workflows | 新增 `./workflows:/app/workflows:ro` |
| 10 | 觸發機制 | 時間戳比對判斷是否有新進度 | 改為 `role:xxx` label 存在即處理，移除 state.json 和時間戳比對 |

### 新增/修改的檔案

| 檔案 | 變更類型 | 說明 |
|------|---------|------|
| `scripts/workflow_loader.py` | 新增 | Workflow YAML 解析、Phase/Workflow dataclass（含 extra_flags）、階段查詢與轉換 |
| `scripts/role_resolver.py` | 重寫 | ResolvedLabels dataclass、解析 `role:`/`workflow:`/`phase:` label、agents_dir 驗證、enabled_agents 過濾 |
| `scripts/agent_loop.py` | 重寫 | process_issue() 整合 workflow、model 優先順序、_advance_workflow() 自動轉換、純 label 觸發（無 state） |
| `scripts/state_manager.py` | 刪除 | state.json 與時間戳機制已全部移除 |
| `scripts/agent_runner.py` | 修改 | 移除 config.json 讀取，改由參數傳入 model 和 extra_flags |
| `scripts/github_client.py` | 新增函式 | `add_label()`, `remove_label()` |
| `scripts/prompt_builder.py` | 修改 | 新增 `extra_context` 參數（插入 workflow phase 資訊） |
| `scripts/config.py` | 修改 | 新增 `enabled_agents`, `workflow_file` 欄位 |
| `docker-compose.yml` | 修改 | 新增 `ENABLED_AGENTS`, `WORKFLOW_FILE` 環境變數、`workflows` volume |
| `Dockerfile` | 修改 | apt install 新增 `python3-yaml` |
| `agents/manager/` | 新增 | Manager 角色（僅 instructions.md，無 config.json） |
| `agents/architect/` | 新增 | Architect 角色（僅 instructions.md） |
| `agents/coder/` | 新增 | Coder 角色（僅 instructions.md） |
| `agents/qa/` | 新增 | QA 角色（僅 instructions.md） |
| `agents/default/config.json` | 刪除 | config.json 已移除，設定集中在 Workflow YAML |
| `workflows/default.yml` | 新增 | 預設 Workflow 定義（full-development, quick-fix） |

### Label 系統

```
role:xxx       → 指定執行的 Agent 角色（必須對應 agents/xxx/ 目錄）
workflow:xxx   → 指定使用的 Workflow 定義（對應 YAML 中的 key）
phase:xxx      → 指定目前所在的 Workflow 階段（對應 YAML 中的 phasename）
```

### Workflow 自動轉換流程

```
Issue labels: [role:manager, workflow:full-development, phase:requirement-analysis]
  → Agent 執行 manager 角色
  → 完成後：
     移除 role:manager, phase:requirement-analysis
     加上 role:architect, phase:system-design
  → 下次輪詢時：
     Agent 執行 architect 角色
  → 完成後：
     移除 role:architect, phase:system-design
     加上 role:coder, phase:implementation
  → ... 直到最後一個階段完成
```

---

## 調整三：State 移除與其他修正

### 調整背景

觸發機制簡化為純 label 存在即處理，移除 state.json 與時間戳比對邏輯。同時修正 Dockerfile 在 Linux x86_64 的架構偵測問題，以及 Workflow 無 phase label 時的自動推斷。

### 調整一覽

| # | 調整項目 | 原設計 | 修正內容 |
|---|---------|--------|---------|
| 1 | 觸發機制 | 比對 `last_processed_at` 與最新 comment 時間 | 改為 `role:xxx` label 存在即處理，完成後移除 label |
| 2 | state.json | 持久化每個 Issue 的處理時間 | 完全移除（檔案、StateManager、volume mount） |
| 3 | state_manager.py | 管理 state.json 讀寫 | 刪除整個檔案 |
| 4 | github_client.py | 包含 `get_latest_activity_time()` | 移除該函式 |
| 5 | config.py | 包含 `state_file` 欄位 | 移除該欄位 |
| 6 | docker-compose.yml | `./data:/data` volume mount | 移除 data volume；移除 `version: "3.8"` |
| 7 | entrypoint.sh | 初始化 state.json | 移除初始化邏輯，改為 auto-clone TARGET_REPO |
| 8 | Dockerfile 架構偵測 | 寫死 `copilot-linux-arm64.tar.gz` | 改用 `dpkg --print-architecture` 自動偵測，`amd64` 映射為 `x64` |
| 9 | Phase 自動推斷 | 必須手動加 `phase:xxx` label | 若有 `workflow:xxx` 但無 `phase:xxx`，自動採用第一階段並加上 label |
| 10 | .gitignore | 包含 `data/state.json` | 移除該行 |

### 影響範圍

- **scripts/agent_loop.py**：移除 state 相關 import 與邏輯，觸發條件改為 label 檢查
- **scripts/state_manager.py**：刪除
- **scripts/github_client.py**：移除 `get_latest_activity_time()`
- **scripts/config.py**：移除 `state_file`
- **scripts/entrypoint.sh**：移除 state.json 初始化，新增 auto-clone
- **Dockerfile**：架構自動偵測，新增 `python3-pip python3-yaml`、`chmod +x`
- **docker-compose.yml**：移除 `version`、移除 data volume
- **.gitignore**：移除 `data/state.json`
- **README.md**：流程圖從 8 步簡化為 6 步
