# 235_R1_step2-plan_C1.md

## 狀況理解

Step 1 已判定標的為 deepseek-harness（DeepSeek AI 開源 Agent Harness，GitHub: deepseek-ai/deepseek-harness），R1 首輪、無前輪對話。Step 2-C1 需依 do/skills/document/SKILL.md 標準調研動作：取得 repo metadata、擷取 README 與關鍵子文件、補查背景脈絡。目標是把 repo 的輪廓、架構、核心機制收斂出來，作為 C2+ 深入各面向的基礎。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 do/skills/document/SKILL.md | 確認標準調研動作 | 依規範執行 | 確認四步：metadata、主要文件、背景脈絡、收斂撰寫；CDP 僅在反爬時用 |
| `gh repo view deepseek-ai/deepseek-harness` | 取得 repo metadata | 拿到 stars/license/語言/時間 | stars 109,712；forks 10,579；主語言 TypeScript；MIT；預設分支 master；created 2026-08-13、pushed 同日；topics: cordis, dsh, dsh-plugin, ai-agents |
| `gh api .../contents/` | 列出根目錄結構 | 找到 README/docs/packages 等關鍵文件 | 根目錄含 README.md/.zh、AGENTS.md、BENCHMARK.md、docs/、packages/、native/、python/、vendor/、website/、examples/ |
| 擷取 README.md 與 README.zh.md | 了解專案定位與用法 | 取得簡介、運行方式、社群 | 確認是「一切皆插件」架構、由 Cordis 驅動；目前 developer preview、會破壞相容；`npx @deepseek-ai/dsh web` 起 Web UI（port 3080）；中文版提供企微社群 |
| 擷取 docs/architecture.md | 了解核心架構 | 取得 plugin tree、events、turn flow | 取得 Cordis 架構、profiles/bundles 分層、核心 packages、事件域、step/turn 流程、capability seams、擴充點表 |
| 擷取 docs/cordis-primer.md | 了解底層框架 | 取得 Cordis 五大概念 | 確認 plugin/context/inject/typed events/可逆 effect；dispatch 模式（emit/waterfall/parallel/serial）|
| `gh api .../contents/docs` 與 `.../contents/packages` | 盤點子文件與套件 | 取得後續可深挖的清單 | docs 有 agent-lifecycle、api-gateway、capability-seams、tool-execution-pipeline、subsystems 等；packages 有 core、llm、tools、session、sandbox、shell、mcp、lsp、subagent 等 50+ 套件 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| metadata | gh repo view 回傳 | 完整取得（stars、license、語言、時間、topics）|
| 專案定位 | README 中英對照 | 「一切皆插件」agent harness、Cordis 驅動、developer preview |
| 架構理解 | architecture.md | plugin tree、events、turn flow、seams 皆已取得原始內容 |
| 底層框架 | cordis-primer.md | Cordis 五大概念與 dispatch 語意已取得 |
| 深挖線索 | docs/ + packages/ 清單 | 已盤點 30+ docs 與 50+ packages，供 C2 挑選 |
| 前輪干擾 | 檢查 memory/log | 有 235_R1_step1-intent.md，無其他 235 前綴檔案 |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否用 CDP | CDP / 一般 curl+gh | 一般 curl+gh | raw 與 API 皆直取成功，無 CAPTCHA，遵循 SKILL「僅必要時才用 CDP」 |
| 深挖優先順序 | 只看 README / 兼取架構文件 | README + architecture + cordis-primer | 需了解「怎麼運作」的核心機制，才能回答報告第 3 點 |
| 是否讀中英雙版 | 只看英文 / 中英對照 | 中英對照 | 使用者用中文，中文版有英文版沒有的企微社群資訊 |
| C2 之後深挖什麼 | 全盤都讀 / 聚焦核心機制 | 聚焦 tools 管線、session log、agent loop、sandbox、替代方案 | 對應報告 5 點所需，避免無邊際調研 |
