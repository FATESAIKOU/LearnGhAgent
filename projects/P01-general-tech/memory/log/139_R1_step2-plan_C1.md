# 139_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1：取得 Buzz (block/buzz) 的 repo metadata 與主要文件，作為後續分析基礎。R1 首次調研，無前輪追問。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view block/buzz --json` | 取得 repo metadata | 獲得名稱、描述、語言、星數、授權等 | 成功。Rust 為主（12.9MB），TypeScript 9.5MB、Dart 1.7MB；11,235 stars、877 forks；Apache 2.0；Block, Inc. 開發；2026-03-06 建立 |
| `gh api repos/block/buzz/readme` | 取得 README 下載 URL | 定位 README.md | 成功：`raw.githubusercontent.com/block/buzz/main/README.md` |
| `gh api repos/block/buzz/contents` | 列出根目錄結構 | 了解專案組織 | 成功。Rust Cargo workspace（`crates/`）、Tauri desktop（`desktop/`）、Flutter mobile（`mobile/`）、web client（`web/`）、admin-web、docs/、deploy/、migrations/、schema/ |
| 讀取 README.md | 理解專案概述 | 取得 quick start、架構圖、功能表 | 成功。核心概念：self-hostable workspace，Nostr relay 為單一真相源，人類與 Agent 共享同一 rooms |
| 讀取 ARCHITECTURE.md（45KB） | 取得完整系統設計 | 理解 event pipeline、subscription、crate 依賴、安全模型 | 成功。81 種 event kind、三層 fan-out、12-step event pipeline、hash-chain audit、SSRF 保護 |
| 讀取 VISION.md（12KB） | 取得平台願景 | 理解 7 個 surface、community 模型、scale target | 成功。Stream/Forum/DM/Agent/Workflow/Search/Home 七個 surface；10K humans + 50K agents target |
| 讀取 VISION_AGENT.md（4.5KB） | 取得 Agent 架構願景 | 理解 buzz-agent + buzz-dev-mcp 設計 | 成功。ACP 協議、MCP tools、session isolation、最小化設計原則 |
| 讀取 VISION_PROJECTS.md（13KB） | 取得 Forge 願景 | 理解 git hosting、branch-as-channel、merge flow | 成功。NIP-34 標準、branch channel 自動建立、approval gate、web-of-trust |
| 讀取 VISION_SOVEREIGN.md（13KB） | 取得 sovereign relay 願景 | 理解 one-domain = one workspace 概念 | 成功。myproject.com 即 workspace，content negotiation 同時 serve browser 與 git |
| 讀取 VISION_MESH.md（4.6KB） | 取得 shared compute 願景 | 理解 community-gated GPU pooling | 成功。成員閒置 GPU 組成 pool，agent 透過 local OpenAI-compatible endpoint 使用 |
| 讀取 CONTRIBUTING.md（15KB） | 取得開發流程 | 理解 setup、test、PR 規範 | 成功。Rust 1.88+、Node 24+、pnpm 10+、Hermit toolchain pinning |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Repo metadata 完整性 | 是否取得名稱、語言、stars、license、建立時間 | 完整取得 |
| 關鍵文件覆蓋率 | README + ARCHITECTURE + VISION 系列 + CONTRIBUTING | 已讀取 10 份文件 |
| 技術棧理解 | Rust monorepo、Nostr protocol、Postgres/Redis/MinIO | 已確認 |
| 架構核心概念 | Relay 為單一真相源、event kind 為唯一 dispatch | 已確認 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 讀取哪些 VISION 文件 | 1. 只讀 VISION.md 2. 讀全部 5 份 VISION_* | 讀全部 5 份 | 每份聚焦不同面向（Agent/Projects/Sovereign/Mesh/Moderation），對完整理解 Buzz 必要 |
| 是否讀取 AGENTS.md（26KB） | 1. 讀取 2. 跳過 | 跳過 | AGENTS.md 主要為 agent 開發者指引，非核心架構文件；C1 已取得足夠架構資訊 |
| 是否讀取 TESTING.md | 1. 讀取 2. 跳過 | 跳過 | 測試細節對理解 Buzz 核心機制非必要，C2 如有需要可補讀 |
| 是否讀取 docs/ 子目錄 | 1. 全部讀取 2. 僅記錄存在 | 僅記錄存在 | docs/ 含 multi-tenant spec、NIP proposals 等進階文件，C2 分析時按需讀取 |
