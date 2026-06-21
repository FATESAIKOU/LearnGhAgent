# anthropic/courses 分析報告

> 調研標的：GitHub repo `anthropics/courses`（21930 stars, 2325 forks, 最後更新 2026-06-21）
> 授權：Other | 主要語言：Jupyter Notebook

---

## 1. 這個技術解決什麼問題？

`anthropics/courses` 解決的是 **「開發者缺乏系統性學習 Claude API 與提示工程的結構化教材」** 的問題。

具體而言：
- Anthropic 提供 Claude 系列 LLM（Haiku / Sonnet / Opus）的 API，但僅有官方文件（API reference）而無循序漸進的實作課程
- 開發者若只閱讀 API 文件，難以掌握提示工程的最佳實務、工具使用（tool use）的完整工作流程、以及生產環境中 prompt 評估（evaluations）的建置方法
- 該 repo 以 Jupyter Notebook 形式提供 5 門課程，涵蓋從 API 基礎到進階工具使用的完整學習路徑

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到

- Anthropic 官方文件（docs.anthropic.com）提供 API reference 與模型概覽，但未提供互動式教學
- 該 repo 的課程設計明確指出「建議依序學習」，暗示各課程間有知識依賴關係
- 課程中使用 Claude 3 Haiku（最低成本模型）以降低學員的 API 費用

### 通用技術背景

- **LLM API 的學習曲線**：與傳統 REST API 不同，LLM API 的輸出品質高度依賴 prompt 設計，開發者需要理解 system prompt、few-shot、chain-of-thought、tool use 等概念才能有效使用
- **提示工程缺乏標準教材**：2023-2024 年間提示工程仍屬新興領域，業界缺乏公認的系統化教材，各 LLM 提供者（OpenAI、Anthropic、Google）各自推出教學資源
- **生產環境需求**：開發者不僅需要「讓模型回答正確」，還需要評估 prompt 品質（evaluations）、處理結構化輸出（tool use / JSON mode）、管理多輪對話等生產級能力，這些在基礎 API 文件中不會涵蓋

---

## 3. 這個技術是如何解決該問題的？

該 repo 以 **5 門課程 + Jupyter Notebook 實作** 的方式提供結構化學習路徑：

### 課程架構

```
anthropics/courses
├── 1. anthropic_api_fundamentals    ← API 基礎（金鑰、訊息格式、參數、串流、視覺）
├── 2. prompt_engineering_interactive_tutorial  ← 提示工程（9 章，從基礎到進階）
├── 3. real_world_prompting          ← 真實世界提示（醫療、客服、通話摘要等案例）
├── 4. prompt_evaluations            ← Prompt 評估（9 課，含 promptfoo 整合）
└── 5. tool_use                      ← 工具使用（6 課，從單一工具到多工具聊天機器人）
```

### 各課程核心機制

| 課程 | 解決的子問題 | 核心做法 |
|---|---|---|
| API fundamentals | 開發者不熟悉 Claude SDK 的基本操作 | 6 個 notebook 逐步教學：取得 API key → messages 格式 → 模型選擇 → 參數調整 → 串流 → 多模態（vision） |
| Prompt engineering | 開發者不知道如何寫出有效 prompt | 9 章循序漸進：基本結構 → 清晰指令 → 角色賦予 → 資料與指令分離 → 輸出格式控制 → 逐步思考 → 範例使用 → 避免幻覺 → 複雜案例 |
| Real world prompting | 開發者無法將提示技巧應用於真實場景 | 5 個真實案例 walkthrough：醫療問診 prompt、客服機器人、通話摘要、提示工程流程、提示回顧 |
| Prompt evaluations | 開發者無法量化評估 prompt 品質 | 9 課涵蓋：評估概論 → Workbench 人工評估 → 程式評分 → 分類評估 → promptfoo 整合（程式評分 / 分類 / 自訂評分 / 模型評分） |
| Tool use | 開發者不知道如何讓 Claude 呼叫外部工具 | 6 課：工具使用概論 → 第一個工具 → 強制 JSON 輸出 → 完整工作流程 → 工具選擇策略 → 多工具聊天機器人 |

### 技術實作方式

- 所有課程以 **Jupyter Notebook (.ipynb)** 格式提供，學員可在本地或雲端環境（Google Colab / AWS Workshop / Google Vertex）直接執行
- 課程內含 **Example Playground** 區域，學員可即時修改 prompt 並觀察 Claude 回應變化
- 提示工程課程另提供 **Google Sheets 版本**（Claude for Sheets 擴充功能），降低技術門檻
- 評估課程整合 **promptfoo** 開源框架，示範如何以程式化方式進行 prompt 回歸測試

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表：替代方案對照

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **OpenAI Cookbook** | OpenAI 官方提供的範例程式碼與指南集合（Python notebook） | 需使用 OpenAI API 金鑰；熟悉 Python | 範例針對 GPT 模型設計，遷移至 Claude 需改寫 API 呼叫格式 | 學習 OpenAI 生態系的提示工程與 API 使用模式 |
| **Google Vertex AI 教學** | Google Cloud 提供的 Generative AI 教學資源（含 notebook 與 Qwiklab） | 需 GCP 帳號與 Vertex AI 啟用；部分內容收費 | 教學內容綁定 Google Cloud 基礎設施，無法獨立使用 | 學習 Gemini 模型的提示工程與 Vertex AI 平台整合 |
| **LangChain 教學文件** | LangChain 框架提供的 LLM 應用開發教學（含提示模板、鏈、代理） | 需理解 LangChain 抽象層概念；框架版本迭代快速 | 抽象層封裝過多細節，可能掩蓋底層 API 行為 | 學習以框架方式組合 prompt、工具與記憶體，加速原型開發 |
| **DeepLearning.AI 短課程** | Andrew Ng 團隊與各 LLM 提供者合作的 1-2 小時短課程（影片 + notebook） | 需註冊平台帳號；部分課程收費 | 課程長度有限，深度不及完整教材 | 快速入門特定主題（如提示工程、RAG、agent） |

### 切入點差異

- **anthropics/courses** 是唯一由 Anthropic 官方維護、完全免費、且專注於 Claude 模型的系統化教材。與 OpenAI Cookbook 相比，其課程結構更完整（非零散範例），且涵蓋 prompt evaluations 與 tool use 等生產級主題
- **LangChain 教學** 與 **DeepLearning.AI 課程** 偏向框架層或通用概念層，而 anthropics/courses 直接操作底層 API，讓學員理解 Claude 的原生行為後再考慮是否引入框架
- **Google Vertex AI 教學** 與 anthropics/courses 的 real_world_prompting 課程有直接合作關係（Vertex 版本分支），但前者綁定 GCP 生態系，後者可獨立於任何雲端平台使用

---

## 5. User Q&A

### Q1：anthropics/courses 是誰？

**A**：`anthropics/courses` 是 **Anthropic 公司官方維護的免費 Claude 教育課程倉庫**。

| 面向 | 內容 |
|---|---|
| owner | `anthropics` — 即 Anthropic 公司（Claude 模型的開發者） |
| 性質 | 官方教育資源，非第三方社群專案 |
| 形式 | Jupyter Notebook（.ipynb），共 5 門課程 |
| 授權 | Other（非標準開源授權，但可免費使用） |
| 規模 | 21.9k stars、2.3k forks、59 commits |

**結論**：這不是一個「技術產品」或「框架」，而是一套由 Claude 開發者官方編寫的免費教材。

### Q2：可以用在什麼業務，加速還是提升品質？

**A**：**兩者皆有**，取決於學習者選修的課程。以下按課程分類說明：

| 課程 | 對應業務場景 | 加速 | 提升品質 | 說明 |
|---|---|---|---|---|
| API fundamentals | 任何要串接 Claude API 的專案 | 是 | 否 | 學會 SDK 基本操作（金鑰、參數、串流、vision），減少摸索 API 的時間 |
| Prompt engineering | 客服機器人、內容生成、資料分類等 LLM 應用 | 是 | 是 | 掌握 prompt 結構與技巧（角色賦予、few-shot、chain-of-thought），減少 trial-and-error 次數（加速），同時提升輸出準確率（品質） |
| Real world prompting | 醫療問診系統、通話摘要、客服支援 | 是 | 是 | 直接提供已驗證的真實案例 prompt 模板，可複用於類似場景（加速）；案例包含邊界情況處理，減少幻覺（品質） |
| Prompt evaluations | 已上線的 LLM 功能需要持續監控 prompt 品質 | 否 | 是 | 建立自動化評估 pipeline（含 promptfoo 整合），確保每次 prompt 修改不降低輸出品質 |
| Tool use | 需要 Claude 呼叫外部 API / 資料庫 / 工具的場景 | 是 | 是 | 提供完整 tool use 工作流程（定義工具 → 強制 JSON → 工具選擇策略 → 多工具協作），減少自行摸索架構的時間（加速），同時避免常見的 tool call 錯誤（品質） |

**結論**：
- **加速**：API fundamentals、Prompt engineering、Real world prompting、Tool use 四門課程直接減少學習與開發時間
- **提升品質**：Prompt engineering、Real world prompting、Prompt evaluations、Tool use 四門課程幫助減少幻覺、提升輸出準確率、建立評估機制
- 唯一純加速的課程是 API fundamentals（僅教基本操作，不涉及品質優化）
- 唯一純品質的課程是 Prompt evaluations（專注評估，不涉及開發加速）

### Q3：你還是沒說清楚 anthropics/courses 到底是什麼——不是產品、不是框架、不是服務，那它是什麼？

**A**：`anthropics/courses` 是一個 **GitHub 倉庫**，裡面放了 5 份 Jupyter Notebook 檔案。它的本質是「文件」，不是可執行的軟體。

| 它不是什麼 | 它是什麼 |
|---|---|
| 不是 SaaS 服務（無需註冊、無 API endpoint） | 是一組 `.ipynb` 檔案，需自行在本地或 Colab 開啟 |
| 不是程式庫 / SDK（無 `pip install`） | 內容是教學步驟與程式碼範例，學員需手動執行每個 cell |
| 不是框架（無抽象層、無 CLI） | 直接呼叫 `anthropic` Python SDK 的底層 API |
| 不是認證課程（無證書、無考試） | 是自主學習教材，完成與否由學員自行決定 |

**結論**：把它理解為「Anthropic 官方出版的 5 本互動式電子書」，每本電子書的每一頁都是一個可執行的 Python cell。

### Q4：你說可以用在業務上，但「學課程」本身不是業務——學完之後具體能做出什麼？

**A**：學完各課程後，學員具備的能力可直接對應到以下業務產出：

| 課程 | 學完後能做出什麼 | 對應業務角色 | 加速 or 品質 |
|---|---|---|---|
| API fundamentals | 寫出第一個串接 Claude API 的 Python 程式，處理文字生成、串流回應、圖片輸入 | 後端工程師 | 加速（從 0 到可呼叫 API 的時間從數天縮至數小時） |
| Prompt engineering | 設計 system prompt 與 few-shot 範例，使 Claude 輸出符合指定格式與正確率 > 90% | 提示工程師 / PM | 品質（減少 prompt trial-and-error 次數，提升輸出穩定性） |
| Real world prompting | 複製已驗證的醫療問診 prompt、客服機器人 prompt、通話摘要 prompt 到自己的專案中 | 領域專家 / 開發者 | 加速（直接套用模板，不需從零設計） |
| Prompt evaluations | 建立自動化測試：每次修改 prompt 後自動跑 100 筆測試案例，確保 regression 為零 | QA / MLOps | 品質（量化監控 prompt 變更的影響） |
| Tool use | 讓 Claude 能查資料庫、發 API 請求、操作檔案系統，建構一個可自主執行多步驟任務的 agent | 後端工程師 / AI 架構師 | 加速 + 品質（提供已驗證的 tool call 模式，避免常見錯誤） |

**結論**：這 5 門課程各自對應一個具體的「產出能力」，而非抽象知識。學員可依自身業務需求選擇對應課程，直接產出可用於生產環境的程式碼與 prompt 模板。
