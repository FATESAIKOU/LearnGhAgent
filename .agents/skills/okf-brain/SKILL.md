---
name: okf-brain
description: Open Knowledge Format (OKF v0.2) 與 FATESAIKOU/MyBrain 第二大腦的撰寫維護規範。**此 skill 應該被觸發**：當你在任何含有 `okf_version` 根 index.md 的 bundle（如 MyBrain）中工作時；當使用者要求「整理成 OKF」「加 frontmatter」「整理筆記」「更新第二大腦」「驗證 bundle」時；當你要新增或修改任何帶 YAML frontmatter 的知識類 markdown 檔時。提供 frontmatter 欄位規則、type 分類、index.md/log.md 格式、以及驗證方式。
---

# OKF — Open Knowledge Format v0.2

Google Cloud 的知識庫格式規範。**核心概念：一個資料夾 + 一堆 .md + 每個檔案開頭的 YAML frontmatter。** 沒有 runtime、沒有 SDK。

規格全文：https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf

## 使用者的 bundle

**https://github.com/FATESAIKOU/MyBrain**（private，用 `gh repo clone` 取得）。

它同時是 Obsidian vault，所以：

- **中文檔名與資料夾名一律保留**，不要「順手」改成英文
- **不要動 `.canvas` 和圖片**
- Obsidian wikilink `[[檔名]]` 靠檔名解析，**改檔名會打斷連結**

### ⚠️ 規則不在這個檔案裡

**bundle 的使用規則（目錄結構、檔名、日誌與主題檔的連結方式、圖片擺放、外部產出參照、信任狀態）全文寫在根目錄 `index.md` 的「使用規則」一節。**

本檔**只講 OKF 格式本身**，刻意不重複那些規則——規則只留一份才不會 drift。

（規則八另外定了三個給讀取側用的約定：`骨幹` tag、`⚠️ **不要…**`、`🔄`。規則三定了日誌段落標記 `## [領域-次狀態] 標題`，規則九定了唯一一份覆寫式檔案 `專案/下一步清單.md`。頂層有五個——技術／抽象理解／日常／日誌／專案，後兩者扁平。寫新檔或改既有檔時都會用到，一樣去 `index.md` 讀。）

**動手改任何東西之前先讀 `index.md`**，不要憑本檔或記憶推測 bundle 規則：

```bash
cat index.md          # 「使用規則」一節
```

## Frontmatter

`type` 是**唯一必填欄位**。其餘全部選填。

```yaml
---
type: Note                    # 必填
title: 標題                    # 建議
description: 一句話摘要         # 建議
tags: [tag1, tag2]            # 建議
status: draft                 # draft | stable | deprecated（預設 stable）
generated:
  by: claude-code/opus-5      # actor
  at: 2026-07-25T09:30:00Z    # ISO 8601 UTC
verified:                     # 沒有這個欄位 = 未經審核
  - by: "human:fatesaikou"
    at: 2026-07-25T10:00:00Z
sources:
  - id: stable-key
    title: 來源說明
    author: claude-code/opus-5
    last_modified: 2026-07-25
stale_after: 2027-01-01       # 絕對日期，不是 TTL
---
```

### Actor 慣例

| 對象 | 寫法 |
|---|---|
| Agent / 工具 | `claude-code/opus-5`、`opencode/glm-5.2` |
| 人 | `human:fatesaikou` |
| 自動流程 | `process:nightly-sync` |

### 信任層級（由 `verified` 推導，不要自己存分數）

| frontmatter 狀態 | 層級 |
|---|---|
| 無 `verified` | **unverified** ← AI 產出一律停在這 |
| `verified` 只有非 `human:` actor | machine-confirmed |
| `verified` 含 `human:` actor | human-reviewed |

**鐵則：AI 寫的內容一律 `status: draft` 且不得填 `verified`。** 只有使用者本人 review 後才能升級。

## type 分類

`type` 表達**形式**，與目錄（主題）正交。這個 bundle 目前在用的：

| `type` | 用於 | 常見所在目錄 |
|---|---|---|
| `Journal` | 每日記錄 | `日誌/` |
| `Tech Review` | 技術評估 | `技術/技術評估/` |
| `Project Log` | 動手做的專案記錄 | `技術/動手做/`、`技術/追加功能/` |
| `Note` | 沉澱後可重用的理解 | `抽象理解/`、`專案/` |
| `Prompt` | 可重用的 prompt 資產 | `技術/` |
| `Idea` | 未驗證的想法 | `技術/靈感/`、`抽象理解/想法/` |
| `Life Event` | 生活事件與人生決策 | `日常/` |

> ⚠️ **不要再用 `(Judge)`／`(MVP)`／`(Feature)`／`(LIFE)` 這類舊記號。** 日誌標題已全面改為 `## [領域-次狀態] 標題`（規則三），舊寫法會被驗證器擋下。

`type` 不需向任何人註冊，但**同一個 bundle 內要保持一致**。消費端必須容忍未知 type。

**該放哪個目錄、什麼時候該合併、圖片放哪——這些是 bundle 規則，看 `index.md`。**

## 保留檔名

`index.md` 和 `log.md` 是保留檔名，**不是**概念文件，**不需要也不可以有一般 frontmatter**。

根目錄的 `CONTEXT.md` 是**後設文件**（bundle 的術語表），同樣不帶 OKF frontmatter、不受連結規則約束。`docs/`、`openspec/`、`.claude/`、`.opencode/` 整個目錄都不在驗證範圍內——它們是文件與 agent 工具鏈，不是知識。

### index.md

```markdown
# 日誌

* [2026-07-25](./2026-07-25.md) - OKF 導入與第二大腦架構設計
* [2026-07-14](./2026-07-14.md) - 一句話描述
```

只有**根目錄**的 `index.md` 可以有 frontmatter，且**只能有 `okf_version`**：

```yaml
---
okf_version: "0.2"
---
```

### log.md

最新的在最上面，日期用 ISO 8601：

```markdown
# 更新記錄

## 2026-07-25
* **Creation**: [標題](/知識/檔名.md) — 一句話說明。
* **Update**: [2026-07-25 日誌](/日誌/2026-07-25.md) — 追加內容。
```

`**Creation**` / `**Update**` / `**Deprecation**` 是慣例，非強制。

## 連結

```markdown
[文字](/抽象理解/思考習慣.md)   ← bundle 根相對，推薦
[文字](./其他.md)              ← 相對路徑
```

連結一律是**無向關係**，關係類型靠上下文文字表達，不靠連結本身。消費端必須容忍壞連結。

⚠️ **檔名含空格時必須把空格編碼成 `%20`**（如 `./20260322%20GStack%20學習.md`），否則 markdown link 會在空格處截斷。中文字元不需編碼，GitHub 與 Obsidian 都能正確解析。**搬動任何檔案後，務必全 repo 掃一次指向舊路徑的連結。**

## Conformance（三條，就這樣）

1. 每個非保留 `.md` 有可解析的 YAML frontmatter
2. 每個 frontmatter 有非空 `type`
3. `index.md` / `log.md` 遵守上面的結構

消費端義務：**不得**因缺少選填欄位、未知 `type`、額外欄位、壞連結、缺 `index.md` 而拒絕文件。

## 驗證

**標準操作腳本都放在 bundle 的 `.okf/` 裡，不在這個 skill 裡。** 改完任何檔案就依序跑，不要手工做它們的事：

```bash
python3 .okf/reindex.py .      # 重生各層 index.md、同步日誌摘要
python3 .okf/validate.py .     # 驗證標頭、連結鏈、圖片配置
```

`index.md` 的條目**不要手寫**——`reindex.py` 會讀各檔 frontmatter 的 `title` / `description` 產生，並保留 `index.md` 裡手寫的「使用規則」區塊。`log.md` 則是手寫。

它會檢查三件事：標頭合法、連結鏈完整（日誌 → 主題檔 → GitHub URL，沒有孤兒）、圖片放在與報告同名的資料夾裡。有問題會指出檔案與修法。

外部 repo 的覆蓋檢查需要那些 repo 在本機，路徑用 `--external NAME=PATH` 給（宣告在 bundle 的 `.okf-external.yaml`，沒給路徑的 repo 會跳過）。GitHub Actions 每次 PR 都會自動跑完整版，所以本機跑不帶 `--external` 也夠。

## 寫作原則

- 寫給**未來的使用者本人**看，不是寫對話紀錄。禁止「我們剛才討論了…」「使用者問我…」
- **一個檔案一個概念**
- 中文為主，技術術語保留原文
- 沒把握的事實 → 不寫，或明確寫成「推測：…」
- **絕對不寫入密鑰、token、密碼、他人個資**
