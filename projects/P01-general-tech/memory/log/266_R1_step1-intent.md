# 266_R1_step1-intent.md

## 狀況理解

本輪為 R1，PR body 給定技術標的 `tt-a1i/archify`（GitHub 連結，無其他附帶條件）。archify 是一個「給 AI Coding Agent 的架構圖 Skill」：Node.js 渲染＋驗證系統，agent 產出 typed JSON IR，archify 以確定性方式編譯成自含 HTML/SVG。支援 architecture / workflow / sequence / data-flow / lifecycle 五種圖型，具 Before/Delta/After 快照比對（PR review）、原子驗證後才交付、failure 帶 repair receipt。MIT、66.8k stars、259 commits，作者為 tt-a1i。

技術標的為「圖表／架構圖生成 Skill」，屬 diagram-as-code 域。本輪為初次分析，無 R2 追問脈絡。

## 執行的動作與結果

Step 1 定調前先查第二大腦（mybrain-read），確認三件事：

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 PR body | 理解調研標的與附帶條件 | 鎖定 archify | 標的＝`tt-a1i/archify`，無附加條件 |
| 查 `技術/技術評估/判定總表.md` 與全量 grep `archify` | 確認是否已評估過此標的 | 若有，帶回判定與理由 | **無 archify 此標的**。全 bundle grep `archify` 零命中 |
| grep `diagram` / `架構圖` / `architecture` 於 `技術/` 與 `專案/` | 找同類圖表 skill 的既有判定，供報告對照 | 取得同品類判決 | 命中同類 **diagram-design**（Reject）、**Hallmark**（觀望）、**OpenDesign**（採用），皆為「design／圖表 skill for agent」；另 `下一步清單.md` 有 DeepSeek V4 Flash Vision Exp（涉及讀「架構圖」） |
| 讀 `專案/下一步清單.md`、`技術/動手做/專案現況表.md` | 確認與哪個進行中專案相關 | 找到所屬專案脈絡 | 無直接對應專案。相關連點：archify 內建 `deepseek-harness` 整合，而 deepseek-harness 在技術評估為**觀望**（Reserve） |
| 讀 `抽象理解/本質洞察/技術取捨準則.md`（骨幹） | 取相關取捨準則 | 用他的判準框定報告 | 三條關鍵準則：①理解優先——不穩定或不熟先自己兜，MVP 是理解驗證點，目的在理解本質非省成本；②MVP→Feature 唯一閘門＝能否影響個人 workflow；③Reject＝不採用≠沒價值，仍抽取需求理解與方案方向 |

**關鍵對照**：第二大腦無 archify 舊結論，但此標的與已判 Reject 的 **diagram-design** 高度同軸——使用者當時拒 diagram-design 主因是「我的目的是解構／理解抽象概念，它是出版工具不是思考工具，對我的目的過重」。archify 同屬「圖表渲染＋交付」系統，且加碼確定性驗證與 PR review 快照比對，此矛盾點必須在報告中正面處理。

查證來源與信任層級：

- `https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md`（generated.by: `ollama-cloud/deepseek-v4-flash`，status: `draft`）——無 archify 條目；有 diagram-design（Reject）等。**AI 草稿，未 review**。
- `https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/diagram-design.md`（generated.by: `process:learn-gh-agent`，status: `draft`）——Reject 理由：目的為理解抽象概念，此類出版工具過重。**機器產出，使用者定案**。
- `https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md`（generated.by: `claude-code/opus-5`，status: `draft`）——無此標的；有 DeepSeek V4 Flash Vision 讀架構圖待試。**AI 草稿，未 review**。
- `https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md`（骨幹，status: `draft`，`generated.by: claude-code/opus-5`）——「原話：」引號內為使用者本人結論，直接引用為準則。

**第二大腦無 archify 此主題** 成立：未查到 archify 或其同源 skill 的舊評估、結論或專案關聯。報告以通用技術知識為主，但可引用 diagram-design 的同品類 Reject 判定作為對照，不冒充為「他對 archify 的舊結論」。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 標的明確性 | PR body 解析 | 單一技術 `archify`，無歧義、無附加條件 |
| 既有評估 | 第二大腦全量 grep（archify／diagram／架構圖／architecture） | 無 archify 舊判定；有同類 diagram-design（Reject）可對照 |
| 專案關聯 | 下一步清單＋專案現況表比對 | 無直接所屬專案；連點僅 deepseek-harness（觀望）整合 |
| 取捨準則 | 技術取捨準則骨幹檔 | 取得理解優先、workflow 閘門、Reject≠沒價值三條判準 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 標的判讀 | 依 README 判為架構圖 Skill；抽成外部 script | 判為 archify（diagram-as-code／架構圖生成 Skill） | AGENTS.md 明定技術名由 LLM 判斷、不抽 script |
| 第二大腦查詢結果處理 | 用通用知識填空；明說「無此主題」再用通用知識＋引用同類判定 | 明說「第二大腦無 archify」，報告以通用知識為主、引 diagram-design 為對照 | AGENTS.md 與 skill 規定不可把 AI 草稿講成他的結論 |
| 報告論述基調 | 依市場效率（用現成比較快）；依理解優先＋workflow 閘門 | 依理解優先＋workflow 閘門，正面處理「archify 是否重蹈 diagram-design Reject」的矛盾 | 使用者的判準，且此標的與既有 Reject 同軸，為最有價值論點 |
