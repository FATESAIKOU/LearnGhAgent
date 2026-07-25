# 133_R2_step2-plan_C1.md

## 狀況理解

R2 使用者提出兩個問題：(1) cache_control 的定義、背景、解決機制、提出者；(2) 導入 pxpipe 前後的 prompt 形狀對比。本 sub-step C1 負責取得 repo metadata、README.md、關鍵子文件，以及補查 Anthropic 官方文件中的 cache_control 說明。

## 執行的動作與結果

| 動作 | 目的 | 預期達成效果 | 實際的結果 |
|------|------|----------|----------|
| `gh repo view teamchong/pxpipe --json` | 取得 repo metadata | 取得名稱、描述、星數、語言、建立日期 | 成功：TypeScript, 6689 stars, 571 forks, 2026-05-20 建立 |
| Web fetch README.md | 取得專案說明文件 | 理解專案概觀、使用方式、benchmark | 成功：取得完整 README（含 FAQ、模型支援矩陣、限制說明） |
| Web fetch docs/CACHING_AND_SAVINGS.md | 取得快取對齊與成本計算說明 | 理解 cache_control 搬移機制、baseline 計算公式 | 成功：取得完整文件（含 warm/cold 範例、OpenAI Responses 路徑說明） |
| Web fetch src/core/transform.ts | 取得轉換邏輯原始碼 | 理解 cache_control 搬移實作細節 | 成功：取得完整原始碼（含 relocateAnchorToHistoryImage、demoteRelocatedCacheControl 等函式） |
| Web fetch src/core/baseline.ts | 取得成本計算原始碼 | 理解 baseline 計算公式的實作 | 成功：取得完整原始碼（含 deriveBaselineWarmth、computeBaselineInputEff） |
| Web fetch Anthropic 官方 Prompt Caching 文件 | 取得 cache_control 的官方定義 | 理解 cache_control 的提出者、語法、定價、限制 | 成功：取得完整文件（含自動快取、顯式斷點、lookback 機制、定價表） |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 驗證結果 |
|----------|---------------|----------|
| cache_control 提出者 | Anthropic 官方文件 | Anthropic 提出，2025 年推出 |
| cache_control 語法 | 官方文件範例 | `{"type": "ephemeral"}`，可附加於 tools/system/messages 的 content block |
| 定價倍率 | 官方文件定價表 | base 1.0×, cache write 1.25× (5m) / 2.0× (1h), cache read 0.1× |
| pxpipe 的 cache 對齊策略 | CACHING_AND_SAVINGS.md + transform.ts | 不新增標記，只搬移既有標記到最後一張圖片區塊 |
| prompt 形狀所需資訊 | transform.ts 中的請求重寫邏輯 | 已取得完整轉換邏輯，可據以建構前後對比範例 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|----------|---------|----------|----------|
| cache_control 資料來源 | 僅 pxpipe 文件 vs Anthropic 官方 + pxpipe | Anthropic 官方 + pxpipe | cache_control 是 Anthropic API 原生功能，需官方文件確認提出者與語法 |
| prompt 形狀場景數 | 1-2 個 vs 3-4 個 | 3 個場景（一般對話、工具呼叫、大工具輸出） | 涵蓋 pxpipe 分層策略的三種典型情境，足夠展示前後差異 |
| 是否讀取更多原始碼 | 僅 transform.ts vs 也讀 render.ts/history.ts | 僅 transform.ts + baseline.ts | 這兩個檔案已涵蓋 cache_control 搬移與成本計算的核心邏輯 |
