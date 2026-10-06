# 278_R2_review_step3.md

## 驗證項目

| 項目 | 結果 | 備註 |
|---|---|---|
| 1. 4 個 section 齊全 | PASS | `## 1.`（問題）、`## 2.`（背景）、`## 3.`（解法）、`## 4.`（替代方案）皆存在；另含 R2 新增 `## 4.7`（判準節）、`## 5. User Q&A`（Q1–Q3）與 `## 附錄`。§5 位置在 §4 與附錄之間，符合 AGENTS.md §5 規範 |
| 2. DA 表存在與完整 | PASS | §4.4 DA 表 5 欄齊全（技術名／技術解法／技術使用前提／技術使用副作用／技術使用預期效果）；列 Hindsight 本體＋EverOS／TencentDB-Agent-Memory／macro／OpenHuman 共 5 列，替代方案 4 個在「2～4」規格內 |
| 3. 語言合規 | 部分 | 全篇中文；無比喻、無情緒性語言。`可能` 共 3 處：L84「mission 過窄可能導致抽不出 fact」、L205「與已 Adopt 的 HermesAgent 可能功能重疊」為殘留模糊用詞（R1 review 已標，R2 未修正）；L306 位於 Q3 標題，係**引用使用者原提問語氣**（AGENTS.md §5 明定「保留使用者原提問語氣與質疑口吻」），屬合規引用、不列瑕疵 |
| 4. 結構化呈現 | PASS | 大量表格（問題三層、retain 步驟、TEMPR、reflect 工具、固化兩層、部署、DA、切入點差異、兩端稅）、ASCII 架構圖（§3.0）、階層式小節；Q1–Q3 各含對照表 |
| 5. 反面論證 | PASS | §4.2 專列衝突點 C1–C4、§4.6 正反淨結論、§4.7 兩端稅對照、Q1–Q3 均含對照表／反證表（如 Q1「你的二元 vs 儲存端二元」、Q3「支持 reject vs 不構成 reject」）；§1 亦反向標注 benchmark 不遷移與「learn」定義模糊 |
| 6. 報告檔名與長度 | 部分 | 檔名 `278_Hindsight.md` 符合 `(pr-id)_(技術名).md`；`validate-report.sh` 回傳 `OK: report valid`（硬性 gate 為 50,000 bytes）。惟長度依 **R1 自身所用之同一衡量（raw 字元數）**：R1 為 16,762、R2 追加 §4.7＋§5 後為 **20,903，超過 AGENTS.md「20000 字」上限**（bytes 36,092）。因 R2 追加 Q&A 是 AGENTS.md 強制（既有 QA 不可刪改），屬規範內在張力，非新引入之實質缺陷 |
| 7. 第二大腦對照 | 部分 | **衝突已明示**：C1（防腐化只過一半）、C2（層級不同）、C3（workflow 閘門）、C4（與 HermesAgent 未定重疊）皆明確指出，未漏，滿足「漏掉即 FAIL」之要求。Hindsight／vectorize 零命中已如實註明；EverOS／TencentDB／macro／OpenHuman／LeanCtx／Headroom／HermesAgent 之判定與信任層級經實查一致；draft 均標「未經 review」。惟存有引用瑕疵（見問題點）：QMD 信任層級誤標、判定總表筆數過期、同步座標 hash 失效 |

抽查核實（獨立複核，`/tmp/mybrain` 實查 HEAD＝`530133b`）：

| 報告主張 | 複核方式 | 結果 |
|---|---|---|
| MyBrain 無 Hindsight／vectorize 紀錄 | `grep -rli` 全樹 | 零命中，一致 |
| EverOS 不採用・`human:fatesaikou`／stable・首見 2026-05-31 | frontmatter | 一致 |
| TencentDB／macro 不採用・`process:learn-gh-agent`／draft | frontmatter | 一致 |
| OpenHuman 未判定・`process:learning-agent`／stable（2026-07-26） | frontmatter | 一致 |
| LeanCtx（2026-06-06）／Headroom／學習 HermesAgent（2026-05-23）採用・`human:fatesaikou`／stable | frontmatter | 一致 |
| planning-with-files 不採用・`human` 系 | frontmatter | 一致（實為 `human:fatesaikou`／stable） |
| 技術取捨準則 `claude-code/opus-5`／draft・未 review | frontmatter | 一致 |
| 統一的兩端稅 `claude-code/opus-5`／draft・未 review | frontmatter | 一致 |
| **QMD 試用・`human:fatesaikou`／stable（首見 2026-08-11）** | frontmatter | **不一致**：實為 `generated.by: claude-code/opus-5`／`status: draft`（外部 ToDo 來源） |
| **判定總表 117 筆・不採用 65** | 全文與 body 統計 | **不一致**：現為 118 筆・不採用 66（新增 security-audit-skill，2026-09-26） |
| 同步座標 `d2aeff7` | `git cat-file -t` | **失效**：現 HEAD 為 `530133b`，`d2aeff7` 已不存在 |

## 問題點

- **QMD 信任層級誤標（R1 已標、R2 未修正）**：§4.0 表將 QMD 標為 `human:fatesaikou` / `stable`，實為 `claude-code/opus-5` / `draft`。把一份未經本人 review 的 AI 草稿標成本人 stable 定稿，屬引用準確性瑕疵（未改變任何衝突結論，Hindsight 為新標的）。
- **判定總表筆數過期**：§4.0「判定總表」一列記 117 筆・不採用 65，與其引用來源現值 118 筆・不採用 66（2026-09-26 新增 security-audit-skill）不符；報告宣稱「2026-09-26 同步」卻未反映同日新增，屬同步座標與引用值不一致。
- **同步座標 hash 失效**：附錄記 `d2aeff7`，複核時 `git cat-file` 顯示該物件不存在，現 HEAD 為 `530133b`（R1 review 後 mybrain 曾重新同步）。屬座標標記過期。
- **報告長度超標（依 R1 同一衡量）**：raw 20,903 字 > 20,000 上限。係因 R2 依規範強制追加 §5 Q1–Q3 所致；硬性 gate（50,000 bytes）通過，非實質缺陷，但與 AGENTS.md 上限字面衝突。
- **`可能` 殘留 2 處**（L84、L205）：與「不寫可能」語言規範有細微出入；R1 已標 L205，R2 未修正。L306 屬使用者原句引用，不計。

## 建議

- 修正 §4.0 QMD 一列：信任層級改為 `claude-code/opus-5` / `draft`，並比照其他 draft 註明「AI 草稿，未經他 review」。
- 將 §4.0「判定總表」列更新為 118 筆・不採用 66，或改寫為不列絕對筆數（避免每次同步即過期）。
- 附錄同步座標改為複核當下有效之 HEAD（或改註「同步日 2026-09-26」而不綁定短 hash）。
- 可精簡 §4.0 與 §4.4 的重複列（同批工具在兩表重述），以回收字數；或於報告開頭註明「§5 為各輪追加，長度上限僅約束 §1–§4 主體」。
- 將 L84、L205 的 `可能` 改為確定句式（如「有 X 風險」「是否重疊未定」）。
- 其餘無。R2 三問（Q1 二元標籤、Q2 升級是否內建、Q3 存取複雜度是否該 reject）拆成 3 條獨立 QA，符合 §5 規範（保留質疑口吻、含表格與結論收斂）；序號自 Q1 起算正確、既有 QA 未刪改；§4.7 新增判準已標 draft 與未 review。

VERDICT: PASS
