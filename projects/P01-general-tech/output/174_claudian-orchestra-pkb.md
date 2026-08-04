# Claudian Orchestra PKB vs MyBrain 異同分析

> 調研標的：Ozaki 的 Claudian Orchestra Template（Obsidian Vault + Codex CLI + Hermes Agent）
> 比較對象：使用者 FATESAIKOU 的 MyBrain（OKF 格式第二大腦）
> 調研日期：2026-08-04

---

## 1. 這個技術解決什麼問題？

**Ozaki 的 PKB 解決的問題**：個人知識庫（PKB）的「土台づくり」——從零開始建立 Obsidian Vault + AI Agent 協作體系時，最困難的目錄規約、代理契約、技能定義、外部接續認證等基礎建設，需要大量試錯。Ozaki 提供一個模板，讓使用者從「0.5」的進度開始，跳過最痛苦的初始階段。

**具體問題**：
- 人類與 AI 如何共享同一份記憶（markdown vault）
- 外部資訊（Slack/Calendar/Gmail/GitHub）如何自動流入個人知識庫
- 如何確保 capture（捕捉）與 curate（整理）分離，避免 raw data 淹沒 curated knowledge
- 多代理（core agent + Hermes）如何分工而不打架（single-writer 原則）

**MyBrain 解決的問題**：個人知識的結構化儲存與可程式化查照——確保「我是誰／我在哪裡／我要去哪」三問能被 AI agent 可靠地回答。MyBrain 不是一個 vault 模板，而是一個**知識庫的格式標準（OKF）+ 查照/更新工具鏈**。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **PKB 建構本身很困難**：Ozaki 自述「ゼロから山ほど作って山ほど壊しました」，花費大量時間在摸索目錄規約、代理邊界、技能定義上
- **外部接續認證是最大障壁**：Slack/Google/GitHub 等服務的 OAuth 流程、token 管理、scope 設定，是 PKB 使用者最常卡住的地方
- **capture 過多會淹沒 Inbox**：自動化 capture 太強時，raw data 累積速度超過整理速度，Inbox 會爆炸
- **single-writer 規律難以維持**：多 PC 同步時容易發生衝突

### 通用技術背景

- **LLM 作為知識庫的讀寫者**：傳統 PKM（如 Zettelkasten）只考慮人類讀寫，LLM 時代需要讓 AI agent 也能讀寫同一份 markdown
- **OKF（Open Knowledge Format）**：Google Cloud 提出的知識格式標準，強調 YAML frontmatter + markdown body + 目錄結構化
- **Karpathy 的 "LLM wiki"**：概念上將 LLM 視為 wiki 的讀寫者，而非僅是問答介面
- **Agent 協作模式**：多 agent 系統需要明確的邊界契約（誰持有認證、誰可以寫哪裡、誰負責 capture vs curate）

---

## 3. 這個技術是如何解決該問題的？

### 3.1 Ozaki 的 PKB（Claudian Orchestra Template）

**核心架構**：Obsidian Vault 作為「人與 AI 的共享記憶」，由 2 個 agent 操作。

```
External Source (Slack/Calendar/Gmail/GitHub/...)
   │ ① capture（Hermes 專任）
   ▼
Inbox/{YYYY-MM-DD}/{source}/{file}.md    ← raw capture，日付ファースト
   │ ② aggregate（Core Agent = Codex CLI）
   ▼
Daily/{YYYY-MM-DD}.md                     ← 唯一の監査点（人間が読む）
   │ ③ distill（Core Agent + 人類承認）
   ▼
Wiki/ → Evergreen notes                  ← Main DB
```

**關鍵機制**：

| 機制 | 說明 |
|---|---|
| **capture/curate 分離** | Hermes 只負責 capture（寫入 Inbox/），不做任何判斷、摘要、路由。Core agent 負責 aggregate 與 distill |
| **Daily 為唯一監査點** | 所有 agent 動作（capture/aggregate/distill/check）都在 Daily 留下痕跡。人類讀 Daily 即可掌握全局 |
| **single-writer** | 同一檔案同一時間只有一個寫手。Hermes 在 Daily 集約前可 idempotent 重跑，集約後所有權移交 Core agent |
| **on-demand 既定** | 非 cron 驅動。人類從 Daily 的 `## 🤖 ジョブリスト` 指示「これやって」才執行 |
| **Hermes 一元持有外部認證** | Core agent 不持有任何 OAuth/PAT。外部查詢透過 `hermes chat -q` pull，capture 透過 Hermes skill push |
| **AGENTS.md 為核心契約** | 所有規則（目錄、frontmatter、tag、agent 邊界、語言）寫在 AGENTS.md + .codex/rules/ 中，Codex CLI 自動讀取 |

**目錄結構**：

```
.codex/          → control plane（rules/ skills/ connections.yaml config.toml）
.hermes/         → Hermes 設定（config.yaml SOUL.md skills/vault-capture/）
Inbox/           → raw capture（日付ファースト）
Daily/           → 日次ハブ
Wiki/            → Main DB（evergreen notes）
Maps/            → MOC（Home/Code-Map/People-Map）
Persona/         → 使用者プロフィール（identity の単一の正）
Templates/       → ノートテンプレート
Archive/         → 非活性退避
Meta/            → vault 自身について（connections/ assets/）
```

**支援的外部接續**（13 種）：GitHub / Google Calendar / Tasks / Gmail / Google Drive / Slack / Discord / RSS / Clippings / Meeting / Zotero / Notion

### 3.2 使用者的 MyBrain

**核心架構**：OKF v0.2 格式的 markdown 知識庫，搭配讀寫兩側的工具鏈。

```
┌─────────────────────────────────────────────────┐
│                  MyBrain (GitHub Repo)            │
│                                                   │
│  技術/    抽象理解/    日常/    日誌/              │
│  (主題軸1) (主題軸2)   (主題軸3) (時間軸)         │
│                                                   │
│  .okf/ → validate.py / reindex.py / skills/      │
│          commands/                                │
└─────────────────────────────────────────────────┘
         ↕ 讀取側（search-from-mybrain skill）      ↕ 寫入側（sync-to-mybrain command）
         ↕                                          ↕
    AI Agent (Claude Code / opencode)          人類 + AI
```

**關鍵機制**：

| 機制 | 說明 |
|---|---|
| **OKF v0.2 格式** | YAML frontmatter（type/status/tags/created/updated/actor/trust）+ markdown body |
| **三條主題軸 + 時間軸** | 技術/（評估、靈感、動手做）、抽象理解/（想法、本質洞察、價值觀、人生方向）、日常/（溝通、金融、生活、職涯）、日誌/（扁平日期檔） |
| **骨幹標記** | 標 `tags: ["骨幹"]` 的檔案直接回答「我是誰／我在哪裡／我要去哪」三問 |
| **信任層級** | unverified / machine-confirmed / human-reviewed |
| **讀取側（search-from-mybrain）** | 5 步驟：更新鏡像 → 讀骨幹 → 掃目錄 → grep 補詞 → 讀全文 → 回報（含信任層級與時間座標） |
| **寫入側（sync-to-mybrain）** | 7 步驟：判斷價值 → clone repo → 讀規則 → 寫檔 → reindex + validate → commit/push/PR → 清理 |
| **驗證器（validate.py）** | 檢查 frontmatter、連結、圖片、檔名 4 類問題 |
| **重生器（reindex.py）** | 自動更新各層 index.md + 日誌摘要 |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 對照表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Ozaki Claudian Orchestra** | Obsidian Vault + Codex CLI + Hermes Agent 的模板化 PKB，capture→Daily→distill 三階段 pipeline | ChatGPT Plus 以上訂閱、Node.js/npm 環境、Hermes Agent 安裝、各外部服務的 OAuth 設定 | 外部接續認證管理複雜、Inbox 容易 overflow、single-writer 需嚴格遵守、Hermes gateway 需常駐 | 15 分鐘可啟動最小 loop（Level 0），逐步加入外部接續後可實現自動化 daily briefing + EOD distill |
| **MyBrain (OKF)** | 自訂 OKF v0.2 格式 + 讀寫工具鏈（search-from-mybrain / sync-to-mybrain）+ validate/reindex 自動化 | GitHub 帳號、AI agent（Claude Code / opencode）安裝對應 skill/command | 格式較固定（OKF 曾被使用者 Reject 但實際採用）、寫入需經 PR 流程、無內建 capture 機制 | AI agent 可可靠回答「我是誰／我在哪裡／我要去哪」，知識庫結構化程度高 |
| **Andrej Karpathy "LLM wiki"** | 將 LLM 視為 wiki 的讀寫者，用自然語言 prompt 作為 query interface | LLM API 存取、結構化 markdown 知識庫 | 無標準格式、無驗證工具、依賴 LLM 的 prompt engineering | 概念上最簡潔，但缺乏工具鏈支援 |
| **Zettelkasten 傳統 PKM** | 卡片盒筆記法，原子化筆記 + 連結網路 | 人類手動維護、Obsidian/Roam/Logseq 等工具 | 不考慮 AI agent 讀寫、無自動 capture 機制、依賴人類手動整理 | 適合人類思考，但無法與 AI agent 協作 |
| **Notion AI Q&A** | Notion 資料庫 + AI 問答，直接在 Notion 內查詢知識庫 | Notion 訂閱、資料需在 Notion 內 | vendor lock-in、非純文字格式、無法與 CLI agent 整合 | 使用門檻最低，但靈活性最低 |

### 4.2 切入點差異

| 維度 | Ozaki | MyBrain | Karpathy | Zettelkasten | Notion AI |
|---|---|---|---|---|---|
| **AI 讀寫** | 原生支援（Codex CLI 直接讀寫 vault） | 透過 skill/command 橋接 | 概念支援，無工具 | 不支援 | 僅支援 Q&A，不支援寫入 |
| **capture 自動化** | Hermes 專任 capture | 無內建 capture | 無 | 無 | 無 |
| **格式標準** | 自訂 frontmatter schema（OKF 啟發） | OKF v0.2 | 無 | 無 | Notion 專有格式 |
| **驗證工具** | 無（依賴 agent 自律） | validate.py + reindex.py | 無 | 無 | 無 |
| **外部接續** | 13 種（Hermes 一元持有） | 無（純知識庫） | 無 | 無 | 有限（內建整合） |
| **查照機制** | Daily 監査點（人類閱讀） | search-from-mybrain skill（AI 查詢） | LLM prompt | 人類瀏覽連結網路 | Notion 搜尋 + AI Q&A |
| **更新機制** | capture→aggregate→distill pipeline | sync-to-mybrain command（PR 流程） | 無 | 人類手動 | 人類手動 |
| **vendor lock-in** | 低（純 markdown） | 低（純 markdown + GitHub） | 低 | 低 | 高 |

### 4.3 關鍵差異總結

| 面向 | Ozaki | MyBrain |
|---|---|---|
| **核心定位** | PKB 模板（土台） | 知識庫格式 + 工具鏈 |
| **AI 接續方式** | Codex CLI 直接讀寫 vault 檔案 | skill/command 橋接（search-from-mybrain / sync-to-mybrain） |
| **capture 機制** | Hermes 專任，13 種外部接續 | 無內建 capture |
| **查照方式** | 人類讀 Daily 監査點 | AI 執行 search-from-mybrain 5 步驟 |
| **更新方式** | capture→aggregate→distill pipeline | sync-to-mybrain → reindex → validate → PR |
| **格式** | 自訂 frontmatter schema | OKF v0.2 |
| **驗證** | 無（依賴 agent 自律） | validate.py + reindex.py |
| **內容分類** | Inbox/Daily/Wiki/Maps/Persona | 技術/抽象理解/日常/日誌 |
| **信任標記** | 無 | unverified / machine-confirmed / human-reviewed |
| **骨幹機制** | 無 | tags: ["骨幹"] 標記三問答案 |
| **外部接續認證** | Hermes 一元持有 | 無（純知識庫） |
| **同步方式** | Google Drive（多 PC） | GitHub（git push/PR） |
| **AI web chat 接續** | 透過 Obsidian vault 檔案間接接續（AI 讀寫同一份檔案） | 無直接接續（MyBrain 是獨立知識庫，非 chat 介面） |

---

## 5. User Q&A

（本輪無提問，此節暫空）
