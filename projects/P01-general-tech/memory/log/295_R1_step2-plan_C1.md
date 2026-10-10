# 295_R1_step2-plan_C1

## 狀況理解

Step 2 C1：取得技術標的的 repo metadata 與主要文件。標的＝`yt-dlp/yt-dlp`（GitHub repo，Python 專案）。R1 首次調研、非追問，主題限縮為「**只抓 YouTube 字幕、不下載影片**」，使用情境為手機 App 的 AI 在 **Linux worker 容器**內呼叫。C1 需盤點：repo 定位與時序、發佈檔（尤其 `yt-dlp_linux` 單檔版）、README 字幕選項、YouTube extractor 對人工／自動字幕與格式的實作、被擋情境的一手訊息；供 C2 補格式轉純文字（jq/awk/sed）、無字幕判定、改版壞法對策與替代方案 DA 表。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` + `gh api repos/yt-dlp/yt-dlp` | 取 repo metadata | stars/license/時序 | 196,645 stars、17,117 forks、**Unlicense**、Python、created 2020-10-26、pushed 2026-09-27、open issues 2693、branch `master` |
| `gh api .../releases/latest` assets | 取單檔版規格 | 檔名／大小／更新支援 | `yt-dlp_linux` = 40,446,224 B（約 38.6 MiB）、glibc 2.17+、下載 697,700；另有 `.zip`（標 no auto-update）、`aarch64`、`musllinux` |
| `gh api releases?per_page=14` | 算發佈節奏 | 更新頻率 | 最新 2026.08.19；近幾版 07-04、06-09、03-17…約每月一次但不定期 |
| 讀 `README.md`（2,504 行） | 取字幕選項與安裝契約 | 一手選項 | Subtitle Options／Release Files／Update Channels 三節齊 |
| 讀 `yt_dlp/YoutubeDL.py` | 取字幕寫入邏輯 | 無字幕／格式行為 | `_write_subtitles`、`subtitlesformat` 預設 `best`、無字幕訊息 |
| 讀 `extractor/youtube/_video.py` | 取字幕來源邏輯 | 人工／自動與格式清單 | `_SUBTITLE_FORMATS`、`asr`、PO token、被擋訊息 |
| 讀 `extractor/youtube/_base.py` | 取登入提示 | 被擋對策 | `_youtube_login_hint` → cookies |

**關鍵事實整理**

| 面向 | 內容 |
|---|---|
| repo 定位 | 「A feature-rich command-line audio/video downloader」；2020-10-26 自 youtube-dl fork（同日 repo created），授權 Unlicense |
| 單檔版 | `yt-dlp_linux`：glibc 2.17+ x86_64 standalone，**免安裝 Python 可直接執行**，支援 `-U` 自我更新；`.zip` 變體標「no auto-update」 |
| 更新頻道 | `stable`（預設、約每月、官方註明常 stale 易壞）、`nightly`（官方建議日常使用）、`master`（canary）；指令 `-U` / `--update-to` |
| 字幕選項 | `--skip-download`（別名 `--no-download`）、`--write-subs`、`--write-auto-subs`（別名 `--write-automatic-subs`）、`--list-subs`、`--sub-format "srt"`／`"ass/srt/best"`、`--sub-langs`（regex、`all`、逗號、`-` 排除，如 `all,-live_chat`）、`--convert-subs`（ass/lrc/srt/vtt） |
| 人工 vs 自動 | 原始碼：軌 `kind != 'asr'` → 人工（歸 `subtitles`）；`kind == 'asr'` → 自動（歸 `automatic_captions`）；分由 `--write-subs` / `--write-auto-subs` 觸發 |
| 字幕格式 | YouTube 提供順序 `json3,srv1,srv2,srv3,ttml,srt,vtt`；`--sub-format best`（預設）取 `formats[-1]`＝**vtt**；無匹配則退回最後一個並警告 |
| 無字幕 | `[info] There are no subtitles for the requested languages`；單語言缺 → `WARNING: {lang} subtitles not available`；PO token 缺 → `missing subtitles languages because a PO token was not provided` |
| 被擋（原始碼實訊） | sign-in：reason 含 "sign in" → 附 cookies 登入提示；captcha → `requiring a captcha challenge`；率限 → `This content isn't available, try again later`＝帳號被限流最多 1 小時、建議 `-t sleep`；age → `age-restricted; some formats may be missing without authentication`；部分 client 因 403 被跳過 |
| 預設字幕語言 | 未給 `--sub-langs` 時優先取 `en`（`en`／`en.*` 優先，再全語言取一）；`--sub-langs "en.*,ja"` 為 regex 比對 |

**待 C2 補**：vtt/json3/srv3 結構與 jq/awk/sed 轉純文字、`--sub-langs` 是「集合過濾」非「優先序」的選取策略、429／bot 實測字串、YouTube 改版常見壞法與對策、替代方案 DA 表。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata | stars/forks/license/語言/時序/issue/branch | 完整（Unlicense 非 OSI 標準；分支 master） |
| 單檔版規格 | releases assets 名稱、size、更新支援 | 取得大小與「免安裝、可自更新」事實 |
| 字幕選項契約 | README Subtitle Options 逐項 | 一手選項齊全 |
| 人工／自動與格式 | `_video.py` `_SUBTITLE_FORMATS`、asr 判定 | 確認 7 種格式與 asr 分流 |
| 無字幕／被擋行為 | `YoutubeDL.py` + `_video.py` 訊息 | 取得精確字串與對策 |
| 背景脈絡 | repo created 2020-10-26、youtube-dl fork 史 | 已補母體；通用背景與替代留 C2 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 資料來源 | clone 全 repo／gh api＋raw 逐檔／只讀 README | gh api metadata＋raw 抓 README 與 3 支關鍵原始檔 | 字幕與被擋行為不在 README，須讀實作才有一手字串；免 clone 開銷 |
| 調研深度 | 只讀文件／文件＋原始碼／全 repo | 文件＋關鍵原始碼 | issue 要「精確指令與判定方式」，原始碼可靠度高於二手教學 |
| 主題邊界 | yt-dlp 全功能／只字幕路徑 | 只字幕路徑 | issue 明限「只抓字幕」 |
| 轉純文字與替代方案 | C1 一併處理／留 C2 | 留 C2 | C1 目標為 metadata 與主要文件盤點 |
| 429 字串定位 | C1 直接斷言／C2 實證 | 標為待補、暫只列原始碼實訊 | 避免未查證的錯誤訊息進報告 |
