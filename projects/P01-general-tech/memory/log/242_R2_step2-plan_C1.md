# 242_R2_step2-plan_C1.md

## 狀況理解

R2 意圖＝以「Provider 廣度 + 免費額度」為主軸對照 Switchyard vs OmniRoute，並各給 claudecode / opencode 的落地安裝手順（見 R2 Step 1）。本 sub-step C1 專注「取得兩套 repo 的最新 metadata 與安裝/整合文件」，不重做 R1 的功能分析。

關鍵背景修正：R1 引用第二腦「OmniRoute 250+ Provider」是 2026-07 舊快照。實際 OmniRoute repo 已更新，廣度數字與安裝方式都不同，C1 需以最新 repo 事實為準，並標註與第二腦判定（draft）的差異。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view NVIDIA-NeMo/Switchyard` | 取得 Switchyard 最新 metadata | 拿到 stars/license/分支/更新時間 | 2218★、Apache-2.0、default `main`、2026-08-22 更新；pre-alpha |
| webfetch Switchyard README + getting_started + core_concepts + CHANGELOG | 抓官方安裝路徑與 TOML 設定 | 確認 server 安裝與 endpoint | 見下方「現狀 A」 |
| `gh search repos OmniRoute` | 定位 OmniRoute 真身 repo（非 FATESAIKOU/MyBrain 內檔） | 找到官方 repo URL | `diegosouzapw/OmniRoute`，default branch `release/v3.8.50` |
| `gh repo view diegosouzapw/OmniRoute` | 最新 metadata | 廣度與版本更新 | 53231★、MIT、53k stars、340 providers/90+ free/1200+ models |
| webfetch OmniRoute README + CLI-INTEGRATIONS + OPENCODE + CLAUDE-CODE-CONFIGURATION | 取得 claudecode/opencode 官方整合命令 | 產出準確安裝 config | 見下方「現狀 B」 |

## 動作結束後的現狀

**現狀 A — Switchyard（NVIDIA-NeMo/Switchyard，2218★，Apache-2.0，pre-alpha）**
- 無內建 Provider 目錄、無免費額度聚合。它是「路由器」，必須由使用者手寫 TOML 指定上游 client（`base_url` + `api_key_env`）+ target + route。
- 官方安裝：`cargo install --locked switchyard-server` → 寫 `routes.toml` → `switchyard-server --config routes.toml --host 127.0.0.1 --port 4000`。
- 對 claudecode/opencode 的承接：server 同時吃 OpenAI Chat / OpenAI Responses / Anthropic Messages 三種 endpoint。**openocode 走 OpenAI 相容** → `base_url=http://localhost:4000/v1`；**claude code 講 Anthropic Messages** → `ANTHROPIC_BASE_URL=http://localhost:4000`（**不可加 `/v1`**），auth 用 `forward_auth=true` 或 `api_key_env` + 對應 token。
- 0.2.0 CHANGELOG 已移除 Python `switchyard launch` / launcher CLI，只留 native Rust `switchyard-server`。使用者連「claudecode/opencode 整合」只能手動接 proxy，無一鍵 setup。
- pre-alpha：README 明示「Not for production use」、API 到 v1.0 前還會大改。

**現狀 B — OmniRoute（diegosouzapw/OmniRoute，53231★，MIT，release/v3.8.50）**
- 廣度大幅超前 R1/二腦快照：**340 Provider / 90+ free / 1200+ models / 43 provider pools / ~1.53B 免費 token/月**（README hero 亦見 290 providers 舊數，以最新 description 340 為準）。
- 原生整合命令（本次關鍵）：
  - 安裝：`npm install -g omniroute` → `omniroute`（boot localhost:20128），零 config，`auto` 即用。
  - **opencode**：`omniroute setup-opencode`（寫 `~/.config/opencode/opencode.json`，provider `omniroute`，`npm:@ai-sdk/openai-compatible`，baseURL `http://localhost:20128/v1`）；或 `@omniroute/opencode-provider`。
  - **claude code**：`omniroute setup-claude`（寫 `~/.claude/profiles/<name>/settings.json`）＋`omniroute launch --profile <name>`（注入 `ANTHROPIC_AUTH_TOKEN`）；或手動 `ANTHROPIC_BASE_URL=http://localhost:20128`（無 `/v1`）。
- 對照重點：OmniRoute 的「廣度」是**內建聚合**（免費 provider pool），Switchyard 的「廣度」是**使用者的手動 route 清單**——兩者不在同一層比較。

**對照資料缺口：**
- OmniRoute 文件需再讀「Quick Start / setup 指引」（C2）以產出最終一一步驟；Switchyard 需補「claude code/opencode 指到 port 4000 的實際 config 範本」（C2）。
- OmniRoute repo 極大（README 被截斷），provider 清單細節於 C2 依 `PROVIDER_REFERENCE` 補。

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| OmniRoute 真身 | FATESAIKOU/MyBrain 內文 vs **官方 repo diegosouzapw/OmniRoute** | 用官方 repo | 安裝手順只能取自官方；二腦只有評估文檔無官方整合文件 |
| 廣度數字來源 | 沿用 R1 二Brain「250+」vs 最新官方「340/1200+」 | 採最新官方 | R1 是 2026-07 快照，已過期；C1 抓到 live metadata |
| OmniRoute 分支 | main vs release/v3.8.50 | 用 release/v3.8.50 | `gh repo view` 顯示 defaultBranch 為 release/v3.8.50，raw 文件據此抓取 |
| C1 深度 | 只抓 README vs README+getting_started+核心config | 抓安裝/整合專用文件 | 本輪是「安裝手順」，需要 CLI/config 而非重複路由演算法 |
| Provider 廣度是否為「同層比較」 | 直接比數字 vs 標註層級差異 | 標註層級差異 | Switchyard 無 Provider 目錄，比較需先說明「內建聚合 vs 手動設定」的基準不同 |
