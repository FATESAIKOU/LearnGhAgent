# 266_R1_step2-plan_C1.md

## 狀況理解

本輪為 R1 初次分析。Step 1 已鎖定標的＝`tt-a1i/archify`（diagram-as-code／架構圖生成 Skill），並定調：第二大腦無此主題，報告以通用知識為主、引已 Reject 的同軸標的 diagram-design 作對照，正面處理「archify 是否重蹈出版工具過重」的矛盾。C1 任務＝依 document skill 取得 repo metadata 與主要文件，為後續收斂（C2）建立事實基礎。

## 執行的動作與結果

以 `gh repo view` / `gh api`（git tree、contents、commits、tags）完成，全走一般 API，未遇 CAPTCHA、不需 CDP。

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view tt-a1i/archify --json ...` | 取得 metadata | stars、license、分支、更新時間 | 66.8k stars、MIT、`main`、更新於 2026-09-19；desc「agent skill for beautiful, verifiable ... diagrams—self-contained HTML」 |
| tree `?recursive=1` | 盤點文件結構 | 找出 key 子文件 | 根有 README(.md/_ZH/_EN)、DESIGN.md、PRODUCT.md、CHANGELOG、CONTRIBUTING、REVIEWING、ROADMAP；skill 體在 `archify/`（SKILL.md、bin/、schemas/、examples/、delta/）；另 `.agents/skills/archify-review/` |
| 抓 `README.md` 全文 | 理解定位與機制 | 掌握「How it works」 | 五圖型＋4 presets＋dark/light；typed JSON IR→確定性編譯為自含 HTML/SVG；Generate/Validate/Preview/Deliver 管線；atomic validation、failure 帶 repair receipt；Architecture Delta Before/Delta/After 比對；證據導向 `SRC n` 來源驗證；DeepSeek Harness DSH 整合；明列非目標：Mermaid 自動排版、WYSIWYG |
| 抓 `archify/SKILL.md` | 取得 agent 操作契約 | 掌握 authoring invariants 與驗證門檻 | 5 型 router、schema v1/v2、9 項 showcase artifact checks、`validate`/`deliver` 兩輪修正、Mermaid 輸入轉換、meta 欄位規則、`based_on: Cocoon-AI/architecture-diagram-generator` |
| 抓 `DESIGN.md`、`PRODUCT.md` | 取設計哲學與產品定位 | 理解「Evidence Console」取向 | 七色語意、mono 字型、Truth before spectacle、portable proof；anti-reference＝Mermaid beautifier / WYSIWYG 套件；非 drawing suite 而是 instrument |
| 抓 `.agents/skills/archify-review/SKILL.md` | 理解 repo 自我 QA 機制 | 掌握其維護判準 | 以 Value/Cost/Impact 三維做 issue/PR review，與分析報告之 DA 表可對照 |
| `commits`+`tags` | 看活躍度與版本節奏 | 佐證成熟度 | 近期 commit 密集（fast-uri 依賴修復、delta arrowheads、SVG UTF-8 聲明）；tags 至 v2.16.0，dev 為 v2.17.0-dev.1；CHANGELOG 顯示 workflow v2 compiler、locale、update awareness 為近期功能 |
| 抓 `integrations/deepseek-harness/README.md` | 補 DSH 整合背景 | 釐清與第二大腦「觀望」標的 deepseek-harness 的關係 | `@tt-a1i/archify-dsh` 為 community 非官方整合，僅 bundled Skill，無 telemetry、無 native tools |

**關鍵發現（供 C2 收斂）**：
- 定位是「溝通 artifact 的技術儀器」，**非**通用繪圖編輯器／Mermaid theme——直接回應 Step 1 的矛盾命題，需與 diagram-design（出版工具過重）做細緻對照。
- 與既有 Reject 軸的差異點在「驗證」：atomic validation、確定性 compile、repair receipt、PR 快照比對，使輸出可被信任、可追蹤，非純視覺出版。
- 66.8k stars 為同類極高值，但 stars 不代表「符合他的理解目的」，報告不應以市場熱度作為採用結論。

查證來源（GitHub API，高信任）：
- `repos/tt-a1i/archify`（main @ 2026-09-16 最後 commit，tags v2.16.0 / v2.17.0-dev.1）
- README.md / archify/SKILL.md / DESIGN.md / PRODUCT.md / .agents/skills/archify-review/SKILL.md / CHANGELOG.md / integrations/deepseek-harness/README.md

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Metadata 完整性 | gh repo view 全欄位 | stars/license/branch/updatedAt/desc 齊全，值合理（無異常） |
| 文件取得 | git tree＋contents 逐檔 base64 decode | README 全文、SKILL.md、DESIGN、PRODUCT、review skill、CHANGELOG 皆成功讀取 |
| 機制理解 | 交叉比對 README「How it works」與 SKILL.md 驗證契約 | Generate→Validate→Deliver 管線、9 項 showcase check、兩輪修正規則互相吻合 |
| 對照素材 | DESIGN/PRODUCT anti-reference＋commit 歷史 | 有充分素材支持「instrument vs drawing suite」論點 |
| 反爬需求 | 全程一般 gh api | 無 CAPTCHA，CDP 未使用 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研深度 | 僅 README；README＋skill 契約＋design/product | README＋SKILL.md＋DESIGN＋PRODUCT＋review skill＋CHANGELOG＋DSH README | 標的為「Skill」，操作契約（SKILL.md）與定位（PRODUCT/DESIGN）是理解核心，非僅行銷 README |
| Mermaid 處理 | 視為核心；視為選配輸入 | 視為「輸入轉換」功能列入機制，但非產品本體 | SKILL.md 明列 Mermaid 為輸入之一，但 anti-reference 排除 Mermaid beautifier 定位，須辨別 |
| stars 權重 | 作為採用結論依據；僅作成熟度佐證 | 僅作成熟度佐證，不作採用結論 | 依 Step 1 判準（理解優先＋workflow 閘門），市場熱度不直接等於符合他的目的 |
| DSH 整合 | 深入調研；僅記錄存在 | 僅記錄為 community 非官方整合，並註記與第二大腦觀望標的的關係 | C1 範圍是 metadata＋主要文件，DSH 細節留待 C2 視需要深入 |
