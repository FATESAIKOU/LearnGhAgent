# 213_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認調研標的為 **MiniMax-H3**（MiniMax 開源的全模態音視頻生成模型，GitHub `MiniMax-AI/MiniMax-H3`）。本 sub-step C1 依 document skill 標準動作：取得 repo metadata、擷取 README 與關鍵子文件、補查背景脈絡。目標是為後續 C2（收斂分析）與最終報告（4 大 section）備齊第一手資料。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 do/skills/document/SKILL.md | 確認標準調研流程 | 依規範執行 | 規範確認：gh repo view → README → 背景脈絡補查 |
| `gh repo view MiniMax-AI/MiniMax-H3` | 取得 repo metadata | 掌握 stars、license、更新時間 | 2495 stars、146 forks、Python、created 2026-07-30、updated 2026-08-09、default branch main；GitHub 上 license 欄位為 null（license 在 HF 端） |
| `gh api repos/.../contents/` | 盤點 repo 結構 | 找出關鍵子文件 | 含 FL2VA/、Ref2VA/ 兩 checkpoint、audio_vae/、visual_vae/、text_encoder/、transformer/、processor/、tokenizer/、scheduler/、skills/、scripts/、model_index.json 等 |
| 抓取 README.md（raw） | 取得主要文件 | 掌握系統概述、架構、部署 | 完整取得：三模組架構、模型變體、輸出規格、部署方式、2K workflow、Prompting Guidance |
| 抓取 HF LICENSE | 確認授權條款 | 掌握使用限制 | 取得 MiniMax H3 Community License（2026-08-02），**Excluded Territories：EU、UK、韓國、美國**；年營收 >2000 萬美元需另行授權 |
| 抓取 HF model API | 補查 HF 端 metadata | 掌握下載量、pipeline、tags | 35295 downloads、3197 likes、pipeline=image-text-to-video、created 2026-07-28；tags 含 text/image/video/audio-to-audio-video 等全模態 |
| 抓取 model_index.json | 確認 diffusers 整合 | 掌握載入方式 | MiniMaxH3ModularPipeline，text_encoder 用 Qwen3VLForConditionalGeneration、Qwen2TokenizerFast、Qwen3VLProcessor |

**關鍵技術事實（供 C2 收斂）：**

- **三模組系統**：H3-Context-IR（hosted 預處理/編排，**未開源**，僅 API）→ H3-Base（開源，768p）→ H3-Regenerate-2K（**未開源**，僅 API，768p→2K 再生）。
- **H3-Base**：33B dense 單流 Transformer，約 13B 參數在 AdaLN 分支（可預計算快取，inference-only 不需載入）；MM-RoPE 三維位置編碼；原生支援 sparse attention 但**初始開源版僅 full attention**。
- **編碼器**：H3-Encoder 用 Qwen3-VL-32B 完整預訓練權重，取第 50 層 hidden states。
- **VAE**：H3-VisualVAE（f16t4d24，時空因果，patch 1×2×2 → 有效空間 32×、時間 4×）；H3-AudioVAE（32kHz→40Hz latent，左右聲道獨立處理再合併，立體聲）。
- **輸出規格**：4–15 秒、最高 2K、24 FPS、32kHz 立體聲、11 種語言穩定支援。
- **兩個 checkpoint**：H3-Base-FL2VA（t2va / fl2va，0/1/2 張圖）、H3-Base-Ref2VA（ref2va，≤9 圖、≤3 影片、≤3 音訊、混合 ≤12 檔）。
- **部署**：SGLang、vLLM、diffusers、ComfyUI；2K 需結合本地 H3-Base + 官方 Context-IR/Regenerate-2K API。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata | gh repo view + gh api | 取得完整 metadata；GitHub license 欄位 null，需以 HF LICENSE 為準 |
| 主要文件 | 抓取 README.md 全文 | 取得系統概述、架構、部署、workflow 完整內容 |
| 授權條款 | 抓取 HF LICENSE | 取得 Community License，含地域排除（EU/UK/韓/美）與商業門檻 |
| HF 端資訊 | HF model API | 取得下載量、likes、pipeline、tags、建立時間 |
| 開源範圍 | 對照 README 三模組說明 | Context-IR 與 Regenerate-2K 未開源，僅 H3-Base 開源 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| license 來源 | (A) GitHub LICENSE（404）(B) HF LICENSE | B | GitHub 端無 LICENSE 檔，HF 端有完整 Community License，且 README 明確指向 HF |
| 開源範圍判定 | (A) 視為全開源 (B) 區分三模組開源狀態 | B | README 明示 Context-IR 與 Regenerate-2K 未開源，僅 H3-Base 開源，報告須如實區分 |
| 背景脈絡補查 | (A) 本 step 即補查 (B) 留待 C2 | B | C1 已取得架構與授權核心事實；替代方案比較（§4）與背景歷史留待 C2 網路補查 |
| 下一步 C2 方向 | (A) 直接撰寫報告 (B) 補查背景脈絡與替代方案 | B | 需補查全模態生成背景、同級替代方案（如 Veo、Sora、Kling、Wan 等）以完成 §2/§4 |
