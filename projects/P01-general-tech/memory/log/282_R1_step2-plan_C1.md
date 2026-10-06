# 282_R1_step2-plan_C1.md

## 狀況理解

- 本 sub-step C1 為 R1 調研第一段：取得 **Laya** 的 repo metadata、主要文件、背景脈絡，作為後續 sub-step（Jev 對照、替代方案 DA、報告收斂）的原料。
- 依 `do/skills/document/SKILL.md` 標準動作：①`gh repo view`／`gh api` 取 metadata ②擷取 README 與關鍵子文件 ③補查背景脈絡。
- Step 1 已定調：標的＝`NandhaKishorM/laya`，對齊 Jev（`/tmp/mybrain` 已判試用）與使用者原話構想；報告須保留「快 X 倍數字取自第三方、未統一基準」的反面論證。
- 預期產出：可支撐報告 §1／§2／§3 的硬事實（架構、訓練法、部署方式、限制），以及 §4 替代方案所需的生態座標。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view`＋`gh api repos/…/laya` | 取 repo metadata | 掌握規模、授權、活躍度 | Apache-2.0；24,965 stars／2,162 forks／97 watchers；413 commits／30 contributors；open issues 44、closed 73；default branch `main`；最新釋出 v0.3.20（09-24），pushed 09-25；topics 含 `jev`、`modernbert`、`typed-decisions`、`rlcd` |
| `gh api …/git/trees/main?recursive=1` | 掃描結構定位關鍵子文件 | 找出訓練碼／文件／benchmark | 主要為 `laya/`（Python 套件）、`laya-ts/`（TypeScript 埠）、`docs/`、`benchmarks/`、`research/`（含 `feishu_zh` Laya/Jev 配對評測、`zh_short_commands`）、`notebooks/`、`tests/` |
| `curl` raw README.md（65KB） | 取主要文件 | 取得安裝／Quickstart／架構／限制 | 三 checkpoint、Router、三 primitive（choice/score/noul）、部署方式、Honest Limits 全數取得 |
| `curl` raw BENCHMARKS.md（22KB）、AGENTS.md、docs/index.md、staged-adoption.md、test_training.py、pyproject.toml、LICENSE | 取次級文件與程式事實 | 驗證文件宣稱與實作一致 | BENCHMARKS 明載 51 語言／7 主題／校準／速度；`proper_reward` 實作嚴格 proper scoring rule；pyproject extras＝serve/fast/mcp/onnx/langchain；Apache-2.0 |
| `gh release list`／`gh api contributors`／`search/issues` | 取釋出節奏與社群規模 | 判斷專案活躍與成熟度 | 09-18 建立後 6 天內釋出 15+ 版（v0.3.6→v0.3.20），開發極密集 |
| `webfetch` HF 模型卡（root／multilingual／typed-decisions） | 取權重、like、衍生模型數 | 量化社群採用 | root 3.73k likes；multilingual 282；typed-decisions 112；61 finetunes、34 quantizations、38 spaces |
| `webfetch` Dev.to 作者文＋arXiv 2503.23303／2510.01237 | 補背景脈絡 | 取得動機與前作 | 作者自陳 Mar 2025 SalesRLAgent、Sep 2025 Confidence-Aware Routing，主張概念早於 Jev；Jev 對照數據為第三方（AbdelStark、nibzard） |

**關鍵事實（供報告引用）：**

| 面向 | 內容 |
|---|---|
| 定位 | Non-autoregressive System 1 decision engine：不生成文字，單次 forward pass 輸出型別化判斷 |
| 三 primitive | `choice`（選項分佈）、`score`（序位期待值）、`noul`（P(true)） |
| 三 checkpoint | `laya`（ModernBERT-large 421M、512 ctx、英文）、`laya-multilingual`（mmBERT-base 322M、1024/8192、100+ 語言）、`laya-typed-decisions`（421M、1024、微調版） |
| 架構 | 雙向 encoder ＋ 決策頭（2 層 transformer＋option-marker scorer＋act/escalate head）；每選項於自身 `[MASK]` 打分後 softmax |
| 訓練 | RLCD：REINFORCE＋group-mean baseline（GRPO-style），reward＝嚴格 proper scoring rule（log＋spherical＋RPS） |
| 部署 | pip、CLI、`laya-serve` HTTP（相容 Jev `POST /v1/systemone`）、MCP、LangChain／LangGraph、Docker、Nix、ONNX、TileLang 快路 |
| 校準 | 訓練用 proper scoring rule；`confidence`＝1−正規化熵；`answer_confidence`＝所報答案機率；出廠 over-confident 需自行 fit temperature |
| 自我揭露限制 | base zero-shot 近隨機（0.362／0.352 vs majority 0.461，微調後 0.766）；`noul` 可能跟標籤而非 state（#156）；choice >20 選項 token 預算崩（Banking77 0.425 vs Jev 0.870）；`score` 最弱（SST-5 0.372）；英文 checkpoint 非英文崩且仍高信心（Khmer 0.000@0.952）→ 故 router 於 forward 前判語言 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| metadata 齊備 | stars／license／分支／釋出／貢獻者 | 全部取得，無缺 |
| 主要文件齊備 | README／BENCHMARKS／docs／AGENTS／訓練測試 | 全部取得 |
| 文件與實作一致 | test_training.py 內 `proper_reward` vs README RLCD 宣稱 | 一致：reward 具嚴格 properness 檢驗 |
| 背景脈絡齊備 | 作者文＋兩篇 arXiv＋Jev 對照來源 | 取得；Jev 數字確為第三方、未統一基準 |
| §4 替代方案原料 | repo topics／生態（MCP/LangChain/社群埠） | 已具雛型；同級替代需 C2 補 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| metadata 取得方式 | ①`gh repo view --json` ②`gh api` | ②為主 | `--json` 不支援 `topics`，`gh api` 一次取全欄位（stars/forks/issues/topics） |
| 文件取得方式 | ①webfetch ②raw curl | ② | raw 無 HTML 雜訊、可存檔比對，且 README 達 65KB |
| 文件取捨 | ①只讀 README ②README＋BENCHMARKS＋訓練碼 | ② | 影片質疑「數字來源／格式正確答案不正確」，須以 BENCHMARKS 與實作交叉驗證 |
| 作者主張處理 | ①照抄「早於 Jev」當事實 ②標為作者自陳 | ② | 兩篇 arXiv 標題與 Laya 架構不同（銷售轉換／confidence routing），非直接前身，須與通用背景分述 |
| 本 sub-step 範圍 | ①含替代方案 DA ②只做 metadata＋主文件＋背景 | ② | Jev 對照與替代方案屬 C2；此 log 保持單一目的 |

> 註記（作者未寫、自行推測）：README 未提供訓練超參細節與資料集清單，僅 notebook 載入 `LocalLLaMA/typed-decisions`（1,200 訓練案例／6,000 決策）與描述「100% 人類標註公開資料、動態洗牌選項」。完整訓練配方未公開，屬推測範圍。
