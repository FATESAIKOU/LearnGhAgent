# 106_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認使用者要求解釋三個名詞：dflash、speculative decoding、mtp。本 sub-step C1 依 SKILL.md 標準調研動作執行：取得 repo metadata、擷取主要文件、補查背景脈絡。三個名詞中，dflash 有明確 GitHub repo（z-lab/dflash），speculative decoding 與 mtp 為學術概念，需從論文與 Wikipedia 補查。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view z-lab/dflash --json ...` | 取得 dflash repo metadata | stars、license、更新時間等 | 成功：5.3k stars、MIT license、main branch、描述 "DFlash: Block Diffusion for Flash Speculative Decoding" |
| webfetch GitHub README (z-lab/dflash) | 擷取主要文件 | 了解安裝、使用方式、支援模型 | 成功：取得完整 README，含支援模型表、安裝指令、vLLM/SGLang/Transformers/MLX 四種後端 quick start |
| webfetch arXiv:2602.06036 (DFlash paper) | 取得論文摘要 | 了解核心機制與效能數據 | 成功：ICML 2026 accepted，6x lossless acceleration，2.5x faster than EAGLE-3 |
| webfetch z-lab.ai/projects/dflash/ (blog) | 取得技術說明 | 了解設計原理與動機 | 成功：取得完整技術說明，含 block diffusion 平行 draft、target feature conditioning、KV injection 機制 |
| webfetch Wikipedia speculative decoding | 取得背景定義 | 了解 speculative decoding 的通用原理 | 成功：取得完整條目，含 mechanism（draft + verify）、history（Leviathan 2022 / Chen 2023）、variants（SpecInfer、Medusa、EAGLE） |
| webfetch arXiv:2404.19737 (MTP paper) | 取得 MTP 論文摘要 | 了解 multi-token prediction 定義 | 成功：Meta/FAIR 2024 論文，訓練時用 n 個獨立 output head 預測未來 n 個 token，推論時可達 3x 加速 |
| GitHub search "mtp multi token prediction llm" | 確認 MTP 相關 repo | 了解實作生態 | 成功：找到 Awesome-Multi-Token-Prediction（160 stars）、Gemma-4 MTP vLLM server 等 repo |
| GitHub search "dflash speculative decoding" | 確認 dflash 生態 | 了解 forks 與社群實作 | 成功：44 repos，含 dflash-mlx（Apple Silicon port）、vllm-dflash、ddtree-mlx 等 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| dflash repo 可存取性 | `gh repo view` + webfetch | 正常存取，5.3k stars，活躍更新 |
| dflash 論文可取得 | webfetch arXiv | 成功，ICML 2026 |
| speculative decoding 定義 | webfetch Wikipedia | 成功，完整條目 |
| MTP 定義 | webfetch arXiv + GitHub search | 成功，Meta/FAIR 論文為核心來源 |
| 三個名詞間的關聯性 | 交叉比對 | dflash 是 speculative decoding 的一種實作；MTP 是訓練策略，也可用於推論加速 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| dflash 的 GitHub repo 定位 | 1. z-lab/dflash（5.3k stars）2. 其他 fork | z-lab/dflash | 官方 repo，stars 最多，README 最完整 |
| MTP 的主要參考來源 | 1. arXiv:2404.19737（Meta/FAIR）2. Google Gemma MTP doc 3. 其他 blog | arXiv:2404.19737 | 原始論文，Google doc 無法存取（transport error） |
| 是否需要 CDP 繞過 | 1. 使用 CDP 2. 改用其他來源 | 改用其他來源 | 僅 Google doc 無法存取，其他來源（arXiv、GitHub、Wikipedia）皆正常 |
| 三個名詞的調研順序 | 1. 依字母 2. 依概念依賴關係（speculative decoding → dflash → MTP） | 概念依賴關係 | speculative decoding 是上層概念，dflash 是其具體實作，MTP 是另一條路線，先建立基礎概念再深入 |
