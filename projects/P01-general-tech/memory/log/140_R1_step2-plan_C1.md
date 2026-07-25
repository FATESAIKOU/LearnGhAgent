# 140_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認技術標的為 Hallmark（Nutlope/hallmark），一個反 AI 味設計 Skill。本 sub-step C1 的任務是取得 repo metadata、主要文件、以及補查背景脈絡，為後續分析報告收集原始資料。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view Nutlope/hallmark --json` | 取得 repo metadata | 獲得 star/fork/license/語言/建立時間 | 17,465 stars, 876 forks, MIT, CSS primary, 2026-04-27 建立 |
| `gh api repos/.../contents` 遍歷目錄 | 了解 repo 結構 | 列出根目錄、docs/、skills/、site/ 等子目錄 | 根目錄 9 項；docs/ 含 4 檔；skills/hallmark/ 含 SKILL.md + references/（29 個檔案）；site/ 含 _tests/（18 個範例頁面） |
| 讀取 README.md | 取得第一手技術描述 | 確認 4 verbs、20 themes、57 slop gates、Custom 模式 | 完整取得：default/audit/redesign/study 四動詞、20 themes、Custom 分支、安裝方式 |
| 讀取 SKILL.md | 取得完整設計流程規範 | 理解 Design flow 6 步驟、Component-scope 流程、6 個跨 verb 紀律 | 完整取得：Pre-flight scan → Design-context gate → Macrostructure pick → Theme route → Visual ruleset → Hero enrichment → Preview → Build → Slop test |
| 讀取 slop-test.md | 取得 58 道閘門 + pre-emit self-critique | 理解 Hallmark 的品質檢查機制 | 完整取得：6 軸自評（Philosophy/Hierarchy/Execution/Specificity/Restraint/Variety）+ 58 gates（Visual/Structural/Microinteractions/Variety/Implementation/Hero/Diversification/Layout/Typography/Input/Contrast/Nav-Footer/Copy/Chrome/Token/Responsive） |
| 讀取 macrostructures.md | 取得 21 種頁面結構索引 | 理解 Hallmark 的結構多樣性設計 | 完整取得：Bento Grid → Component Playground 共 21 種，含 diversification rule 與 SaaS page sequence |
| 讀取 anti-patterns.md | 取得 AI 生成 UI 的「tells」清單 | 理解 Hallmark 要消除的具體問題 | 完整取得：Critical 13 項（purple-gradient hero、Inter-everywhere、3-column grid、card-in-card 等）、Major 20+ 項、Minor 8 項 |
| 讀取 contract.md | 取得輸出合約與範圍 | 理解 Hallmark 的 scope 限制 | 確認：taste skill，不發明 product copy、不選 brand identity、不建 logic |
| 讀取 recipes.md | 取得 8 個完整工作範例 | 理解 Hallmark 實際應用情境 | 完整取得：Coffeebox/Tide/Streampipe/Maple/Meridian/Tracejam/Anya/Foundry/Cohort 共 9 個範例 |
| 讀取 ROADMAP.md | 取得未來發展方向 | 理解專案 roadmap | 取得：Now（Nanobanana hook）、Next（Brand-first flow、motion tokens、variant verb、structural cookbook 等 7 項）、Later（explain、negative-capability、emotion-first 等 6 項） |
| 列舉 references/ 子目錄 | 了解完整參考文件體系 | 確認文件覆蓋範圍 | 29 個檔案：4 genres、21 macrostructures、50+ components（nav/footer/hero/section/feature/CTA/testimonial）、4 themes spec、2 verbs、color/typography/layout/motion/copy/microinteractions/responsive/study 等 |
| 列舉 site/_tests/ | 確認範例頁面數量 | 了解實作驗證規模 | 18 個測試範例頁面 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Repo metadata 完整性 | 確認 star/fork/license/語言/建立時間 | 完整。17.5k stars、876 forks、MIT、CSS primary、2026-04-27 |
| 文件體系覆蓋率 | 確認 SKILL.md + 29 references + 4 genres + 21 macrostructures + 50+ components | 完整。Hallmark 的文件體系極其完整，從設計流程到品質檢查到元件庫均有對應文件 |
| 核心機制理解 | 確認 4 verbs、58 gates、21 macrostructures、20 themes、Custom 模式 | 完整。Hallmark 的核心機制是「結構多樣性 + 嚴格的 slop test + 主題旋轉」 |
| 背景脈絡 | 確認 AI 生成 UI 的常見問題（anti-patterns） | 完整。anti-patterns.md 詳細列出了 40+ 種 AI tells |
| 專案狀態 | 確認活躍開發中、有 roadmap | 活躍。ROADMAP.md 列出 Now/Next/Later 三層計劃 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 需讀取哪些 references | (a) 只讀 SKILL.md (b) 讀 SKILL.md + 關鍵 references (c) 讀全部 29 個 | (b) 讀 SKILL.md + 6 個關鍵 references | 6000 字上限限制，無法詳列全部 29 個。選取最能說明核心機制的文件：SKILL.md（流程）、slop-test.md（品質）、macrostructures.md（結構多樣性）、anti-patterns.md（問題定義）、contract.md（範圍）、recipes.md（實例） |
| 是否需要補查外部背景 | (a) 僅依賴 repo 內文件 (b) 搜尋外部文章/影片 | (a) 僅依賴 repo 內文件 | Hallmark 的文件體系已極其完整（29 references + 4 genres + 21 macrostructures + 50+ components），足以支撐分析報告。外部背景（AI 生成 UI 問題）已在 anti-patterns.md 中充分涵蓋 |
| 是否讀取 themes/ 下的 spec 檔 | (a) 讀取全部 4 個 (b) 不讀取 | (b) 不讀取 | 4 個 theme spec（carnival/cobalt/hum/lumen）是 per-theme 的細節規範，對理解 Hallmark 核心機制非必要。6000 字上限下優先保留更重要的文件 |
