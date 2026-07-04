# Strix — 開源 AI 滲透測試 Agent

> 調研日期：2026-07-04 | 版本：v1.0.4 (Alpha) | 授權：Apache-2.0 | Stars：35K

---

## 1. 這個技術解決什麼問題？

**Strix 解決的問題：應用程式安全性測試（Application Security Testing）的自動化與準確性不足。**

具體來說，傳統做法存在三個無法同時滿足的缺口：

| 缺口 | 描述 |
|---|---|
| **手動滲透測試成本高、週期長** | 專業滲透測試人員稀缺，一次完整測試需數天至數週，無法跟上 CI/CD 迭代節奏 |
| **靜態分析工具（SAST）假陽性過高** | SAST 不執行程式碼，僅做模式匹配，產出大量誤報，開發者需花時間人工驗證 |
| **動態掃描工具（DAST）缺乏驗證能力** | 傳統 DAST 掃描器（如 Nessus、OpenVAS）只能「發現」潛在弱點，無法「驗證」該弱點是否真正可被利用 |

Strix 的宣稱：以 AI agent 模擬真實駭客行為，動態執行程式碼、發現弱點、並透過實際 PoC（Proof-of-Concept）驗證，同時產出可操作的修補建議。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 軟體開發節奏的演變

- **2010s 之前**：瀑布式開發，安全測試在 release 前集中進行，有足夠時間做人工滲透測試
- **2010s 之後**：CI/CD、DevOps、每日多次部署成為常態，安全測試必須嵌入 pipeline，時間壓縮到分鐘級
- **2020s**：AI 輔助程式碼生成（Copilot、Cursor 等）大幅提升開發速度，但安全測試速度未同步提升，形成「寫得快、測得慢」的剪刀差

### 2.2 既有工具的先天限制

| 工具類型 | 代表 | 限制 |
|---|---|---|
| **SAST（靜態分析）** | SonarQube, Semgrep, CodeQL | 不執行程式碼，只能做 pattern matching；無法發現邏輯漏洞（如 IDOR、race condition）；假陽性率 20-50% |
| **DAST（動態掃描）** | Nessus, OpenVAS, Nuclei | 發送預定義 payload，只能檢測已知簽章；無法做多步驟攻擊鏈；無法理解業務邏輯 |
| **人工滲透測試** | 紅隊演練 | 成本高（$5K-$50K+ per engagement）、週期長（1-4 週）、無法 scale |

### 2.3 LLM 的出現改變了可能性

- GPT-4 / Claude 等模型展現了「理解程式碼語義 + 推理攻擊路徑 + 生成 exploit」的能力
- 但 LLM 本身是 stateless 的對話模型，缺乏「操作真實環境」的工具介面
- 需要一個框架將 LLM 的推理能力與實際的滲透測試工具鏈（瀏覽器、代理、shell、sandbox）橋接起來

> 以上 2.1-2.3 為通用技術背景，非 Strix 文件明確提及。

---

## 3. 這個技術是如何解決該問題的？

Strix 的核心機制是 **「LLM Agent + 隔離沙箱 + 工具鏈 + 多 Agent 協作」** 四層架構。

### 3.1 整體架構

```
┌─────────────────────────────────────────────────────┐
│                   使用者 CLI                         │
│  strix --target ./app                               │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Agent Orchestrator (root agent)          │
│  - 解析目標、建立 scope context                       │
│  - 動態 spawn 子 agent（recon / exploit / post）      │
│  - 協調 agent 間訊息傳遞                              │
└────┬────────────┬────────────┬───────────────────────┘
     │            │            │
┌────▼───┐  ┌────▼───┐  ┌────▼───┐
│ Recon  │  │Exploit │  │ Post   │  ← 子 agent（specialist）
│ Agent  │  │Agent   │  │Agent   │
└───┬────┘  └───┬────┘  └───┬────┘
    │           │           │
┌───▼───────────▼───────────▼─────────────────────────┐
│                工具層 (Tools)                         │
│  agent_browser │ shell │ proxy (Caido) │ web_search  │
│  apply_patch  │ notes │ todo │ view_image           │
│  load_skill   │ thinking │ reporting │ finish        │
└───┬─────────────────────────────────────────────────┘
    │
┌───▼─────────────────────────────────────────────────┐
│              Docker 沙箱 (Sandbox)                    │
│  - 隔離執行環境，避免對宿主機造成影響                    │
│  - 內建 Caido proxy、Python runtime、瀏覽器            │
│  - 支援 local source mount                           │
└─────────────────────────────────────────────────────┘
```

### 3.2 Agent 提示詞系統（Skill 機制）

Strix 使用 **Jinja2 模板 + 動態 skill 載入** 來組合 system prompt，而非寫死單一提示詞。

**流程**（`strix/agents/prompt.py`）：

```
使用者指定 scan_mode（quick / standard / deep）
  │
  ▼
_resolve_skills() 決定 skill 載入順序：
  1. 使用者指定的 skills（若有）
  2. scan_modes/<mode>（強制）
  3. tooling/agent_browser（強制）
  4. tooling/python（強制）
  5. coordination/root_agent（僅 root agent）
  6. coordination/source_aware_whitebox（僅 whitebox 模式）
  │
  ▼
load_skills() 讀取對應 .md 檔案內容
  │
  ▼
Jinja2 渲染 system_prompt.jinja，將 skill 內容注入模板
```

**Skill 目錄結構**（`strix/skills/`）：

```
skills/
├── scan_modes/        # 掃描模式定義
│   ├── deep.md
│   ├── quick.md
│   └── standard.md
├── coordination/      # agent 協作指引
│   ├── root_agent.md
│   └── source_aware_whitebox.md
├── tooling/           # 工具使用說明
│   ├── agent_browser.md
│   ├── python.md
│   ├── nuclei.md
│   ├── sqlmap.md
│   ├── nmap.md
│   ├── subfinder.md
│   ├── httpx.md
│   ├── katana.md
│   ├── naabu.md
│   ├── ffuf.md
│   └── semgrep.md
├── reconnaissance/    # 偵察技能
├── vulnerabilities/   # 漏洞利用技能
├── frameworks/        # 框架特定技能
├── protocols/         # 協定特定技能
├── technologies/      # 技術棧特定技能
├── cloud/             # 雲端安全技能
└── custom/            # 自訂技能
```

### 3.3 多 Agent 協作（AgentCoordinator）

`strix/core/agents.py` 中的 `AgentCoordinator` 是核心協調器：

| 功能 | 實作方式 |
|---|---|
| **Agent 註冊** | `register(agent_id, name, parent_id)` 建立 agent 樹狀結構 |
| **狀態管理** | 每個 agent 有 `running / waiting / completed / stopped / crashed / failed` 狀態 |
| **訊息傳遞** | `send(target_id, message)` 將訊息寫入目標 agent 的 SDK session |
| **等待機制** | `wait_for_message()` + `asyncio.Event`，agent 在無訊息時 park |
| **預算控制** | `trigger_budget_stop()` 全域停止，超過 USD 預算時觸發 |
| **快照/恢復** | `snapshot()` / `restore()` 序列化整個 agent 圖狀態，支援 resume |

**協作流程範例**：

```
1. Root agent 收到目標
2. Root agent spawn Recon agent → Recon agent 執行 subdomain enumeration
3. Recon agent 發現新子域名 → 發送訊息給 Root agent
4. Root agent spawn Exploit agent → Exploit agent 對子域名執行 SQL injection 測試
5. Exploit agent 找到注入點 → 產出 PoC → 發送給 Reporting agent
6. Reporting agent 生成 CVSS 評分 + 修補建議
```

### 3.4 沙箱執行環境

Strix 使用 Docker 容器作為隔離執行環境（`strix/runtime/`）：

```
strix/runtime/
├── backends.py          # 後端抽象（Docker / 其他）
├── caido_bootstrap.py   # Caido proxy 初始化
├── docker_client.py     # Docker SDK 封裝
└── session_manager.py   # session 生命週期管理
```

- 每個 scan 建立一個獨立的 Docker container
- 內部執行 Caido（HTTP 代理）、Python sandbox、瀏覽器
- 支援 local source code mount（whitebox 模式）
- scan 結束後自動 cleanup

### 3.5 工具鏈（13 個內建工具）

| 工具 | 用途 |
|---|---|
| `agent_browser` | Playwright 驅動的瀏覽器自動化（XSS、CSRF、點擊劫持測試） |
| `shell` | 容器內 shell 執行（命令注入、post-exploitation） |
| `proxy` | Caido HTTP 代理（請求/回應攔截與修改） |
| `web_search` | 網路搜尋（OSINT、漏洞情報收集） |
| `apply_patch` | 自動產生並套用修補程式 |
| `load_skill` | 動態載入新 skill |
| `notes` | agent 筆記本（跨 agent 共享發現） |
| `todo` | 待辦事項管理 |
| `thinking` | 結構化思考鏈 |
| `view_image` | 截圖檢視 |
| `reporting` | 發現報告生成 |
| `finish` | 掃描結束與最終報告輸出 |
| `agents_graph` | 子 agent 管理（spawn / stop / list） |

### 3.6 執行流程（`strix/core/runner.py`）

```
run_strix_scan()
  │
  ├─ 建立 run directory + state directory
  ├─ 載入設定（load_settings）
  ├─ 初始化 AgentCoordinator
  ├─ 建立或復用 Docker sandbox session
  ├─ 建立 root agent（build_strix_agent）
  ├─ 註冊 root agent 到 coordinator
  ├─ 建立 child agent factory（make_child_factory）
  ├─ 開啟 root SDK session
  ├─ 如果是 resume：respawn_subagents()
  ├─ 執行 run_agent_loop()
  │   ├─ agent 接收 initial_input（root_task）
  │   ├─ agent 決定下一步動作（呼叫工具 / spawn 子 agent / 發送訊息）
  │   ├─ 子 agent 執行完成後回報結果
  │   └─ 重複直到 finish_scan 被呼叫或 max_turns 耗盡
  └─ cleanup：關閉 session、移除 sandbox
```

### 3.7 弱點驗證方式

Strix 與傳統掃描器的關鍵差異在於「驗證」：

```
傳統掃描器：
  發送 payload → 檢查 response 是否包含特定字串 → 報告「可能存在漏洞」

Strix：
  發送 payload → 檢查 response → 若懷疑存在漏洞 → 撰寫 Python PoC script
  → 在 sandbox 中執行 PoC → 確認漏洞是否真實可利用 → 產出含 PoC 的報告
```

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Burp Suite Pro + 擴充** | 手動/半自動滲透測試平台，搭配 Intruder/Repeater/Scanner 模組，可加裝 Extender 擴充（如 Autorize、Backslash Powered Scanner） | 需安裝 Java runtime；專業版 $449/year；需具備滲透測試知識 | 自動化程度低，仍需大量人工操作；無 LLM 輔助推理；擴充品質參差不齊 | 深度人工測試的黃金標準，但無法 scale 到 CI/CD 場景 |
| **Nuclei + ProjectDiscovery 生態** | YAML 模板驅動的弱點掃描器，社群維護數千模板，支援 HTTP/DNS/SSL/TCP 等多協定 | 需撰寫/維護 YAML 模板；無執行環境隔離 | 模板只能檢測已知模式，無法做邏輯推理；無 PoC 驗證；假陽性需人工過濾 | 快速大規模掃描，適合 CI/CD 閘道，但缺乏深度驗證 |
| **Semgrep + CodeQL（SAST）** | 靜態程式碼分析，Semgrep 以 pattern matching 為主，CodeQL 以資料流分析為主 | 需定義安全規則（Semgrep）或編寫 QL 查詢（CodeQL）；需原始碼存取 | 不執行程式碼，無法發現執行時期漏洞（如 SSRF、IDOR）；假陽性率高 | 在開發階段早期發現程式碼層級弱點，適合 shift-left，但無法取代動態測試 |
| **OpenAI GPT / Claude 直接使用** | 直接將程式碼或網頁內容餵給 LLM，要求 LLM 分析安全性 | 需手動提供 context；無工具鏈整合；無隔離執行環境 | LLM 可能 hallucinate 漏洞；無法實際驗證；無結構化報告；token 成本不可控 | 快速獲得初步安全意見，但不可靠且不可重複 |
| **PentestGPT** | LLM agent 迭代式滲透測試，v1.0 升級為 agentic 模式（Claude Code CLI 驅動），legacy 模式支援多 LLM provider | 需安裝 Claude Code CLI（agent 模式）或設定 API key（legacy 模式）；無內建沙箱 | 依賴 Claude Code 的 sandbox 而非自有隔離環境；agent 模式僅支援 Claude；無內建弱點掃描工具鏈（如 nuclei/sqlmap） | 在 LLM 推理層面與 Strix 同級，但缺乏自有工具鏈與沙箱，實際攻擊能力受限 |

### 4.2 切入點差異分析

```
                    ┌─────────────────────┐
                    │   自動化程度         │
                    │  高 ←────────→ 低   │
                    └──────┬──────────────┘
                           │
    Strix ─────────────────┤ (LLM agent 全自動)
    Nuclei ────────────────┤ (模板驅動，需人工撰寫模板)
    Semgrep ───────────────┤ (規則驅動，需人工定義規則)
    Burp Suite ────────────┤ (平台，需人工操作)
    GPT direct ────────────┤ (無框架，需人工引導)
                           │
                    ┌──────┴──────────────┐
                    │   驗證深度           │
                    │  高 ←────────→ 低   │
                    └─────────────────────┘
    Strix ─────────────────┤ (PoC 執行驗證)
    Burp Suite ────────────┤ (人工驗證)
    Nuclei ────────────────┤ (無驗證，僅檢測)
    Semgrep ───────────────┘ (無驗證)
    GPT direct ────────────┤ (無驗證，LLM 推測)
```

### 4.3 Strix 的獨特定位

Strix 的切入點是 **「LLM Agent + 工具鏈 + 沙箱」** 的組合，這使得它與既有工具不在同一競爭維度：

- 相較於 Nuclei / Semgrep：Strix 不是規則/模板驅動，而是 LLM 推理驅動，能發現未知模式漏洞
- 相較於 Burp Suite：Strix 是全自動的，不需要人工操作，但深度不如人工測試
- 相較於直接使用 LLM：Strix 提供了工具鏈（瀏覽器、代理、shell）和隔離環境，讓 LLM 能實際「操作」目標而非僅「分析」文字

**Strix 的弱點**（基於架構推測，非官方文件）：

| 面向 | 推測的限制 |
|---|---|
| **LLM 成本** | 每次 scan 消耗大量 token（尤其是 deep mode），長期運作成本可能高於傳統工具 |
| **LLM 幻覺** | LLM 可能產生不存在的漏洞或錯誤的 PoC，雖然沙箱執行可過濾部分，但無法完全避免 |
| **速度** | LLM 推理延遲（數秒至數十秒）遠高於規則引擎（毫秒級），大規模掃描效率低 |
| **可重複性** | LLM 輸出非確定性，同一目標兩次 scan 結果可能不同 |
| **覆蓋面** | 依賴 LLM 的知識邊界，對於極新或極冷門的漏洞類型可能無法覆蓋 |

### 4.4 Strix vs PentestGPT 對照

| 面向 | Strix | PentestGPT |
|---|---|---|
| 建立時間 | 2025-08-05 | 2023-02-27 |
| Stars | 35.5K | 14.1K |
| License | Apache-2.0 | MIT |
| 核心語言 | Python | Python |
| 架構 | 多 Agent（root/recon/exploit/post）+ Docker sandbox | 單 Agent iteration loop + Claude Code CLI |
| 沙箱 | Docker 容器（內建 Caido proxy、瀏覽器、Python runtime） | 無獨立沙箱（依賴 Claude Code 的 sandbox） |
| 工具鏈 | 13 個內建工具（browser/shell/proxy/search 等） | 依賴 Claude Code 內建工具 |
| 多 LLM 支援 | 是（OpenAI/Anthropic/Google/Vertex/Bedrock/Azure/本地） | 是（legacy 模式支援 8+ provider；agent 模式僅 Claude） |
| 弱點驗證 | PoC 執行驗證（sandbox 中執行 Python exploit） | 依賴 LLM 推理判斷（無獨立 PoC 執行層） |
| 學術背景 | 無（開源專案） | USENIX Security 2024 論文 |
| 安裝方式 | curl 腳本 / pip | git clone + make install |
| CI/CD 整合 | GitHub Actions workflow 範例 | 無明確 CI/CD 範例 |
| 收費模式 | 開源 + 雲端平台（app.strix.ai） | 開源（MIT） |

**是否重造輪子的判斷**：Strix 與 PentestGPT 在「LLM agent 驅動滲透測試」的抽象概念上相同，但實作層級有顯著差異：

| 主張 | 反證 |
|---|---|
| 兩者都是「LLM 問答 + 工具執行」的 loop | Strix 實作多 Agent 協作架構（root/recon/exploit/post），PentestGPT 為單 Agent 迭代；Strix 有自有 Docker 沙箱與 13 個內建工具，PentestGPT 依賴 Claude Code 生態 |
| 兩者都支援多 LLM provider | PentestGPT agent 模式僅支援 Claude，legacy 模式雖支援多 provider 但功能受限；Strix 所有模式皆支援多 provider |
| 兩者都是開源 | Strix 為 Apache-2.0，PentestGPT 為 MIT，授權不同 |
| 兩者都做滲透測試 | Strix 強調 PoC 執行驗證（sandbox 中實際執行 exploit），PentestGPT 依賴 LLM 推理判斷，驗證深度不同 |

**結論**：Strix 與 PentestGPT 在「LLM agent 驅動」的抽象層面屬於同類，但在架構深度（多 Agent vs 單 Agent）、工具鏈自有程度（13 內建工具 vs 依賴 Claude Code）、驗證機制（PoC 執行 vs LLM 推理）三個維度上有實質差異，不構成單純的「重造輪子」。

---

## 5. User Q&A

### Q1：Strix 與 PentestGPT 有何區別？是不是重造輪子？

**A**：不是單純的重造輪子。兩者在「LLM agent 驅動滲透測試」的抽象概念上同類，但在三個實作維度上有顯著差異：

| 維度 | Strix | PentestGPT | 差異是否實質 |
|---|---|---|---|
| **架構** | 多 Agent 協作（root/recon/exploit/post），AgentCoordinator 管理狀態與訊息傳遞 | 單 Agent iteration loop，依賴 Claude Code CLI 的 agent 模式 | 是 — 多 Agent 架構允許分工與平行執行，單 Agent 只能序列操作 |
| **工具鏈** | 13 個內建工具（browser/shell/proxy/nuclei/sqlmap/nmap 等），自有實作 | 依賴 Claude Code 內建工具，無自有工具鏈 | 是 — 自有工具鏈不受 LLM provider 限制，且可精確控制工具行為 |
| **驗證機制** | PoC 執行驗證：在 Docker sandbox 中實際執行 Python exploit 確認漏洞 | 依賴 LLM 推理判斷漏洞是否存在，無獨立 PoC 執行層 | 是 — 執行驗證可過濾 LLM 幻覺產生的假漏洞，PentestGPT 無此過濾層 |
| **沙箱** | 自有 Docker 容器（內建 Caido proxy、瀏覽器、Python runtime） | 無自有沙箱，依賴 Claude Code 的 sandbox | 是 — 自有沙箱可精確控制環境、支援 local source mount、獨立於 LLM provider |
| **多 LLM 支援** | 所有模式皆支援 OpenAI/Anthropic/Google/Vertex/Bedrock/Azure/本地 | agent 模式僅 Claude，legacy 模式支援多 provider 但功能受限 | 部分 — PentestGPT legacy 模式功能較弱 |
| **學術背景** | 無 | USENIX Security 2024 論文 | 非功能差異 |

**反證表**（若主張「是重造輪子」需回答的問題）：

| 若主張「重造輪子」 | 需解釋 |
|---|---|
| 為何 Strix 需要實作自有 Docker 沙箱而非直接使用 Claude Code sandbox？ | PentestGPT 選擇依賴 Claude Code，Strix 選擇自建，兩者架構決策不同 |
| 為何 Strix 需要實作 13 個內建工具而非使用 Claude Code 內建工具？ | PentestGPT 的工具能力受限於 Claude Code 提供的工具集 |
| 為何 Strix 需要實作多 Agent 協調器而非單 Agent loop？ | 單 Agent loop 無法平行執行偵察與利用任務 |
| 為何 Strix 需要 PoC 執行驗證層？ | PentestGPT 無此層，LLM 幻覺產生的假漏洞無法被過濾 |

**結論**：Strix 與 PentestGPT 在抽象層面同類，但在架構深度、工具鏈自有程度、驗證機制三個維度有實質差異，不構成單純的「重造輪子」。

### Q2：實際上如何一步一步執行 Strix？（給指令）

**A**：以下為完整執行流程，從安裝到進階使用。

#### 前置需求

| 項目 | 版本要求 | 說明 |
|---|---|---|
| Python | >= 3.11 | Strix 執行環境 |
| Docker | 最新版 | 沙箱執行環境 |
| LLM API Key | 依 provider 而定 | OpenAI / Anthropic / Google 等 |

#### Step 1：安裝

```bash
# 方式一：curl 安裝腳本（推薦）
curl -fsSL https://raw.githubusercontent.com/usestrix/strix/main/install.sh | bash

# 方式二：pip 安裝
pip install strix

# 驗證安裝
strix --version
```

#### Step 2：設定 LLM Provider

```bash
# 設定環境變數（以 Anthropic Claude 為例）
export ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx

# 或寫入設定檔
strix config set provider anthropic
strix config set model claude-sonnet-4-20250514
```

#### Step 3：基本掃描（Blackbox 模式）

```bash
# 掃描一個公開網址（無原始碼存取）
strix --target https://example.com

# 指定掃描模式
strix --target https://example.com --mode quick    # 快速掃描（~5 分鐘）
strix --target https://example.com --mode standard # 標準掃描（~15 分鐘）
strix --target https://example.com --mode deep     # 深度掃描（~30+ 分鐘）
```

#### Step 4：Whitebox 模式（有原始碼）

```bash
# 掛載本地原始碼目錄
strix --target ./my-app --whitebox

# 指定語言框架（加速分析）
strix --target ./my-app --whitebox --framework django
```

#### Step 5：進階使用

```bash
# 指定輸出目錄
strix --target https://example.com --output ./reports

# 設定預算上限（USD）
strix --target https://example.com --budget 5.0

# 指定自訂 skill
strix --target https://example.com --skills custom/my_skill.md

# 恢復中斷的掃描
strix --resume ./strix_runs/scan_2025xxxx/
```

#### Step 6：CI/CD 整合（GitHub Actions）

```yaml
# .github/workflows/strix-scan.yml
name: Strix Security Scan
on:
  push:
    branches: [main]
jobs:
  strix:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Strix
        uses: usestrix/strix-action@v1
        with:
          target: ${{ github.workspace }}
          whitebox: true
          mode: quick
          api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

#### 注意事項

| 事項 | 說明 |
|---|---|
| **首次執行** | 第一次執行會自動 pull Docker image（約 1-2 GB），需等待數分鐘 |
| **Token 消耗** | quick mode 約 50K-100K tokens，deep mode 可達 500K+ tokens |
| **掃描時間** | 取決於 LLM 延遲與目標複雜度，quick mode 約 5 分鐘，deep mode 可達 1 小時 |
| **Docker 權限** | 確保執行使用者有 Docker 權限（`docker ps` 可正常執行） |
| **網路要求** | 沙箱需要網路存取目標，若目標在內網需確保 Docker 可到達 |
