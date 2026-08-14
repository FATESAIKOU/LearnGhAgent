# 218_R1_step1-intent.md

## 狀況理解

本輪（R1，PR #218）使用者貼上 RS Components 日本站的一個商品頁面，標的為「Okdo ROCK 3 C Model C 1GB 單板電腦」（RS112-D1W2P1，RS品番 249-3157）。頁面內容為：品牌 Okdo、1GB RAM、連接埠 CSI／DSI／USB 2.0／USB 3／HDMI／Host／M.2／OTG、1080p@60fps、OS 支援 Linux 與 Android、售價約 ¥7,835 未稅。

使用者的意圖非常簡短：自述用過 Raspberry Pi（數枚派）與 NVIDIA 的開發板，但**不知道這塊板子是啥、能幹嘛**，要求「調研它」（Closes #217）。即：這是一份**技術認識／定位**性質的調研請求，標的是一個具體的 SBC 商品型號，而非軟體／框架。核心問題是「這是什麼、能做什麼、和他手上的經驗（樹莓派／NVIDIA 板）相比如何」。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 PR body 的原始貼文 | 判斷技術標的與附帶條件 | 定出調研對象與邊界 | 標的＝Okdo ROCK 3 C Model C（RS112-D1W2P1），屬 ROCK 系列 SBC，與 ROCK 4/5 屬同系列 |
| 用 mybrain-read 查 FATESAIKOU/MyBrain，grep「ROCK 3／okdo／radxa／rockchip／單板／開發板／sbc」 | 確認他是否已評估過這個標的 | 找到舊判定或舊筆記 | **第二大腦無此主題**。ROCK／Okdo／Radxa／Rockchip／SBC／單板 皆零命中 |
| grep「raspberry／樹莓／數枚派／jetson／nvidia」 | 確認他對同類硬體（SBC）的既有評估與經驗脈絡 | 找到他對樹莓派／NVIDIA 板的看法 | NVIDIA 命中的是 [nvidia cosmos](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/nvidia%20cosmos.md)（世界基礎模型，generated.by=human:fatesaikou, status=stable, 首見 2026-06-20）——是軟體模型**非開發板**；沒有「買過／評過哪張樹莓派或 Jetson 板」的評估紀錄。僅在 [Feedly 閱讀](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/靈感/Feedly%20閱讀.md)（human:fatesaikou, stable, 2026-03-21）提及「NVIDIA DGX Spark 桌面 AI 超級電腦可本地跑 200B 參數模型」的產業趨勢 |
| 讀骨幹檔「判定總表」「技術取捨準則」「專案/下一步清單」 | 確認他對硬體／動手做專案的取捨準則與現況 | 判斷調研應採取的定位視角 | 「下一步清單」的技術條目全是軟體（QMD、GKE、ego-lite、OmniRoute 等），**無任何硬體／SBC 專案**。判準：理解優先、Reject≠沒價值、會否進日常 workflow 是更強判準（見[技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md)，draft，2026-08-01） |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 標的識別 | 商品名、型號、品牌、系列 | Okdo ROCK 3 C Model C，RS112-D1W2P1，屬 Radxa ROCK 3 系列（ROCK 4/5 同系列）SBC |
| 他是否已評估過 | grep 第二腦 ROCK/Okdo/Radxa/Rockchip/SBC | 無任何評估紀錄 → 此為全新標的，非追問非補充 |
| 與其既有經驗的關聯 | grep Raspberry/NVIDIA/Jetson | 僅 NVIDIA cosmos（軟體模型）與 Feedly 的 DGX Spark 趨勢；無 SBC 硬體購買／評估紀錄 |
| 取捨準則 | 讀技術取捨準則、下一步清單 | 無硬體專案；調研宜帶「硬體技術理解」與「與樹莓派／Jetson 定位差異」雙視角，但不需預設他想購入 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研標的的抽象層級 | ① 單一型號 RS112-D1W2P1 ② ROCK 3 C 系列 ③ ROCK 3 全家族 ④ ROCK 全系列＋同級 SBC | 以 ROCK 3 C 系列為主體，旁及 ROCK 3 家族與同級 SBC 對照 | 使用者問「這啥能幹嘛」，需先講清這塊板子的規格與定位；再放到 ROCK 系列與樹莓派／Jetson 的比較框架才有意義 |
| 使用者的動機定位 | ① 想買硬體 ② 純認識技術 ③ 學習硬體知識 | 定位為「技術認識＋與既有經驗對照」，不預設購買意圖 | 原文只說「不知道這啥能幹嘛」，未提購買；第二腦無相關購買評估，故不引入採購建議 |
| 第二腦查不到時的回報方式 | ① 用通用知識填補 ② 明說無此主題再補 | 明說「第二大腦無此主題」，技術細節另以一般知識補足 | 依 mybrain-read 規則：查不到就直接講沒有，不把通用知識講成他的舊結論 |
