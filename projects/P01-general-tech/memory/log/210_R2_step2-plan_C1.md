# 210_R2_step2-plan_C1.md

## 狀況理解

R2 為追問輪，非新標的。使用者先聲明「安全滲透最近沒打算深追」，再提兩題概念性問題：
1. **本質分類**：這東西的解決方式本質上是 skill？harness engineering？還是 graph engineering？
2. **使用門檻**：要駕馭它，人可以不懂資安嗎（就一般工程師）？

R1 已產出完整報告（`output/210_reverse-skill.md`），本 sub-step 不重做 R1 的 repo 全貌調研，而是**針對兩題做定向取證**：抓取能回答「本質抽象層」與「使用前提」的文件——ARCHITECTURE、OVERVIEW、SKILL.md、RULES.md、routing.json、IDENTITY.md、MASTER-ROUTING.md。目標是收斂出「路由機制是規則計分而非 graph」「是否需資安專業知識」的事實基礎，供 Step 3 在報告 §5 追加 QA。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` metadata | 確認 repo 現況 | 掌握 stars/license/更新 | stars 23,187、MIT、PowerShell、main、2026-08-10 更新（活躍） |
| `git/trees?recursive=1` | 盤點結構 | 確認「skill 包」組成 | 頂層含 RULES/AGENTS/CLAUDE/README_AI、`skills/`（40+ 子 skill）、`scripts/`、`docs/`、`kali/`、`burp-mcp-full/`、`CTF-Sandbox-Orchestrator/` 子模組 |
| `curl` docs/ARCHITECTURE.md | 取證「是否 graph」 | 判斷有無圖形路由 | 僅 mermaid 流程圖（文件層），無 runtime graph 引擎；路由是「關鍵字命中→計分→PRIMARY」線性分流 |
| `curl` docs/OVERVIEW.md | 取證定位 | 確認自我定位 | 明言「Skill Router + Tool Orchestration」「workflow operating system」，非單一工具安裝器 |
| `curl` skills/SKILL.md | 取證執行契約 | 理解 agent 行為鏈 | CRITICAL 路由契約：MASTER-ROUTING→case-init/scope→PRIMARY SKILL→tool-index→Evidence→報告 |
| `curl` RULES.md | 取證 client-neutral 與門檻 | 判斷是否需資安知識 | 明言「單一事實源」「client-neutral」；要求 agent 執行 ACTUAL SIDE EFFECTS（裝工具/分析/驗證/寫報告） |
| `curl` skills/config/routing.json | 取證路由機制 | 確認規則式 vs graph | 41 條規則（R0–R40），`must/exclude/mustAll` 關鍵字正規式計分，非語意/圖形路由 |
| `curl` skills/ops/IDENTITY.md | 取證本質定位 | 確認「是什麼」 | 明言「Skill 路由包」，**不是** Z3r0 平台（無 React/FastAPI/PostgreSQL/Docker 池/多 Agent 運行時） |
| `curl` skills/MASTER-ROUTING.md | 取證快路徑 | 確認 PRIMARY 判定 | 優先級表 R1–R40，與 routing.json 對應 |

**R2 兩題的關鍵取證收斂：**

**題 1（本質分類）**：
- **是 skill**：本體是 `skills/` 下 40+ 個 `SKILL.md` 子模組（apk-reverse、ida-reverse、js-reverse、pentest-tools…），每個是「方法論＋工具鏈＋工作流」的 markdown 指令包；`skills/SKILL.md` 是總控入口。IDENTITY.md 自稱「Skill 路由包」。
- **是 harness engineering（部分）**：`RULES.md`＋`skills/SKILL.md` 定義 agent 的**執行契約**（NOW/NEXT/ACT 順序、case-init scope 門禁、Evidence→Finding→Path、禁止假停），這屬「約束 agent 行為的 harness」層。但 harness 是**文件契約**，非程式碼 runtime。
- **不是 graph engineering**：路由是 `routing.json` 的**關鍵字正規式計分**（must/exclude/mustAll 命中→計分→取最高分 PRIMARY），是**規則式線性分流**，非語意圖、非知識圖譜、非 DAG 執行引擎。ARCHITECTURE 的 mermaid 是文件示意，非 runtime graph。
- **結論**：本質是 **skill 包 + 文件式 harness 契約**，路由用**規則計分**（非 graph）。「graph engineering」不成立。

**題 2（不懂資安可否駕馭）**：
- **路由層不需資安知識**：使用者只需描述任務（「分析這個 APK 的簽名驗證」），`routing.json` 關鍵字命中自動選 PRIMARY skill，agent 照 SKILL.md 走。一般工程師可當「黑箱路由器」用。
- **但執行層需要**：SKILL.md/RULES.md 要求 agent 產出「ACTUAL SIDE EFFECTS」——裝工具、分析、驗證漏洞、寫報告。**驗證漏洞真偽、判斷 false positive、理解 Evidence→Finding→Path 的證據鏈**，需要資安專業判斷。不懂資安的人無法判斷 agent 產出是否正確。
- **門檻分層**：駕馭「路由」低；駕馭「結果可信度」高。且 scope/auth 門禁（授權邊界）若不懂資安，可能誤授權或漏授權。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 是否 graph | 讀 routing.json + ARCHITECTURE | 規則計分路由，非 graph；mermaid 僅文件示意 |
| 本質定位 | 讀 IDENTITY.md + OVERVIEW.md | 自稱「Skill 路由包」，非平台、非 harness runtime |
| 執行契約 | 讀 RULES.md + SKILL.md | 文件式 harness 契約（NOW/NEXT/ACT、scope 門禁、Evidence 鏈） |
| 使用門檻 | 讀 SKILL.md/RULES.md 的 ACT 要求 | 路由層低門檻；執行/驗證層需資安專業 |
| 既有報告 | 讀 output/210_reverse-skill.md | R1 已含機制事實，R2 只需在 §5 追加 QA，不重寫 §1–§4 |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研範圍 | 重做 R1 全貌 / 定向取證兩題 | 定向取證兩題 | R2 是追問輪，AGENTS.md 明令「針對這輪意圖調研，非重做 R1」 |
| 取證文件 | 僅 README / 架構＋路由＋契約＋身份 | ARCHITECTURE+OVERVIEW+SKILL+RULES+routing.json+IDENTITY+MASTER-ROUTING | 兩題需「本質抽象層」與「使用前提」證據，非 README 行銷面 |
| 題 1 判定 | 單一歸類 / 分層歸類 | 分層歸類（skill＋harness 契約，非 graph） | 本體是 skill，執行契約是 harness，路由是規則計分；單一標籤會失真 |
| 題 2 判定 | 一刀切可/不可 / 分層 | 分層（路由低門檻、執行/驗證高門檻） | 駕馭「路由」與「結果可信度」是不同能力，需分開回答 |
