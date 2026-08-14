# 220_R2_step2-plan_C1.md

## 狀況理解

R2 使用者四問追問，C1 負責「一手資料」：Q1（對話與 commit 是否一一對應）、Q3（是否真的無損留下）、Q4（用途僅 Code Review 或含開發/改修）。R1 已抓過官方 blog 與 docs 主頁，本 sub-step 針對 R2 意圖重抓 DeltaDB 資料模型、threads、review、comments、collaboration、data-storage 等子頁，驗證粒度、無損性與適用域。Q2（對照 LearnGhAgent memory）留給 C2。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| webfetch delta.dev/docs/concepts/delta-and-git | Q1 資料模型粒度 | 確認 delta 是否等同 commit、conversation↔operation 對應 | 取得關鍵定義：delta 是對 thread/worktree 的記錄變更（file edit、tree change、message、comment），連續產生、不需 stage/commit；**conversation 訊息本身就是 delta**，與 file edit 同屬一個 delta 流；git commit 留在 git，DeltaDB 另記 delta 流 |
| webfetch delta.dev/docs/agents/threads | Q3 無損性 | 確認對話是否無損原文留存 | 取得「Edit a sent message」：可原地編輯先前訊息，**發送後會取代該訊息之後的對話（後續回應被丟棄）**；thread 可 revert 到較早點並一併還原 worktree |
| webfetch delta.dev/docs/agents/review-and-sync | Q4 適用域 | 確認是否僅 review | 取得 review 是「bring changes in」前的整合閘門；agent 在獨立 checkout 工作，review 後才 push local/origin |
| webfetch delta.dev/docs/concepts/worktrees-and-machines | Q1/Q3 底層 | 確認 delta 流與同步 | 取得每參與者一份 checkout、DeltaDB 同步；agent 一次只在單一機器跑；「records every change as it is made」 |
| webfetch delta.dev/docs/agents/comments | Q4 適用域 | 確認 review 機制 | 取得 annotation 式 comment（選取文字片段附註、可回覆），agent 把 comment 當針對該段落的回饋 |
| webfetch delta.dev/docs/collaboration/collaborate-thread | Q1/Q4 協作 | 確認多人協作模型 | 取得 thread 分享、每參與者 checkout、agent 一次單機跑、draft 可多人編輯 |
| webfetch delta.dev/docs/privacy-and-security/data-storage | Q3 無損性 | 確認儲存是否無損 | 取得 DeltaDB 存「deltas in sequence」以重建 thread；thread 刪除只移除本機、伺服器副本不即時移除；retention/backup 可能暫留 |
| webfetch delta.dev/docs/getting-started | Q4 適用域 | 確認官方宣稱用途 | 取得「explore the codebase, fix a bug, or scaffold a feature」——**明確含新功能 scaffold、bug fix、探索**，非僅 review |

**關鍵一手資料（來源與信任層級）：**

| 標的 | 內容 | 來源 | 信任層級 |
|---|---|---|---|
| Q1 delta 定義 | delta＝對 thread/worktree 的記錄變更（file edit、tree change、message、comment）；連續產生、不需 stage/commit；**conversation 訊息即 delta** | delta.dev/docs/concepts/delta-and-git | 官方 / stable |
| Q1 對應關係 | git commit 留在 git；DeltaDB 另記 delta 流；**非 1:1 對應 commit**，delta 粒度細於 commit | 同上 | 官方 / stable |
| Q3 無損性 | 可原地編輯先前訊息，發送後**取代該訊息之後的對話（後續回應丟棄）**；可 revert 到較早點並還原 worktree | delta.dev/docs/agents/threads | 官方 / stable |
| Q3 儲存 | DeltaDB 存 deltas in sequence 以重建 thread；thread 刪除僅移除本機、伺服器副本不即時移除；retention/backup 可能暫留 | delta.dev/docs/privacy-and-security/data-storage | 官方 / stable |
| Q4 適用域 | 官方宣稱用途＝explore codebase、fix bug、scaffold feature；review 是 bring changes in 前的整合閘門 | delta.dev/docs/getting-started + review-and-sync | 官方 / stable |
| Q4 review 機制 | annotation 式 comment（選取文字附註、可回覆），agent 當針對段落的回饋 | delta.dev/docs/agents/comments | 官方 / stable |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Q1 粒度 | delta-and-git 頁定義 | **非 1:1**：conversation 訊息與 file edit 都是 delta，同屬一個 delta 流；git commit 是另一層，DeltaDB 不把對話對應到 commit，而是把「對話＋編輯」一起記成連續 delta |
| Q3 無損性 | threads 頁＋data-storage 頁 | **非純 append-only 無損**：支援原地編輯先前訊息並丟棄後續、revert 到較早點；儲存為 delta 序列可重建，但刪除/編輯會破壞「無損原文留存」的假設 |
| Q4 適用域 | getting-started＋review-and-sync＋comments | **非僅 review**：官方宣稱用於新功能 scaffold、bug fix、codebase 探索；review 是整合前的閘門，非唯一用途 |
| 對 R2 四問的素材 | 已收集 | Q1/Q3/Q4 一手證據齊備；Q2 留 C2 對照 LearnGhAgent memory |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| Q1 立場 | 對話與 commit 一一對應／對話是獨立 delta 流 | 對話是獨立 delta 流 | 官方明確定義 message 即 delta、與 file edit 同流，git commit 另層；非 1:1 |
| Q3 立場 | 照 R1 判防腐化缺口／承認無損即不需防腐 | 兩者皆需修正 | 使用者質疑正確：Delta 非純無損 append-only，支援原地編輯丟棄後續與 revert，故「無損 raw data」前提不成立，防腐缺口比 R1 所述更實質 |
| Q4 立場 | 僅 review／含開發改修 | 含開發改修 | 官方 getting-started 明列 scaffold feature、fix bug、explore，review 只是整合閘門 |
| 後續 sub-step | 直接收斂／再補對照 | 需 C2 | Q2 對照 LearnGhAgent memory 定位與防腐模型，屬自建機制對照，非一手資料 |
