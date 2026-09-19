# 263_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認標的為 `scientific-agent-skills`（K-Dense-AI/scientific-agent-skills，issue #260），屬新技術評估，第二大腦無既存判定。C1 為 Step 2 第一個調研 sub-step，任務是取得 repo metadata、主要文件與背景脈絡，為後續 C2 收斂分析打底。此 step 只做「收集與摘要」，不下結論。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` + `gh api repos/...` | 取得 repo metadata | 掌握 stars、license、語言、更新時間、topics | 取得完整 metadata（見下） |
| `gh api .../contents/` | 列出 repo 根目錄 | 判斷文件結構 | 見 plugin.json、pyproject.toml、docs/、skills/、AGENTS.md 等 |
| 抓取 README.md（raw，971 行） | 取得主要文件 | 理解定位、功能、用法、範例 | 取得 17 個一級標題、詳細分類與 6 組 workflow 範例 |
| 抓取 docs/skills.md（250 行） | 取得 skill 總表 | 掌握 166 個 skill 的領域分布 | 取得全部分類與 skill 清單 |
| 抓取 AGENTS.md、plugin.json、pyproject.toml | 理解規格與打包 | 掌握 skill 標準與結構契約 | 確認 Agent Skills spec + Agent Plugins 1.0.0 打包 |
| 抓取 pkpd-modeling/SKILL.md | 抽樣看單一 skill 結構 | 掌握 skill 內部格式 | 取得 frontmatter（name/description/license/allowed-tools）+ 3 rules + scripts 表 |
| webfetch arXiv:2609.00065 | 補查論文背景 | 掌握學術定位與量測數據 | 取得論文摘要（163/166 skills、7.1% token、24% workflow） |
| 補查背景（agent-skills 標準、anthropics/skills 關聯） | 理解標準脈絡 | 定位該 repo 在 agent skill 生態中的位置 | 確認 docx/pdf/pptx/xlsx 為 Anthropic 上游 vendored |

**Metadata 重點**：
- stars 45,516、forks 4,126、subscribers 195、open issues 13、MIT license、language Python
- created 2025-10-19、pushed 2026-09-14、default branch main、homepage = arXiv:2609.00065
- topics：agent-skills、ai-scientist、bioinformatics、cheminformatics、genomics、drug-discovery、claude-skills 等 17 個

**主要文件結構**：`skills/`（166 skill 目錄，每目錄含 SKILL.md 必選、references/scripts/assets 選選）、`docs/`（skills.md、examples.md、security-report）、根目錄 plugin.json（Agent Plugins 1.0.0 manifest）+ pyproject.toml（version 2.69.0）。

**skill 分類**（docs/skills.md 25 個小節）：Scientific Databases & Data Access、Scientific Integrations（LIMS/雲端/實驗室自動化/ELN/Workflow/顯微鏡/Protocol）、Scientific Packages（生物資訊、化學資訊、藥理、蛋白質、ML/DL、材料、工程、數據分析、演化、Agent 框架、科學寫作、文件轉換、監管標準）、Scientific Thinking（方法論、決策分析、Web 檢索）。README 歸納為 5 大類：100+ 資料庫、70+ Python 套件、9 科學整合、30+ 分析通訊、10+ 研究臨床。

**paper 論文摘要**：163 個 procedures、16 個 practice areas；每個 skill = 一個以「版本化、人讀的 instruction 檔」為核心的目錄，agent 僅在任務觸發時載入。量測：163 個 skill 的常駐 description 佔 200k token window 的 7.1%；median workflow 佔 23.9%（但 29/46 若載入全部 references 會 overflow）。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo 存在與公開狀態 | `gh repo view` / API | 存在、公開、MIT、可存取 |
| 規模與成熟度 | metadata | 45.5k stars、4.1k forks，2025/10 建立、活躍維護（2026/09 仍 push） |
| 技術定位 | README + paper | 「把任意 AI agent 變 AI Scientist」，Agent Skills 標準，論文 arXiv:2609.00065 |
| 內容結構 | README + skills.md + AGENTS.md | 166 skill、明確 in-scope/out-of-scope、結構契約與測試規範 |
| 標準與打包 | plugin.json + pyproject + AGENTS.md | 同時為 Agent Skills 集合與 Agent Plugins 1.0.0 套件 |
| 學術依據 | arXiv 摘要 | 有正式論文，含 token 成本量測，**無 task-level 評估、無 host selection rate** |
| 安全機制 | README Security 章節 | Cisco AI Defense Skill Scanner 每週掃描、發布 security-report、建議使用者自行 review |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否逐個讀取 166 個 SKILL.md | 1. 全部抓取 2. 抽樣（pkpd-modeling）+ 靠 skills.md 總表 | 抽樣 + 總表 | 166 個全抓會爆 token 且超出 C1 範圍；總表 description 已含每 skill 摘要 |
| 背景脈絡來源 | 1. 只靠 README 2. 加上 arXiv 論文 | 加上論文 | README 是行銷口吻；論文給出可量化機制與侷限，補足「文章沒寫的」 |
| 是否深入 Anthropic 上游關係 | 1. 追查 docx/pdf/pptx 上游 2. 僅記錄 vendored 事實 | 僅記錄 | 屬次要細節，留待報告 §4 替代方案討論，不必在 C1 深挖 |
| C1 與 C2 分工 | 1. C1 就開始比較替代方案 2. C1 只收集 | 只收集 | 替代方案與 DA 表屬分析收斂（後續 sub-step），C1 聚焦取得原始資料 |
