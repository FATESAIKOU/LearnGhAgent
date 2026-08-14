# 220_R1_step2-plan_C1.md

## 狀況理解

R1 第一輪，標的為 Zed 團隊 2026-08-12 發布的「Delta」與其後端「DeltaDB」。使用者三問：①對個人工作流是加成還是替換；②是 harness／tool／還是團隊大一統 culture；③與類似方案相比有無本質突破（沒有就自己幹）。C1 是 Step 2 第一個 sub-step，任務是「取得 repo metadata 與主要文件」。Delta 目前是 private beta，GitHub 上無公開 repo，故改以官方 blog 與 docs 為主要一手來源。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view zed-industries/delta` / `deltadb` | 取得 repo metadata（stars/license/分支） | 若有公開 repo 直接拿 metadata | 兩者皆 GraphQL 解析失敗，repo 不存在 |
| `gh search repos "delta zed"` / `"deltadb"` | 找官方 repo 或同名專案 | 定位官方 repo | 無官方 repo；同名 deltadb 皆為無關的第三方資料庫專案 |
| `gh api orgs/zed-industries/repos` 過濾 delta | 確認 Zed org 內有無 delta repo | 確認官方 repo 位置 | org 內無 delta 相關 repo，確認 private beta 未開源 |
| webfetch zed.dev/blog/introducing-delta | 取得 Delta 官方公告 | 掌握定位、功能、beta 狀態 | 取得完整公告：multiplayer agent 協作環境、DeltaDB 同步 conversation+worktree、WASM/WebGL 網頁版、Claude Code harness 連動、private beta |
| webfetch zed.dev/blog/introducing-deltadb | 取得 DeltaDB 技術公告 | 掌握核心機制 | 取得「Software Is Made Between Commits」：fine-grained deltas、每 operation 有 stable identity、CRDT 複製 worktree、anchor 到 delta 而非行號 |
| webfetch zed.dev/blog/crdts | 補 CRDT 技術背景 | 理解 DeltaDB 底層 | 取得 Zed 的 CRDT 實作原理（anchor、tombstone、Lamport timestamp、undo map） |
| webfetch delta.dev + /docs 系列 | 取得產品文件 | 掌握實際使用流程 | 取得 Getting Started、Delta & Git、Worktrees & Machines、Threads、Review & Sync 等文件 |

**關鍵一手資料（來源與信任層級）：**

| 標的 | 內容 | 來源 | 信任層級 |
|---|---|---|---|
| Delta 定位 | 「multiplayer environment for coding with agents and reviewing what they build」；thread 為中心 | zed.dev/blog/introducing-delta | 官方 / stable |
| DeltaDB 核心 | 把 conversation 與 worktree 一起即時複製；與既有 git repo 相容；capture 每個 commit 之間的 edit 與 chat | zed.dev/blog/introducing-deltadb | 官方 / stable |
| delta 定義 | 對 thread 或 worktree 的記錄變更（file edit、tree change、message、comment）；連續產生，不需 stage/commit | delta.dev/docs/concepts/delta-and-git | 官方 / stable |
| 底層機制 | CRDT conflict-free replicated worktrees；anchor 到 delta 而非行號，code 移動時 reference 仍存活 | zed.dev/blog/introducing-deltadb + crdts | 官方 / stable |
| 執行模型 | agent 在 checkout（真實檔案夾）工作；每參與者一份本地 copy，DeltaDB 即時同步；agent 一次只在單一機器跑（本機或 cloud runner） | delta.dev/docs/concepts/worktrees-and-machines | 官方 / stable |
| git 整合 | 兩 remote：origin（共享上游）＋ local（本機 repo）；agent 可 push 到 local 免 GitHub round-trip；支援 jj colocated | delta.dev/docs/concepts/delta-and-git | 官方 / stable |
| 協作 | thread 私有、可分享；browser 版為同一 Rust app 編譯 WASM＋WebGL；Claude Code 為首波第三方 harness 連動 | zed.dev/blog/introducing-delta | 官方 / stable |
| 其他 | skills、可編輯已發訊息（重寫後續）、可切換 model、.gitignore 尊重、cloud runner 尚在 rollout | delta.dev/docs | 官方 / stable |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo 存在性 | gh api / gh search 查官方 repo | 無公開 repo，private beta 未開源；以官方 blog＋docs 為一手來源 |
| 定位 | 官方公告與 docs 交叉比對 | Delta＝agent 協作＋review 環境；DeltaDB＝以 conversation 為中心的 version control |
| 核心機制 | deltadb 公告＋CRDT 公告 | fine-grained delta、stable identity、CRDT 複製 worktree、delta-anchor |
| 執行與整合 | docs 的 worktrees/git 頁 | checkout 模型、兩 remote、cloud runner、jj 支援 |
| 對使用者三問的素材 | 已收集 | ①個人 vs 團隊張力（thread 為中心、多人協作）；②harness/tool 光譜（Delta 是 app＋DeltaDB 是資料層，非純 harness）；③本質突破（delta-anchor＋conversation 即 source，需與 Aionui/EverOS/TencentDB 對照） |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 資料來源 | 等 GitHub repo 開源／用官方 blog＋docs | 官方 blog＋docs | private beta 未開源，官方一手文件已足夠支撐分析；無需 CDP |
| 標的拆解 | 只查 Delta app／Delta＋DeltaDB 分開查 | 分開查 | 使用者三問中②③都需區分「app 層」與「資料層」，DeltaDB 才是本質突破的載體 |
| 技術深度 | 只讀公告／補 CRDT 底層 | 補 CRDT 底層 | ③「本質突破」需理解 delta-anchor 與 CRDT 複製的機制差異，才能與既有判定對照 |
| 後續 sub-step 方向 | 直接收斂／再補對照組 | 需再補對照組 | ③需 Aionui（agent 協作）、EverOS/TencentDB（團隊記憶）的機制對照，留待 C2 處理 |
