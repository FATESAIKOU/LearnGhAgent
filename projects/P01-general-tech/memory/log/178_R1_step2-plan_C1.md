# 178_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認調研標的為 **Ollama 的 vision 模型**（llava、llama3.2-vision、qwen2-vl 等），使用者要回答三點：(1) 各自能力與參數量；(2) 哪個適合給 agent 做截圖理解；(3) 與 ChatGPT 等商業 vision API 的取捨。本 sub-step C1 依 document skill 標準動作：取得 Ollama repo metadata、README、vision 能力文件，以及三個 vision 模型的官方 model page，作為後續能力/參數/取捨分析的原始資料。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 do/skills/document/SKILL.md | 確認標準調研動作流程 | 依規範執行 | 規範確認：gh repo view → README → 背景脈絡補查 |
| `gh repo view ollama/ollama` | 取得 repo metadata | 取得 stars/license/更新時間 | 成功：178,076 stars、MIT、default branch main、2026-08-08 更新、description 列 Kimi-K2.6/GLM-5.2/Qwen/Gemma 等 |
| 抓取 README.md（raw） | 取得專案定位與使用方式 | 了解 Ollama 框架定位 | 成功：定位「Start building with open models」，含 REST API、Python/JS SDK、`ollama run` 用法 |
| 抓取 docs/capabilities/vision.mdx | 取得 vision 輸入機制 | 了解 agent 如何餵圖 | 成功：`images` array（base64/路徑/URL），`/api/chat` 帶 images 欄位 |
| 抓取 ollama.com/library/llava | 取得 llava 能力與參數量 | 取得 llava 規格 | 成功：LLaVA 1.6，7B/13B/34B，7B=4.7GB、13B=8.0GB、34B=20GB，context 32K/4K/4K |
| 抓取 ollama.com/library/llama3.2-vision | 取得 llama3.2-vision 規格 | 取得該模型規格 | 成功：11B/90B，11B=7.8GB、90B=55GB，128K context，image+text 僅支援英文 |
| 抓取 ollama.com/library/qwen2-vl | 取得 qwen2-vl 規格 | 取得該模型規格 | **404**：`qwen2-vl` 在 Ollama library 已不存在 |
| 探測正確 model 名稱 | 找出 qwen 系列 vision 正確名稱 | 取得正確規格 | 成功：`qwen2.5vl`（200），`qwen2-vl`/`qwen2.5-vl` 皆 404 |
| 抓取 ollama.com/library/qwen2.5vl | 取得 qwen2.5-vl 規格 | 取得該模型規格 | 成功：3B/7B/32B/72B，3B=3.2GB、7B=6.0GB、32B=21GB、72B=49GB，125K context，需 Ollama 0.7.0+，具 agentic/computer use/視覺定位能力 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Ollama repo metadata | gh repo view | 178k stars、MIT、活躍更新（2026-08-08） |
| vision 輸入機制 | docs/capabilities/vision.mdx | `images` array 支援 base64/路徑/URL，REST `/api/chat` |
| llava 規格 | ollama.com/library/llava | 7B/13B/34B，LLaVA 1.6，context 32K/4K/4K |
| llama3.2-vision 規格 | ollama.com/library/llama3.2-vision | 11B/90B，128K context，image+text 僅英文 |
| qwen2-vl 存在性 | 探測多個 URL | `qwen2-vl` 已下架，現行為 `qwen2.5vl`（3B/7B/32B/72B，125K） |
| 使用者標的對應 | 對照 PR body | 使用者列的「qwen2-vl」需以現行 `qwen2.5vl` 取代並註明版本演進 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| qwen2-vl 404 處理 | (A) 放棄 qwen 系列 (B) 探測正確名稱並改用 qwen2.5vl | B | 使用者標的「qwen2-vl」在 Ollama 已下架，現行為 qwen2.5vl；需以現行版本回應並註明演進，避免報告引用已不存在模型 |
| 資料來源 | (A) 只用 repo README (B) 補 model page + vision docs | B | 使用者問「能力與參數量」，model page 提供精確參數/context/檔案大小，vision.mdx 提供 agent 餵圖機制，兩者互補 |
| 是否需要 CDP | (A) 對 ollama.com 用 CDP (B) 直接 webfetch/curl | B | ollama.com 與 raw.githubusercontent 皆正常回傳，無反爬阻擋，不需動用 CDP |
| 下一步 C2 方向 | (A) 直接撰寫報告 (B) 補查「agent 截圖理解」實務與商業 API 取捨 | B | 使用者三問中「哪個適合 agent 截圖理解」與「商業 API 取捨」需額外背景（agent 視覺依賴、token/成本、隱私），C1 僅取得模型規格，需 C2 補查 |
