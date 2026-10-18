# 309_R1_step1-intent.md

## 狀況理解

這是 R1，Issue #308 只給連結與「幫我調研這東西」，沒有指定分析面向、版本或比較對象。

技術標的判定為 `backnotprop/pstack`：Cursor `cursor/plugins/pstack` 的 standalone mirror，由 poteto（Cursor、React core team）撰寫。本體是純檔案化的 Agent Skills（`skills/<name>/SKILL.md`），可用 `npx skills add backnotprop/pstack` 安裝進 Claude Code、Codex、Pi、Cursor、OpenCode。內容含 16 個可獨立使用的 skill、需成組安裝的 `teach`／`why`／`architect`／`blast-radius` 等、24 個 `principle-*` 準則、`poteto-agent` 與 `comment-sicko` 兩個 subagent，以及入口 `poteto-mode`：依任務挑 23 個 playbook（bug fix、perf、feature、shipping、autonomous run 等）再路由到其他 skill，預設 opus 5.5／grok 分工。MIT，約 2.2k stars、24 commits。

使用者的意圖是「先理解這是什麼、解什麼問題」，不是指定導入評估；因此依 AGENTS.md 五問產出解析，並在替代方案一節對照他已跑過的 agent workflow／skill 方案。與 OpenSpec 主幹、mattpocock grill 的關係是隱含判準。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 執行 mybrain-read 的 refresh 並列出 `骨幹` tag 檔 | 確認是否已有既有判定與準則 | 先讀結論再定調意圖 | 鏡像更新至 cf70d51；取得 11 份骨幹檔 |
| grep `pstack`／`backnotprop` | 確認是否評估過同一標的 | 找到既有 verdict | **0 命中：第二大腦無此主題** |
| 讀 `GStack 學習` | 找同類 skill／工作流前例 | 避免重複推導 | 見下，屬同類但不同專案 |
| 讀 `判定總表` 與 `agent-skills` | 確認 skill 類方案的判定分布 | 取得他對 skill pack 的態度 | 見下 |
| 讀 `技術取捨準則`、`下一步清單` | 取得判準與當前優先序 | 校準 R1 的解讀 | 見下 |
| fetch GitHub repo README | 確認標的內容與定位 | 界定 §1～§4 範圍 | 取得 skill／playbook／principle 清單 |

查到的第二大腦內容（皆非 pstack 本身）：

| 檔案 | 內容與信任層級 | 對本案的意義 |
|---|---|---|
| [GStack 學習](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/GStack%20學習.md) | 判定「不採用」；`human:fatesaikou`／`stable`；2026-03-22。理由：多角色強制工作流＋防禦性提示詞＋每個 Duty 拆四檔，屬理解優先的抽取 | 與 pstack 同屬「用 skill 把工程紀律強制化」，但作者是 Garry Tan、架構不同。**不可當成他對 pstack 的舊結論** |
| [agent-skills](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/agent-skills.md) | 判定「觀望」，2026-08-11 由採用降級、未排入下一步；`human:fatesaikou`／`stable`；時間 2026-06-20 | 他對「24 個 skill＋生命週期命令」這類包裝已有一次降級經驗，R1 需分辨 pstack 是否只是同類再包裝 |
| [技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md) | 骨幹；`claude-code/opus-5`／`draft`；2026-08-01。理解優先；MVP→Feature 唯一閘門是「能否影響個人 workflow」；Reject≠沒價值；約束放 harness、不加人工審核關卡 | 替代方案與使用前提以此為軸，不以「比較快」論證 |
| [AI 開發 workflow 方案比較](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/AI開發workflow方案比較.md)／[三案實測](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/AI開發workflow實測.md) | 皆 `claude-code/opus-5`／`draft`；2026-08-02。定案為 OpenSpec 主幹、mattpocock grill 對齊、superpowers 降為 Reserve | pstack 的 playbook 與 superpowers 強流程同型，§4 需對照此定案 |
| [下一步清單](https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md) | 骨幹；`claude-code/opus-5`／`draft`；2026-08-11。無 pstack 條目；技術側有 context 治理工具比較等待辦 | 本案不是既有動作，屬新輸入 |
| [LearnGhAgent](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/LearnGhAgent.md) | `human:fatesaikou`／`stable`；2026-07-26 | 本次調研的 harness；與 pstack 的 skill 化路線同問題域 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 技術標的 | 從 PR body 與 README 交叉確認 | `backnotprop/pstack`，Cursor plugin 的 standalone mirror |
| 輪次 | 檢查 `memory/log/` 有無 309_ 前綴檔 | 無前輪，確認 R1 |
| 分析範圍 | 依 AGENTS.md 五問 | 四節必備；本輪無提問故不追加 §5 |
| 既有判定 | grep 全 bundle | pstack 無紀錄；僅有 GStack、agent-skills、superpowers 等相鄰前例 |
| 使用者約束 | 讀骨幹與取捨準則 | 理解優先、workflow 閘門、harness 驗證 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 意圖判定 | 只做摘要／完整五問 | 完整五問解析 | Issue 只給連結；AGENTS.md 已固定報告格式，他慣例是先理解再判定 |
| 標的邊界 | Cursor 原版／standalone mirror | 以 mirror 為主，標明上游 | 使用者給的是 mirror；其多 harness 改寫與 OpenCode 環境直接相關 |
| 與 GStack 的關係 | 他的舊結論／同類前例 | 同類前例，明確區隔 | 作者與架構不同；講成他的判定會製造錯誤記憶 |
| 分析焦點 | 純通用／對照現行 workflow | 通用為主，§4 對照 OpenSpec、superpowers | 五問要求替代方案；其定案是判斷切入點差異的必要背景 |
