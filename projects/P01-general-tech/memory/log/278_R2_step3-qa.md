# 278_R2_step3-qa.md

## 狀況理解

R2 為質問型追問（觸發 §5 User Q&A），三問同一軸：Hindsight 的複雜度是否正當。Step 2 已取得證據：可寫入型別僅 `world`／`experience`（軸＝誰在說）、observation 為 derived 且 PATCH 回 400、consolidation 背景自動且可關、TEMPR 四路＋RRF＋rerank、有 chunks 無 LLM 與 slim 輕量路徑。本 step 讀既有報告、覆核官方文件、查第二大腦判準，把三問沉澱進報告 §5，並補 §4.7 判準節。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀既有 `output/278_Hindsight.md` | 確認 §1–§4 既有內容 | 不刪改、只追加 | 取得 §4.0–4.6 判定總覽，§5 尚不存在 |
| 覆核 `gh api` retain/memories/recall/observations/mental-models/memory-banks/retrieval | 確認 Q1–Q3 事實 | 主張有據 | fact_type 軸為「誰在說」；observation 不升格；consolidation 可關；TEMPR＋RRF＋rerank；`chunks` 不呼叫 LLM |
| 重取 repo metadata | 校準時間座標 | 更新數字 | 30,861 stars、3,335 forks、MIT、pushed 2026-09-25 |
| 跑 mybrain-read：骨幹、判定總表、技術取捨準則、統一的兩端稅、TencentDB/EverOS/macro/LeanCtx/planning-with-files | 取 Q3 判準與同域對照 | 不照通則、標 URL 與信任層級 | 無 Hindsight 紀錄；統一兩端稅（draft）判準＝「同一件事 vs 不同的事」；TencentDB/判定總表為 AI 未-review 草稿 |
| 追加報告 §4.7 與 §5（Q1–Q3） | 沉澱本輪 QA | 既有 QA 不刪、序號遞增 | §5 新增 Q1／Q2／Q3 三條，拆題不併 |
| 跑 validate-report.sh 與 validate-step3.sh | 硬性驗證 | 確認合規 | 報告 20,903 字 < 50,000；log < 3,000 |

## 動作結束後的現狀

- **產出報告檔名**：`output/278_Hindsight.md`（沿用 R1 檔名）。
- **本輪變更摘要**：新增 §4.7「統一的兩端稅」判準節（Q3 對照尺，標 draft 未 review）；新增 §5 User Q&A Q1–Q3，各附表格與結論。§1–§4 既有內容未刪改。
- **Q1 落點**：可寫入僅二類（軸＝誰在說），事實／推論非標籤而是三層型別；標籤無法產生跨條合成信念。
- **Q2 落點**：升格路徑不存在；內建的是衍生合成，非升格規則；無獨立驗證閘門。
- **Q3 落點**：存與取皆工程化多階段架構為真，有輕量路徑；以分界判準 Hindsight 過，以 workflow 閘門不過。

## 其中的決斷點

| 意思決定面向 | 可選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 三問處理 | 合併為一題 | 拆 Q1／Q2／Q3 | AGENTS.md 明定同輪多子題須拆獨立 QA |
| 回應定位 | 護航 Hindsight | 以他判準檢核、明示不成立處 | 他可能真的 reject，不替他背書 |
| Q2 前提 | 照問回答升格 | 先修正「不存在升格」 | 官方明示 observation 永不升格 |
| Q3 判準 | 用「重不重」 | 用「同一件事 vs 不同的事」 | 兩端稅明示重量非判準 |
| §4 補充 | 只列通則 | 併入兩端稅 draft 並標未 review | skill 規則：AI draft 不可當他拍板 |
