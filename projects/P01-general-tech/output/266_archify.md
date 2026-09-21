# archify —— 生成可信架構圖的 Agent Skill 技術分析

> 標的：https://github.com/tt-a1i/archify
> 分析：`tech-research-agent`，2026-09-19
> 前置查證：第二大腦（FATESAIKOU/MyBrain）無 `archify` 此主題的既有判定或專案關聯。本報告事實以 GitHub 官方 repo 文件為主，個人適用性判斷對照第二大腦的技術取捨準則與同品類判定（diagram-design / OpenDesign / Hallmark / deepseek-harness）。

---

## 1. 這個技術解決什麼問題？

archify 解決的問題是：**AI Coding Agent 產出的「架構圖／流程圖」不可信、不可追蹤、難以在協作流程（尤其 PR review）中被驗證與比較**。

具體拆成三層：

1. **輸出不確定**：LLM 直接用 Markdown/`mermaid` 畫圖時，佈局、語意、節點取捨每次都不一樣，同一個系統兩次生成的圖不同。
2. **無法驗證**：圖是「畫出來看的」，沒有對應的結構化契約，無法自動檢查它是否對得上程式碼實作或設計意圖。
3. **無法比對變更**：改架構時沒有機制知道「這張圖跟前一版差在哪」，review 者只能靠肉眼比對兩張圖。

archify 主張「架構圖是**溝通的技術 artifact**」，應由 agent 產出 **typed JSON IR**，再由一套確定性編譯器輸出自含（self-contained）的 HTML/SVG。輸出可被原子驗證、可產生 Before/Delta/After 快照供 PR review，失敗時附 repair receipt。

### 問題描述的模糊之處

- 「架構圖」的邊界未明確定義——它涵蓋 architecture / workflow / sequence / data-flow / lifecycle 五型，但**沒有說明與程式碼實作的自動對齊範圍**。README 明列「非目標：Mermaid 自動排版、WYSIWYG」，但對「圖內容如何證明自己對得上程式碼」只有「證據導向 `SRC n` 來源驗證」的描述，未給出強制約束的範圍。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章明確提到的背景

- **LLM 圖表輸出的統計隨機性**：agent 直接生成 mermaid / 圖檔時，圖形語意與佈局依賴模型當下的機率分佈，無法保證確定性；這正是 README「How it works」開宗明義要打掉的問題。
- **圖是「可視化」不是「資料」**：archify 定位自己是「溝通 artifact 的技術儀器（instrument）」，反參考是「Mermaid beautifier / WYSIWYG 套件」——因為那些工具把圖當「呈現」而非「可驗證的結構」。

### 通用技術背景（補充）

- **Diagram-as-code 的演化**：從手繪、Visio、再到 Mermaid / PlantUML / Graphviz 這類「文字描述→圖」的工具，解決了「圖與程式碼同一來源」的問題，但**沒有解決「圖的內容是否可信」**——渲染確定，語意仍由作者（或 LLM）自由決定。
- **AI Coding Agent 的信任問題**：在 agent 自動化開發流程中，產出物是否可信、可否被 review、可否自動驗證，決定了 agent 能否放手執行。架構圖若不可驗證，就只是裝飾品；若可驗證，就成為 PR review 與設計文件的一部分。
- **PR review 需要「差異」，不是「整張圖」**：傳統工具給的是靜態全圖，改動時無法自動指出「哪一段變了」。archify 的 Delta 快照比對正是回應這個 gap。

---

## 3. 這個技術是如何解決該問題的？

核心做法是「**結構化 IR + 確定性編譯 + 原子驗證 + 差異交付**」的管線：

```
Agent 產出 typed JSON IR
        │
        ▼
┌───────────────────────────────┐
│ archify 確定性編譯器（Node.js） │
│  架構圖/工作流/序列/資料流/生命週期│
└───────────────────────────────┘
        │
        ▼
  自含 HTML / SVG（dark / light，4 presets）
        │
        ▼
  原子驗證（9 項 showcase artifact checks）
        │
        ├─ 失敗 → repair receipt（帶修正指引，回饋給 agent）
        │
        ▼
  交付 + Before/Delta/After 快照（供 PR review）
```

### 機制細節

1. **Typed JSON IR 為唯一來源**：agent 先產出結構化、typed 的圖資料（schema v1/v2），而不是直接寫 mermaid。5 種圖型（architecture / workflow / sequence / data-flow / lifecycle）由 router 分派。
2. **確定性編譯**：Node.js 渲染＋驗證系統把 IR 編譯成**自含的 HTML/SVG**（不依賴外部 CDN、不需套件）。輸出有七色語意、mono 字型、dark/light，遵循「Truth before spectacle（真實先於花俏）」。
3. **原子驗證才交付**：`validate` 與 `deliver` 是兩輪操作，內建 9 項 showcase artifact checks。**驗證不過就不交付**，並帶出 **repair receipt**（一份失敗診斷與修正指引）回饋給 agent，讓它能自我修正後重試。
4. **快照比對（PR review）**：支援 **Architecture Delta** 的 **Before / Delta / After** 三階段比對，自動指出變更處，適合放入 PR 供 review。
5. **證據導向來源**：`SRC n` 來源驗證機制，把圖中節點對應到原始碼位置，強化「圖是可信證據」而非「畫好看的」。
6. **Mermaid 作為輸入之一**：可接受 Mermaid 輸入並轉換為其 IR——但這只是「輸入轉換」，非產品本體。
7. **DeepSeek Harness（DSH）整合**：`@tt-a1i/archify-dsh` 為 **community 非官方整合**，僅 bundled Skill，無 telemetry、無 native tools。archify 本體與 deepseek-harness 無直接耦合。

### 對「是否重蹈 diagram-design 出版工具過重」矛盾的處理

archify 與已 Reject 的 **diagram-design** 同屬「圖表渲染＋交付」的 skill，但有**一個關鍵差異點：驗證**。

| 面向 | diagram-design（Reject） | archify |
|---|---|---|
| 目的 | 出版級視覺（品牌一致、對外呈現） | 溝通的技術 artifact（可驗證、可追蹤） |
| 核心賣點 | 品牌 token、27 視覺型、反 AI-slop | typed IR、確定性 compile、原子驗證、Delta 比對 |
| 驗證 | style-guide gate、CI（視覺規範） | 結構驗證、repair receipt、PR 快照 |
| 對「保留複雜度以理解」的態度 | 刪減約束（≤9 節點、density 4/10） | 未見強制節點刪減；著重可信而非簡化 |

兩者都屬「skill for agent」，但 archify 的取徑是「把圖變成**可被程式驗證的資料**」，diagram-design 的取徑是「把圖變成**符合品牌的視覺輸出**」。因此 archify 是否對使用者適用，不應沿用 diagram-design 的 Reject 結論，而應依使用者自己的判準重新評估（見 §4 與結論）。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 第二大腦查證結果（先讀判定總表再讀個案）

第二大腦無 `archify` 此主題。但**同品類的「design／圖表 skill for agent」他已有判定**，且與本標的高度相關：

| 標的 | 判定 | 來源／信任層級 |
|---|---|---|
| **diagram-design**（出版級圖表設計 skill） | **Reject**——用不到如此重型，目的是理解抽象概念，它是出版工具不是思考工具 | [diagram-design.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/diagram-design.md)（`generated.by: process:learn-gh-agent`，`status: draft`，**未經 review**） |
| **OpenDesign**（coding agent 產出設計產物的自主平台） | **採用**——可以在 Local 嘗試 | [OpenDesign.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OpenDesign.md)（`generated.by: human:fatesaikou`，`status: stable`，**他本人定案**） |
| **Hallmark**（反 AI 味 UI 設計 skill） | **觀望**——2026-08-11 由採用降級，判定成立但未排入下一步清單 | [Hallmark.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Hallmark.md)（`generated.by: opencode/deepseek-v4-pro`，`status: stable`，**有 human verified**） |
| **deepseek-harness（dsh）** | **觀望**（Reserve）——很重型無法立刻 Accept，等更輕量方案 | [DeepSeek Harness.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/DeepSeek%20Harness.md) |
| **DeepSeek V4 Flash Vision Exp** | **試用**——要驗截圖與圖表讀取堪用度 | [DeepSeek V4 Flash Vision Exp.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/DeepSeek%20V4%20Flash%20Vision%20Exp.md)（`draft`） |

**判定總表**為索引（`generated.by: ollama-cloud/deepseek-v4-flash`，`status: draft`，**AI 草稿**）。技術取捨準則為骨幹檔（`status: draft`，`generated.by: claude-code/opus-5`，但「原話」引號內為使用者本人結論）。

**與 archify 結論的關係**：第二大腦對「圖表 skill」的既有態度是「**出版工具對我的目的過重**」（diagram-design Reject）。archify 若被歸類為「出版工具」，則會與此衝突；但它強調「驗證」與「Delta 比對」，這與使用者「**要補驗證機制而非加審核關卡**」的準則（技術取捨準則第五條）**同向**——因此 archify 並非單純重蹈 diagram-design，值得獨立看待。這是查證衝突最有價值的點。

### 替代方案與 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Mermaid / PlantUML / Graphviz（diagram-as-code）** | 用文字 DSL 描述圖，由引擎渲染為 SVG/PNG | 需圖形語意明確、不需自動驗證內容；接受「渲染確定、語意由人保證」 | 無結構化驗證，圖內容可信度靠作者；LLM 生成時輸出不確定；無內建 PR diff | 快速產圖、與文件同源；但不可自動驗證、不可追蹤變更 |
| **diagram-design（出版級圖表 skill）** | 語意 pattern→27 視覺型→品牌 token→CI gate，輸出出版級 HTML/SVG | 需對外呈現、品牌一致性需求；接受對「理解抽象」目的過重 | 對「解構／理解」目的過重，多餘重量；刪減約束與保留複雜度矛盾 | 高品質對外圖表；對思考型使用者不合用 |
| **OpenDesign（自主設計產物平台）** | 讓 coding agent 從自然語言直接產出可編輯設計產物，155+ SKILL.md + 150+ DESIGN.md | 需整套自主設計平台、願投入導入 | 重型、需安裝 daemon/web/desktop；與 archify 是不同層級的系統 | 端到端設計產物自主產出；比 archify 更全面但也更重 |
| **archify（本標的）** | typed JSON IR→確定性編譯→原子驗證→Delta 快照 | 需接受「圖是結構化資料」的模型、願以 Node.js 跑編譯器、要 PR diff 驗證 | 需維護 IR schema；輸出受限於五型與其 presets；驗證範圍未含與程式碼的自動對齊 | 可信、可驗證、可 PR 比對的架構圖；降低 agent 輸出不可信成本 |

### 各方案切入點差異

- **Mermaid 類**：解決「文字描述→圖」，但把「圖是否可信」完全交給作者，無驗證層。
- **diagram-design**：解決「圖的品牌與視覺品質」，把圖當「對外呈現的產品」，對「理解抽象概念」目的過重。
- **OpenDesign**：解決「整套設計產物的自主產出」，涵蓋範圍最廣，也最重。
- **archify**：唯一把「驗證」與「PR diff 比對」當核心的——圖被視為**可被程式驗證的技術 artifact**，直接回應 agent 產出可信度問題。

> 結論：archify 的獨特切入點是「**把架構圖變成可驗證、可追蹤的技術 artifact**」，而非視覺品質或 DSL 渲染。這使其與已 Reject 的 diagram-design（出版工具過重）在目的上分岔。對使用者而言，適用性取決於：**他的「理解抽象概念」目的是否需要這種「確定性＋驗證」的圖譜**——若他需要的是保留複雜度的思考圖，archify 的「可信交付」價值有限；若他需要的是 agent 在 PR 中自動產出可驗證架構圖，則 archify 的設計與他的「補驗證機制」準則同向。
