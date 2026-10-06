# 280_R2_step2-plan_C1.md

## 狀況理解

R2 Step 2 首個 sub-step。R1 已建立 Univer 的定位／架構／授權全貌，C1 不重做 R1，而是針對本輪三則質問補一手事實：

| 提問 | C1 需取得的一手事實 |
|---|---|
| Q1 到底解決什麼問題、是否＝「自有網頁搞出 Office365 編輯頁面」 | README「What is Univer?」+ 使用情境清單（是否 hosted、是否 iframe、容器掛載模式） |
| Q2 是否踩微軟紅線／有官方背景／團隊多大／年紀多長 | 組織、公司實體、成立年、Luckysheet 血緣、contributor 規模、商業模式（Pro 同步機制） |
| Q3 AI-first 下是否沒用、是否更該用 OfficeCLI | Univer 自身 agent 路徑（AI SDK／univer-cli／Worktree）與 OfficeCLI 定位對照 |

調研標的仍為 `dream-num/univer`；R1 已證第二大腦無 Univer 同級判定（僅 OfficeCLI＝試用、human/stable）。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 實際的結果 |
|---|---|---|
| `gh api repos/dream-num/univer` | 取最新 metadata | **18,993★／1,618 forks**；Apache-2.0；TypeScript；created 2022-09-29；pushed 2026-09-24；desc「The Office Harness for AI Agents — Spreadsheets, Docs, Slides, Canvas, Relational Tables and PDF in one runtime」；topic 含 docx/xlsx/pptx/pdf/collaboration/sdk |
| `gh api orgs/dream-num` | Q2 組織身世 | **DreamNum，GitHub org 建於 2020-02-25**；blog univer.ai；email developer@univer.ai；90 public repos；435 followers |
| 官網 footer＋docs footer | 確認公司實體 | 網站「© 2026 **DreamNum Inc.**」；docs「© 2026 **DreamNum Co., Ltd.**」→ 公司化營運，非個人 |
| `gh api orgs/dream-num/members` | 團隊規模 | 8 位公開成員（DR-Univer, hexf00, jikkai, OTime-Coder, siam-ese, VicKun4937, wpxp123456, yangluoshen） |
| contributors API | 貢獻者規模 | **實名 68 人／含匿名 78 人**；top：jikkai 1177、DR-Univer 623、wzhudev 574、Dushusir 547、wpxp123456 534 commits |
| commits API（首末） | 專案年齡 | repo 首 commit **2022-12-30**；總 commit 頁數 5,808（per_page=1）→ 高活躍 |
| releases API | 版本節奏 | v1.0.0/1/2 皆 **2026-09-24 同日**；v0.25.2 為 2026-09-17；v0.21～v0.25 密集（每月數版） |
| `gh api repos/dream-num/Luckysheet` | 血緣 | **archived；created 2020-05-15；16,642★；MIT**；desc「Luckysheet upgraded to Univer」 |
| 列 org 全部 90 repos | 產品線規模 | univer-workspace **1,232★**、dsh-univer-office **405★**、Luckyexcel 476★（archived）、LuckysheetServer 459★、obsidian-univer 168★、skills 71★、univer-mcp 38★、univer-cli 11★ |
| 讀 univer README（What is Univer?／AI Agents／OSS-Pro） | Q1、Q3 一手文字 | 「Without forcing you into a hosted app or a fixed UI」「Embed spreadsheet/document editing into SaaS／internal tool／BI／AI application」「Not a file viewer only — a framework for building your own productivity surface」 |
| 讀 univer-cli README（獨立 repo） | Q3 agent 路徑 | **Univer 家族本身有 Apache-2.0 的 agent CLI**：建立／編輯／檢查／交付 Sheet/Doc/Slide/Base/Board；Worktree 隔離草稿＋Viewer 人審 Merge/Discard；import/export xlsx/docx/pptx |
| 讀 docs.univer.ai/ai 與 /ai/worktree | Q3 AI-first 機制 | AI SDK＝TypeScript SDK＋Node CLI 入口；流程 commit→markReady→Web 人審→Merge/Reopen；**Worktree Service/Client 屬 Collaboration SDK（Pro）** |
| 讀 univer.ai/ecosystem | Q2 官方合作 | 官網列 OpenCode／Claude Code／OpenClaw／Hermes／Codex／WorkBuddy／Kimi Work 為「Built for any agent」；**dsh-univer-office 為 DeepSeek Harness 官方 Office 插件** |
| `gh api repos/dream-num/dsh-univer-office` | 官方合作佐證 | Apache-2.0；405★；desc「the Univer office plugin for DeepSeek Harness (DSH)」 |
| 讀 DREAMNUM.md | 責任邊界 | 明示本 repo 不擁有 Pro 的協作／import-export／server 能力；含 `dispatch-sync-univer-pro.yml` 同步至獨立 Pro repo |
| npm registry @univerjs/core | 授權與採用 | license Apache-2.0；latest 1.0.2；2023-12-05 上架；univer-cli npm latest 0.5.1（2026-05-07 上架） |
| `gh search repos officecli` | Q3 對照 | 主體為 **iOfficeAI/OfficeCLI：31,265★、Apache-2.0**；另有 officecli/officecli（MIT, 105★）等同名混淆項 |
| HTTP 檢查 | 官網節點 | `univer.ai/pricing` **404**、`docs.univer.ai/guides/pro` **404**（R1 已記）；office.univer.ai＝200 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| **Q2 官方背景** | org／公司實體／合作 | **無微軟官方背景，但非個人專案**：DreamNum（公司 Inc./Co., Ltd.）2020 成立；與 DeepSeek Harness 等為官方合作；核心 Apache-2.0 |
| **Q2 團隊規模** | members＋contributors | 公開成員 8；實名貢獻者 68；非「個人冒出」 |
| **Q2 專案年齡** | 首 commit／Luckysheet | Univer 首 commit 2022-12-30；前身 Luckysheet **2020-05-15**（官網「10+ yrs」自 Luckysheet 起算）；Luckysheet 2025-08 封存併入 |
| **Q2 踩紅線** | 事實面 | 無複製微軟源碼跡象；對標公開標準 OOXML（ECMA-376）與自建引擎；屬獨立實作（法律面另見 C2 若需） |
| **Q1 定位** | README 一手句 | **是「在自有網頁內嵌編輯器」之意，但非 hosted、非 iframe**：開發者給容器 div，SDK 掛載；六工具一 runtime |
| **Q3 agent 路徑** | univer-cli／AI SDK | Univer 家族**自身即提供 OfficeCLI 式 agent CLI**（操作成品檔＋Worktree 審查）；完整 AI SDK 與 Worktree 依賴 Pro／Collaboration |
| **商業模式** | DREAMNUM.md／Pro 同步 | OSS 核心 Apache-2.0；Pro 為獨立商業 repo；CLI 內含 90 天輪替 runtime 憑證（非 OSS 授權範圍） |
| **未取得** | 定價頁 | Pro 定價（pricing／guides/pro 皆 404） |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否重做 R1 | 重跑標準調研／只補 Q2/Q3 缺口 | 只補缺口 | R1 已有定位／架構／授權；重做浪費且違「非重做 R1」指令 |
| Q2 身世來源 | 網站行銷詞／GitHub API 一手 | GitHub API＋公司實體標示 | 「官方背景／團隊／年齡」為事實命題，須客觀可查來源；行銷詞不足採信 |
| 微軟紅線判定 | 直接下定論／列事實、法源留 C2 | 先列事實，法源（OOXML 標準屬性）標為 C2 | 紅線涉及法律分析，C1 只取事實，避免臆測 |
| Q3 OfficeCLI 對照 | 只比 R1 既有表／查新資料 | 查 iOfficeAI/OfficeCLI 現況＋Univer 自家 CLI | Q3 前提是「更該用 OfficeCLI」，須確認其主體與 Univer 重疊範圍 |
| 同名混淆 | 忽略／標明 | 標明同名 repo | `officecli/officecli`(MIT) 與 `iOfficeAI/OfficeCLI`(Apache) 不同；避免 Q3 張冠李戴 |
| 官網數字 | 直接引用「30k+ stars」 | 拆為 Univer 18,993＋Luckysheet 16,642 | 官網為家族加總；如實拆分可避免誤導 |
