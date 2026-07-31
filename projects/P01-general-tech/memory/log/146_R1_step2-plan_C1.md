# 146_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1 的任務是取得 Qoder 的 repo metadata 與主要文件。Qoder 並非 GitHub 上的開源專案，而是一個商業產品（公司：Bright Zenith Private Limited，新加坡註冊）。因此「repo metadata」不適用，改為取得官網、定價頁、文件站、公司資訊、以及 GitHub 上相關的第三方社群 repo 資訊。

## 執行的動作與結果

| 動作 | 目的 | 預期達成效果 | 實際的結果 |
|------|------|----------|----------|
| 讀取 qoder.com 首頁（英文版） | 取得產品定位與產品線概覽 | 了解 Qoder 賣什麼 | 成功：Qoder 定位為「Agentic Platform for Real Work」，產品線含 Desktop / QoderWork / QoderWake / CLI / Cloud Agents / JetBrains Plugin |
| 讀取 qoder.com/ja（日文版） | 確認使用者提供的日本官網內容 | 與英文版比對有無差異 | 成功：內容與英文版一致 |
| 讀取 qoder.com/about-us | 取得公司背景 | 了解背後公司 | 成功：Bright Zenith Private Limited，新加坡，51 Bras Basah Road #03-01 Lazada One |
| 讀取 docs.qoder.com（文件站） | 取得完整技術文件索引 | 了解產品功能深度 | 成功：文件站涵蓋 Desktop / CLI / Cloud Agents / QoderWork / QoderWake / JetBrains Plugin / Enterprise 七大產品線，文件量極大 |
| 讀取 docs.qoder.com/account/pricing | 取得定價細節 | 了解價格結構與用量單位 | 成功：Free / Pro($20) / Pro+($60) / Ultra($200) 四階，以 Credits 為用量單位 |
| 讀取 docs.qoder.com/Credits | 取得 Credits 消耗規則 | 了解實際用量如何計算 | 成功：Ask ~3-4 Credits/次、Agent ~7-12 Credits/次、Quest ~50 Credits/次 |
| 讀取 docs.qoder.com/user-guide/chat/model-tier-selector | 取得模型層級與支援模型 | 了解 Qoder 提供哪些模型 | 成功：5 個 Tier（Auto/Ultimate/Performance/Efficient/Lite）+ 具體模型選擇（Qwen3.7-Max/Plus、DeepSeek-V4-Pro/Flash、GLM-5.2、Kimi-K2.7-Code、MiniMax-M3） |
| 讀取 docs.qoder.com/user-guide/chat/custom-models | 取得 BYOK 支援 | 了解是否可自帶模型 | 成功：支援 Alibaba Cloud / DeepSeek / Z.ai / Kimi / MiniMax / Xiaomi MIMO 等 provider 的 API key |
| 用 gh search 搜尋 GitHub 上 Qoder 相關 repo | 確認有無官方開源 repo | 了解開源社群狀況 | 成功：官方 org Qoder-AI 僅有 qoder-community(68 stars) 與 homebrew-qoder；第三方有 qoder-rules(527 stars)、qoder-free(385 stars)、qoder-proxy(134 stars)、qoder2api(74 stars) 等逆向/破解工具 |
| 讀取 openrouter.ai/pricing | 取得 OpenRouter 定價作為比較基準 | 後續回答 Q4 所需 | 成功：OpenRouter 為 Pay-as-you-go 模式，平台費 5.5%，無月費訂閱制 |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 驗證結果 |
|----------|----------------|----------|
| 產品定位 | 官網首頁描述 | Qoder 是 agentic coding platform，非純 LLM 轉售 |
| 產品線完整度 | 文件站索引 | 7 大產品線，從 IDE 到 CLI 到雲端 agent 到企業管理 |
| 定價結構 | 定價頁 + Credits 頁 | 月訂閱制（$20/$60/$200），用量以 Credits 計，超額降級至 Lite 免費 tier |
| 模型來源 | Model Selector 頁 | 全部為第三方模型（Qwen/DeepSeek/GLM/Kimi/MiniMax），Qoder 為 aggregator |
| BYOK 支援 | Custom Models 頁 | 支援自帶 API key，不消耗 Credits |
| 公司背景 | About Us 頁 | Bright Zenith Private Limited，新加坡，非知名 AI 公司 |
| 開源狀態 | GitHub search | 無官方開源核心產品，僅社群 repo 與逆向工具 |
| OpenRouter 對比 | OpenRouter 定價頁 | OpenRouter 純 API gateway（5.5% markup），無月費、無 IDE 產品 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|----------|----------|----------|----------|
| 是否搜尋 GitHub repo | 搜尋 / 跳過 | 搜尋 | 確認 Qoder 非開源專案，避免後續誤判 |
| 是否讀取完整文件站所有頁面 | 全部讀取 / 只讀關鍵頁 | 只讀關鍵頁（定價、模型、Credits、BYOK） | 文件站超過 200 頁，全部讀取不切實際；關鍵頁已涵蓋使用者 4 個問題所需 |
| 是否先取得 OpenRouter 資料 | 現在取得 / 留到 C2 | 現在取得 | OpenRouter 定價為 Q4 比較所需，先取得可減少後續 round trip |
| 是否讀取第三方社群 repo 內容 | 讀取 / 跳過 | 僅記錄存在，不深入讀取 | 第三方 repo 多為逆向/破解工具，與官方產品分析無直接關聯 |
