# 291_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1：取得 `browser-use/video-use` 的 repo metadata 與主要文件。標的是一個「coding-agent skill（video editing）」，非獨立可執行軟體，故主要文件＝README.md、SKILL.md（skill 本體）、install.md（安裝契約），加上 `helpers/` 六支腳本（真正的編輯引擎）與 `skills/manim-video/`（vendored 子 skill）。C1 需先盤點：定位、機制、pipeline、helpers、硬規則、依賴與限制、檔案結構，供 C2 補通用背景與替代方案。R1 首次調研，非追問。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh api repos/browser-use/video-use` | 取 metadata | stars/license/語言/時序 | 28,075 stars、3,312 forks、MIT、Python、created 2026-04-12、pushed 2026-10-02、open issues 145、topics 空、無 release |
| `gh api .../git/trees/main?recursive=1` | 取完整結構 | 確認組成 | 47 路徑：README/SKILL/install、helpers/×6、skills/manim-video/、tests/×3、poster.html、static/、pyproject.toml |
| `gh api .../readme` | 取 README | 定位與用法 | 一句定位、六項功能、Setup prompt、兩層讀取機制、pipeline 圖、5 設計原則 |
| 讀 `SKILL.md`（342 行） | 取 skill 主檔 | 機制、硬規則、流程 | 7 principles、12 hard rules、8 步流程、cut craft、EDL 格式、動畫/字幕/音樂、anti-patterns |
| 讀 `install.md`（162 行） | 取安裝契約 | 依賴與環境 | clone→deps→ffmpeg→註冊 skill→ElevenLabs key→驗證 |
| 讀 `helpers/*.py` 頭段 | 認識編輯引擎 | 確認每個 helper 職責 | transcribe/batch、pack、timeline_view、render、grade；render 實作「分段抽取→lossless concat→overlay PTS 位移→字幕最後」 |
| `gh api .../commits` + languages | 確認活躍度 | 版本演進 | 最新 2026-09-24（captions/音效/fonts/critic）；Python 87,657B、HTML 19,975B、Shell 921B |
| 讀 `skills/manim-video/README.md` | 確認 vendored 子 skill | 動畫引擎來源 | 3Blue1Brown 式數學動畫生產線，需 Manim CE + LaTeX |

**關鍵事實整理**

| 面向 | 內容 |
|---|---|
| 一句定位 | 用對話剪片的 agent skill：丟原始素材進資料夾，跟 Claude Code 對話，拿回 `final.mp4` |
| 核心機制 | **LLM 不看影片，用「讀」的**：Layer1 ElevenLabs Scribe 逐字稿（word-level + 講者分離 + 音訊事件）打包成 ~12KB `takes_packed.md`；Layer2 按需 `timeline_view` 產生 filmstrip+waveform PNG。對比 naive 30,000 幀＝45M tokens |
| Pipeline | Transcribe → Pack → LLM Reasons → EDL → Render → Self-Eval（問題則修+重渲染，上限 3 輪） |
| 主要功能 | 去贅字/停頓、自動調色、30ms 音訊淡入淡出、燒字幕、動畫 overlay（HyperFrames/Remotion/Manim/PIL，平行 sub-agent）、輸出前自我評估、`project.md` 跨 session 記憶 |
| 12 Hard Rules | 字幕最後、分段抽取+`-c copy` concat、每段 30ms fade、overlay `setpts` 位移、SRT 用 output-timeline offset、不切字、切點 30–200ms padding、word-level 逐字、快取逐字稿、動畫平行、先確認策略、輸出全在 `edit/` |
| 依賴 | Python≥3.10（requests/librosa/matplotlib/pillow/numpy）、ffmpeg 硬需求、**ElevenLabs API key（Scribe 付費）**、yt-dlp 選用、Node 22+（HyperFrames/Remotion）、Manim+LaTeX 選用 |
| 安裝 | 手動 symlink 整個 repo 進 agent skills 目錄；或貼 Setup prompt 讓 agent 自理 |
| 品質保證 | 內建 3 個 unittest（captions/fps/orientation），無 CI |

**發現的出入（需在報告標記）**

| 項目 | PR body／影片 | 一手來源實況 | 判定 |
|---|---|---|---|
| Stars | 28,069 | API 實查 28,075（2026-10-05） | 以 API 為準，差 6 屬正常抖動 |
| 定位敘述 | 「剪視頻的開源 Skill」 | 「Edit videos with coding agents」，agent-agnostic（Claude Code/Codex/Hermes/Openclaw） | 一致，補充非 Claude 專屬 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Repo metadata 完整性 | stars/forks/license/語言/時序/topics/release | 完整（topics 空、0 release，屬早期專案） |
| 文件覆蓋率 | README + tree + SKILL + install + helpers 頭段 | 足以支撐報告 §1–§3 |
| 機制理解 | 兩層讀取、EDL、render 順序、12 硬規則 | 清晰 |
| 依賴與限制 | install.md + pyproject + .env.example | 已取得，關鍵限制＝ElevenLabs 付費外部依賴 |
| 背景脈絡 | browser-use 組織（117k stars，2024-10 成立） | 已補母體；通用領域背景與替代方案留 C2 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 抓取方式 | clone 全 repo／gh api 逐檔 | gh api 逐檔（raw content） | 只需文字文件，免 clone 開銷；helpers 只讀頭段即足 |
| helpers 深度 | 逐支全文精讀／只讀 docstring 頭段／全略 | 只讀頭段 + render 關鍵函式 grep | C1 目標為 metadata 與主要文件盤點，演算法細節留 C2 |
| `manim-video` 處理 | 視為 repo 一部分略過／標記為 vendored 子 skill | 標記為 vendored 子 skill | 是獨立上游 skill，影響 §3「動畫」與 §4「替代」判斷 |
| 影片逐字稿缺失 | 再嘗試抓字幕／改走 repo+網路 | 改走 repo+網路 | AGENTS.md 明令資訊不足時從網路補；影片非一手 |
| ElevenLabs 依賴定位 | 當一般依賴／標為關鍵限制 | 標為關鍵限制 | 付費外部 API 直接影響 §2 背景與 §4 對照（本機/開源替代） |

## 交接給 C2

- 補通用背景：LLM 處理影片的 token 爆炸問題、ASR 逐字稿 vs 幀掃描、ElevenLabs Scribe 付費與開源替代（Whisper、faster-whisper）、ffmpeg 剪輯管線的既有痛點。
- 補替代方案：MyBrain 既有 HyperFrames（採用）、OpenMontage（試用）、OpenCut-AI（不採用），加上 Descript/Opus Clip 等商用，做 DA 表。
- 已可用來源：README 兩層機制與 45M token 對照、SKILL.md 12 硬規則與 anti-patterns、MyBrain 三筆同軸判定。
