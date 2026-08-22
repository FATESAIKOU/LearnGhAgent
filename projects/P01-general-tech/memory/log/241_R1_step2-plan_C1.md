# 241_R1_step2-plan_C1

## 狀況理解

Step 1 已定調：全新技術調研，標的為「needle — 端側的超小型工具調用模型」（cactus-compute/needle）。本 sub-step C1 為 Step 2 的第一個資料取得動作，依 do/skills/document/SKILL.md 標準流程：取得 repo metadata → 擷取主要文件 → 補查背景脈絡。目的在建立對該技術的完整事實基礎，供後續 C2+ 收斂成分析報告。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view cactus-compute/needle --json ...` | 取得 repo metadata | 掌握 stars、license、分支、更新時間 | 成功：8,425 stars、Apache-2.0、main 分支、2026-08-22 更新、description「14MB foundation model for tiny devices」 |
| `curl` 抓 README.md | 擷取主要文件 | 掌握定位、架構、用法 | 成功：取得完整 README（Needle 2、45M 參數、14MB 單一二進位、28MB RAM 全 session） |
| `curl` 抓 doc/apis.md | 擷取 API 文件 | 掌握核心 API 與行為契約 | 成功：取得完整 API（Needle/run/complete/extract/tool/Field）、行為、tool retrieval、confidence、offline 部署 |
| `curl` 抓 doc/finetuning.md | 擷取微調文件 | 掌握 LoRA 微調與 export 流程 | 成功：取得資料格式、finetune/build 指令、JAX 後端 |
| `curl` 抓 llms.txt | 擷取給 AI 的摘要 | 交叉驗證核心 API | 成功：取得精簡 API 摘要，與 apis.md 一致 |
| `curl` 抓 arXiv:2607.18363 | 補查背景（Simple Attention Network 論文） | 掌握架構理論基礎 | 成功：確認 SAN 論文（attention-only transformer，刪除 FFN 的受控研究） |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo 基本資料 | gh repo view | 8,425 stars、Apache-2.0、main、2026-08-22 更新 |
| 核心定位 | README 開頭 | 45M 參數、14MB 單一二進位、28MB RAM、工具調用/裝置使用/結構化抽取 |
| 核心機制 | README + apis.md | 5 大機制：self-contained、grammar-constrained JSON、confidence-gated、tool retrieval、bounded memory（256-token sliding window + KV sinks） |
| 架構理論基礎 | arXiv 論文 | Simple Attention Network（attention-only，Hadamard MLP 取代 FFN、GQA、engram KV memory、multi-lane hyper-connections） |
| 微調/部署 | finetuning.md + apis.md | LoRA 微調→merge→export 單一 .cact；offline/air-gapped 部署流程完整 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件擷取範圍 | ① 只 README ② README+doc/apis+finetuning+llms.txt | ② 全擷取 | 標的機制複雜（5 大機制），需完整 API 與微調文件才能支撐報告 §3 機制描述 |
| 背景補查方式 | ① 只靠 README ② 追 arXiv 論文 | ② 追 arXiv | README 提及 SAN 論文，需原始論文確認架構理論基礎，避免只轉述 README |
| 是否需 CDP | ① 一般 fetch ② CDP | ① 一般 fetch | 所有抓取皆成功，無 CAPTCHA/反爬，不需 CDP |
| 是否需查第二大腦 | ① 查 ② 不查 | ② 不查 | Step 1 已確認無既有評估，C1 專注事實取得，不重複 |
