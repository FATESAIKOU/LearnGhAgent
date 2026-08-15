# 233_R1_step2-plan_C1.md

## 狀況理解

Step 1 已定標的：**prime-agent**（Prime Intellect 開源的自進化 RLM 程式設計／研究 Agent）。本 sub-step C1 是 Step 2 的第一個資訊取得動作：取得 repo metadata、擷取主要文件、補查背景脈絡。標的為新技術，需從 repo 與網路建立骨架，供後續 C2（RLM 機制深挖）與 C3（替代方案）收斂。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view PrimeIntellect-ai/prime-agent` | 取得 repo metadata | 掌握 stars、license、語言、更新時間 | 16,145 stars、1,733 forks、MIT、TypeScript、created 2026-05-08、updated 2026-08-15、非 archived、default branch `main` |
| `gh api .../contents/` 列根目錄 | 了解 repo 結構 | 找出關鍵文件位置 | 根含 `AGENTS.md`、`README.md`、`packages/`（agent/ai/coding-agent/tui）、`prime-agent-runtime`、`install.sh` |
| 抓取 README.md | 取得定位與核心抽象 | 掌握「解決什麼問題」 | 定位＝general/long-running coding & research agent；兩大抽象：**RLM**（prompt-as-variable、subagent-as-function-call、persistent REPL）＋ **Continual Harness**（durable state、`/refine` 自改進、可 rollback） |
| 抓取 `packages/coding-agent/docs/rlm.md` | 深挖 RLM 程式設計模型 | 掌握核心機制 | RLM loop：parent model → persistent IPython kernel → data/skills/`rlm(...)` child agents；4 invariants：programmatic execution、native subagents、Python-backed skills、state outlives one turn；trust model＝非 sandbox |
| 抓取 `packages/coding-agent/docs/architecture.md` | 了解系統架構 | 掌握 daemon/worker/kernel 邊界 | TUI/headless → AgentConnection → daemon supervisor → session worker（AgentSessionRuntime + root kernel + RLM children）；worker/kernel 分離為 lifecycle 隔離非安全沙箱 |
| 抓取 `AGENTS.md` | 了解開發規則 | 補 repo 文化脈絡 | 開發規則（無 inline import、daemon protocol 版本化、7-day dependency cooldown 等） |
| webfetch Prime Intellect RLM blog | 補 RLM 背景與實驗數據 | 掌握 RLM 為何、效果 | RLM 起源（Alex Zhang 2025-10）、context folding 定位、4 環境消融（DeepDive/math-python/Oolong/verbatim-copy）、GPT-5-mini 為主、RLM 提升長上下文與 token 效率但增加時間、需 RL 訓練釋放潛力 |
| webfetch arXiv 2512.24601（RLM 論文） | 補 RLM 學術定義 | 掌握正式定義與數據 | RLM＝inference-time scaling 範式，可處理超出 context window 兩數量級；median 提升：vs compaction +26%、vs CodeAct +130%、vs Claude Code +13%；RLM-Qwen3-8B 超越底層 28.3% |
| webfetch arXiv 2605.09998（Continual Harness） | 補 Continual Harness 背景 | 掌握自改進 harness 機制 | 源自 Gemini Plays Pokemon；reset-free 自改進 harness，agent 交替 act/refine 自己的 prompt、sub-agents、skills、memory；線上 process-reward co-learning loop |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata | gh repo view 欄位 | 完整取得（stars/license/language/日期） |
| 核心文件 | README + rlm.md + architecture.md | 已取得，含 RLM 機制與系統架構 |
| 背景脈絡 | RLM blog + 2 篇 arXiv | 已取得 RLM 定義、消融數據、Continual Harness 定位 |
| 反爬 | 是否遭遇 CAPTCHA | 無，webfetch/gh api 全程成功，未用 CDP |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件範圍 | 只抓 README / 抓 README＋關鍵子文件 | 抓 README＋rlm.md＋architecture.md＋AGENTS.md | 標的同時含「agent 產品」與「RLM 訓練機制」兩層，需架構與機制文件支撐 |
| 背景來源 | 只靠 repo / 補網路 | 補 RLM blog＋2 篇 arXiv | RLM 與 Continual Harness 為論文級概念，需原始定義與實驗數據 |
| 後續分工 | 一次抓完 / 拆 C2、C3 | 拆 C2（RLM 機制深挖）、C3（替代方案） | 依 AGENTS.md 5 點格式，替代方案需獨立收集 |
