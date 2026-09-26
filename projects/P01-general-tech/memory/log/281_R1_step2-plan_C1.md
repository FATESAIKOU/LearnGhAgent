# 281_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1：取得 `cloudflare/security-audit-skill` 的 repo metadata 與主要文件。標的是一個「coding-agent skill」而非可執行軟體，故主要文件＝README 與 `skills/security-audit/*.md`（skill 本體）；另有 blog 作為設計理念與上位 harness 的一手來源。C1 需先把 metadata、檔案結構、六／七階段流程、三類 verdict、安裝方式、已知限制盤點齊，供 C2 補背景與替代方案。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` + `gh api repos/...` | 取 metadata | stars/license/語言/時序 | 21757 stars、1254 forks、MIT、JavaScript、created 2026-06-18、pushed 2026-09-14、open issues 50、無 topics/releases/tags |
| `gh api .../git/trees/main?recursive=1` | 取完整檔案結構 | 確認 skill 組成 | 24 個路徑，全在 `skills/security-audit/`；無 CI、無測試框架 |
| `gh api .../readme` | 取 README | 定位與用法 | 6 階段流程、3 verdict、安裝、requirements、設計原則 |
| 讀 `SKILL.md` | 取 skill 主檔 | 模式、安全邊界、6 階段 | guidance/full audit 兩模式；sandbox 與 write isolation 規範 |
| 讀 `RECONNAISSANCE.md` | Phase 1 細節 | 認識 recon 4 agent 與 coverage ledger | 1a~1d 四個 research agent、ledger 狀態機、`coverage_id` 編碼規則 |
| 讀 `HUNTING.md` | Phase 2 細節 | 認識 hunter prompt 與 critic wave | hunter prompt 8 段、promotion 程序、candidate gate、coverage critic |
| 讀 `VALIDATION-AND-REPORTING.md` | Phase 3–6 細節 | 認識驗證與報告契約 | 獨立 verifier、`findings.json` 三 verdict 契約、Phase 5 fresh eyes、REPORT/FINDINGS-DETAIL/NEEDS-VALIDATION |
| 讀 `ATTACK-CLASSES.md`（前段） | 認識攻擊分類 | 確認 companion 選擇邏輯 | 12 個 companion 域 + 6 個通用 class；依 codebase 類型選擇 |
| 讀 `report-schema.json`（前段） | 認識 findings 契約 | 佐證機器可讀輸出 | JSON Schema，`additionalProperties:false`，三 verdict oneOf |
| `webfetch` blog | 補背景脈絡 | 取得 harness 與 skill 關係 | 7 階段原始版、VDH/VVS、成本、數字（20,799→12,057→7,245） |
| 讀 `gh api .../commits` | 確認活躍度 | 版本演進 | 2026-09-10 大幅 rework workflow 與 validators；2026-09-14 釐清兩模式 |

**關鍵事實整理**

| 面向 | 內容 |
|---|---|
| 一句定位 | 讓 coding agent 變身安全稽核員的 skill：以隔離 agent 執行 recon→覆蓋導向 hunting→對抗式驗證→結構化輸出→獨立複核→報告 |
| 六階段 | 1 Recon／2 Coverage-led hunting／3 Candidate validation／4 Structured output／5 Independent record verification／6 Target-neutral report |
| 三類 verdict | `confirmed`（完整 source trace + 有界實測）／`needs_validation`（有精確未解事實、無 severity）／`rejected`（已被推翻） |
| 核心機制 | 攻擊者／發現者與驗證者身分分離；coverage-ledger 為唯一覆蓋主張；`.cjs` 確定性 validator 硬檢 schema 與 ledger；多次執行為 additive |
| 安裝 | `npx skills add https://github.com/cloudflare/security-audit-skill --skill security-audit`（`--global` 可選） |
| Requirements | 支援 tool use 與並行 sub-agent 的模型；Node.js；OS 強制沙箱（無外網、allowlist 環境、資源限制） |
| 限制 | 完整流程耗時耗算力（blog：單 repo 3–4 小時、最壞 14 小時，多 worker）；跑目標碼需真正系統級沙箱；單次只約找到反覆執行總數一半的漏洞 |

**發現的兩處出入**（需在報告中標記）

| 項目 | 影片／PR body 說法 | 一手來源實況 | 判定 |
|---|---|---|---|
| 安裝指令 | `npx skill add`（念作 mpx） | README：`npx skills add`（Skills CLI，skills.sh） | 以 README 為準 |
| 階段數 | 影片列 5 步、blog 稱 7-phase | README／SKILL.md：6 phases | 6 階段為對外現行版本；7 階段為 blog 描述的內部初始版，已演進 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Repo metadata 完整性 | stars/license/語言/時序/topics/releases | 完整（topics 為空、無 release/tag） |
| 文件覆蓋率 | README + tree + 6 個核心 md + schema | 完整，足以支撐報告 §1–§3 |
| 機制理解 | 6 階段、3 verdict、ledger 狀態機、verifier 獨立性 | 清晰 |
| 安裝與限制 | README requirements + blog cost | 已取得，含與影片的出入 |
| 背景脈絡 | harness 上位概念的歷史（Project Glasswing、VDH/VVS） | blog 已補；通用領域背景與替代方案留 C2 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 文件深度 | 只讀 README／讀 6 核心 md／逐 companion 精讀 | README + tree + 6 核心 md + schema 前段 | C1 目標為 metadata 與主要文件盤點；companion 細部與原始碼邏輯留 C2 |
| 是否讀滿 12 個 companion | 是／否 | 否，只讀 `ATTACK-CLASSES.md` 導引段 | companion 內容屬「清單」性質，對 §3 機制說明非必要 |
| blog 定位 | 視為行銷文略過／視為一手設計文件 | 視為一手來源並採信機制描述 | 由 Cloudflare 官方發布且與 repo 內容一致 |
| 出入處理 | 以影片為準／以 repo 為準／並列 | 以 repo 為準並列表標記 | repo 為現行可執行實況，影片為二手轉述 |
| metadata 的 topics/releases | 再嘗試其他 endpoint／直接記錄空值 | 直接記錄，不再深挖 | 對分析價值低，且已足夠 |

## 交接給 C2

- 補通用背景：LLM/agent 資安稽核的 false positive 問題、context window 限制、sandbox 隔離技術（unshare/gVisor/microVM）。
- 補替代方案：Strix、一般 SAST/DAST、Semgrep、multi-agent pentest 框架等，做 DA 表。
- 已可用來源：blog VDH/VVS 對照表與成本數字、MyBrain 既有 Strix 紀錄。
