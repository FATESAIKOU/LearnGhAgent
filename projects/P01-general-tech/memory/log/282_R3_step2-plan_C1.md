# 282_R3_step2-plan_C1.md

## 狀況理解

- R3 為 Laya 調研的**收尾輪**，使用者判**不採用（Reject）**並列 4 點。本 sub-step C1 不重做 R1/R2 調研，而是針對 R3 意圖執行三件調研：
  1. **覆核命題**：第 1 點「比起 Jev 只是多了個框架」、第 2 點「準確度還差」是否被外部證據支持。
  2. **抽取方案方向**（依骨幹 `技術取捨準則`：Reject≠沒價值）：Laya 有哪些非自迴歸決策零件可與「判斷／不確定性」構想掛鉤。
  3. **為未來觸發條件備料**：第 4 點「之後可能寫**收斂 LLM 不確定性**的程式」，Laya 的 confidence 機制是否為該線素材。
- Step1 已定調：標的 `NandhaKishorM/laya`；第二大腦 `Laya` 零命中、`Jev` 判**試用**；「收斂 LLM 不確定性」零命中（與 `AiStorage` 的「收斂 AI」同詞不同義）；4 點無質問句構 → **§5 不觸發**。
- 依 `do/skills/document/SKILL.md`：①metadata ②主要文件 ③背景脈絡。因 R2+ 不重做 R1，本次僅取「自 R2 後的差異」與「命題覆核所需的獨立證據」。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view`＋`gh api repos/…` | 更新 metadata | 掌握自 R2 後的變化 | stars **30,954**（R2 25,335）、forks 2,726、open issues+PR 83；Apache-2.0；created 09-18、pushed **10-05（當日）** |
| `gh release list`＋`commits` | 追版本與近期開發 | 判斷是否已改善 R2 弱點 | 最新 **v0.3.28**（10-05），較 R2 的 v0.3.20 再進 8 版；近期多為合併社群 PR |
| `curl` raw README（1,788 行） | 取差異化條目 | 找對「準確度」的新證據 | 新增 `predict_tournament`（#950）、order-invariant 權重、`laya-train` CLI、`Router.register`、abstention 修正 |
| `curl` raw BENCHMARKS.md、`docs/staged-adoption.md` | 交叉驗證官方數字與系統層方法 | 覆核命題 1（框架） | 系統層確有 Router／Jev 相容 HTTP／MCP／LangChain／hooks／staged adoption／calibration 全套 |
| `gh api` issues #450、#555、#963 | 取**獨立第三方**與新 bug | 覆核命題 2（準確度） | #450 laya 0.780 vs Jev 0.919；#555 laya 0.686 vs Jev 0.907（9 項全落後）；#963 預設 4 epoch 在小資料集靜默坍縮 |
| `curl` research/benchmarks/feishu_zh/README.md | 取**中文**情境獨立診斷 | 貼近使用者中文落地場景 | 64 筆中文職場決策：Laya multilingual choice **20/64** vs Jev **64/64**（archived 09-21） |
| `curl` HF `api/models`（三權重） | 量化社群採用 | 判斷是否已成生態 | root likes **5,226**（R1 3.73k）、downloads 11,733；三 repo 皆 `commercial-use`／Apache-2.0 |
| `curl` pyproject.toml、docs/index.md | 確認套件邊界與系統層清單 | 支撐「框架」定性 | 依賴僅 torch/transformers 等；無雲端 SDK；docs 列 routing/staged-adoption/hooks/evals 等系統層 |

**命題覆核（R3 第 1、2 點）：**

| R3 命題 | 支持證據 | 反證／限縮 | 判定 |
|---|---|---|---|
| ①「比 Jev 只是多了個框架」 | Laya 相對 Jev（封閉 API）的實質增幅確在系統層：Router 選 checkpoint、`POST /v1/systemone` 相容協定、MCP／LangChain／LangGraph、hooks 觀測、`staged-adoption`、calibration 流程；R1/R2 亦已確認權重為自訓非 Jev fork | 「框架」之外仍有兩項非框架物：Apache-2.0 開放權重（Jev 無）與 proper-scoring 校準的 `answer_confidence`；是否算「只是框架」屬價值判斷 | **事實層成立**：判斷品質未超越 Jev，增益集中於可自架／可微調／可整合 |
| ②「準確度還差」 | 三則獨立評測一致落後 Jev：#450 0.780 vs 0.919（英文聯邦採購、quote-graded）；#555 0.686 vs 0.907（9 suite）；feishu_zh 中文 20/64 vs 64/64。官方自陳 base zero-shot 0.362 近隨機（majority 0.461） | 官方微調版 `laya-typed-decisions` 在 typed-decisions 達 **0.766 > Jev 0.727**；v0.3.28 的 tournament 將 Banking77 由 0.430 升 0.610 | **成立**：微調單一 benchmark 可勝，但跨任務、跨語言（尤其中文）仍普遍落後 |

**可抽取的方案方向（供骨幹「抽方案方向」）：**

- **判斷/不確定性零件**：非自迴歸 encoder＋決策頭（單次 forward pass 出 choice／score／noul）；`confidence`＝1−正規化熵、`answer_confidence`＝所報答案機率；訓練以**嚴格 proper scoring rule**（log＋spherical＋RPS）的 RLCD，使 confidence 具統計意義。
- **系統層方法（語言無關、可移植）**：Router 於 forward 前判語言（<0.5ms 純 Python）；`staged-adoption` 的 shadow→compare→policy→bounded promote；`min_confidence` abstention 三態（passed／abstained／unevaluated）。
- **與未來觸發點（收斂 LLM 不確定性）的接口**：Laya 的 proper-scoring confidence 正是「把不確定性數值化並可分流」的零件；但 R3 判定不採用，故**僅記錄為素材**，不建議現在引進。

**新揭露的負面事實（R2 未見）：** 官方 issue #963（10-05）：`laya.train` 固定 4-epoch 預設在數百～千筆小資料集會**靜默坍縮至類別先驗**（25 次中 24 次訓練 CE 停在 ln K），收斂取決於 seed（15 次中 6 次未跳脫）。意涵：Laya「可微調」的門檻比 R2 呈現的高——小資料集需 8–32 epoch 與早停，否則失敗無告警。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 是否為收尾輪 | 檢視訊息 | 是：明示 Reject，無新事實需求 |
| 命題①可覆核 | 系統層清單 vs 非框架實質項 | 可覆核：事實層成立，定性屬價值判斷 |
| 命題②可覆核 | 3 則獨立 eval＋官方自陳 | 可覆核：跨任務／語言普遍落後；單一微調 benchmark 例外 |
| 抽取素材齊備 | 架構碼、訓練目標、系統層方法 | 齊備；且與「不確定性收斂」接口明確 |
| 未來觸發點對位 | 第二大腦「收斂 LLM 不確定性」零命中 | 屬新線；Laya 僅為素材，非既有結論 |
| R3 不重做 R1 | 本次僅取差異與覆核證據 | 未重複 R1 已載事實 |
| §5 觸發 | 檢視句構 | 否：4 點為判定與理由，無質問句構 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研範圍 | ①重跑 R1 全調研 ②只取差異與覆核證據 | ② | workflow 指示 R2+ 針對本輪意圖；R3 無新事實需求 |
| 命題 2 證據來源 | ①僅官方 BENCHMARKS ②加獨立第三方＋中文診斷 | ② | 帶質疑命題須非官方證據；中文落地貼近使用者 |
| Reject 後處理 | ①整案封存 ②依骨幹抽需求理解與方案方向 | ② | `技術取捨準則` 明定 Reject≠沒價值 |
| 未來觸發點落點 | ①併入 `AiStorage` 的「收斂 AI」②獨立記錄為新線 | ② | 兩者同詞不同義，混淆會誤導後續 |
| 是否建議採用 | ①推薦作為不確定性零件 ②只記錄素材 | ② | R3 已判不採用，C1 不自作推薦 |

> 註記（作者未寫、自行推測）：README 未載完整 base 訓練配方；#963 顯示微調預設對小資料集不友善，官方尚未修正（issue 仍 open）。
