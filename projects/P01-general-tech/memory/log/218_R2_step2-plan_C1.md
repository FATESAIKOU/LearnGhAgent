# 218_R2_step2-plan_C1.md

## 狀況理解

R2（PR #218）使用者不再問「這是什麼」，而是三連問，合起來是一個**硬體採購＋自建 AI agent 工作區**的評估意圖，非 R1 的重做：

1. **對樹莓派的優勢**：問「便宜＋雖不好開發但效能夠」這個判斷是否成立 → 需 ROCK 3C vs Pi 的規格/價格/生態比較。
2. **AI agent 工作區可行性**：想用 OllamaCloud/claude 配 opencode/claudecode 開**常駐 agent**，問 ROCK 3C 是否合適 → 關鍵是區分「本板算力 vs 雲端推論」的分工，以及 1GB RAM 是否夠跑常駐 CLI agent。
3. **微型電腦取捨**：預算 <3 萬日幣、想開 2–3 個 agent、甚至跑瀏覽器，問是否改買微型電腦 → 需 x86 N100 級 mini-PC 對照。

C1 依 document skill 標準動作，針對**這輪意圖**補 metadata：opencode repo 取得（gh），opencode 使用模型來源（官方 docs），Pi 規格補查（raspberrypi.com 403 反爬，改用通用知識＋R1 既有 §4 比較），ROCK 3C 規格沿用 R1 一手來源。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| gh repo view anomalyco/opencode | 取得 opencode（問題 2 的軟體核心）repo metadata | 掌握版本狀態、授權、規模 | anomalyco/opencode，**MIT**，stars **196,910**，desc「The open source coding agent」——opencode 是活躍的 terminal coding agent |
| 抓 opencode 官方 docs（opencode.ai/docs/） | 確認 opencode 的執行模型來源（本地 vs 雲端） | 判斷「ROCK 3C 是否需在本地跑推論」 | opencode **不帶本地模型**，靠 API keys 連 LLM provider（含 Ollama/雲端）→ **推論在雲端/OllamaCloud 遠端**，板子只需當 CLI 客戶端 |
| 抓 Radxa docs ROCK 3C Features（沿用 R1） | 取得本板精確 RAM/CPU 以評估「跑 2–3 agent」 | 評估 1GB 上限 | 本商品為 **1GB LPDDR4**（系列另有 2/4GB）、四核 A55 1.6GHz、無 NPU 強調、5V/2A、eMMC+microSD |
| 補查 Pi 5 規格（raspberrypi.com） | 做 ROCK 3C vs Pi 的規格/價格比較 | 驗證「便宜但不好開發」假設 | **403 反爬**，未取得官方頁；改依通用知識＋R1 §4 既有比較（Pi 生態最熟、價格較高）補足，C2 視需要再用 CDP |
| 補查微型電腦對照（通用知識） | 評估 x86 N100 級 mini-PC 作為問題 3 的替代載體 | 建立預算/多 agent/瀏覽器對照 | N100 級 mini-PC（4/8GB RAM、x86 原生、可插瀏覽器/桌面）與 ROCK 3C 在「RAM 容量、x86 相容性、體積功耗價格」上作對照，留待 C2 收斂 |

**關鍵技術事實（供 C2 收斂）：**
- **分工關鍵**：opencode/claudecode 連 **OllamaCloud/claude（雲端推論）**，重算在遠端；ROCK 3C 只需當 CLI 客戶端跑 Node/CLI＋終端，不需本地 NPU——這**推翻了 R1 中「與 NVIDIA 板比較 AI 算力」的框架**，本輪核心是「RAM/多工/相容性」而非算力。
- **RAM 瓶頸**：本商品 **1GB** 對「開 2–3 個常駐 agent」極緊；每 agent 一個 opencode/claudecode 進程＋Node runtime＋git 工作樹，1GB 會 swap；瀏覽器（問題 3 需求）幾乎不可行。系列 2/4GB 較可行。
- **價格定位**：RS 價 ¥7,835（未稅）接近「低成本」，與同級樹莓派價格差異不大；「便宜」優勢在 RAM/型號組合上需實際對價。
- **生態 vs 效能夠**：「不好開發」不精確——RK3566 有官方 Debian OS，但社群/文件遠遜 Pi；「效能夠」指**通用運算/多媒體**夠（A55 1.6GHz），非 AI 算力。
- **Mini-PC 替代**：N100 級 x86 mini-PC（8GB）對「2–3 agent＋瀏覽器＋<3 萬日幣」更貼合：x86 原生 Node/Chrome、RAM 充裕、功耗仍低；換取的是失去 GPIO/嵌入式彈性與較大體積。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| opencode 執行模式 | opencode 官方 docs | 確認推論走雲端/Ollama，ROCK 3C 只需當 CLI 客戶端 |
| opencode metadata | gh repo view | 取得 MIT、196,910 stars、desc |
| ROCK 3C 規格（1GB 限制） | Radxa docs | 本商品 1GB LPDDR4、四核 A55 1.6GHz、無 NPU |
| Pi 比較資料 | raspberrypi.com | 403 反爬未取得；R1 §4 既有比較＋通用知識可支撐 |
| Mini-PC 對照 | 通用知識 | N100 級 8GB 作為問題 3 替代載體納入 C2 |
| C2 缺口 | 收斂評估 | 需收斂：分工模型、RAM/多 agent 承載、價格/預算對照、Pi vs mini-PC 結論 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否重做 R1 的「這是什麼」 | (A) 重做 (B) 針對 R2 意圖（比較/agent/mini-PC） | B | R2 是採購＋agent 工作區評估意圖，重做 R1 是冗餘；只補 R2 需要的資料 |
| opencode 是否視為本地推論 | (A) 誤以為需本地算力 (B) 確認雲端推論、板子當客戶端 | B | 官方 docs 明示靠 provider API key；這決定評估核心是 RAM/多工非算力，避免方向錯誤 |
| Pi 比較來源 | (A) CDP 硬繞 403 (B) 用 R1 §4＋通用知識、C2 再決定 | B | 403 反爬；CDP 慢僅必要時用。R1 已有 Pi 定位比較，C2 收斂即可 |
| 1GB 商品是否作為唯一評估對象 | (A) 只評 1GB (B) 一併提系列 2/4GB 對照 | B | 使用者要「開 2–3 agent」，1GB 會是硬瓶頸，須指出系列高 RAM 版才可行，避免誤導 |
| Mini-PC 納入否 | (A) 只答 ROCK 3C (B) 納入 N100 對照 | B | 問題 3 明要求「微型電腦是否更適合」，不納入會漏掉他真正的取捨 |
| 下一步 C2 方向 | (A) 直接寫報告 (B) 收斂分工/RAM/預算對照表 | B | 需把本 C1 關鍵事實收斂成可寫入報告 §4 與 User Q&A 的結論 |
