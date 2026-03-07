# GitHub Issue Agent

定期監視 GitHub repo 的 Issue，自動使用 `gh copilot` CLI 讀取 Issue 內容並執行任務，完成後將結果回寫為 Issue comment。

## 使用場景

### 1. 自動回覆 Issue 任務

在 Issue 中描述一個任務，Agent 會自動讀取並嘗試執行，完成後回寫摘要。

**適合用在：**
- 「幫我在 workspace 裡建立一個 hello world 的 Python script」
- 「幫我把 workspace 裡的 README 翻譯成英文」
- 讓 AI 自動處理簡單的檔案操作或程式碼生成

### 2. 持續監控 + 對話式任務

Agent 每隔固定秒數輪詢一次，發現 Issue 有新 comment 就會重新處理。你可以在 Issue 裡持續追加指示，Agent 會接續執行。

**適合用在：**
- 對 Agent 的結果不滿意，追加修改指示
- 多步驟任務，分次下達

### 3. 多角色分派（未來擴展）

透過 Issue label 指定不同的 Agent 角色（如 `role:coder`、`role:qa`），每個角色有獨立的 instructions 和設定。

**適合用在：**
- 不同 Issue 用不同風格的 AI 處理
- 建立 Manager / Architect / Coder / QA 多角色工作流

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
  -v "$(pwd)/workspace:/workspace" \
  gh-issue-agent
```

```bash
# 自訂 poll 間隔和 timeout
docker run -d --name gh-issue-agent \
  -e TARGET_REPO=owner/repo \
  -e POLL_INTERVAL=30 \
  -e AGENT_TIMEOUT=120 \
  -v "$(pwd)/auth/hosts.yml:/auth-src/hosts.yml:ro" \
  -v "$(pwd)/data:/data" \
  -v "$(pwd)/agents:/app/agents:ro" \
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
│   ├── entrypoint.sh            # 容器啟動腳本
│   ├── agent_loop.py            # 主控迴圈
│   ├── config.py                # 環境變數讀取
│   ├── github_client.py         # GitHub API 封裝
│   ├── state_manager.py         # 狀態持久化
│   ├── role_resolver.py         # 角色分派
│   ├── prompt_builder.py        # Prompt 組合
│   ├── agent_runner.py          # gh copilot 執行器
│   └── setup-auth.sh            # 認證設定工具（host 端）
├── agents/                      # Agent 角色定義
│   └── default/
│       ├── instructions.md      # 角色系統指示
│       └── config.json          # 角色設定
├── auth/                        # 認證檔案（gitignored）
├── data/                        # 狀態持久化（state.json）
└── workspace/                   # Agent 工作區
```

---

## 自訂角色

在 `agents/` 下建立新目錄：

```
agents/
├── default/
│   ├── instructions.md
│   └── config.json
└── coder/                  # 新角色
    ├── instructions.md     # 角色的系統指示
    └── config.json         # {"model": "", "extra_flags": ""}
```

然後在 Issue 上加 label `role:coder`，Agent 就會使用該角色的 instructions 執行。

---

## 運作原理

1. **輪詢**：每 `POLL_INTERVAL` 秒取得 repo 所有 open issues
2. **偵測新活動**：比對每個 Issue 的最新 comment 時間與 `state.json` 中的記錄
3. **執行**：有新活動時，組合 issue 內容 + 角色 instructions 為 prompt，呼叫 `gh copilot -p "..." --yolo --no-ask-user --output-format json`
4. **回寫**：將 Agent 輸出作為 comment 回寫到 Issue
5. **更新狀態**：記錄已處理時間，下次輪詢跳過無新活動的 Issue
