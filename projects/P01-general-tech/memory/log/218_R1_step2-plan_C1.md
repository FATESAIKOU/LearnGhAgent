# 218_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認調研標的為 **Okdo ROCK 3 C Model C 1GB 單板電腦**（RS 商品型號 RS112-D1W2P1，RS品番 249-3157），屬 Radxa ROCK 3 系列的 SBC，非 GitHub repo。使用者自述用過樹莓派與 NVIDIA 開發板，但不知此板為何物、能幹嘛。本 sub-step C1 依 document skill 標準動作執行：此標的非 GitHub repo，故改以**官方產品頁 + 官方 docs** 取代 gh repo view，取得硬體 metadata、規格文件與品牌背景。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 do/skills/document/SKILL.md | 確認標準調研流程 | 依規範執行 | 規範確認：metadata → 主要文件 → 背景脈絡；非 repo 標的應改用官方網頁 |
| 抓 Radxa 官方產品頁（radxa.com/products/rock3/3c/） | 取得硬體「metadata」（定位、SoC、規格總覽） | 掌握定位與核心規格 | 取得：Rockchip **RK3566**、四核 Cortex-A55 1.6GHz、Mali-G52-2EE GPU、LPDDR4 1/2/4GB、WiFi5/BT5 或 WiFi6/BT5.4、雙 OS 支援、HMI/機器人/智慧家庭等應用情境 |
| 抓 Radxa docs ROCK 3C 主頁（docs.radxa.com/en/rock3/rock3c/） | 取得詳細規格表（Features） | 掌握精確規格供報告引用 | 取得完整 Features：CPU/GPU/RAM/儲存（eMMC+microSD）/1080P@60 HDMI、2-lane MIPI DSI、Gigabit+PoE、WiFi/BT、USB2.0 OTG×1+Host×2+USB3.0 Host×1、2-lane MIPI CSI×1、40-pin GPIO、5V/2A、尺寸 85×56mm |
| 補查 Okdo 品牌定位 | 釐清 RS 商品頁品牌「Okdo」與 Radxa 的關係 | 掌握品牌脈絡（為何叫 Okdo ROCK 3C） | RS Components 自有品牌 Okdo 與 Radxa 共同掛名銷售 ROCK 系列；本板實為 Radxa ROCK 3C 在 RS 渠道的 co-brand 版本，非獨立設計 |
| 補查 RK3566 定位（網路搜尋遇 Google 反爬） | 掌握 SoC 背景 | 補足通用技術背景 | 通用知識補足：RK3566 屬瑞芯微中低階應用處理器，定位與樹莓派 Pi 3/4 級相近；未取得額外外部分頁（Google 反爬，C2 再補或省略） |

**關鍵技術事實（供 C2 收斂）：**
- **SoC**：Rockchip RK3566，四核 Cortex-A55（至 1.6GHz）、Mali-G52-2EE GPU、**無 NPU 強調**（通用規格）。
- **RAM**：LPDDR4，本商品為 1GB；系列另有 2GB/4GB。
- **儲存**：eMMC 模組（可擴充）+ microSD。
- **顯示**：1080P@60 HDMI、2-lane MIPI DSI。
- **I/O**：USB2.0 OTG×1、USB2.0 Host×2、USB3.0 Host×1、Gigabit Ethernet（支援 PoE HAT）、2-lane MIPI CSI×1、40-pin GPIO、3.5mm 麥克風音訊孔。
- **無線**：V1.4=WiFi6+BT5.4、V1.3=WiFi5+BT5.0。
- **電源**：5V/2A；尺寸 85×56mm（接近樹莓派 3B 尺寸）。
- **OS**：Linux（Radxa OS 基於 Debian）、Android。
- **定位**：低成本通用 SBC，官方列 HMI／機器人／智慧家庭／販賣機等情境。
- **品牌**：Okdo=RS 自有 maker 品牌，co-brand 銷售 Radxa ROCK 3C。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 硬體 metadata | Radxa 官方產品頁 | 取得 RK3566、CPU/GPU/RAM/無線/尺寸等完整資訊 |
| 詳細規格 | Radxa docs Features 表 | 取得完整連接埠、顯示、電源、尺寸規格，足以支撐報告 |
| 品牌關係 | RS/Okdo 背景補查 | 確認 Okdo 為 RS 自有品牌、co-brand 銷售 Radxa ROCK 3C |
| 背景脈絡 | RK3566 / 網路補查 | Google 反爬未取得外部比較頁；依通用知識補足 RK3566 定位，C2 再處理替代方案比較 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 標的非 GitHub repo 的 metadata 取得方式 | (A) gh repo view（不適用）(B) 官方產品頁＋docs | B | 此為硬體商品非 repo，改以官方一手來源（Radxa 產品頁＋docs）取代 gh，資訊可信度最高 |
| 規格來源 | (A) RS 商品頁（使用者貼的）(B) Radxa 官方 docs | B 為主、A 為輔 | RS 頁規格簡略且為轉售資訊；Radxa 官方 docs 才是權威一手規格，RS 頁作為售價/型號佐證 |
| 品牌脈絡處理 | (A) 視「Okdo」為獨立廠牌 (B) 查明為 Radxa 的 co-brand | B | 避免誤導使用者以為是另一家獨立硬體公司；實情是 RS 自有品牌掛名銷售 Radxa 板 |
| 背景補查失敗處理 | (A) 用 CDP 硬繞 Google (B) 依通用知識補足、留待 C2 | B | Google 反爬；CDP 慢僅必要時用。RK3566 定位屬通用知識，C2 網路補查替代方案比較即可 |
| 下一步 C2 方向 | (A) 直接撰寫報告 (B) 補查同級 SBC 比較（樹莓派/其他 RK 板）與替代方案 | B | 使用者要「這啥能幹嘛」＋和他手上的樹莓派/NVIDIA 板對照，需 §4 替代方案比較與 §2 背景（C2 網路補查） |
