# GitHub Issue Agent

定期監視 GitHub repo 的 Issue，自動使用 `gh copilot` CLI 讀取 Issue 內容並執行任務，完成後將結果回寫為 Issue comment。

## 使用場景

### Workflow 自動串接

透過 Workflow YAML 定義多階段任務，Issue 只需加上 `workflow:xxx` label 即可啟動。Agent 會自動從第一階段開始，每個階段完成後根據 **branch rules** 決定下一階段（條件分歧或無條件前進），最後標記 `phase:end` 表示完成。

Workflow 可以指定多個工作 repo，Agent 會自動 clone 並建立 feature branch，每次執行後自動 push + 開 PR。

**範例：** `full-development` workflow（無條件線性前進）
1. 自動開始 → `role:manager` + `phase:requirement-analysis` → Manager 分析需求
2. Branch → `role:architect` + `phase:system-design` → Architect 設計架構
3. Branch → `role:coder` + `phase:implementation` → Coder 寫程式
4. Branch → `role:qa` + `phase:verification` → QA 驗證
5. Branch → `target: end` → 設定 `phase:end`

**範例：** `technical-investigation` workflow（條件分歧 + 重試）
- 每階段完成後由 `check-deliverables.sh` 驗證成果物
- 驗證通過（`PHASE_STATUS=OK`）→ 前進到下一階段
- 驗證失敗 → 重試同一階段（label 不變，下次 poll 再執行）

**適合用在：**
- 完整的功能開發流程（需求 → 設計 → 實作 → 驗證）
- 快速修復流程（修復 → 驗證）
- 技術調查、文件撰寫等多步驟任務

### 重新觸發

Workflow 完成後 Issue 會有 `workflow:xxx` + `phase:end`。若要重新執行，移除 `phase:end` label 即可，Agent 會從第一階段重新開始。

---

## 快速開始

### 前置需求

- Docker（macOS 可用 Colima）
- `gh` CLI（[安裝](https://cli.github.com/)）
- 已登入 `gh auth login`

### 1. 設定認證

```bash
# 自動產生 auth/hosts.yml
bash scripts/setup-auth.sh
```

或手動建立 `auth/hosts.yml`：

```yaml
github.com:
    oauth_token: gho_你的token
    git_protocol: https
    user: 你的GitHub帳號
```

> Token 可透過 `gh auth token` 取得。

### 2. Build Docker Image

```bash
docker build -t gh-issue-agent .
```

### 3. 啟動 Agent

```bash
# 基本啟動（背景執行）
docker run -d --name gh-issue-agent \
  -e TARGET_ISSUE_REPO=owner/issue-repo \
  -v "$(pwd)/auth/hosts.yml:/auth-src/hosts.yml:ro" \
  -v "$(pwd)/agents:/app/agents:ro" \
  -v "$(pwd)/workflows:/app/workflows:ro" \
  -v "$(pwd)/workspace-scripts:/app/workspace-scripts:ro" \
  -v "$(pwd)/workspace:/workspace" \
  gh-issue-agent
```

```bash
# 自訂設定（指定啟用角色、model、poll 間隔）
docker run -d --name gh-issue-agent \
  -e TARGET_ISSUE_REPO=owner/issue-repo \
  -e POLL_INTERVAL=30 \
  -e AGENT_TIMEOUT=120 \
  -e COPILOT_MODEL=claude-sonnet-4.6 \
  -e ENABLED_AGENTS=coder,qa \
  -v "$(pwd)/auth/hosts.yml:/auth-src/hosts.yml:ro" \
  -v "$(pwd)/agents:/app/agents:ro" \
  -v "$(pwd)/workflows:/app/workflows:ro" \
  -v "$(pwd)/workspace-scripts:/app/workspace-scripts:ro" \
  -v "$(pwd)/workspace:/workspace" \
  gh-issue-agent
```

若有安裝 Docker Compose plugin：

```bash
TARGET_ISSUE_REPO=owner/issue-repo docker compose up -d
```

### 4. 查看 Log

```bash
docker logs -f gh-issue-agent
```

### 5. 停止

```bash
docker stop gh-issue-agent && docker rm gh-issue-agent
```

---

## 環境變數

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `TARGET_ISSUE_REPO` | Issue 管理用的 repo（`owner/repo` 格式） | **必填** |
| `POLL_INTERVAL` | 輪詢間隔（秒） | `60` |
| `AGENT_TIMEOUT` | Agent 單次執行超時（秒） | `900` |
| `COPILOT_MODEL` | 指定 AI 模型（見下方模型表） | 不指定（用預設） |
| `DEFAULT_ROLE` | 預設 Agent 角色 | `default` |
| `ENABLED_AGENTS` | 啟用的 agent 角色（逗號分隔，空=全部） | 空（全部啟用） |
| `WORKFLOW_FILE` | Workflow YAML 定義檔路徑 | `/app/workflows/default.yml` |

---

## 可用模型

透過環境變數 `COPILOT_MODEL` 或 Workflow YAML 中的 `llm-model` 欄位指定。

```bash
# 範例：使用 Claude Sonnet 4.6
docker run -d --name gh-issue-agent \
  -e TARGET_ISSUE_REPO=owner/issue-repo \
  -e COPILOT_MODEL=claude-sonnet-4.6 \
  ...
```

| VS Code 顯示名稱 | CLI `--model` 值 | Premium 倍率 |
|---|---|---|
| Claude Haiku 4.5 | `claude-haiku-4.5` | 0.33x |
| Claude Sonnet 4 | `claude-sonnet-4` | 1x |
| Claude Sonnet 4.5 | `claude-sonnet-4.5` | 1x |
| Claude Sonnet 4.6 | `claude-sonnet-4.6` | 1x |
| Claude Opus 4.5 | `claude-opus-4.5` | 3x |
| Claude Opus 4.6 | `claude-opus-4.6` | 3x |
| *(CLI 專屬)* | `claude-opus-4.6-fast` | — |
| GPT-4.1 | `gpt-4.1` | 0x |
| GPT-5 mini | `gpt-5-mini` | 0x |
| GPT-5.1 | `gpt-5.1` | 1x |
| GPT-5.1-Codex | `gpt-5.1-codex` | 1x |
| GPT-5.1-Codex-Max | `gpt-5.1-codex-max` | 1x |
| GPT-5.1-Codex-Mini (Preview) | `gpt-5.1-codex-mini` | 0.33x |
| GPT-5.2 | `gpt-5.2` | 1x |
| GPT-5.2-Codex | `gpt-5.2-codex` | 1x |
| GPT-5.3-Codex | `gpt-5.3-codex` | 1x |
| GPT-5.4 | `gpt-5.4` | 1x |
| Gemini 3 Pro (Preview) | `gemini-3-pro-preview` | 1x |

> **注意**：以下 VS Code 模型在 CLI **不可用**：GPT-4o、Raptor mini、Gemini 2.5 Pro、Gemini 3 Flash、Gemini 3.1 Pro、Grok Code Fast 1。

---

## 專案結構

本專案採用 **Hexagonal Architecture（Ports & Adapters）**，將程式碼分為 Domain Model、Port、Service、Adapter 四層。

```
LearnGhAgent/
├── Dockerfile                   # Docker 映像定義
├── docker-compose.yml           # Docker Compose 設定
├── .gitignore
├── docs/                        # 設計文件
│   ├── 01-requirements.md       # 需求定義
│   ├── 02-system-design.md      # 系統要件設計
│   └── 03-basic-design.md       # 系統基本設計
├── scripts/
│   ├── main.py                  # Composition Root（組裝依賴 + Polling Loop）
│   ├── config.py                # 環境變數讀取、Config dataclass
│   ├── domain/                  # Domain Model（純資料結構，零依賴）
│   │   ├── models.py            # AgentResult, ResolvedLabels
│   │   └── workflow.py          # Workflow, Phase, RepoConfig, BranchRule
│   ├── ports/                   # Port 介面定義（typing.Protocol）
│   │   ├── github_port.py       # GitHubPort: issue/comment/label
│   │   ├── agent_port.py        # AgentPort: 執行 agent
│   │   └── hooks_port.py        # HooksPort: workspace-scripts
│   ├── services/                # 業務邏輯（依賴 Port + Domain）
│   │   ├── pipeline.py          # process_issue()：主流程編排
│   │   ├── workflow_service.py  # Workflow YAML 載入、phase 導航
│   │   ├── role_service.py      # Label 解析 → 角色分派
│   │   └── prompt_service.py    # Prompt 組裝
│   ├── adapters/                # Outbound Adapter（實作 Port）
│   │   ├── github_adapter.py    # gh CLI → GitHubPort
│   │   ├── agent_adapter.py     # gh copilot CLI → AgentPort
│   │   └── hooks_adapter.py     # subprocess → HooksPort
│   ├── entrypoint.sh            # Docker entrypoint（auth + 驗證 + 啟動）
│   └── setup-auth.sh            # 認證設定工具（host 端）
├── workspace-scripts/           # Workspace hook scripts
│   ├── clone-and-branch.sh      # Clone repos + checkout feature branch
│   ├── push-and-pr.sh           # Stage/commit/push + create draft PR
│   ├── check-deliverables.sh    # 驗證成果物，寫入 PHASE_STATUS 到 .branch-vars
│   ├── ban-git-write.sh         # 攔截 Agent 的 git write 操作
│   └── unban-git-write.sh       # 移除 git write 攔截
├── agents/                      # Agent 角色定義
│   ├── default/                 # 預設角色
│   ├── manager/                 # 需求分析、任務分解
│   ├── architect/               # 系統設計、架構規劃
│   ├── coder/                   # 程式實作
│   └── qa/                      # 品質驗證、測試
├── workflows/                   # Workflow 定義
│   └── default.yml              # 預設 Workflow
├── test/
│   └── e2e-test.sh              # E2E 測試腳本
├── auth/                        # 認證檔案（gitignored）
└── workspace/                   # Agent 工作區（各 repo clone 於此）
```

---

## 自訂角色

在 `agents/` 下建立新目錄：

```
agents/
└── my-role/
    └── instructions.md     # 角色的系統指示（唯一必要檔案）
```

然後在 Workflow YAML 的 step 中指定 `role: my-role`，Agent 就會使用該角色的 instructions 執行。

### 內建角色

| 角色 | Label | 說明 |
|------|-------|------|
| default | `role:default` | 通用 AI 助手 |
| manager | `role:manager` | 需求分析、任務分解、產出需求文件 |
| architect | `role:architect` | 系統設計、架構規劃、技術選型 |
| coder | `role:coder` | 程式實作、撰寫測試、commit 變更 |
| qa | `role:qa` | 品質驗證、測試執行、安全審查 |

---

## Workflow 系統

### Label 系統

Issue 使用三種 label 控制 Agent 行為：

| Label | 格式 | 說明 |
|-------|------|------|
| 工作流 | `workflow:xxx` | **必須**。指定使用的 Workflow 定義（對應 YAML 中的 key），作為觸發條件 |
| 角色 | `role:xxx` | 自動管理。由 Workflow 根據當前 phase 自動設定，無需手動加 |
| 階段 | `phase:xxx` | 自動管理。追蹤目前階段，`phase:end` 表示 Workflow 已完成 |

### 啟動 Workflow

只加 `workflow:xxx` label → Agent 自動從第一階段開始，每個 phase 完成後根據 `branchs` 規則決定下一步，最後標記 `phase:end`。

> `role:xxx` 和 `phase:xxx` 由系統自動管理，不需手動設定。

**範例：啟動 full-development workflow**

在 Issue 加上 1 個 label：
- `workflow:full-development`

Agent 會根據 branch rules 自動執行：
1. Manager → 需求分析 → branch → system-design
2. Architect → 系統設計 → branch → implementation
3. Coder → 程式實作 → branch → verification
4. QA → 品質驗證 → branch → end
5. 完成 → `phase:end`

### Workflow YAML 格式

定義在 `workflows/default.yml`，每個 workflow 包含 `config`（工作 repo 清單）和 `steps`（階段序列）：

```yaml
full-development:
  config:
    - repo: owner/some-project
      url: ""                   # 可省略（用 gh repo clone）
      description: "專案說明"
  steps:
    - role: manager
      phasename: requirement-analysis
      phase-prompt: "Analyze the issue, clarify requirements."
      llm-model: ""          # 空字串 = 使用預設 model
      phase-env: {}           # 額外環境變數（傳給 hook scripts）
      workspace-init:         # Agent 執行前跑的腳本（從 workspace-scripts/ 載入）
        - clone-and-branch.sh
        - ban-git-write.sh
      workspace-cleanup:      # Agent 執行後跑的腳本
        - unban-git-write.sh
        - push-and-pr.sh
      branchs:                # 必填：分歧規則（依序評估，第一個匹配生效）
        - target: system-design
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
      branchs:
        - target: implementation
    # ... (coder → verification → end)

technical-investigation:
  config:
    - repo: owner/target-repo
      description: "Investigation output repo"
  steps:
    - role: manager
      phasename: investigation-scope
      phase-prompt: "Define investigation boundaries."
      llm-model: "gpt-5-mini"
      phase-env:
        DELIVERABLES: "*/docs/issue-{ISSUE_NUMBER}/requirements.md"  # 驗證用 glob 模式
      workspace-init:
        - clone-and-branch.sh
        - ban-git-write.sh
      workspace-cleanup:
        - unban-git-write.sh
        - push-and-pr.sh
        - check-deliverables.sh   # 驗證成果物，寫入 PHASE_STATUS
      branchs:                    # 條件分歧：驗證通過才前進
        - PHASE_STATUS: OK
          target: evaluation-framework
        - target: investigation-scope   # 預設：重試當前階段
    # ...
```

**config 欄位（工作 repo 清單）：**

| 欄位 | 說明 |
|------|------|
| `repo` | `owner/repo` 格式，用於 git clone 和 PR 建立 |
| `url` | 可選的 git URL override（空 = 用 `gh repo clone`）|
| `description` | repo 說明（會帶入 Agent prompt）|

**step 欄位（每階段設定）：**

| 欄位 | 說明 |
|------|------|
| `role` | Agent 角色（對應 `agents/xxx/` 目錄） |
| `phasename` | 階段識別名（用於 `phase:xxx` label） |
| `phase-prompt` | 該階段的提示文字（帶入 agent prompt，支援 `{BRANCH_NAME}` / `{ISSUE_NUMBER}` 佔位符） |
| `llm-model` | LLM 模型 override（空 = 用環境變數） |
| `phase-env` | 額外環境變數 map（傳給該 phase 的所有 hook scripts） |
| `workspace-init` | Agent 執行前跑的腳本列表（從 `workspace-scripts/` 載入） |
| `workspace-cleanup` | Agent 執行後跑的腳本列表 |
| `branchs` | **必填**。分歧規則列表，每個規則含 `target`（phasename 或 `end`）及可選條件。詳見下方 |

### Branch Rules（分歧規則）

每個 step 必須有 `branchs` 欄位，定義階段完成後的流向。規則依序評估，第一個匹配規則生效：

| 欄位 | 說明 |
|------|------|
| `target` | **必填**。目標 phasename 或 `end`（結束 Workflow） |
| 其他 KEY: VALUE | 可選條件。與 `/workspace/.branch-vars` 中的值比對 |

**無條件規則**（只有 `target`）= 預設 fallback，總是匹配。
**條件規則** = 所有 KEY=VALUE 都必須匹配才生效。

```yaml
branchs:
  - PHASE_STATUS: OK          # 條件：PHASE_STATUS 等於 OK
    target: next-phase         # 匹配 → 前進到 next-phase
  - target: current-phase      # 無條件 → 重試（label 不變）
```

**Branch-vars 機制**：workspace-cleanup 腳本（如 `check-deliverables.sh`）將結果寫入 `/workspace/.branch-vars`（`KEY=VALUE` 格式），Pipeline 在 cleanup 後讀取此檔案評估分歧規則。

### Model 優先順序

1. Workflow phase 的 `llm-model`（若非空）
2. 環境變數 `COPILOT_MODEL`

---

## 運作原理

1. **輪詢**：每 `POLL_INTERVAL` 秒取得 `TARGET_ISSUE_REPO` 所有 open issues
2. **觸發判定**：檢查 Issue 是否有 `workflow:xxx` label；若有 `phase:end` 則跳過（已完成）
3. **Workflow 解析**：載入對應 Workflow 定義；若無 `phase:xxx` 則自動從第一階段開始，並補上 `role:xxx` + `phase:xxx` label
4. **角色決定**：從 Workflow phase 定義取得角色（`phase.role`），對應 `agents/xxx/` 目錄
5. **Phase 環境建構**：從 Workflow config + phase-env 建構環境變數（含 `REPOS`、`ISSUE_NUMBER`、`BRANCH_NAME` 等）
6. **Workspace-init hooks**：執行當前 phase 定義的 `workspace-init` 腳本（例如 `clone-and-branch.sh` clone repo + checkout branch、`ban-git-write.sh` 安裝 git write 攔截）
7. **執行**：組合 issue 內容 + 角色 instructions + workflow/repos/phase-prompt context 為 prompt，呼叫 `gh copilot`
8. **Workspace-cleanup hooks**：執行當前 phase 定義的 `workspace-cleanup` 腳本（例如 `unban-git-write.sh` 移除攔截、`push-and-pr.sh` 自動 commit + push + 建立 draft PR、`check-deliverables.sh` 驗證成果物）
9. **回寫**：將 Agent 輸出作為 comment 回寫到 Issue
10. **Branch 評估與階段轉換**：讀取 `/workspace/.branch-vars`，依序評估 `branchs` 規則決定目標。目標為同一階段時保持 label 不變（重試），目標為 `end` 時設定 `phase:end`，否則轉換到目標階段的 `role:xxx` + `phase:xxx`

> **觸發機制**：以 `workflow:xxx` label 存在且無 `phase:end` 作為處理依據，無需時間戳比對。Workflow 完成後設定 `phase:end`，因此下次輪詢不會重複處理。Git clone / push / PR 操作已移至 `workspace-scripts/` 中的 shell scripts，透過 `workspace-init` 和 `workspace-cleanup` hooks 執行。Agent 超時或失敗時不進行 branch 評估，label 維持不變，下次輪詢自動重試。

---

## E2E 測試

提供 E2E 測試腳本，可驗證完整的多階段 Workflow 執行流程。

### 前置需求

- Docker 已啟動（已 build `learnghagent:latest`）
- `gh` CLI 已登入
- 目標 repo 已存在對應的 Issue

### 執行方式

```bash
bash test/e2e-test.sh <REPO> <ISSUE_NUMBER> <WORKFLOW_NAME>

# 範例：
bash test/e2e-test.sh FATESAIKOU/SelfImprovement 20 technical-investigation
```

### 測試流程

1. 在目標 Issue 上設定 `workflow:xxx` label（系統自動加 `role:xxx` + `phase:xxx`）
2. 啟動 Docker container（`POLL_INTERVAL=10`）
3. 等待所有 Workflow 階段完成（偵測 `phase:end` label 設定）
4. 驗證：comment 數量、push 次數、PR 建立、workspace-scripts 執行
5. 清理：停止 container
