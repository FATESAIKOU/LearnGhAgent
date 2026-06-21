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

**A**：`anthropics/courses` 是 **Anthropic 公司官方 GitHub 帳號（anthropics）** 下的一個公開 repo。

- Anthropic 是一家美國 AI 公司（總部舊金山），由前 OpenAI 高階主管 Dario Amodei（CEO）與 Daniela Amodei（President）於 2021 年創立
- 核心產品為 Claude 系列 LLM（Haiku / Sonnet / Opus）
- 截至 2026 年 5 月估值約 $9650 億美元，為全球最高估值純 AI 公司
- 該 repo 的 LICENSE 為 **CC BY-NC 4.0**（非商業用途），禁止商用

| 面向 | 內容 |
|---|---|
| 擁有者 | Anthropic PBC（公司官方帳號 `anthropics`） |
| repo 定位 | "Anthropic's educational courses" |
| 建立時間 | 2024-05-30 |
| 授權 | CC BY-NC 4.0（非商業用途） |
| 課程數量 | 5 門，共約 35+ 個 Jupyter Notebook |

**結論**：這是 Anthropic 官方出品的免費 Claude 教學教材，不是第三方社群專案。

### Q2：可以用在什麼業務？

**A**：該 repo 本身是**教材**，不是可直接部署的產品。它的「業務用途」是**培訓開發團隊**，而非直接服務終端客戶。適用場景如下：

| 業務場景 | 對應課程 | 說明 |
|---|---|---|
| 團隊 onboarding 新成員使用 Claude API | API fundamentals | 新進開發者可在 6 個 notebook 內學會 SDK 操作、參數調整、串流、多模態 |
| 建立內部 prompt 工程標準 | Prompt engineering | 9 章循序漸進，可作為團隊 prompt 撰寫規範的訓練教材 |
| 開發 LLM 驅動的客服 / 醫療 / 摘要功能 | Real world prompting | 5 個真實案例 walkthrough，可直接參考 prompt 設計模式 |
| 建立 prompt 品質評估機制（回歸測試） | Prompt evaluations | 9 課含 promptfoo 整合，可導入 CI/CD 做 prompt 回歸測試 |
| 開發 tool use / function calling 功能 | Tool use | 6 課從單一工具到多工具聊天機器人，適合需要 Claude 呼叫外部 API 的場景 |

**結論**：適用於「需要讓開發團隊系統性學習 Claude API 與提示工程」的組織內部培訓場景。不適用於直接交付客戶的產品。

### Q3：加速還是提升品質？

**A**：**兩者皆有，但主要效果是提升品質，加速是次要效果。**

| 效果維度 | 機制 | 證據 |
|---|---|---|
| **提升品質（主要）** | 課程教導 prompt 最佳實務（清晰指令、角色賦予、資料與指令分離、輸出格式控制、逐步思考、避免幻覺），減少 trial-and-error 導致的低品質輸出 | Prompt engineering 課程 9 章中有 6 章直接針對輸出品質；Evaluations 課程 9 課全部針對品質量化 |
| **加速（次要）** | 結構化教材縮短學習曲線，開發者不需自行摸索 API 行為與提示技巧 | API fundamentals 課程 6 課涵蓋 SDK 所有基礎操作，學完即可上手 |
| **加速（間接）** | Evaluations 課程整合 promptfoo，可自動化 prompt 回歸測試，減少人工 review 時間 | Evaluations 課程第 5-9 課示範程式化評分流程 |

**反證表**：

| 如果目的是... | 這個 repo 是否適合 | 原因 |
|---|---|---|
| 加速現有產品的開發時程 | 部分適合 | 教材本身不提供程式碼片段直接複製貼上，需理解後自行實作 |
| 提升現有產品的輸出品質 | 適合 | 課程直接教授 prompt 品質控制與評估方法 |
| 快速 prototyping | 不適合 | 應直接使用 Claude API 文件或 SDK quickstart，而非上完整課程 |
| 建立團隊的 LLM 開發能力（長期） | 適合 | 5 門課程涵蓋從基礎到生產級的完整知識體系 |

**結論**：主要效果是**提升品質**（透過系統化 prompt 工程與評估方法），次要效果是**加速**（透過結構化教材縮短學習曲線）。若目標是快速出貨，應直接讀 API 文件而非上課。
