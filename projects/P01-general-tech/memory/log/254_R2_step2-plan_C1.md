# 254_R2_step2-plan_C1

## 狀況理解

R2 是使用者對 R1 報告的 4 題決策支援追問：Q1 執行環境可否脫離桌面／無頭 VPS、Q2 刨除外觀後與 herdr／orca 的本質差異、Q3 這個差異對「個人 AiAgent 入口／MyBrain／LLMGateway」三件事有沒有用、Q4 要取得差異價值只能安裝工具還是只需薄的擴張。

本 sub-step（C1）目標：取得 repo metadata 與主要文件，並針對 R2 意圖抓取「執行環境」「本質差異（herdr/orca/tmux 對照）」「協作機制（orchestrator/git-as-audit/檔案信箱）」的關鍵資料。不做 R1 已做的重複機制描述，只補 R2 需要的增量。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` 取得 metadata | 掌握 repo 現況（stars、license、語言、建立時間） | 確認成熟度與版本狀態 | TypeScript、MIT、6,362 stars、created 2026-05-31（約 3 個月）、pushed 2026-09-05、not archived |
| `gh api` 遞迴 tree + topics | 盤點 docs/ 與 blog/ 結構，找到對照文章 | 定位 Q2（herdr/orca）與 Q1（執行環境）的官方對照文 | 抓到 5 篇直接相關：`orca-vs-munder-difflin`、`tmux-and-scripts-vs-an-agent-harness`、`run-munder-difflin-on-a-mac-mini`、`file-based-coordination-vs-message-queues`、`single-committer-git-pattern`、`what-is-a-multi-agent-harness`、`how-the-god-orchestrator-works` |
| 抓 package.json＋5 份設計文件 | 補齊 R1 未細讀的執行環境與引擎設定事實 | 確認依賴、本地模型路線、無頭可跑性 | package.json 為 Electron 32 桌面依賴（node-pty、electron-updater、xterm、pixi）；無獨立 headless server entry |
| 讀 herdr 配置＋orca 對照文 | 建立 herdr/orca 的本質對照組 | 剝離外觀，找出「協調層在人 vs 在系統」的差異軸 | 見下方發現 2、3 |
| 用 mybrain-read 查三件事的既有判定 | 把 Q3 落地到 MyBrain／LLMGateway 既有事實 | 確認「hive layer 本質＝MyBrain 既有 git 基底」「LLMGateway 是另一層路由」 | 見下方發現 4、5 |

**發現（含來源與信任層級）：**

1. **執行環境（Q1）**：`run-munder-difflin-on-a-mac-mini`（blog，author=官方，draft=false）——控制面（router/scheduler/mailboxes/audit log）已是 local-first，唯一雲端依賴是 model 呼叫；把 model 指到本地 Ollama/LM Studio（OpenAI-compatible endpoint）即可完全離線。但**引擎是 CLI 程序、app 是 Electron 單體、無 headless server entry**——「無頭 VPS 常駐」非官方設計路徑（官方無頭場景是「Mac Mini 上當 always-on box」仍跑 Electron＋本機模型）。

2. **本質差異 vs herdr（Q2）**：`herdr 配置.md`（第二大腦，claude-code/opus-5，draft）——herdr 是「認得 pane 裡哪個 agent＋追蹤 idle/working/blocked/done＋開放給 CLI」，`herdr agent prompt <name> --wait` 可送指令並等待。**它是 UI/程序層，不提供共享記憶、路由、仲裁、自主觸發**——協調仍靠使用者（「驗收 agent 任務要看實際產出不可看 exit code」正是使用者當 message bus 的證據）。

3. **本質差異 vs orca（Q2）**：`orca-vs-munder-difflin`（blog，官方，draft=false）——orca（Stably AI，YC-backed）是 Agent IDE/ADE，平行 agents 在隔離 worktree，你在鍵盤前「驅動」（drive）；munder-difflin 是「辦公室」（office），GOD orchestrator 路由/裁決/升級，work 由 Slack/webhook/schedule/voice 觸發，有 approval/budget/circuit-breaker。官方自己畫的界線：**Orca 你是 Driver；Munder-Difflin 你是 Manager**。

4. **MyBrain 關聯（Q3）**：`munder-difflin.md`（第二大腦 verdict 未判定）＋ `個人 AiAgent 入口.md`——MyBrain 本身就是 git repo＋markdown-first＋PR review 寫入，與 munder-difflin 的「git-as-audit＋single-committer＋檔案信箱」基底**同構**。hive layer 的核心機制對 MyBrain 是「既有基底」，不是新增概念。

5. **LLMGateway 關聯（Q3）**：`OmniRoute.md`/`Switchyard.md`（第二大腦，verdict Accept/觀望）+ `下一步清單`——他的「LLMGateway」= LLM Provider 解耦層（統一 endpoint 切換 250+ provider）。這是「路由到哪個 model」的層；munder-difflin 的 orchestrator 是「路由工作給哪個 agent」的層，**路由域不同，無直接幫助**。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| metadata 現況 | gh repo view 比對 R1 的「5.5k star、v0.4.6」 | 通過：已升至 6,362 stars；版本仍 0.4.6（package.json） |
| 執行環境事實 | 官方 mac-mini 文＋package.json | 確認：local-first 控制面、桌面單體、無 headless entry |
| herdr 對照組 | 第二大腦 herdr 配置＋tmux vs harness 文 | 確認：herdr 是「人在圈內的協調」，無共享記憶/路由/自主 |
| orca 對照組 | 官方 orca 對照文 | 確認：orca 你當 Driver，munder-difflin 你當 Manager |
| 三件事落地 | mybrain-read 查 MyBrain/LLMGateway 既有判定 | MyBrain 同構（git 基底）；LLMGateway 是另一路由域 |
| 反爬 | 全程用 gh api＋raw.githubusercontent | 未觸發 CAPTCHA，不需 CDP |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| C1 範圍 | ① 重做 R1 的完整文件調研 ② 只抓 R2 需要的增量 | ② | R1 已讀 README+4 設計文件；R2 的增量是執行環境＋herdr/orca 對照＋三件事落地，不重複 |
| Q2 對照組素材 | ① 只用第二大腦 herdr 配置 ② 補官方 orca/tmux 對照文 | ② | herdr 有他實測紀錄，orca/tmux 無官方對照會缺佐證；官方文與第二大腦 herdr 檔互相補強 |
| Q3 的 LLMGateway 查證 | ① 只查個人 AiAgent 入口檔 ② 深挖 OmniRoute/Switchyard/下一步清單 | ② | Step1 已定調 LLMGateway 是「provider 抽象層」，C1 用其技術評估檔＋下一步清單確認路由域不同 |
| 執行環境的定位 | ① 只引 README 說「Electron 桌機」 ② 用官方無頭指南佐證 | ② | Q1 問「可否無頭 VPS」，需官方對無頭場景的明確敘述（Mac Mini always-on）佐證桌面單體是硬約束 |

**下一步（C2 若需）**：C1 已涵蓋 Q1/Q2 的事實與 Q3 的落地；分析收斂與 Q4（薄的擴張可行性）結論在 Step 3 報告中撰寫。
