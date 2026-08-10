# MiniMax-H3 技術分析報告

> 調研日期：2026-08-09
> 資料來源：GitHub `MiniMax-AI/MiniMax-H3`（README、repo 結構）、HuggingFace model card 與 LICENSE、model_index.json
> 標的：MiniMax 開源的全模態（text/image/video/audio）音視頻生成模型

---

## 1. 這個技術解決什麼問題？

MiniMax-H3 解決的是「**用單一模型，從文字、圖片、影片、音訊的任意組合輸入，直接生成帶同步音訊的影片**」這個問題。

具體拆解為三個子問題：

| 子問題 | 具體痛點 |
|---|---|
| **P1 全模態輸入** | 過去文生影片（t2v）只能吃文字；H3 可吃 0/1/2 張圖（FL2VA）或 ≤9 圖、≤3 影片、≤3 音訊、混合 ≤12 檔（Ref2VA），把「參考圖／參考影片／參考音訊」一起當條件 |
| **P2 音畫同步生成** | 多數影片模型只出畫面，音訊要另外用 TTS/音效模型補，容易對不上嘴型與節奏；H3 在單一模型內同時生成 32kHz 立體聲音訊與畫面 |
| **P3 解析度與時長** | 輸出 4–15 秒、最高 2K、24 FPS，並提供 768p→2K 的再生（Regenerate-2K）流程 |

**問題描述的模糊之處**：issue 標籤誤標為「HuggingFace 連結」，實際是 GitHub repo。此外「全模態」一詞在 README 中指的是「輸入模態全」，但**輸出只有影片＋音訊**，不是「輸出也全模態」——這點容易誤讀。另「開源」需限定：**只有 H3-Base 開源**，Context-IR 與 Regenerate-2K 兩模組僅以 API 提供，未開源。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- MiniMax 於 2026-07-28 在 HuggingFace 發布 H3，2026-07-30 建立 GitHub repo
- 授權為 MiniMax H3 Community License（2026-08-02），**排除地域：EU、UK、韓國、美國**；年營收 >2000 萬美元需另行授權
- 三模組架構：H3-Context-IR（hosted 預處理/編排）→ H3-Base（開源）→ H3-Regenerate-2K（hosted 再生）

### 通用技術背景

**問題發生的根源：影片生成模型長期「只出畫面、不出聲音」，且輸入模態單一。**

| 背景限制 | 說明 |
|---|---|
| 模態割裂 | 文生影片（Sora、Veo、Kling 等）多為「文字→畫面」單向；音訊靠外部 TTS/音效模型事後合成，音畫同步靠後製對齊 |
| 輸入條件單一 | 早期模型只能吃文字 prompt，無法把參考圖／參考影片／參考音訊當作生成條件，難以做角色一致性、風格遷移 |
| 解析度瓶頸 | 高解析度影片生成計算量極大，多數模型先出低解析再超分，或直接限制在 720p/1080p |
| 時長瓶頸 | 自回歸式影片生成隨幀數線性增長成本，多數模型限制在數秒內 |

**歷史脈絡**：2024–2026 年影片生成從「文生圖的時序延伸」演進到「世界模型／全模態生成」。MiniMax 過去以 LLM（MiniMax-Text）與語音模型見長，H3 是其把「音訊生成能力」與「影片生成能力」合併到單一 Transformer 的嘗試。同期 NVIDIA Cosmos、Google Veo、OpenAI Sora 也在做類似「多模態統一生成」的收斂。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 整體架構（三模組）

```
使用者輸入（文字/圖/影片/音訊）
        │
        ▼
┌─────────────────────────────────────────────┐
│ H3-Context-IR（hosted，未開源，僅 API）      │
│   預處理輸入、編排 prompt、決定生成策略        │
└────────────────────┬────────────────────────┘
                     ▼
┌─────────────────────────────────────────────┐
│ H3-Base（開源，768p）                         │
│   33B dense 單流 Transformer                 │
│   + H3-Encoder（Qwen3-VL-32B 第50層）         │
│   + H3-VisualVAE + H3-AudioVAE               │
│   輸出：768p 影片 + 32kHz 立體聲音訊           │
└────────────────────┬────────────────────────┘
                     ▼
┌─────────────────────────────────────────────┐
│ H3-Regenerate-2K（hosted，未開源，僅 API）    │
│   768p → 2K 再生                             │
└─────────────────────────────────────────────┘
```

### 3.2 H3-Base 核心機制

| 元件 | 機制 | 作用 |
|---|---|---|
| **主幹** | 33B dense 單流 Transformer；約 13B 參數在 AdaLN 分支（可預計算快取，inference-only 不需載入） | 統一處理多模態 token |
| **位置編碼** | MM-RoPE 三維位置編碼 | 在空間（寬×高）與時間三維上定位 token，支援影片時序 |
| **注意力** | 原生支援 sparse attention，但**初始開源版僅 full attention** | 降低長序列計算（尚未在開源版啟用） |
| **H3-Encoder** | 用 Qwen3-VL-32B 完整預訓練權重，取第 50 層 hidden states | 把文字/圖片/影片編碼成條件 token |
| **H3-VisualVAE** | f16t4d24，時空因果，patch 1×2×2 → 有效空間 32×、時間 4× | 把影片壓縮到 latent 空間再還原 |
| **H3-AudioVAE** | 32kHz→40Hz latent，左右聲道獨立處理再合併 | 生成立體聲音訊 latent |

### 3.3 兩個 checkpoint（輸入模態差異）

| Checkpoint | 輸入條件 | 用途 |
|---|---|---|
| **H3-Base-FL2VA** | t2va / fl2va：0/1/2 張圖 | 純文字或少量參考圖生成 |
| **H3-Base-Ref2VA** | ref2va：≤9 圖、≤3 影片、≤3 音訊、混合 ≤12 檔 | 多參考條件生成（角色一致性、風格遷移） |

### 3.4 輸出規格

- 時長：4–15 秒
- 解析度：最高 2K（768p 原生，2K 需 Regenerate-2K API）
- 幀率：24 FPS
- 音訊：32kHz 立體聲
- 語言：11 種語言穩定支援

### 3.5 部署方式

SGLang、vLLM、diffusers（`MiniMaxH3ModularPipeline`）、ComfyUI。2K 流程需結合本地 H3-Base + 官方 Context-IR / Regenerate-2K API。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

以下替代方案分兩類：**通用影片生成模型**（與 H3 同級的直接競爭）與 **MyBrain 中已評估過的相關技術**（含判定）。

### 4.1 通用影片生成模型（同級替代）

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Google Veo** | 閉源雲端文生影片，高品質、長時長、原生音訊 | 需 Google 雲端 API、付費、網路連線 | 閉源不可自託管、資料離機、成本按用量 | 高品質影片，但無法本地部署、無法自訂 |
| **OpenAI Sora** | 閉源雲端文生影片，擴散式時空建模 | 需 OpenAI API、付費 | 閉源、成本高、音訊需另接 | 高品質長影片，但封閉 |
| **快手 Kling** | 閉源雲端文生影片，主打動作與物理合理性 | 需快手 API、付費 | 閉源、地域限制 | 動作自然，但封閉 |
| **阿里 Wan（萬相）** | 開源影片生成模型，多模態輸入 | 需 GPU 部署、開源授權 | 開源但需自建推理、音訊能力視版本 | 可自託管，但音畫同步能力弱於 H3 |

### 4.2 MyBrain 已評估過的相關技術（含判定）

| 技術名 | MyBrain 判定 | 信任層級 | 與 H3 的關係 |
|---|---|---|---|
| **NVIDIA Cosmos** | **Reject**（「方向有趣，但我很難使用」） | `human:fatesaikou` / `stable` | 同為「多模態統一生成」路線，但 Cosmos 偏世界模型／機器人模擬，H3 偏內容生成 |
| **HyperFrames** | **Accept**（「免費且將確定性 HTML 變成影片很有價值」） | `human:fatesaikou` / `stable` | 反方向：用確定性 HTML 渲染影片，而非生成式；其結論明言「多模態不能很好解決穩定性的議題」 |
| **OpenMontage** | **Accept**（「總之研究看看」） | `human:fatesaikou` / `stable` | 影片製作 pipeline 編排，非生成模型本身 |
| **OpenCut-AI** | **Reject**（「專 For 剪輯，我用不上」） | `human:fatesaikou` / `stable` | 影片剪輯，非生成 |
| **LingBot-Map** | **Reject**（「主要應用於平面影像建模」） | `human:fatesaikou` / `stable` | 3D 重建，非生成 |

> 以上 MyBrain 判定來源：`技術/技術評估/判定總表.md`（`generated.by: ollama-cloud/deepseek-v4-flash`、`status: draft`，索引檔，非本人逐字定稿）。各單篇判定為 `human:fatesaikou` 本人寫、`stable`。GitHub URL：`https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/<檔名>.md`。

### 4.3 切入點差異與對照

| 面向 | MiniMax-H3 | NVIDIA Cosmos | HyperFrames | Veo/Sora/Kling |
|---|---|---|---|---|
| 開源 | 部分（僅 H3-Base） | 開源 | 開源 | 閉源 |
| 音畫同步 | 單一模型內建 | 未強調 | 無（純畫面） | 部分內建 |
| 輸入模態 | 文字/圖/影片/音訊 | 文字/影像/動作 | HTML/CSS | 文字/圖 |
| 定位 | 內容生成 | 世界模型/機器人 | 確定性渲染 | 內容生成 |
| 可自託管 | 是（H3-Base） | 是 | 是 | 否 |

**與 MyBrain 既有判定的衝突點**：HyperFrames 的結論是「多模態生成不能很好解決穩定性議題，所以用確定性 HTML 渲染」。H3 走的是「多模態生成」路線，兩者對「影片該怎麼產」的切入點相反——H3 追求生成品質與模態統一，HyperFrames 追求確定性與低成本。這不是矛盾，而是同一需求（產出影片）的兩條不同解法軸。

**第二大腦中沒有**：MyBrain 的 `技術/技術評估` 中**沒有**對 MiniMax-H3、Veo、Sora、Kling、Wan 的直接評估記錄（僅有 Cosmos、HyperFrames、OpenMontage、OpenCut-AI 等相關但不同標的的判定）。因此 H3 本身是全新標的，本報告 §4 的通用影片生成模型（Veo/Sora/Kling/Wan）為一般知識補查，非 MyBrain 既有結論。

### 4.4 依技術取捨準則的觀察（供判斷材料，非採用建議）

依 `技術/技術評估/判定總表.md` 與 `抽象理解/本質洞察/技術取捨準則.md`（兩者皆 `status: draft`，AI 產出未經本人 review）：

- **理解優先**：H3 屬「不熟悉」的技術，符合「先自己兜／先理解」的觸發條件；但 33B 模型對個人硬體門檻高，理解成本不低。
- **MVP→Feature 閘門**：能否影響個人 workflow 是唯一閘門。H3 屬影片生成，與他既有的 HyperFrames（確定性渲染）路線不同，是否進 workflow 需他自行判斷。
- **Reject≠沒價值**：即使不採用，H3 的「單一模型音畫同步」「多參考條件輸入」是可抽取的需求理解與方案方向。
- **不追新**：H3 發布僅約兩週（2026-07-28），符合「不追新」原則下的觀望特徵。

> 以上為依 MyBrain 準則的推論，非本人拍板結論；是否採用由使用者判斷。

---

## 5. User Q&A

> 本節為 R2 使用者追問（PR chat）的構造化 QA。三問皆質問型句構，觸發本節。回答資料來源：R1 報告既有事實 ＋ R2 Step 2 補查（SGLang cookbook、MiniMax PAYGO 定價頁、H3 video-generation API guide、README/model card）。

### Q1：這東西拿來寫程式，CP 值或效能能比肩 deepseek-v4-0731-flash 之頂尖流嗎？

**A**：不能，且此比較基準不成立——**H3 不是程式碼生成模型，與 deepseek-v4 屬不同賽道，無 CP 值可比性**。

| 面向 | MiniMax-H3 | deepseek-v4-0731-flash |
|---|---|---|
| 模型類型 | 全模態**生成**模型（輸入→影片+音訊） | coding/agent **LLM** |
| 輸出 | 影片（mp4）+ 32kHz 立體聲音訊 | 文字／程式碼／工具呼叫 |
| 程式碼生成能力 | **無**（repo/model card 均無此宣稱） | 核心能力 |
| 上下文 | 影片 token 序列 | 1M context、XML tool calling |
| 用途 | 影音內容生成 | 寫程式、agent 任務 |

**佐證**：H3 repo 的 9 個 skills 中，`h3-prompt-writing` 是「影片 prompt 撰寫」skill，其餘 8 個是 MiniMax Hub 的影片風格 skill——**皆非程式生成工具**。deepseek-v4 的定位見 MyBrain `技術/技術評估/DeepSeek V4.md`（`human:fatesaikou`／`stable`，2026-04-26）：1M 上下文、XML tool calling、Agent 一等公民，屬 coding/agent 模型。

**反證表（若硬要拿來寫程式）**：

| 假設 | 結果 |
|---|---|
| 用 H3 生成程式碼 | 無此輸出路徑，輸出固定為影片 |
| 用 H3 當 coding agent | 無 tool calling、無文字輸出，無法執行 |
| 用 deepseek-v4 生成影片 | 無影片輸出能力，屬另一模型 |

**結論**：H3 與 deepseek-v4 是兩類不同工具，前者解決「生成影音」，後者解決「寫程式／跑 agent」。拿 H3 寫程式等同拿影片生成器當編譯器，不存在 CP 值比較的基準。

---

### Q2：這東西比起其他同類模型，有何對一般使用者友善的點（除了開源，比如足夠小可自架、或很便宜）？

**A**：**自架門檻高、API 不便宜、且無訂閱折扣**——對一般使用者友善度低，開源是唯一明顯友善點。

**自架硬體門檻**（SGLang 官方驗證配置）：

| 配置 | 需求 | 備註 |
|---|---|---|
| 最低（offload） | 2×RTX 5090（各 32GB）＋ 384GiB 主機 | 需 layerwise offload，lossless BF16 |
| 資料中心級 | 4×H100 80GB ／ 4×H200 ／ 8×B200 ／ 8×B300 | resident 完整品質 |
| AMD | 8×MI300X ／ 8×MI355X | AITER packed attention |

→ 33B 模型，**最低也要 2 張消費級旗艦卡＋384GiB 主機**，非一般使用者可負擔。

**API 成本**（MiniMax PAYGO 定價頁）：

| 項目 | 價格 |
|---|---|
| 768P 輸出 | $0.08/秒 |
| 2K 輸出 | $0.13/秒 |
| 圖片輸入 | 前 5 張免費，之後 $0.04/張 |
| Regeneration 768P→2K | $0.05/秒 |
| Context-IR | $0.90/M in、$3.60/M out |

→ 一支 5 秒 768P = **$0.4**、5 秒 2K = **$0.65**；Context-IR 另計 token 費。

**對照表（友善度）**：

| 面向 | MiniMax-H3 | 同類（Veo/Sora/Kling） |
|---|---|---|
| 開源 | 部分（僅 H3-Base） | 全閉源 |
| 自架 | 高門檻（2×5090+384GiB） | 不可自架 |
| 訂閱折扣 | **無**（Video Packages 明示「H3 not supported yet」） | 有套餐 |
| 計價 | 僅 PAYGO，按秒 | 按用量/訂閱 |

**與 MyBrain 既有判定的對照**：MyBrain `技術/技術評估/LLM降本增效.md`（`human:fatesaikou`／`stable`，2026-05-01）結論「個人開發強烈推薦 Ollama Cloud」，其降本切入點是**文字 LLM 的 token 成本**；H3 屬影片生成，計價單位是「秒」而非「token」，**不適用該降本框架**。H3 的「便宜」與否，與他既有的 LLM 成本模型是兩套計價邏輯。

**結論**：H3 對一般使用者的友善點僅「部分開源」一項；自架硬體門檻高、API 按秒計價且無折扣，不屬「夠小可自架」或「很便宜」的類別。

---

### Q3：這東西只能生成影音？

**A**：**是，H3 輸出僅限「影片＋音訊」**。輸入全模態，但輸出固定為帶同步立體聲的影片（mp4）。

| 方向 | 模態 | 說明 |
|---|---|---|
| **輸入** | 文字／圖片／影片／音訊（任意組合） | 全模態輸入 |
| **輸出** | 影片（mp4）＋ 32kHz 立體聲音訊 | **固定，無其他輸出路徑** |

**三處規格交叉佐證**：

| 來源 | 輸出規格 |
|---|---|
| README | 「generate video with native stereo audio」 |
| model card | 影片＋音訊 |
| H3 video-generation API guide | 回應僅回傳影片 URL（`content.url`，mp4） |

**反證表（H3 不能做什麼）**：

| 想產出的東西 | H3 能否 | 原因 |
|---|---|---|
| 純文字 | 否 | 無 t2t 輸出路徑 |
| 純圖片 | 否 | 無 t2i 輸出路徑 |
| 純音樂 | 否 | 音訊僅作為影片內嵌，無獨立音訊輸出 |
| 影片＋音訊 | 是 | 唯一輸出 |

**結論**：H3 的「全模態」指**輸入**；**輸出**固定為影片＋音訊，無法產出純文字、純圖片或純音樂。

---

## 附錄：資料來源

- GitHub repo：`https://github.com/MiniMax-AI/MiniMax-H3`
- HuggingFace model card 與 LICENSE：MiniMax H3 Community License（2026-08-02）
- `model_index.json`：`MiniMaxH3ModularPipeline` 整合資訊
