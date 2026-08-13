# 218_R2_step1-intent.md

## 狀況理解

R2 使用者追加三問，不再只是「這是什麼」。三問合起來是一個**硬體採購＋自建 AI agent 工作區**的意圖：

1. **與樹莓派的比較**：問 ROCK 3C 相對樹莓派的優勢是不是「便宜＋雖不好開發但效能夠」。這是 R1 報告的延伸比較需求。
2. **AI agent 工作區的可行性**：想用 OllamaCloud/claude 搭配 opencode/claudecode 開**常駐 agent** 做事，問 ROCK 3C 是否合適。
3. **微型電腦的取捨**：預算 < 3 萬日幣、想開 2–3 個 agent、甚至跑瀏覽器，問是否該改買微型電腦。

核心：他要把「個人 AiAgent 的執行環境」從雲端/GAS 落地到一台具體硬體上，ROCK 3C 是被拿來測試這個載體是否成立的候選。

## 執行的動作與結果

先查第二腦 FATESAIKOU/MyBrain（refresh 至 c664bad 2026-08-11）後理解意圖：

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀骨幹「下一步清單」 | 確認他手上進行中的專案 | 找出與三問重疊的條目 | 命中「判定個人 AiAgent 的執行環境：GAS vs 自架伺服器跑 opencode」（技術-技術評估，低優先） |
| 讀骨幹「技術取捨準則」 | 確認他的技術評估判準 | 避免用通則推薦 | 抓到「理解優先」「MVP→Feature 閘門＝能否影響個人 workflow」「Reject≠沒價值」三條準則 |
| 讀骨幹「專案現況表」 | 確認硬體／SBC 相關專案 | 找是否有微型電腦標的 | 無任何 SBC／微型電腦專案，硬體軸是空白 |
| grep 技術評估 | 確認 ROCK/樹莓派/SBC 是否評估過 | 判斷是首見還是舊結論 | 無此標的——第二大腦無此主題 |
| 讀「個人 AiAgent 入口」 | 掌握他的 AI agent 工作區構想 | 理解三問落在哪個未決問題上 | 直接命中：整個專案卡在「執行環境未定」 |
| 讀 OpenCode／Openship 評估 | 確認 opencode 是否已用、對自架服務的立場 | 抓他的既有決策 | OpenCode 判定 stable（本人寫，2026-05-01）；Openship 判定 Reject，原話「我用 VPS 不是為了開服務」 |

**MyBrain 發現（每則帶 URL／信任層級／時間）：**

- **執行環境未定是既存卡點**：`個人 AiAgent 入口` 明列「GAS vs 自架伺服器跑 opencode」兩選項，R2 問題 2/3 正是把「自架」這一側具體化到硬體。URL：https://github.com/FATESAIKOU/MyBrain/blob/main/技術/靈感/個人%20AiAgent%20入口.md ｜ 信任：claude-code/opus-5，status draft（AI 草稿，未 review）｜ 時間 2026-08-11。
- **「開服務」立場已明**：Openship 判 Reject，原話「我用 VPS 不是為了開服務」。這與「自架一台常駐 agent 的硬體」可能衝突，QA 時須正面處理。URL：https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Openship.md ｜ 信任：opencode/deepseek-v4-pro 產出，human 2026-08-09 verified，status stable ｜ 時間 2026-07-26。
- **opencode 已實際使用**：OpenCode 判定 stable，「大致堪用，Ollama 帶來極大自由度」。他已有 opencode 實務基礎。URL：https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OpenCode.md ｜ 信任：human:fatesaikou，status stable ｜ 時間 2026-05-01。
- **無硬體評估紀錄**：ROCK／樹莓派／Jetson／任何 SBC／微型電腦，MyBrain 皆無技術評估——**第二大腦無此主題**，以上皆為通用知識範圍。
- **採購判準**：技術取捨準則的閘門是「能否影響個人 workflow」＋「理解優先」。這台硬體若只是為了開 agent，與他「先理解需求再堆工具」的取向須對照。URL：https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md ｜ 信任：claude-code/opus-5，status draft ｜ 時間 2026-08-01。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 標的 | ROCK 3C 與微型電腦之比較，且與「個人 AiAgent 執行環境」未決題掛鉤 | 三問是同一採購意圖的三個面向 |
| 第二腦重疊 | 命中「個人 AiAgent 入口」卡點與 Openship「不開服務」立場 | R2 直接觸碰他未定的決策，且與既有立場可能衝突 |
| 硬體評估 | MyBrain 是否有 ROCK/SBC/微型電腦紀錄 | 無，此標的第二大腦空白 |
| 既有工具 | opencode 是否已用 | 已 stable 判定並實際使用 |
| 本輪範圍 | 需含比較表、可行性評估、微型電腦對照、預算與多 agent 承載 | Step 2/3 須涵蓋 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 意圖定位 | ① 僅做硬體比較 ② 併入「個人 AiAgent 執行環境」未決題 | ② | 問題 2/3 明說要「開常駐 agent」，直擊 MyBrain 既存未決判定，不接上會漏掉他真正的問題 |
| 硬體範圍 | ① 只評 ROCK 3C ② 加微型電腦（N100 級）對照 | ② | 問題 3 明確要求「是否微型電腦更適合」，須納入預算/多 agent/跑瀏覽器對照 |
| 立場衝突 | ① 忽略 Openship「不開服務」② QA 時正面對照 | ② | 他既想自架 agent 又不開服務，兩者須並陳，避免報告與他舊結論打架 |
| 信任標注 | ① 只引 stable ② 區分 human stable 與 AI draft | ② | 個人 AiAgent 入口是 AI 草稿未 review，轉述時標明，避免當成他拍板過的結論 |
