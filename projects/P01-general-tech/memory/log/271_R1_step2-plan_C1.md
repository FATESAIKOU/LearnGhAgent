# 271_R1_step2-plan_C1

## 狀況理解

R1 首次調研 colibri（PR #271 / Issue #268）。本 sub-step C1 為標準調研動作的資料取得階段：抓 repo metadata、README 主文件、關鍵子文件（benchmarks、GPU backends），並補查技術背景脈絡。colibri 定位為「消費級與異構硬體上運行前沿 MoE 模型」，與 Step1 判斷一致，屬 MoE 低資源部署技術評估。已確認 repo 為純 C、零依賴、MoE 推理引擎。

## 執行的動作與結果

| 動作 | 目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh api repos/JustVugg/colibri` | 取得 repo metadata | 抓 stars/license/語言/活躍度 | 36.7k stars、3.9k forks、Apache-2.0、主語言 C、default `main`、2026-07 創建、持續活躍更新 |
| `gh api .../contents` 列根目錄 | 掌握 repo 結構 | 定位 README 與子文件 | README 多語系（en/zh-CN/zh-TW/it）、docs/、c/、web/、desktop/、docker/ 齊全 |
| `gh api .../readme`（base64 解碼） | 擷取主文件 | 取得 5 點報告所需核心機制 | 775 行完整 README，含核心演算法、支援模型、benchmark、架構 |
| `gh api .../contents/docs` | 盤點關鍵子文件 | 篩出值得深入的文件 | benchmarks.md、GPU_BACKENDS.md、tuning.md、cuda/vulkan/metal.md、各模型 md、experiments/ |
| 讀 `docs/benchmarks.md` | 取得量測數字 | 填 §2 背景與 §3 效果 | 原始 dev box：744B、int4、resident 9.9GB、cold decode ~11GB/token、0.05–0.1 tok/s cold、6×RTX5090 全駐留 6.84 tok/s |
| 讀 `GPU_BACKENDS.md` | 確認異構後端 | 填 §4 異構方案 | 單一 `.cu` 經 `backend_gpu_compat.h` 編給 CUDA/HIP；Metal/Vulkan 另有後端 |

**取得的 repo metadata：**

| 欄位 | 值 |
|---|---|
| 全名 | JustVugg/colibri |
| 描述 | Run frontier MoE models on hardware you already own — pure C, zero deps, experts streamed from disk |
| stars / forks | 36,729 / 3,924 |
| license | Apache-2.0 |
| 主語言 | C（另有 Python、CUDA、C++） |
| default branch / 更新 | main / 2026-09 持續活躍 |
| 版本 | v1.12.0 |

**核心機制（README 重點）：**

- **MoE 稀疏性**：744B 每 token 僅啟動 ~40B，其中 routed experts 每次只變 ~11GB → 不需「fit」在快速記憶體，只需「placement」
- **三層階層（multitiering）**：VRAM / RAM / NVMe 視為同一推理層級
  - dense 部分（attention/shared experts/embedding ~17B）常駐 RAM int4 ~9.9GB
  - 19,456 個 routed experts（75 MoE layers × 256，int4 各 ~19MB）放 disk ~370GB 隨需串流
- **JIT for weights**：routing heat 驅動 per-layer LRU、learned pinned hot-store、一層前視 prefetch（routing 71.6% 可預測）
- **I/O 引擎化**：batch-union、overlap read+compute、O_DIRECT、dual-SSD strip（兩份 model、兩倍讀寬）
- **異構執行**：CPU、CUDA、Metal、Vulkan、NUMA memory、partial/full expert residency 共用一 runtime
- **語意保證**：placement 只影響速度不影響 router/精度；無 SLA on speed、有 hard guarantee on semantics
- **支援模型**：GLM-5.2/5.3（744B）、Inkling（975B）、Kimi K3（2.8T）、DeepSeek V4/V4.1 Flash、Qwen3.8/3.6、OLMoE 共九族，一族一 `.c`

**背景脈絡（與 Step1 查到的近鄰對照）：** README 明列受啟發之研究：REAP/EASY-EP、SERE/ReMoE、MC-SMoE、MoBE/D²-MoE、HybriMoE/ScMoE/OD-MoE；工程上重實作 safetensors、tiktoken、llama.cpp（GBNF/Metal）、vLLM（輸出語意）、transformers（oracle）、DietGPU、rocWMMA。與使用者既有評估 AirLLM（per-expert streaming, Reject 太慢）、llama.cpp/vllm（消費級/生產引擎）直接同問題域。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata | `gh api` JSON | 完整取得：36.7k stars、Apache-2.0、C 為主、活躍 |
| 主文件 | README base64 解碼 | 775 行，核心機制/支援模型/benchmark 齊全 |
| 子文件 | docs/ 盤點 + benchmarks/GPU_BACKENDS 精讀 | 量測數字、異構後端取得 |
| 標的吻合 | README 與 Issue 標題對照 | colibri = 消費級/異構硬體跑 MoE，一致 |

## 其中的決斷點

| 決斷面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 深入文件取捨 | ①全讀 docs/ ②只讀 benchmark+backend ③僅 README | ② | README 已含主要機制，benchmark 補量測、GPU_BACKENDS 補異構細節，避免過度耗 token |
| 後續 C2 方向 | ①深挖單一機制 ②補背景搜尋（MoE offload 對照）③抓 tuning/quickstart | ②為主、③為輔 | §4 需替代方案對照，需補 AirLLM/llama.cpp/kTransformers 的異同；tuning 補實際操作面 |
| 是否已需 CDP | 一般 fetch 是否受阻 | 未受阻 | 全程 `gh api`/base64 順利，無 CAPTCHA，不需繞行 |
