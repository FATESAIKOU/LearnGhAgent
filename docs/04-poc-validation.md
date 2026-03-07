# 04 - PoC 驗證報告

## 總結

| PoC | 項目 | 結果 |
|-----|------|------|
| A | gh CLI (issue list / api / comment) | PASS |
| B | gh copilot 非互動模式 | PASS |
| C | Python subprocess + timeout | PASS |
| D | gh issue comment 回報 | PASS |
| E | Docker 完整流程 | PASS |

---

## PoC-A：gh CLI 操作

**目的**：確認 `gh issue list`、`gh api`、`gh issue comment` 等 CLI 指令可正常運作。

**測試指令**：
```bash
gh issue list --repo fatesaikou/LearnGhAgent
gh api repos/fatesaikou/LearnGhAgent/issues/1
gh api repos/fatesaikou/LearnGhAgent/issues/1/comments
```

**結果**：PASS — 所有指令皆正常回傳 JSON 資料。

---

## PoC-B：gh copilot 非互動模式

**目的**：確認 `gh copilot` 可在非互動模式下執行，支援 `-p`、`--yolo`、`-s`、`--no-ask-user` 等 flag。

**測試指令**：
```bash
gh copilot -p "Reply with exactly: Hello from Agent!" --yolo -s --no-ask-user
```

**結果**：PASS — 回覆 "Hello from Agent!"，無互動提示。

---

## PoC-C：Python subprocess + timeout

**目的**：確認 Python `subprocess.run()` 可控制 gh copilot 執行並正確處理 timeout。

**測試腳本** (`poc/test_subprocess.py`)：
```python
import subprocess, time

# 正常執行
result = subprocess.run(
    ["gh", "copilot", "-p", "Reply with exactly: Hello from subprocess!",
     "--yolo", "-s", "--no-ask-user"],
    capture_output=True, text=True, timeout=60
)
print(f"stdout: {result.stdout.strip()}")
print(f"returncode: {result.returncode}")

# Timeout 測試
try:
    subprocess.run(["sleep", "10"], timeout=3)
except subprocess.TimeoutExpired:
    print("TimeoutExpired caught correctly")
```

**結果**：PASS
- 正常執行：約 11.7 秒完成，正確取得輸出
- Timeout：`TimeoutExpired` 例外正確被捕獲

---

## PoC-D：gh issue comment 回報

**目的**：確認可透過 `gh api` 對 Issue 發表留言。

**測試指令**：
```bash
gh api repos/fatesaikou/LearnGhAgent/issues/1/comments \
  -f body="PoC test comment from agent"
```

**結果**：PASS — Issue #1 成功新增留言。

---

## PoC-E：Docker 完整流程

**目的**：確認在 Docker container 內可完成 auth → gh CLI → gh copilot 全流程。

### 遭遇問題與解決方案

#### 問題 1：Colima DNS 失敗
- **現象**：container 內無法解析外部 domain
- **解法**：`colima stop && colima start` 重啟

#### 問題 2：macOS Keychain auth 無法在 container 使用
- **現象**：本機 `gh auth` token 存在 macOS Keychain，`hosts.yml` 無 token 欄位
- **解法**：用 `gh auth token` 取得 token，產生含 `oauth_token` 的 `auth/hosts.yml`（已加入 .gitignore）
- **格式**：必須使用舊版單帳號格式（非 multi-user `users:` 格式），否則 gh CLI config migration 會報錯

```yaml
github.com:
    oauth_token: gho_xxxx
    git_protocol: https
    user: FATESAIKOU
```

#### 問題 3：gh CLI config migration 需要可寫目錄
- **現象**：直接 mount 為 `/root/.config/gh/hosts.yml:ro` 會因 config migration 寫入失敗
- **解法**：mount 為 `/auth-src:ro`，entrypoint 時 copy 到可寫位置

```bash
mkdir -p /root/.config/gh
cp /auth-src/hosts.yml /root/.config/gh/hosts.yml
chmod 600 /root/.config/gh/hosts.yml
```

#### 問題 4：gh copilot CLI 安裝需要互動式 TTY
- **現象**：Container 內首次執行 `gh copilot` 會提示 "Would you like to install?"，無 TTY 時靜默失敗
- **嘗試過的方案**：`echo "y" | gh copilot`、`yes | gh copilot`、環境變數、expect — 皆不穩定
- **最終解法**：在 Dockerfile build 階段直接 curl 下載 copilot binary

### 最終 Dockerfile

```dockerfile
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    curl git jq ca-certificates gnupg python3 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=...] ..." \
    > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# gh copilot CLI — 直接下載，跳過互動式安裝
RUN mkdir -p /root/.local/share/gh/copilot \
    && curl -sL "https://github.com/github/copilot-cli/releases/latest/download/copilot-linux-arm64.tar.gz" \
       -o /tmp/copilot.tar.gz \
    && tar xzf /tmp/copilot.tar.gz -C /root/.local/share/gh/copilot \
    && chmod +x /root/.local/share/gh/copilot/copilot \
    && rm /tmp/copilot.tar.gz
```

**關鍵發現**：
- Copilot binary 來源是 `github/copilot-cli` repo（非 `github/gh-copilot`，後者是舊版 Go suggest/explain 工具）
- 下載 URL：`https://github.com/github/copilot-cli/releases/latest/download/copilot-{platform}-{arch}.tar.gz`
- 版本 1.0.2，134MB 解壓後（內含 Node.js runtime），支援 `-p`、`--yolo`、`--agent` 等完整功能

### 最終驗證

```bash
docker run --rm \
  -v "$(pwd)/auth/hosts.yml:/auth-src/hosts.yml:ro" \
  gh-agent-poc bash -c '
    mkdir -p /root/.config/gh
    cp /auth-src/hosts.yml /root/.config/gh/hosts.yml
    chmod 600 /root/.config/gh/hosts.yml
    gh auth status
    gh copilot -- --version
    gh copilot -p "Reply with exactly: Hello from Docker!" --yolo -s --no-ask-user
  '
```

**輸出**：
```
✓ Logged in to github.com account FATESAIKOU
GitHub Copilot CLI 1.0.2.
Hello from Docker!
```

**結果**：PASS

---

## 設計影響整理

PoC 驗證結果對基本設計產生以下影響：

| 項目 | 原設計假設 | PoC 發現 | 需調整 |
|------|-----------|---------|--------|
| Auth | 直接 mount hosts.yml | 需 ro mount + copy | entrypoint.sh 加入 copy 邏輯 |
| Copilot 安裝 | Runtime 安裝 | Build time 下載 | Dockerfile 加入 curl 下載步驟 |
| expect | 可能需要 | 不需要 | 從 apt-get 移除 |
| copilot-cli 來源 | `github/gh-copilot` | `github/copilot-cli` | 修正 Dockerfile 與文件 |
| hosts.yml 格式 | 新版 multi-user | 舊版 single-account | auth 產生腳本需注意格式 |
