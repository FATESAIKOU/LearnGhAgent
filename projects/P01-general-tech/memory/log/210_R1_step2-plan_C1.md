# 210_R1_step2-plan_C1.md

## 狀況理解

R1 首次調研，標的為 `zhaoxuya520/reverse-skill`（逆向與安全研究 Skill 路由包）。Step 1 已確認標的、無前輪、第二大腦無此主題。本 sub-step C1 依 document skill 標準動作：取得 repo metadata、擷取 README 與關鍵子文件、補查背景脈絡。目標是收斂出「這是什麼、解決什麼問題、核心機制」的事實基礎，供後續 C2（替代方案）與 Step 3 報告使用。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view zhaoxuya520/reverse-skill --json ...` | 取得 repo metadata | 確認 stars、license、語言、更新時間 | 見下方 metadata 摘要 |
| `curl` README.md（raw） | 擷取主文件 | 理解定位、場景、架構 | 取得完整 README（About/Usage/架構/授權） |
| `curl` skills/MASTER-ROUTING.md | 擷取路由核心 | 理解 PRIMARY 快路徑與優先級表 | 取得 R0–R40 路由表與執行契約 |
| `curl` skills/config/routing.json | 擷取路由單一事實源 | 理解路由判定機制 | 取得 schema、scoring 規則、R1–R10 關鍵字樣本 |
| `curl` RULES.md | 擷取全域規則 | 理解 agent 行為鏈與授權門禁 | 取得 CRITICAL 執行區塊、client-neutral 邊界 |
| `curl` README_AI.md | 擷取 AI bootstrap | 理解首次部署流程 | 取得 OS 偵測→tool-index→路由→ops gate 流程 |
| `gh api .../git/trees/main?recursive=1` | 驗證關鍵文件存在 | 確認文件路徑真實 | 確認 AGENTS/RULES/README_AI/ops 契約等存在 |

**Metadata 摘要：**
- 建立：2026-05-13；更新：2026-08-09（活躍）
- stars：22,267；license：MIT（CTF-Sandbox-Orchestrator 子模組為 GPLv3）
- 主要語言：PowerShell；預設分支：main
- description：逆向/滲透/安全技能路由包，AI 自動路由 + 按需自舉工具鏈 + 自動進化經驗庫，支援 Claude Code/Kiro/Cursor/Cline 等

**核心機制（C1 收斂）：**
- 定位：AI agent 遇到 APK/二進位/前端 JS 加密/CTF/滲透目標時，路由到正確方法論、檢查工具、執行可重複工作流，而非猜指令
- 路由核心：`skills/config/routing.json` 為單一事實源（41 條規則 R0–R40），`master-route.ps1` 讀取並依關鍵字命中計分選 PRIMARY；`verify-routing-coherence.ps1` 校驗 json 與 markdown 表一致
- 行為鏈：RULES.md → MASTER-ROUTING → PRIMARY SKILL → case-init/scope（auth 門禁）→ 工具 bootstrap → Evidence→Finding→Path → 報告
- 工具管理：`tool-index.md` 為工具可用性單一事實源，缺則按 manifest bootstrap；refresh-tool-index 依平台生成
- 品質：163 個回歸測試案例、Windows+Ubuntu CI、supply-chain pin gate
- client-neutral：路由核心與測試不綁特定 AI client，client 配接器為選用

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo 存在性 | gh repo view | 存在，活躍，22k stars |
| 授權 | licenseInfo | MIT（含 GPLv3 子模組） |
| 路由機制 | routing.json + MASTER-ROUTING.md | 確認單一事實源 + 計分路由 |
| 文件路徑 | git/trees 遞迴 | 關鍵文件均存在 |
| 背景脈絡 | README About/Why | 取得「為何存在」的 4 點動機 |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 擷取文件範圍 | 僅 README / README+路由核心+規則 | README+MASTER-ROUTING+routing.json+RULES+README_AI | 需理解「路由包」本質，路由機制與行為鏈是核心 |
| 背景補查 | 本步補 / 留待 C2 | 本步僅取 repo 內背景 | C1 聚焦 repo 事實，外部替代方案留 C2 |
| 驗證方式 | 信任 README / 用 git/trees 交叉驗證 | 交叉驗證 | 確認文件路徑真實，避免報告引用不存在文件 |
