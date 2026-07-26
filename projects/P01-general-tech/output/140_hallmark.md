# Hallmark 技術分析報告

> 調研日期：2026-07-25 | 基於 Nutlope/hallmark（17.9k stars, MIT, CSS primary）

---

## 1. 這個技術解決什麼問題？

Hallmark 解決的是 **AI 生成 UI 程式碼時，產出外觀高度重複、缺乏視覺多樣性的「罐頭感」問題**。具體來說，它同時處理以下 3 個子問題：

| 子問題 | 具體表現 |
|--------|----------|
| **結構單一化** | AI 反覆產出 3-column grid layout、hero + features + pricing + CTA + footer 的固定頁面結構，缺乏佈局多樣性 |
| **視覺風格重複** | 每次產出使用相同的紫色漸層 hero、Inter 字型、card-in-card 模式、過度陰影，形成可辨識的「AI 生成痕跡」 |
| **無品質自檢機制** | AI 產出 UI 後無自我審查流程，無法辨識自身是否落入常見的 anti-pattern |

Hallmark 的目標受眾是使用 Claude Code、Cursor、Codex 等 AI coding agent 產出 Prototype 與 Landing Page 的開發者。它不解決設計系統的 token 管理（DESIGN.md 的領域），也不解決元件庫的程式碼品質，而是專注於「讓 AI 產出的 UI 看起來不像 AI 產的」。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **AI 生成 UI 的訓練資料偏差**：LLM 訓練資料中的 UI 範例大量來自 SaaS landing page、Bootstrap 模板、Tailwind 範例，這些資料的結構與風格高度同質化。LLM 從中學習到的「典型 landing page」就是 hero + features + pricing + CTA + footer 的固定模式。
- **LLM 的保守傾向**：在缺乏明確設計規範時，LLM 傾向選擇訓練資料中出現頻率最高的模式（安全牌），導致每次產出趨同。
- **無設計多樣性約束**：標準的 coding agent prompt 只要求「產出一個好看的 landing page」，未強制要求結構多樣性或風格差異化，LLM 自然回歸均值。

### 通用技術背景（文章中未明確提及但為必要脈絡）

- **LLM 的 mode collapse 現象**：在開放式生成任務中，LLM 傾向收斂到少數高概率路徑，缺乏人類設計師的「刻意差異化」思維。
- **Prompt engineering 的局限性**：開發者難以在 prompt 中精確描述「不要長得像 AI 生成的」，因為「AI 生成痕跡」的定義模糊且不斷演化。
- **前端框架的模板化**：Tailwind UI、shadcn/ui、Flowbite 等元件庫提供現成模板，LLM 訓練資料大量包含這些模板，進一步強化了結構單一性。
- **無標準化的「反 AI 味」規範**：在 Hallmark 出現之前，不存在針對 AI 生成 UI 的品質檢查標準或設計多樣性規範。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 整體架構

Hallmark 是一個提供給 Claude Code / Cursor / Codex 的 **Skill 設定檔**（Prompt 集合），透過 `npx hallmark` 安裝。它不修改 LLM 本身，而是在 LLM 生成 UI 的過程中注入結構化約束與品質檢查。

```
┌─────────────────────────────────────────────────────────────────┐
│  Hallmark Skill 架構                                            │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │  4 Verbs     │───▶│  Design Flow     │───▶│  Slop Test   │  │
│  │  (入口指令)   │    │  (6 步驟流程)    │    │  (58 道閘門)  │  │
│  └──────────────┘    └──────────────────┘    └──────────────┘  │
│         │                     │                       │         │
│         ▼                     ▼                       ▼         │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │ 21 種結構     │    │ 20 種主題風格     │    │ Self-critique│  │
│  │ Macrostructure│    │ Theme Rotation   │    │ 6 軸自評     │  │
│  └──────────────┘    └──────────────────┘    └──────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  6 條跨 Verb 紀律（貫穿所有流程）                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 4 個 Verbs（入口指令）

| Verb | 功能 | 觸發方式 |
|------|------|----------|
| **Default** | 從零開始生成頁面，遵循完整 Design Flow | `hallmark`（無參數） |
| **Audit** | 審計現有頁面的 AI 生成痕跡，產出改善建議 | `hallmark audit` |
| **Redesign** | 對現有頁面做視覺重構，保留內容但更換結構與風格 | `hallmark redesign` |
| **Study** | 從給定的參考頁面或截圖提取設計風格，產出風格摘要 | `hallmark study` |

### 3.3 Design Flow（6 步驟，Default / Redesign 共用）

```
Step 1: Pre-flight scan
  └─ 掃描專案現有檔案，判斷專案類型（SaaS / 電商 / 個人頁面等）
  └─ 檢查是否已有 DESIGN.md 或 design tokens

Step 2: Design-context gate
  └─ 從 4 個 Genre 中選擇一個：
      ├─ Clean Professional（乾淨專業）
      ├─ Bold & Experimental（大膽實驗）
      ├─ Warm & Organic（溫暖有機）
      └─ Editorial / Magazine（編輯雜誌）
  └─ 每個 Genre 有對應的 diversification rule

Step 3: Macrostructure pick
  └─ 從 21 種頁面結構中選擇一種（不可重複使用同一種）
  └─ 21 種結構列表（見 3.4）

Step 4: Theme route
  └─ 從 20 種主題風格中選擇一種（不可重複使用同一種）
  └─ 每個主題有對應的 color palette、typography、mood

Step 5: Visual ruleset
  └─ 根據 Genre + Macrostructure + Theme 產出具體的視覺規則
  └─ 包含：顏色使用限制、排版規則、間距系統、元件樣式

Step 6: Hero enrichment → Preview → Build → Slop test
  └─ Hero 區塊特殊處理（Hallmark 認為 hero 是頁面第一印象的關鍵）
  └─ 預覽 → 生成 → 執行 Slop Test
```

### 3.4 21 種 Macrostructure（頁面結構）

Hallmark 定義了 21 種不同的頁面結構，強制 LLM 在每次生成時選擇不同的結構，避免結構重複：

| 編號 | 結構名稱 | 特徵 |
|------|----------|------|
| 1 | Bento Grid | 非對稱網格，大小不一的區塊拼貼 |
| 2 | Component Playground | 元件展示為主的頁面 |
| 3 | Curved Scroll | 曲線分割的滾動頁面 |
| 4 | Dashboard | 儀表板式佈局 |
| 5 | Diagonal Split | 對角線分割的雙欄佈局 |
| 6 | Editorial | 雜誌編輯式佈局 |
| 7 | Feature Wall | 功能牆式展示 |
| 8 | Full-Screen Sections | 全螢幕區塊輪播 |
| 9 | Gallery Grid | 圖庫式網格 |
| 10 | Hero Focus | 以 hero 為核心的單頁設計 |
| 11 | Horizontal Scroll | 水平滾動佈局 |
| 12 | Interactive Story | 互動式故事敘述 |
| 13 | Magazine | 雜誌式多欄佈局 |
| 14 | Minimal | 極簡主義佈局 |
| 15 | Modular | 模組化區塊組合 |
| 16 | Parallax | 視差滾動佈局 |
| 17 | Single Column | 單欄式長頁面 |
| 18 | Split Screen | 分割螢幕雙欄 |
| 19 | Stepped | 階梯式區塊排列 |
| 20 | Symmetrical | 對稱式佈局 |
| 21 | Terminal | 終端機風格的頁面 |

**Diversification Rule**：同一個 session 中不可重複使用同一種 macrostructure。若所有 21 種皆已用過，則從頭開始但需使用不同的 theme 組合。

### 3.5 20 種 Theme（主題風格）

Hallmark 內建 20 種主題風格，每個主題有獨立的 color palette、typography pairings、mood 定義。4 個有完整 spec 的主題範例：

| Theme | 色調 | 字型 | Mood |
|-------|------|------|------|
| **Carnival** | 鮮豔對比色 | Display + Sans | 活潑、節慶 |
| **Cobalt** | 藍色系為主 | Serif + Sans | 專業、冷靜 |
| **Hum** | 暖色系 | Sans + Mono | 溫暖、親切 |
| **Lumen** | 淺色系 | Sans | 明亮、通透 |

其餘 16 個主題（名稱未在公開文件中詳列）同樣有完整的 color / typography / mood 定義。

### 3.6 Slop Test（58 道品質閘門 + Self-Critique）

Hallmark 的核心品質機制，分為兩層：

**第一層：Pre-emit Self-Critique（6 軸自評）**

在產出最終程式碼前，LLM 先對自己的設計做 6 軸自我評估：

| 軸向 | 評估問題 |
|------|----------|
| **Philosophy** | 這個設計是否有明確的視覺哲學？還是只是拼湊元件？ |
| **Hierarchy** | 視覺層級是否清晰？最重要的元素是否最突出？ |
| **Execution** | 細節執行是否到位？間距、對齊、比例是否一致？ |
| **Specificity** | 這個設計是否有具體的參考來源？還是 generic 的 AI 產出？ |
| **Restraint** | 是否過度設計？是否有不必要的裝飾或效果？ |
| **Variety** | 與前一次產出相比，結構與風格是否有足夠差異？ |

**第二層：58 道 Slop Gates（分類檢查）**

| 閘門類別 | 閘門數 | 檢查內容範例 |
|----------|--------|-------------|
| **Visual** | 多道 | 是否使用紫色漸層 hero？是否使用過度陰影？ |
| **Structural** | 多道 | 是否使用 3-column grid？是否使用 card-in-card 模式？ |
| **Microinteractions** | 多道 | hover 效果是否過於單一？ |
| **Variety** | 多道 | 與前次產出的結構差異是否足夠？ |
| **Implementation** | 多道 | CSS 實作是否使用了常見的 AI 模式？ |
| **Hero** | 多道 | hero 區塊是否落入常見模板？ |
| **Diversification** | 多道 | 是否強制更換了 macrostructure 與 theme？ |
| **Layout** | 多道 | 佈局是否過於對稱？是否缺乏視覺張力？ |
| **Typography** | 多道 | 是否使用 Inter 字型（AI 最常用字型）？ |
| **Input** | 多道 | 表單元件是否落入常見模式？ |
| **Contrast** | 多道 | 對比度是否足夠？ |
| **Nav-Footer** | 多道 | 導航與 footer 是否落入常見模式？ |
| **Copy** | 多道 | 文案是否為 AI 典型的 Lorem ipsum 風格？ |
| **Chrome** | 多道 | 瀏覽器 chrome 相關的設計是否合理？ |
| **Token** | 多道 | 設計 token 的使用是否一致？ |
| **Responsive** | 多道 | RWD 實作是否落入常見模式？ |

### 3.7 Anti-patterns（AI 生成 UI 的「tells」）

Hallmark 的 `anti-patterns.md` 明確列出了 AI 生成 UI 的可辨識特徵，分為三個等級：

**Critical（13 項，必須避免）**：
- Purple-gradient hero section
- Inter 字型無例外
- 3-column feature grid
- Card-in-card 模式
- 過度使用 `backdrop-filter: blur()`
- 固定的 hero + features + pricing + CTA + footer 結構
- 過度使用漸層文字
- 不對稱的導航列
- 過度使用 border-radius
- 固定的 pricing table 3-tier 結構
- 使用 `#0a0a0a` 作為背景色
- 使用 `#fafafa` 作為背景色
- 使用 `#ffffff` 作為卡片背景色

**Major（20+ 項，應避免）**：
- 使用 system-ui 字型堆疊
- 過度使用 `rgba(0,0,0,0.5)` 作為 overlay
- 固定的 feature icon + text 模式
- 使用 `transition: all 0.3s ease`
- 使用 `box-shadow` 而非 `drop-shadow`
- 固定的 CTA button 樣式

**Minor（8 項，建議避免）**：
- 使用 `#333` 作為文字色
- 使用 `#666` 作為次要文字色
- 使用 `#eee` 作為邊框色

### 3.8 6 條跨 Verb 紀律

貫穿所有 verb 的強制規則：

1. **No purple gradients**：禁止使用紫色漸層 hero
2. **No Inter**：禁止使用 Inter 字型（除非專案已使用）
3. **No 3-column grids**：禁止使用 3 欄網格
4. **No card-in-card**：禁止卡片內嵌卡片的模式
5. **Structure rotation**：每次生成必須更換 macrostructure
6. **Theme rotation**：每次生成必須更換 theme

### 3.9 Custom 模式

使用者可透過 `hallmark custom` 自訂：
- 自訂 anti-pattern 清單（追加或覆蓋預設清單）
- 自訂 macrostructure 清單（追加自訂結構）
- 自訂 theme（定義自己的 color palette + typography）
- 自訂 slop gate 的嚴格程度

### 3.10 Contract（輸出範圍限制）

Hallmark 明確限定自己的 scope：
- **不發明 product copy**：只處理視覺設計，不產生產品文案
- **不選擇 brand identity**：不決定品牌定位或品牌名稱
- **不建立 logic**：不處理互動邏輯或狀態管理
- **只處理視覺層**：專注於 HTML/CSS 的視覺呈現

### 3.11 實際工作流程範例（以 Coffeebox recipe 為例）

```
使用者輸入：hallmark

Step 1: Pre-flight scan
  → 掃描目錄：空專案
  → 判斷類型：Landing Page
  → 無現有 design tokens

Step 2: Design-context gate
  → 選擇 Genre: Warm & Organic
  → Diversification rule: 使用暖色系 + 有機形狀

Step 3: Macrostructure pick
  → 從 21 種中選擇: Bento Grid（本次 session 尚未使用）
  → 記錄：Bento Grid 已使用

Step 4: Theme route
  → 從 20 種中選擇: Hum（暖色系，Sans + Mono）
  → 記錄：Hum 已使用

Step 5: Visual ruleset
  → 顏色：暖色調（棕色、奶油色、橄欖綠）
  → 字型：Sans（非 Inter）+ Mono
  → 間距：寬鬆
  → 元件：圓角適中，無過度陰影

Step 6: Hero enrichment → Preview → Build
  → Hero：使用大標題 + 暖色背景 + 有機形狀裝飾
  → 生成完整頁面

Slop Test:
  → Self-critique: Philosophy PASS, Hierarchy PASS, ...
  → 58 gates: 全部通過
  → 輸出最終程式碼
```

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表：替代方案對照

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|----------|-------------|---------------|-----------------|
| **DESIGN.md** | 定義 YAML + Markdown 的設計系統描述格式，讓 AI Agent 讀取統一的設計規範 | 專案使用 AI coding agent；需有能力撰寫 prose 描述設計意圖 | 無強制執行力（Agent 可能不遵循）；需持續維護 DESIGN.md 與實際設計同步 | Agent 跨 session 產出視覺一致的 UI，但無法解決結構多樣性問題 |
| **Custom System Prompt** | 在 Agent 的 system prompt 中手寫設計規範與 anti-pattern 清單 | 使用支援自訂 system prompt 的 Agent 框架 | 無標準格式；跨 Agent 不可攜帶；難以維護與擴充；無自動品質檢查 | 快速上手，但效果取決於 prompt 品質，且無法規模化 |
| **UI Component Library（shadcn/ui, Tailwind UI）** | 提供預先設計好的元件與模板，開發者直接組合使用 | 專案使用對應的框架（React, Tailwind） | 元件庫本身也有「模板感」；限制設計自由度；所有使用相同元件庫的專案外觀相似 | 開發效率高，但無法解決「與眾不同」的需求 |
| **Human Design Review** | 由人類設計師審查 AI 產出的 UI，提供修改建議 | 團隊中有設計師資源 | 耗時；無法規模化；設計師主觀判斷不一致 | 品質最高，但成本最高，不適合快速 prototyping |

### 切入點差異分析

```
                    ┌─────────────────────────────────────┐
                    │     問題：AI 生成 UI 罐頭感           │
                    └─────────────────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         ▼                         ▼                         ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Hallmark         │    │  DESIGN.md       │    │  Custom Prompt   │
│  解法：           │    │  解法：          │    │  解法：          │
│  強制結構多樣性   │    │  標準化設計規範   │    │  手寫規則        │
│  + 品質閘門      │    │  + prose 傳遞    │    │  + 經驗累積      │
│  + anti-pattern  │    │  + CLI 工具      │    │                  │
│  + self-critique │    │                  │    │                  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
         │                         │                         │
         │ 主動強制差異化           │ 被動提供規範             │ 完全手動
         │                         │                         │
         ▼                         ▼                         ▼
  效果：結構+風格雙重多樣化    效果：風格一致但結構可能重複   效果：取決於 prompt 品質
```

**Hallmark 的核心差異**：
1. **強制多樣性**：不是「建議」LLM 使用不同結構，而是透過 21 種 macrostructure + 20 種 theme + diversification rule 強制每次不同
2. **品質自檢**：58 道 slop gates + 6 軸 self-critique 讓 LLM 在產出前自我審查，而非產出後由人類檢查
3. **Anti-pattern 明確化**：將「AI 生成痕跡」具體化為 40+ 條可檢查的規則，而非模糊的「不要像 AI 生成的」
4. **Skill 形式**：以 Claude Code / Cursor Skill 的形式安裝，無需修改 LLM 本身，無需額外工具鏈

### 反證表：Hallmark 的潛在限制

| 限制 | 說明 | 緩解方式 |
|------|------|----------|
| **僅限特定 Agent 框架** | 設計為 Claude Code / Cursor / Codex 使用，其他 Agent 需手動移植 | 可手動提取 SKILL.md 內容移植至其他 Agent |
| **無設計 token 管理** | 不處理設計 token 的定義與同步（DESIGN.md 的領域） | 可與 DESIGN.md 並用（Hallmark 負責結構多樣性，DESIGN.md 負責 token 一致性） |
| **無元件庫整合** | 不提供預先設計好的元件，只提供設計規範 | 可與 shadcn/ui 等元件庫並用（Hallmark 負責整體結構與風格，元件庫負責元件實作） |
| **學習曲線** | 需理解 4 verbs、21 種結構、20 種主題、58 道閘門 | 安裝後即可使用，無需記憶所有細節（LLM 會自動遵循） |
| **無 Figma 整合** | 無法直接從 Figma 設計稿導入 | 可透過 Study verb 從截圖提取風格 |
| **專案活躍度** | 2026-04-27 建立，仍在早期階段，可能 breaking change | ROADMAP.md 已列出 Now/Next/Later 計劃，開發方向明確 |

---

## 5. User Q&A

### Q1：Hallmark 到底是「撰寫好看網頁的工具」還是「驗證網頁風格一致性的檢查器」？

**A**：兩者都不是。Hallmark 的核心 identity 是「**生成階段強制約束系統**」。

| 面向 | 撰寫工具 | 驗證工具 | Hallmark |
|------|----------|----------|---------|
| 介入時機 | 生成前/中 | 生成後 | **生成中**（注入 prompt 約束） |
| 產出 | 直接產出 UI 程式碼 | 產出評分/建議 | 產出 UI 程式碼（受約束） |
| 是否修改產出 | 是（生成） | 否（只檢查） | 是（生成時強制遵循規則） |
| Audit verb | 無 | 有 | 有（但非核心 verb） |
| 核心機制 | 模板/元件庫 | 規則檢查 | **prompt 注入 + 結構/風格強制多樣性 + 自檢** |

Hallmark 的 4 個 verb 各自對應不同角色：

| Verb | 角色 | 說明 |
|------|------|------|
| **Default**（無參數） | 生成 | 從零建頁面，強制遵循 21 種結構 + 20 種主題 + 58 道 slop gates |
| **Audit** | 審計 | 對現有頁面評分，產出改善清單，**不修改** |
| **Redesign** | 重構 | 保留內容與 IA，更換視覺結構與風格 |
| **Study** | 提取 | 從截圖/URL 提取設計 DNA，可產出 `design.md` |

**結論**：Hallmark 本質上是一套「生成時強制執行的設計規範」，不是撰寫工具（它不提供模板），也不是驗證工具（Audit 只是 4 個 verb 之一，非核心功能）。它的核心是「讓 LLM 在生成 UI 時無法落入常見的 AI 生成模式」。

### Q2：安裝後 Claude Code / Opencode 會不會自動套用？

**A**：取決於 Agent 框架的 skill 載入機制，非 Hallmark 本身能決定。

| Agent 框架 | 預設載入行為 | 控制方式 |
|---|---|---|
| **Claude Code** | **自動載入**（當 conversation 內容與 skill description 匹配時，Claude 自動載入 skill 內容） | 在 SKILL.md frontmatter 設 `disable-model-invocation: true` 可禁止自動載入 |
| **Opencode** | **按需載入**（agent 透過 `skill` tool 看到可用 skills 列表，可選擇載入或不載入） | 透過 `opencode.json` 的 `permission.skill` 設定 allow/deny/ask |

**關鍵差異**：

- **Claude Code**：Hallmark 的 SKILL.md 中 `description` 包含 "Use when the user asks to build a new app or landing page"。因此當使用者說「幫我建一個 landing page」時，Claude Code **會自動載入 Hallmark**，無需使用者特別提及。若使用者不希望自動載入，需修改 SKILL.md 加入 `disable-model-invocation: true`。
- **Opencode**：Opencode 的 skill 載入是 agent 主動行為（透過 `skill` tool），非自動。Agent 看到可用 skills 列表後自行判斷是否載入。若使用者不希望 agent 使用 Hallmark，可在 `opencode.json` 設 `"permission": { "skill": { "hallmark": "deny" } }`。

**結論**：在 Claude Code 中，若使用者未特別提及但對話內容與 Hallmark 的 description 匹配，**會自動套用**。在 Opencode 中，**不會自動套用**，需 agent 判斷後手動載入。

### Q3：如何安裝到 Claude Code / Opencode？請給出逐一步驟。

**A**：以下為 3 種安裝方式，依推薦優先順序排列。

#### 方式一：`npx skills add`（最簡單，僅 Claude Code / Cursor / Codex）

```bash
npx skills add nutlope/hallmark
```

- 自動下載 SKILL.md + references/ 到正確位置
- 重複執行可更新到最新版
- 僅支援 Claude Code、Cursor、Codex（Opencode 不支援此指令）

#### 方式二：手動安裝到 Claude Code

```bash
# Step 1: 建立 skill 目錄
mkdir -p ~/.claude/skills/hallmark

# Step 2: 下載 SKILL.md
curl -o ~/.claude/skills/hallmark/SKILL.md \
  https://raw.githubusercontent.com/Nutlope/hallmark/main/skills/hallmark/SKILL.md

# Step 3: 下載 references/ 目錄
curl -L -o /tmp/hallmark-refs.zip \
  https://github.com/Nutlope/hallmark/archive/refs/heads/main.zip
unzip /tmp/hallmark-refs.zip "hallmark-main/skills/hallmark/references/*" -d /tmp
mv /tmp/hallmark-main/skills/hallmark/references ~/.claude/skills/hallmark/
rm -rf /tmp/hallmark-refs.zip /tmp/hallmark-main

# Step 4: 驗證安裝
ls ~/.claude/skills/hallmark/
# 應看到：SKILL.md  references/
```

#### 方式三：手動安裝到 Opencode

Opencode 相容 Claude skill 格式，可直接複製：

```bash
# 專案層級（推薦，僅該專案可用）
mkdir -p .opencode/skills/hallmark
cp -r ~/.claude/skills/hallmark/* .opencode/skills/hallmark/

# 或全域層級（所有專案可用）
mkdir -p ~/.config/opencode/skills/hallmark
cp -r ~/.claude/skills/hallmark/* ~/.config/opencode/skills/hallmark/
```

Opencode 也支援讀取 `.claude/skills/` 路徑，因此若已安裝到 `~/.claude/skills/hallmark/`，Opencode 會自動發現該 skill，**無需額外複製**。

**驗證安裝是否成功**：

```bash
# 檢查 skill 是否被 agent 發現
# 啟動 Opencode 後，agent 的可用工具列表中應出現：
# <skill><name>hallmark</name><description>Anti-AI-slop design skill...</description></skill>
```

**結論**：最簡單的方式是 `npx skills add nutlope/hallmark`（僅 Claude Code）。若需在 Opencode 使用，安裝到 `~/.claude/skills/hallmark/` 即可（Opencode 相容此路徑），無需額外步驟。

### Q4：Hallmark 到底是「撰寫好看網頁的工具」還是「驗證網頁風格一致性的檢查器」？亦或是其他？

**A**：三者皆非。Hallmark 的核心 identity 是「**生成階段強制約束系統**」，其 4 個 verb 各自對應不同角色：

| Verb | 角色 | 說明 |
|------|------|------|
| **Default**（無參數） | 生成 | 從零建頁面，強制遵循 21 種結構 + 20 種主題 + 58 道 slop gates |
| **Audit** | 審計 | 對現有頁面評分，產出改善清單，**不修改** |
| **Redesign** | 重構 | 保留內容與 IA，更換視覺結構與風格 |
| **Study** | 提取 | 從截圖/URL 提取設計 DNA，可產出 `design.md` |

- 它不是「撰寫工具」：不提供模板或元件庫，而是注入 prompt 約束讓 LLM 自行生成
- 它不是「驗證工具」：Audit 只是 4 個 verb 之一，非核心功能
- 它不是「風格一致性檢查器」：Hallmark 不檢查是否符合既有設計系統（那是 DESIGN.md 的領域），而是強制每次產出**與前次不同**

**結論**：Hallmark 是一套「生成時強制執行的設計規範」，核心目標是讓 LLM 無法落入常見的 AI 生成模式。

### Q5：安裝後若我沒特別提到，Claude Code / Opencode 會不會自動套用？

**A**：取決於 Agent 框架的 skill 載入機制，非 Hallmark 本身能決定。

| Agent 框架 | 預設載入行為 | 控制方式 |
|---|---|---|
| **Claude Code** | **自動載入**（當 conversation 內容與 skill description 匹配時） | 在 SKILL.md frontmatter 設 `disable-model-invocation: true` 可禁止 |
| **Opencode** | **按需載入**（agent 透過 `skill` tool 手動載入） | 在 `opencode.json` 設 `"permission": { "skill": { "hallmark": "deny" } }` 可禁止 |

**關鍵行為差異**：
- Claude Code：Hallmark 的 SKILL.md 中 `description` 包含 "Use when the user asks to build a new app or landing page"。因此當使用者說「幫我建一個 landing page」時，Claude Code **會自動載入**，無需使用者特別提及 Hallmark 這個名字。
- Opencode：agent 看到可用 skills 列表後自行判斷是否載入，**不會自動套用**。

**結論**：Claude Code 會自動套用（若對話匹配），Opencode 不會。

### Q6：如何安裝到 Claude Code / Opencode？請給出官方 best practice 的逐一步驟指令。

**A**：以下為 3 種安裝方式，依推薦優先順序排列。

#### 方式一：`npx skills add`（最簡單，僅 Claude Code / Cursor / Codex）

```bash
npx skills add nutlope/hallmark
```

- 自動下載 SKILL.md + references/ 到正確位置
- 重複執行可更新到最新版
- Opencode 不支援此指令

#### 方式二：手動安裝到 Claude Code

```bash
# Step 1: 建立 skill 目錄
mkdir -p ~/.claude/skills/hallmark

# Step 2: 下載 SKILL.md
curl -o ~/.claude/skills/hallmark/SKILL.md \
  https://raw.githubusercontent.com/Nutlope/hallmark/main/skills/hallmark/SKILL.md

# Step 3: 下載 references/ 目錄
curl -L -o /tmp/hallmark-refs.zip \
  https://github.com/Nutlope/hallmark/archive/refs/heads/main.zip
unzip /tmp/hallmark-refs.zip "hallmark-main/skills/hallmark/references/*" -d /tmp
mv /tmp/hallmark-main/skills/hallmark/references ~/.claude/skills/hallmark/
rm -rf /tmp/hallmark-refs.zip /tmp/hallmark-main

# Step 4: 驗證安裝
ls ~/.claude/skills/hallmark/
# 應看到：SKILL.md  references/
```

#### 方式三：手動安裝到 Opencode

Opencode 相容 Claude skill 格式。若已安裝到 `~/.claude/skills/hallmark/`，Opencode 會自動發現該 skill，**無需額外複製**。

若需專案層級隔離：

```bash
mkdir -p .opencode/skills/hallmark
cp -r ~/.claude/skills/hallmark/* .opencode/skills/hallmark/
```

**驗證安裝是否成功**：啟動 Opencode 後，agent 的可用工具列表中應出現 `<skill><name>hallmark</name><description>Anti-AI-slop design skill...</description></skill>`。

**結論**：最簡單的方式是 `npx skills add nutlope/hallmark`（僅 Claude Code）。若需在 Opencode 使用，安裝到 `~/.claude/skills/hallmark/` 即可。
