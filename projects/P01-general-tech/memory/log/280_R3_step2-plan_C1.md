# 280_R3_step2-plan_C1.md

## 狀況理解

R3（PR #280）使用者下最終判定「不採用」，理由為**需求層不成立**（「我沒有寫編輯器的需求」），並指示「技術本身可以放入參考，記住有這類寫編輯器的工具」。此輪非質問型，不觸發 §5 Q&A。

C1 不重做 R1 的定位／架構／授權調研，只針對本輪任務補三類事實：

| 本輪需求 | C1 要取得的事實 |
|---|---|
| 記錄判定與理由 | 對齊 Step1 已確認之準則（已於 Step1 完成，C1 複核無需重查） |
| 「放入參考」＝記住「這類編輯器 SDK」方向 | **類別層**同級方案現況（誰是「提供嵌入編輯能力」的工具），而非只記 Univer 單一 repo |
| 判定為需求層、非技術否定 | 確認 Univer 技術面事實無重大反轉（metadata 是否變動），避免以過期資料落記 |

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 實際的結果 |
|---|---|---|
| `gh repo view` + `gh api repos/dream-num/univer` | 覆核 metadata 是否變動 | **22,383★／1,872 forks**（R2 為 18,993／1,618）；Apache-2.0；TypeScript；created 2022-09-29；pushed 2026-10-05；desc 續寫「The Office Harness for AI Agents」；topic 含 docx/xlsx/pptx/pdf/sheet/slides/sdk/collaboration |
| `gh api repos/.../releases` | 版本節奏 | 新增 **v1.0.3（2026-09-29）**；v1.0.0/1/2 為 2026-09-24 同日；前版 v0.25.2（2026-09-17）。與 R1 記「v1.0.2 最新」相比已前進一版 |
| `gh api repos/.../commits` | 活躍度 | 最近 commit 2026-10-04（docs/Sheets/Docs），持續活躍 |
| `gh api repos/.../contributors` | 團隊規模覆核 | 首頁 30 筆；top：jikkai 1189、DR-Univer 630、wzhudev 574、Dushusir 547、wpxp123456 538（R2 記實名 68 人，本次為 API 分頁首頁，非全量） |
| `gh api orgs/dream-num` | 組織覆核 | DreamNum，org 建於 **2020-02-25**；blog univer.ai；90 public repos；followers 468 |
| 抓 README（dev）全文 425 行 | 一手定位句覆核 | 「an open-source SDK for creating office applications inside your own product…without forcing you into a hosted app or a fixed UI」；「not a spreadsheet file viewer only — a framework for building your own productivity surface」；工具列 **Spreadsheets・Documents・Presentations・Bases・Boards・PDFs**（R1 記 Canvas／Relational；本次 README 作 Bases／Boards／PDFs） |
| 抓 `docs/API_STABILITY.md` | 覆核「pre-1.0」自稱 | 明載「Univer is currently **pre-1.0**, so the project can still make breaking changes」；Stable／Experimental／Internal 三級 |
| `gh api` 生態 repos | 家族 agent 路徑現況 | univer-workspace **2,237★**（Apache-2.0，2026-10-04 pushed）、dsh-univer-office **470★**（Apache-2.0）、univer-cli 13★、univer-sdk-skills 11★、univer-mcp 38★（MIT） |
| `gh api` 類別同級方案 | 供「放入參考」的類別盤點 | ONLYOFFICE/DocumentServer 6,970★（AGPL-3.0）、CollaboraOnline/online 3,366★、ueberdosis/tiptap 38,645★（MIT，headless rich text）、ruilisi/fortune-sheet 3,733★（MIT，drop-in JS spreadsheet）、jspreadsheet/ce 7,231★（MIT）、gristlabs/grist-core 11,901★（Apache-2.0） |
| grep 第二大腦 | 確認「放入參考」無既有承載處 | 無「Office 編輯器 SDK」同類項；既有「編輯器」全指程式碼編輯器（Zed／Delta，皆不採用）。`OpenDesign.md` 的 univer 命中為「universal」字串，非 Univer |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 標的是否變動 | metadata 覆核 | 標的未變；僅數字成長（22,383★）與新增 v1.0.3 |
| R1 結論是否翻轉 | 一手文件覆核 | **未翻轉**：仍是可嵌入 Office SDK；agent 相關 Worktree／協作／import-export 仍屬 Pro；API 仍自稱 pre-1.0 |
| 工具命名差異 | README 對照 R1 | 現列 Bases／Boards／PDFs；與 R1 記的 Canvas／Relational Tables 為同一產品線的不同列法，非矛盾（R1 已註 PDF 規劃中） |
| 判定依據正確性 | 對齊 Step1 準則 | 「無寫編輯器需求」＝需求層不成立，非技術缺陷；Univer 技術面事實無反轉，判定站得住 |
| 「放入參考」承載處 | grep MyBrain＋報告 | MyBrain 無同類項；只能落記於報告，寫入 MyBrain 須使用者觸發 `sync-to-mybrain` |
| 類別盤點完整性 | 同級方案查詢 | 已取得「嵌入編輯能力」類別代表：Univer、ONLYOFFICE、Collabora、tiptap、fortune-sheet、Grist、jspreadsheet |
| 待辦（後續 step） | — | 於報告落記：①判定與理由（需求層不成立）；②Univer 定位為「這類編輯器 SDK」類別參考；③標明本次未寫入 MyBrain |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否重跑 R1 調研 | 全套重調／只補本輪缺口 | **只補本輪缺口** | 指令明示 R2+ 針對本輪意圖；且 R1／R2 已建立全貌，重跑無新增價值 |
| metadata 是否需更新 | 沿用 R2 數字／重新取 | **重新取並標差異** | 判定結論雖不變，但報告若引過期數字會失真（★由 18,993→22,383、新增 v1.0.3） |
| 參考粒度 | 記 Univer 單一 repo／記「類別」 | **類別** | 使用者原話「有這類寫編輯器的工具」，指向類別；C1 須備齊同級方案才能支撐類別盤點 |
| 類別方案取捨 | 只列 R1 既有 DA 表／補查現況 | **補查現況** | R1 表部分數字可能過期；類別參考要能長期使用，需附最新★／授權 |
| 是否再查 MyBrain | 略過／複核 | **複核** | 確認「放入參考」無既有承載處，避免誤記為已入庫 |
| 工具命名差異處理 | 當作矛盾／視為同線列法 | **視為同線列法並註記** | README 六工具與 R1 記的 Canvas／Relational 為不同切入的列法，非事實衝突 |
