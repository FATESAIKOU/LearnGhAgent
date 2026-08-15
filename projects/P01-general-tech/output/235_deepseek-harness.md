# deepseek-harness（DeepSeek Harness, `dsh`）技術分析報告

> 標的：https://github.com/deepseek-ai/deepseek-harness
> 本報告為 R1 首次產出。所有對第二大腦（FATESAIKOU/MyBrain）的引用，皆標註信任層級與時間座標。

---

## 1. 這個技術解決什麼問題？

DeepSeek Harness（`dsh`）解決的問題是：**「把 AI agent 的執行骨架（harness）做成可插拔、可替換、可審計的開源框架」**——讓 agent 的核心機制（模型 adapter、工具登錄、session 記錄、agent loop 本身）不是被寫死成一個不可拆的產品，而是全部以 plugin 形式掛在一個共用的 context 上，每一層都能從設定檔替換。

更精確地拆成三層需求：

| 問題 | 描述 |
|---|---|
| **可替換** | 換模型、換工具、換沙箱、換 UI，都只是換掉一個 plugin／provider，不改動其他部分。架構文件明說「沒有需要打補丁的特權核心」 |
| **可審計** | session log 是「model 看得到的東西」的唯一來源；凡進入 model request 的輸入，都必須能從 log 重構，且有 runtime invariant 強制此不變式。這是要做到「重放（replay）與崩潰還原」的硬前提 |
| **可擴充** | 新能力透過「capability seam」加入——一個 seam 由 Service Definition（介面）、Service Provider（實作）、Consumer（常是 model-facing tool）三角色組成，三件套齊了才叫一個可替換的能力 |

**問題描述中可能含糊之處**：標題與 README 只說「open-source agent harness」，並未明確定義「harness」的邊界——它究竟指「能跑 agent 的完整產品」還是「agent 執行所需的基礎骨架」。從架構看，它偏向後者＋一個可選的 Web UI，但對外宣稱時兩者混用。此外「developer preview、會有破壞相容變更」這句，讓「當前可用性」的邊界也很模糊——你現在看到的是會變的狀態，不是穩定版本。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章明確提到的背景

- **Cordis 驅動**：`dsh` 由 [Cordis](https://github.com/cordiverse/cordis) 這個框架驅動，其設計論文題為《A Programming Paradigm for Spatiotemporal Composability》。Cordis 提供「plugins 貢獻 services、typed events、reversible effects 給一個共用 context」的模型——這是「一切皆 plugin」架構的來源。
- **developer preview 的迭代節奏**：README 用大寫強調「THERE WILL BE COMPATIBILITY-BREAKING CHANGES」，說明它目前正快速迭代，還不是穩定 API。
- **設計目標的自我描述**：架構文件開宗明義「沒有需要打補丁的特權核心：你靠把 plugin 掛在別的 plugin 旁邊來擴充 dsh，而 registration 是 effects，會在 plugin unload 時 unwind」。

### 2.2 通用技術背景（文章未明說，屬背景脈絡補足）

- **agent harness 的演化**：早期的 coding agent（如單體 CLI）把「模型呼叫、工具執行、session 管理、權限」全部綁死在一個程式裡。這帶來三個痛點：換模型要改產品、加工具要動核心、session 記錄與實際執行的可見輸入之間可能不一致（出問題難重放）。
- **可替換性的驅動力**：LLM provider 快速更替、工具生態爆炸，agent 若不能低代價換 provider，就會被綁死在特定供應商。`dsh` 的「adapter seam + provider 三件套」正是回應這個背景。
- **審計／重放的需求**：agent 是長時間、多步驟、會呼叫工具的執行體，若沒有「model 看到的全部都能從 log 重構」的不變式，就無法在 crash 後精確還原、也無法審計它為什麼這樣做。這是 agent 信任的基礎工程。
- **spatiotemporal composability**：Cordis 論文標題的這組詞，暗示它處理的是「在空間（哪些 plugin 掛在一起）與時間（lifecycle、unload、replay）上如何組合」的問題——這正是 plugin 系統最難的兩件事。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 核心：一切皆 plugin ＋ Cordis 的共用 context

`dsh` 的解法是把「產品的所有部分」都變成 plugin：**model adapter、tool registry、session log、agent loop 本身**都是 plugin。所以：

- 沒有「核心程式」需要改——要擴充或替換，就在其他 plugin 旁多掛一個 plugin。
- registration 是 **reversible effect**——plugin unload 時，其註冊會被 unwind，不留殘留狀態。

### 3.2 Profiles 與 Bundles：啟動時的組合層

一個運作中的 `dsh` 是一個 plugin tree，由 boot 時照**有序層次**組合而成：

| 概念 | 角色 |
|---|---|
| **profile** | 具名組合，放在 Harness home；列它疊的 bundles、裝的 out-of-tree plugins、使用者的 `cordis.patch.yml`。`web` 與 `headless` 是現成 template |
| **bundle** | Cordis config rows 與其掛載程式碼的分發格式；其內容可被上層 patch |

層次套用順序：每個 bundle（照 profile 所列順序）→ profile 的 `cordis.patch.yml` → home 層級 → 任何 `--patch` overlay。一個 patch 依 id 定位某 row 並整體取代其 config，或插入新 rows。

可執行 `dsh --profile web --dump-config` 看你這台機器實際 boot 出來的 tree——印出的任何 row 都可以用你自己的 patch 取代。

### 3.3 核心 packages

| Package | 掌管 | ctx key |
|---|---|---|
| `core/session` | append-only `SessionEvent` log 與 in-memory store | `ctx.sessions` |
| `core/system-prompt` | prompt-section 與 tool-schema 組裝 | `ctx.systemPrompt` |
| `core/tools` | scoped tool registry 與 guarded execution pipeline | `ctx.tools` |
| `core/agent` | `Agent` 介面、live registry、`agent/*` events | `ctx.agents` |
| `core/agent-loop` | 實作該介面的預設 driver | `ctx.agentLoop` |
| `core/scope` | per-agent scoped-registration 原語 | 無 key（library） |
| `llm/llm` | message 與 stream 詞彙＋adapter seam | `ctx.llm` |

### 3.4 事件域：擴充點的選域是第一決策

`dsh` 用事件當擴充點，選對域是多數修改的第一步：

| 事件域 | 特性 | 用途 |
|---|---|---|
| **session events** | durable facts，append 到 log 並經 `session/event` 廣播 | 事實需在 reload 後存活時用 |
| **agent events**（`agent/*`）| 帶 live `Agent`：inbox、step、status、request、validation、continuation | 觀察或攔截 in-flight work |
| **capability events** | 把 policy 與 adapters 附到 seam（`fs/*`、`tools/*`、`telemetry/*`）而不 import loop | 純附加策略 |

### 3.5 Turn flow：step 與 turn

- **step** = 一次 model request 加上它所呼叫的工具。
- **turn** = 零個或多個 step；在其第一個 input 被 claim 前開啟，在「不再欠任何東西」時關閉。

```text
turn/start
  claim next-step input plus one queued message
  assemble prompt sections + tool schemas
  -> agent/pre-step                   reject | enter(messages)
     reject, 或第一個 enter 被重寫成空 -> 關閉該 turn（花 0 個 step）
     step/start
     append entered messages as user/message
     derive model history from the log
     agent/request -> llm/stream -> assistant/chunk* -> assistant/message
     tool/call* -> tools/pre-execute -> tools/execute -> tools/post-execute -> tool/result*
     step/end
     tools 還欠另一個 request, 或 next-step input 到了 -> claim -> 下一個 step
  -> agent/turn-stopping
turn/end
```

關鍵點：`turn/*`、`step/*`、`user/message`、`assistant/*`、`tool/*` 是 **durable session events**；其餘是 live extension points。`agent/pre-step`、`agent/request`、`llm/stream`、三個 `tools/*` events 是 **waterfall**（listener 必須 call `next()` 來委派）；`agent/turn-stopping` 是 **serial** 且無 `next()`。

輸入經由單一 inbox 到達 driver：有些 message 立即喚醒它；injected context 先待在 inbox，等另一個 message 到才處理。`agent/pre-step` 決定 model 看到什麼——listener 可改寫被 claim 的 messages 或直接 reject 它們。

### 3.6 Session log：model 可見性的唯一來源

```
「Model-visible means logged.」
任何到達 model request 的輸入，都必須能從 log 重構，runtime invariant 強制此不變式。
```

- `deriveMessages()` 從 log 投影出 model history。
- 原始 `assistant/chunk` events 保留 replay 與 UI fidelity。
- Fork、resume、transcripts、telemetry、persistence 全都從這個 stream 衍生。
- **因此新增一個 model 可見的輸入，就必須新增一個 session event**（擴充 `SessionEventMap`），並從 log render。

### 3.7 Capability seams：替換一個 provider 改變整個產品

seam = 可替換能力，三角色：

```
Service Definition（宣告介面）
Service Provider（實作）
Consumer（使用它，通常是 model-facing tool）
```

一個 package 可同時擔任多個角色，但單一角色不構成 seam——要加能力就要設計齊三件套。**seam 之所以是重點**：filesystem 與 subprocess provider 共用一個執行世界，所以把它們指向 remote sandbox，會連帶把 Bash、PTY、LSP 一起搬走，不需 fork 各自的 provider。Subagent providers 也一樣——介面後面可以從「全新 child agent」到「在另一個產品委派 turn」，差異極大但藏在一個介面後。

### 3.8 「新行為往哪放」：一份機制對照表

| 目標 | 機制 |
|---|---|
| 加 model provider | 在 `ctx.llm` 註冊 adapter |
| 加 model-facing capability | 在 `ctx.tools` 註冊；其 schema 加入 prompt assembly |
| 給單一 session 不同能力集 | 組 agent preset；那裡的 service row 需要 `isolate` realm |
| 加 shell 執行 | 註冊 `ctx.shell` backend |
| 加 human command | 在 `ctx.commands` 註冊（無 model turn 就分發）|
| 加背景工作 | 在 `ctx.jobs` 註冊；`job_*` tools 收集或停止它 |
| 加檔案系統存取或 policy | 註冊 `ctx.fs` provider 或監聽 `fs/*` events |
| 限制 spawned processes | 用 `ctx.sandbox` backend |
| 攔截 request／tool／turn | 用對應 `agent/*` 或 `tools/*` event |
| 加 durable session state | 擴充 `SessionEventMap`，從 log render 與 replay |
| Fork 一個 live session | `ctx.sessions.fork(source, boundary?, childSessionId?)` |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

「解決類似問題」在此指：**提供 agent 執行骨架／讓 agent 的 memory/read/action/permission/verify 可被框架化**。以下對照第二大腦（FATESAIKOU/MyBrain）的既有判定，不只是照通則列。

### DA 表（技術名 / 技術解法 / 使用前提 / 使用副作用 / 預期效果）

| 技術 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **deepseek-harness（`dsh`）** | 一切皆 plugin，Cordis 共用 context＋reversible effects；session log 是 model 可見性的唯一來源；capability seam 三件套 | 接受 Node.js 生態、接受 Cordis 框架綁定、接受 developer preview 的破壞相容、接受「要懂事件域選域」的學習成本 | vendor 綁定 Cordis 的「plugin tree＋patch」組合模型；需為新 model 可見輸入新增 session event（框架強制）；框架較重，個人小專案可能過度工程化 | 換 provider／工具／沙箱低代價；session 可重放與審計；產品層可完全替換而不碰核心 |
| **opencode**（他正用） | AI 輔助編碼 CLI，可搭配 Ollama 使用多種模型；透過 Ollama 整合多模型後端避免綁定供應商 | 需要 CLI 驅動的 coding agent；接受 harness 與模型解耦 | harness 與模型層由不同廠商維護，介面以 base_url 對接（如 Muse Code drop-in）；約束放 harness | 已在他的日常 workflow，屬「已覆蓋需求」端 |
| **Muse Code**（Meta，2026-08-05 beta）| 長時程 async background agents、append-only local event log（crash 後 replay-exact）、`/plan`→`/grill`→`/goal` 規劃 skill、approval＋OS sandbox | 想要長時程背景 agent；接受 beta 未穩定 | 撞「不追新」＋「已覆蓋需求」；與現有 harness 高度重疊 | 見下：他判定**換 harness 暫緩**，僅模型層（Muse Spark 1.2）可 drop-in opencode 試 |
| **Qoder**（三層捆綁：模型聚合＋IDE＋Agent 框架）| 把多家模型包成 Credits 轉售＋Desktop/CLI＋Ask/Agent/Quest/Experts 執行模式 | 想要一個月費多用多家模型＋IDE 整合 | markup 藏在 Credits；供應商風險偏高；需求已被既有訂閱覆蓋 | 見下：他判定 **Reject** |
| **DeepSeek-Reasonix** | 最大化 DeepSeek prefix cache hit 的 AI agent 框架（ImmutablePrefix＋AppendOnlyLog 的 cache-first loop）| 有明確的 cache 成本結構需要最佳化 | 沒有成功率基線時，成本優化無從比較 | 見下：他判定 **Reject**（無成功率基線下成本優化無意義）|

### 切入點差異

- **`dsh` vs opencode**：`dsh` 的切入點是「把 harness 本體當 plugin 系統設計、以 session log 為唯一真相」，重的是**可重放審計與 provider 可替換**；opencode 的切入點是「CLI＋多模型後端解耦、約束放 harness」，更貼近終端 coding 的日常。
- **`dsh` vs Muse Code**：兩者都強調 append-only event log 與 replay，但 `dsh` 走向「可插拔 plugin 生態」，Muse Code 走向「長時程背景 agent＋規劃 skill」。
- **`dsh` vs Qoder**：Qoder 是「捆綁販售多模型＋IDE」，`dsh` 是「開源框架、provider 自己接」，二者是「商業產品」與「基礎框架」的不同切面。
- **`dsh` vs DeepSeek-Reasonix**：同屬 DeepSeek 開源生態，但 Reasonix 只做 prefix cache 成本最佳化單點，`dsh` 做整個 harness；Reasonix 的失敗教訓（無成功率基線的成本優化無意義）是評估同生態方案的對照。

### 第二大腦既有判定（§4 的對照依據）

| 標的 | 判定 | 信任層級 | 時間 | GitHub URL |
|---|---|---|---|---|
| **換 harness 的立場（Muse Code）** | 換 Muse Code harness **暫緩**——撞「不追新」＋「已覆蓋需求」（Kimi Code 同域 Reject 前例）＋ beta 未穩定；僅「Muse Spark 1.2 模型」可 drop-in opencode 試 | process:learn-gh-agent / draft（本 harness 自動產出，未經他 review） | 2026-08-15 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Muse%20Code.md |
| **Qoder** | **Reject**——無價格優勢（與直打 API 持平）、需求已被既有訂閱覆蓋（Ollama Cloud＋Anthropic）、供應商風險偏高 | human:fatesaikou / stable（`verified`） | 2026-08-09 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Qoder.md |
| **DeepSeek-Reasonix** | **Reject**——沒有成功率基線的保障下做成本優化沒有意義 | human:fatesaikou / stable | 2026-05-31 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/DeepSeek-Reasonix.md |

> ⚠️ **信任層級說明**：Muse Code 那份是 `process:learn-gh-agent` 產出的 **draft**（未經使用者 review），「換 harness 暫緩」是該草稿的結論，不是使用者本人拍板。Qoder 與 DeepSeek-Reasonix 是使用者本人（`human:fatesaikou`）且 Qoder 有 `verified`，可當成他的既定結論。Muse Code 若引用為「他的立場」需謹慎。

### 與他的技術取捨準則的對照

依據骨幹檔《技術取捨準則》（claude-code/opus-5 / **draft**，2026-08-01）：

| 準則 | 對 `dsh` 的意涵 |
|---|---|
| **理解優先**：不穩定或不熟悉就先自己兜，MVP 是理解的驗證點 | `dsh` 屬「不熟悉」＋ developer preview「不穩定」，依準則反而可能觸發「自己兜來理解本質」而非直接採用。它不是效率考量，是學習策略 |
| **MVP → Feature 唯一閘門**：能否影響個人 workflow | 要進 Feature，得先問「`dsh` 能否影響他日常的 agent workflow」——這是最強判準，不是技術優劣 |
| **Reject ≠ 沒價值**：被拒仍抽取需求理解與方案方向 | 即便 `dsh` 最終不採用，其「session log 是 model 可見性的唯一來源」與「capability seam 三件套」都是可抽取的方案方向 |
| **汰換看上游死沒死，不看有沒有更好** | 他不追新。`dsh` 才兩天大（見下時間），屬「新」而非「已死」，不會因「更好」就被換過去 |
| **Harness Engineering 五問**（human:fatesaikou / stable，2026-03-29）：memory / read / action / permission / verify | 可用此五問檢視 `dsh`：memory（session log＋replay）、read（scoped tool registry）、action（tool pipeline）、permission（`ctx.sandbox`＋approval）、verify（runtime invariant＋log 重構）。這是他的 agent 設計判準 |
| **約束在 harness，不在權限** | `dsh` 把 sandbox 與 approval 放 harness 層，與此一致；且不該建議加人工審核關卡，而該看它有沒有補驗證機制 |

> ⚠️ 《技術取捨準則》本身是 `draft`（claude-code/opus-5，2026-08-01），但內文大量引用他的原話（「先自己兜」「能跑就不動」「你怎麼知道自己做對了」）。引用準則時註明這是 AI 草稿整理，原話部分是他說的。

---

## 附錄：本輪 metadata

| 欄位 | 值 |
|---|---|
| 專案 | DeepSeek Harness（`dsh`） |
| GitHub | https://github.com/deepseek-ai/deepseek-harness |
| License | MIT |
| 主語言 | TypeScript |
| 預設分支 | master |
| 建立／最後 push | 2026-08-13 ／ 同日 |
| Topics | cordis, dsh, dsh-plugin, ai-agents |
| 狀態 | developer preview（破壞相容變更）|
| 運行 | `npx @deepseek-ai/dsh web`（Web UI 於 127.0.0.1:3080）|

> 註：Step 2-C1 取得的 stars/forks 數值異常偏高，疑與該時間點的快取或資料有關；本報告不以該數值為論據，僅以架構與機制為分析主體。
