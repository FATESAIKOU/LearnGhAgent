# 46_R2_step2-plan_C1.md

## 狀況理解

R2 使用者追問三個實作導向問題：(1) PentestGPT 能否接 Ollama Cloud 訂閱 (2) 能否針對 Docker Compose 服務測試 (3) 若可，提供完整逐步指令。R1 報告已有 §5 初步回答，但需從原始碼層級驗證關鍵細節。本 step 針對這三個問題收集原始碼證據。

## 執行的動作與結果

| 動作 | 目的 | 預期效果 | 實際結果 |
|------|------|----------|----------|
| `gh api repos/GreyDGL/PentestGPT` | 取得 repo metadata | 確認 stars/forks/license/語言 | 13,941 stars, 2,422 forks, Python, MIT, 60 open issues |
| 擷取 README.md | 確認 Ollama 支援宣告與 CLI 用法 | 確認文件層級支援度 | README 明確列出 Ollama 支援（legacy 模式），`pentestgpt-legacy --reasoning-model ollama:qwen3` |
| 擷取 `pentestgpt_legacy/llm/registry.py` | 確認 Ollama 在 LLM registry 中的實作 | 確認 Ollama 是否為一等公民 provider | Ollama 定義為 `kind="openai"`，`base_url="http://localhost:11434/v1"`，`requires_key=False`，支援動態 `ollama:<model>` 解析 |
| 擷取 `pentestgpt/core/backend.py` | 確認 v1.0 agentic 模式的 LLM 後端實作 | 確認是否可換後端 | `ClaudeCodeBackend` 硬編碼呼叫 `claude` CLI subprocess，註解標明 `OpenAIBackend`/`LocalLLMBackend` 為 future |
| 擷取 `pentestgpt/interface/main.py` | 確認 `--target` 參數的格式驗證 | 確認是否接受 IP:port | `--target` 為 `type=str`，無格式驗證，無目標位址過濾 |
| 擷取 `Dockerfile` + `docker-compose.yml` | 確認 Docker 環境的工具鏈與網路設定 | 確認容器內工具可用性 | 容器內預裝 nmap/curl/netcat/wget/openvpn；`host.docker.internal` 已設定；支援 NET_ADMIN + /dev/net/tun |
| 擷取 `entrypoint.sh` | 確認 Docker 的 auth 模式與 CCR 配置 | 確認 Docker 內能否代理 LLM 請求 | 支援 openrouter/local/anthropic/manual 四種 auth 模式；CCR 可將 Claude Code 代理到 OpenAI-compatible 端點 |
| 擷取 `.env.example` | 確認 Ollama 環境變數 | 確認 `OLLAMA_BASE_URL` 是否為官方支援 | `.env.example` 註解中明確列出 `OLLAMA_BASE_URL` |
| 讀取 R1 報告 `output/46_PentestGPT.md` | 回顧已產出的 §5 Q&A | 確認哪些問題已回答、哪些需補充 | §5 已有 Q1-Q3 完整回答，但部分原始碼證據可補充強化 |

## 動作結束後的現狀

| 驗證面向 | 驗證內容 | 結果 |
|----------|----------|------|
| Q1：Ollama Cloud 支援 | v1.0 agentic 後端是否可換 | **不可直接換** — `ClaudeCodeBackend` 硬編碼 `claude` CLI，無其他實作 |
| Q1：Ollama Cloud 支援 | Legacy 模式是否支援 Ollama | **支援** — registry 中 Ollama 為一等公民 provider，`kind="openai"`，可設 `OLLAMA_BASE_URL` |
| Q1：Ollama Cloud 支援 | Docker + CCR 能否代理 | **可** — entrypoint.sh 支援 openrouter/local 模式，CCR 可代理到任意 OpenAI-compatible 端點 |
| Q2：Docker Compose 目標 | `--target` 是否接受 IP:port | **接受** — `type=str` 無格式驗證 |
| Q2：Docker Compose 目標 | 是否有目標位址過濾 | **無** — 原始碼中無任何 IP/hostname 過濾邏輯 |
| Q2：Docker Compose 目標 | 容器內工具鏈是否完整 | **完整** — nmap/curl/netcat/wget/openvpn 已預裝 |
| Q3：逐步指令 | R1 報告 §5 Q3 是否已涵蓋 | **已涵蓋** — A 路線（v1.0+Docker）與 B 路線（Legacy+Ollama Cloud）均已提供 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|----------|----------|----------|----------|
| Q1 查證範圍 | (a) 只看 README (b) 看 registry.py + backend.py | (b) | README 只說「支援 Ollama」，但未區分 v1.0 agentic 與 legacy 模式。需看原始碼確認 v1.0 是否真的不支援 |
| Q2 查證範圍 | (a) 只看 CLI 文件 (b) 看 main.py 的 argparse 實作 | (b) | 文件可能未列出所有參數限制，需看原始碼確認 `--target` 是否有隱含格式驗證 |
| Q3 是否重寫指令 | (a) 沿用 R1 §5 Q3 (b) 重新撰寫更詳細版本 | (a) | R1 §5 Q3 已提供完整 A/B 路線逐步指令，無需重複。Step 3 QA 時確認是否需補充原始碼引用 |
