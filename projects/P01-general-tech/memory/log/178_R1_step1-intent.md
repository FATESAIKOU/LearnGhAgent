# 178_R1_step1-intent.md

## 狀況理解

PR body（issue #177）為「測試端到端流程用」的調研請求。技術標的：**Ollama 目前的 vision 模型（llava、llama3.2-vision、qwen2-vl 等）**。使用者要求回答三點：(1) 各自能力與參數量；(2) 哪個適合給 agent 做截圖理解；(3) 與 ChatGPT 等商業 vision API 的取捨。`Closes #177`。

這是 R1（首次發言），非追問輪。

## 執行的動作與結果

| 動作 | 目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| refresh MyBrain 鏡像 | 取得最新第二大腦 | 查到相關既有結論 | 更新失敗沿用舊副本 adf968c（2026-08-04），資料可能過期，已註明 |
| 讀骨幹檔 + grep vision/Ollama/截圖 | 確認是否已評估此標的、關聯專案、取捨準則 | 定調意圖前先看他的立場 | 見下方發現 |

**第二大腦查詢發現**（每則帶 URL 與信任層級）：
- **Ollama 已採用**：[LLM降本增效.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/LLM降本增效.md) — `human:fatesaikou` + `stable`，本人定稿。結論：基本採用 Ollama，開原生態、性價比、彈性；個人開發強烈推薦 Ollama Cloud；複雜推理/企業場景才用 Gemini/Anthropic/Codex。
- **agent 操作瀏覽器是進行中需求**：[強化 opencode browser 操作.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/強化%20opencode%20browser%20操作.md)（human + stable）、[完善化 BrowserBase.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/完善化%20BrowserBase.md)（human + stable）。特徵：「能讓 LLM 高速操作、不吃太多 token、**讓沒辦法讀圖的 LLM 也能高速操作瀏覽器**」→ 他傾向降低對視覺的依賴。
- **取捨準則**：[技術取捨準則.md](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md)（AI 草稿 `claude-code/opus-5` + `draft`，未 review）— 模型選用分級（高/中高/中低價位對應錯誤擴散範圍）、MVP→Feature 唯一閘門＝「能否影響個人 workflow」、Reject＝不採用而非沒價值。

**第二大腦無此主題**：未查到針對 **llava / llama3.2-vision / qwen2-vl 個別 vision 模型的技術評估**。此部分需以通用知識＋網路搜尋補齊。

## 動作結束後的現狀

| 驗證面向 | 內容與方式 | 結果 |
|---|---|---|
| 標的已評估與否 | grep llava/qwen2-vl/llama3.2/vision | 無個別 vision 模型評估；僅有 Ollama 框架層結論 |
| 關聯專案 | 瀏覽器操作自動化（CDP/BrowserBase） | 進行中，且偏好低視覺依賴 |
| 取捨準則 | 骨幹檔技術取捨準則 | 有：模型分級、workflow 閘門、Reject 語意 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 意圖範圍 | (a) 純報告模型能力 (b) 以「agent 截圖理解」為落地場景評估 | (b) | 使用者明問「哪個適合給 agent 做截圖理解」，且對應其進行中的瀏覽器操作專案 |
| 取捨分析基調 | (a) 中性 (b) 對齊「Ollama 已採用＋偏好本地/低依賴」立場 | (b) | 商業 API 取捨須對照他既有的 Ollama 採用判定，避免矛盾 |
| 第二大腦缺漏處理 | (a) 用通用知識填空 (b) 明標缺漏＋以搜尋補 | (b) | 規則要求查不到就明說，不可偽裝成舊結論 |
