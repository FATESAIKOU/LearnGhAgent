# 282_R2_step2-plan_C1.md

## 狀況理解

- 本 sub-step C1 為 R2 追問輪第一段。R2 非新調研，須針對 5 問的**界定向**取新硬證據：Q1 模型 vs 軟體、Q2 成本結構、Q3 與 Jev 關係、Q4「效能不好」語意、Q5 該借模型層或系統層。
- 依 `do/skills/document/SKILL.md`：①取 repo metadata ②擷取 README／關鍵子文件 ③補背景。因 R1 已取 README，本次重點是「能回答 Q1–Q5 的具體條目」與**獨立第三方證據**（R1 未取）。
- 第二大腦 R2 step1 已確認：`laya` 全 bundle 零命中；Q5 判準命中骨幹 `技術取捨準則`；Model Router preset 與 `DeepSeek V4` stable 判定衝突。故 C1 只補硬事實，不再重查個人立場。
- 輸出落點：供 Step3 撰寫 `output/282_laya.md` 的 `## 5. User Q&A`（Q1–Q5 各一題）。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view`／`gh api repos/…/laya` | 更新 metadata | 確認規模與活躍 | 25,335 stars／2,196 forks／173 open issues；Apache-2.0；created 09-18、pushed 09-25；topics 含 `jev` |
| `curl` raw README（65KB）＋pyproject.toml | 取產品邊界（Q1） | 分清套件與權重 | 套件 `laya` 0.3.20、4 個 console script；權重另存 HF（見下）；`dependencies` 僅 torch/transformers 等，**無任何雲端 SDK** |
| `gh api …/git/trees/main?recursive=1` | 掃描訓練碼存在性（Q1/Q5） | 判斷架構/訓練手法可否被學 | repo **無獨立 base 訓練 pipeline**；訓練數學在 runtime 套件 `laya/common.py`（`DecisionModel`／`proper_reward`／`build_model`）＋`tests/test_training.py`；完整訓練只有**微調** notebook |
| `curl` HF root README＋`api/models` | 取權重清單與授權（Q1/Q2） | 確認 weights 型態 | 同 repo 三權重資料夾（root／multilingual／typed-decisions）＋HF 另兩 repo；`license: apache-2.0`、`commercial-use` tag |
| `curl` 微調 notebook | 取訓練配方（Q1/Q5） | 驗證「可自己訓練」到什麼程度 | 微調迴路完整公開：`LocalLLaMA/typed-decisions`（1,200 案例）＋DDP RLCD／GRPO／`proper_reward`；~4–5h、4 epochs、~30k questions、Kaggle 免費 2×T4 |
| `curl` `laya/common.py` | 取架構與訓練法（Q5） | 取得「方法」本體 | `DecisionModel`＝encoder＋2 層 transformer head＋option-marker scorer＋act head；`proper_reward`＝log＋spherical（＋RPS）嚴格 proper |
| `gh search issues`／view #450、#555 | 取**獨立第三方**評測（Q4） | 補 R1 缺的反證 | #450：聯邦採購 laya 0.780 vs Jev 0.919；#555：9 套件 laya 0.686 vs Jev 0.907（8/9 顯著）；均非官方 |
| `curl` Dev.to 作者文 | 取作者動機（Q3） | 驗證是否「因 Jev 未開源才做」 | 作者自陳 2025-03（arXiv 2503.23303）已做非自迴歸決策、PPO／RL；Jev（09-15）出現時感到被忽視→Laya 是「把原方向開源化」 |

**Q1–Q5 對應硬事實：**

| 問 | 證據 |
|---|---|
| Q1 模型 or 軟體 | **兩者分離**：權重＝HF 上的 encoder＋自訓 decision head（safetensors）；軟體＝pip 套件 `laya`（Router／CLI／`laya-serve`／MCP／LangChain／ONNX）。repo 不含權重本體，權重載入前 Router 只做 `<0.5ms` 純 Python 路由 |
| Q2 雲端付費 | **無**。Apache-2.0、README 自列 `$0 self-hosted`；唯一收費字樣是 Buy Me a Coffee 贊助按鈕；無 hosted endpoint、無 metering、無訂閱、無 API key 販售（`LAYA_API_KEY` 只是自架 bearer auth）。成本＝自備硬體或雲資源 |
| Q3 與 Jev 關係 | **非 wrapper、非 Jev fork**。Laya 不呼叫 Jev；權重來自 ModernBERT／mmBERT＋自訓 head。僅**相容** Jev `POST /v1/systemone` wire protocol（換 `baseUrl` 即可），並沿用 choice／score／noul 回答形式。作者主張概念早於 Jev |
| Q4「效能不好」 | 指**判斷品質**，非速度。base zero-shot 0.362／0.352（majority 0.461）近隨機；微調後 0.766。獨立評測 #555：laya 0.686 vs Jev 0.907（8/9 顯著落後）；#450：0.780 vs 0.919 |
| Q5 借哪層 | 模型層（encoder＋head＋RLCD）無第三方案例、且未勝 Jev；系統層（語言 Router、Jev 相容協定、`docs/staged-adoption.md` 的 shadow→compare→policy→bounded promote、hooks 觀測）為可抽取方法 |

**第二大腦對照（C1 只引用 step1 已查結果，未新增）：** `技術取捨準則`（骨幹、draft）＝Reject≠沒價值、可抽取「需求理解＋方案方向」；`DeepSeek V4`（human stable）＝降低 Model Routing 研究優先級。兩者為 Step3 Q5 的判準來源。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Q1 可答 | 套件 vs 權重實體位置 | 可答：軟體框架＋可下載權重，兩者分離 |
| Q2 可答 | 全文 grep 收費／hosted 字樣 | 可答：無雲端付費；僅贊助按鈕 |
| Q3 可答 | 權重來源＋作者自陳＋協定關係 | 可答：獨立同型實作，非包裝 Jev |
| Q4 可答 | 官方 Honest Limits＋兩則獨立 eval | 可答：判斷品質（zero-shot 近隨機、獨立評測落後） |
| Q5 可答 | 架構碼＋訓練碼存在性＋骨幹判準 | 可答：架構/手法無廣泛驗證；系統層可抽取 |
| R2 不重做 R1 | 本次僅補 Q1–Q5 缺口與獨立 eval | 未重複 R1 已載事實 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 判斷「Q4 效能」證據來源 | ①僅 README 自陳 ②加獨立第三方 eval | ② | R1 只用官方數字；Q4 帶質疑，需非官方反證（#450／#555） |
| Q1 訓練碼是否算「軟體含訓練」 | ①只列 runtime ②區分 runtime／微調 loop／base 完整配方 | ② | 「模型架構與訓練手法可否學」需精確：base 完整訓練 pipeline 未公開 |
| Q3 論證取向 | ①依「影片說沒開源所以複製」 ②依作者原話與權重來源 | ② | 影片為二手觀點；作者 Dev.to 與 HF 為一手 |
| 是否重跑 mybrain-read | ①重跑 ②引用 step1 結果 | ② | step1 已同步 @4ce59b3；本 sub-step 不新增個人立場需求 |
