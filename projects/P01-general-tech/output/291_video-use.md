# video-use —— 用 coding agent 剪輯影片的 Agent Skill 技術分析

> 標的：https://github.com/browser-use/video-use
> 分析：`tech-research-agent`，2026-10-05
> 來源：GitHub 一周熱點 133 期（https://youtu.be/gv9IGo9qqZM；該影片無字幕軌，逐字稿取不到，本報告事實以 GitHub 一手文件為主）
> 前置查證：第二大腦（FATESAIKOU/MyBrain）**無 `video-use` 此主題**（全 bundle 零命中）。本報告事實來自 repo 的 README / SKILL.md / install.md / helpers 原始碼；個人適用性判斷對照第二大腦的技術取捨準則與同軸判定（HyperFrames / OpenMontage / OpenCut-AI / Browser-use）。

---

## 1. 這個技術解決什麼問題？

video-use 解決的問題是：**讓 coding agent（Claude Code / Codex / Hermes / Openclaw 等）能剪輯「既有的原始影片素材」，且在剪輯前不必用多模態方式「觀看」整支影片。**

拆成三層具體問題：

| # | 子問題 | 具體痛點 |
|---|---|---|
| P1 | **影片不可被 LLM 有效讀取** | 影片是時間軸上的像素序列。若把每個影格餵給多模態模型，一支影片的 token 量不可行（repo 舉例：30,000 幀 ≈ 45M tokens）。LLM 無法「看」完整支影片後才剪。 |
| P2 | **剪輯操作缺乏可重現的結構** | 人對 agent 口述「把停頓去掉、加字幕、調色」，若 agent 直接輸出成品，中間決策沒有可檢視的結構，也無法重跑、局部調整、或跨 session 延續。 |
| P3 | **剪輯指令與最終渲染之間易失準** | 分段裁剪、音訊淡入淡出、字幕時軸、overlay 位移等若順序或時軸處理錯誤，成品會出現破音、字幕位移、切點爆音等問題。 |

video-use 的定位是「**用對話剪片**」：把原始素材放進資料夾，對 agent 下指令，拿回 `final.mp4`。

### 問題描述的模糊之處

- **「剪輯」的範圍未在 README 收斂到單一操作集**：repo 同時涵蓋去贅字／停頓、調色、音訊淡化、燒字幕、動畫 overlay、自我評估六類功能，未明確界定哪些屬核心、哪些屬附加。
- **主觀剪輯意圖的品質無客觀衡量**：agent 是否「剪得好」依賴 LLM 的判斷，repo 僅以內建 self-eval 步驟與 3 個 unittest（captions / fps / orientation）作為品質手段，未提供主觀剪輯品質的評估基準。
- **「agent-agnostic」的實際覆蓋範圍未逐一驗證**：README 宣稱支援多個 coding agent，但安裝契約（install.md）以「把整個 repo symlink 進 agent 的 skills 目錄」為通用做法，各 agent 的實際相容性未逐一給出驗證結果。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章（repo 文件）明確提到的背景

- **多模態直接讀影片的成本不可行**：README 的兩層讀取機制以「30,000 幀 ＝ 45M tokens」對比「~12KB 的逐字稿包」，說明設計動機。
- **剪輯需要「文字化的時間軸」而非像素**：video-use 把影格問題轉成 ASR 逐字稿問題——用語音轉文字（word-level timestamp）建立時間基準，讓 LLM 在文字空間做剪輯決策。
- **coding agent 已具備檔案操作與工具調用能力**：這使其能讀取逐字稿、產生 EDL、呼叫 ffmpeg 渲染，因此 skill 只需提供「讀取機制 + 硬規則」，不需要另建一套 agent。

### 通用技術背景（補充）

| 背景項 | 內容 |
|---|---|
| **LLM context 與影片的維度落差** | 影片是「時間 × 空間 × 聲道」的高維訊號，LLM 的 context 以 token 計。把影片降維成「逐字稿（語意＋時間）+ 少量視覺採樣（filmstrip）」是降低跨模態成本的通用手段。 |
| **ASR 逐字稿作為時間索引** | 語音辨識輸出的 word-level timestamp 天然提供「時間軸 ↔ 文字」對應，可作為剪點定位的索引；這是文字剪輯（text-based editing）在 Descript 等工具上的既有做法。 |
| **ffmpeg 剪輯管線的既有痛點** | ffmpeg 是通用剪輯引擎，但分段裁剪 + concat 若用 re-encode 會損失畫質與速度；正確做法是「分段抽取 + `-c copy` lossless concat」。音訊接縫爆音、字幕時軸錯位、overlay 時間基準偏移是常見實作陷阱。video-use 的 12 條硬規則即是對這些陷阱的封裝。 |
| **同一組織的前作** | video-use 屬 `browser-use` 組織（117k stars 的瀏覽器自動化專案之母體）。本專案將「agent 操作既有工具」的模式，從瀏覽器搬到影片剪輯。 |
| **專案成熟度偏低** | repo 建立於 2026-04-12，至 2026-10-05（約 6 個月）達 28,075 stars、3,312 forks，但 open issues 145、無 release、無 CI、僅 3 個 unittest。屬「高關注度、低流程成熟度」的早期高熱專案。 |

---

## 3. 這個技術是如何解決該問題的？

核心做法是「**把影片降維成文字與少量視覺採樣，讓 LLM 在文字空間決策，再用確定性的 ffmpeg 管線渲染**」。整體分為「讀取」與「渲染」兩半。

### 3.1 兩層讀取機制（解決 P1）

```
Layer 1（一次性、全片）
  原始影片 ──► ElevenLabs Scribe 逐字稿
                ├─ word-level timestamps
                ├─ 講者分離（diarization）
                └─ 音訊事件（笑聲、停頓等）
              ──► 打包成 takes_packed.md（~12KB）

Layer 2（按需、區域）
  timeline_view ──► filmstrip + waveform PNG
                    （只針對需要看畫面的時間段產生）

對照：naive 30,000 幀 ≈ 45M tokens
```

LLM 主要讀 Layer 1 的 `takes_packed.md`，只有在需要確認畫面（例如構圖、轉場、調色）時，才要求 Layer 2 的 `timeline_view` 產生對應區段的 filmstrip PNG。

### 3.2 剪輯 Pipeline（解決 P2）

```
Transcribe → Pack → LLM Reasons → EDL → Render → Self-Eval
                                        │              │
                                        │        問題則修 + 重渲染
                                        │        （上限 3 輪）
                                        ▼
                                   final.mp4
```

- **EDL（Edit Decision List）**：LLM 在文字空間產出結構化的剪輯決策清單，而非直接輸出成品。這使剪輯過程可檢視、可修改、可重跑。
- **`project.md` 跨 session 記憶**：把專案狀態落檔，讓 agent 在新 session 接續同一支影片的工作。

### 3.3 硬規則封裝（解決 P3）

repo 的 `SKILL.md` 定義 12 條 hard rules，把 ffmpeg 剪輯的實作陷阱變成 agent 必須遵守的契約：

| 規則（擇要） | 目的 |
|---|---|
| 字幕最後處理 | 避免 overlay 與字幕互相污染時軸 |
| 分段抽取 + `-c copy` concat | 避免 re-encode 損失畫質 |
| 每段 30ms 音訊 fade | 消除切點爆音 |
| overlay 用 `setpts` 位移 | 對齊 overlay 的時間基準 |
| SRT 用 output-timeline offset | 修正 concat 後字幕時軸 |
| 不切開單字、切點 30–200ms padding | 保持語意與聽感的完整 |
| 逐字稿快取 | 避免重複呼叫 ASR |
| 動畫平行、輸出全在 `edit/` | 資源隔離與加速 |

`helpers/` 提供六支 Python 腳本作為編輯引擎：`transcribe` / `batch` / `pack` / `timeline_view` / `render` / `grade`。其中 `render` 實作順序為「分段抽取 → lossless concat → overlay PTS 位移 → 字幕最後」。

### 3.4 動畫 overlay 與子 skill

- 動畫 overlay 支援 **HyperFrames / Remotion / Manim / PIL**，以平行 sub-agent 產生。
- repo 內 vendored 一個子 skill `skills/manim-video/`（3Blue1Brown 式數學動畫生產線，需 Manim CE + LaTeX），屬獨立上游 skill，非 video-use 本體。

### 3.5 依賴與安裝

| 面向 | 內容 |
|---|---|
| 執行環境 | Python ≥ 3.10（requests / librosa / matplotlib / pillow / numpy）、**ffmpeg（硬需求）** |
| 外部服務 | **ElevenLabs API key（Scribe，付費）**——為關鍵外部依賴 |
| 選用 | yt-dlp、Node 22+（HyperFrames / Remotion）、Manim + LaTeX |
| 安裝 | 手動把整個 repo symlink 進 agent 的 skills 目錄；或貼 Setup prompt 讓 agent 自理 |
| 品質保證 | 內建 3 個 unittest（captions / fps / orientation），無 CI |

### 3.6 整體資料流

```
原始素材資料夾
      │
      ▼
 ElevenLabs Scribe ──► takes_packed.md ──┐
                                          ▼
                              LLM（讀文字 + 按需看 filmstrip）
                                          │
                                          ▼
                                        EDL
                                          │
                                          ▼
                    ffmpeg render（分段抽取→concat→overlay→字幕）
                                          │
                                          ▼
                                     final.mp4
                                          │
                                          ▼
                       Self-Eval（問題→修→重渲染，上限 3 輪）
```

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 第二大腦查證結果

**先讀骨幹索引 `判定總表`，再讀個案。** 第二大腦**無 `video-use` 此主題**，但同軸（影片剪輯／影片生成／同一開發組織）他已有數筆判定：

| 標的 | 判定 | 判定理由 | 來源／信任層級 |
|---|---|---|---|
| **HyperFrames** | **採用** | 將 HTML+CSS+animation 逐幀渲染為確定性 MP4；免費、比多模態更穩定且成本更低 | [HyperFrames.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/HyperFrames.md)（`generated.by: human:fatesaikou`、`status: stable`，**他本人定案**，首見 2026-05-31） |
| **OpenMontage** | **試用** | 讓 AI coding assistant 當影片製作總監的純檔案化 pipeline；Accept, 總之研究看看, 使用太複雜就放棄 | [OpenMontage.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OpenMontage.md)（`human:fatesaikou`、`stable`，**他本人定案**，2026-06-27） |
| **OpenCut-AI** | **不採用** | 全棧自託管的 AI 影片剪輯系統；「專為剪輯設計，他用不上，不符日常 workflow」 | [OpenCut-AI.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OpenCut-AI.md)（`human:fatesaikou`、`stable`，**他本人定案**，2026-06-27） |
| **Browser-use, EIAgent（同開發組織）** | **不採用** | 瀏覽器自動化工具；「效率不優，乾脆自己兜好；瀏覽器自動化方向值得自己做」 | [Browser-use, EIAgent 之瀏覽器操作自動化.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Browser-use,%20EIAgent%20之瀏覽器操作自動化.md)（`human:fatesaikou`、`stable`，**他本人定案**，2026-05-10） |

**判準來源（骨幹）**：

| 檔案 | 關鍵準則 | 信任層級 |
|---|---|---|
| [技術取捨準則.md](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md) | ①理解優先（不夠穩定或不熟悉先自己兜，MVP 是理解驗證點）②MVP→Feature 唯一閘門＝能否影響個人 workflow ③Reject ≠ 沒價值，仍抽取需求理解與方案方向 ④汰換看上游死沒死，不看有沒有更好的 ⑤不要加人工審核關卡，要補驗證機制 | `generated.by: claude-code/opus-5`、`status: draft`（**AI 草稿，未經他 review**；但檔內「原話：」引號內為他本人結論） |
| [下一步清單.md](https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md) | **無任何影片剪輯相關的可執行條目** | `generated.by: claude-code/opus-5`、`status: draft`（AI 草稿） |
| [判定總表.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md) | 索引；「不採用」不等於「沒價值」 | `generated.by: ollama-cloud/deepseek-v4-flash`、`status: draft`（AI 草稿） |

### 4.2 替代方案與 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **video-use（本標的）** | 影片降維成 ElevenLabs 逐字稿（+按需 filmstrip）→ LLM 產生 EDL → ffmpeg 確定性管線渲染 | 需 **ElevenLabs Scribe 付費 key**；需 ffmpeg；信任 LLM 在文字空間的剪輯決策；專案僅 6 個月、145 open issues、無 CI | 依賴付費外部服務；早期高熱專案穩定性風險；剪輯品質依 LLM 判斷；驗證面僅 3 unittest | 用對話對既有素材剪片；agent 不需「看」完整支影片；剪輯過程結構化、可重跑 |
| **HyperFrames（已採用）** | HTML + CSS + seekable animation runtime → headless Chrome 逐幀確定性 render → ffmpeg 編碼 MP4 | 需 Node.js ≥ 22、FFmpeg；畫面須以 HTML/CSS 定義 | 只處理「從零生成的畫面」，不處理既有實拍素材的裁剪 | 確定性、低成本地把 HTML 轉影片；比多模態生成穩定 |
| **OpenMontage（已試用）** | 純檔案化 YAML pipeline manifest + Markdown skill 定義工作流，Python 僅做工具不編排 | 需已安裝 AI coding assistant；pipeline 定義較重型 | YAML + Markdown 檔數量多，導入複雜度高（他註明「使用太複雜就放棄」） | 一句話驅動研究→腳本→資產→剪輯→渲染的完整製作流程 |
| **OpenCut-AI（已不採用）** | 全棧自託管系統：瀏覽器端 OPFS + Docker 7 微服務（faster-whisper、XTTS、SD 等）+ EditorCore 三層耦合 | 需 Docker、7 個微服務、大量本地資源；面向完整剪輯工作台 | 極重型、專為剪輯工作台設計 | 本地自託管的 AI 剪輯閉環，素材不離機 |
| **Descript / CapCut 等商用 SaaS（通用參照）** | 雲端文字式剪輯：上傳素材→ASR→在逐字稿上刪字即剪片 | 需上傳素材至雲端；訂閱制 | 隱私外洩、按量計費、素材離機 | 成熟的文字剪輯體驗，但非 agent-driven、非本地 |

### 4.3 各方案切入點差異

- **HyperFrames**：解決「**從零生成畫面**→確定性影片」，是生成端的確定性引擎。
- **OpenMontage**：解決「**一句話驅動的完整製作流程**」，是編排層（YAML manifest），範圍涵蓋研究到渲染。
- **OpenCut-AI**：解決「**本地自託管的完整剪輯工作台**」，是把 SaaS 剪輯器整套搬回本地，最重型。
- **video-use**：解決「**agent 剪既有素材**」，切入點是「把影片降維成逐字稿讓 LLM 讀」，屬剪輯端，且以 coding agent 為宿主。

### 4.4 與第二大腦既有判定的衝突（對照最有價值處）

| 衝突點 | 第二大腦既有立場 | video-use 的情形 | 判定 |
|---|---|---|---|
| **「專為剪輯設計 → 用不上」** | OpenCut-AI 之不採用理由為「專為剪輯設計，他用不上，不符日常 workflow」。此為他本人 `stable` 定案。 | video-use **同屬專為剪輯設計**（且同樣重度依賴剪輯工作流），與 OpenCut-AI 同軸。 | **明確衝突**：若 video-use 的價值命題是「拿來剪片」，則直接撞上他對剪輯工具「用不上」的既有結論。除非 video-use 進入他的日常 workflow（見下），否則不成立。 |
| **同一開發組織前作被判不採用** | Browser-use 組織的瀏覽器自動化工具他判「效率不優，乾脆自己兜好」，且認為該方向值得自己兜。 | video-use 屬同一組織，但領域由「瀏覽器操作」換成「影片剪輯」。 | 非直接衝突：不採用理由（效率、Ollama 接不上）是瀏覽器領域的實測結果，不能直接套到影片剪輯。**不套用其結論，但保留對「自己兜」的傾向。** |
| **理解優先 vs 直接採用現成** | 技術取捨準則第一條：不夠穩定或不熟悉就先自己兜，MVP 是理解驗證點。video-use 僅 6 個月、145 open issues、無 CI。 | 成熟度低，正落在「不夠穩定」的觸發條件；且他已採用 HyperFrames 作為確定性影片引擎，具備自己兜的積木。 | 「**先自己兜**」準則與「直接採用 video-use」衝突。 |
| **驗證機制 vs 低驗證面** | 準則第五條：約束放 harness，要補驗證機制（測試、validator、CI、可回滾），不要人工審核關卡。 | video-use 的品質保證僅 3 個 unittest、無 CI；self-eval 依賴 LLM 判斷。 | 「**補驗證機制**」準則與 video-use 目前薄弱的驗證面衝突。 |
| **workflow 閘門** | MVP→Feature 唯一閘門＝能否影響個人 workflow。`下一步清單` 無影片剪輯條目。 | 影片**生成**（HyperFrames）有採用紀錄，影片**剪輯**（既有素材裁剪）未見日常需求。 | 依閘門，video-use 的採用前提是「剪既有素材」進入他的日常 workflow；未見證據。 |

### 4.5 可抽取的方案方向（依準則第三條：Reject ≠ 沒價值）

即使不採用，video-use 仍提供兩個可抽取的設計方向：

1. **「用逐字稿降維影片」的讀取模式**：以 ASR word-level timestamp 作為時間索引，取代逐幀多模態掃描，把影片問題轉成文字問題。此方向可套用到任何需要 LLM 理解長時序影音素材的場景。
2. **「EDL + 硬規則封裝」的渲染契約**：把 LLM 的剪輯決策輸出成結構化 EDL，再由確定性管線（分段抽取 → `-c copy` concat → overlay 位移 → 字幕最後）渲染。此模式與他既有的 HyperFrames「確定性 HTML → 影片」在精神上同構——都是「把不確定的生成與確定的渲染分離」。

> **結論**：video-use 的獨特切入點是「**把影片降維成逐字稿讓 coding agent 在文字空間剪輯**」，與既有判定分岔如下——HyperFrames 是「生成端確定性引擎」、OpenMontage 是「編排層」、OpenCut-AI 是「本地完整工作台」。然而其**領域（專為剪輯）與 OpenCut-AI 同軸且後者已被他本人判不採用**，其**成熟度低與驗證面薄弱則與他的「理解優先」與「補驗證」準則衝突**。因此採用與否的判準不在技術優劣，而在：**「剪既有素材」是否進入他的日常 workflow（閘門）**，以及**是否值得先自己兜一個理解裝置（理解優先）**。
