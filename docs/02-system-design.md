# 02 - 系統要件設計

## 系統組件一覽

| 組件 | 說明 |
|---|---|
| Docker Container | 運行環境，包含所有工具和 Script |
| 主控程式 (`agent_loop.py`) | 常駐 loop，定期輪詢 Issue、依角色分派 Agent |
| 角色分派器 (`role_resolver.py`) | 根據 Issue label 決定用哪個 Agent 角色 |
| Workflow 載入器 (`workflow_loader.py`) | 載入 Workflow YAML、解析階段、處理階段轉換 |
| 認證設定工具 (`setup-auth.sh`) | host 端執行，協助 User 設定 gh 認證情報 |
| gh copilot CLI | Agent 本體，以 `--yolo` 模式執行任務 |
| 狀態檔 (`state.json`) | 記錄每個 Issue 的最後處理時間 |
| 角色 Agent 設定 (`agents/`) | 每個角色一個目錄，包含 instructions 和設定 |
| Workflow 定義 (`workflows/`) | YAML 定義多階段工作流 |

## Docker 映像要件

| 項目 | 規格 |
|---|---|
| Base Image | `ubuntu:24.04` |
| 必裝軟體 | `gh` (GitHub CLI)、`gh copilot` CLI、`jq`、`curl`、`git`、`node` (npm/npx)、`python3-yaml` |
| 工作目錄 | `/workspace` |
| Script 位置 | `/app/` |
| 設定/狀態目錄 | `/data/`（mount volume） |

## Docker Mount 結構

```
Host                              Container                    用途
─────────────────────────────     ──────────────────           ──────────────────
./auth/hosts.yml            →    /auth-src/hosts.yml (ro)     gh 認證情報（entrypoint copy 到可寫位置）
./data/                     →    /data/                        state.json 持久化
./agents/                   →    /app/agents/        (ro)     自訂 Agent 角色定義
./workflows/                →    /app/workflows/     (ro)     Workflow 定義檔
./workspace/                →    /workspace/                   Agent 工作區
```

## 環境變數

| 變數名 | 說明 | 預設值 |
|---|---|---|
| `TARGET_REPO` | 監控的 GitHub repo（`owner/repo`） | **必填** |
| `POLL_INTERVAL` | 輪詢間隔（秒） | `60` |
| `AGENT_TIMEOUT` | Agent 執行超時（秒） | `900`（15 分鐘） |
| `COPILOT_MODEL` | 使用的 AI 模型 | 不指定（用預設） |
| `DEFAULT_ROLE` | 預設 Agent 角色 | `default` |
| `ENABLED_AGENTS` | 啟用的 agent 角色（逗號分隔，空=全部啟用） | 空（全部） |
| `WORKFLOW_FILE` | Workflow YAML 定義檔路徑 | `/app/workflows/default.yml` |

## 角色 Agent 設計

### 目錄結構

```
agents/
├── default/                    # 預設角色
│   ├── instructions.md         # 該角色的 system prompt / instructions
│   └── config.json             # 該角色的特殊設定
├── manager/                    # Manager 角色（需求分析、任務分解）
│   ├── instructions.md
│   └── config.json
├── architect/                  # Architect 角色（系統設計、架構規劃）
│   ├── instructions.md
│   └── config.json
├── coder/                      # Coder 角色（程式實作）
│   ├── instructions.md
│   └── config.json
└── qa/                         # QA 角色（品質驗證、測試）
    ├── instructions.md
    └── config.json
```

### config.json 格式

```json
{
  "model": "",
  "extra_flags": "",
  "allowed_tools": []
}
```

- `model`：空字串表示使用環境變數 `COPILOT_MODEL` 或 gh copilot 預設
- `extra_flags`：傳給 `gh copilot` 的額外旗標
- `allowed_tools`：未來擴展用（限制角色可用工具）

### 角色分派邏輯

- Issue 必須帶有 `role:xxx` label 才會觸發對應角色
- `role:xxx` 中的 `xxx` 必須對應 `agents/` 下的子目錄
- 若設定了 `ENABLED_AGENTS`，只有在清單中的角色會被啟用
- 一個 Issue 同一時間只有一個角色在處理

### Label 系統

| Label 類型 | 格式 | 說明 |
|---|---|---|
| 角色 | `role:xxx` | 指定執行的 Agent 角色（對應 `agents/xxx/`） |
| 工作流 | `workflow:xxx` | 指定使用的 Workflow 定義 |
| 階段 | `phase:xxx` | 指定目前所在的 Workflow 階段 |

### Workflow 系統

Workflow 定義在 YAML 檔案中（預設 `/app/workflows/default.yml`），描述多階段任務的執行順序。

#### Workflow YAML 格式

```yaml
full-development:
  - role: manager
    phasename: requirement-analysis
    phasetarget: "Analyze the issue, clarify requirements."
    llm-model: ""
  - role: architect
    phasename: system-design
    phasetarget: "Design the system architecture."
    llm-model: ""
  - role: coder
    phasename: implementation
    phasetarget: "Implement the design."
    llm-model: ""
  - role: qa
    phasename: verification
    phasetarget: "Verify the implementation."
    llm-model: ""
```

#### Model 優先順序

1. Workflow phase 的 `llm-model`（若非空）
2. 角色 `config.json` 的 `model`（若非空）
3. 環境變數 `COPILOT_MODEL`

#### 自動階段轉換

Agent 完成當前階段後：
1. 移除當前的 `role:xxx` 和 `phase:xxx` label
2. 根據 Workflow 定義，加上下一階段的 `role:xxx` 和 `phase:xxx` label
3. 若已是最後階段，僅移除 label（Workflow 完成）
4. 若 Issue 無 Workflow label，完成後僅移除 `role:xxx` label

## Agent 呼叫方式

```bash
# 讀取角色設定
ROLE_DIR="/app/agents/${ROLE}"
INSTRUCTIONS=$(cat "${ROLE_DIR}/instructions.md")
CONFIG="${ROLE_DIR}/config.json"

# 從 config.json 讀取 model（若有）
MODEL=$(jq -r '.model // empty' "${CONFIG}")
EXTRA_FLAGS=$(jq -r '.extra_flags // empty' "${CONFIG}")

# 組合 prompt
PROMPT="${INSTRUCTIONS}\n\n---\n\n以下是 Issue #${ISSUE_NUMBER} 的完整對話內容：\n${ISSUE_CONTENT}"

# 組合指令
CMD="gh copilot -p \"${PROMPT}\" --yolo -s --no-ask-user --add-dir /workspace"
[ -n "${MODEL}" ] && CMD="${CMD} --model ${MODEL}"
[ -n "${EXTRA_FLAGS}" ] && CMD="${CMD} ${EXTRA_FLAGS}"

# 帶超時執行
timeout ${AGENT_TIMEOUT} bash -c "${CMD}"
```

## 主控 Script 流程

```
Loop:
  1. gh issue list --repo $TARGET_REPO --state open --json number,labels,updatedAt
  2. 對每個 Issue:
     a. 取最新 comment 時間
        → gh api repos/{owner}/{repo}/issues/{n}/comments --jq '.[].created_at' | sort | tail -1
     b. 比對 state.json 中的 last_processed_at
     c. 若 last_processed_at >= 最新 comment 時間 → skip
     d. 否則：
        i.   決定角色：從 Issue labels 找 "role:xxx"，沒有就用 DEFAULT_ROLE
        ii.  取 Issue body + 所有 comments → 組成對話內容
        iii. 讀取角色 instructions.md → 前置到 prompt
        iv.  timeout $AGENT_TIMEOUT gh copilot -p "<prompt>" --yolo -s --no-ask-user
        v.   若超時（exit code 124）→ 不回寫
        vi.  若正常完成 → 取 stdout 作為總結，gh issue comment 回寫
        vii. 更新 state.json 中該 Issue 的 last_processed_at = 當前時間
  3. sleep $POLL_INTERVAL
```

## 認證設定工具

### 流程

```
setup-auth.sh:
  1. 檢查 host 上是否已安裝 gh CLI
  2. 若未登入，執行 gh auth login
  3. 用 gh auth token 取得 token，產生含 oauth_token 的 hosts.yml
     （macOS 的 token 存在 Keychain，無法直接複製 hosts.yml）
  4. hosts.yml 必須使用舊版單帳號格式（非 multi-user users: 格式）
  5. 驗證認證是否有效
  6. 提示完成
```

### 所需認證檔案

```
auth/
└── hosts.yml       # gh 的認證 token 資訊（含 oauth_token 欄位）
```

#### hosts.yml 格式（舊版單帳號格式）

```yaml
github.com:
    oauth_token: gho_xxxxxxxxxxxxxxxxxxxx
    git_protocol: https
    user: USERNAME
```

## 狀態檔格式

### state.json

```json
{
  "issues": {
    "1": {
      "last_processed_at": "2026-03-07T12:00:00Z"
    },
    "42": {
      "last_processed_at": "2026-03-07T11:30:00Z"
    }
  }
}
```

## 安全考量

- 認證檔案（`./auth/hosts.yml`）以 **read-only** mount 進容器（`/auth-src/hosts.yml:ro`），entrypoint 再 copy 到可寫位置
- Agent 定義目錄（`./agents/`）以 **read-only** mount
- Agent 檔案操作範圍限制在 `/workspace`（`--add-dir /workspace`）
- 超時強制 kill 防止 Agent 失控
- state.json 以 volume mount 持久化，容器重啟不遺失
- `./auth/` 應加入 `.gitignore`

## 專案檔案結構

```
LearnGhAgent/
├── Dockerfile
├── docker-compose.yml
├── .gitignore
├── docs/
│   ├── 01-requirements.md       # 需求定義
│   ├── 02-system-design.md      # 系統要件設計（本文件）
│   ├── 03-basic-design.md       # 系統基本設計
│   ├── 04-poc-validation.md     # PoC 驗證報告
│   └── 05-design-adjustments.md # 設計調整報告
├── scripts/
│   ├── agent_loop.py            # 主控程式 (Python)
│   ├── config.py                # 環境變數讀取、設定管理
│   ├── github_client.py         # GitHub API 封裝（含 label 操作）
│   ├── state_manager.py         # state.json 讀寫
│   ├── role_resolver.py         # 角色分派邏輯（label 解析）
│   ├── prompt_builder.py        # Prompt 組合（含 workflow context）
│   ├── agent_runner.py          # gh copilot 子程序管理（JSONL streaming）
│   ├── workflow_loader.py       # Workflow YAML 載入與階段轉換
│   ├── setup-auth.sh            # 認證設定工具（host 端執行）
│   └── entrypoint.sh            # Docker entrypoint（含 auto-clone）
├── agents/                      # 角色 Agent 定義
│   ├── default/
│   │   ├── instructions.md
│   │   └── config.json
│   ├── manager/
│   │   ├── instructions.md
│   │   └── config.json
│   ├── architect/
│   │   ├── instructions.md
│   │   └── config.json
│   ├── coder/
│   │   ├── instructions.md
│   │   └── config.json
│   └── qa/
│       ├── instructions.md
│       └── config.json
├── workflows/                   # Workflow 定義
│   └── default.yml              # 預設 Workflow（full-development, quick-fix）
├── auth/                        # gh 認證情報（gitignore）
├── data/                        # 持久化狀態
│   └── state.json
└── workspace/                   # Agent 工作區
```
