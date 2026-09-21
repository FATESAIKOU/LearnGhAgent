# 265_R1_step2-plan_C1

## 狀況理解

- R1 首次調研，標的為 GitHub repo `bilawalsidhu/gods-eye-view`（3D 地球觀測台）。C1 為 Step 2 第一個 sub-step，任務是取得 repo metadata 與主要文件，作為後續分析（問題定義、背景、機制、替代方案）的原始素材。
- Step 1 已確認：MyBrain 無此標的評估紀錄，屬首次調研，報告僅做機制分析（§1–§4），不下個人採用結論。
- C1 範圍：repo metadata、README、資料來源文件、架構文件、依賴清單，並補查背景脈絡。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` 取 metadata | 取得基本盤（描述、語言、星數、fork、授權、建置時間） | 定位 repo 規模與成熟度 | 描述：瀏覽器中的偵察衛星模擬器，資料為真；JS 為主要語言；37,834 stars／7,623 forks；homepage maptheworld.ai；license=Other；建於 2026-06-22 |
| `gh api readme` 解碼 README（521 行） | 掌握產品定位、功能、架構、授權 | 理解技術「解決什麼、怎麼做」 | 完整取得：15 圖層、voice AI（OpenAI Realtime）、架構、6 組 API key、成本、授權（MIT code＋data carve-out）、「不做的界線」（無人名搜索/人臉辨識） |
| 抓 `docs/CURRENT-STATE.md`、`docs/INFRASTRUCTURE-LAYERS.md` | 取得架構與可重用模組說明 | 理解系統分層與設計 | 取得：狀態 owners 化、Director 場景、voice ownership 架構、`createInfrastructureLayers` 可重用介面 |
| 抓 `DATA_SOURCES.md` | 列舉所有資料源與其授權 | 掌握「公開數據」的真實來源與授權風險 | 取得 30+ 即時資料源（OSM、Google Map Tiles、OpenSky、adsb.lol、AISStream、CelesTrak、USGS、TomTom、Open-Meteo、GDELT、各城市 CCTV API…）與各自授權/限制 |
| 抓 `package.json` dependencies | 確認技術棧 | 驗證 README 所述、補足核心依賴 | 核心：`cesium@1.124`、`satellite.js@6`（SGP4）、`mgrs`、`egm96-universal`、`@mapbox/vector-tile`、`pbf`；dev：`vite@6`、`puppeteer`；另見 exports 對外發布多個可重用子模組 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| metadata | gh repo view 欄位是否齊全 | 齊全：描述、語言、stars/forks、license、建置時間、homepage 皆取得 |
| 產品定位 | README「Why This Exists」 | 單一探索式地球，整合航班/船舶/衛星/地震/交通/CCTV/無線電，全部公開即時資料；資料即時或定期更新，交通為模擬、CCTV 姿態為估算 |
| 技術棧 | package.json vs README 宣稱 | 一致：無 framework、CesiumJS、Vite、OpenAI Realtime；衛星用 satellite.js SGP4 |
| 授權結構 | README＋DATA_SOURCES | code 為 MIT；第三方資料各自授權並 carve-out（如 TeleGeography 非商用、OpenSky 非商用、Google ToS） |
| 架構可重用性 | INFRASTRUCTURE-LAYERS.md | 已將 datacenter/dam 等基礎設施層抽成可重用 `createInfrastructureLayers` factory，並經 package `exports` 對外發布 |
| 背景脈絡 | README 歷史與定位 | 源自 viral YouTube series（WorldView）改開源、2026-08 GitHub Trending #1、Product Hunt #8；hosted 版由 Halfpixel 提供 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| C1 素材範圍 | 只抓 README vs 抓 README＋DATA_SOURCES＋架構 docs＋deps | 抓齊主要文件 | 標的的核心是「公開數據融合＋3D 呈現＋語音 agent」，單靠 README 不足以支撐 §3 機制分析與 §4 替代方案；DATA_SOURCES 是理解其授權/資料來源的關鍵 |
| 是否深入 src/ 逐層讀碼 | 逐檔案讀 src vs 以文件層級為準 | 以文件層級為準，src 留待 C2 | C1 任務即「metadata 與主要文件」；逐層讀碼屬後續 sub-step，避免 C1 膨脹超 6000 字 |
| 技術名命名 | gods-eye-view / gods-eye-view-3d-earth | gods-eye-view（沿用 repo 名） | 與 Step 1 決策一致，report 檔名採 repo 名 |
| 背景補查 | 依 README 自述 vs 外部搜尋 | C1 以 repo 自述為主，外部搜尋留待 C2 | README 已含充分背景（歷史、定位、hosted）；外部背景（GEOINT/OSINT 趨勢、替代品如 Google Earth Cesium 等）屬下一步補充 |
