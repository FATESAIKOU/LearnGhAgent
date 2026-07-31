# 146_R2_step2-plan_C1.md

## 狀況理解

本 sub-step 針對 R2 的兩個追問進行資料收集：

1. **Qoder vs Ollama Cloud 性價比計算**：使用者常用 DeepSeek-V4-Pro 與 GLM-5.2，週用量 70-80%，需量化比較
2. **Ollama Cloud ($20) + Anthropic ($20) vs Qoder Pro+ ($60)**：驗證 Qoder $60 方案能否使用 Anthropic/OpenAI 最新模型，並比較性價比

關鍵前提驗證：Qoder 是否支援 Anthropic/OpenAI 模型（內建或 BYOK）。

## 執行的動作與結果

| 動作 | 目的 | 預期達成效果 | 實際的結果 |
|------|------|----------|----------|
| Fetch Qoder 官網 | 確認產品定位與模型列表 | 取得最新產品資訊 | Qoder 為 agentic coding platform，提供 Desktop/CLI/Plugin/QoderWork/QoderWake 等產品線 |
| Fetch Qoder Pricing 頁面 | 取得完整定價方案 | 確認 Pro/Pro+/Ultra 的 Credits 與價格 | Free($0)/Pro($20, 2000cr)/Pro+($60, 6000cr)/Ultra($200, 20000cr)；Credit Pack $20/1500cr |
| Fetch Qoder Credits 頁面 | 取得各模式消耗率 | 計算每次操作的 Credits 成本 | Ask ~3-4cr, Agent ~7-12cr, Quest Agent ~50cr, Quest Experts ~75cr |
| Fetch Qoder Model Selector 頁面 | 取得模型清單與消耗率 | 確認 DeepSeek-V4-Pro(0.5x) 與 GLM-5.2(0.6x) 的消耗率 | 7 個內建模型，均為中國模型；5 個 Tier（Auto/Ultimate/Performance/Efficient/Lite） |
| Fetch Qoder Custom Models 頁面 | 確認 BYOK 支援範圍 | 驗證是否支援 Anthropic/OpenAI | BYOK 僅支援 6 家中國 provider：Alibaba Cloud、DeepSeek、Z.ai、Kimi、MiniMax、Xiaomi MIMO。**不支援 Anthropic/OpenAI** |
| Fetch Ollama Cloud Pricing | 取得 Ollama Cloud 定價與用量限制 | 比較 $20 Pro 方案的 fair use 限制 | Free($0)/Pro($20, 50x Free)/Max($100, 5x Pro)；DeepSeek-V4-Pro 為 level 4（extra heavy）；session 限制每 5h 重置 |
| Fetch Anthropic Pricing | 取得 Claude 定價 | 確認 $20 Pro 方案的用量限制 | Free($0)/Pro($17-20)/Max($100+); Pro 含 Claude Code; 5h session window + weekly limits |
| Fetch OpenRouter Pricing | 取得 OpenRouter 定價 | 確認 5.5% markup 與模型數量 | Free/Pay-as-you-go(5.5% markup)/Enterprise；400+ 模型；BYOK $25K 內免平台費 |
| 讀取 R1 報告 | 回顧既有分析 | 避免重複工作 | 確認 R1 已涵蓋基本定價與模型資料，R2 需補充用量量化比較 |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 驗證結果 |
|----------|----------------|----------|
| Qoder 模型支援範圍 | 讀取 Model Selector + Custom Models 頁面 | 內建 7 個模型全為中國模型；BYOK 僅支援 6 家中國 provider。**Qoder 不支援 Anthropic/OpenAI 模型** |
| DeepSeek-V4-Pro 消耗率 | Model Selector 頁面 | 0.5x（Specific Model），在 Auto tier 下約 1.0x |
| GLM-5.2 消耗率 | Model Selector 頁面 | 0.6x（Specific Model） |
| Ollama Cloud 用量限制 | Ollama Pricing 頁面 | Pro $20：50x Free；DeepSeek-V4-Pro 為 level 4（extra heavy）；session 限制每 5h 重置 |
| Anthropic Pro 用量 | Anthropic Pricing 頁面 | $20/月；5h session window；含 Claude Code；無公開 token 配額 |
| Qoder Pro+ $60 能否用 Anthropic/OpenAI | Custom Models 頁面 | **不能**。BYOK 不支援 Anthropic/OpenAI，內建模型也不包含 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|----------|----------|----------|----------|
| 是否需要重新 fetch Qoder 模型列表 | 信任 R1 / 重新 fetch | 重新 fetch | R2 Q2 關鍵前提是 Qoder 是否支援 Anthropic/OpenAI，需最新資料驗證 |
| Ollama Cloud 用量細節 | 搜尋官方 fair use 頁面 / 以已知資料推估 | 搜尋官方定價頁面 | Ollama Pricing 頁面已提供足夠資訊（level 4 模型、session 限制） |
| Anthropic $20 方案細節 | 搜尋官方定價 / 以已知資料推估 | 搜尋官方定價頁面 | Anthropic 未公開具體 token 配額，僅知 session window 與相對倍數 |
| 是否 fetch OpenRouter 定價 | 需要 / 不需要 | 需要 | R2 Q2 涉及多方案比較，OpenRouter 作為對照組有參考價值 |
