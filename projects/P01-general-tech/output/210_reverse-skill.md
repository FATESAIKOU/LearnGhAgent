# reverse-skill 分析報告

> 調研標的：zhaoxuya520/reverse-skill（GitHub）
> 定位：逆向工程／授權滲透測試／安全研究的 Skill 路由包
> 版本：v1.0.1；stars：22,268；license：MIT（CTF-Sandbox-Orchestrator 子模組為 GPLv3）
> 主要語言：PowerShell；預設分支：main；建立 2026-05-13，更新 2026-08-09（活躍）

---

## 1. 這個技術解決什麼問題？

**reverse-skill 解決的問題：AI coding agent 在面對逆向／滲透／安全研究任務時，不知道該用哪套方法論與工具、也不知道該按什麼順序執行，只能「猜指令」的問題。**

具體而言，當一個 AI agent（Claude Code、Codex、Cursor、OpenCode 等）收到一個 APK、一個二進位檔、前端 JS 加密參數、一個 CTF 題目、或一個滲透測試目標時，它需要決定：

- 該用 jadx、apktool、Frida、IDA 還是 BurpSuite？
- APK、ELF、JS、PCAP、CTF 各自需要不同的 playbook，該走哪一條？
- 工具、MCP server、script 散落在不同機器上，怎麼知道本機有哪些可用？
- 同樣的錯誤反覆發生，因為經驗沒有被重複利用。

reverse-skill 宣稱以「AI 自動路由 + 按需自舉工具鏈 + 自動進化經驗庫」來解決上述問題：把任務路由到正確的方法論、檢查可用工具、執行可重複的工作流，而不是讓 agent 猜指令。

**模糊之處**：README 的「路由」是**規則式（關鍵字計分）**而非語意式——它依賴 `routing.json` 的關鍵字正規表示式命中來選 PRIMARY。這代表它解決的是「已知任務型態的分流」，而非「理解任意新任務」。此外「自動進化經驗庫」的實際閉環機制（經驗如何被寫回、由誰 review）在 README 中未詳細展開，需看 `field-journal/` 與 ops 契約才能確認。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景（README「Why this exists」）

- AI agent 不知道某個任務該用 jadx、apktool、Frida、IDA 還是 BurpSuite
- APK、ELF、JS、PCAP、CTF 任務各自需要不同的 playbook
- 工具、MCP server、script 散落在不同機器上
- 同樣的錯誤反覆發生，因為經驗沒有被重複利用

### 通用技術背景（文章未明確提及，但為必要脈絡）

- **逆向／安全領域的工具多樣性與專業性**：逆向工程與滲透測試的工具鏈極度分散（靜態分析、動態 hook、網路抓包、漏洞利用、CTF 各有專屬工具），且每個工具都有陡峭的學習曲線。這使得「選對工具」本身就是一項專業知識，LLM 的統計式知識不足以穩定選對。
- **AI agent 的「猜指令」問題**：LLM 對工具名稱與用法有模糊記憶，但缺乏「本機實際裝了什麼、版本為何、該按什麼順序跑」的確定性資訊。在安全場景，猜錯指令可能導致誤判（false positive）或浪費大量時間。
- **工具環境的機器差異**：逆向工具（IDA、Frida、jadx）與滲透工具（nmap、BurpSuite）的可用性高度依賴作業系統與安裝狀態。Windows、Linux、Kali 的環境差異大，agent 無法憑空知道本機狀態。
- **經驗不可重複利用**：安全研究是高度經驗導向的工作，但經驗通常存在個人腦中或散落的筆記，沒有結構化沉澱，導致每次任務都從零開始。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 整體行為鏈

reverse-skill 定義了一條從任務到報告的固定執行鏈：

```
User task
  → RULES.md
  → MASTER-ROUTING / master-route.ps1 (PRIMARY)
  → case-init / scope.md (auth + network_profile; no target ACT until ready)
  → Scenario skill → tools / MCP / scripts
  → timeline + Evidence→Finding→Path → report + field-journal
```

### 3.2 路由核心：單一事實源 + 計分路由

- `skills/config/routing.json` 是**路由的單一事實源**，含 41 條規則（R0–R40）。每條規則定義 `label`、對應的 `skill`、以及一組關鍵字（`must`／`exclude`／`mustAll`）。
- `master-route.ps1` 讀取 routing.json，依關鍵字命中計分選出 PRIMARY：每條規則命中後計入候選集，按 priority 順序取「命中分數最高」者為 PRIMARY；分數並列時 priority 靠前者勝出；未命中任何規則時回退到 fallbackId（R0）。
- `verify-routing-coherence.ps1` 校驗 routing.json 與 `MASTER-ROUTING.md` 的優先級表一致，防止文件與設定漂移。

**路由規則範例（routing.json）：**

| 規則 | label | 對應 skill | 關鍵字（節錄） |
|---|---|---|---|
| R1 | APK reverse | `apk-reverse/SKILL.md` | `\bapk\b\|smali\|jadx\|apktool\|android\|反编译.?apk\|root.?检测\|pinning.?绕过` |
| R2 | Mobile reverse | `mobile-reverse/SKILL.md` | `\bipa\b\|ios.?reverse\|objection\|mobsf\|越狱`（越狱 裸詞分 iOS，LLM 語境歸 R14） |
| R3 | JS / frontend reverse | `js-reverse/SKILL.md` | `js.?reverse\|webpack\|cryptojs\|encrypted.?param\|抓包\|请求.?重放` |
| R6 | IDA reverse | `ida-reverse/SKILL.md` | `\bida\b\|decompile\|disassembl\|\.so\b\|\.elf\b\|jni` |
| R9 | Malware analysis | `malware-analysis/SKILL.md` | `malware\|yara\|ransomware\|webshell\|backdoor` |
| R10 | Attack chain | `attack-chain/SKILL.md` | `attack.?chain\|red.?team\|lateral\|内网.?渗透\|红队` |
| R11 | Pentest tools | `pentest-tools/SKILL.md` | `nmap\|nuclei\|sqlmap\|burp\|metasploit\|hashcat\|提权` |
| R14 | LLM / Agent security | `llm-security/SKILL.md` | `llm\|prompt.?inject\|jailbreak\|提示词.?注入\|模型.?越狱` |

### 3.3 工具管理：tool-index 為單一事實源

- `skills/tool-index.md` 記錄本機已偵測到的工具狀態（自動生成）。
- `refresh-tool-index.ps1`（Windows）／`refresh-tool-index.sh`（Linux/macOS）／`kali/scripts/refresh-tool-index.sh`（Kali）依平台掃描並生成工具索引。
- 缺工具時按 manifest 自舉（bootstrap），但**未 pin 的自動安裝會失敗**（supply-chain pin gate），確保工具來源可追溯。

### 3.4 案例工作流與授權門禁

- `case-init.ps1` 建立案例目錄（scope / timeline / workitems）。
- `RULES.md` 定義全域規則：**在 scope 就緒前不得對目標 ACT**（auth + network_profile 門禁），避免未授權掃描。
- `skills/case-review/` 提供唯讀的 Evidence graph review 與 artifact fixity 檢查，確保證據鏈可追溯。

### 3.5 品質保證與 client-neutral

- 163 個回歸測試案例（`test-routing.ps1`），任何路由變更若造成 hint→expected PRIMARY 不匹配即 CI 失敗。
- GitHub Actions 在 **Windows + Ubuntu** 上跑全部測試。
- 路由核心、回歸套件、manifest、案例工作流**不綁定特定 AI client**；Claude Code、Codex、Cursor、OpenCode 透過各自的 adapter 或 project-instruction 機制載入，client 特定設定為選用且不進入核心路由契約。

### 3.6 支援場景（節錄）

APK/Android、iOS/mobile、Binary reverse（exe/dll/so/elf）、.NET/C#、前端 JS/加密參數、DSL VM/自訂 opcode VM、HTTP 抓包/重放、Malware/YARA、滲透測試/掃描、攻擊鏈/紅隊編排、案例證據審查/報告交接、CTF（42 個子 skill）、Firmware/IoT、Patch diff/N-day、Pwn/exploit 開發、EDR bypass、API/GraphQL、供應鏈/SBOM、LLM/AI 安全、OLLVM 去混淆。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

> 本節對照第二大腦 FATESAIKOU/MyBrain 的既有判定。reverse-skill 本身在第二大腦中**無任何評估紀錄**（Step 1 已確認），屬全新標的。以下替代方案均為第二大腦已評估過、且與「AI agent 路由／安全任務自動化」相關的標的。

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 使用前提 | 副作用 / 限制 | 預期效果 |
|---|---|---|---|---|
| **Strix**（usestrix/strix） | LLM Agent + 隔離沙箱 + 工具鏈 + 多 Agent 協作，模擬真實駭客行為動態執行程式碼、發現弱點並以 PoC 驗證 | Python ≥3.11、Docker、LLM API key；目標需可網路連線 | **token 消耗大**（依測試面向差異極大）；需 Docker 沙箱；LLM API 成本 | 端到端自動化滲透測試並產出可操作修補建議；**第二大腦判定：Accept**，想接 Ollama Cloud 掃 Axross Recipe |
| **PentestGPT**（GreyDGL/PentestGPT） | 三模組（Reasoning/Generation/Parsing）分工 + Pentesting Task Tree（PTT）結構化全域脈絡，LLM 驅動滲透流程 | LLM provider；目標需可網路連線 | 需維護全域脈絡；LLM 推理延遲；v1.0 agentic 模式綁定 claude CLI | 以任務樹維持全域脈絡，降低單一 LLM session 的 context loss；**第二大腦判定：未判定**（僅分析報告，無採用結論） |
| **agent-skills**（addyosmani/agent-skills） | 24 個 skill（23 lifecycle + 1 meta）+ 4 個專家 persona + hooks，以 7 命令 × 6 階段（DEFINE→PLAN→BUILD→VERIFY→REVIEW→SHIP）約束 AI coding agent 的工程紀律 | 支援 skill 機制的 AI client | 內嵌 Google 工程文化，非安全領域專用；需 client 支援 skill 載入 | 讓 agent 走完整工程生命週期而非跳過紀律；**第二大腦判定：Accept**，可拿來構築私有小產品開發流程 |
| **OmniRoute** | 本機開源 AI 網關，單一 OpenAI 相容 Endpoint 統一 250+ LLM Provider，18 種路由策略 + Token 壓縮 + 三層 Resilience | 本機執行；需 LLM provider | 是「LLM Provider 解耦層」，非「任務→方法論路由」；不處理安全工具選擇 | 解耦應用與 Provider 依賴，統一 Endpoint 自由切換；**第二大腦判定：Accept**，本質是解耦層，有學習必要 |

### 4.2 切入點差異

- **Strix**：從「執行」切入——直接跑滲透測試並驗證弱點，是**端到端安全測試 agent**，不是路由包。與 reverse-skill 可互補（reverse-skill 路由到方法論，Strix 實際執行）。
- **PentestGPT**：從「全域脈絡維持」切入——用任務樹解決 LLM 在長流程中的 context loss。與 reverse-skill 的「任務分流」是不同層次的問題。
- **agent-skills**：從「工程紀律」切入——約束 agent 的開發流程，非安全領域專用。與 reverse-skill 同屬「skill 包」形式，但領域不同。
- **OmniRoute**：從「Provider 解耦」切入——解決「接哪個 LLM」，而非「該做什麼任務」。與 reverse-skill 的「任務路由」是不同抽象層。

### 4.3 第二大腦對照與衝突

| 面向 | 第二大腦既有判定 | 本報告結論 | 衝突？ |
|---|---|---|---|
| reverse-skill 本身 | **無評估紀錄**（Step 1 確認） | 全新標的，本報告為首次分析 | 無衝突（查不到，明寫沒有） |
| Strix | **Accept**（`技術/技術評估/Strix.md`，`human:fatesaikou`，stable）；動手做「學習 Strix」記錄 token 消耗大 | 列為替代方案，指出其「執行導向」與 reverse-skill「路由導向」互補 | 無衝突；但**注意**：Strix 的 token 消耗痛點（動手做紀錄）正是 reverse-skill 想用「路由＋工具索引」緩解的方向 |
| PentestGPT | **未判定**（`技術/技術評估/PentestGPT.md`，`process:learning-agent`，stable） | 列為替代方案，指出其「脈絡維持」切入點 | 無衝突（未判定＝無結論可衝突） |
| agent-skills | **Accept**（`技術/技術評估/agent-skills.md`，`human:fatesaikou`，stable） | 列為替代方案，指出同屬 skill 包形式但領域不同 | 無衝突 |
| OmniRoute | **Accept**（`技術/技術評估/OmniRoute.md`，`opencode/deepseek-v4-pro`，**draft**，未經 review） | 列為替代方案，指出其「Provider 解耦」與 reverse-skill「任務路由」不同層 | 無衝突；但 OmniRoute 判定為 **AI draft**，引用時需註明未經本人 review |

**與技術取捨準則的對照**（`抽象理解/本質洞察/技術取捨準則.md`，`claude-code/opus-5`，**draft**）：

- **理解優先原則**：reverse-skill 是「現成的路由包」，依準則一，若使用者對其「不夠熟悉或不夠穩定」，會傾向**先自己兜**一個理解本質，而非直接採用。這與「用現成的比較快」的論證相抵——快不是重點，理解才是。
- **MVP→Feature 唯一閘門**：reverse-skill 是否進 Feature，唯一判準是「能否影響個人 workflow」。使用者目前的安全研究 workflow 以 Strix（滲透）為主，reverse-skill 的逆向路由是否進入日常，需先做 MVP 驗證。
- **Reject ≠ 沒價值**：即使 reverse-skill 不採用，其「路由單一事實源 + 計分路由 + 工具索引 + 回歸測試」的設計方向仍可被抽取，作為自兜路由包的參考。
- **汰換看上游死沒死**：reverse-skill 目前活躍（2026-08-09 更新），不構成汰換條件。

**衝突點**：無直接衝突。但需指出——reverse-skill 的「路由包」定位與使用者已 Accept 的 Strix（執行導向）在**抽象層不同**：reverse-skill 解決「該做什麼」，Strix 解決「怎麼執行」。若使用者想用 reverse-skill 取代 Strix，會是層次錯置；兩者應視為互補而非替代。

---

## 附錄：資料來源

- README.md（raw）：https://raw.githubusercontent.com/zhaoxuya520/reverse-skill/main/README.md
- routing.json：https://raw.githubusercontent.com/zhaoxuya520/reverse-skill/main/skills/config/routing.json
- repo metadata：`gh repo view zhaoxuya520/reverse-skill`
- 第二大腦：`技術/技術評估/判定總表.md`、`技術/技術評估/Strix.md`、`技術/技術評估/PentestGPT.md`、`技術/技術評估/agent-skills.md`、`技術/技術評估/OmniRoute.md`、`抽象理解/本質洞察/技術取捨準則.md`、`技術/動手做/學習 Strix.md`、`技術/動手做/LearnGhAgent.md`
