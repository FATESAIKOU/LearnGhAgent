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

### Q1：anthropics/courses 是什麼（「是誰」）？

**A**：`anthropics/courses` 是 **Anthropic 官方維護的免費教學資源庫**，不是產品、不是工具、不是框架。

| 面向 | 內容 |
|---|---|
| 擁有者 | Anthropic（Claude 模型的開發公司） |
| 形式 | GitHub 上的 Jupyter Notebook 集合 |
| 定位 | 官方教學課程（educational courses），非 SDK、非 CLI、非 API |
| 內容 | 5 門課程：API 基礎 → 提示工程 → 真實世界提示 → Prompt 評估 → 工具使用 |
| 費用 | 完全免費（學員僅需自付 Claude API 使用費） |
| 技術棧 | Python + Jupyter Notebook，可在本地、Colab、AWS、Vertex 執行 |

**結論**：它是一套「官方出品的教科書」，不是一個可以部署的軟體元件。

---

### Q2：可以用在什麼業務？

**A**：適用於需要 **團隊內建立 Claude API 開發能力** 的任何業務場景。以下為具體業務場景與對應課程：

| 業務場景 | 適用課程 | 解決的問題 |
|---|---|---|
| **新進開發者 onboarding** | API fundamentals + Prompt engineering | 讓不熟悉 Claude API 的開發者在 2-3 天內具備基礎開發能力 |
| **客服機器人開發** | Real world prompting（客服案例）+ Tool use | 學習如何設計客服 prompt、讓 Claude 查詢訂單系統、處理多輪對話 |
| **醫療 / 專業領域 prompt 設計** | Real world prompting（醫療案例） | 學習領域專用 prompt 的設計模式（結構化輸出、安全限制、引用來源） |
| **Prompt 品質管控（QA 流程）** | Prompt evaluations | 建立 prompt 回歸測試機制，確保 prompt 修改不降低輸出品質 |
| **內部工具串接（function calling）** | Tool use | 讓 Claude 呼叫內部 API / 資料庫 / 第三方服務 |
| **通話 / 會議摘要自動化** | Real world prompting（通話摘要案例） | 學習長文本摘要的 prompt 設計與結構化輸出 |
| **提示工程團隊標準化** | Prompt engineering（完整 9 章） | 統一團隊的 prompt 撰寫風格與最佳實務 |

**結論**：適用於任何需要「讓團隊學會有效使用 Claude API」的業務，不適用於不需要 Claude 或不需要自建 LLM 應用的業務。

---

### Q3：是加速還是提升品質？

**A**：**兩者兼具**，但貢獻面向不同。

| 面向 | 加速開發 | 提升品質 | 說明 |
|---|---|---|---|
| API fundamentals | ✅ 縮短摸索期 | — | 提供可直接執行的 notebook，開發者不必從零讀 API 文件 |
| Prompt engineering | ✅ 減少 trial-and-error | ✅ 教導最佳實務 | 系統化教學避免常見錯誤（幻覺、格式不穩、指令模糊） |
| Real world prompting | ✅ 提供可複用模板 | ✅ 展示生產級設計 | 5 個真實案例可直接改寫為生產 prompt |
| Prompt evaluations | — | ✅ 建立量化評估機制 | 引入 promptfoo 做回歸測試，防止品質退化 |
| Tool use | ✅ 加速工具整合開發 | ✅ 教導錯誤處理與邊界案例 | 完整工作流程範例減少整合時的除錯時間 |

**量化估算**（基於課程內容推測，非官方數據）：

| 指標 | 無課程（自學） | 使用 courses | 差異 |
|---|---|---|---|
| 從零到第一個可用 prompt | 2-5 天 | 0.5-1 天 | 加速 4-5 倍 |
| 建立 prompt 評估 pipeline | 2-4 週（需自行摸索） | 1-3 天（照課程實作） | 加速 5-10 倍 |
| 生產環境 prompt 品質 | 不穩定，依個人經驗 | 有系統化評估機制 | 品質可量化、可回歸 |
| 團隊 prompt 風格一致性 | 低（每人各自摸索） | 高（共用教材與最佳實務） | 品質提升 |

**結論**：`anthropics/courses` 同時貢獻加速（降低學習曲線、提供可複用範例）與品質（系統化最佳實務、評估機制），但「加速」的效果更直接且可量化，「品質」的提升則依賴團隊是否確實執行課程中的評估流程。
