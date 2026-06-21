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

**A**：`anthropics/courses` 是 Anthropic 公司（Claude 系列 LLM 的開發者）官方維護的 **教育性 GitHub 倉庫**，不是一個產品或工具，而是一套 **免費的結構化教材**。

| 面向 | 內容 |
|---|---|
| 維護者 | Anthropic（AI 安全公司，Claude Haiku / Sonnet / Opus 的開發者） |
| 形式 | 5 門 Jupyter Notebook 課程，可於本地或 Google Colab 執行 |
| 目標受眾 | 使用 Claude API 的軟體開發者 |
| 授權 | CC BY-NC 4.0（非商業用途免費，須標示出處） |
| 規模 | 21.9k GitHub stars，2.3k forks |

它不是一個「可以安裝的套件」或「可以呼叫的服務」，而是一份 **教學資源**，類似官方提供的教科書。

**結論**：`anthropics/courses` 是 Anthropic 官方為 Claude API 開發者設計的免費系統化教材倉庫。

### Q2：可以用在什麼業務？

**A**：該教材本身不直接提供業務功能，但教材教授的技術可直接應用於以下業務場景：

| 業務場景 | 對應課程 | 具體應用 |
|---|---|---|
| **客服自動化** | real_world_prompting（客服機器人案例） | 用 Claude API 建置客服對話機器人，處理常見問題、升級複雜案件 |
| **醫療問診輔助** | real_world_prompting（醫療問診 prompt） | 設計結構化 prompt 引導 Claude 進行症狀問診與病歷摘要 |
| **通話摘要與分析** | real_world_prompting（通話摘要） | 將客服/銷售通話錄音轉為結構化摘要（關鍵主題、行動項目） |
| **內容生成與格式控制** | prompt_engineering（輸出格式控制）+ tool_use（強制 JSON） | 從非結構化資料生成結構化輸出（JSON/XML），用於資料管線 |
| **Prompt 品質管控** | prompt_evaluations（promptfoo 整合） | 建立 prompt 回歸測試，確保 prompt 修改不破壞既有功能 |
| **多工具自動化流程** | tool_use（多工具聊天機器人） | 讓 Claude 根據使用者意圖自動選擇並呼叫外部 API（資料庫查詢、排程系統等） |

**結論**：教材本身是學習資源，但其所教授的技術可應用於客服、醫療、內容生產、品質管控、流程自動化等業務場景。

### Q3：效果是加速還是提升品質？

**A**：**兩者皆有，但主要貢獻在品質提升，加速為次要效果。** 以下對照表說明各課程對加速與品質的影響：

| 課程 | 對加速的貢獻 | 對品質的貢獻 |
|---|---|---|
| API fundamentals | 降低 API 整合的學習時間（從 0 到可呼叫 API） | 確保正確使用 API 參數（max_tokens、temperature、streaming），避免因參數錯誤導致輸出異常 |
| Prompt engineering | 減少反覆嘗試 prompt 的時間（提供 proven pattern） | 提升 prompt 的準確性與一致性（清晰指令、角色賦予、few-shot、chain-of-thought） |
| Real world prompting | 提供可直接參考的案例模板，加速開發 | 展示真實場景的 prompt 設計陷阱與解決方案，提升生產環境的穩定性 |
| Prompt evaluations | 自動化評估減少人工審查時間 | 建立量化評估標準，確保 prompt 修改不降低品質 |
| Tool use | 提供 tool use 完整工作流程模板，加速整合 | 確保工具呼叫的正確性與錯誤處理，提升多工具協作的可靠性 |

**加速效果**：教材提供 proven pattern 與模板，開發者不需從零摸索，可直接參考或修改既有 notebook，縮短開發週期。

**品質效果**：教材強調 prompt 評估（evaluations）、輸出格式控制、避免幻覺等生產級議題，這些是基礎 API 文件不會涵蓋的品質面向。

**結論**：教材的主要價值在於提升 Claude API 應用的品質（正確性、一致性、可評估性），同時透過模板與最佳實務間接加速開發。
