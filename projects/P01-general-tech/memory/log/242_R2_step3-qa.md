# 242_R2_step3-qa.md

## 狀況理解

Step 3：對 R2 的 C1 調研（Switchyard 與 OmniRoute 的 Provider 廣度對照 + claudecode/opencode 安裝手順）做硬性（validate-report.sh）與軟性（judge/step3-qa.md）驗證，產出/更新最終報告 `output/242_switchyard.md` 與本 step log。R2 使用者 3 問：Model 廣度差異、Switchyard 安裝手順、OmniRoute 安裝手順，皆有「已 OllamaCloud/Claude 訂閱」前提。依 judge 觀點 7，§4 替代方案須對照 MyBrain 判定並標 URL/信任層級、AI draft 註明未經 review、衝突明示。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| mybrain-read refresh + 讀骨幹（技術取捨準則） | 取個人技術決策準則 | 避免照通則推薦到反方向 | 掌握：理解優先/先自己兜、MVP→Feature 看 workflow、Reject≠沒價值 |
| 讀 `判定總表.md` + grep omniroute/litellm/openrouter/portkey/model routing | 確認替代方案既有判定與廣度快照 | 知道誰有判定誰無 | OmniRoute=Accept(draft)；LiteLLM/OpenRouter/Portkey 僅列對照組；DeepSeek V4(降路由,stable) 存在 |
| 讀 `OmniRoute.md`、`DeepSeek V4.md`、`下一步清單.md`、`整理 claudecode-opencode 環境.md` | 取對照與環境脈絡 | 銜接導入實務 | OmniRoute Accept(250+ 快照)；清單有「APIGateway 試用—OmniRoute」未 MVP；claude/opencode 已完整整理成功(human stable) |
| 讀 `142_OmniRoute.md` R1 對照 | 補 Provider 數字細節 | 校準 250+→live 數字 | 舊快照 250+/1.54B；C1 抓到官方 live 340/1200+/1.53B |
| 更新報告：§4 DA 表廣度數字 + 追加 `## 5. User Q&A`（Q1-Q3） | 沉澱本輪 QA、校準快照 | 符合 §5 格式 | 新增 3 條 QA，含廣度結構對照、兩套安裝手順、落地難度對照；既有 §1-§4 未刪 |
| 驗證（validate-report.sh） | 硬性檢查 | 長度/4 section/檔名 | 21134 bytes < 50000、4 section 齊、檔名 `242_switchyard.md` 符合 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 產出報告檔名 | `output/242_switchyard.md`，沿用 R1 檔名 | 符合 `(pr-id)_(tech).md`；未改名 |
| 本輪變更摘要 | R2 追加 | §4 OmniRoute 廣度快照更新（250+→340/live）；新增 `## 5. User Q&A`（Q1 廣度差異、Q2 Switchyard 安裝、Q3 OmniRoute 安裝＋附落地對照）；既有 §1-§4 內容未刪 |
| §4 對照既有判定 | 對照 OmniRoute(Accept,draft)、DeepSeek V4(降路由優先,human stable)、清單對照組 | 均有標 URL/信任層級；AI draft（OmniRoute）註明未經審查 |
| 衝突明示 | 與 DeepSeek V4 stable「降低 Model Routing 優先級」衝突 | §4 已設「⚠️ 衝突聲明」；本輪 QA 結論再重申「廣度/免費額度軸指 OmniRoute，Switchyard 僅當細路由補強」 |
| 語言/結構 | 中文、表格、圖示、無模糊用詞（可能/也許/我認為） | 合規 |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 廣度數字來源 | 沿用二腦「250+」/ 官方 live「340」 | 採官方 live 340/1200+ | R1 是 2026-07 快照已過期；C1 抓到 v3.8.50 最新 metadata |
| §4 替代方案選取 | 只列既有 / 含 OmniRoute + 自研 wrapper | 維持既有含 OmniRoute | 二腦已拍 OmniRoute(decoupling) 與「先自己兜」，替換需與個人判準對齊 |
| QA 觸發處理 | 只回答 / 沉澱進 §5 | 沉澱進 §5（Q1-Q3） | AGENTS.md §5 規則：質問型句構觸發，追加不刪改既有 QA |
| Q2/Q3 標題 | 沿用使用者原文 / 保留口吻改寫 | 保留口吻改寫 | 符合 §5「保留原提問語氣」；Q1 原樣句構即為問題題 |
| 安裝手順詳度 | 只給指令 / 含承接關係與坑 | 給指令＋承接關係＋坑 | R2 要「能用」+「已有訂閱」前提，需講 base_url 指法與 OllamaCloud/Claude 上游 client 承接 |
