# opencode 的 skill／agent 系統：發現、載入與跨工具對比

> 本報告解析 opencode（`anomalyco/opencode`）的 skill／agent 系統：skill 如何被發現與載入、skill 與 command／plugin 的關係，並對比 Claude Code 的 skill 載入機制。原始碼以 `dev` 分支為準（預設分支），文件以官方 docs 為準。

---

## 1. 這個技術解決什麼問題？

**opencode 的 skill／agent 系統解決的是「AI coding agent 的能力如何被結構化地擴充、發現與觸發」的問題。**

具體子問題：

- **能力擴充缺乏標準載入機制**：使用者想讓 agent 具備特定領域知識或工作流（如「查第二大腦」「做 code review」），需要一套可重複、可版本化的方式把「指令＋知識」餵給 agent，而不是每次手動貼 prompt。
- **能力發現缺乏統一入口**：agent 需要知道「現在有哪些能力可用、各自做什麼」，才能在使用者提出需求時自動選用正確的能力。
- **能力觸發缺乏可控性**：能力該在什麼條件下被自動叫用、什麼條件下只能手動叫，需要一套權限與觸發規則，避免 agent 亂叫或漏叫。
- **跨工具可攜性**：同一份 skill 知識能否在不同 agent（opencode、Claude Code、Codex 等）之間共用，避免每換一個工具就重寫一遍。

opencode 的答案：以 **skill** 為能力載體，以 **目錄掃描＋frontmatter** 為發現機制，以 **system context 注入**為觸發入口，並以 **command／plugin** 作為不同層級的能力擴充形式。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 LLM agent 的「能力」本質上是 prompt 工程

LLM 本身沒有「安裝能力」的概念——它只有一個 context window。要讓 agent「會做某件事」，本質是把「怎麼做這件事的指令＋相關知識」放進它的 context。因此「能力擴充」在工程上就變成「**如何把一段可重複使用的指令＋知識，在正確的時機注入 context**」。這是 skill 系統要解決的根本約束。

### 2.2 早期做法是「把一切塞進 system prompt」

最早的 agent 把能力寫死在 system prompt 或 AGENTS.md 裡。問題：

| 做法 | 限制 |
|---|---|
| 全部塞進 system prompt | 長度爆炸、無法按需載入、改一個能力要動整個 prompt |
| 每次手動貼指令 | 不可重複、不可版本化、遺漏率高 |
| 單一 AGENTS.md | 只能承載靜態規則，無法承載「可被自動發現的動態能力集」 |

### 2.3 需要「可發現、可觸發、可攜」的能力抽象

當能力數量從幾個成長到幾十個（如 mattpocock 22 個、superpowers 13 個），就必須有：

- **發現**：agent 開機時掃描哪些目錄，知道有哪些能力
- **描述**：每個能力用 frontmatter（name／description）自我描述，供 agent 判斷何時該用
- **觸發**：能力被注入 system context 後，agent 依描述自行決定是否叫用
- **可攜**：能力以「目錄＋SKILL.md」的檔案形式存在，可跨工具複製

### 2.4 通用技術背景

- **Agent 工具抽象**：skill 是「工具（tool）抽象」的一種，與 MCP、function calling 同屬「把能力暴露給 LLM」的家族。
- **Context 注入**：skill 的載入本質是「把 skill 內容注入 system context」，與 RAG、system prompt 注入同屬「context 工程」。
- **生態碎片化**：不同 agent（Claude Code、opencode、Codex、Cursor）各自定義 skill 格式，催生了「共用目錄（`~/.agents`）＋symlink」的相容做法。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 整體架構：三層能力擴充

opencode 把能力擴充分成三層，各自有獨立的發現路徑與觸發方式：

```
┌─────────────────────────────────────────────────────────────┐
│  Skill（能力載體）                                            │
│  ─ 目錄 + SKILL.md（frontmatter: name/description）          │
│  ─ 發現：掃描多個目錄 → 注入 <available_skills> system context│
│  ─ 觸發：agent 依 description 自行決定叫用                    │
├─────────────────────────────────────────────────────────────┤
│  Command（slash 指令）                                       │
│  ─ 目錄 + *.md（或 JSON 的 command 欄位）                    │
│  ─ 發現：掃描 {command,commands}/**/*.md                     │
│  ─ 觸發：使用者手動打 /command-name                          │
├─────────────────────────────────────────────────────────────┤
│  Plugin（外掛）                                              │
│  ─ 目錄 + 設定檔 / npm 套件                                  │
│  ─ 發現：掃描 plugins 目錄 / 全域 plugin 目錄 / npm           │
│  ─ 觸發：經 ctx.skill.transform() 注入 skill source          │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Skill 的發現與載入（核心機制）

**發現路徑**（app 層 `packages/opencode/src/skill/index.ts` 實作）：

```
掃描來源（依序）：
1. ~/.claude/skills/**/SKILL.md        （Claude Code 相容，symlink:true）
2. ~/.agents/skills/**/SKILL.md        （共用目錄，symlink:true）
3. 專案 up-walk 的 .claude/skills、.agents/skills
4. .opencode/{skill,skills}/
5. config.skills.paths / config.skills.urls（url 走 index.json pull）
```

**載入流程**：

```
啟動
  │
  ▼
掃描上述目錄，glob 匹配 {*.md, **/SKILL.md}
  │
  ▼
解析 frontmatter（app 層認 name + description；core 層另認 slash）
  │
  ▼
依 agent permission 過濾（SkillV2.available()，deny 則隱藏）
  │
  ▼
注入 <available_skills> 到 system context
  │
  ▼
agent 依 description 判斷是否叫用（tool/skill.ts 載入時再 assert）
```

**frontmatter 欄位**：

| 層級 | 認的欄位 | 說明 |
|---|---|---|
| app 層 `isSkillFrontmatter` | `name`、`description` | 最小可辨識集合 |
| core 層 `SkillV2` | `name`、`description`、`slash` | 另支援 slash 觸發 |
| docs 另列 | `license`、`compatibility`、`metadata` | 文件層的擴充欄位 |

**source 型別**（core 層 `packages/core/src/skill.ts`）：`directory`、`url`、`embedded` 三種。`url` 型別透過 `index.json` 拉取遠端 skill 集。

### 3.3 Skill 與 Command 的關係

| 面向 | Skill | Command |
|---|---|---|
| 載體 | 目錄 + `SKILL.md` | 目錄 + `*.md`（或 JSON `command` 欄位） |
| 發現目錄 | `.claude/skills`、`.agents/skills`、`.opencode/skills`、config paths/urls | `.opencode/commands/`（`{command,commands}/**/*.md`） |
| 觸發方式 | agent 依 description 自動叫用 | 使用者手動打 `/command-name` |
| 是否吃 `~/.agents` | **是**（原生掃描） | **否**（只掃自身設定目錄） |

> 關鍵差異：**skill 原生讀 `~/.agents`，command 不讀。** 這是 2026-08-04 日誌實測確認的——command 必須靠 symlink 才能共用 `~/.agents/commands/`。

### 3.4 Skill 與 Plugin 的關係

Plugin 是更高層的擴充形式，可把 skill 作為其一部分注入：

```
Plugin（.opencode/plugins/、全域 plugin 目錄、npm 套件）
  │
  └─ ctx.skill.transform()  →  注入 skill source
```

即 plugin 可以「包裝」skill，在載入時對 skill source 做轉換（transform），再注入給 agent。skill 是能力的最小單位，plugin 是能力的組合／包裝層。

### 3.5 虛擬碼

```
def discover_skills():
    sources = []
    if not disable_claude_code_skills:
        sources.append(".claude")
    sources.append(".agents")
    for src in sources:
        scan(join(home, src), "skills/**/SKILL.md", {dot:true, scope:"global"})
    # + 專案 up-walk、.opencode/{skill,skills}、config.skills.paths/urls

def load_skill(skill):
    fm = parse_frontmatter(skill.SKILL.md)   # name, description, [slash]
    if not SkillV2.available(fm, agent_permission):  # deny 則隱藏
        return None
    return inject_to_system_context(fm)      # <available_skills>

def discover_commands():
    return scan(config_dir, "{command,commands}/**/*.md")  # 不吃 ~/.agents

def load_plugin(plugin):
    return ctx.skill.transform(plugin.skill_sources)  # 包裝/轉換後注入
```

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

> 本節對照第二大腦（FATESAIKOU/MyBrain）的既有判定。查到的判定標 GitHub URL 與信任層級；AI draft 註明「未經他 review」。

### 4.1 第二大腦對照

| 主題 | 第二大腦判定 | 信任層級 | 來源 |
|---|---|---|---|
| opencode 本體 | 試用（「大致堪用，Ollama 整合帶來自由度避免綁定」） | human:fatesaikou, stable | [OpenCode.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OpenCode.md) |
| skill／command 探索路徑 | 已實測：skill 原生讀 `~/.agents`、command 不讀 | human:fatesaikou, stable | [2026-08-04 日誌](https://github.com/FATESAIKOU/MyBrain/blob/main/日誌/2026-08-04.md) |
| agent-skills（工程紀律 skill 框架） | 採用（「可以拿來構築私有的小產品開發流程」） | human:fatesaikou, stable | [agent-skills.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/agent-skills.md) |
| mattpocock skills | 採用（個人開發對齊主力） | claude-code/opus-5, draft（實測檔） | [AI開發workflow實測.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/AI開發workflow實測.md) |
| superpowers | Reserve（團隊場景才划算） | claude-code/opus-5, draft（實測檔） | [AI開發workflow實測.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/AI開發workflow實測.md) |
| OpenSpec | 採用（長期沈澱主力） | claude-code/opus-5, draft（實測檔） | [AI開發workflow實測.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/AI開發workflow實測.md) |
| 技術取捨準則 | 理解優先、MVP→Feature 閘門、約束在 harness | claude-code/opus-5, **draft（未經他 review）** | [技術取捨準則.md](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md) |

> ⚠️ **衝突提示**：技術取捨準則（AI draft）主張「約束放在 harness 不放權限」——即 agent 的約束應靠驗證機制（測試、validator、CI）而非人工審核關卡。這與 opencode 的 skill 權限機制（`SkillV2.available()` 依 permission 過濾、deny 則隱藏）**方向一致**：兩者都傾向「用機制約束而非人工把關」。但該準則為 AI draft，未經他 review，轉述時需標註。

### 4.2 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Claude Code Skills** | 掃描 `~/.claude/skills/**/SKILL.md`，frontmatter 描述，注入 system context | 需 Claude Code 環境；skill 需符合其 frontmatter 格式 | 與 opencode 的 skill 格式相容（opencode 原生讀 `~/.claude/skills`）；command 需 symlink 才能共用 | 能力可被自動發現與觸發；與 opencode 共用同一份 skill 知識 |
| **MCP（Model Context Protocol）** | 標準化工具協定，agent 透過 MCP server 暴露工具 | 需 MCP server 實作；需 agent 支援 MCP 協定 | 比 skill 更重（需 server 進程）；工具是「呼叫式」而非「注入式」 | 跨 agent 標準化工具介面；適合需要真實執行的工具 |
| **superpowers（流程強制 skill 集）** | 用硬規則（HARD-GATE、強制 TDD、兩階段 review）封死 agent 偷懶路徑 | 需完整流程骨架；團隊場景才划算 | 個人開發成本高（$0.12/28 subagent）；排除 `using-superpowers` 後不會自動觸發 | 單次交付高品質；但長期沈澱不整合 |
| **OpenSpec（規格沈澱）** | 以 `openspec/specs/` 累積系統真相，delta-first 規格管理 | 需 `openspec init`；需每步打指令 | 7 個指令要自己記得打（實測顯示每步會提示下一步，弱點不成立） | 長期沈澱整合；三個月後讀 specs 就有系統答案 |

### 4.3 切入點差異

- **opencode skill vs Claude Code skill**：兩者格式相容（opencode 原生讀 `~/.claude/skills`），差異在發現路徑——opencode 額外原生讀 `~/.agents/skills`，command 則兩者都需 symlink 才能共用 `~/.agents/commands/`。
- **skill vs MCP**：skill 是「注入式」能力（把指令＋知識放進 context），MCP 是「呼叫式」工具（agent 呼叫 server 執行）。skill 適合知識型能力，MCP 適合需要真實執行的工具。
- **skill vs superpowers**：skill 是能力載體，superpowers 是「用 skill 組成的強制流程」。superpowers 的價值在流程強制，但個人開發時「執行者就是自己盯著的 agent」，流程強制假設不成立。
- **skill vs OpenSpec**：skill 是能力抽象，OpenSpec 是「規格沈澱」的 workflow。opencode 的 skill 系統解決「能力怎麼載入」，OpenSpec 解決「開發流程怎麼沈澱」。

### 4.4 對照第二大腦的結論

- 第二大腦對 opencode 的判定是「試用」（堪用、Ollama 自由度），本報告的 skill 載入機制分析**不與該判定衝突**，而是補足其未涵蓋的「skill 載入機制」細節。
- 第二大腦對 skill 生態的判定（mattpocock 採用、superpowers Reserve、OpenSpec 採用）**與本報告的 skill 系統分析一致**——opencode 的 skill 系統正是承載這些 skill 集的載入機制。
- 技術取捨準則（AI draft）的「約束在 harness」與 opencode 的 skill 權限機制方向一致，但該準則未經他 review，僅作參考。

---

## 附錄：資料來源

- 原始碼：`anomalyco/opencode`（`dev` 分支），`packages/core/src/skill.ts`、`packages/opencode/src/skill/index.ts`、`config/plugin/skill.ts`、`plugin/skill.ts`
- 官方文件：docs 的 skills／agents／commands.mdx
- 第二大腦：`技術/技術評估/OpenCode.md`、`日誌/2026-08-04.md`、`技術/動手做/AI開發workflow實測.md`、`技術/技術評估/agent-skills.md`、`抽象理解/本質洞察/技術取捨準則.md`
