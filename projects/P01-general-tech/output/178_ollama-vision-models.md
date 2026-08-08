# Ollama Vision 模型技術分析報告

> 調研日期：2026-08-08（R1 首產；R2 更新 §4 對照第二大腦）
> 資料來源：Ollama repo（github.com/ollama/ollama，178k stars）、Ollama 官方文件 docs/capabilities/vision.mdx、Ollama library model page（llava / llama3.2-vision / qwen2.5vl）
> 標的：llava、llama3.2-vision、qwen2-vl（現行名 qwen2.5vl）等 Ollama 可跑的 vision 模型，評估其能力、參數量、對 agent 截圖理解的適用性，以及與商業 vision API 的取捨。

---

## 1. 這個技術解決什麼問題？

Ollama 的 vision 模型解決的是「**讓本地／自託管環境中的 LLM 能直接理解圖片內容**」這個問題——具體是讓 agent 或應用程式把一張截圖、照片或文件圖像餵給模型，模型回傳對圖像內容的文字描述、問答或操作指令。

對應到使用者標的「給 agent 做截圖理解」，它解決的具體問題是：**agent 在操作瀏覽器或 GUI 時，需要「看到」畫面才能決定下一步動作**。vision 模型把像素轉成 agent 可推理的文字表徵，讓 agent 具備視覺感知能力。

**問題描述的模糊之處**：
- 「截圖理解」的深度未定義——是「描述畫面裡有什麼」（captioning）、「回答關於畫面的問題」（VQA）、還是「定位元素座標以操作」（grounding / computer use）？三者的模型需求差異很大。
- 「適合」的判準未給——是看準確度、延遲、token 成本、隱私、還是硬體負載？不同判準會導向不同模型。
- 使用者列的「qwen2-vl」在 Ollama library 已下架，現行為 `qwen2.5vl`，需以現行版本為準。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- Ollama 定位為「Start building with open models」的本地 LLM 執行框架，透過 `images` array 支援 vision 輸入（base64 / 路徑 / URL），REST `/api/chat` 帶 `images` 欄位即可餵圖。
- 三個標的模型皆為開源多模態模型，由不同團隊發布，Ollama 負責把它們包成可一鍵 `ollama run` 的格式。

### 通用技術背景

**問題發生的根源：LLM 本質上是文字模型，視覺是後天嫁接的能力。**

| 背景因素 | 說明 |
|---|---|
| 純文字 LLM 無法讀圖 | 傳統 LLM 只吃 token，像素無法直接進入 transformer 的輸入序列 |
| 多模態架構 | 需額外引入 vision encoder（如 CLIP、SigLIP）把圖像切成 patch 並投影成與文字同空間的 embedding，再與文字 token 一起餵給 LLM |
| 參數量與硬體 | 視覺 encoder 加上 LLM 本體，模型總參數量直接決定本地跑得動與否（記憶體、GPU VRAM） |
| agent 的視覺依賴 | 瀏覽器／GUI 自動化 agent 若無視覺，只能靠 DOM／accessibility tree 等結構化介面；有視覺則能處理 canvas、截圖、非標準 UI |

**歷史脈絡**：LLaVA 系列（2023-2024）是「LLM + 視覺 encoder + 投影層」的開山架構，把視覺理解成本大幅降低；Meta 的 Llama 3.2 Vision 是官方多模態版本；Qwen2-VL 系列（2024-2025）主打高解析度與視覺定位（grounding），Qwen2.5-VL 進一步強化 agentic / computer use 能力。Ollama 作為本地執行層，把這些模型統一成同一套 `ollama run` 介面。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 整體機制

Ollama 解決「餵圖給 LLM」的方式是**標準化 vision 輸入介面**：

```
使用者/agent ──(base64 / 路徑 / URL)──> Ollama /api/chat
                                          │  images: [ ... ]
                                          ▼
                              vision encoder 切 patch → 投影成 embedding
                                          │
                                          ▼
                              LLM 本體（文字 + 圖像 embedding 混合推理）
                                          │
                                          ▼
                              回傳文字描述 / 問答 / 操作指令
```

- **輸入**：`/api/chat` 的 `images` array，支援 base64、本地路徑、URL 三種形式。
- **處理**：Ollama 內部把圖像交給模型的 vision encoder，轉成與文字同空間的 embedding，與文字 prompt 一起送入 LLM。
- **輸出**：模型回傳純文字，agent 可據此推理。

### 3.2 三個標的模型的能力與參數量

| 模型 | 版本 | 參數量 | 檔案大小 | Context | 能力重點 |
|---|---|---|---|---|---|
| **llava** | LLaVA 1.6 | 7B / 13B / 34B | 4.7GB / 8.0GB / 20GB | 32K / 4K / 4K | 基礎 VQA、圖像描述、OCR；開山架構，能力較基礎 |
| **llama3.2-vision** | Llama 3.2 | 11B / 90B | 7.8GB / 55GB | 128K | 官方多模態；image+text 推理**僅支援英文**；長 context |
| **qwen2.5vl**（原 qwen2-vl） | Qwen2.5-VL | 3B / 7B / 32B / 72B | 3.2GB / 6.0GB / 21GB / 49GB | 125K | 高解析度、視覺定位（grounding）、agentic / computer use；需 Ollama 0.7.0+ |

**版本演進註記**：使用者列的 `qwen2-vl` 在 Ollama library 已下架，現行為 `qwen2.5vl`。報告以現行版本為準。

### 3.3 對「agent 截圖理解」的適用性分析

| 判準 | llava | llama3.2-vision | qwen2.5vl |
|---|---|---|---|
| 視覺定位（點擊座標） | 弱 | 弱 | **強**（grounding / computer use） |
| 高解析度截圖 | 一般 | 一般 | **強**（高解析度支援） |
| 多語言 | 中 | **僅英文** | **強**（中英皆佳） |
| 低硬體門檻 | 7B 最輕 | 11B 中等 | 3B 最輕、7B 中等 |
| 長 context | 32K（7B） | **128K** | 125K |
| agentic 能力 | 無 | 無 | **有**（原生 agent 導向） |

**結論**：若「截圖理解」指「agent 看畫面並定位元素以操作」，**qwen2.5vl 最適合**——它有原生視覺定位與 computer use 能力，且 3B/7B 版本硬體門檻低。llava 適合最基礎的圖像描述，llama3.2-vision 適合長 context 但僅英文。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **商業 vision API**（ChatGPT / GPT-4o、Gemini、Claude） | 雲端多模態模型，API 餵圖回傳文字 | 需付費、需網路、需接受資料外送 | 隱私外洩風險、每張圖計費、延遲受網路影響、供應商綁定 | 最高準確度與最強視覺能力，免硬體 |
| **OS 級自主操控**（ChatGPT 5.5 視覺驅動，MyBrain：試用） | 端到端觀察電腦介面、移動指標、跨工具操作（OS World 78.7%） | 雲端模型、付費；治理與人機協作問題未解 | 供應商綁定、資料外送、人跟不上開發進程 | 超越傳統 RPA 與 DOM 驅動 E2E（見 MyBrain 試用判定） |
| **結構化介面替代視覺**（DOM / accessibility tree / CDP） | 不靠視覺，直接讀瀏覽器 DOM、accessibility tree、CDP 節點 | 目標是標準網頁、有 DOM 可讀 | 無法處理 canvas、截圖、非標準 UI；需額外解析層 | 不吃視覺 token、成本低、讓無視覺 LLM 也能操作 |
| **自建瀏覽器自動化**（Browser-use / EIAgent，MyBrain：不採用） | 自己兜瀏覽器自動化工具，避免現成工具 token 效率不優 | 需自研、投入維護成本 | 開發成本高、非標準 UI 仍難處理 | 符合他「自己兜理解本質」路線（見 MyBrain 判定） |
| **本地 OCR + 文字模型**（Tesseract / PaddleOCR） | 先 OCR 把圖轉文字，再餵純文字 LLM | 圖像以文字為主（文件、表單） | 無法理解圖形、圖表、版面語意；OCR 誤差會擴散 | 極低成本、硬體需求低、隱私本地 |
| **HyperFrames（確定性渲染）** | 將 HTML+CSS 逐幀渲染為確定性影片，以確定性取代多模態 | 目標是網頁動畫／影片類 | 只適用可渲染的網頁，非通用視覺 | 比多模態更穩定、成本更低（見 MyBrain 判定） |

### 4.2 第二大腦對照（FATESAIKOU/MyBrain）

**查詢結果**：第二大腦**沒有**針對 llava / llama3.2-vision / qwen2-vl 個別 vision 模型的技術評估。此部分以通用知識＋本次調研補齊，非既有結論。判定總表（骨幹檔）`技術/技術評估/判定總表.md` 與目錄 grep（llava / qwen / vision / llama3.2 / 截圖）皆無命中。

**相關既有判定**（與本報告結論直接相關）：

1. **Ollama 已採用**：[LLM降本增效.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/LLM降本增效.md) — `human:fatesaikou` + `stable`，本人定稿。結論：基本採用 Ollama，開原生態、性價比、彈性；個人開發強烈推薦 Ollama Cloud；複雜推理／企業場景才用 Gemini/Anthropic/Codex。→ **與本報告「本地 vision 模型優先、商業 API 僅在需要最強能力時用」的方向一致，無衝突。**

2. **agent 操作瀏覽器是進行中需求**：[強化 opencode browser 操作.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/強化%20opencode%20browser%20操作.md)（`human:fatesaikou` + `stable`）、[完善化 BrowserBase.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/完善化%20BrowserBase.md)（`human:fatesaikou` + `stable`）。特徵：「能讓 LLM 高速操作、不吃太多 token、**讓沒辦法讀圖的 LLM 也能高速操作瀏覽器**」，實作是 chrome-devtools-mcp 串進 opencode。→ **與本報告 §4 的「結構化介面替代視覺」方向一致**：他明確傾向降低對視覺的依賴（甚至讓「讀不了圖的 LLM」也能操作），vision 模型對他是補充而非主軸。

3. **OS 級自主操控＝試用**：[理解 ChatGPT 5.5.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/理解%20ChatGPT%205.5.md)（`human:fatesaikou` + `stable`，判定總表：試用）。他認為 VLM 視覺驅動將「讓 DOM Tree 驅動的 E2E 測試（Cypress/Selenium）死亡」，並規劃「在 Axross Recipe 探索基於 VLM 的視覺驅動 E2E 測試 PoC」。→ **支持「視覺驅動是未來方向」**，與本報告「商業 API ／OS 級 vision 是更強替代」互為呼應。

4. **自建瀏覽器自動化＝不採用現成**：[Browser-use, EIAgent 之瀏覽器操作自動化.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Browser-use%2C%20EIAgent%20%E4%B9%8B%E7%80%8F%E8%A6%BD%E5%99%A8%E6%93%8D%E4%BD%9C%E8%87%AA%E5%8B%95%E5%8C%96.md)（判定總表：不採用）— 現成瀏覽器自動化工具「效率不優，乾脆自己兜好」。→ 符合他「理解優先：先自己兜」的準則（見取捨準則原則一）。

5. **技術取捨準則**：[技術取捨準則.md](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md)（`claude-code/opus-5` + `draft`，**未經他 review 的 AI 草稿**）。模型選用分級（高／中高／中低價位對應錯誤擴散範圍）、MVP→Feature 唯一閘門＝「能否影響個人 workflow」、Reject＝不採用而非沒價值。→ 依此準則，vision 模型是否採用，最終判準是「能否影響他的個人 workflow」，而非純技術優劣。⚠️ 此檔為 AI 草稿，其中「錯誤擴散範圍」軸也未經他確認。

6. **HyperFrames 已採用**：[HyperFrames.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/HyperFrames.md)（`human:fatesaikou` + `stable`，判定總表：採用）— 將 HTML+CSS 逐幀渲染為確定性影片，**比多模態更穩定且成本更低**。→ 這是「用確定性取代多模態」的既有採用案例，支持 §4 中「結構化／確定性替代視覺」的思考方向。

**衝突說明**：本報告 §3.3 結論「qwen2.5vl 最適合 agent 截圖理解」與他「降低對視覺依賴」的既有方向**存在張力**——若截圖理解是為了操作瀏覽器，他既有的 BrowserBase/CDP 結構化路線可能已覆蓋大部分需求，vision 模型只在結構化介面不可得（canvas、截圖、非標準 UI）時才必要。此張力已在此明確指出，供使用者決策。

**對「給 agent 做截圖理解」的第二大腦結論**：依 `技術取捨準則.md` 的 MVP→Feature 閘門，**qwen2.5vl 是否值得進入他的 workflow，判準是「能否影響他的個人 workflow」**；依 BrowserBase/CDP 既有方向，**他更可能先走結構化路線，vision 模型是補充**。兩點都指向「qwen2.5vl 適合，但落地優先序在他既有結構化路線之後」。

---

## 5. User Q&A

### R2 註記

- **R1**：首次產出，無使用者追問，無 QA。
- **R2**：使用者留言為「把這次的結論存進我的第二大腦吧」——是**儲存請求**，非質問型句構（無「為何／憑什麼／不能理解／為什麼是」），依 §5 觸發規則不新增 QA 條目。該請求屬 `/sync-to-mybrain` 流程（由使用者觸發、本輪只讀不寫），本報告僅更新 §4 對照第二大腦，不因儲存請求改動結論。
