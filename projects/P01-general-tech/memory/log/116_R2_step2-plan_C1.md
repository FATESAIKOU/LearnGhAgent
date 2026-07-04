# 116_R2_step2-plan_C1.md

## 狀況理解

R2 為使用者追問輪，Q1 質疑 DESIGN.md 的本體定位（格式標準 vs Markdown 檔案），Q2 要求表格化列出目標使用效果/前提/方式/副作用。本 step 為 R2 的資料收集，目標是補足 R1 未深入挖掘的面向：

1. **Q1 所需**：spec.md 中對「format specification」的明確定義、Consumer Behavior 章節、PHILOSOPHY 對 prose/token 關係的論述
2. **Q2 所需**：CLI 工具實際使用方式（package.json、bin 入口）、其他範例（驗證使用模式）、.agents/skills/ 目錄（了解專案自身如何實踐 agent-first 設計）
3. **背景補查**：專案自身使用的 agent skills（agent-dx-cli-scale, ink, tdd, typed-service-contracts）是否提供額外脈絡

## 執行的動作與結果

| 動作 | 目的 | 預期效果 | 實際結果 |
|------|------|----------|----------|
| `gh repo view` 取得最新 metadata | 確認 R1 後 repo 是否有變化 | stars/forks/license 等 | 成功：24.7k stars, 1.9k forks, Apache-2.0, TypeScript，與 R1 一致 |
| 讀取 README.md | 確認 Q1/Q2 相關段落 | 取得格式定義與 CLI 使用說明 | 成功：明確說明「format specification」定位，含 lint/diff 範例 |
| 讀取 docs/spec.md（完整 365 行） | 取得完整格式規格，特別是 Consumer Behavior 章節 | 確認 spec 對「格式標準」的定義 | 成功：spec 第 6 行明確寫「A format specification」；Consumer Behavior 章節（L354-365）定義 6 種未知內容處理規則 |
| 讀取 PHILOSOPHY.md | 取得 prose/token 關係論述 | 確認「prose > tokens」原則 | 成功：PHILOSOPHY 明確指出「prose is where the design lives」「tokens are context」 |
| 讀取 .agents/skills/ 下 4 個 SKILL.md | 了解專案自身如何實踐 agent-first | 取得 meta 脈絡 | 成功：agent-dx-cli-scale（CLI 評分框架）、ink（terminal renderer）、tdd（測試流程）、typed-service-contracts（型別安全架構）— 皆為獨立技能，非 DESIGN.md 核心 |
| 讀取 packages/cli/package.json | 確認 CLI 工具版本與發布狀態 | 取得 bin 入口、版本號、相依套件 | 成功：v0.3.0，bin 為 `design.md` / `designmd`，發布至 wombat-dressing-room.appspot.com |
| 讀取 examples/paws-and-paths/DESIGN.md | 取得第二個範例 | 驗證不同規模的設計系統使用模式 | 成功：Material You 風格的 50+ color tokens + 完整 typography scale |
| 讀取 examples/totality-festival/DESIGN.md | 取得第三個範例 | 驗證暗色主題設計系統 | 成功：暗色主題 + Space Grotesk/Inter 字型組合 |
| 讀取 docs/spec.md 中 Consumer Behavior 章節 | 精確回答 Q1 的「格式標準 vs Markdown」定位 | 取得 spec 對未知內容的處理規則 | 成功：6 種 scenario（unknown section/color/typography/spacing/component/duplicate）的明確行為定義 |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 驗證結果 |
|----------|---------------|----------|
| Q1 所需證據 | spec.md 是否明確自稱 format specification | 是：L6「A format specification for describing a visual identity to coding agents」 |
| Q1 所需證據 | Consumer Behavior 章節是否存在 | 是：L354-365，定義 6 種 scenario |
| Q1 所需證據 | PHILOSOPHY 是否區分 prose/token 角色 | 是：明確指出「prose is where the design lives」「tokens are context」 |
| Q2 所需證據 | CLI 工具版本與使用方式 | 是：v0.3.0，`npx @google/design.md lint/diff/export` |
| Q2 所需證據 | 多個範例驗證使用模式 | 是：3 個範例（atmospheric-glass glassmorphism、paws-and-paths Material You、totality-festival 暗色主題） |
| Q2 所需證據 | 使用前提（Node.js 需求） | 是：package.json 確認 bun/Node.js 環境 |
| 背景脈絡 | .agents/skills/ 是否提供額外資訊 | 4 個 skills 皆為通用開發技能，非 DESIGN.md 專屬，不影響 Q1/Q2 回答 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|----------|----------|----------|----------|
| 是否讀取全部 3 個範例 | 只讀 R1 已讀的 atmospheric-glass / 補讀全部 | 補讀全部 | Q2 的「使用方式」需多個實例佐證，不同規模的範例可展示使用模式的多樣性 |
| 是否讀取 .agents/skills/ | 是 / 否 | 是 | 了解專案自身如何實踐 agent-first 設計，但結果為 4 個通用技能，不影響 Q1/Q2 |
| 是否讀取 spec.md Consumer Behavior 章節 | 是 / 否 | 是 | 該章節直接回答「格式標準 vs Markdown 檔案」的定位問題 |
| 是否搜尋外部文章補背景 | 是 / 否 | 否 | R1 已涵蓋完整背景，Q1/Q2 的答案皆可在 repo 內文件找到 |
