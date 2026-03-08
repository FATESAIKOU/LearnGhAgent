# GitHub Issue Agent

定期監視 GitHub repo 的 Issue，自動使用 `gh copilot` CLI 讀取 Issue 內容並執行任務，完成後將結果回寫為 Issue comment。

## 使用場景

### 1. 單一角色任務

在 Issue 上加上 `role:coder` label，Agent 會自動用 Coder 角色讀取 Issue 並執行任務，完成後回寫摘要並移除 label。

**適合用在：**
- 「幫我在 workspace 裡建立一個 hello world 的 Python script」
- 「幫我把 workspace 裡的 README 翻譯成英文」
- 讓 AI 自動處理簡單的檔案操作或程式碼生成

### 2. 持續監控 + 對話式任務

Agent 每隔固定秒數輪詢一次，發現 Issue 有新 comment 就會重新處理。你可以重新加上 `role:xxx` label 並追加指示，Agent 會接續執行。

**適合用在：**
- 對 Agent 的結果不滿意，追加修改指示
- 多步驟任務，分次下達

### 3. 多角色 Workflow 自動串接

透過 Workflow YAML 定義多階段任務，Issue 加上 `role:xxx` + `workflow:xxx` + `phase:xxx` 三個 label 啟動。Agent 完成每個階段後自動轉換到下一個角色/階段。

**範例：** `full-development` workflow
1. `role:manager` + `phase:requirement-analysis` → Manager 分析需求
2. 自動轉換 → `role:architect` + `phase:system-design` → Architect 設計架構
3. 自動轉換 → `role:coder` + `phase:implementation` → Coder 寫程式
4. 自動轉換 → `role:qa` + `phase:verification` → QA 驗證

**適合用在：**
- 完整的功能開發流程（需求 → 設計 → 實作 → 驗證）
- 快速修復流程（修復 → 驗證）

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
  -e TARGET_REPO=owner/repo \
  -v "$(pwd)/auth/hosts.yml:/auth-src/hosts.yml:ro" \
  -v "$(pwd)/data:/data" \
  -v "$(pwd)/agents:/app/agents:ro" \
  -v "$(pwd)/workflows:/app/workflows:ro" \
  -v "$(pwd)/workspace:/workspace" \
  gh-issue-agent
```

```bash
# 自訂設定（指定啟用角色、model、poll 間隔）
docker run -d --name gh-issue-agent \
  -e TARGET_REPO=owner/repo \
  -e POLL_INTERVAL=30 \
  -e AGENT_TIMEOUT=120 \
  -e COPILOT_MODEL=claude-sonnet-4.6 \
  -e ENABLED_AGENTS=coder,qa \
  -v "$(pwd)/auth/hosts.yml:/auth-src/hosts.yml:ro" \
  -v "$(pwd)/data:/data" \
  -v "$(pwd)/agents:/app/agents:ro" \
  -v "$(pwd)/workflows:/app/workflows:ro" \
  -v "$(pwd)/workspace:/workspace" \
  gh-issue-agent
```

若有安裝 Docker Compose plugin：

```bash
TARGET_REPO=owner/repo docker compose up -d
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
| `TARGET_REPO` | 監控的 repo（`owner/repo` 格式） | **必填** |
| `POLL_INTERVAL` | 輪詢間隔（秒） | `60` |
| `AGENT_TIMEOUT` | Agent 單次執行超時（秒） | `900` |
| `COPILOT_MODEL` | 指定 AI 模型（見下方模型表） | 不指定（用預設） |
| `DEFAULT_ROLE` | 預設 Agent 角色 | `default` |
| `ENABLED_AGENTS` | 啟用的 agent 角色（逗號分隔，空=全部） | 空（全部啟用） |
| `WORKFLOW_FILE` | Workflow YAML 定義檔路徑 | `/app/workflows/default.yml` |

---

## 可用模型

透過環境變數 `COPILOT_MODEL` 或角色 `config.json` 中的 `model` 欄位指定。

```bash
# 範例：使用 Claude Sonnet 4.6
docker run -d --name gh-issue-agent \
  -e TARGET_REPO=owner/repo \
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

```
LearnGhAgent/
├── Dockerfile                   # Docker 映像定義
├── docker-compose.yml           # Docker Compose 設定
├── .gitignore
├── scripts/
│   ├── entrypoint.sh            # 容器啟動腳本（含 auto-clone）
│   ├── agent_loop.py            # 主控迴圈（含 workflow 支援）
│   ├── config.py                # 環境變數讀取
│   ├── github_client.py         # GitHub API 封裝（含 label 操作）
│   ├── state_manager.py         # 狀態持久化
│   ├── role_resolver.py         # 角色分派（label 解析）
│   ├── prompt_builder.py        # Prompt 組合（含 workflow context）
│   ├── agent_runner.py          # gh copilot 執行器（JSONL streaming）
│   ├── workflow_loader.py       # Workflow YAML 載入與階段轉換
│   └── setup-auth.sh            # 認證設定工具（host 端）
├── agents/                      # Agent 角色定義
│   ├── default/                 # 預設角色
│   ├── manager/                 # 需求分析、任務分解
│   ├── architect/               # 系統設計、架構規劃
│   ├── coder/                   # 程式實作
│   └── qa/                      # 品質驗證、測試
├── workflows/                   # Workflow 定義
│   └── default.yml              # 預設 Workflow
├── auth/                        # 認證檔案（gitignored）
├── data/                        # 狀態持久化（state.json）
└── workspace/                   # Agent 工作區
```

---

## 自訂角色

在 `agents/` 下建立新目錄：

```
agents/
└── my-role/
    ├── instructions.md     # 角色的系統指示
    └── config.json         # {"model": "", "extra_flags": ""}
```

然後在 Issue 上加 label `role:my-role`，Agent 就會使用該角色的 instructions 執行。

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
| 角色 | `role:xxx` | **必須**。指定執行的 Agent 角色（對應 `agents/xxx/` 目錄） |
| 工作流 | `workflow:xxx` | 選用。指定使用的 Workflow 定義（對應 YAML 中的 key） |
| 階段 | `phase:xxx` | 選用。指定 Workflow 目前階段（對應 YAML 中的 phasename） |

### 單一角色（無 Workflow）

只加 `role:xxx` label → Agent 執行後自動移除該 label。

### 多階段 Workflow

加上 `role:xxx` + `workflow:xxx` + `phase:xxx` → Agent 完成後自動轉換到下一階段。

**範例：啟動 full-development workflow**

在 Issue 加上以下 3 個 label：
- `role:manager`
- `workflow:full-development`
- `phase:requirement-analysis`

Agent 會依序自動執行：
1. Manager → 需求分析
2. Architect → 系統設計
3. Coder → 程式實作
4. QA → 品質驗證

### Workflow YAML 格式

定義在 `workflows/default.yml`：

```yaml
full-development:
  - role: manager
    phasename: requirement-analysis
    phasetarget: "Analyze the issue, clarify requirements."
    llm-model: ""          # 空字串 = 使用預設 model
  - role: architect
    phasename: system-design
    phasetarget: "Design the system architecture."
    llm-model: ""
  - role: coder
    phasename: implementation
    phasetarget: "Implement the design, write code."
    llm-model: ""
  - role: qa
    phasename: verification
    phasetarget: "Verify the implementation."
    llm-model: ""

quick-fix:
  - role: coder
    phasename: fix
    phasetarget: "Fix the bug described in the issue."
    llm-model: ""
  - role: qa
    phasename: verify-fix
    phasetarget: "Verify the fix is correct."
    llm-model: ""
```

### Model 優先順序

1. Workflow phase 的 `llm-model`（若非空）
2. 環境變數 `COPILOT_MODEL`

---

## 運作原理

1. **輪詢**：每 `POLL_INTERVAL` 秒取得 repo 所有 open issues
2. **Label 解析**：檢查每個 Issue 的 `role:xxx` label，對應 `agents/xxx/` 目錄，過濾 `ENABLED_AGENTS`
3. **偵測新活動**：比對 Issue 最新 comment 時間與 `state.json` 記錄
4. **Workflow 解析**：若有 `workflow:xxx` + `phase:xxx` label，載入對應 Workflow 定義，注入 phase 資訊到 prompt
5. **執行**：組合 issue 內容 + 角色 instructions + workflow context 為 prompt，呼叫 `gh copilot -p "..." --yolo --no-ask-user --output-format json`
6. **回寫**：將 Agent 輸出作為 comment 回寫到 Issue
7. **階段轉換**：移除當前 `role:` + `phase:` label，加上下一階段的 label（若有 Workflow）
8. **更新狀態**：記錄已處理時間
