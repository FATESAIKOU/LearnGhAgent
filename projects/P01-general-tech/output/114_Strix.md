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
