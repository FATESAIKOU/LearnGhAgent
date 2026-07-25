# 133_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1：取得 pxpipe 的 repo metadata 與主要文件。使用者已提供影片逐字稿，但需以專案原始文件為準進行驗證與補充。需取得：repo 基本資料、README、關鍵子文件（NOT-OCR.md、CACHING_AND_SAVINGS.md、FINDINGS.md）、package.json、核心原始碼（render.ts、transform.ts）。

## 執行的動作與結果

| 動作 | 目的 | 預期效果 | 實際結果 |
|------|------|----------|----------|
| `gh repo view` 取得 metadata | 取得 repo 基本資料 | 名稱、描述、星數、fork、license、語言 | 成功：6.7k stars, 570 forks, MIT, TypeScript, 2026-05-20 建立 |
| 擷取 README.md | 取得專案官方說明 | 核心機制、使用方式、benchmark | 成功：完整取得，含 FAQ、benchmark 表格、模型支援矩陣 |
| 擷取 docs/NOT-OCR.md | 理解 VLM 視覺機制 | VLM 非 OCR 的技術說明 | 成功：取得 patch embedding 機制、glyph 解析度掃描數據 |
| 擷取 docs/CACHING_AND_SAVINGS.md | 理解快取對齊與成本計算 | 快取對齊策略與節省計算公式 | 成功：取得 cache-aligned rewrite、savings accounting、worked examples |
| 擷取 FINDINGS.md | 取得完整研究歷程 | 專案從「死亡 verdict」到「逆轉」的完整記錄 | 成功：取得 verdict reversed 歷程、Fable 5 測試數據、glyph 實驗 |
| 擷取 package.json | 確認專案技術棧 | 版本、依賴、scripts | 成功：v0.10.0, pnpm, vitest, TypeScript, esbuild |
| 擷取 src/core/render.ts | 理解渲染核心實作 | 5×8 點陣字體、1568×728 頁面、reflow 機制 | 成功：取得完整 render pipeline 原始碼 |
| 擷取 src/core/transform.ts | 理解請求轉換邏輯 | 分層策略、break-even gate、cache 對齊 | 部分成功：檔案過長被截斷，但已取得關鍵 gate 邏輯與 TransformInfo 定義 |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 驗證結果 |
|----------|---------------|----------|
| 影片 vs 官方文件一致性 | 比對影片聲稱與 README/FINDINGS 數據 | 影片數據與官方文件一致（59-70% 節省、13/15 hex、0/15 Opus） |
| 核心機制 | render.ts 確認 5×8 Spleen 字體、1568×728 頁面、28080 chars/page | 與影片描述完全一致 |
| 分層策略 | transform.ts 確認 static slab → image、recent turns → text、history collapse | 與影片描述一致，另有 keepSharp 逃生口 |
| 模型支援 | README benchmark 矩陣確認 Fable 5 為 default、Opus opt-in | 與影片一致，補充 Gemini 3.6 Flash 也為 default |
| 成本計算 | CACHING_AND_SAVINGS.md 確認 end-to-end 59-70% 節省 | 與影片一致，補充詳細計算公式 |
| 技術限制 | NOT-OCR.md 確認 VLM 非 OCR、silent confabulation | 與影片一致，補充 glyph 解析度掃描數據 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|----------|---------|----------|----------|
| 文件擷取範圍 | 只讀 README vs 讀取所有關鍵子文件 | 讀取所有關鍵子文件 | 影片已涵蓋 README 內容，子文件（NOT-OCR、CACHING、FINDINGS）提供影片未涵蓋的深度技術細節 |
| 原始碼擷取 | 跳過原始碼 vs 讀取 render.ts + transform.ts | 讀取核心原始碼 | 原始碼是唯一能驗證影片聲稱是否準確的來源 |
| 是否需要更多 sub-step | C1 已足夠 vs 需 C2 補其他文件 | C1 已涵蓋主要文件 | 已取得 repo 層級所需資訊，C2 應聚焦於特定技術面向的深入調研 |
