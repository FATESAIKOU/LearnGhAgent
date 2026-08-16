# 234_R2_step2-plan_C1.md

## 狀況理解

本輪為 R2（追問輪）。R1 已產出 diagram-design 技術本質報告（output/234_diagram-design.md，含 27 視覺型、semantic pattern、品牌 onboarding、靜態輸出、替代方案對照）。本輪使用者不再問「這技術是什麼」，而是**把標的對準自己的處境做適用性質問**，3 題皆以「我（工程師兼顧問、追求解構抽象概念、非設計師、不做客戶圖表）」為主語：

1. 這狀況下能不能用這技能？
2. 對我的目的是否過度重型，或該找專門技能？
3. 這技能最可能的使用者是誰？

Step 1 已定調為「個人適用性評估」並確認觸發 §5 User Q&A。本 sub-step C1 的調研目標**不是重做 R1**，而是補查能回答這 3 題的證據：①實際使用門檻（是否需設計知識）②目標受眾定位（README / SKILL.md 明說給誰）③與「解構抽象概念」用途的契合度（semantic pattern 路由、audience dial、consultant 變體、density 限制）。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view cathrynlavery/diagram-design` | 更新 metadata 比對 R1 | 確認活躍度與規模變化 | 19,143 stars（R1 時 18,112，+5.7%）、MIT、HTML、updated 2026-08-16，活躍迭代 |
| 抓取 README.md（raw） | 更新 R1 已讀文件 | 補抓受眾定位與「when-not-to-use」細節 | 取得全文：Why/What it makes/Install（Claude Code/Codex/Pi/Cowork）/Onboarding/Quickstart/Import 四 dials/Export/Architecture/「It's working if…」/設計系統/Primitives/「When not to use」 |
| 抓取 skills/diagram-design/SKILL.md（564 行） | 讀核心規格中與「門檻/受眾/用途契合」相關章節 | 掌握 first-run gate、density、audience 判準 | 取得 §0 first-run gate、§1 Philosophy、§2 When to Use、§3 semantic pattern 路由表、§4 anti-patterns、§5 設計系統、§6 connector、§7 4px grid 與 complexity budget、§9 taste gate、§10 變體（含 consultant special）、§11 import、§12 output |
| 抓取 references/semantic-patterns.md | 評估「解構抽象概念」的契合度 | 確認 7 種行為語意與「結構化整理」的對應 | 取得 7 pattern 路由表（fan-in queue、stage framework、unstructured→structured、paired policy traces、secure paved road、governance catalog、compensating security layers）＋每種的 triggers/budget/anti-patterns/static fallback |
| 抓取 references/output-spec.md | 補「過度重型」判準 | 確認 audience dial 與 node budget | 取得四 dials（format/size/detail/audience），audience＝engineer/mixed/executive 只改措辭；detail＝faithful≤24/balanced≤12/simplified≤7；§7 預設 ≤9 nodes，超標 split overview+detail |
| 抓取 references/type-quadrant.md（grep consultant） | 補 Q3 目標受眾證據 | 確認存在「consultant 專用」變體 | 取得 consultant special 2×2 scenario matrix（BCG/McKinsey 領域），含 use 判準與 style tokens |

**關鍵證據（供 Step 3 收斂成 Q&A）：**

- **使用門檻（Q2）**：
  - **不要求先備設計知識**：first-run gate（§0）不考驗設計能力，只要求選品牌來源（URL / 已裝 skill / 本地資料夾 / 手貼 / default / 存 profile）。品牌 onboarding 從網站自動萃取 dominant palette + font stack → 語意 token，並自動做 WCAG AA 對比檢查；非要求使用者自述設計系統。此點與 R1 對照 Taste Skill「需設計知識與儲備」被拒的主因**可切割**。
  - **有使用成本的硬限制**：density 4/10、預設 ≤9 nodes、超標要 split overview+detail（§7）。對「解構複雜概念求完整理解」的使用者，**9 節點上限可能成為結構化大概念的瓶頸**——需要拆圖。
  - **非零 onboarding 成本**：需裝 plugin（Claude Code/Codex/Pi）+ 跑 onboarding + 維護 style-guide；editable install 需 clone 或 symlink。
- **目標受眾（Q3）**：
  - README 開宗明義「Editorial diagrams your designer won't hate」→ 受眾是**需要出版級圖表的內容創作者/部落客/產品人**（作者 Cathryn Lavery：BestSelf.co 創辦人、littlemight.com 部落格作者），非工程師。
  - Install 支援 Claude Code/Codex/Pi——是「**會用 coding agent 的人**」。
  - 內建 **consultant special 2×2 scenario matrix**（BCG/McKinsey territory）→ **明確瞄準管理/IT 顧問**做策略框架圖。
  - audience dial 含 `executive` 措辭層級；import 的 `--audience=executive` → 可產出給高階主管看的簡化圖。→ 顧問/管理層是顯性受眾。
  - 27 型含大量**技術向型別**（architecture、sequence、state、ER、data-flow、DP security matrix、IT current-state、medallion）→ 也服務工程師的系統圖需求。
  - **排除對象**：SKILL.md §2 明說「quick unicode → wiretext、lists → table、before/after → table、one-shape → 寫句子」；「讀者從視覺學到的比一段好文章多嗎？」為 gate。→ **不適合拿來做「純文字概念整理」**，Youtuber/SNS 營運者若要的只是速食示意圖也非主要標的（除非走 social-og/social-square 的 PNG 匯出）。
- **「解構抽象概念」契合度（Q1）**：
  - **正面**：7 種 semantic pattern 正是「把行為/風險/治理抽象化」的語意，如 paired policy-evaluation traces（兩條規則軌跡找 first divergence）、governance catalog（按 enforcement surface 分組）、unstructured input→structured artifact（對話正規化為結構）。這與使用者「解構／抽象複雜概念與事件以求完全理解或結構化整理」的軸高度對應。
  - **張力**：diagram-design 的輸出目的是「**對外出版**」（blog/slide/social），不是「**對內思考**」的工具。它強制 brand、density 4/10、≤9 nodes、fidelity ledger——這些對「要完整保留複雜度以求理解」的思考用途是**約束而非助力**。README/SKILL.md 的判準是「讀者學得比段落多嗎」，不是「作者理解得了嗎」。
  - **結論導向**：semantic pattern 的 budget（如 ≤9 節點、≤3 產源）強制刪減——適合「把理解成果輸出為簡化圖」，不適合「用圖來窮盡理解」。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo 現況 | gh repo view | 19,143 stars、活躍（updated 2026-08-16），比 R1 時更活躍 |
| 使用門檻 | SKILL.md §0/§7/§9、onboarding | 不要求設計知識（品牌自動萃取＋first-run gate）；但有 9-node 上限、需 plugin 安裝＋onboarding |
| 目標受眾 | README 定位、§10 consultant special、audience dial、§2 when-not-to-use | 主要受眾＝需出版級圖表的內容創作者；顧問（consultant 2×2）與工程師（技術型別）皆涵蓋；排除純文字概念整理 |
| 解構抽象契合 | semantic-patterns.md、Philosophy、§7 | 7 pattern 對應抽象語意（正面）；但輸出面向「出版」非「思考」，density/節點上限是對理解用途的約束（張力） |
| 資訊缺口 | 對照 3 題 | 已足：門檻/受眾/契合皆已取得證據；可進 Step 3 收斂成 §5 Q&A 並評估「過度重型」 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研範圍 | (A) 重做 R1 全量技術調研 (B) 只補查適用性證據 | B | 使用者此輪是適用性質問，R1 已覆蓋技術本質；重做浪費且偏離意圖 |
| 補查文件 | (A) 讀全部 27 型 type-*.md (B) 只讀受眾/門檻/契合相關 | B | consultant special、semantic patterns、SKILL.md 門檻章節已足；逐型細節對「適用性」非必要 |
| 判準軸 | (A) 純技術優劣 (B) 對照 MyBrain 時間預算＋workflow 閘門 | B | Step 1 已確認「過度重型」需以 10–20h/週時間預算與「是否影響個人 workflow」為硬約束，非技術比較 |
| 用途面向 | (A) 把「解構抽象」視為與標的完全相容 (B) 標出「出版 vs 思考」張力 | B | README/SKILL.md 的判準是對外出版，與「對內理解」用途有實質張力，須點明以免誤導 |
| 下一步 | (A) 直接產 Q&A (B) 收斂證據進 Step 3 | B | Step 3 依 AGENTS.md 產出報告 §5 User Q&A 與 QA log |
