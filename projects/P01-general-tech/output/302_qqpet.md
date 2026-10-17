# QQPet（AnkioTomas/qqpet）技術解析

> 標的：`AnkioTomas/qqpet`（GitHub repo；QQ 宠物跨平台單機復刻版，主要語言 TypeScript，授權 GPL-3.0-only）
> 分析：技術解析助理，Round R1，對應 Original Issue #301（無 §5 User Q&A，本輪尚無提問）
> 前置查證：第二大腦（FATESAIKOU/MyBrain）**無 QQPet／桌面寵物養成／Flash 遊戲復刻／Ruffle／SWF 逆向下之獨立技術評估**（`技術/技術評估/判定總表.md` 129 筆與全 bundle grep 均查無）。本報告事實以 repo 的 GitHub API metadata、README、首頁 `pet.ankio.net`、以及關鍵原始碼（`shared/ai.ts`、`renderer/pet/ai.ts`、`shared/save.ts`、`main/content-pack.ts`、`swf/player.ts`、`main/index.ts`、`resources/asr/README.md`）與公開背景資料為主。
>
> 註：本輪 PR body 附帶的影片（GitHub 一週熱點 135 期）**無字幕軌（transcripts disabled）**，影片觀點與示範內容不可得，全篇不引用影片內容。

---

## 0. 標的事實速覽

| 項目 | 值 |
|---|---|
| repo | `AnkioTomas/qqpet` |
| 描述 | 「QQ宠物单机复刻版(AI)」 |
| 實查 Stars / Forks | **703★ / 109 fork**（issue 快照為 695★，以實查為準） |
| 主要語言 | TypeScript（TS 728K ＞ JS 296K ＞ Objective-C 184K ＞ ActionScript 102K） |
| License | GPL-3.0-only（程式碼；不含 `resources/pet` 美術與 SWF） |
| 建立 / 最後 push | 2026-10-07 / 2026-10-17（10 天內 18 個 release，最新 `v0.7.0-beta.2`） |
| 首頁 | `pet.ankio.net`；topics `qq, qqpet` |
| 支援平台 | Windows / macOS / Linux / Android / HarmonyOS / iOS |

---

## 1. 這個技術解決什麼問題？

**被解決的具體問題：讓已停服的騰訊線上養成遊戲「QQ 宠物」在沒有 Flash Player、也不連騰訊伺服器的條件下，於現代多平台可運行。**

這個問題實際由兩個獨立失效面組成：

| 失效面 | 具體內容 | 為何使遊戲不可玩 |
|---|---|---|
| **播放執行環境失效** | 客戶端內容是 Adobe Flash（SWF/ActionScript）；Adobe 於 2020-12-31 終止 Flash Player 支援，瀏覽器移除外掛 | 現代瀏覽器／作業系統無法直接播放 `resources/pet` 的 SWF |
| **線上服務失效** | 原版玩法（商城、任務、社交、限時活動、企鵝島等）依賴騰訊伺服器；遊戲 2018-09-15 停服 | 無伺服器可連，登入、商店、社交等功能全部中斷 |

### 問題描述中的模糊之處

README 自述為「單機復刻」，但「復刻」一詞在實作上混合了三種不同目標，三者的問題定義不同，須分開看待：

1. **播放層替換**：不重寫內容，改以 Ruffle 執行原版 SWF。
2. **邏輯層重建與去聯網**：逆向重建原版玩法、移除聯網依賴、單機化。
3. **功能追加**：加入原版沒有的 AI 對話與本地 ASR。

「單機復刻」未區分（1）（2）（3）的優先順序與邊界，因此「復刻」的完成度如何界定，屬未定義項。

---

## 2. 這個問題為什麼會發生？（背景）

分「repo 文件明確提到」與「通用技術背景」兩類。

### 2.1 repo 文件明確提到的背景

| 項目 | 內容 |
|---|---|
| 原版時序 | QQ 宠物 2005-09 由騰訊推出，2018-09-15 停服（營運約 13 年） |
| 自述技術路線 | 「基於 **Arctic Penguin T800** 逆向重建」；Flash 內容交 **Ruffle** 播放；跨 6 平台 |
| 授權邊界 | 程式碼 **GPL-3.0-only**；`resources/pet` 的美術與 SWF 版權歸騰訊，**不隨 GPL 覆蓋**；旅行照片版權歸《旅行青蛙·中國之旅》；README 明示僅供學習、勿商用 |

**低信任層級標記**：`Arctic Penguin T800` 僅見於本 repo 及其轉載頁，**無獨立第三方文件佐證**，屬作者自述的逆向標的代號。另一條「2026-07-27 於手機 QQ 以 3D 形象回歸」為單一時點主張，未見多方佐證，同標低信任。

### 2.2 通用技術背景（作者未寫、外部補）

| 背景項 | 內容 |
|---|---|
| **Flash 技術棧被淘汰** | Adobe 於 2020-12-31 終止 Flash Player 支援並封鎖內容執行；瀏覽器移除 NPAPI／PPAPI 外掛。任何依賴 Flash 的舊內容在現代瀏覽器與作業系統無法直接播放。Ruffle 即為以 Rust/WASM 重寫的 Flash Player 替代執行環境。 |
| **線上遊戲停服的兩個失效面** | 客戶端失效（執行環境消失）與伺服器失效（連線、帳號、商城、社交資料消失）屬不同問題，須分別處理。 |
| **SWF 可反編譯** | SWF 是可反編譯的位元組碼，ActionScript 可讀取（JPEXS FFDec 等工具）。這使「不重寫、直接改原檔」與「反編譯後移植」兩條路皆可行。 |
| **內容與外殼可解耦** | SWF 內容為靜態資產，播放器與遊戲邏輯可與外殼程式分離，因此「資源分發」與「程式碼」能各自管理。 |
| **時序與熱度** | repo 建立於 2026-10-07，10 天內 703★、18 個 release，屬高頻更新之新專案。 |

---

## 3. 這個技術是如何解決該問題的？

核心做法：**以 TypeScript（Electron）外殼包住 Ruffle 播放層，直接執行原版 SWF，透過 SWF 補丁與存檔相容把聯網依賴移除，並將可選的 AI／ASR 疊加在外殼層。**

### 3.1 整體分層

```
┌──────────────────────────────────────────────────────────┐
│ 外殼層 Shell：TypeScript + Electron（main/ renderer/ shared/）│
│  ├── 存檔：userData/save.json（相容原版格式）                  │
│  ├── 資源分發：content-pack（.qqpetpack）＋ Git LFS           │
│  └── 已改 SWF（以 FFDec 打補丁）                              │
├──────────────────────────────────────────────────────────┤
│ 播放層：Ruffle（執行原版 resources/pet 的 SWF）               │
├──────────────────────────────────────────────────────────┤
│ 遊戲邏輯：原版 SWF 內 ActionScript ＋外殼改寫的 ExternalInterface│
├──────────────────────────────────────────────────────────┤
│ 可選疊加：AI 對話（OpenAI 相容 API）／本地 ASR                 │
└──────────────────────────────────────────────────────────┘
```

### 3.2 播放層替換：Flash → Ruffle

- 不重寫原版玩法，改以 **Ruffle**（Rust/WASM 實作的 Flash Player 替代）執行 `resources/pet` 內的 SWF。
- 這是解決「播放執行環境失效」的直接手段。

### 3.3 聯網去除與 SWF 補丁（JPEXS FFDec）

以 JPEXS FFDec 對原版 SWF 打補丁，具體三項：

| 補丁 | 目的 |
|---|---|
| 隱藏聯網按鈕 | 移除指向已停伺服器的入口 |
| 農場「金幣 → 元寶」 | 改寫貨幣顯示，配合無伺服器情境 |
| 小遊戲螢幕尺寸改走 `ExternalInterface` | 由 Ruffle 回傳播放器自身尺寸，解決尺寸取得問題 |

### 3.4 存檔相容

- 格式沿用逆向標的的 `config.json`（`petInfoData`）；存檔落於 `userData/save.json`。
- **欄位名含拼錯的 `petComputedlInfo` 原樣保留**，使舊存檔免轉譯載入。
- 相容原版導入：首次選蛋頁可直接匯入原版存檔。

### 3.5 資源分發：內容與外殼分離

- `resources/pet`（原版 SWF／美術）走 **Git LFS**，與外殼程式分離，另以 content pack 形式分發：
  - 完整版（約 450–520 MB）隨安裝包自帶。
  - 精簡版（約 120–160 MB）於首次啟動下載或匯入 `QQPet-content-*.qqpetpack`。
- 支援增量包（`base`）與 **SHA-256 校驗**。

### 3.6 單機社區與可選 AI／ASR

| 模組 | 機制 |
|---|---|
| **企鵝島** | 單機社區功能（`ui/island.ts`）；另有 LAN 互訪機制 |
| **AI（可選）** | 接**任意 OpenAI 相容接口**（`/models`、`/chat/completions`、`Bearer` key、60s timeout）；無 key 即退回原版台詞。用途：寵物閒聊、改寫台詞（保留原句數字／時間／物品）、點評／翻譯剪貼簿文字。persona 由 `petComputedlInfo` ＋狀態＋日期即時生成；含小模型去重（LOOP 正則）與 think 標籤剝除 |
| **本地 ASR** | `sherpa-onnx-node` ＋ Paraformer-zh int8／CT-Transformer 標點，模型約 228+285 MB，**不隨倉庫分發**，缺失不影響其他功能 |

### 3.7 功能範圍（復刻內容）

養成（選蛋／成長／饑餓／清潔／心情／健康／就醫／死亡復活／重生換性別）、日常（打工／上學升學／全國旅遊 35 城）、物品商城／背包／限時／粉鑽／情侶、任務與郵件、活動（池塘／農場／密室／6 類 101 小遊戲）、企鵝島單機社區、天氣播報。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

先將問題拆成兩個可獨立選擇的子問題：

- **子問題 A：讓既有 Flash 內容在現代平台執行**（播放執行環境失效）。
- **子問題 B：讓已停服的線上服務／玩法重新可用**（線上服務失效）。

### 4.1 替代方案條列

| # | 方案 | 解的子問題 | 一句話切入點 |
|---|---|---|---|
| 1 | **Ruffle（本專案採用）** | A | 以 Rust/WASM 重寫 Flash Player，直接執行原版 SWF，保留原內容 |
| 2 | **原生重寫／反編譯移植** | A + B | 反編譯 SWF 取 ActionScript 後重寫，或依行為 clean-room 重建 |
| 3 | **私有伺服器模擬／連線重導** | B | 保留原客戶端與 Flash，重寫伺服器端協議或將請求導向自建伺服器 |
| 4 | **原 Flash 執行環境封存** | A（限保存） | Flashpoint／舊 projector／VM 內跑原 Flash，不下架原環境 |

### 4.2 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Ruffle（本專案）** | 以 Rust/WASM 重寫 Flash Player，直接執行原版 SWF | SWF 完整可得；Ruffle 對該 SWF 用到的 ActionScript／`ExternalInterface` 支援度足夠 | 支援度缺口需逐支 SWF 補丁；跨平台外殼仍須自建；美術版權仍歸騰訊、授權邊界須自行劃定 | 不重寫玩法即可在現代平台重現原內容 |
| **原生重寫／反編譯移植** | 反編譯 SWF 取 ActionScript，重寫為現代語言／引擎；或 clean-room 依可觀察行為重建 | 有可反編譯的 SWF 或可觀察的原版行為；clean-room 須嚴格隔離來源 | 成本高、週期長，易與原版行為漂移；美術須自行重做或沿用受版權限制資源 | 執行環境與原版完全脫鉤，長期可維護 |
| **私有伺服器模擬／連線重導** | 保留原客戶端與 Flash，重寫伺服器端協議或導向自建伺服器 | 客戶端通訊協議可逆向；有可執行原客戶端的 Flash 環境 | 法律風險高（未經授權）；協議逆向成本高；須持續對抗客戶端檢查 | 可保留原版完整線上玩法與社交 |
| **原 Flash 執行環境封存** | Flashpoint／舊 projector／VM 內跑原 Flash | 須保存原 SWF 與可用的舊執行環境 | 無法跨平台、無法在現代 OS 直接跑、安全風險高 | 以最小改動保存原內容，不符跨平台單機目標 |

### 4.3 切入點差異

- **Ruffle**：只解子問題 A（播放層替換），保留原內容，不動玩法邏輯。
- **原生重寫**：同時解 A 與 B（連玩法邏輯一起重做），成本最高但執行環境可控。
- **私有伺服器**：解子問題 B（服務層重建），保留原客戶端與 Flash 依賴。
- **封存**：不解問題，只保存內容。

QQPet 選擇 Ruffle ＋去聯網補丁，等同「解 A ＋以補丁局部解 B（移除聯網需求）」，而非走「私有伺服器」或「原生重寫」路線。

### 4.4 第二大腦對照（FATESAIKOU/MyBrain）

**第二大腦裡沒有這個主題**：QQPet／桌面寵物養成／Flash 遊戲復刻／Ruffle／SWF 逆向，於 `技術/技術評估/判定總表.md`（129 筆）與全 bundle grep 均查無。以下僅取既有**一般性取捨準則**作對照，不視為他評過 QQPet 的結論。

| 來源檔（信任層級） | 內容 | 與本技術的關係 |
|---|---|---|
| [技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md)（`骨幹`；status `draft`；`generated.by: claude-code/opus-5` → **未經他 review 的 AI 草稿**） | 理解優先（不夠穩定或不熟悉就先自己兜，MVP 是理解達成的驗證點）；**MVP→Feature 唯一閘門＝能否影響我個人的 workflow**；Reject ≠ 沒價值；汰換看上游死沒死（他不追新） | QQPet 屬娛樂內容、不影響其個人 workflow，依此準則不會進 Feature。Ruffle 路線本身與「不追新、理解優先」相容 |
| [判定總表](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md)（`骨幹`；`draft`；`generated.by: ollama-cloud/deepseek-v4-flash` → **未經他 review 的 AI 草稿**） | 129 筆技術判定的索引；分類為採用／試用／觀望／不採用／未判定 | **查無** QQPet 及同類（Flash 遊戲復刻／模擬器／逆向重建）之任何條目 |
| [reverse-skill](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/reverse-skill.md)（status `draft`；`generated.by: process:learn-gh-agent` → **AI 草稿未經他 review**） | 逆向／滲透／安全研究 skill 路由包，判定**不採用**；理由為「沒必要學一個 skill（依理解優先原則傾向自兜）」「沒打算深入看資安，無法信任其產出」 | **衝突點**：本技術的核心動作是逆向重建，而第二大腦對「逆向工程類工具」的判定是不採用。惟兩者不同軸——reverse-skill 拒的是「以現成 skill 包取代自身理解」與資安滲透領域，QQPet 是以逆向為手段、產物為遊戲本身。依「Reject ≠ 沒價值」，reverse-skill 的「路由單一事實源＋工具索引＋回歸測試」設計方向仍可抽取。此衝突不構成對 QQPet 的否定，但顯示「逆向工程」本身不在他現行優先清單 |
| [統一的兩端稅](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/統一的兩端稅.md)（`draft`；`generated.by: claude-code/opus-5` → **未經他 review 的 AI 草稿**） | 判準一句：「這兩個是同一件事的不同實作，還是不同的事？」前者統一是對的，後者統一是錯的 | QQPet 以**同一份原版 SWF 資源**替換播放器（Ruffle 取代 Flash Player）＝同一件事的不同實作，符合統一；但把 AI 對話、本地 ASR、企鵝島收進同一外殼＝把不同的事統一，屬該準則標示的風險結構 |
| [下一步清單](https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md)（`骨幹`；`draft`；`generated.by: claude-code/opus-5` → **未經他 review 的 AI 草稿**） | 技術側進行中項目（AiStorage、MyLinuxPool、個人 AiAgent 入口、LLM 內部架構學習等） | **無任何遊戲／寵物相關動作** |

**結論**：對照後，Ruffle 的技術路線與其「理解優先、不追新」準則相容；但 QQPet 作為娛樂產品不通過其「MVP→Feature ＝ 能否影響個人 workflow」閘門，故第二大腦視角下其用途偏向**機制抽取來源**（內容與外殼分離、存檔向後相容、SWF 補丁等），而非採用標的。

---

## 附錄：資料來源與信任層級

| 來源 | 用途 | 信任層級 |
|---|---|---|
| GitHub API（repo metadata / releases / contributors / languages） | stars、license、時序、語言、發佈節奏 | 一手實查 |
| repo `README.md`、`package.json`、首頁 `pet.ankio.net` | 定位、功能、建置、授權 | 一手（作者自述） |
| 關鍵原始碼（`shared/ai.ts`、`renderer/pet/ai.ts`、`shared/save.ts`、`main/content-pack.ts`、`swf/player.ts`、`main/index.ts`、`resources/asr/README.md`） | AI／存檔／資源分發／播放機制 | 一手實作 |
| 公開背景（QQ 宠物停服時點、Flash 終止支援時點、SWF 反編譯工具） | 背景脈絡 | 通用技術背景 |
| 「Arctic Penguin T800」「2026-07-27 3D 回歸」 | 逆向標的代號、回歸時點 | **低信任**：單源、無第三方佐證，已於 §2 標記 |
| GitHub 一週熱點 135 期影片 | 影片觀點／示範 | **不可得**（無字幕軌），未引用 |
