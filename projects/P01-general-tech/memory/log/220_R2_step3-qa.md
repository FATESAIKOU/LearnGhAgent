# 220_R2_step3-qa.md

## 狀況理解

R2 使用者以四問追問 R1 報告，四問跨三塊：Q1/Q3（DeltaDB 資料模型的粒度與無損性）、Q2（與自建 LearnGhAgent memory 對照）、Q4（適用域）。Step 2（C1）已建立一手資料庫（delta.dev/docs 八頁，官方／stable）並初步收斂立場。本 step 將四問沉澱進既有報告的 `## 5. User Q&A`，並用第二大腦既有判定強化對照。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取既有報告 output/220_Delta.md | 取得可承接的既有內容 | 追加不刪改 | 完整讀取，157 行既有內容 |
| mybrain-read：LearnGhAgent、技術取捨準則、TencentDB、EverOS、Zed | Q2 對照與 §4 判準 | 用既有判定對照 | 取得 memory 定位（軌跡非知識）、防腐化模型、Reject 家族判定 |
| mybrain-read：grep Delta | 確認是否已判 | 若已判則引用 | 第二大腦無 Delta 主題；僅 openspec 與 workflow 方案檔中同名的無關 delta |
| 更新報告追加 `## 5. User Q&A` 四則 | 沉澱 R2 問答 | 追加不刪改既有內容 | 已追加，檔案增至 5 節，Q1~Q4 |
| 產出本 step log | 記錄動作總結 | 滿足流程 | 本檔 |

**Q1 判決**：非 1:1 對應 commit——對話與 file edit 同屬一個 delta 流（message 即 delta），git commit 是另層。**Q2 判決**：不類似——Delta 把對話當知識保存，使用者機制把執行軌跡當 debug、知識只在人 review 後的 output；哲學相反。**Q3 判決**：非無損 append-only——支援原地編輯丟棄後續回應與 revert，破壞「無損 raw data」前提，防腐缺口比 R1 更硬。**Q4 判決**：非僅 review——官方列 scaffold feature、fix bug、explore、review 四用途，review 只是整合閘門。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 報告檔名與變更 | 產出檔 output/220_Delta.md | 檔名不變；追加 `## 5. User Q&A`（Q1~Q4），既有 §1~§4 未刪改 |
| 報告長度 | 50000 字上限 | 符合（遠低於上限） |
| Q2 對照完整性 | 與 LearnGhAgent.md 對照 | memory 定位（275 份軌跡、刻意不納入知識）、MyBrain 防腐化模型（append-only＋validate/reindex CI）均寫入 |
| 報告 4 節完整性 | §1~§4＋§5 | 全部存在；§4 第二大腦判定表保留 |

**產出報告**：`output/220_Delta.md`（本輪變更＝新增 `## 5. User Q&A` 四則 QA，追加說明「非 1:1、非無損、非僅 review、與自建機制哲學相反」）

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| Q1 立場 | 對話↔commit 一一對應／對話是獨立 delta 流 | 獨立 delta 流 | 官方定義 message 即 delta、與 file edit 同流，非 1:1 |
| Q3 立場 | 承認無損即不需防腐／判非無損 | 判非無損 | 官方明文支援原地編輯丟棄後續與 revert，raw data 前提不成立 |
| Q2 對照基準 | 通則比較／用第二大腦既有判定 | 用既有判定 | LearnGhAgent memory 定位與防腐模型有 stable 檔可依 |
| 追加方式 | 改寫既有 QA／遞增追加 | 遞增追加（Q1~Q4） | AGENTS.md 規定既有 QA 不可刪改 |
