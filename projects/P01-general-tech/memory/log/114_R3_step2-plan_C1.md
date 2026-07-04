# 114_R3_step2-plan_C1.md

## 狀況理解

R3 為 R2 的重現（force push 覆蓋導致遺失）。使用者要求：(Q1) 比較 Strix 與 PentestGPT，判斷是否重造輪子；(Q2) 給出 Strix 的實際一步一步執行指令。本 sub-step C1 負責取得兩者的 repo metadata 與 README 內容，為後續比較分析與指令撰寫提供基礎資料。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view usestrix/strix --json` | 取得 Strix repo metadata | 名稱、描述、stars、forks、license、語言、建立時間、topics | 成功：35.5K stars, 3.6K forks, Apache-2.0, Python, 2025-08-05 建立 |
| `gh repo view greydgl/pentestgpt --json` | 取得 PentestGPT repo metadata | 同上 | 成功：14.1K stars, 2.5K forks, MIT, Python, 2023-02-27 建立 |
| webfetch Strix README | 取得 Strix 完整 README | 安裝方式、使用範例、功能列表 | 成功：含 quick start、CI/CD 整合、多 agent 架構說明 |
| webfetch PentestGPT README | 取得 PentestGPT 完整 README | 同上 | 成功：含 v1.0 agentic upgrade、legacy 模式、benchmark（86.5% success rate） |
| `gh api repos/GreyDGL/PentestGPT/contents/pentestgpt` | 查看 PentestGPT 原始碼目錄結構 | 了解其架構組織 | 成功：core/、interface/、prompts/ 三個子目錄 |

## 動作結束後的現狀

**已取得的關鍵資料對照：**

| 面向 | Strix | PentestGPT |
|---|---|---|
| 建立時間 | 2025-08-05 | 2023-02-27 |
| Stars | 35.5K | 14.1K |
| License | Apache-2.0 | MIT |
| 核心語言 | Python | Python |
| 架構 | 多 Agent（root/recon/exploit/post）+ Docker sandbox | 單 Agent iteration loop + Claude Code CLI |
| 沙箱 | Docker 容器（內建 Caido proxy、瀏覽器、Python runtime） | 無獨立沙箱（依賴 Claude Code 的 sandbox） |
| 工具鏈 | 13 個內建工具（browser/shell/proxy/search 等） | 依賴 Claude Code 內建工具 |
| 多 LLM 支援 | 是（OpenAI/Anthropic/Google/Vertex/Bedrock/Azure/本地） | 是（legacy 模式支援 8+ provider；agent 模式僅 Claude） |
| 弱點驗證 | PoC 執行驗證（sandbox 中執行 Python exploit） | 依賴 LLM 推理判斷（無獨立 PoC 執行層） |
| 學術背景 | 無（開源專案） | USENIX Security 2024 論文 |
| 安裝方式 | curl 腳本 / pip | git clone + make install |
| CI/CD 整合 | GitHub Actions workflow 範例 | 無明確 CI/CD 範例 |
| 收費模式 | 開源 + 雲端平台（app.strix.ai） | 開源（MIT） |

**待後續 sub-step 處理：**
- C2：深入 PentestGPT 原始碼架構（core/ 目錄），理解其實作差異
- 產出更新版報告（§4 加入 PentestGPT DA 表 + §4.3 對照表 + §5 User Q&A）

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研深度 | 僅 README / README + 原始碼目錄 | README + 原始碼目錄 | 需了解 PentestGPT 架構才能做有意義的比較 |
| 是否需要重新 fetch Strix 資料 | 是（R1 資料可能過時）/ 否（沿用 R1） | 是 | R1 距今可能已有更新（v1.0.4），且需確認最新安裝指令 |
| 對照表欄位 | 僅 stars/license / 含架構/沙箱/工具鏈 | 含架構/沙箱/工具鏈 | Q1 核心問題是「是否重造輪子」，需架構層級比較 |
