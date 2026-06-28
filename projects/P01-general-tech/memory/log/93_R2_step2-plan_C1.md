# 93_R2_step2-plan_C1.md

## 狀況理解

R2 使用者要求「補充 RSC 與 Streaming SSR 的效能對比數據」。Streaming SSR 指 React 18 `renderToPipeableStream` + Suspense 串流機制。R1 報告 §3.4 已有功能面對照但無量化數據。本 sub-step 需從 React 18 架構討論、Vercel 官方分析、真實案例（Mux 5 萬行遷移、Dagster dbt docs 20x 改善）取得量化效能指標。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| webfetch reactwg/react-18/discussions/37 | 取得 Streaming SSR 架構說明 | 理解傳統 SSR 三大問題與 Streaming SSR 解法 | 完整取得：fetch all → show any、load all → hydrate any、hydrate all → interact any 三問題，以及 Streaming HTML + Selective Hydration 兩大解法 |
| webfetch vercel.com/blog/understanding-react-server-components | 取得 Vercel 官方 RSC 分析 | 理解 RSC 效能優勢的官方論述 | 取得 bundle size 減少、資料獲取瀑布消除、Server Actions 等說明 |
| webfetch mux.com/blog/what-are-react-server-components | 取得 Mux 5 萬行遷移經驗 | 真實案例的效能數據與遷移痛點 | 取得 CSS-in-JS 不相容、React Context 限制、增量遷移策略等實戰經驗 |
| webfetch dagster.io/blog/dbt-docs-on-react | 取得 Dagster dbt docs 20x 改善案例 | 具體量化效能對比數據 | **關鍵數據**：LCP 4.5s → 220ms（20x）、記憶體 350MB → 16MB（20x）、Lighthouse 分數大幅提升、profiler 顯示 blocking time 歸零 |
| webfetch joshwcomeau.com/react/server-components | 取得 Josh Comeau 的 RSC 圖解分析 | 理解 RSC vs SSR 的網路請求時序差異 | 取得 FCP/TTI/LCP 時序圖、client boundary 概念、Server Component 序列化機制 |
| webfetch nextjs.org/docs/app/getting-started/server-and-client-components | 取得 Next.js 官方 RSC 文件 | 確認 RSC Payload 格式與渲染流程 | 取得 RSC Payload 為 compact binary、HTML → RSC Payload → JS 的三階段客戶端載入流程 |
| webfetch nextjs.org/docs/app/building-your-application/rendering | 取得 Next.js 渲染模型（含 PPR） | 了解 2025-2026 的 PPR 發展 | 取得 Partial Prerendering 預設啟用、`use cache` directive、static shell + streaming 混合模型 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Streaming SSR 定義 | React 18 `renderToPipeableStream` + Suspense | 確認：串流 HTML + Selective Hydration + event replaying |
| 傳統 SSR 問題 | React 18 架構討論 #37 | 三大瀑布：fetch → render → load → hydrate |
| Bundle size 對比 | Vercel blog + Josh Comeau 圖解 | RSC 可消除 Server Component 全部 bundle；Streaming SSR 不減少 bundle |
| 真實效能數據 | Dagster dbt docs 案例 | LCP 4.5s→220ms（20x）、記憶體 350MB→16MB（20x） |
| 時序差異 | Josh Comeau 網路請求圖 | RSC 可在 DB query 完成後直接 render 並串流，無需 client round-trip |
| PPR 發展 | Next.js 16.2 docs | `use cache` + Suspense 為 PPR 核心，靜態 shell + 動態串流混合 |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 量化數據來源 | 僅官方 benchmark / 真實案例 + 推估 | 真實案例為主（Dagster、Mux）+ 推估補足 | 官方無直接 RSC vs Streaming SSR 的 A/B benchmark，真實案例提供最具說服力的數據 |
| 對比維度 | 僅 bundle size / 多維度 | 多維度：bundle size、FCP、TTI、LCP、記憶體、First Byte、hydration 時間 | 使用者要求「效能對比數據」，單一維度不足 |
| Streaming SSR 範圍 | 僅 React 18 API / 含 Next.js 實作 | React 18 API 為主，Next.js 實作為輔 | 使用者語意為 React 層級，但 Next.js 是唯一完整實作，需引用其渲染模型 |
| 是否包含 PPR | 是 / 否 | 是 | PPR 是 2025-2026 RSC 發展的關鍵方向，直接影響效能權衡 |
