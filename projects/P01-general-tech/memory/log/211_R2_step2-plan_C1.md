# 211_R2_step2-plan_C1.md

## 狀況理解

R2 使用者的兩個問題（Q1 可行性、Q2 秒速/context 試算）都以「在 RTX 2070S + 64GB RAM 上跑 deepseek-v4-flash:0731」為前提。C1 任務不是重做 R1 的 AirLLM 機制調研，而是針對 R2 意圖補查三件事：**(1) 目標模型 deepseek-v4-flash:0731 的真實規格**、(2) **AirLLM 對該模型的支援度**、(3) **RTX 2070S(8GB, sm_75) 的相容性瓶頸**。R1 已確認 AirLLM 核心機制（meta device + forward hook 逐層 stream + per-expert streaming），故 C1 聚焦把「模型 × 框架 × 硬體」三者對齊。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view lyogavin/airllm` | 取得 R2 當下 repo metadata | 確認更新狀態 | 30,490 stars、Apache-2.0、2026-08-10 更新（活躍） |
| 抓 raw README.md | 確認支援模型清單 | 判斷 V4 是否在列 | README 明列 DeepSeek V2/V3/R1，**無 V4**；支援表「Tiny GPU huge models」最高到 V3(671B)~12GB |
| `gh api` 抓 `air_llm/airllm/` 檔清單 | 確認是否有 V4 專用子類 | 判斷架構是否被支援 | 有 airllm_kimi_k3.py 但**無 deepseek_v4.py**；base + auto_model 走 generic 路徑 |
| 抓 auto_model.py | 確認架構對應 | 判斷 DeepseekV4 是否走 generic | `ARCH_OVERRIDES` 無 `DeepseekV4ForCausalLM` → 走 generic `AirLLMBaseModel` |
| 抓 airllm_base.py | 確認 generic 對混合注意力/FP4 expert 的處理 | 判斷能否正確 stream | generic 依賴 `model.model.layers` 標準結構 + transformers 驅動 forward；**無 hybrid attention (CSA/HCA) 與 FP4 expert 特殊處理** |
| webfetch ollama.com `deepseek-v4-flash` | 確認 0731 tag 規格 | 取得模型身份 | 304B 參數、MoE、1M context；tag `0731-cloud` 存在但僅雲端 cloud 用量 |
| webfetch huggingface `deepseek-ai/DeepSeek-V4-Flash` + API | 確認權重規格 | 取得權重大小/架構/精度 | 291B params、safetensors 總量 ~291B；`DeepseekV4ForCausalLM`、**hybrid attention (CSA/HCA)**、**expert FP4 + 其他 FP8 mixed**、43 層、256 expert、MoE top-6、max_pos 1M |
| `gh api` issue #299（能否 8G VRAM 跑 V4） | 取得官方/社群直接證據 | 佐證 Q1 | 社群回「可以，但 TPS 極慢，coding 不建議」 |
| `gh api` issue #317（舊 GPU） | 取得 bf16/GPU 相容證據 | 確認 2070S 相容性 | 官方回：bf16 需 Ampere(sm_80+)；Turing(sm_75) 需強制 fp16；無多 GPU 平行 |

**關鍵資料整理：**

| 面向 | 事實 |
|---|---|
| 模型身份 | deepseek-v4-flash:0731 = DeepSeek-V4-Flash（284B/304B total、13B activated、MoE、1M ctx） |
| 權重大小 | 291B params、FP4+FP8 mixed、safetensors 46 shards |
| 架構 | `DeepseekV4ForCausalLM`、hybrid attention（CSA+HCA）、43 層、256 experts、top-6 |
| AirLLM 支援 | README 只列 V2/V3/R1；無 V4 專用子類；generic 路徑無 hybrid-attention / FP4-expert 特化處理 |
| 硬體相容 | RTX 2070S = 8GB、Turing sm_75；AirLLM v3 預設 bf16，**2070S 無 bf16 原生支援**，須強制 fp16（issue #317） |
| 社群直接證據 | issue #299：「能跑但 TPS 極慢，coding 不建議」 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 模型規格 | ollama + HF 頁面/API | 304B/291B、MoE top-6、1M ctx、FP4+FP8、hybrid attention |
| AirLLM 對 V4 支援度 | README + auto_model + airllm_base | **官方未宣告支援 V4**；generic 路徑架構上可載入但對 hybrid attention/FP4 無特化，正確性有風險 |
| 硬體相容性 | issue #317 | 2070S(sm_75) 需 fp16；bf16 不原生支援 |
| Q1 可行性初步結論 | 綜合以上 | **能載入，但非「官方支援」，且效能/正確性皆受挑戰**；社群實測「可跑但極慢」 |
| Q2 試算所需數字 | 模型/硬體規格 | 已具備權重、層數、expert 數、VRAM、context 上限；**秒速需 C2 從 shard 大小與 I/O 頻寬推估** |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研聚焦 | (A) 重做 AirLLM 機制 (B) 對齊「模型×框架×硬體」 | B | R2 是可行性+量化追問，非再評機制；R1 已覆蓋機制 |
| V4 支援度判定 | (A) 視為支援 (B) 標註「未宣告支援、generic 路徑、有風險」 | B | README 未列 V4、無專用子類、generic 對 hybrid-attention/FP4 無特化；不能誇大支援 |
| Q1 答法 | (A) 直接給「可/不可」 (B) 給「可載入但附條件」 | B | 需拆解「能載入」與「能用得好」；issue #299 佐證 TPS 極慢 |
| 秒速試算基礎 | (A) 引社群數字 (B) 自 shard 大小×I/O 頻寬推估 | B | 社群僅定性「極慢」，需 C2 用 NVMe/PCIe 頻寬量化推估，並標明誤差 |
