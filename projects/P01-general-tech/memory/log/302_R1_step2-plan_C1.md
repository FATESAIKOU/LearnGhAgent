# 302_R1_step2-plan_C1

## 狀況理解

Step 2 C1：取得技術標的 repo metadata 與主要文件。標的＝`AnkioTomas/qqpet`（QQ 宠物开源复刻版，TypeScript）。R1 首次調研、非追問。C1 需盤點：repo metadata 與時序、README 全文、首頁文件、關鍵原始碼（架構與 AI／存檔／資源分發機制）、背景脈絡（原版 QQ 宠物史、Ruffle、逆向母體）。供 C2 補核心機制深化（Ruffle 播放、企鵝島、反混淆/逆向流程）與替代方案 DA 表。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` + `gh api repos/AnkioTomas/qqpet` | 取 repo metadata | stars/license/時序 | 703★、109 fork、**GPL-3.0**、TypeScript、created **2026-10-07**、pushed 2026-10-17、open issues 17、branch `main`、size 6148 KB、topics `qq,qqpet`、homepage `pet.ankio.net` |
| `gh api .../releases`（18 筆） | 取發佈節奏與產物 | 更新頻率、平台覆蓋 | 最新 `v0.7.0-beta.2`（2026-10-17），10 天內 18 個 release；每筆含 dmg/AppImage/deb/apk/hap/ipa + `content.qqpetpack`（約 375 MB）；**極高頻** |
| `gh api .../contributors`、`/languages` | 取人力與語言分布 | 主要語言佐證 | contributors：AnkioTomas 227、Torrekie 18、zxzx123x456 14、其餘 4 人；語言 TS 728K＞JS 296K＞Objective-C 184K＞ActionScript 102K |
| 讀 `README.md`（207 行）+ `package.json` | 取定位、功能、建置契約 | 一手文件 | 見下 |
| 讀 `pet.ankio.net/` 首頁 | 取使用指南與作者自述 | 一手定位 | 「把 QQ 宠物请回桌面」；單機、本地存檔、AI 可選 |
| 讀關鍵原始碼（`shared/ai.ts`、`renderer/pet/ai.ts`、`shared/save.ts`、`main/content-pack.ts`、`swf/player.ts`、`main/index.ts`、`resources/asr/README.md`） | 取機制一手事實 | AI／存檔／資源分發機制 | 見下 |
| 搜「QQ宠物 停服」「Arctic Penguin T800」 | 補背景脈絡 | 原版史與母體 | 見下 |

**關鍵事實整理**

| 面向 | 內容 |
|---|---|
| 定位 | 「QQ 宠物跨平台复刻（Windows/macOS/Linux/Android/HarmonyOS/iOS），基於 **Arctic Penguin T800** 逆向重建」；Flash 內容交 **Ruffle** 播放；README 自述「单机复刻」，與 issue 描述一致 |
| 時序 | repo 極新（2026-10-07 建立，10 天內 703★、18 release）；`package.json` version 停留 `0.1.0`，與 release `v0.7.0-beta.2` 不符（版本欄未同步） |
| 功能 | 養成（選蛋/成長/饑餓/清潔/心情/健康/就醫/死亡復活/重生換性別）、日常（打工/上學升學/全國旅遊 35 城）、物品商城／背包／限時／粉鑽／情侶、任務與郵件、活動（池塘/農場/密室/6 類 101 小遊戲）、**企鵝島單機社區**、天氣播報 |
| AI（可選） | 接**任意 OpenAI 相容接口**（`/models`、`/chat/completions`、`Bearer` key、60s timeout）；無 key 即退回原版台詞。用途：寵物閒聊、改寫台詞（保留原句數字/時間/物品）、點評／翻譯剪貼簿文字。persona 由 `petComputedlInfo`＋狀態＋日期即時生成；含小模型去重（LOOP 正則）與 think 標籤剝除 |
| 語音 | 另有**本地 ASR**（`sherpa-onnx-node`＋Paraformer-zh int8／CT-Transformer 標點，模型約 228+285 MB，**不隨倉庫分發**，缺失不影響其他功能） |
| 存檔 | 格式沿用原版 Arctic Penguin T800 的 `config.json`（`petInfoData`）；**欄位名含拼錯的 `petComputedlInfo` 原樣保留**以求舊存檔免轉譯載入；`userData/save.json`，相容原版導入、首次選蛋頁可直接匯入 |
| 資源分發 | `resources/pet`（原版 SWF/美術）走 **Git LFS**，且**與外殼分離**成 content pack：完整版（450–520 MB）自帶；精簡版（120–160 MB）首啟下載／匯入 `QQPet-content-*.qqpetpack`，支援增量包（`base`）+SHA-256 校驗 |
| 已改 SWF | 以 JPEXS FFDec 打補丁：隱藏聯網按鈕、農場「金幣→元寶」、小遊戲螢幕尺寸改走 `ExternalInterface`（Ruffle 回傳播放器自身尺寸） |
| 授權邊界 | **程式碼 GPL-3.0-only**；**不覆蓋** `resources/pet` 的美術／SWF（版權歸騰訊）與旅行照片（歸《旅行青蛙·中國之旅》）；README 明示僅供學習、勿商用 |
| 背景（原版） | 騰訊 QQ 宠物 2005-09 推出、2018-09-15 停服（13 年）；2026-07-27 於手機 QQ 以 3D 形象回歸 |
| 背景（母體） | 「Arctic Penguin T800」僅見於本 repo 及其轉載頁，**無獨立第三方文件**（作者自稱的逆向母體代號，存疑處須在 Step 3 注記） |

**待 C2 補**：Ruffle 架構與 SWF 播放／補丁細節、企鵝島（`ui/island.ts` 69 KB）與 LAN 互訪機制、`tools/deobfuscate` 反混淆流程、替代方案 DA 表（Ruffle vs 原版 Flash 插件／自製原生渲染；單機復刻 vs 私有伺服器重連）。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata | stars/license/時序/語言/branch | 完整（**703★，與 issue 的 695★ 有時間差，以實查為準**） |
| 主要文件 | README 全文＋首頁＋package.json | 取得定位、功能、建置、授權 |
| 核心機制 | AI／存檔／資源分發／播放原始碼 | 取得一手實訊（OpenAI 相容、存檔相容拼錯欄位、content pack） |
| 背景脈絡 | web 搜尋原版史與母體 | 原版時序取得；母體無第三方佐證，已註記 |
| 資訊缺口 | 影片逐字稿 | 無字幕軌、不可得，維持不臆造 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 資料來源 | clone 全 repo／gh api＋raw 逐檔／只讀 README | gh api metadata＋raw 抓 README 與 6 支關鍵檔 | 機制不在 README；resources 由 LFS 管理、體積大，免 clone 開銷 |
| 調研深度 | 只文件／文件＋原始碼 | 文件＋關鍵原始碼 | 「如何解決問題」須看實作，二手教學與轉載頁可靠性低 |
| star 數 | 沿用 issue 的 695／實查 | **實查 703 並註記差異** | issue 為 2026-10-17 舊快照，repo 高頻變動 |
| 母體可信度 | 當既有事實／標為存疑 | **標為作者自述、無第三方佐證** | 避免把未查證代號寫成公認事實 |
| 機制深化與替代方案 | C1 一併處理／留 C2 | 留 C2 | C1 目標為 metadata 與主要文件盤點 |
