# 222_R1_step1-intent.md

## 狀況理解

使用者（R1，首次請求，無前輪）要求調研外部簡報「expiration-date-of-sdd」（仕様駆動開発的賞味期限），來源為 speakerdeck.com/watany/expiration-date-of-sdd。技術標的為「仕様駆動開発（Spec-Driven Development, SDD）」。使用者特別在意三點：(1) 這種開發方式的適用場景、條件、成本與效果；(2) 簡報所稱「賞味期限」的意涵；(3) 對其個人工作流的影響。第三點是個人化問題，需對照其第二大腦的既有 workflow 與技術取捨準則，不能只做通用技術分析。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 PR body | 確認技術標的與附帶條件 | 取得完整需求 | 標的為 SDD 簡報，附帶 3 個子面向（適用場景/成本效果、賞味期限、個人工作流影響） |
| 讀取 know/AGENTS.md | 確認 step 流程與輸出規範 | 確保 log 格式正確 | 確認 4-section 格式、3500 字上限、檔名規則 |
| 讀取 judge/step1-intent.md | 確認軟性驗證觀點 | 確保產出符合 review 判準 | 確認需含 MyBrain 查詢紀錄、帶 URL 與信任層級 |
| 執行 mybrain-read（refresh + 骨幹 + grep） | 確認標的是否已評估、與哪個專案相關、有無取捨準則 | 取得個人化脈絡 | 見下方查詢結果 |

**MyBrain 查詢結果：**

| 發現 | GitHub URL | 信任層級 | 時間 |
|---|---|---|---|
| 第二大腦無「仕様駆動開発／SDD／spec-driven」的技術評估檔，判定總表 86 筆中無此主題 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md | generated.by: `ollama-cloud/deepseek-v4-flash`；status: `draft` | 2026-08-02 |
| 唯一相關線索：agent-skills 的 `/spec` 命令啟動 `spec-driven-development` skill，原則「Spec before code」——但該檔 2026-08-11 已由「採用」降級為「觀望」（判定成立但未排入下一步清單） | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/agent-skills.md | generated.by: 未標明；status: `draft`（判定總表內註明降級） | 2026-06-20 |
| 技術取捨準則：理解優先（不穩定或不熟悉先自己兜，MVP 是理解驗證點）；MVP→Feature 唯一閘門是「能否影響個人 workflow」；Reject＝不採用≠沒價值 | https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md | generated.by: `claude-code/opus-5`；status: `draft` | 2026-08-01 |
| 下一步清單：無任何與 SDD 直接相關的進行中專案；「個人 AiAgent 入口」等技術評估卡點與 SDD 無關 | https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md | generated.by: `claude-code/opus-5`；status: `draft` | 2026-08-11 |

**第二大腦無此主題**：SDD 本身未被評估過，無既有判定可引用。上述 agent-skills 的 `/spec` 是唯一沾邊線索，且屬 AI 草稿、未經本人 review，僅作背景參考，不得當成他的舊結論。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 技術標的 | 從 PR body 提取 | 仕様駆動開発（SDD），來源為 watany 的 speakerdeck 簡報 |
| 分析範圍 | 3 個子面向 | 適用場景/條件/成本/效果、賞味期限意涵、個人工作流影響 |
| 輪次 | 檢查 memory/log/ 中 222_ 前綴檔案 | 無前輪，確認為 R1 |
| 個人化脈絡 | 查 MyBrain 判定總表、技術取捨準則、下一步清單 | SDD 無既有判定；取捨準則可作為「個人工作流影響」的對照框架 |
| 輸出格式 | 對照 AGENTS.md Step 1 規範 | 4-section 格式符合要求 |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 技術標的判定 | 簡報本身 / SDD 方法論 | SDD 方法論（以簡報為主要素材） | 使用者要「調研理解內部的內容」，標的是簡報所講的 SDD，簡報是素材非標的 |
| 個人工作流影響的處理 | 通用分析 / 對照 MyBrain 取捨準則 | 對照 MyBrain 取捨準則 | 使用者明確問「對我個人工作流的影響」，需用其「MVP→Feature 閘門」等準則評估，不能只做通用分析 |
| 賞味期限的詮釋 | 字面翻譯 / 依簡報脈絡理解 | 依簡報脈絡理解 | 使用者問「他說的賞味期限是甚麼」，需從簡報內容推導其定義，非字面翻譯 |
| 資訊缺口 | 直接產出 / 先補查簡報內容 | Step 2 補查簡報全文 | 目前僅有 speakerdeck 連結，簡報實際內容需在 Step 2 抓取後才能分析 |
