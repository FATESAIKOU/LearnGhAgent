# 125_R1_step2-plan_C1.md

## 狀況理解

Step 2 的第一個 sub-step C1：取得 caveman repo 的 metadata 與主要文件。目標是收集足夠的原始資料，供後續 sub-step 進行分析收斂。技術標的為 JuliusBrussee/caveman — 一個讓 AI coding agent 以壓縮式「山頂洞人語」輸出、號稱減少 65% output token 的 skill/plugin。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh api repos/JuliusBrussee/caveman` | 取得 repo metadata | 取得 stars、forks、license、topics 等 | 成功：88k stars、5k forks、MIT、10 topics |
| `gh api repos/.../readme` (base64 decode) | 擷取 README.md | 了解產品定位、功能、安裝方式 | 成功：取得完整 README（產品 pitch、Before/After 對照、6 級強度、benchmark 表、生態系） |
| `gh api repos/.../contents/CLAUDE.md` | 讀取 maintainer 指南 | 了解架構設計、檔案布局、hook 系統 | 成功：取得完整 CLAUDE.md（單一真相來源規則、hook 架構、CI 同步流程、agent 分發矩陣） |
| `gh api repos/.../contents/INSTALL.md` | 讀取安裝文件 | 了解 30+ agent 的安裝方式 | 成功：取得完整安裝矩陣（每 agent 的安裝命令、是否 auto-activate） |
| `gh api repos/.../contents/docs/HONEST-NUMBERS.md` | 讀取誠實數字文件 | 了解真實 token 節省與成本 | 成功：取得完整分析（65% output 節省、~1-1.5k input 成本、net-negative 場景） |
| `gh api repos/.../contents/skills%2Fcaveman%2FSKILL.md` | 讀取核心 skill 提示詞 | 了解 caveman 實際運作機制 | 成功：取得完整 SKILL.md（6 級強度規則、auto-clarity 例外、wenyan 文言文模式） |
| `gh api repos/.../contents/SECURITY.md` | 讀取安全政策 | 了解隱私與 telemetry 狀況 | 成功：確認零 telemetry、零 network calls after install |
| `gh api repos/.../contents/package.json` | 讀取專案 metadata | 了解版本、依賴、entry point | 成功：Node ≥18、bin 指向 bin/install.js |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Repo metadata | 確認 stars、forks、license、topics | 88,027 stars / 5,058 forks / MIT / 10 topics（ai, anthropic, caveman, claude, claude-code, llm, meme, prompt-engineering, skill, tokens） |
| 核心文件完整性 | 確認已取得 README、CLAUDE、INSTALL、HONEST-NUMBERS、SKILL、SECURITY、package.json | 7 份關鍵文件全部取得 |
| 技術定位 | 確認 caveman 是 system-prompt skill 還是 model fine-tune | 純 system-prompt skill，非 fine-tune |
| 生態系範圍 | 確認相關專案 | caveman（本體）、caveman-code（完整 agent）、cavemem（記憶）、cavekit（build loop）、cavegemma（fine-tune） |
| 資料充足性 | 判斷是否需要額外背景查詢 | 需補查：caveman 所依賴的「AI agent skill/plugin」技術背景、token 計價背景、wenyan 文言文壓縮原理 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件讀取範圍 | (a) 僅讀 README (b) 讀 README + 關鍵子文件 (c) 讀所有文件 | (b) 讀 README + 7 份關鍵文件 | 涵蓋產品、架構、安裝、成本、安全、核心機制，足以支撐分析 |
| 是否讀取原始碼 | (a) 讀 hooks 原始碼 (b) 不讀原始碼 | (b) 不讀原始碼 | CLAUDE.md 已充分描述 hook 架構與安全機制，原始碼細節對分析報告貢獻有限 |
| 背景查詢需求 | (a) 僅用 repo 文件 (b) 補查外部背景 | (b) 補查外部背景 | 需補查：AI agent skill/plugin 技術背景、token 計價模型、wenyan 文言文壓縮原理 — 留給 C2 |
