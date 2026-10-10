# yt-dlp「只抓 YouTube 字幕、不下載影片」操作分析

> 標的：`yt-dlp/yt-dlp`（GitHub repo；Python 專案，2020-10-26 自 youtube-dl fork，授權 Unlicense）
> 分析：技術解析助理，2026-10-10
> 前置查證：第二大腦（FATESAIKOU/MyBrain）**無 yt-dlp 的獨立技術評估**；僅在 [Agent Reach](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Agent%20Reach.md) 內被當作 youtube 渠道提及。本報告事實以 repo 的 README、releases metadata 與 `yt_dlp/YoutubeDL.py`、`extractor/youtube/_video.py`、`_base.py` 一手原始碼為主。

---

## 1. 這個技術解決什麼問題？

用一句話：**在不觸碰影片本體的前提下，把 YouTube 影片的人工字幕與自動字幕抓成檔案，並轉成純文字逐字稿。**

使用情境限定為「手機 App 的 AI 在 Linux worker 容器內呼叫」，因此被解的問題再拆成六個操作級子問題：

| # | 子問題 | 具體要求 |
|---|---|---|
| P1 | 只抓字幕的指令集 | `--skip-download`／`--write-subs`／`--write-auto-subs`／`--sub-langs`／`--sub-format` 的組合 |
| P2 | 人工字幕與自動字幕的分辨 | 兩者在 yt-dlp 內部分屬不同資料結構與不同開關 |
| P3 | 語言優先序 | 原語言 → 中文 → 日文 → 英文，且要能落成可執行邏輯 |
| P4 | 字幕轉純文字 | 只准用 `jq`／`awk`／`sed`，不得用 Python |
| P5 | 無字幕影片的判定 | 影片沒有字幕時的行為與判斷方式 |
| P6 | 單檔執行版與被擋情境 | `yt-dlp_linux` 免安裝、大小、更新、改版壞法；429／登入／年齡限制的處理 |

### 問題描述中的模糊之處

- **「原語言」未定義取得方式**：YouTube 字幕語言是一組標籤（如 `en`、`zh-Hans`、`ja`），沒有「這是不是原始語言」的旗標。原語言如何取得，需求未指定。
- **「純文字」未定界線**：是否保留時間軸、講者標記、換行節奏，需求未指定。
- **「沒字幕時的回應」未定介面**：是回空字串、錯誤碼，還是一個事件，需求未指定。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 repo 文件與原始碼明確提到的背景

- **字幕與影片是兩個獨立的資源**：YouTube 提供字幕（subtitle）與自動字幕（automatic caption）兩種軌，各自有獨立的取得 URL。yt-dlp 原始碼把軌依 `kind` 分流——`kind != 'asr'` 歸 `subtitles`（人工），`kind == 'asr'` 歸 `automatic_captions`（自動，ASR 產生）。因此抓字幕與抓影片在協定層可分離，才有「只抓字幕」的空間。
- **YouTube 端點不會靜止**：專案自承 `stable` 發佈「often stale and prone to external breakage」，即網站改版會壞掉 yt-dlp，官方因此建議一般使用者走 `nightly` 頻道。
- **完整 YouTube 支援需要 JavaScript 元件**：README 明列 `yt-dlp-ejs`「Required for full YouTube support」，並需要一個 JS runtime（推薦 `deno`，或 `node`／`bun`／`quickjs`）。官方 executable 內含 `yt-dlp-ejs`，但 JS runtime 為外部依賴。若無可用 JS runtime，預設 client `visionos,web` 會捨去 `web`。

### 2.2 通用技術背景（補充）

| 背景項 | 內容 |
|---|---|
| **YouTube 的播放頁是 JS 渲染** | 直接 HTTP GET 觀看頁得到的是殼，字幕 URL 藏在 player response 內，需走 innertube API。這是「為什麼不能純 curl ＋ grep」的原因。 |
| **字幕格式的來源順序** | yt-dlp 記錄 YouTube 可提供 `json3, srv1, srv2, srv3, ttml, srt, vtt`。`--sub-format best`（預設）取清單最後者，即 **vtt**。 |
| **自動字幕的滾動重複** | ASR 字幕在時間軸上會把上一行重複帶入下一 cue，逐行輸出時會出現大量重複行，這是轉純文字必須處理的雜訊。 |
| **反爬與維護債** | YouTube 以簽章混淆（nsig）、PO token、client 輪換對抗下載器，造成 extractor 週期性損壞；這是「頻繁更新」的根因。 |
| **情境脈絡（第二大腦）** | [個人 AiAgent 入口](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/個人%20AiAgent%20入口.md)（`claude-code/opus-5.5`、`draft`，**AI 草稿未經他 review**）記有 app 擴充需求「直接吃 YouTube 連結——用 tool 或其他低成本方式抽逐字稿」，並明寫低成本是硬約束、**不自己跑 ASR**。[MyLinuxPool](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/MyLinuxPool.md)（`ai:claude-opus-5`、`draft`，**AI 草稿未經他 review**）記 worker 為無狀態 Linux 容器、**不持有任何憑證**。 |

---

## 3. 這個技術是如何解決該問題的？

yt-dlp 的做法是：**以單一 CLI 呼叫 innertube API 取得 player response，從中挑出字幕軌，寫成檔案；字幕轉純文字則留給外部工具。** 以下逐項對應 issue 的 5 塊。

### 3.1 只抓字幕的指令與選項（對應 P1）

```sh
# 最小指令：只抓字幕、不下載影片
yt-dlp --skip-download \
  --write-subs --write-auto-subs \
  --sub-langs "en.*,zh-Hans,zh-Hant,ja" \
  --sub-format "vtt" \
  -o "%(id)s.%(ext)s" \
  "https://www.youtube.com/watch?v=VIDEO_ID"
```

| 選項 | 作用 | 備註 |
|---|---|---|
| `--skip-download` | 不下載影片，但仍寫相關檔案 | 別名 `--no-download`；這是「只抓字幕」的關鍵 |
| `--write-subs` | 寫人工字幕 | 預設關閉 |
| `--write-auto-subs` | 寫自動（ASR）字幕 | 別名 `--write-automatic-subs`；預設關閉。**兩者都給，才會「有哪個抓哪個」** |
| `--sub-langs` | 指定語言（可 regex）或 `all`，逗號分隔；`-` 前綴排除 | 例：`all,-live_chat`（排除直播聊天） |
| `--sub-format` | 格式偏好，`/` 分隔 | 例：`srt`、`ass/srt/best`；預設 `best`＝vtt |
| `--list-subs` | 列出可用字幕 | **預設 simulate**（只列不寫） |
| `--convert-subs` | 轉檔（`ass`/`lrc`/`srt`/`vtt`） | 由 yt-dlp 內部轉換，字幕轉換不需 ffmpeg |
| `-o` / `-P` | 輸出樣板／目錄 | 固定檔名用 `-o "%(id)s.%(ext)s"` |

**先列清單再下載**：

```sh
yt-dlp --skip-download --list-subs "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 3.2 人工字幕與自動字幕怎麼分（對應 P2）

| 面向 | 人工字幕 | 自動字幕 |
|---|---|---|
| 內部資料 | `subtitles` | `automatic_captions` |
| 原始碼判準 | 軌的 `kind != 'asr'` | 軌的 `kind == 'asr'` |
| 觸發開關 | `--write-subs` | `--write-auto-subs` |
| `--list-subs` 輸出區塊 | `Available subtitles` | `Available automatic captions` |

- **判定實務**：用 `--list-subs` 的兩個標題區塊分辨最可靠；或讀 `.info.json` 的 `subtitles` 與 `automatic_captions` 兩個 key。
- **直播聊天是字幕的一種**：`live_chat` 會被視為字幕，需以 `--sub-langs all,-live_chat` 排除。

### 3.3 語言優先序（對應 P3）

**關鍵限制：`--sub-langs` 是「集合過濾」不是「優先序」。** 給多個語言時，yt-dlp 會把每一個命中的語言都下載，不會只取第一個命中者。語言碼以 regex 比對，「原語言」沒有專屬旗標。

可行做法是**兩段式**：先寫 metadata，讀出可用語言，再依「原語言 → 中文 → 日文 → 英文」挑單一語言下載。

```sh
url="https://www.youtube.com/watch?v=VIDEO_ID"
yt-dlp --skip-download --write-info-json -o "%(id)s" "$url"

info=VIDEO_ID.info.json

# 原語言：info.json 的 language 欄位常為 null，需以實際內容為準，不可假設
orig=$(jq -r '.language // empty' "$info")
# 可用語言集合（人工＋自動）
avail=$(jq -r '(((.subtitles // {})|keys) + ((.automatic_captions // {})|keys)) | unique | join(",")' "$info")

# 依 原語言 → 中文 → 日文 → 英文 挑第一個存在的語言碼
chosen=""
for cand in "$orig" zh-Hans zh-Hant zh-CN zh-TW zh ja en; do
  [ -n "$cand" ] || continue
  case ",$avail," in *",$cand,"*) chosen="$cand"; break;; esac
done
printf 'chosen=%s\n' "$chosen"
```

```sh
# 以選定的單一語言下載
yt-dlp --skip-download --write-subs --write-auto-subs \
  --sub-langs "$chosen" --sub-format "vtt" \
  -o "%(id)s.%(ext)s" "$url"
```

- 語言碼是 regex：要涵蓋變體（如 `en-US`、`en-orig`）須寫成 `en.*`；只寫 `en` 時不匹配變體。
- 「原語言」的替代推法：若 `.language` 為 null，可把可用語言集合中「非 en／zh／ja」者優先視為原語言，或由 App 端提供提示碼。此推法需以實際資料驗證。

### 3.4 字幕格式轉純文字：只用 jq／awk／sed（對應 P4）

**建議：優先取 vtt（現行預設），需要結構化時取 json3；srv1/2/3 屬舊 XML，非必要不用。**

**vtt（WebVTT）→ 純文字**

```sh
sed -e '/^WEBVTT/d' -e '/^NOTE\b/d' -e '/^STYLE/d' -e '/-->/d' \
    -e 's/<[^>]*>//g' -e 's/\r$//' FILE.vtt \
| awk 'NF' \
| awk '$0!=prev{print} {prev=$0}'
```

- `/-->/d` 去掉時間軸 cue；`s/<[^>]*>//g` 去掉行內標籤（`<c>`、`<v Speaker>`、`<00:00:00.000>` 等）；`awk 'NF'` 去空行；末行把「連續重複行」折疊（ASR 滾動字幕常見）。
- 若需**全域**去重複，改用 `awk '!seen[$0]++'`（代價是會刪掉非連續的重複句）。

**json3（YouTube JSON）→ 純文字**

```sh
jq -r '[.events[] | .segs[]? | .utf8 // empty] | join("")' FILE.json3 \
| awk 'NF'
```

- 逐事件串接所有文字片段；換行以 `\n` 存在 `utf8` 內，`join("")` 後自然成形。

**srv3／srv1／srv2／ttml（XML）→ 純文字**

```sh
sed -e 's/<[^>]*>//g' FILE.srv3 \
| sed -e 's/&amp;/\&/g' -e 's/&lt;/</g' -e 's/&gt;/>/g' \
      -e 's/&quot;/"/g' -e "s/&#39;/'/g" -e 's/&#10;/\n/g' \
| awk 'NF'
```

- 先脫標籤，再做 XML 實體還原（`&#10;` 還原為換行）。srv 系列為舊格式，yt-dlp 仍可寫出，但格式變動風險高於 vtt／json3。

**若不想自己剝時間軸**，可讓 yt-dlp 直接跟 YouTube 要 `srt`（`--sub-format "srt"`）或用 `--convert-subs srt` 內部轉換；但 SRT 仍含時間軸，仍需上面的行處理才能得純文字。

### 3.5 沒有字幕的影片會怎樣、怎麼判斷（對應 P5）

| 情況 | yt-dlp 訊息（原始碼／README） |
|---|---|
| 指定語言完全沒有字幕 | `[info] There are no subtitles for the requested languages` |
| 單一語言缺 | `WARNING: <lang> subtitles not available` |
| 缺 PO token 導致語言缺 | `missing subtitles languages because a PO token was not provided` |

- **不要用 exit code 判定**：以上多為 info／warning 級訊息，yt-dlp 一般仍回傳成功。判定應以「輸出檔是否存在」或「metadata 是否有軌」為準。
- **下載前判定（jq-only）**：

```sh
yt-dlp --skip-download --write-info-json -o "%(id)s" "$url"
n=$(jq -r '(((.subtitles // {})|length) + ((.automatic_captions // {})|length))' VIDEO_ID.info.json)
[ "$n" -eq 0 ] && echo "NO_SUBS" || echo "HAS_SUBS"
```

- **下載後判定（檔案存在）**：

```sh
if compgen -G "VIDEO_ID*.vtt" >/dev/null; then echo HAS_SUBS; else echo NO_SUBS; fi
```

### 3.6 單檔執行版與更新（對應 P6 前半）

| 面向 | 內容 |
|---|---|
| 檔名 | `yt-dlp_linux`（官方列為 Alternatives） |
| 大小 | 40,446,224 bytes ≈ 38.6 MiB（本輪 `releases/latest` 實測） |
| 前提 | Linux glibc **2.17+**、x86_64，**免安裝 Python 可直接執行** |
| 自我更新 | 支援 `-U`／`--update`；`.zip` 變體標「no auto-update」 |
| 架構變體 | `yt-dlp_linux_aarch64`、`yt-dlp_musllinux`（musl 1.2+）、`yt-dlp_linux_armv7l`（glibc 2.31+） |
| 更新頻道 | `stable`（預設，約每月、官方自承常 stale 易壞）、`nightly`（官方建議一般使用者）、`master`（canary） |
| 發佈節奏 | 近幾版 2026.08.19、07-04、06-09、03-17，約每月一次但不定期 |

```sh
curl -L -o yt-dlp_linux https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux
chmod +x yt-dlp_linux
./yt-dlp_linux --version
./yt-dlp_linux --update-to nightly   # 或 -U（依現行頻道更新）
```

**重要注意（與 issue 第 4 點直接相關）**：

1. **容器基礎映像決定檔名**：Ubuntu/Debian（glibc）用 `yt-dlp_linux`；Alpine（musl）須用 `yt-dlp_musllinux`。
2. **JS runtime 是另一個依賴**：README 明列完整 YouTube 支援需 `yt-dlp-ejs` ＋ JS runtime（推薦 `deno`）。官方 executable 內含 ejs，但 `deno` 需自行放入映像；無 JS runtime 時預設 client 會捨去 `web`。
3. **worker 無狀態，`-U` 會失效**：`MyLinuxPool` 的 worker 不掛持久卷（`draft`，未經他 review），`-U` 更新的檔案在容器刪除後消失。可維運做法是把 `yt-dlp_linux`（與 `deno`）**烘進映像**或於容器啟動時抓取，而非依賴 `-U`。

**YouTube 改版時的常見壞法與對策**：

| 壞法 | 症狀 | 對策 |
|---|---|---|
| 簽章／nsig 混淆變更 | `Unable to extract nsig`／擷取失敗 | 升到 `nightly`；放入 JS runtime（`deno`）以跑 ejs |
| 格式 URL 403 | `HTTP Error 403` | 更新版本；必要時換 client（`--extractor-args "youtube:player_client=..."`） |
| PO token 要求 | 部分格式無法下載／字幕語言缺 | 更新版本；多數情況非字幕路徑必要 |
| 機器人驗證 | `Sign in to confirm you're not a bot` | cookies（見 §3.7，與零憑證原則相衝） |

### 3.7 被擋情境的行為（對應 P6 後半）

| 情境 | yt-dlp 訊息（原始碼實訊） | 行為與對策 |
|---|---|---|
| 率限／429 | `This content isn't available, try again later` | 帳號被限流，官方註記最長約 1 小時；用 `-t sleep`（preset alias）或 `--sleep-requests` 降速 |
| 需要登入 | 失敗原因含 `sign in`，附 cookies 登入提示 | 需 `--cookies` 或 `--cookies-from-browser` |
| 機器人驗證 | `Sign in to confirm you're not a bot` | 同上，需 cookies |
| 年齡限制 | `age-restricted; some formats may be missing without authentication` | 需 cookies；`web_embedded` client 對可嵌入影片有機會繞過 |
| 驗證碼 | `requiring a captcha challenge` | 需人工或 cookies，難自動化 |
| 部分 client 被跳過 | client 因 403 被略過 | yt-dlp 自動改用其他 client，屬正常降級 |

⚠️ **與既有架構原則的相衝**：`MyLinuxPool`（`draft`）明記 **worker 不持有任何憑證**。需要登入／年齡限制的影片在此架構下無法用 cookies 繞過——把 cookies 放進 worker 即違反該原則。這一類影片只能落為「無法取得」或改由持有憑證的一側處理。

### 3.8 可直接複製的端到端範例

```sh
#!/usr/bin/env bash
# 只抓 YouTube 字幕 → 純文字。用法: ./get_subs.sh <URL>
set -eu
url="$1"

# 1) metadata（不下載影片）
yt-dlp --skip-download --write-info-json -o "%(id)s" "$url"
info=$(ls -t *.info.json | head -1)          # 假設當前目錄只處理此影片
vid=$(jq -r '.id' "$info")

# 2) 依 原語言 → 中文 → 日文 → 英文 選語言
orig=$(jq -r '.language // empty' "$info")
avail=$(jq -r '(((.subtitles // {})|keys)+((.automatic_captions // {})|keys))|unique|join(",")' "$info")
chosen=""
for c in "$orig" zh-Hans zh-Hant zh-CN zh-TW zh ja en; do
  [ -n "$c" ] || continue
  case ",$avail," in *",$c,"*) chosen="$c"; break;; esac
done
[ -n "$chosen" ] || { echo "NO_SUBS: $vid"; exit 0; }

# 3) 下載該語言字幕（vtt）
yt-dlp --skip-download --write-subs --write-auto-subs \
  --sub-langs "$chosen" --sub-format "vtt" \
  -o "%(id)s.%(ext)s" "$url"

# 4) vtt → 純文字
vtt=$(ls "$vid.$chosen"*.vtt 2>/dev/null | head -1 || true)
[ -n "$vtt" ] || { echo "NO_SUBS: $vid"; exit 0; }
sed -e '/^WEBVTT/d' -e '/^NOTE\b/d' -e '/^STYLE/d' -e '/-->/d' \
    -e 's/<[^>]*>//g' -e 's/\r$//' "$vtt" \
| awk 'NF' | awk '$0!=prev{print}{prev=$0}' > "$vid.$chosen.txt"

echo "OK: $vid.$chosen.txt"
```

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 第二大腦查證結果

**先讀骨幹索引 `判定總表`，再讀個案。** 第二大腦**無 yt-dlp 的獨立技術評估**，但同軸（字幕／逐字稿抽取、瀏覽器自動化、ASR）他已有數筆判定：

| 標的 | 判定 | 判定理由 | 來源／信任層級 |
|---|---|---|---|
| **Agent Reach**（把 yt-dlp 當 youtube 渠道的系統） | **不採用** | 「不如直接搬瀏覽器上去」，維護多平台 adapter 成本太高；並記錄「B 站通用下載工具（yt-dlp）被風控 412 封死」 | [Agent Reach.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Agent%20Reach.md)（`human:fatesaikou`、`stable`，**他本人定案**，2026-06-27） |
| **Meetily**（本地 ASR 會議助理） | **不採用** | 「側錄困難，價值只剩 STT，不急著試」 | [Meetily.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Meetily.md)（`human:fatesaikou`、`stable`，**他本人定案**，2026-07-12） |
| **VoiceStudio**（本地語音工作台，含 STT） | **試用（Weak）** | aiagent 通用語音能力有意義，但含前端架構不必要，只需測能力邊界 | [VoiceStudio.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/VoiceStudio.md)（`process:learn-gh-agent`、`draft`，**AI／流程草稿未經他 review**，2026-09-21） |
| **video-use**（把影片轉逐字稿供 agent 用） | **不採用** | 影片剪輯他用不到；同軸剪輯工具 OpenCut-AI 亦已不採用 | [video-use.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/video-use.md)（`ollama-cloud/deepseek-v4.1-flash`、`draft`，**AI 草稿未經他 review**，2026-10-05） |
| **Browser-use／EIAgent** | **不採用** | 「效率不優，乾脆自己兜好；瀏覽器自動化這個需求方向值得自己做」 | [Browser-use, EIAgent 之瀏覽器操作自動化.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Browser-use,%20EIAgent%20之瀏覽器操作自動化.md)（`human:fatesaikou`、`stable`，**他本人定案**，2026-05-10） |
| **ego-lite**（瀏覽器自動化） | **試用** | 架構優勢真實存在，進 MVP 試用但主力留 BrowserBase | [ego-lite.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/ego-lite.md)（`claude-code/opus-5`、`draft`，**AI 草稿未經他 review**，2026-08-01） |

**判準來源（骨幹）**：

| 檔案 | 關鍵準則 | 信任層級 |
|---|---|---|
| [技術取捨準則.md](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md) | ①理解優先（不穩定或不熟悉先自己兜）②MVP→Feature 唯一閘門＝能否影響個人 workflow ③Reject ≠ 沒價值，仍抽取需求理解與方案方向 ④汰換看上游死沒死，不看有沒有更好的（不追新）⑤不要人工審核關卡，要補驗證機制 | `claude-code/opus-5`、`draft`（**AI 草稿未經他 review**；檔內「原話：」引號內為他本人結論） |
| [判定總表.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md) | 索引；明寫「不採用不等於沒價值」 | `ollama-cloud/deepseek-v4-flash`、`draft`（**AI 草稿未經他 review**） |
| [個人 AiAgent 入口.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/個人%20AiAgent%20入口.md) | app 要吃 YouTube 連結抽逐字稿；**低成本硬約束、不自己跑 ASR** | `claude-code/opus-5.5`、`draft`（**AI 草稿未經他 review**） |
| [MyLinuxPool.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/MyLinuxPool.md) | worker 為無狀態 Linux 容器、**不持有任何憑證** | `ai:claude-opus-5`、`draft`（**AI 草稿未經他 review**） |

### 4.2 替代方案與 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **yt-dlp（本標的）** | CLI 呼 innertube 取 player response，挑字幕軌寫檔；純文字另以 jq/awk/sed 轉 | glibc 2.17+ 容器；完整 YouTube 支援另需 deno；被登入／年齡限制需 cookies | 需隨 YouTube 改版更新；worker 無狀態需烘進映像；cookie 路徑與零憑證原則相衝 | 同時取人工＋自動字幕，覆蓋多語言與多格式；成熟、活躍、Unlicense |
| **youtube-transcript-api（Python 套件）** | 直接對 YouTube 的 timedtext 端點取字幕，回結構化片段 | 需 Python 環境；純抓字幕，不管其他 | 與「不用 Python」的轉檔約束同語言的另一入口；端點異動時同受影響；不處理被擋情境 | 呼叫極簡、回傳已是結構化資料，轉純文字不需解析 vtt |
| **第三方逐字稿 API／SaaS（如通用 ASR API 或字幕服務）** | 送 URL 或音訊，回逐字稿 | 需外部憑證與網路；多為付費、按量計費 | 資料離機、隱私外洩風險；需憑證（與零憑證相衝）；供應商停服風險 | 免自建維護、免隨改版修；代價是成本與外部依賴 |
| **瀏覽器自動化（Playwright／ego-lite／Browser-use）** | 開觀看頁、展開字幕面板、抓 DOM 文字 | 需常駐瀏覽器與 headless 環境 | 資源重、脆、維護成本高；其工具方向他判「效率不優」 | 理論上能讀一切前端可見內容，繞過 API 變動 |
| **自跑 ASR（faster-whisper／Meetily／VoiceStudio）** | 下載音訊→本地語音辨識→逐字稿 | 需下載媒體與 GPU／CPU 算力 | 偏離「低成本、不自己跑 ASR」硬約束；品質與速度取決於模型 | 對「完全沒有字幕」的影片是唯一補位手段 |

### 4.3 各方案切入點差異

- **yt-dlp**：切入點是「**用既有字幕軌，不下載媒體**」。它吃到的是 YouTube 已經產好的字幕，成本最低、覆蓋最廣。
- **youtube-transcript-api**：切入點是「**只做字幕這一件事的專用客戶端**」。比 yt-dlp 更薄，但不解決被擋與改版之外的其他需求。
- **第三方 API／SaaS**：切入點是「**把維護與反爬成本外包**」。以憑證與費用換取穩定。
- **瀏覽器自動化**：切入點是「**用前端可見性繞過 API**」。能讀一切，但最脆最重。
- **自跑 ASR**：切入點是「**不依賴 YouTube 是否有字幕**」。唯一能補位無字幕影片，但直接違反既定硬約束。

### 4.4 與第二大腦既有判定的衝突（對照最有價值處）

| 衝突點 | 第二大腦既有立場 | 本標的的情形 | 判定 |
|---|---|---|---|
| **「不如直接搬瀏覽器上去」** | Agent Reach（`stable`，**他本人定案**）拒絕整套系統，理由含「不如直接搬瀏覽器上去」，且該系統把 yt-dlp 當 youtube 渠道。 | yt-dlp 被該 verdict 直接點名。 | **明確衝突**。但該 verdict 的對象是「多平台 adapter 系統的整體維護成本」，不是「單一工具抓 YouTube 字幕的能力」；其記錄的 yt-dlp 封鎖發生在 **B 站（412）**，非 YouTube。因此衝突的是「用它兜一整套系統」的用法，不是「用它的字幕路徑」。**若要把本標的升格成平台抽象層，才會正面撞上此結論。** |
| **「不自己跑 ASR」硬約束** | 個人 AiAgent 入口（`draft`）明寫低成本硬約束、不自己跑 ASR。 | 本標的走 YouTube 既有字幕軌，不下載音訊、不跑 ASR。 | **相符**。這條約束反過來排除了 DA 表最後一列（自跑 ASR）與部分第三方 API（若其實作是 ASR）。yt-dlp 的字幕路徑是唯一同時滿足「低成本」與「不跑 ASR」者。 |
| **worker 不持有任何憑證** | MyLinuxPool（`draft`）明記 worker 不持有任何憑證。 | §3.7 的登入／年齡限制情境標準對策是 cookies。 | **明確衝突**。把 cookies 放進 worker 即違反零憑證原則。此架構下，需登入或年齡限制的影片無法以本路徑取得，只能落為「無法取得」或改由持憑證的一側處理。 |
| **「不追新／汰換看上游死沒死」** | 技術取捨準則（骨幹，`draft`）：不追新；汰換看上游死沒死。 | yt-dlp 自 2020 活躍至今，196k stars、持續發佈。 | **相符**。上游未死，不觸發汰換；本輪是「使用既有活躍工具」，非「採用新系統」。 |
| **「理解優先：先自己兜」** | 技術取捨準則（骨幹，`draft`）：不穩定或不熟悉先自己兜，MVP 是理解驗證點。 | yt-dlp 成熟穩定；且它是既有工具而非待導入的新框架。 | **不衝突**。此準則的觸發條件是「不夠穩定或不熟悉」，本標的兩者皆非；反而是「成熟工具直接使用」的典型。 |
| **瀏覽器自動化方向** | Browser-use（`stable`，**他本人定案**）判「效率不優，乾脆自己兜好」；ego-lite（`draft`）判試用。 | DA 表第 4 列以瀏覽器抓字幕。 | **不建議**。以瀏覽器抓字幕會落入他對既有瀏覽器自動化工具「效率不優」的否定，且成本遠高於 API 路徑。 |

### 4.5 可抽取的方向與結論

即使不採用任何外部框架，本輪仍有兩個可抽取的方向：

1. **「字幕軌是獨立資源」的分層**：把「取字幕」與「取媒體」在協定層切開（yt-dlp 靠 `subtitles` / `automatic_captions` 兩個資料結構實現）。這是可轉移到任何影音平台的通用結構。
2. **「集合過濾 ＋ 外部優先序選擇器」的模式**：工具本身只做集合過濾（`--sub-langs`），優先序由呼叫端以 shell／jq 決定。這與他既有「約束放 harness、領域規則不住在被操作系統之外」的偏好一致。

> **結論**：本輪是**操作型需求**（怎麼下指令），不是技術採用判定。yt-dlp 的字幕路徑同時滿足「低成本」與「不自己跑 ASR」兩條既有硬約束，且在 MyBrain 中**無相反的獨立否定**（Agent Reach 拒絕的是整套多平台系統，非單一字幕能力）。**唯一正面衝突在於被擋情境**：需要登入或年齡限制的影片，其標準對策（cookies）與 `MyLinuxPool`「worker 不持有任何憑證」直接相衝，此架構下無解。因此建議的邊界是：**將 yt-dlp 定位為 worker 內「取 YouTube 既有字幕」的單一工具，不擴張為平台抽象層；對需登入的影片明確回報無法取得，不做 cookie 注入。**
