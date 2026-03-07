# 02 - 系統要件設計

## 系統組件一覽

| 組件 | 說明 |
|---|---|
| Docker Container | 運行環境，包含所有工具和 Script |
| 主控 Script (`agent-loop.sh`) | 常駐 loop，定期輪詢 Issue、依角色分派 Agent |
| 角色分派器（dispatcher 邏輯） | 根據 Issue label 決定用哪個 Agent 角色 |
| 認證設定工具 (`setup-auth.sh`) | host 端執行，協助 User 設定 gh 認證情報 |
| gh copilot CLI | Agent 本體，以 `--yolo` 模式執行任務 |
| 狀態檔 (`state.json`) | 記錄每個 Issue 的最後處理時間 |
| 角色 Agent 設定 (`agents/`) | 每個角色一個目錄，包含 instructions 和設定 |

## Docker 映像要件

| 項目 | 規格 |
|---|---|
| Base Image | `ubuntu:24.04` |
| 必裝軟體 | `gh` (GitHub CLI)、`gh copilot` CLI、`jq`、`curl`、`git`、`node` (npm/npx) |
| 工作目錄 | `/workspace` |
| Script 位置 | `/app/` |
| 設定/狀態目錄 | `/data/`（mount volume） |

## Docker Mount 結構

```
Host                              Container                    用途
─────────────────────────────     ──────────────────           ──────────────────
./auth/                     →    /root/.config/gh/   (ro)     gh 認證情報
./data/                     →    /data/                        state.json 持久化
./agents/                   →    /app/agents/        (ro)     自訂 Agent 角色定義
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

## 角色 Agent 設計

### 目錄結構

```
agents/
├── default/                    # 預設角色（v1 唯一角色）
│   ├── instructions.md         # 該角色的 system prompt / instructions
│   └── config.json             # 該角色的特殊設定（可選：model、tools 等）
├── manager/                    # 未來：Manager 角色
│   ├── instructions.md
│   └── config.json
├── architect/                  # 未來：Architect 角色
│   ├── instructions.md
│   └── config.json
├── coder/                      # 未來：Coder 角色
│   ├── instructions.md
│   └── config.json
└── qa/                         # 未來：QA 角色
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

- **v1（目前）**：所有 Issue 使用 `default` 角色
- **v2（未來）**：根據 Issue 的 label 分派
  - `role:manager` → `manager` 角色
  - `role:architect` → `architect` 角色
  - `role:coder` → `coder` 角色
  - `role:qa` → `qa` 角色
  - 無 role label → 使用 `DEFAULT_ROLE`
- **限制**：一個 Issue 同一時間只有一個角色在處理

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
  2. 執行 gh auth login（或讓 User 以 token 方式設定）
  3. 將 ~/.config/gh/ 下的認證檔案複製到 ./auth/
  4. 驗證認證是否有效（gh auth status）
  5. 提示完成
```

### 所需認證檔案

```
auth/
├── hosts.yml       # gh 的認證 token 資訊
└── config.yml      # gh 的基本設定（可選）
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

- 認證目錄（`./auth/`）以 **read-only** mount 進容器
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
│   └── 02-system-design.md      # 系統要件設計（本文件）
├── scripts/
│   ├── agent-loop.sh            # 主控 loop Script
│   ├── setup-auth.sh            # 認證設定工具（host 端執行）
│   └── entrypoint.sh            # Docker entrypoint
├── agents/                      # 角色 Agent 定義
│   └── default/
│       ├── instructions.md
│       └── config.json
├── auth/                        # gh 認證情報（gitignore）
├── data/                        # 持久化狀態
│   └── state.json
└── workspace/                   # Agent 工作區
```
