# 288_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1：取得 `t8y2/dbx` 的 repo metadata 與主要文件。標的是「100+ 資料庫的輕量跨平台客戶端」，實作跨 Rust / Vue / Java / Go 多語言，故主要文件＝README、架構文件（`crates/ARCHITECTURE.md`）、MCP/CLI 子專案 README、官方 docs 與 skills。C1 需先把 metadata、檔案結構、技術堆疊、驅動架構、安全模型盤點齊，供 C2 補背景、替代方案與 DA 表。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh api repos/t8y2/dbx` + `gh repo view` | 取 metadata | stars/license/語言/時序 | 24,696 stars、2,246 forks、105 watchers、Apache-2.0、Rust、created 2026-04-29、pushed 2026-10-05、size 212,888 KB、open issues 1,019、topics 19 個 |
| `gh api .../readme` | 取 README | 定位/功能/安裝/堆疊 | 632 行；25MB、100+ DB、AI、MCP、CLI、Docker；附大量贊助與社群徽章 |
| `gh api .../git/trees?recursive=1` | 取完整檔案結構 | 確認組成 | 7,723 條路徑；頂層有 `crates/`、`agents/`、`packages/`、`apps/`、`docs/`、`plugins/`、`skills/`、`src-tauri/`、`vendor/` |
| `gh api .../languages` | 語言佔比 | 判斷主體語言 | Rust 24.5M、TypeScript 18.6M、Vue 11.0M、Go 3.7M、Java 3.2M bytes |
| 讀 `Cargo.toml` / `crates/ARCHITECTURE.md` | 取 Rust 模組邊界 | 理解分層與依賴 | 27 個 workspace crate；core→drivers→sql→types 單向；vendor 8 個上游 crate patch |
| 讀 `crates/README.md` / `agents/README` | 取 crate 職責 | 理解各層 | dbx-core 編排；dbx-sql 方言/風險；dbx-drivers 原生+Agent；dbx-ai-provider；dbx-plugin-runtime；dbx-web；dbx-cli；dbx-mcp |
| 讀 `packages/mcp-server/README.md` | 取 MCP 機制 | 理解 AI 整合 | Rust MCP binary + Node launcher；18 個 tool；stdio 預設、可選 Streamable HTTP + bearer；三種執行模式 |
| 讀 `packages/cli/README.md` / `skills/dbx/SKILL.md` | 取 CLI 能力 | 理解 agent 介面 | 穩定 JSON 輸出；`dbx doctor/capabilities/agent setup/query`；預設唯讀；`--allow-writes`/`--allow-dangerous-sql` 雙閘 |
| 讀官方 docs（what-is-dbx、databases、production-safety、ai-assistant） | 補一手設計 | 安全模型/支援範圍 | 七類資料系統、四種 driver runtime、六層寫入安全、AI 五類 provider |
| 查 releases / commits / contributors | 評估活躍度與開發模式 | 事實依據 | 323 個 release，近一週每日多版；100 commits 中 lxk955 35、t8y2 18；contributors 327 頁 |
| 查 t8y2 使用者 / SECURITY.md | 作者與資安 | 背景 | 作者在中國北京、544 followers、58 repos；資安範圍涵蓋憑證、MCP、外掛沙箱 |

**關鍵事實整理**

| 面向 | 內容 |
|---|---|
| 一句定位 | 用 Rust/Tauri 打造的輕量資料庫工作台：單一 ~25MB 應用提供 100+ 資料庫/資料系統的連線、瀏覽、查詢、編輯、傳輸，並內建 AI、MCP Server、CLI 與 Docker/Web |
| 技術堆疊 | Tauri 2 + Vue 3/TS + shadcn-vue + CodeMirror 6；後端 Rust（sqlx/tiberius/redis-rs/mongodb） |
| 驅動架構 | 4 種 runtime：內建原生 Rust、Native Agent sidecar（Go/Rust）、JDBC Agent（Java+JRE+vendor JAR）、通用 JDBC plugin；Oracle 另有 OCI thick driver |
| MCP | 獨立 Rust MCP server，18 tools；npm launcher；本地/Web/Docker 三模式；read_only / safe_write / high_risk_write 三模式 + 連線 allowlist |
| CLI | 獨立 native binary；`--json` 穩定輸出；預設唯讀；內建 DBX Agent Skill 供 shell agent 使用 |
| 安全模型 | 六層：DB 權限、連線唯讀、生產保護、危險 SQL 確認、AI 執行規則、全域 MCP policy；任何高層工具皆不可放寬底層 |
| 支援廣度 | 關聯式、分析倉儲、文件/KV/搜尋、圖/向量、時序、訊息佇列、註冊中心七類 |
| 外掛 | 簽章驗證 + 沙箱 sidecar；Go/TS SDK；`t8y2/dbx-store` marketplace |
| 活躍度 | 323 release、開發極頻繁、327 頁 contributors、1,019 open issues |

**發現的出入**（供報告標記）

| 項目 | PR body 說法 | 一手實況 | 判定 |
|---|---|---|---|
| 描述語言 | 僅英文描述 | API `description` 中英雙語 | 一致，PR 只節錄英文段 |
| 「25MB」 | 25 MB | README 自稱 ~25MB、無 bundled Chromium | 一致（行銷數字，未逐平台驗證） |
| 支援數 | 100+ | 官方明言「connect ≠ 全功能」，進階功能受 capability 限制 | 需在報告標明「連線數≠功能數」 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Metadata 完整性 | stars/license/語言/時序/topics/issues | 完整 |
| 文件覆蓋率 | README + tree + ARCHITECTURE + 3 子 README + 4 docs + SKILL | 完整，足以支撐 §1–§3 |
| 機制理解 | 驅動 runtime、MCP 三模式、CLI 閘門、六層安全 | 清晰 |
| 背景脈絡 | 通用 DB client 史、替代方案留 C2 | 未做，C2 補 |
| 資訊缺口 | 影片逐字稿不可得；25MB 與「100+」為自稱 | 已標記，報告需保留保留語氣 |
| log 格式 | 4 section + 6000 字上限 | 符合 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件深度 | 只讀 README／讀架構+子專案+docs | README + ARCHITECTURE + MCP/CLI/SKILL + 4 篇 docs | 機制分散在子專案，單讀 README 不足支撐 §3 |
| 是否逐 crate 精讀原始碼 | 是／否 | 否 | C1 為 metadata 與主要文件盤點；原始碼細節對 §1–§3 非必要 |
| 支援數宣稱處理 | 照抄「100+」／標明 capability 限制 | 標明「connect ≠ 全功能」 | 官方 docs 明示，避免誤導 |
| 影片不可得 | 硬猜／略過 | 略過觀點，只採 repo 事實 | 逐字稿不可得，不強求 |
| 活躍度指標 | 只看 stars／補 releases+commits | 補 323 release、commit 作者分佈 | 24k stars 需佐證是否真活躍 |

## 交接給 C2

- 補通用背景：資料庫客戶端演化（DBeaver/Navicat/JetBrains DataGrip/TablePlus）、JDBC 與原生驅動取捨、Tauri vs Electron 體積差異。
- 補替代方案 DA 表：DBeaver、DataGrip、Navicat、TablePlus、Beekeeper 等，並納入 MyBrain 既有判定準則視角。
- 已可用來源：`crates/ARCHITECTURE.md`、MCP/CLI README、production-safety、what-is-dbx（已抓）。
