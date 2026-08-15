# 224_R2_step2-plan_C1.md

## 狀況理解

R2 為追問輪，三問：①管理者在「掌握成員動機、不安、阻礙」此一目的上，除 1on1 外有無其他做法（質疑 R1 §4 未解說 1on1 目的與最優性）②後進資深員工（可能接管理）如何掌握周邊成員與上級狀態 ③把原文 1on1 技法收斂成表格（技法名／技法詳細／技法效果目的）。

本 sub-step C1 依 document skill 執行。標的仍非 GitHub repo，故以網路調研取代 gh repo view。C1 目標：為 Q1 補「掌握狀態」目的的跨機制比較（1on1 以外的機制），為 Q2 補「準管理者／資深 IC 掌握同儕與上級」的參考資料。Q3 純原文萃取，不需外部調研，留待 C2 收斂。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 R1 報告 `output/224_1on1.md` | 確認 R1 已答內容，定位 Q1 缺口 | 判斷 Q1 質疑是否成立 | R1 §4 有替代方案 DA 表（coaching／feedback／OKR），但未解說「1on1 目的」與「是否最優」；Q1 質疑成立，需補「掌握狀態」目的之跨機制比較 |
| 讀取 R1 C1 log | 確認 R1 已抓取的來源與脈絡 | 避免重複調研 | R1 已抓原文、チーフ1年、EM3ヶ月、CEO 芹澤「1on1の功罪」、リクルートMS；C1 應聚焦 R2 新缺口 |
| DuckDuckGo 搜尋「manager 掌握成員動機／engagement 方法 beyond 1on1」 | 為 Q1 取得 1on1 以外的掌握機制 | 取得跨機制比較來源 | 取得：engagement survey／pulse survey、360 feedback、skip-level meeting、觀察（MBWA）等機制；360 feedback 需「行動於洞察」否則淪為抽屜問卷 |
| DuckDuckGo 搜尋「senior engineer 掌握同儕與上級狀態 skip-level／upward feedback」 | 為 Q2 取得準管理者視角來源 | 取得資深 IC 掌握上級／同儕的參考 | 取得 skip-level meeting 系列（Management Center、LeadDev、em-tools、questworks）與「managing up」文獻 |
| 抓取 LeadDev「Fostering a skip-level manager relationship」（Maude Lemaire, 2023） | 取得 Q2 核心一手參考 | 掌握資深 IC 與 skip-level 上級建立關係的具體做法 | 取得：Staff+ 工程師應與 skip-level 建立 1:1；skip-level 提供公司視角／職涯贊助／第二回饋迴路；雙向——skip-level 依賴線下工程師提供真實資訊 |
| DuckDuckGo 第二次搜尋（Q2 補充） | 補 Q2 的 managing up 文獻 | 取得更多上級掌握來源 | 遭遇 CAPTCHA（選鴨子驗證），改用 Bing 但結果無關（senior living 誤判）；Q2 已由 LeadDev＋skip-level 系列涵蓋，不需 CDP |

**關鍵調研事實（供 C2 收斂）：**

- **Q1 跨機制比較（掌握成員狀態的目的）：**
  - **1on1（作者形式）**：定期一對一對談，聚焦狀態；成本＝時間＋對談能力；副作用＝可能淪為ヒアリング。
  - **skip-level meeting**：管理者越過直屬下屬，與下屬的下屬對談，取得被過濾掉的真實資訊；副作用＝可能削弱中間管理者信任。
  - **360 feedback**：從上下左右取得多向回饋；前提＝需信任基礎與匿名性；副作用＝若未行動於洞察則淪為抽屜問卷（decisionwise 明確指出）。
  - **engagement survey／pulse survey**：量化掌握團隊整體狀態；前提＝需設計良好問卷；副作用＝頻率過高造成問卷疲勞、只能掌握整體難掌握個人。
  - **觀察（MBWA／日常互動）**：從日常協作、會議、工作產出觀察狀態；成本低但主觀、易漏。
  - **coaching**：以提問引導成員自我探索，間接掌握狀態；前提＝管理者受過 coaching 訓練。
- **Q2 準管理者視角（掌握同儕與上級）：**
  - **與 skip-level 建立 1:1**（LeadDev）：Staff+ 工程師主動與上級的上級對談，取得公司視角、職涯贊助、第二回饋迴路；雙向——skip-level 依賴線下工程師提供真實資訊。
  - **managing up**：調整溝通風格對齊上級、主動提出需求與解決方案、建立互惠關係。
  - **同儕掌握**：透過協作、code review、跨團隊專案、日常互動觀察同儕狀態；無權力不對稱，需靠信任與互惠。
  - **上級狀態掌握**：上級握有資源與決策權，掌握其優先序／壓力／限制，需透過 1:1、skip-level、主動對齊目標取得。
- **Q3**：純原文萃取，技法清單＝①10 點體調分數 icebreak ②目的たたき台 ③アジェンダ整理（定例＋特別）④頻度時間設定 ⑤持ち込みトピック優先 ⑥チーフ提問範例 ⑦四半期振り返り聚焦提問。留待 C2 收斂成表格。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Q1 缺口 | R1 §4 是否解說 1on1 目的與最優性 | 未解說，Q1 質疑成立；C1 已取得跨機制比較來源（skip-level／360／survey／觀察／coaching） |
| Q2 主體 | 準管理者（資深 IC）視角 | 已取得 LeadDev skip-level 關係＋managing up 文獻，涵蓋上級與同儕掌握 |
| Q3 範圍 | 純原文萃取 | 已列出原文技法清單，留待 C2 收斂成表格 |
| 反爬處理 | DuckDuckGo 第二次搜尋 CAPTCHA → Bing | Bing 結果無關；Q2 已由 LeadDev＋skip-level 系列涵蓋，不需動用 CDP |
| 參考來源 | 是否足以支撐三問 | Q1/Q2 有外部參考；Q3 以原文為限，不需外部 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| Q1 比較範圍 | 僅 1on1 變體 / 跨機制（含非對談機制） | 跨機制 | 使用者問「掌握動機不安阻礙」此一目的，需含 1on1 以外的機制（skip-level／360／survey／觀察／coaching） |
| Q1 是否重答 R1 §4 | 重答替代方案 / 聚焦「掌握狀態」目的比較 | 聚焦「掌握狀態」目的 | 使用者明指 R1 未解說「1on1 目的與最優性」，需補此缺口而非重列替代方案 |
| Q2 主體 | 管理者視角 / 準管理者（資深 IC）視角 | 準管理者視角 | 使用者明示「後進資深員工、之後可能接管理」，對象含同儕與上級 |
| Q2 參考來源 | 通用管理文獻 / 資深 IC 專屬（LeadDev Staff+） | 資深 IC 專屬 | LeadDev「Fostering a skip-level manager relationship」直接對應 Staff+ 工程師掌握上級，最貼近 Q2 主體 |
| 反爬處理 | 動用 CDP / 改用 Bing | 改用 Bing | DuckDuckGo CAPTCHA 後 Bing 結果無關，但 Q2 已由既有來源涵蓋，不需動用較慢的 CDP |
| 下一步 C2 方向 | 直接撰寫報告 / 收斂三問成報告 | 收斂三問成報告 | C1 已取得 Q1/Q2 參考與 Q3 技法清單，C2 收斂成最終報告並追加 §5 User Q&A |
