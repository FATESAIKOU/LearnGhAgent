# 213_R2_step2-plan_C1.md

## 狀況理解

R2 為使用者對 R1 報告的三問追問（PR chat），屬 User Q&A 觸發。Step 1 已拆解三問意圖並指出資訊缺口：**Q1 H3 寫程式能力**、**Q2 自架門檻／成本**、**Q3 輸出模態範圍**。

本 sub-step C1 針對這輪意圖做定向調研——**不是重做 R1 的全模態架構調研**，而是補查 R1 缺口：
- Q1：H3 是否具程式碼生成能力（需澄清 H3 為生成模型非 coding LLM）。
- Q2：硬體需求（SGLang 官方部署規格）＋ API 定價（H3 每秒計價）。
- Q3：輸出模態是否僅限影片＋音訊（對照 repo、model card、API 三處規格）。

R1 已備齊的架構事實（33B、三模組、768p/2K、影音輸出）沿用，本 step 僅補查 R2 三問所需新資料。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view MiniMax-AI/MiniMax-H3` | 更新 repo metadata | 確認 R2 時的 stars/更新 | 3466 stars（R1 2495）、updated 2026-08-10、licenseInfo null、description 空 |
| 抓取 README raw 全文 | 對照輸出模態、部署、skills | 確認 Q3 輸出範圍、Q1 是否具 coding | README 明示「generate video with native stereo audio」＝**輸出僅影片+音訊**；全模態指輸入；有 `skills/h3-prompt-writing`（prompt 撰寫 skill，非 coding），其餘 8 個是 MiniMax Hub 影片風格 skill，皆非程式生成 |
| 抓取 SGLang MiniMax-H3 cookbook | 取得官方硬體部署規格 | 掌握 Q2 自架硬體門檻 | 見下方硬體表：最低 2×RTX 5090（32GB，需 384GiB host 主機），完整品質需 B200×8 / H200×4 / H100×4 等 |
| 抓取 MiniMax PAYGO 定價頁 | 取得 H3 官方每秒計價 | 掌握 Q2 API 成本 | H3 2K **$0.13/秒**、768P **$0.08/秒**輸出；圖片前 5 張免費、之後 $0.04/張；影片輸入按時長；Regeneration 768P→2K $0.05/秒；Context-IR $0.90/M in、$3.60/M out |
| 抓取 MiniMax Video 套裝定價頁 | 確認是否有訂閱套餐優惠 | 判斷 Q2 便宜與否 | **Video Packages 明確標註「MiniMax H3 is not supported yet」**——H3 目前僅 PAYGO，無套餐折扣 |
| 抓取 H3 video-generation API guide | 確認輸出規格與流程 | 佐證 Q3 輸出模態 | API 回應僅回傳影片 URL（`content.url`，mp4），輸出就是影片+內嵌音訊；無文字/純影像輸出 |

**關鍵 R2 事實（供 §5 Q&A 使用）：**

- **Q1（寫程式）**：H3 是**全模態輸入→影片+音訊輸出**的生成模型，非 LLM；repo/model card 均無任何 code generation 能力宣稱。deepseek-v4-0731-flash 屬 coding/agent LLM（1M context、XML tool calling，MyBrain `DeepSeek V4.md`），兩者**不同賽道，無 CP 值可比性**。H3 的「9 skills」皆為影片 prompt 撰寫/風格 skill，非寫程式工具。
- **Q2（自架/成本）**：
  - **硬體**（SGLang 官方驗證配置）：

    | 配置 | 需求 | 備註 |
    |---|---|---|
    | 最低（offload） | 2×RTX 5090（各 32GB）+ 384GiB 主機 | 需 layerwise offload，lossless BF16 |
    | 資料中心級 | 4×H100 80GB ／ 4×H200 ／ 8×B200 ／ 8×B300 | resident 完整品質 |
    | AMD | 8×MI300X ／ 8×MI355X | AITER packed attention |
  - **API 成本**：2K $0.13/秒、768P $0.08/秒；一支 5 秒 768P = **$0.4**、5 秒 2K = **$0.65**；Context-IR 需額外算 token 費。**Video Packages（訂閱折扣）尚未支援 H3**，只能 PAYGO。
- **Q3（輸出範圍）**：**是，H3 輸出僅限「影片＋音訊」**。輸入全模態（文字/圖/影片/音訊任組），但輸出固定為帶同步立體聲（32kHz）的影片（mp4）。無法產出純文字、純圖片、純音樂——無 t2i 或 t2t 輸出路徑。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Q1 事實基礎 | 對照 README/model card 有無 code 能力宣稱 | H3 無 coding 能力；deepseek-v4 屬 coding/agent LLM，不同賽道；Q1 需先指正比較基準 |
| Q2 硬體門檻 | SGLang cookbook 官方配置 | 最低 2×RTX 5090+384GiB 主機；完整品質需 4~8 張資料中心 GPU，自架門檻高 |
| Q2 成本 | PAYGO 定價頁 | 768P $0.08/秒、2K $0.13/秒；Video Packages 未支援 H3 |
| Q3 輸出模態 | repo + model card + API guide 三處交叉 | 輸出僅影片+音訊（mp4）；輸入全模態但輸出固定影音 |
| R1 資料沿用 | 對照 213_R1_step2-plan_C1 | 架構/規格沿用；本 step 未重做，僅補 R2 缺口 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| Q1 回答策略 | (a) 照問直接比對 CP 值 (b) 先澄清賽道差異再給結論 | (b) | H3 非 coding 模型，與 deepseek 無法同基準比 CP 值，須先指正比較基準再答 |
| 自架 vs API 資料 | (a) 只給硬體 (b) 只給價格 (c) 兩者並列 | (c) | Q2 同時問「夠小可自架？」與「便宜？」，需硬體＋價格雙軌回答 |
| Q2 硬體來源 | (a) 用 HF model size 推估 (b) 用 SGLang 官方配置 | (b) | HF 僅標 33B params；SGLang cookbook 有官方驗證的明確 GPU 配置，可據實引用 |
| Q3 佐證強度 | (a) 單靠 README (b) repo+model card+API 三處交叉 | (b) | 輸出模態是 Q3 核心，三處規格一致（僅影音輸出）才可下確定結論 |
| 下一步 C2 | (a) 直接寫報告 (b) 補查對比（deepseek 規格、同類替代） | (b) | 需 deepseek-v4 具體規格做 Q1 對照表，及同級生成模型（Veo/Sora/Kling/Wan）成本/自架對照以完成 §5 |
