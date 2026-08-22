# 242_R1_step3-qa.md

## 狀況理解

Step 3：對 C1 調研資料做硬性（validate-report.sh）與軟性（judge/step3-qa.md review 觀點）驗證，產出最終分析報告 `output/242_switchyard.md` 與本 step log。標的為 Switchyard（NVIDIA-NeMo，Rust LLM 流量 proxy + 路由 + 協議翻譯）。依 judge 觀點 7，§4 必須對照第二大腦既有判定並標註 URL 與信任層級、AI draft 需註明未經 review、與既有判定衝突時需明確指出。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| mybrain-read refresh + 讀骨幹（技術取捨準則） | 取使用者技術決策準則 | 避免照通則推薦到反方向 | 掌握：理解優先/先自己兜、MVP→Feature 看 workflow、Reject≠沒價值 |
| 讀 `技術/技術評估/判定總表.md` 路由相關行 + grep switchyard/litellm/openrouter/portkey | 確認替代方案既有判定 | 知道哪些有判定、哪些無 | Switchyard 零命中；OmniRoute=Accept(draft)；LiteLLM/OpenRouter/Portkey 無獨立評估，僅列為 OmniRoute 對照組 |
| 讀 `OmniRoute.md` 全文 | 取得 decoupling 判定細節 | 引為 §4 主要對照 | Accept，本質 LLM Provider 解耦層；標 draft |
| 讀 `DeepSeek V4.md` 路由段 | 抓 user stable 判準 | 找出與本標的衝突 | 命中「降低 Model Routing 優先級」（human, stable）→ 與 Switchyard 主體直接衝突 |
| 讀 `下一步清單.md` | 確認 APIGateway 行動 | 定位本標的落點 | 「LLM APIGateway 試用（解耦）——OmniRoute」尚未 MVP，對照組= LiteLLM/OpenRouter/Portkey |
| clone repo 並讀 README/core_concepts/routing overview/llm_classifier/stage_router/getting_started | 補足演算法細節與成本 | 收斂 §3 客觀描述 | 取得演算法決策機制與各額外 model call 副作用 |
| 寫報告 `output/242_switchyard.md` | 產出最終成果物 | 符合 5 點格式 | 含 4 section；§4 對照二腦標 URL/信任層級，並設衝突聲明 |
| 驗證（validate-report.sh） | 硬性檢查 | 長度/4 section/檔名 | 長度 <50000、4 section 齊、檔名符合 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 產出報告檔名 | `242_switchyard.md`，`pr-id=242, tech=switchyard` | 符合 `(pr-id)_(tech).md` |
| 本輪變更摘要 | 首次產出（R1） | 新增分析報告（僅 4 section，無 §5）；並寫本 step log |
| §4 對照既有判定 | 對照 OmniRoute(Accept,draft)、DeepSeek V4(降路由優先,stable)、清單對照組 | 均有標 GitHub URL 與信任層級；AI draft 註明未經審查 |
| 衝突明示 | 與 DeepSeek V4 stable「降低 Model Routing」衝突 | 已在 §4 設「⚠️ 衝突聲明」明確指出並給處置 |
| 語言/結構 | 中文、表格、無模糊用詞 | 合規 |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 技術名 | `switchyard` / `switchyard-nemo` / `llm-router` | `switchyard` | 用 repo 名稱，簡潔、唯一 |
| §4 替代方案選取 | 只列 LiteLLM/OpenRouter/Portkey / 含 OmniRoute + 自研 wrapper | 含 OmniRoute + 自研 wrapper | 第二腦已拍 OmniRoute（decoupling）與「先自己兜」準則，替換方案需與個人判準對齊 |
| 與 DeepSeek V4 衝突處理 | 忽略 / 附註 / 明確衝突聲明 | 明確衝突聲明 | 第二腦 stable 判定與本標的主體直接衝突，是對照最有價值處，判準要求必標 |
| libsy 詳細 API 深挖 | 不深挖 / 深挖 | 不深挖（述） | 報告僅回答 5 問題，libsy 機制已在 §3 概述，避免延伸 |
