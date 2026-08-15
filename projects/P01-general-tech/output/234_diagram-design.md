# diagram-design 技術分析報告

> 調研日期：2026-08-15 | 基於 cathrynlavery/diagram-design（18,112 stars, MIT, default branch=main, primaryLanguage=HTML, created 2026-04-16, updated 2026-08-15）
> 定位描述（README）：「29 editorial diagram types for Claude Code. Self-contained HTML + SVG. No shadows, no Mermaid-slop.」
> 作者：Cathryn Lavery（BestSelf.co 創辦人、littlemight.com 作者）

---

## 1. 這個技術解決什麼問題？

**diagram-design 解決的是：AI Coding Agent（Claude Code / Codex / Pi）在產出「可出版、可用於部落格或文件」的圖表時，回傳的是千篇一律的 generic 圖形（圓角方框、過度陰影、Mermaid 罐頭圖），品質遠低於編輯級（editorial）水準，且與使用者自身品牌風格不一致。**

它把「AI 產出圖表」從「隨機的 SVG 拼湊」改造成「一個有 27 種視覺型、一組品牌 token、一組反 AI-slop 規則、並以 CI 硬性驗證的確定性產物」。具體分為以下子問題：

| 子問題 | 具體表現 |
|---|---|
| **視覺型不匹配** | 使用者要「架構圖／流程圖」，Claude 回傳的只是「generic rounded-box」，無法自動對應到正確的圖表類型 |
| **品牌不一致** | 每次產出與網站既有風格不符，需 30 分鐘手動用 Figma 調整，或乾脆跳過圖表 |
| **AI 罐頭感（slop）** | 使用 shadow、過度圓角、不整除的座標、Mermaid 輸出，一眼即知是 AI 生成的廉價圖 |
| **無品質驗證** | 產出後無任何自動檢查，是否對齊、是否可讀、是否符合無障礙，全憑運氣 |

### 問題描述中的模糊之處

- 「出版級（editorial quality）」是主觀形容詞，repo 以**一組可檢查的規則**（data-ink ratio 精神、無 shadow、4px 網格、3 字型限制、WCAG AA 對比）把它操作化成可驗證的條件，而非停留在美感描述。
- 標的**受眾不明**：README 明說給 Claude Code / Codex / Pi，因此「解決問題」的適用範圍限於這類 skill-based agent，不含純瀏覽器或 Figma 類工具。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **作者個人動機**：Cathryn Lavery 在部落格／產品內容中頻繁需要圖表，但每次請 Claude 繪製，回傳的都是「generic rounded-box」且與網站風格不符；與 Figma 搏鬥 30 分鐘或乾脆跳過。問題根源在於 **LLM 缺乏對「該用哪種視覺型」「該遵守哪些設計約束」的內建知識**，而既有的 coding agent 沒有為圖表輸出提供約束。
- **Mermaid-slop**：Agent 傾向直接把結構描述丟給 Mermaid 產生示意圖，輸出帶有 Mermaid 的預設風格與排版瑕疵，稱之為「Mermaid-slop」。

### 通用技術背景（文章中未明確提及但為必要脈絡）

- **LLM 的統計回歸**：在缺乏明確視覺約束時，LLM 會收斂到訓練資料中出現頻率最高的圖形模式（圓角方框＋陰影＋漸層），這是生成式模型的 mode collapse 在視覺領域的表現。
- **視覺編碼的準確度階層**：圖表領域的既有方法論（例如 Cleveland & McGill 的視覺編碼準確度、Tufte 的 data-ink ratio）已明確哪些視覺通道傳遞數值最準（位置＞長度＞角度＞面積＞顏色）。AI 若無此知識，就會用不準確的編碼（3D、面積、過多顏色）呈現資料，**誤導讀者**。
- **圖表的目的是揭露資料，不是裝飾**：這是使用者第二大腦中「資料視覺化」思考習慣（第 39 條）的核心判準——圖表存在的目的是讓眼睛看見表格看不見的模式，任何裝飾（3D、陰影、漸層）都是 chartjunk，會扭曲資料感知。
- **無標準化的「Agent 圖表設計規範」**：Hallmark 解決的是網頁 UI 的 AI 罐頭感，DESIGN.md 解決的是設計 token 的跨 session 一致性；在 diagram-design 之前，**沒有一套專為「Agent 產出圖表」定義視覺型、品牌 token、反 slop 規則的標準**。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 整體架構

diagram-design 是一個 Claude Code / Codex / Pi 的 **Agent Skill**，產出「自含（self-contained）HTML + SVG」的圖表，無 build step、無 JS、無外部圖片依賴，可直接嵌入部落格或文件。它透過「先選語意型 → 再選視覺型 → 套品牌 token → 通過 style-gate 與 CI 驗證」的強制流程，把圖表產出收斂到確定性、可檢查的狀態。

```
┌────────────────────────────────────────────────────────────────────┐
│  diagram-design Skill                                               │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌───────────────────────┐   │
│  │ 語意 pattern  │──▶│ 27 種視覺型    │──▶│ 設計系統 (brand token) │   │
│  │ (7 種行為語意) │   │ 每型 3 種變體   │   │ paper/ink/accent/...  │   │
│  └──────────────┘   └──────────────┘   └───────────────────────┘   │
│         │                   │                       │               │
│         ▼                   ▼                       ▼               │
│  ┌──────────────┐   ┌──────────────┐   ┌───────────────────────┐   │
│  │ 匯入重繪       │   │ anti-pattern │   │ style-guide gate      │   │
│  │ draw.io/Mermaid│   │ (universal   │   │ (確認後才繪製)         │   │
│  │ 四 dials      │   │  AI-slop 清單)│   │                       │   │
│  └──────────────┘   └──────────────┘   └───────────────────────┘   │
│         │                                                            │
│         ▼                                                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  靜態 HTML + SVG（無 JS / 無 build / 無外部依賴）             │   │
│  │  motion 為選配（none/reveal/step/loop，預設 none，            │   │
│  │  僅單一 pinned controller 且 SHA-256 + 字串雙重驗證）          │   │
│  │  a11y（role="img" + aria-labelledby + prefers-reduced-motion）│   │
│  │  CI 驗證（lint-skin / verify-geometry / verify-motion /      │   │
│  │  verify-drawio-import / verify-mermaid-import / verify-docs） │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 核心機制：語意 pattern → 視覺型路由

- **不擴充型別數量**，而是先依「行為語意」（fan-in queue、policy trace、trust boundary 等 **7 種**）選出語意 pattern，再路由到最接近的視覺型。
- **27 種視覺型**：architecture、flowchart、sequence、state、ER、timeline、swimlane、quadrant、radar、loop、nested、tree、org-chart、layers、venn、pyramid、bar、line、gantt、scatter、process、medallion、data-flow、DP integration、DP security matrix、IT current-state、high-level。
- 每種視覺型提供 **3 種靜態變體**：minimal light / minimal dark / full-editorial，由設計系統決定用哪一種。

### 3.3 設計系統（消除「AI 感」的具體約束）

| 約束 | 內容 | 目的 |
|---|---|---|
| 強調色 | 1 個 accent | 避免過多顏色造成視覺混淆（呼應「用超過 7 種顏色眼睛無法區分」的誤用） |
| 焦點元素 | 1–2 個 focal elements | 建立視覺層級 |
| 字型 | 3 種：Instrument Serif / Geist sans / Geist Mono | 固定字型堆疊，避免 AI 慣用的 Inter/system-ui |
| 線條 | 1px hairline | 避免厚重外框 |
| 陰影 | 無 shadow | 避免 AI 罐頭感 |
| 圓角 | max radius 10px | 避免過度圓角 |
| 座標網格 | 所有座標／寬／間距可被 **4 整除** | 產生人類設計師才有的對齊規律，去除 AI 隨機浮點座標的痕跡 |

### 3.4 品牌 onboarding（60 秒）

- 從使用者網站抓取 **dominant palette + font stack**，映射到語意 token：`paper / ink / muted / accent / link`，寫入 `style-guide.md`。
- **自動做 WCAG AA 對比檢查**，確保圖表在該品牌色下仍可讀。
- **first-run gate** 強制完成品牌客製化，避免未套用品牌就產圖。

### 3.5 匯入重繪（draw.io / Mermaid）

- 可 redraw 既有檔案：draw.io（`.drawio` / `.drawio.xml` / `.drawio.png` / `.drawio.svg`）與 Mermaid（`.mmd` / fenced block）。
- 透過 **四 dials**（format × size × detail × audience）控制重繪方向，輸出附 **fidelity ledger**（記錄重繪後保留／變更了哪些資訊）。

### 3.6 反 AI-slop 規則（universal anti-patterns）

- SKILL.md 內建一套「AI slop 清單」：列出具體的 AI 圖表痕跡（shadow、過度圓角、不整除座標、Mermaid 預設樣式等），繪製前以此自檢。
- **style-guide gate**：依品牌 token 驗證產出符合設計系統後，**確認後才繪製**，不直接輸出未經驗證的圖。

### 3.7 靜態預設與 motion（資安與可驗證性的取捨，ADR 0001）

- **motion 為選配**（none / reveal / step / loop），**預設 none**，產出自含靜態 HTML。
- 當啟用 motion 時，**僅允許單一 pinned controller**，且以 **SHA-256 + 字串雙重驗證**確保 controller 內容未遭置換。
- 動機（ADR 0001）：自含靜態無 script 是「審查最安全、review 成本最低」的預設；motion 因引入執行行為而需要資安與驗證機制。此設計與使用者「AI agent 的約束放在 harness 而非權限」「要的是『你怎麼知道自己做對了（verify）』而非人工審核」的信念一致。

### 3.8 無障礙（a11y）與 CI 驗證

- 每個 SVG 帶 `role="img"`、`aria-labelledby`、`title/desc`；`prefers-reduced-motion` 顯示完整靜態幀。
- **CI 多重 gate**：`lint-skin`、`verify-geometry`、`verify-motion`、`verify-drawio-import`、`verify-mermaid-import`、`verify-docs-sync`，把品質檢查程式化，而非依賴人工 review。
- **metadata 版本**：SKILL.md metadata version 2.4；README 提及 2.0 Loop、2.3 semantic patterns + accessible motion。

### 3.9 實際工作流程範例

```
使用者需求：畫一張「訂單處理的 fan-in queue」架構圖

Step 1: 語意 pattern 選擇
  → 行為語意 = fan-in queue（多來源匯入同一處理節點）
  → 路由到視覺型 = flow / data-flow

Step 2: 視覺型與變體
  → 選 architecture（或 data-flow），變體依設計系統選 minimal / editorial

Step 3: 品牌 token 套用
  → 從 style-guide.md 讀 paper/ink/accent/link
  → 檢查 WCAG AA 對比，1 個 accent、1–2 focal elements

Step 4: anti-slop 自檢
  → 無 shadow、圓角 ≤ 10px、座標可被 4 整除、3 字型內、無 Mermaid 預設樣式

Step 5: style-guide gate + 確認
  → 符合設計系統後確認，才繪製

Step 6: 輸出
  → 自含靜態 HTML + SVG（無 JS），內嵌 role="img" 無障礙屬性
  → CI 跑 lint-skin / verify-geometry 等 gate 通過
```

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

**第二大腦對照說明**：Step 1 已確認第二大腦中無 `diagram-design`／`cathrynlavery` 兩個關鍵詞的任何評估記錄（第二大腦無此主題）。以下替代方案多數是使用者**已判定過**的項目，取其判定作為對照素材；凡為 AI 草稿或未定稿者均註明。

### DA 表：替代方案對照

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Mermaid** | 用近似自然語言的 DSL 描述圖，引擎自動排版輸出 SVG/PNG | 圖表結構能用文字描述；接受引擎預設排版 | 排版受引擎限制、輸出帶「Mermaid 預設樣式」＝slop 來源；複雜佈局難控制 | 快速產出結構圖，但無法達成「出版級」品牌一致性 |
| **draw.io / Excalidraw** | 手動 GUI 拖曳繪圖，可匯出 SVG；draw.io 有 XML 檔案格式 | 需要人工投入時間；Excalidraw 偏手繪風 | 無法由 Agent 直接產出；draw.io 檔案需人工維護 | 品牌與排版可控，但無法被 coding agent 自動化 |
| **Hallmark**（已判定：採用→觀望） | AI Coding Agent 的 UI 設計規範 Skill，生成／審計／重構／提取 4 種能力 | 使用 Claude Code / Cursor / Codex；處理的是網頁 UI 而非圖表 | 資源未排程（觀望）；專注 UI 結構多樣性，非圖表視覺型 | 消除網頁 UI 罐頭感；對圖表產出無直接作用 |
| **OpenDesign**（已判定：採用，可 Local 嘗試） | 檔案化 skills + design systems，讓 coding agent 從自然語言產出可編輯／可預覽／可匯出的設計產出物 | 已安裝任意 coding agent；需能接受檔案化 skill + design-system resolver 架構 | 架構較重（web/daemon/desktop 三件套）；範圍涵蓋 deck/prototype 等多種產物，非專精圖表 | 把設計產出流程檔案化、可控、可匯出；圖表只是其中一類產物 |
| **DESIGN.md**（已判定：Reject/Reserve） | 單一檔案、雙層結構（YAML token + Markdown prose）的設計系統描述格式 | 需具備成熟設計系統、設計師具 prose 撰寫能力 | 無強制執行力；Agent 有不遵循的風險；需持續維護同步 | 跨 session 視覺一致；但因外部條件不成熟被保留 |
| **HyperFrames**（已判定：採用） | 將 HTML + CSS + seekable animation 逐幀渲染為確定性 MP4 | 需把畫面以 HTML+CSS+animation 描述 | 產出為影片，非內嵌圖表 | 把確定性 HTML 轉成穩定影片，品質比多模態穩定；與 diagram-design 的靜態 HTML 輸出同源 |

### 切入點差異分析

```
                    ┌────────────────────────────────────────┐
                    │  問題：Agent 產出出版級圖表的品質        │
                    └────────────────────────────────────────┘
           ┌───────────────┼───────────────┬────────────────┐
           ▼               ▼               ▼                ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐   ┌────────────┐
    │ diagram-   │  │ Mermaid /  │  │ Hallmark / │   │ draw.io /  │
    │ design     │  │ Graphviz   │  │ OpenDesign │   │ Excalidraw │
    │ 解法:      │  │ 解法:      │  │ 解法:      │   │ 解法:      │
    │ 27 視覺型  │  │ 文字 DSL   │  │ 設計規範   │   │ 手動 GUI   │
    │ + 品牌 token│  │ + 自動排版 │  │ Skill      │   │ + 手動對齊 │
    │ + anti-slop│  │            │  │            │   │            │
    │ + CI 驗證  │  │            │  │            │   │            │
    └────────────┘  └────────────┘  └────────────┘   └────────────┘
     專精圖表+品牌    引擎自動化        泛用設計 skill     人類可控但慢
     確定性輸出       但 slop 化      但非專精圖表        無法 agent 化
```

**各方案切入點差異：**

| 方案 | 解決問題的切入點 | 本質 |
|---|---|---|
| **diagram-design** | 專精「圖表」這一個產物類別，用視覺型路由＋品牌 token＋反 slop＋CI 把它做成確定性、可驗證的輸出 | 圖表專用的「設計系統 + 品質閘門」Skill |
| **Mermaid / Graphviz** | 用引擎把文字 DSL 轉成圖，犧牲排版控制換取效率 | 文字→圖的編譯器 |
| **Hallmark** | 從結構與主題層面強制 UI 多樣性，消除網頁罐頭感 | 泛用 UI 反 slop Skill |
| **OpenDesign** | 把整個設計產出流程（skill + design system + artifact store）檔案化、可匯出 | 泛用設計產出平台 |
| **DESIGN.md** | 用單一檔案統一設計 token 與 prose，讓 Agent 讀到一致的設計規範 | 設計規範的序列化格式 |
| **HyperFrames** | 把確定性 HTML 轉成影片，解決多模態產出品質不穩的問題 | 確定性渲染管線 |

### 與第二大腦既有判定的衝突與呼應

**① Hallmark（採用→觀望）——最接近的同類，但判定為觀望。**
- URL: https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Hallmark.md（status: stable, verified: human:fatesaikou 2026-08-09，本人拍板）
- Hallmark 是「反 AI 味設計 Skill」，與 diagram-design 是同一品類（design skill for agent）。他判定 Hallmark「採用」後因**資源而非技術**降級為觀望（四功能的場景試驗未排入下一步清單）。**這對 diagram-design 有直接意涵**：diagram-design 同屬設計 Skill，若他連 Hallmark 的試驗都未排程，diagram-design 也需面對同一資源閘門。**衝突點**：diagram-design 相較 Hallmark 更專精、且附帶 CI 硬性驗證與品牌 onboarding，能否突破 Hallmark 因「未排程」而觀望的卡點，視他是否將其排入下一步清單而定——目前清單中並無此判定。

**② Taste Skill（不採用）——與 diagram-design 高度同構，是最實質的衝突來源。**
- URL: https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md（status: draft, generated.by: ollama-cloud/deepseek-v4-flash，AI 草稿，未經本人 review 的總表；逐檔判定原始來源為各評估檔）
- Taste Skill 是「可移植的 Agent Skill 指令集，覆寫 AI 生成前端的模板化風格」，被判定**不採用**，理由是「過分偏向設計師，知識與經驗儲備不足以運用」。**diagram-design 正是同一機制的圖表版**——它也是一個「覆寫 AI 圖表輸出模板化風格」的 skill。**衝突必須點明**：依他對 Taste Skill 的判準，diagram-design 同樣需要使用者具備足夠的圖表設計知識與儲備才能運用其 full-editorial 變體與品牌系統。**但兩者有實質差異**：diagram-design 的 full-editorial 變體是「內建的確定性模板」，不要求使用者具備設計能力，且品牌 onboarding 從既有網站自動萃取而非要求使用者自述——這有機會規避 Taste Skill 被拒的主因。此推論基於 AI 草稿的總表，需注意原始判定檔的信任層級。

**③ OpenDesign（採用，可嘗試）——上游／並行平台。**
- URL: https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OpenDesign.md（status: stable, generated.by: human:fatesaikou 2026-06-06，本人寫的結論）
- 他已 Accept OpenDesign，理由是「讓 coding agent 產出可編輯、可預覽、可匯出的設計產出物」。diagram-design 可視為 OpenDesign 圖表產物類別的專精子集，**兩者不衝突而是互補**；但若他要在 OpenDesign 的檔案化架構內處理圖表，diagram-design 會與其 design-system resolver 重疊。

**④ DESIGN.md（Reject/Reserve）——前提條件警告。**
- URL: https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/DESIGN.md.md（status: stable, generated.by: human:fatesaikou 2026-07-04，本人寫的結論）
- 他被判 Reject(Reserve) DESIGN.md，主因是「外部條件不成熟：設計流程工程化不成熟、無成熟設計系統、設計師無 prose 能力」+「內部條件不符合套用條件」。**衝突點**：diagram-design 的「品牌 onboarding 自動萃取」與「內建 27 視覺型」**不要求他具備成熟設計系統或 prose 能力**，因此能否不受 DESIGN.md 被拒時所缺的內部條件限制，取決於其實際萃取與模板效果——這正是 diagram-design 與 DESIGN.md 的關鍵差異所在。

**⑤ HyperFrames（採用）——輸出形式同源。**
- URL: https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/HyperFrames.md（status: stable, generated.by: human:fatesaikou 2026-05-31，本人寫的結論）
- 他已 Accept HyperFrames，理由是「將確定性 HTML 變成影片有價值，品質比多模態穩定且成本更低」。diagram-design 的靜態 HTML+SVG 輸出與此信念同源（確定性 > 多模態隨機），**互為補充而非競爭**；若他需要圖表動畫，可將 diagram-design 的 HTML 餵給 HyperFrames 渲染成影片。

**⑥ 技術取捨準則（骨幹）——套用於 diagram-design 的判準。**
- URL: https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md（status: draft, generated.by: claude-code/opus-5，AI 草稿）
- 準則包含：**理解優先**（不穩定或不熟悉就先自己兜）、**MVP→Feature 唯一閘門＝能否影響個人 workflow**、**Reject≠沒價值**、**不追新**。對 diagram-design：他是「資料視覺化」（思考習慣第 39 條）與「溝通設計」（第 55 條）的理解者，圖表品質是他的既有關心點——若「出版級圖表」真的影響他的 workflow，才會進 Feature；否則即使技術優異也只停在理解層。**這是他判定 diagram-design 的最強濾網**，比技術比較更決定採用與否。

### 反證表：diagram-design 的潛在限制

| 限制 | 說明 | 緩解方式 |
|---|---|---|
| **Agent 綁定** | 設計給 Claude Code / Codex / Pi，其他 agent 需手動移植 | 可抽取 SKILL.md 核心規則移植至其他 harness |
| **設計知識前提** | full-editorial 變體與品牌系統的深度客製需使用者具備設計判斷力（同 Taste Skill 被拒主因） | 品牌 onboarding 自動萃取＋內建 27 型模板降低門檻 |
| **無資料庫整合** | 靜態 SVG 輸出，不直接讀資料庫或圖表框架 | 需自行把資料餵給 agent 描述；不處理動態資料 |
| **品牌萃取的準確性** | 自動抓取 dominant palette 有抓錯網站代表色的風險 | 自動做 WCAG AA 檢查兜底；first-run gate 強制人工確認 |
| **資源排程** | 同 Hallmark 觀望邏輯，有因未排入下一步清單而停在理解層的風險 | 依「是否影響個人 workflow」決定，無法靠技術優劣催生 |
| **專案年輕** | 2026-04-16 建立，仍活躍（updated 2026-08-15）但迭代快速 | ADR 與 CI gate 提供穩定性；版本 2.4 顯示持續演化 |

---

## 5. User Q&A

（本輪 R1 為首次產出，使用者無提問，依規範不產出此節。）
