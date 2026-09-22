# Tinycast —— 完全原生 macOS 啟動器技術分析

> 標的：https://github.com/abue-ammar/tinycast
> 分析：`tech-research-agent`，2026-09-21
> 前置查證：第二大腦（FATESAIKOU/MyBrain）無 `tinycast` 此主題、也無任何 launcher 域（Raycast／Alfred／Spotlight）的既有判定。本報告事實以 GitHub 官方 repo 文件為主，個人適用性判斷對照第二大腦的技術取捨準則、硬體脈絡（MyLinuxPool「日常操作都在 Mac 上」）與少數沾到 macOS 但不同域的評估。

---

## 1. 這個技術解決什麼問題？

Tinycast 解決的問題是：**macOS 使用者在日常操作中，被「啟動、切換、查找、貼上、計算、排程」等分散在各種 app 與系統能力裡的高頻動作綁住，缺乏一個單一入口把它們收攏，而既有的收攏方案（Raycast／Alfred）是閉源付費訂閱、且多數採 Electron 重型架構**。

具體拆成三層：

1. **操作碎片化**：開 app、切視窗、查檔案、貼剪貼簿、算數、查字典、開網頁、跑行事曆、叫 emoji……每一件事都要各自切到對應工具或記住對應快捷鍵，缺少統一入口。
2. **收攏方案被商業化綁住**：市場主流（Raycast、Alfred）是閉源＋訂閱制，使用者無法自由檢視與修改，且需支付持續費用；這與「想要一個乾淨、可掌控、免費的啟動器」的目標衝突。
3. **原生性與資源成本**：Electron 系的啟動器記憶體耗用高（動輒數百 MB）、打包了整顆 Chromium；對追求輕量、低 footprint、無 telemetry 的使用者是負擔。

Tinycast 的定位是「一個 hotkey，everything under 100 MB RAM」——SwiftUI＋AppKit、零第三方相依、無 Electron、無 telemetry，且可**原生執行既有 Raycast extensions、從 Raycast 匯入設定**，以此吸納 Raycast 生態而不需付其費用。

### 問題描述的模糊之處

- 「啟動器」的範圍邊界未硬性定義——Tinycast 已把範圍擴張到剪貼簿、行事曆、Notes、emoji、視窗管理、AI chat 等，已超過傳統 launcher 範疇，成為「命令面板＋工作流整合器」。這使「它到底解決哪一類問題」需視使用者 workflow 而定。
- 「<100 MB RAM」是作者設定的硬性目標（repo AGENTS.md Non-negotiables），但實際記憶體會隨啟用的 feature 數量（如跑 Raycast extension）浮動，README 未給出分情境的數字。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章明確提到的背景

- **零相依、無 Electron 作為設計前提**：repo 的 AGENTS.md 把「RAM < 100 MB 鐵則」「零第三方相依」「無 telemetry」列為 Non-negotiables，且架構分層由 `Tests/` harness 編譯 shipped 來源強制，不是行銷宣稱。
- **「latest-only always」Posture**：Tinycast 只支援單一最新 macOS（26+），不提供相容層。repo 明示這是它保持精簡 codebase 的主因——不背相容包袱，就能刪減而非兼容。
- **可原生跑 Raycast extensions**：同一 `package.json`＋prebuilt CommonJS bundle，以 **JavaScriptCore**（macOS 內建、零 binary 成本）＋自製 `@raycast/api` shim 與 Node polyfills 渲染，`__slot`／`$fn` 機制把 React tree 序列化給 Swift。這使「吸納 Raycast 生態」成為技術上可行。

### 通用技術背景（補充）

- **Launcher 的演化**：從系統內建 Spotlight（僅搜尋、無法擴充），到 Alfred（可擴充 workflow、閉源付費）、Raycast（extensions 生態、閉源訂閱制）。使用者面對的是「免費但貧弱」vs「強大但閉源付費」的兩難。
- **Electron 的代價**：跨平台 app 以 Chromium 為底座換取開發速度，代價是記憶體與磁碟 footprint 大、啟動慢、telemetry 常內建。Tinycast 走 SwiftUI＋AppKit 純原生路線正是反此趨勢。
- **Raycast extensions 生態的價值**：Raycast 累積了大量第三方 extensions（GitHub、Slack、Notion 等）。Tinycast 的相容策略把「生態」與「閉源訂閱」分離——取其擴充、免其費用。

---

## 3. 這個技術是如何解決該問題的？

核心做法是「**純原生（SwiftUI＋AppKit）＋ 分層架構強制精簡 ＋ JavaScriptCore 相容 Raycast 生態**」：

```
PURE（Foundation-only，環境全注入）
  → EFFECT（AppKit / CGEventTap / URLSession）
  → OBSERVABLE（39 stores，Observation）
  → VIEW（SwiftUI）
      ↑ 由 Tests/ harness 編譯 shipped 來源強制分層
  AppCore.shared = 單一 wiring point
```

### 機制細節

1. **分層強制（PURE→VIEW）**：`Model/` 層不可 import AppKit/SwiftUI；Swift 6 的 data-race 是硬錯誤；`AppCore.shared` 是唯一 wiring point。由測試 harness 編譯「實際出貨的來源」來保證分層不被破壞——精簡不是靠意志，是靠編譯期約束。
2. **低記憶體的結構性保證**：無 Electron、零第三方相依、無 telemetry，配合 SwiftUI 原生渲染，讓 <100 MB 的目標有結構性基礎；Carbon 僅用在兩個 capability-gap（`RegisterEventHotKey` 全域 hotkey、`TIS` 輸入來源），其餘全走現代 API。
3. **Raycast 生態相容**：以 JavaScriptCore（macOS 內建 JS 引擎，無需打包 Node）執行 prebuilt CommonJS bundle，自製 `@raycast/api` shim 與 Node polyfills 覆蓋 extension 所需 API；React tree 透過 `__slot`／`$fn` 序列化給 Swift 渲染。此功能**選配、確認後才啟用、不隨 backup**。
4. **隱私預設**：無 telemetry、offline by default；AI chat 功能**預設關閉**，需 consent-gated 才啟用、不隨 backup 授權；clipboard history 僅存本機。
5. **功能廣度**：App launcher、global/per-app hotkeys、Spotlight 檔案搜尋（不建自有 index，直接走系統）、字典、剪貼簿歷史、計算機、Quicklinks、Apple Shortcuts、Snippets、自訂命令、視窗管理（34 種 Rectangle 式動作）、行事曆、Notes、emoji、Quick Actions。

### 工程現況（成熟度佐證）

- repo 2026-06-29 創建（約 3 個月）但極活躍：7,023 stars、daily commits，近期功能含 extensions menu bar、Raycast TLS、clipboard pinned、window commands。
- 文檔齊全：`docs/` 含 architecture／standards／testing／ui／development／release／signing ＋ 26 個 feature 文件；CONTRIBUTING 以「RAM<100MB、zero-leak、before/after 影片」為 PR 硬門檻，feature set 刻意封閉（「another launcher has it」不是新增理由）。
- LICENSE 全文確認為 **AGPL-3.0**（gh metadata 回 `other`，以檔全文為準）；NOTICE 僅列品牌 icon（Simple Icons CC0／Lobe MIT）。
- 無 CI，靠本地 harness＋CodeRabbit 把關。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 第二大腦查證結果（先讀判定總表再讀個案）

第二大腦無 `tinycast` 此主題，也**無任何 launcher 域（Raycast／Alfred／Spotlight）的既有評估**。同屬「macOS 或工具」但不同域的相關判定如下：

| 標的 | 判定 | 來源／信任層級 |
|---|---|---|
| **apple container**（macOS 原生 Linux 容器） | **不採用**——還不成熟，但方向可嘉；抽取 per-container 獨立輕量 VM 隔離、OCI 互通、Swift 原生整合 | [apple container.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/apple%20container.md)（`generated.by: human:fatesaikou`，`status: stable`，**本人定案**） |
| **omlx**（Apple Silicon 專用 OS） | **不採用**——他沒有高性能 Mac，能跑 LLM 的 Mac 太貴，與 NVIDIA + Linux 體系比不划算 | [omlx.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/omlx.md)（`generated.by: human:fatesaikou`，`status: stable`，**本人定案**） |
| **terminal-browser**（瀏覽器搬進終端機） | **不採用**——方向相反（瀏覽器進終端機而非終端機進瀏覽器） | [terminal-browser.md](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/terminal-browser.md)（`draft`，**未 review**） |

**判定總表**為索引（`generated.by: ollama-cloud/deepseek-v4-flash`，`status: draft`，**AI 草稿**）。技術取捨準則為骨幹檔（`status: draft`，`generated.by: claude-code/opus-5`，但「原話：」引號內為使用者本人結論）。

**硬體脈絡**：`MyLinuxPool.md`（`generated.by: human:fatesaikou`，**本人實作文件**）明載「日常操作都在 Mac 上」——使用者的日常主力機是 Mac，launcher 屬他每天會碰的 workflow 工具，與「Apple Silicon 跑不起高階 LLM」（omlx Reject 理由）是兩條獨立的軸。

**與 Tinycast 結論的關係（查證最有價值的衝突點）**：

| 使用者準則 | 準則內容 | 與 Tinycast 的關係 |
|---|---|---|
| **① 理解優先** | 不夠穩定或不熟 → 先自己兜，MVP 是理解驗證點，目的在理解本質非省成本 | Tinycast repo 極新（3 個月）、單人維護——**這正是「先自己兜」的觸發條件**，而非「用現成」的論據 |
| **② MVP→Feature 閘門** | 唯一閘門＝能否影響個人 workflow | launcher 是 daily workflow 工具，若他確實每天用會直接命中閘門；但他**從未評估過任何 launcher**，無既有結論 |
| **④ 汰換：不追新** | 只看上游死沒死，不看有沒有更好的 | 潛在衝突：Tinycast 是「更新的替代品」，依「不追新」他不會只因「Raycast 更成熟」就換；但 Raycast 是**閉源付費**（非「能跑就不動」的既用工具），兩者性質不同 |
| **③ Reject≠沒價值** | 被拒仍抽取需求理解與方案方向 | 即便不採用，Tinycast 的「原生零相依＋JS runtime 相容生態＋latest-only 精簡」是可抽取的解法方向 |

### 替代方案與 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Raycast** | 閉源訂閱制啟動器，強大的 extensions 生態、workflow、clipboard 等 | 需接受持續付費訂閱與閉源；需接受 telemetry；功能深度要求高 | 閉源不可檢視修改；訂閱成本；資源佔用較高（Electron 系） | 開箱即用的成熟完整啟動器；但與「免費、可掌控、無 telemetry」目標衝突 |
| **Alfred** | 閉源買斷制啟動器，workflow／Powerpack 擴充 | 需一次付費（Powerpack）；閉源；偏好其 workflow 語法 | 閉源；無 Raycast 那麼大的第三方 extension 市場；更新較慢 | 穩定成熟、單次買斷；但閉源且擴充生態較窄 |
| **Spotlight（系統內建）** | macOS 內建啟動＋檔案搜尋（Spotlight index） | 僅需基礎啟動／查找；不需擴充、不需跨功能收攏 | 無法擴充、無剪貼簿／計算／視窗管理等；無 hotkey 彈性 | 零成本、零額外 footprint；但功能貧弱，無法作為工作流整合器 |
| **Tinycast（本標的）** | 純原生（SwiftUI＋AppKit）、零相依、無 telemetry、AGPL-3.0，以 JavaScriptCore 原生跑既有 Raycast extensions | 需在 macOS 26+（latest-only）；接受極新 repo 的成熟度風險；願自行維護/自建 | 只支援單一最新 macOS，鎖死升級節奏；單人維護，bus factor 低；功能深度待時間累積 | 免費、開源可檢視、<100MB 輕量、可吸納 Raycast 生態；但成熟度與長期維護有風險 |

### 各方案切入點差異

- **Raycast**：切入點是「閉源訂閱＋最強 extension 生態」，用商業模式與生態厚度取勝，代價是閉源與費用。
- **Alfred**：切入點是「閉源買斷＋workflow 語法」，單次付費，但生態擴充較窄。
- **Spotlight**：切入點是「系統內建零成本」，功能貧弱，無擴充與收攏能力。
- **Tinycast**：切入點是「開源免費原生 + 相容既有 Raycast 生態」——把「生態」與「閉源訂閱」分離，是唯一同時滿足「免費、可掌控、無 telemetry、還能用 Raycast extensions」的方案。

> 結論：Tinycast 的獨特切入點是「**以純原生 + AGPL 開源，正面對抗閉源訂閱制啟動器，同時用 JavaScriptCore 相容策略吸納 Raycast 生態**」。對使用者而言，適用性落在兩條準則的張力上：launcher 是 daily workflow 工具（②閘門可能命中，且他日常就在 Mac 上），但 repo 極新、單人維護、只支援單一最新 macOS，這正是「①理解優先先自己兜」的觸發情境，且與「④不追新」相抵。報告不替使用者下採用/拒絕判定，僅指出：若要試，Tinycast 的「原生零相依＋JS runtime 相容」是最值得抽取的解法方向；若他在意長期維護與 macOS 升級鎖定，需自行衡量（判斷屬他 workflow 閘門與汰換準則的事）。
