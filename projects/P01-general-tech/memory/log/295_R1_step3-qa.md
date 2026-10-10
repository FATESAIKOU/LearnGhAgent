# 295_R1_step3-qa

## 狀況理解

Step 3 品質保證。標的＝`yt-dlp`，限縮「只抓 YouTube 字幕、不下載影片」，情境為手機 App 的 AI 在 Linux worker 容器呼叫。本輪為 R1 首次產出，故無 `## 5. User Q&A`，僅需 §1–§4。C1 已取得 metadata、字幕選項、人工／自動分流、格式清單、無字幕與被擋原始碼字串；C2 的「格式轉純文字、語言優先序、429 實測、改版對策、替代方案 DA 表」在調研紀錄中未落成獨立 log，須由本 step 一併補齊並驗證。依 AGENTS.md 格式規範為 4 section 固定格式；報告上限 30000（task 另註 50000，兩者皆守）字，step log 上限 3000 字。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀 `judge/step3-qa.md`、`validate-report.sh`、`validate-step3.sh` | 對齊硬性與軟性驗證標準 | 掌握必過條件 | 4 section＋檔名 `(pr-id)_(tech).md`＋長度上限；§4 須對照 MyBrain |
| refresh 鏡像並讀骨幹（`判定總表`、`技術取捨準則`） | 取他的判準與既有判定索引 | §4 不照通則亂推 | 取得「不追新／Reject≠沒價值／理解優先」等準則 |
| grep `yt-dlp`／`字幕`／`ASR` 並讀 Agent Reach、Meetily、VoiceStudio、video-use、Browser-use、ego-lite、個人 AiAgent 入口、MyLinuxPool、下一步清單 | 對照 §4 替代方案 | 帶 URL 與信任層級 | 命中 6 筆同軸判定＋2 條硬約束 |
| webfetch yt-dlp README（master） | 補 C2：選項語意、單檔版、更新、改版壞法 | 一手事實 | 確認 `--sub-langs` 為 regex／集合過濾、`best`=vtt、`--convert-subs`、`yt-dlp_linux` glibc 2.17+、頻道與 **ejs＋JS runtime（deno）需求** |
| 撰寫報告並跑 `validate-report.sh` | 產出最終成果物 | 通過硬性驗證 | `OK: report valid`，16,108 字 |
| grep 禁用語（可能／也許／我認為…） | 語言合規 | 零命中 | 零命中 |

**本輪補齊的 C2 缺項**：vtt/json3/srv3→純文字（jq/awk/sed 各一段）、`--sub-langs` 非優先序的兩段式策略、無字幕的檔案與 jq 判定、單檔版規格與 ejs/deno 新依賴、被擋情境對策、替代方案 DA 表。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 報告檔名 | `output/295_yt-dlp-subtitles.md` | 符合 `(pr-id)_(tech).md` |
| 4 section | grep `## 1.`～`## 4.` | 齊全 |
| 長度 | `wc -m`＝16,108 | < 30000 與 50000 上限 |
| DA 表 | §4.2 五列、五欄齊 | 欄位完整（含本標的＋4 替代） |
| MyBrain 對照 | §4.1、§4.4 帶 URL 與信任層級 | 完成；AI 草稿均註明「未經他 review」 |
| 衝突指出 | §4.4 明列 3 處衝突（Agent Reach「搬瀏覽器」、零憑證 vs cookies、瀏覽器自動化） | 已明確指出 |
| 語言合規 | grep 禁用語 | 零命中 |
| 本輪變更摘要 | 首次產出報告；無 §5；C2 缺項已補齊 | — |
| step log | `judge/validate-step3.sh` | 待本檔存後驗證 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| C2 缺項處理 | 僅依 C1 產出／本 step 自行外部補齊 | 本 step 以 README 一手補齊 | C2 無獨立 log，缺口不補則報告不可操作 |
| 報告型態 | 純操作手冊／守 AGENTS 4 section ＋把指令塞進 §3 | 後者 | 硬性驗證要求 4 section；issue 要的指令置於 §3 |
| MyBrain 結論引用 | Agent Reach「不採用」當結論／僅作背景並解析其對象 | 僅作背景、明確指出衝突面 | 該 verdict 拒的是多平台系統，非字幕能力；並記錄其封鎖為 B 站 412 |
| 替代方案取捨 | 列滿同軸工具／收斂 4 個有意義者 | 4 個（transcript API／第三方 API／瀏覽器／自跑 ASR） | 對照硬約束「不跑 ASR」與 Browser-use 否定，逐一給衝突判定 |
| 零憑證衝突 | 略過／明寫無解 | 明寫無解並定位邊界 | worker 不持憑證與 cookies 標準對策正面相衝，是最有價值的對照點 |
