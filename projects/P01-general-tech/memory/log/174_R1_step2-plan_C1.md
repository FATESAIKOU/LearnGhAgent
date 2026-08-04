# 174_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1 的任務是取得 Ozaki 的 Claudian Orchestra Template 的 repo metadata 與主要文件，同時補查使用者 MyBrain 中相關技術的既有立場，為後續比較分析建立資料基礎。

## 執行的動作與結果

| 動作 | 目的 | 預期效果 | 實際結果 |
|---|---|---|---|
| `gh repo view` + `gh api repos/.../contents` 取得 repo metadata 與目錄結構 | 了解 template 的完整檔案布局 | 取得 repo 基本資訊 | 完成。repo 含 17 個頂層項目（.codex/ .hermes/ .obsidian/ AGENTS.md 等） |
| 讀取 README.md、AGENTS.md、GETTING-STARTED.md | 理解架構全貌與核心契約 | 掌握 PKB 設計思想 | 完成。3 份文件完整取得 |
| 讀取 .codex/rules/ 下 7 份規則檔 | 理解 vault 內部運作規則 | 取得 frontmatter schema、tagging、Daily 操作、Inbox routing、agent boundaries 等細節 | 完成。7 份規則檔全部讀取 |
| 讀取 .codex/connections.yaml、.codex/config.toml、.codex/AGENTS.md | 理解 Codex 設定與外部接續註冊表 | 取得接續管理方式 | 完成 |
| 讀取 .hermes/config.yaml、.hermes/SOUL.md | 理解 Hermes 設定 | 取得 Hermes 的 provider 選擇與 persona | 完成 |
| 讀取 Meta/connections/ 目錄結構 | 確認支援的外部接續種類 | 確認 13 種接續（GitHub/Google Calendar/Tasks/Gmail/Drive/Slack/Discord/RSS/Clippings/Meeting/Zotero/Notion） | 完成 |
| 讀取 MyBrain 骨幹檔（判定總表、技術取捨準則、專案現況表） | 確認使用者對 Ozaki 所用技術的既有立場 | 取得比較基準 | 完成。Hermes→Adopt、Obsidian→試用、OKF→Reject、Codex CLI→無直接評估 |
| 讀取 MyBrain 中 HermesAgent、Obsidian、OKF 的個別評估檔 | 取得各技術的詳細評估理由 | 取得比較的細部依據 | 完成 |

## 動作結束後的現狀

| 驗證面向 | 驗證內容 | 結果 |
|---|---|---|
| Ozaki PKB 架構理解 | Obsidian Vault + Codex CLI（core agent）+ Hermes Agent（capture）+ Google Drive（sync） | 明確 |
| Ozaki PKB 內部結構定義 | 自幹的 AGENTS.md + .codex/rules/ + .codex/skills/ 體系，非套用 OKF | 確認。README 雖提及 OKF 為設計思想之一，但實際結構是自定義的 frontmatter schema + 目錄規約 |
| Ozaki PKB 的 capture 機制 | Hermes 為 capture 專任，外部接續認證由 Hermes 一元所有；Codex 不直接持有外部 token | 明確 |
| Ozaki PKB 的查照機制 | Daily 為唯一監査點，capture→aggregate→distill 三階段，on-demand 既定 | 明確 |
| 使用者 MyBrain 結構 | OKF 格式（.okf/ 目錄 + validate.py + reindex.py），三條主題軸（技術/抽象理解/日常）+ 時間軸（日誌） | 明確 |
| 使用者對 Ozaki 所用技術的立場 | Hermes→Adopt（browser 比 opencode 強）、Obsidian→試用（無明顯問題）、OKF→Reject（結構太固定）、Codex CLI→無評估 | 已確認 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇 | 理由 |
|---|---|---|---|
| 調研深度 | 只讀 README vs 讀到 rules/ 層級 | 讀到 rules/ 層級 | 使用者要求比較「內部結構定義」與「查照更新機制」，rules/ 層級才能回答 |
| MyBrain 查詢範圍 | 只查判定總表 vs 同時讀個別評估檔 | 兩者都讀 | 判定總表只有結論，個別檔才有評估理由，後者對比較分析必要 |
| 是否讀取 .codex/skills/ 下的 skill 定義 | 讀 vs 不讀 | 不讀（留 C2） | C1 已取得足夠的架構理解，skill 細節可在 C2 視需要補查 |
