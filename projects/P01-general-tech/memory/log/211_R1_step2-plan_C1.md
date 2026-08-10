# 211_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認標的為 **AirLLM**（lyogavin/airllm，低顯存 LLM 推理工具），且使用者已有 llama.cpp/vllm 評估（Reject/Reserve）。C1 任務為取得 repo metadata、README 與關鍵子文件，並補查背景脈絡，為 C2 的機制細節與替代方案比較鋪路。重點是釐清「如何用極低 VRAM 跑超大模型」的核心機制。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view lyogavin/airllm` | 取得 repo metadata | 確認 stars、license、更新時間 | 30,308 stars、Apache-2.0、created 2023-06-12、updated 2026-08-09、primaryLanguage Jupyter Notebook、fork 3,224 |
| 抓取 raw README.md | 取得官方說明全文 | 了解定位、支援模型、用法 | 385 行；宣稱 70B 跑在單張 4GB、405B 跑 8GB、DeepSeek-V3(671B) 跑 ~12GB、Kimi K3(2.8T) 跑 <4GB |
| 列舉 repo 根目錄與 `air_llm/` 結構 | 定位關鍵子文件 | 找出核心實作檔 | 核心在 `air_llm/airllm/`：airllm_base.py、各架構子類、persist/（safetensor/mlx persister）、utils.py |
| 抓取 `airllm_base.py` | 理解核心機制 | 確認「逐層流式載入」實作 | 756 行；確認 meta device 實例化 + forward hook 逐模組 stream 權重 |
| 抓取 `utils.py` | 確認載入/釋放細節 | 確認 load_layer / clean_memory | 確認 load_layer、load_layer_subset、layer_tensor_names、clean_memory 存在 |
| 抓取 `persist/` 清單 | 確認分片儲存方式 | 確認 safetensors 分片 | 有 safetensor_model_persister.py、mlx_model_persister.py、model_persister.py |

**核心機制（從 airllm_base.py 確認）：**
- checkpoint 在磁碟上切成 per-layer shard
- 真實 transformers 模型在 `meta` device 實例化（不佔記憶體），forward/generation 邏輯由 transformers 驅動
- 對每個大模組（embed、每個 decoder layer、final norm、lm_head）掛 forward hook：執行前把該模組權重 disk→GPU，執行後釋放
- `prefetching`：worker thread 預載下一個模組，與當前計算重疊
- MoE 模型（Kimi K3、DeepSeek-V3）走 **per-expert streaming**：只載入 token 實際路由到的 expert（K3 一層 experts 展開 ~55GB，token 只碰 ~1GB）
- 選配 block-wise quantization（4bit/8bit）壓縮磁碟分片以加速載入；v3.0 支援 FP8

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo 定位 | gh repo view | 30k stars、Apache-2.0、活躍維護（2026-08 更新） |
| 核心機制 | 讀 airllm_base.py | 確認「meta device + forward hook 逐層 stream + prefetch + per-expert streaming」 |
| 支援模型 | README | Llama 2/3/3.1/3.3/4、Qwen 1/2/2.5/3、DeepSeek V2/V3/R1、Mistral/Mixtral、Phi、Gemma、ChatGLM、Baichuan、InternLM、Yi |
| 與既有評估關聯 | 對照 llama.cpp/vllm | 同屬「低 VRAM 跑 LLM」領域，但切入點不同（AirLLM 靠逐層 offload，非量化/蒸餾/剪枝） |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否深入讀原始碼 | (A) 只讀 README (B) 讀 airllm_base.py 核心實作 | B | README 只講「一次只放一層」，需原始碼確認 hook/stream/prefetch/expert 機制才能回答「如何解決」 |
| 是否讀論文 | (A) 讀 arxiv 2212.09720（block-wise quantization）(B) 留給 C2 | B | C1 只做文件定位；量化論文細節屬機制深挖，留 C2 |
| 是否抓所有子類檔 | (A) 全抓 (B) 只抓 base + utils + persist 清單 | B | 各架構子類僅是 transformers 對接差異，核心機制在 base，避免過度抓取 |
