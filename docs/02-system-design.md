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
| 角色 Agent 設定 (`agents/`) | 每個角色一個目錄，包含 instructions |
| Workflow 定義 (`workflows/`) | YAML 定義多階段工作流 |

## Docker 映像要件

| 項目 | 規格 |
|---|---|
| Base Image | `ubuntu:24.04` |
| 必裝軟體 | `gh` (GitHub CLI)、`gh copilot` CLI、`jq`、`curl`、`git`、`node` (npm/npx)、`python3`、`python3-yaml` |
| 工作目錄 | `/workspace` |
| Script 位置 | `/app/` |

## Docker Mount 結構

```
Host                              Container                    用途
─────────────────────────────     ──────────────────           ──────────────────
./auth/hosts.yml            →    /auth-src/hosts.yml (ro)     gh 認證情報（entrypoint copy 到可寫位置）
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
│   └── instructions.md         # 該角色的 system prompt / instructions
├── manager/                    # Manager 角色（需求分析、任務分解）
│   └── instructions.md
├── architect/                  # Architect 角色（系統設計、架構規劃）
│   └── instructions.md
├── coder/                      # Coder 角色（程式實作）
│   └── instructions.md
└── qa/                         # QA 角色（品質驗證、測試）
    └── instructions.md
```

Agent 目錄只包含 `instructions.md`，model 和 extra flags 等啟動設定集中在 Workflow YAML 中管理。

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
    extra-flags: ""
  - role: architect
    phasename: system-design
    phasetarget: "Design the system architecture."
    llm-model: ""
    extra-flags: ""
  - role: coder
    phasename: implementation
    phasetarget: "Implement the design."
    llm-model: ""
    extra-flags: ""
  - role: qa
    phasename: verification
    phasetarget: "Verify the implementation."
    llm-model: ""
    extra-flags: ""
```

- `llm-model`：指定該階段使用的 LLM 模型（空字串 = 使用 `COPILOT_MODEL` 環境變數）
- `extra-flags`：傳給 `gh copilot` 的額外旗標（空字串 = 無額外旗標）

#### Model 優先順序

1. Workflow phase 的 `llm-model`（若非空）
2. 環境變數 `COPILOT_MODEL`

#### 自動階段轉換

Agent 完成當前階段後：
1. 移除當前的 `role:xxx` 和 `phase:xxx` label
2. 根據 Workflow 定義，加上下一階段的 `role:xxx` 和 `phase:xxx` label
3. 下次輪詢時自動偵測到新的 `role:xxx` label 並執行
4. 若已是最後階段，僅移除 label（Workflow 完成）
5. 若 Issue 無 Workflow label，完成後僅移除 `role:xxx` label
6. 若有 `workflow:xxx` 但無 `phase:xxx`，自動採用 Workflow 第一階段

> **觸發機制**：以 `role:xxx` label 存在與否作為處理依據，無需時間戳比對。Agent 完成後會移除 label，因此下次輪詢不會重複處理。

## Agent 呼叫方式

```bash
# 讀取角色 instructions
ROLE_DIR="/app/agents/${ROLE}"
INSTRUCTIONS=$(cat "${ROLE_DIR}/instructions.md")

# Model 和 extra flags 從 Workflow YAML 取得（由 Python 程式處理）
# 組合 prompt
PROMPT="${INSTRUCTIONS}\n\n---\n\n以下是 Issue #${ISSUE_NUMBER} 的完整對話內容：\n${ISSUE_CONTENT}"

# 組合指令
CMD="gh copilot -p \"${PROMPT}\" --yolo --no-ask-user --add-dir /workspace"
[ -n "${MODEL}" ] && CMD="${CMD} --model ${MODEL}"
[ -n "${EXTRA_FLAGS}" ] && CMD="${CMD} ${EXTRA_FLAGS}"

# 帶超時執行
timeout ${AGENT_TIMEOUT} bash -c "${CMD}"
```

## 主控 Script 流程

```
Loop:
  1. gh issue list --repo $TARGET_REPO --state open --json number,labels
  2. 對每個 Issue:
     a. 解析 labels：取得 role:xxx / workflow:xxx / phase:xxx
     b. 若無 role:xxx label → skip
     c. 若 role 不在 ENABLED_AGENTS 中 → skip
     d. 若有 workflow:xxx：
        - 有 phase:xxx → 查找對應階段
        - 無 phase:xxx → 自動採用第一階段，補上 phase label
     e. 取 Issue body + 所有 comments → 組成對話內容
     f. 讀取角色 instructions.md + workflow context → 組合 prompt
     g. timeout $AGENT_TIMEOUT gh copilot -p "<prompt>" --yolo --no-ask-user --output-format json
     h. 若超時 → 不回寫
     i. 若正常完成 → 取 stdout 作為總結，gh issue comment 回寫
     j. Workflow 階段轉換：移除當前 role/phase label，加上下一階段 label
     k. 若無 Workflow：僅移除 role label
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

## 安全考量

- 認證檔案（`./auth/hosts.yml`）以 **read-only** mount 進容器（`/auth-src/hosts.yml:ro`），entrypoint 再 copy 到可寫位置
- Agent 定義目錄（`./agents/`）以 **read-only** mount
- Agent 檔案操作範圍限制在 `/workspace`（`--add-dir /workspace`）
- 超時強制 kill 防止 Agent 失控
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
│   ├── role_resolver.py         # 角色分派邏輯（label 解析）
│   ├── prompt_builder.py        # Prompt 組合（含 workflow context）
│   ├── agent_runner.py          # gh copilot 子程序管理（JSONL streaming）
│   ├── workflow_loader.py       # Workflow YAML 載入與階段轉換
│   ├── setup-auth.sh            # 認證設定工具（host 端執行）
│   └── entrypoint.sh            # Docker entrypoint（含 auto-clone）
├── agents/                      # 角色 Agent 定義
│   ├── default/
│   │   └── instructions.md
│   ├── manager/
│   │   └── instructions.md
│   ├── architect/
│   │   └── instructions.md
│   ├── coder/
│   │   └── instructions.md
│   └── qa/
│       └── instructions.md
├── workflows/                   # Workflow 定義
│   └── default.yml              # 預設 Workflow（full-development, quick-fix）
├── auth/                        # gh 認證情報（gitignore）
└── workspace/                   # Agent 工作區
```
