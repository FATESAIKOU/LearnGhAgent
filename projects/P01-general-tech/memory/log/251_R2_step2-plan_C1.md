# 251_R2_step2-plan_C1

## 狀況理解

- 本 sub-step 為 R2 的 Step 2 第一個調研動作。R2 意圖（Step 1 已定調）是兩個子題：①以五面向（a.免費額度網羅 b.私有訂閱登錄 c.能否簡單自擴調度規則 d.無多餘 GUI/TUI、輕量 e.維護者/穩定度）把第二大腦所有類似技術拉入深入比較；②基於 1 接上「個人 AiAgent 入口」的落地做法＋判定 GAS/Serverless/VPS/私有機器哪個好。
- 因此 C1 不是重做 R1 的「取得 freellmapi 基本資料」，而是**針對 R2 意圖補抓資料**：①freellmapi 在五面向上的現況（尤其 c 自擴調度、b 私有訂閱、d 輕量、e 維護者）；②部署面向（Docker/自架/ARM SBC）以支撐子題 2 的環境判定。
- 同時把第二大腦中「所有類似技術」的既有評估檔撈出，作為 C2 深入比較的原料。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` 取 metadata | 掌握最新 stars/更新/授權/語言 | 確認維護活躍度（面向 e） | 24,300 stars、3314 forks、MIT、TypeScript、updated 2026-09-05（活躍）、非 archived |
| 抓 README.md（490 行） | 掌握定位、custom provider、routing、比較表 | 面向 a/b/c/d 的現況 | 見下方摘要 |
| 抓 docs/architecture.md（96 行）＋ architecture/01-routing-and-bandit-scoring.md | 掌握 routing 策略與自擴機制 | 面向 c 的深度 | 6 策略、bandit、profile、custom relay 機制 |
| 抓 docs/deployment/01-docker.md＋install.md | 掌握部署方式 | 支撐子題 2 環境判定 | Docker/Compose/ARM SBC/desktop/Node 20+ 皆可 |
| 抓 docs/providers/03-adding-a-new-provider.md | 掌握新增 provider 的難度 | 面向 c 的「自擴」 | 需改 Platform union＋adapter＋catalog，非純設定 |
| 讀第二大腦 OmniRoute/Switchyard/個人 AiAgent 入口/gas-aiagent-core/技術取捨準則/下一步清單 | 撈出所有類似技術與落地脈絡 | 建立比較清單與部署判定原料 | 見下方「第二大腦原料」 |

### freellmapi 五面向現況（C1 摘要）

- **a. 免費額度網羅**：34 providers、635 免費 endpoint、7.4B tokens/月；自更新 signed catalog（免費版落後 30 天、Premium 即時）。
- **b. 私有訂閱登錄**：README 明列「custom provider」——可從 Keys 頁把 chat/embedding/image/audio 指到任何 OpenAI 相容 endpoint（llama.cpp、LM Studio、vLLM、本地 Ollama、遠端 gateway）。**可登錄私有/自架 endpoint**。
- **c. 自擴調度規則**：6 種 routing 策略（priority/balanced/smartest/fastest/reliable/custom）＋命名 fallback-chain profile（`auto:<profile>`）＋dashboard/PUT API 切換；custom relay 以 `custom:<base_url_hash>` 獨立計分。**但新增「provider」需改程式碼**（Platform union＋adapter＋catalog），非純設定。
- **d. 輕量/無多餘 GUI**：Express proxy＋React dashboard（admin 用）；~40MB RSS idle；可跑 Node 20+ 任何處（含 ARM SBC）。**有 dashboard 但屬管理面，非強制**。
- **e. 維護者/穩定度**：24.3k stars、3314 forks、2026-04 建立、持續活躍（2026-09-05 更新）、MIT、單人主導但社群大。

### 第二大腦原料（比較清單與落地脈絡）

- **OmniRoute**（技術評估，verdict 採用，draft）：250+ Provider/90+ free、18 路由策略、token 壓縮、MCP；本機單一 Endpoint。
- **Switchyard**（技術評估，verdict 試用，draft）：NVIDIA-NeMo Rust 路由 proxy，依任務/品質/成本切 endpoint；無 Provider 目錄、無 quota 感知；定位「路由政策層」。
- **LiteLLM/OpenRouter/Portkey**：僅在 OmniRoute/下一步清單作對照組，無獨立評估。
- **個人 AiAgent 入口**（靈感，draft）：app＋拆開後端；執行環境三選項（自架實體/自架雲端/跑終端）未定案；08-30 新增 MultiProvider 需求（接既有 LLMGateway/自建/App 內嵌三方向未比較）。
- **gas-aiagent-core**（動手做，draft）：GAS 白嫖路線產出；LLM Provider 抽象＋Tool Registry＋Loop Driver；Exec Provider 只有介面無實作。
- **技術取捨準則**（骨幹，draft）：理解優先、MVP→Feature 看 workflow、Reject≠沒價值、汰換看上游死沒死。
- **下一步清單**：第 71 條「試玩 OmniRoute＋Switchyard 組合（Model Router 線）」；第 79 條「決定 app 版 MultiProvider 方向（接既有 LLMGateway/自建/App 內嵌三選一）」。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 五面向資料齊備 | README/architecture/deployment/providers 四類文件 | a/b/c/d/e 皆有對應資料，可支撐 C2 打分 |
| 比較清單完整性 | 第二大腦 grep gateway/router/聚合 | OmniRoute、Switchyard、LiteLLM/OpenRouter/Portkey（對照組）＋本標的 freellmapi |
| 落地脈絡 | 個人 AiAgent 入口＋gas-aiagent-core＋下一步清單 | 子題 2 的接入口（MultiProvider 三方向）與部署三選項脈絡已取得 |
| 反爬阻擋 | 全程 gh api/raw | 未觸發 CAPTCHA，無需 CDP |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| C1 抓取範圍 | ① 重抓 R1 全部文件 ② 只抓 R2 意圖相關 | ② | R1 已抓 README/architecture/api；R2 需補 deployment、providers、routing 深度，避免重複 |
| 是否重取 metadata | ① 沿用 R1 ② 重取 | ② | repo 自 R1 後更新（stars 22k→24.3k、updated 2026-09-05），面向 e 需最新值 |
| 比較清單來源 | ① 只列 freellmapi ② 拉第二大腦全部類似技術 | ② | 使用者明言「把第二大腦有的類似技術全部拉入」；含 OmniRoute、Switchyard、LiteLLM/OpenRouter/Portkey |
| 子題 2 資料 | ① 只查 freellmapi 部署 ② 併讀個人 AiAgent 入口/gas-aiagent-core | ② | 落地判定須對齊既有「執行環境三選項」與 GAS 白嫖路線，不能脫離既有專案空談 |
