# 02 - 系統要件設計

## 架構概覽

本系統採用 **Hexagonal Architecture（Ports & Adapters）** 設計，將程式碼分為四層：

```
┌─────────────────────────────────────────────────┐
│  main.py (Composition Root + Inbound Adapter)    │
│  組裝所有依賴、啟動 Polling Loop                   │
├─────────────────────────────────────────────────┤
│  services/         業務邏輯層                      │
│  ├── pipeline      主流程編排（process_issue）      │
│  ├── workflow       Workflow YAML 載入 + phase 導航│
│  ├── role           Label 解析 → 角色分派          │
│  └── prompt         Prompt 組裝                    │
├─────────────────────────────────────────────────┤
│  ports/            介面定義（typing.Protocol）      │
│  ├── github_port   Issue/Comment/Label 操作        │
│  ├── agent_port    Agent 執行                      │
│  └── hooks_port    Workspace hook scripts 執行     │
├─────────────────────────────────────────────────┤
│  domain/           純資料模型（零依賴）              │
│  ├── models        AgentResult, ResolvedLabels     │
│  └── workflow      Workflow, Phase, RepoConfig     │
├─────────────────────────────────────────────────┤
│  adapters/         Outbound Adapter（實作 Port）    │
│  ├── github        gh CLI → GitHubPort             │
│  ├── agent         gh copilot CLI → AgentPort      │
│  └── hooks         subprocess → HooksPort          │
└─────────────────────────────────────────────────┘
```

**依賴方向**：`main.py` → `services/` → `ports/` + `domain/` ← `adapters/`

**核心規則**：`services/` 和 `domain/` 絕不 import `adapters/`，只透過 `ports/` 定義的 Protocol 介面互動。

## 系統組件一覽

| 組件 | 層級 | 說明 |
|---|---|---|
| Docker Container | 基礎設施 | 運行環境，包含所有工具和 Script |
| `main.py` | Inbound Adapter | Composition Root：組裝依賴 + 常駐 Polling Loop |
| `services/pipeline.py` | Service | 主流程編排：process_issue()，依賴 Port 介面 |
| `services/workflow_service.py` | Service | Workflow YAML 載入、phase 導航 |
| `services/role_service.py` | Service | 根據 Issue label 決定 Agent 角色 |
| `services/prompt_service.py` | Service | Prompt 組裝（含 workflow/repos/phase-prompt context） |
| `ports/` | Port | 介面定義（`typing.Protocol`），解耦 Service 與 Adapter |
| `adapters/github_adapter.py` | Outbound Adapter | GitHub API 封裝（via `gh` CLI） |
| `adapters/agent_adapter.py` | Outbound Adapter | `gh copilot` CLI 執行器 |
| `adapters/hooks_adapter.py` | Outbound Adapter | Workspace hook scripts 執行（支援 phase_env 環境變數） |
| `domain/models.py` | Domain Model | 純資料結構：AgentResult, ResolvedLabels |
| `domain/workflow.py` | Domain Model | 純資料結構：Workflow, Phase, RepoConfig |
| `config.py` | 設定 | 環境變數讀取、Config dataclass |
| `entrypoint.sh` | 基礎設施 | Docker entrypoint（auth + 驗證 + 啟動） |
| `setup-auth.sh` | 工具 | host 端執行，協助 User 設定 gh 認證情報 |
| 角色 Agent 設定 (`agents/`) | 設定 | 每個角色一個目錄，包含 instructions |
| Workflow 定義 (`workflows/`) | 設定 | YAML 定義多階段工作流 |
| Workspace hook scripts (`workspace-scripts/`) | 設定 | Agent 執行前後的環境設定腳本（如 git clone/push、git write 攔截） |

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
./workspace-scripts/        →    /app/workspace-scripts/ (ro)  Workspace hook scripts
./workspace/                →    /workspace/                   Agent 工作區
```

## 環境變數

| 變數名 | 說明 | 預設值 |
|---|---|---|
| `TARGET_ISSUE_REPO` | 監控的 GitHub repo（`owner/repo`） | **必填** |
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

Agent 目錄只包含 `instructions.md`，model 等啟動設定集中在 Workflow YAML 中管理。

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
  config:
    - repo: owner/some-project
      url: ""
      description: "專案說明"
  steps:
    - role: manager
      phasename: requirement-analysis
      phase-prompt: "Analyze the issue, clarify requirements."
      llm-model: ""
      phase-env: {}
      workspace-init:
        - clone-and-branch.sh
        - ban-git-write.sh
      workspace-cleanup:
        - unban-git-write.sh
        - push-and-pr.sh
    - role: architect
      phasename: system-design
      phase-prompt: "Design the system architecture."
      llm-model: ""
      workspace-init:
        - clone-and-branch.sh
        - ban-git-write.sh
      workspace-cleanup:
        - unban-git-write.sh
        - push-and-pr.sh
    - role: coder
      phasename: implementation
      phase-prompt: "Implement the design."
      llm-model: ""
      workspace-init:
        - clone-and-branch.sh
        - ban-git-write.sh
      workspace-cleanup:
        - unban-git-write.sh
        - push-and-pr.sh
    - role: qa
      phasename: verification
      phase-prompt: "Verify the implementation."
      llm-model: ""
      workspace-init:
        - clone-and-branch.sh
        - ban-git-write.sh
      workspace-cleanup:
        - unban-git-write.sh
        - push-and-pr.sh
```

- `config`：工作 repo 清單。`repo` 為 `owner/repo` 格式，`url` 可選（空 = 用 `gh repo clone`），`description` 會帶入 prompt。
- `steps`：階段設定。`phase-prompt` 為該階段的提示文字（帶入 agent prompt，支援 `{BRANCH_NAME}` / `{ISSUE_NUMBER}` 佔位符）。`llm-model` 指定該階段使用的 LLM 模型（空字串 = 使用 `COPILOT_MODEL` 環境變數）。
- `phase-env`：額外環境變數 map，傳給該 phase 的所有 hook scripts。
- `workspace-init` / `workspace-cleanup`：Agent 執行前/後跑的腳本（從 `workspace-scripts/` 載入）。典型配置：`clone-and-branch.sh`（clone + checkout）+ `ban-git-write.sh`（攔截）在 init，`unban-git-write.sh`（移除攔截）+ `push-and-pr.sh`（push + PR）在 cleanup。

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

> **觸發機制**：以 `workflow:xxx` label 存在與否作為處理依據，無需時間戳比對。Workflow 完成後設定 `phase:end`，因此下次輪詢不會重複處理。

## Agent 呼叫方式

```bash
gh copilot -p "<prompt>" --yolo --no-ask-user --add-dir /workspace [--model MODEL]
```

- prompt 由 PromptService 組裝：role instructions + issue 內容 + workflow/repos/phase-prompt context
- Model 由 Workflow YAML 或環境變數決定

## 主控流程（Hexagonal Architecture）

### Composition Root（main.py）

```
main():
  1. config = load_config()
  2. 建立 Adapter 實例（github, agent, hooks）
  3. 建立 Service 實例，注入 Port/Adapter
  4. workflows = workflow_service.load_workflows(config.workflow_file)
  5. Loop:
     a. issues = github_adapter.list_open_issues(config.target_issue_repo)
     b. 對每個 issue:
        pipeline_service.process_issue(issue["number"], issue["labels"], config, workflows)
     c. sleep $POLL_INTERVAL
```

### Pipeline Service（process_issue）

```
process_issue(number, labels, config, workflows):
  1. role_service.resolve_labels(labels) → ResolvedLabels（role, workflow, phase）
  2. 若無 workflow → skip；若 phase:end → skip
  3. workflow_service.resolve_phase(workflow, phase_name, repo, number) → (idx, phase)
  4. workflow_service.build_phase_env(workflow, phase, number, repo) → phase_env
  5. hooks_port.run_workspace_scripts(phase.workspace_init, phase_env) → clone + branch + ban-git-write
  6. prompt_service.build_prompt(repo, number, role, agents_dir, phase, workflow_repos)
  7. agent_port.run(prompt, role, agents_dir, timeout, model) → AgentResult
  8. hooks_port.run_workspace_scripts(phase.workspace_cleanup, phase_env) → unban-git-write + push + PR
  9. github_port.post_comment(repo, number, body)
  10. workflow_service.advance_phase(workflow, idx, repo, number) → 階段轉換
```

### 依賴注入方式

Service 透過建構式接收 Port 介面（`typing.Protocol`），不直接 import Adapter 實作。
`main.py` 負責建立 Adapter 實例並注入到 Service。

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
│   └── 03-basic-design.md       # 系統基本設計
├── scripts/
│   ├── main.py                  # Composition Root（組裝依賴 + Polling Loop）
│   ├── config.py                # 環境變數讀取、Config dataclass
│   ├── domain/                  # Domain Model（純資料結構，零依賴）
│   │   ├── models.py            # AgentResult, ResolvedLabels
│   │   └── workflow.py          # Workflow, Phase, RepoConfig dataclasses
│   ├── ports/                   # Port 介面定義（typing.Protocol）
│   │   ├── github_port.py       # GitHubPort: issue/comment/label 操作
│   │   ├── agent_port.py        # AgentPort: 執行 agent
│   │   └── hooks_port.py        # HooksPort: workspace-scripts 執行
│   ├── services/                # 業務邏輯（依賴 Port + Domain）
│   │   ├── pipeline.py          # process_issue()：主流程編排
│   │   ├── workflow_service.py  # Workflow YAML 載入、phase 導航
│   │   ├── role_service.py      # Label 解析 → ResolvedLabels
│   │   └── prompt_service.py    # Prompt 組裝（含 workflow/repos context）
│   ├── adapters/                # Outbound Adapter（實作 Port 介面）
│   │   ├── github_adapter.py    # 實作 GitHubPort（gh CLI）
│   │   ├── agent_adapter.py     # 實作 AgentPort（gh copilot CLI）
│   │   └── hooks_adapter.py     # 實作 HooksPort（subprocess）
│   ├── entrypoint.sh            # Docker entrypoint（auth + 驗證 + 啟動）
│   └── setup-auth.sh            # 認證設定工具（host 端執行）
├── workspace-scripts/           # Workspace hook scripts
│   ├── clone-and-branch.sh      # Clone repos + checkout feature branch
│   ├── push-and-pr.sh           # Stage/commit/push + create draft PR
│   ├── ban-git-write.sh         # 攔截 Agent 的 git write 操作
│   └── unban-git-write.sh       # 移除 git write 攔截
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
│   └── default.yml              # 預設 Workflow
├── test/
│   └── e2e-test.sh              # E2E 測試腳本
├── auth/                        # gh 認證情報（gitignore）
└── workspace/                   # Agent 工作區
```
