# 272_R1_step1-intent.md

## 狀況理解

使用者（R1 首輪請求，無前輪對話）給定技術標的：`i-have-adhd`（ayghri/i-have-adhd），一句描述為「讓 AI 程式助手輸出更直接」。這是 PR #272，Closes #267。使用者未附其他子面向或指定分析深度，交由我自行判斷。核心意圖是：解析這項工具「做什麼、為什麼存在、如何運作、與同類有何差異」。

技術類別上，`i-have-adhd` 與使用者第二大腦裡已評估的 **Caveman** 高度重疊——都是透過注入規則讓 AI coding agent 的輸出更簡潔／直接／少廢話的 system-prompt skill。因此本輪調研應特別對照既有判定，避免孤立看待。

## 執行的動作與結果

先查第二大腦（FATESAIKOU/MyBrain，`/tmp/mybrain` 鏡像 5a02dd5，2026-09-21 同步）：

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 PR body | 確認技術標的與附帶條件 | 取得完整需求 | 標的為 i-have-adhd，無額外子面向 |
| `grep adhd/ayghri` | 確認是否已評估過此標的 | 命中即引用舊結論 | **無此主題**——第二大腦無 i-have-adhd 評估記錄（GitHub URL 無從對應，判定：不存在）。不得以通用知識填空成「他的舊結論」 |
| 讀骨幹檔「技術取捨準則」 | 取得判斷準則 | 定位此標的該用哪條準則評估 | 理解優先（MVP 是驗證點）、MVP→Feature 唯一閘門＝「能否影響個人 workflow」、Reject=不採用≠沒價值。`generated.by: claude-code/opus-5`，`status: draft`（AI 草稿，本人未定稿），GitHub URL https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md |
| 讀技術評估「Caveman」 | 找最接近的同類判定 | 得知此類工具他的立場 | Caveman 判定「試用」：讓 coding agent 輸出更簡潔的 system-prompt skill，可採用、成本低、反正先裝。`status: stable`，`generated.by: human:fatesaikou`，https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Caveman.md |
| 讀「下一步清單」 | 確認此類標的是否接得上進行中的事 | 連結到現有計畫 | 命中第 69 行「Caveman/context-mode/LeanCtx/Headroom 與 rtk 比較」：五個工具解同一個問題（context 治理），判定散落、彼此沒共同基準比較過，rtk 每天在用是對照組。`i-have-adhd` 屬同一問題軸，應併入此比較。https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md |

> 註：第 69 行列的是 Caveman/context-mode/LeanCtx/Headroom/rtk 五者，未含 i-have-adhd（該檔為覆寫式快照，新增標的後需由本人決定是否併入）。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 技術標的 | 從 PR body 提取 | i-have-adhd（ayghri/i-have-adhd） |
| 是否已評估過 | grep 第二大腦 | 無此標的；但同類 Caveman 已判「試用」（stable/human） |
| 與進行中專案的關聯 | 查「下一步清單」 | 屬 context 治理比較軸（第 69 行），rtk 為現用對照組 |
| 判斷準則 | 讀骨幹「技術取捨準則」 | 能否影響個人 workflow 是 MVP→Feature 的閘門（draft/未定稿） |
| 輪次 | 檢查目錄 272_ 前綴 | 無前輪，確認為 R1 |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 技術標的判定 | i-have-adhd / Caveman / 其他 | i-have-adhd | PR body 明指此標的；Caveman 僅作對照 |
| 是否併入既有比較軸 | 孤立看待 / 併入 context 治理比較 | 併入比較 | 使用者已把同類五工具放進下一步清單比較，孤立分析會錯過他的既有脈絡 |
| 分析深度 | 僅摘要 / 對照既有判定深入調研 | 深入調研＋對照 Caveman | 需解析機制、並與已判「試用」的 Caveman 對照，才能定調 i-have-adhd 與其差異 |
| 採納判準 | 只用技術優劣 / 參照 workflow 閘門 | 兩者並用 | 技術取捨準則明示「能否影響個人 workflow」比技術優劣更強（draft） |
