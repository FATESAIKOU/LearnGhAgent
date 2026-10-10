# 295_R1_step1-intent

## 狀況理解

本輪為 **R1、全新主題**（Original Issue #294），非追問或質疑。

- **技術標的**：`yt-dlp`，但範圍被明確限縮為「**只抓 YouTube 字幕、不下載影片**」。
- **使用情境**：給「手機 App 的 AI」在 **worker（Linux 容器）** 上執行——即 app 側 agent 呼叫 worker 執行抽取，產出逐字稿。
- **使用者要的 5 塊**：
  1. 只抓字幕的指令與選項（`--skip-download`／`--write-subs`／`--write-auto-subs`／`--sub-langs`／`--sub-format`）；**人工 vs 自動字幕的區分**；語言優先序（原語言 → 中文 → 日文 → 英文）。
  2. 字幕格式（vtt／srv3／json3）**轉純文字，僅用 jq／awk／sed**（不用 python）。
  3. **無字幕影片**的回應與判斷方式。
  4. **單檔執行版（`yt-dlp_linux`）**：可否不安裝直接用、檔案多大、更新頻率；YouTube 改版時的常見壞法與對策。
  5. **被擋情境**（429、需登入、年齡限制）的行為。
- **輸出期待**：一份**短報告 + 可直接複製的指令範例**（操作型，非技術評估判定）。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| refresh MyBrain 鏡像並讀骨幹 | 取得他的既有立場 | 得知準則與判定語意 | 鏡像 @a19ce8f 更新成功 |
| grep `yt-dlp`／`字幕`／`YouTube`／`逐字稿`／`ASR` | 找既有評估與關聯專案 | 確認標的與專案 | 命中下列 4 項 |

第二大腦查得（皆附 URL 與信任層級）：

1. **標的是否評估過：yt-dlp 本身無獨立技術評估。** 相關脈絡在 [Agent Reach](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Agent Reach.md)（`generated.by: human:fatesaikou`／`status: stable`／時間座標 2026-06-27）。該案把 `yt-dlp` 當 youtube 渠道實作，且記錄「B 站通用下載工具（yt-dlp）被風控 412 封死」；整體 verdict **不採用**（理由「不如直接搬瀏覽器上去」）。⚠️ 依 [判定總表](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md) 語意，「不採用 ≠ 沒價值」。另有 [video-use](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/video-use.md)（`ollama-cloud/deepseek-v4.1-flash`／`draft`／不採用）但屬影片剪輯，**不同軸**。
2. **關聯的進行中專案：[個人 AiAgent 入口](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/個人%20AiAgent%20入口.md)**（`claude-code/opus-5.5`／`status: draft`）。2026-08-30 記的四條 app 擴充需求含「**直接吃 YouTube 連結**——用 tool 或其他低成本方式抽逐字稿」，並明寫「**不自己跑 ASR**」。worker＝Linux 容器見 [MyLinuxPool](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/MyLinuxPool.md)（`ai:claude-opus-5`／`draft`），且「**worker 不持有任何憑證**」。
3. **取捨準則（骨幹）：[技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md)**（`claude-code/opus-5`／`draft`／`tags: [骨幹]`）——「理解優先」「Reject≠沒價值」。另有 [VoiceStudio](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/VoiceStudio.md)（`process:learn-gh-agent`／`draft`）轉述下一步清單硬約束：YouTube 逐字稿抽取「**低成本硬約束，不自己跑 ASR**」。

⚠️ **第二大腦無此主題的部分**：yt-dlp 的「subtitle-only 選項、字幕格式轉純文字、單檔版特性、429／登入／年齡限制行為」等**細部操作問題，第二大腦查無既有結論**——這些須靠外部資料補，不得當成他的舊結論。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 標的判定 | grep `yt-dlp` 全 bundle | 無獨立評估；僅 Agent Reach 內提及，屬穩定檔 |
| 專案關聯 | 讀「個人 AiAgent 入口」與「MyLinuxPool」 | 對應 app 版 YouTube 逐字稿需求 + worker Linux 容器 |
| 準則 | 讀骨幹「技術取捨準則」 | 理解優先、Reject≠沒價值、低成本不自己跑 ASR |
| 本輪性質 | 對照 issue 與既有 QA | R1 全新，非追問 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 本輪定位 | R1 新主題／R2 追問 | **R1 新主題** | issue 為 `Closes #294` 的原始需求 |
| 技術標的邊界 | yt-dlp 全功能／只抓字幕操作 | **只抓字幕的操作知識** | issue 明確限定「只抓字幕、不下載影片」 |
| 報告型態 | 技術評估（含 DA 表判定）／操作型短報告 | **操作型短報告 + 可複製指令** | 訴求是「怎麼下指令」，非「值不值得採用」 |
| 與既有評估的關係 | 引用 Agent Reach「不採用」當結論／僅作背景 | **僅作背景，不當結論** | 該案拒的是「多平台 adapter 的整套系統」，非 yt-dlp 抓字幕能力 |
