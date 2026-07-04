# DESIGN.md 技術分析報告

> 調研日期：2026-07-04 | 基於 google-labs-code/design.md（24.7k stars, Apache-2.0, TypeScript）

---

## 1. 這個技術解決什麼問題？

DESIGN.md 解決的是 **AI 程式碼生成 Agent 在跨 session、跨專案時無法維持一致的視覺設計風格** 的問題。具體來說，它同時處理以下 4 個子問題：

| 子問題 | 具體表現 |
|---|---|
| **設計語意無法傳遞給 AI** | 開發者對 Agent 說「用現代、乾淨的風格」→ Agent 產出每次不同，因為形容詞（modern, clean）的語意邊界模糊 |
| **跨 session 設計遺忘** | Agent 在 session A 產出符合風格的 UI，session B 從零開始，無記憶機制保留設計決策 |
| **設計 token 與 prose 分離** | 設計系統的數值（色碼、字型大小）存在 Figma / tokens.json，設計 rationale 存在 Notion / Confluence，Agent 無法同時存取兩者 |
| **無標準化 Agent 設計介面** | 每個 Agent 框架（Copilot, Cursor, Windsurf, Claude Code）各自定義設計提示格式，無互通性 |

DESIGN.md 的目標是提供一個 **單一檔案、人機可讀、Agent 可執行的設計系統描述格式**，讓 AI Agent 能像讀取 `package.json` 一樣讀取設計規範。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **AI Code Generation 的興起**：LLM-based coding agent（GitHub Copilot, Cursor, Claude Code, Windsurf）開始直接產出 UI 程式碼，但缺乏標準化的設計輸入格式。
- **設計系統的碎片化**：設計 token 存在 Figma variables / DTCG JSON / Tailwind config，設計 rationale 存在設計師的 Notion 文件，Agent 無法自動整合。
- **Prose > Tokens 的洞察**：DESIGN.md PHILOSOPHY 明確指出「token 是 context，prose 才是設計的核心」。精確的 prose（如「1970 年代研究生講義 handout」）比 50 個 token 值承載更多設計意圖。

### 通用技術背景（文章中未明確提及但為必要脈絡）

- **LLM 對形容詞的語意模糊性**：LLM 對「modern」「clean」「premium」等形容詞的 embedding 落在語意空間的廣義區域，每次 sampling 可能落在不同位置，導致輸出不一致。
- **Agent 無持久化記憶**：多數 coding agent 的 context window 有限，session 結束後設計決策遺失，下次需重新描述。
- **設計 token 格式戰國時代**：W3C DTCG、Tailwind、Style Dictionary、Figma variables 各有不同格式，缺乏統一橋接層。
- **前端工具鏈的標準化慣例**：`package.json`（依賴）、`tsconfig.json`（編譯）、`eslint.config.js`（程式碼風格）已成為標準化配置檔案，但設計系統缺乏對應標準。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 核心機制：雙層結構（YAML front matter + Markdown prose）

```
┌─────────────────────────────────────────────────────┐
│  DESIGN.md                                          │
│                                                     │
│  ┌─ YAML Front Matter ──────────────────────────┐   │
│  │  ---                                          │   │
│  │  name: Heritage                               │   │
│  │  colors:                                      │   │
│  │    primary: "#1A1C1E"                         │   │
│  │    secondary: "#6C7278"                        │   │
│  │  typography:                                   │   │
│  │    h1:                                         │   │
│  │      fontFamily: Public Sans                   │   │
│  │      fontSize: 3rem                            │   │
│  │  ---                                          │   │
│  └───────────────────────────────────────────────┘   │
│                                                     │
│  ┌─ Markdown Prose ─────────────────────────────┐   │
│  │  ## Overview                                  │   │
│  │  Architectural Minimalism meets Journalistic   │   │
│  │  Gravitas. The UI evokes a premium matte      │   │
│  │  finish...                                    │   │
│  │                                               │   │
│  │  ## Colors                                    │   │
│  │  - **Primary (#1A1C1E):** Deep ink for        │   │
│  │    headlines and core text.                   │   │
│  │  - **Secondary (#6C7278):** Sophisticated     │   │
│  │    slate for borders, captions...             │   │
│  └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

**Token 層（YAML front matter）**：機器可讀的設計數值，包含：
- `colors`：色票（任何 CSS 有效顏色值）
- `typography`：字型定義（fontFamily, fontSize, fontWeight, lineHeight, letterSpacing）
- `rounded`：圓角尺度
- `spacing`：間距尺度
- `components`：元件 token（含 `{path.to.token}` 引用語法）

**Prose 層（Markdown body）**：人類可讀的設計 rationale，按固定 section 順序組織：
1. Overview（品牌風格描述）
2. Colors（色票使用規則）
3. Typography（字型使用規則）
4. Layout（佈局策略）
5. Elevation & Depth（層級表現）
6. Shapes（形狀語言）
7. Components（元件規範）
8. Do's and Don'ts（限制條件）

### 3.2 Token 引用機制

元件 token 可引用其他 token 值，形成依賴圖：

```yaml
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"    # 引用 colors.tertiary
    textColor: "{colors.on-tertiary}"       # 引用 colors.on-tertiary
    rounded: "{rounded.sm}"                 # 引用 rounded.sm
    padding: 12px                           # 字面值
  button-primary-hover:
    backgroundColor: "{colors.tertiary-container}"  # hover 變體
```

### 3.3 CLI 工具鏈

| 命令 | 功能 | 輸出範例 |
|------|------|----------|
| `designmd lint` | 驗證結構正確性、token 引用完整性、WCAG 對比度 | JSON findings（error/warning/info） |
| `designmd diff` | 比較兩個 DESIGN.md 的 token 層級差異 | JSON（added/removed/modified） |
| `designmd export` | 匯出為 Tailwind v3 JSON / Tailwind v4 CSS / DTCG JSON | 對應格式檔案 |
| `designmd spec` | 輸出格式規格（可注入 Agent prompt） | Markdown / JSON |

### 3.4 Linting 規則（9 條）

| 規則 | 嚴重度 | 檢查內容 |
|------|--------|----------|
| `broken-ref` | error | Token 引用 `{colors.primary}` 指向未定義的 token |
| `missing-primary` | warning | 定義了 colors 但無 `primary` token |
| `contrast-ratio` | warning | Component 的 backgroundColor/textColor 低於 WCAG AA（4.5:1） |
| `orphaned-tokens` | warning | 定義了 color token 但未被任何 component 引用 |
| `token-summary` | info | 各 section 定義的 token 數量摘要 |
| `missing-sections` | info | 缺少可選 section（spacing, rounded） |
| `missing-typography` | warning | 有 colors 但無 typography token |
| `section-order` | warning | Section 未按規範順序排列 |
| `unknown-key` | warning | 頂層 YAML key 疑似拼寫錯誤（如 `colours:` → `colors:`） |

### 3.5 實際範例：Atmospheric Glass（glassmorphism 設計系統）

```yaml
---
name: Atmospheric Glass
colors:
  surface: "#0b1326"
  primary: "#ffffff"
  on-primary: "#2f3131"
  # ... 50+ color tokens
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 84px
    fontWeight: "700"
    lineHeight: 90px
    letterSpacing: -0.04em
  # ... 6 typography levels
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-padding: 24px
  card-gap: 16px
components:
  glass-card-standard:
    backgroundColor: rgba(255, 255, 255, 0.1)
    textColor: "{colors.primary}"
    rounded: "{rounded.lg}"
    padding: "{spacing.glass-padding}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.xl}"
    height: 48px
---
```

Prose 層描述設計意圖：
- **Brand & Style**：高保真 Glassmorphism，多色抽象漸層背景 + 磨砂玻璃元件
- **Colors**：單色白系 + alpha channel，背景為 Deep Blue / Vivid Purple / Soft Pink 漸層
- **Typography**：Inter 字型，display 層級 84px 用於溫度讀數
- **Elevation**：`backdrop-filter: blur(20px~40px)` + 1px 白邊框模擬光折射

### 3.6 三項設計哲學原則

| 原則 | 說明 | 反面案例 |
|------|------|----------|
| **Prose > Tokens** | Prose 承載設計意圖，token 只是 context | 只給色碼不給使用規則 → Agent 無法判斷何時用哪個色 |
| **Specific Reference > Adjectives** | 具體參考（「1970 年代講義 handout」）比形容詞（「modern, clean」）承載更多資訊 | 「Modern, clean, trustworthy, premium」→ 產出 generic |
| **Negative Constraints** | 精確的參考自動帶來限制（講義不會發光、不會用漸層） | 模糊描述 → 需長串 don't list 補救 |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表：替代方案對照

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|----------|-------------|---------------|-----------------|
| **W3C Design Tokens (DTCG)** | 純 JSON 格式的設計 token 標準，定義 typed token groups（color, dimension, font family）與 alias 引用 | 已有設計 token 管理工具（Style Dictionary, Figma Tokens） | 無 prose 層，無法傳遞設計 rationale；需額外工具轉換為 Agent 可讀格式 | 標準化 token 交換格式，但 Agent 仍需 prose 才能理解使用情境 |
| **Tailwind CSS Theme Config** | 在 `tailwind.config.js` 中定義 `theme.extend` 的顏色、字型、間距 scale | 專案使用 Tailwind CSS 框架 | 綁定 Tailwind 生態系；無設計 rationale；無跨 Agent 互通性 | 開發者可直接使用 utility class，但 Agent 無法理解「為何用這個色」 |
| **Figma Variables + REST API** | 在 Figma 中定義 design tokens 為 variables，透過 Figma REST API 讀取 | 設計師使用 Figma 且 token 結構已建立 | 需 Figma 授權與網路連線；無離線可用性；無 prose 層 | 設計 token 與設計工具同步，但 Agent 無法直接消費 Figma API |
| **Style Dictionary** | 將設計 token 定義為 JSON/JSON5/YAML，透過 build 流程輸出為各平台格式（CSS, JS, Swift, Kotlin） | 需建立 build pipeline；需定義 token 命名規範 | 純 token 無 prose；需額外步驟才能讓 Agent 使用；無 lint/diff 工具 | 跨平台 token 同步，但 Agent 使用需額外轉換層 |
| **Agent-specific Prompt Templates** | 在 Agent 的 system prompt 或 `.cursorrules` / `.clinerules` 中直接寫設計規範 | 使用特定 Agent 框架 | 無標準格式；跨 Agent 不可攜帶；prose 與 token 混雜在 prompt 中難以維護 | 快速上手但無法規模化 |

### 切入點差異分析

```
                    ┌─────────────────────────────┐
                    │     設計 token 標準化         │
                    │  W3C DTCG / Style Dictionary │
                    └─────────────┬───────────────┘
                                  │ 只有 token，無 prose
                                  │
                    ┌─────────────▼───────────────┐
                    │     DESIGN.md                │
                    │  Token + Prose + CLI + Lint  │
                    └─────────────┬───────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
      ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
      │ Tailwind     │   │ Figma        │   │ Agent Prompt │
      │ Config       │   │ Variables    │   │ Templates    │
      └──────────────┘   └──────────────┘   └──────────────┘
      框架綁定           需 Figma 授權      無標準化
```

**DESIGN.md 的核心差異**：
1. **Token + Prose 合一**：其他方案只解決 token 標準化，DESIGN.md 同時解決「數值」與「意圖」的傳遞
2. **Agent 原生設計**：從設計之初就考慮 AI Agent 作為消費者，而非人類開發者
3. **CLI 工具鏈**：lint/diff/export 讓 DESIGN.md 可納入 CI/CD pipeline，其他方案無對應工具
4. **格式寬容**：接受未知 section、未知 token name、未知 component property，不阻斷解析（僅 warning），降低採用門檻
5. **可匯出性**：可雙向轉換為 DTCG JSON / Tailwind config，不 lock-in

### 反證表：DESIGN.md 的潛在限制

| 限制 | 說明 | 緩解方式 |
|------|------|----------|
| 格式仍在 alpha | spec 與 CLI 仍在活躍開發中，可能 breaking change | 版本欄位 `version: alpha` 明確標示 |
| 無動畫 / motion 標準 | spec 未定義 motion token schema | 透過 prose section + 自訂 YAML key 擴充（PHILOSOPHY 明確允許） |
| 無 iconography 標準 | 無內建 icon token 類型 | 同上，透過 prose 描述 |
| Agent 採用度未知 | 需 Agent 框架（Copilot, Cursor, Claude Code）原生支援才能發揮最大效益 | CLI 工具讓 Agent 可透過 `designmd lint` / `designmd spec` 程式化讀取 |
| 無 Figma 雙向同步 | 無官方 Figma plugin 同步 token | 可透過 `export --format dtcg` 橋接 Figma Tokens plugin |

---

## 5. User Q&A

### Q1：所以這東西是「設計標準文件」還是「一份 Markdown(Prompt)」？

**A**：DESIGN.md 同時是「格式標準（format specification）」與「一份 Markdown 檔案」，兩者不互斥，而是規範與實例的關係。

| 層面 | 內容 | 對應實體 |
|------|------|----------|
| **格式標準（specification）** | 定義 YAML front matter schema、8 個 prose section 順序、token 引用語法 `{path.to.token}`、9 條 lint 規則、component property 白名單 | `docs/spec.md`、`PHILOSOPHY.md`、CLI 工具（lint/diff/export） |
| **具體檔案（Markdown file）** | 開發者撰寫的 `DESIGN.md`，包含具體的色票、字型、prose 描述 | 專案根目錄的 `DESIGN.md`（如 examples/atmospheric-glass/DESIGN.md） |
| **Prompt 模板** | Agent 可將 `DESIGN.md` 內容注入 system prompt 或 context window，作為設計規範的輸入 | 無固定格式，取決於 Agent 框架（Copilot / Cursor / Claude Code） |

**類比**：`package.json` 同時是「npm package.json 格式規範」與「專案中的 package.json 檔案」。DESIGN.md 的 spec 定義了格式，而專案中的 DESIGN.md 是該格式的實例。

**關鍵區別**：
- DESIGN.md **不是**一份通用的「Prompt 模板字串」——它是有結構的格式（YAML + Markdown），有專屬 CLI 工具可驗證、比對、匯出
- DESIGN.md **可以**被當作 Prompt 的一部分餵給 Agent——但這只是消費方式之一，不是它的本體定義
- 官方定位為「format specification」，產出物為「Markdown file with YAML front matter」

**結論**：DESIGN.md 是「一份定義了設計系統描述格式的標準」，其實例是「一份遵循該標準的 Markdown 檔案」。

---

### Q2：這東西的「目標使用效果」、「使用前提」、「使用方式」、「使用副作用」為何？

**A**：

| 面向 | 內容 |
|------|------|
| **目標使用效果** | 1. AI Agent 跨 session、跨專案產出視覺一致的 UI 程式碼<br>2. 開發者只需維護一份 `DESIGN.md`，即可讓所有 Agent 框架（Copilot, Cursor, Claude Code, Windsurf）讀取相同設計規範<br>3. 設計 token 與 prose 合一，Agent 同時取得「數值」與「使用規則」<br>4. 可透過 CLI 工具（lint/diff/export）納入 CI/CD pipeline，設計變更可追蹤 |
| **使用前提** | 1. 專案使用 AI coding agent 產出 UI 程式碼（非純手寫專案效益低）<br>2. 開發者需有能力撰寫 YAML front matter + Markdown prose（基本文件能力）<br>3. 需安裝 Node.js 以執行 CLI 工具（lint/diff/export）<br>4. Agent 框架需支援讀取外部檔案作為 context（多數現代 Agent 皆支援）<br>5. 設計系統需有一定成熟度（臨時專案或一次性頁面不適合） |
| **使用方式** | 1. **撰寫**：在專案根目錄建立 `DESIGN.md`，依 spec 撰寫 YAML front matter（colors, typography, rounded, spacing, components）+ Markdown prose（Overview, Colors, Typography, Layout, Elevation, Shapes, Components, Do's and Don'ts）<br>2. **驗證**：執行 `npx @google/design.md lint DESIGN.md` 檢查結構正確性與 WCAG 對比度<br>3. **引用**：在 Agent 的 system prompt 或 context 中指示「請參考專案根目錄的 DESIGN.md 作為設計規範」<br>4. **維護**：設計變更時更新 DESIGN.md，執行 `designmd diff` 比較變更，透過 `designmd export` 同步至 Tailwind config / DTCG JSON |
| **使用副作用** | 1. **維護成本**：需持續更新 DESIGN.md 以反映設計變更，否則 Agent 會使用過時規範<br>2. **格式仍在 alpha**：spec 可能 breaking change，需追蹤 upstream 更新<br>3. **無強制執行力**：Agent 可能不完全遵循 DESIGN.md（取決於 Agent 的 instruction following 能力）<br>4. **無動畫 / motion 標準**：需自行擴充 prose section 描述<br>5. **無 Figma 雙向同步**：設計師在 Figma 修改後需手動同步至 DESIGN.md<br>6. **學習曲線**：團隊需學習 prose 撰寫技巧（Specific Reference > Adjectives 原則）才能發揮最大效益 |

**反證表：何時不該使用 DESIGN.md**

| 情境 | 原因 |
|------|------|
| 專案無 AI Agent 參與 | DESIGN.md 的設計目標是給 Agent 讀，純人類開發用 Tailwind config 或 Style Dictionary 更直接 |
| 設計系統尚未穩定 | 頻繁變動的 token 會導致 DESIGN.md 與實際產出脫節，維護成本 > 效益 |
| 單人一次性專案 | 無跨 session / 跨 Agent 需求時，直接在 Agent prompt 寫規範更快 |
| 團隊無 prose 撰寫能力 | 寫出模糊 prose（「modern, clean, premium」）反而比不寫更糟（產生 generic 輸出） |
