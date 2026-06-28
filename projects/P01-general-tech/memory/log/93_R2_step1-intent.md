# 93_R2_step1-intent.md

## 狀況理解

使用者要求「補充 RSC 與 Streaming SSR 的效能對比數據」。這是 R2（追問輪），使用者對 R1 報告中 §3.4 的 RSC vs 傳統 SSR 對照表不滿足，要求進一步補上 Streaming SSR（React 18 `renderToPipeableStream`）與 RSC 之間的具體效能數據（如 bundle size、TTI、FCP、LCP、hydration 時間等量化指標）。使用者未指定特定 benchmark 來源，需自行從網路搜尋或推估合理數據。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 R1 報告 | 確認現有內容中 RSC vs SSR 的涵蓋範圍 | 判斷 R2 需補充的缺口 | §3.4 已有功能面對照，但無量化效能數據，且未區分 Streaming SSR 與傳統 SSR |
| 讀取 R1 step logs | 確認前輪決策脈絡 | 確保 R2 不重複已做過的工作 | R1 已涵蓋功能對照，R2 需聚焦量化數據 |
| 解析使用者語意 | 判斷「Streaming SSR」的具體指涉 | 明確搜尋方向 | Streaming SSR = React 18 `renderToPipeableStream` + Suspense streaming，非傳統 `renderToString` |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 需求類型 | 追問 / 質疑 / 新需求 | 追問（要求補充量化數據） |
| 技術範圍 | RSC vs Streaming SSR | 需區分 Streaming SSR（React 18）與傳統 SSR（React 17 以前） |
| 數據類型 | 效能對比數據 | 需量化指標：bundle size、FCP、TTI、LCP、hydration 時間、First Byte 延遲 |
| 現有報告缺口 | R1 §3.4 有功能對照但無數字 | 需補上 benchmark 數據或合理推估值 |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 數據來源 | 僅引用官方 benchmark / 自行推估 / 兩者並列 | 兩者並列 | 官方 benchmark 有限，需以推估補足，但須明確標示來源 |
| Streaming SSR 定義 | React 18 `renderToPipeableStream` / 廣義含 Next.js 串流 | React 18 `renderToPipeableStream` | 使用者語意為 React 層級的 Streaming SSR，非框架特定實作 |
| 對比維度 | 僅 bundle size / 多維度（bundle + 時間 + 使用者體驗） | 多維度 | 使用者要求「效能對比數據」，單一維度不足 |
