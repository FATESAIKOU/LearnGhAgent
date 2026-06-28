# React Server Components (RSC) 技術分析報告

> 調研日期：2025-06-28 | 基於 React 19 穩定版、RFC 0188、React.dev 官方文件、Next.js App Router、Remix/React Router v7

---

## 1. 這個技術解決什麼問題？

React Server Components 解決的是 **React 應用中客戶端 bundle 過大、資料獲取效率低落、以及伺服器端能力無法在元件層級直接使用** 的問題。具體來說，RSC 同時處理以下 5 個子問題：

| 子問題 | 具體表現 |
|---|---|
| **Zero-bundle-size 元件** | 使用 marked（35.9K）、sanitize-html（206K）等函式庫時，即使只在伺服器端渲染靜態內容，這些程式碼仍須下載到客戶端 |
| **客戶端-伺服器瀑布效應** | 父元件在 useEffect 中 fetch 資料 → 子元件等父元件渲染完才開始 fetch → 多輪 round-trip |
| **手動 code splitting** | 開發者需手動使用 `React.lazy()` + dynamic import 才能拆分 bundle，且拆分決策只能在客戶端做 |
| **後端資料源無法直接存取** | 資料庫、檔案系統、內部微服務等後端資源需先建立 API endpoint，再從客戶端 fetch |
| **抽象化稅（abstraction tax）** | 多層元件抽象在客戶端產生不必要的 runtime 開銷與 bundle 體積 |

RSC 的目標是讓 React 應用能「在單一語言、單一框架、單一 API 集合下，同時取得伺服器渲染與客戶端渲染的優點」。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **React 的客戶端中心設計**：React 從 2013 年誕生以來，核心模型是 client-side rendering（CSR）。元件在瀏覽器中執行，所有程式碼（包括僅在伺服器端使用的函式庫）都必須打包進客戶端 bundle。
- **傳統 SSR 的侷限**：React 的 server-side rendering（SSR）僅在伺服器端將 React 元件渲染為 HTML 字串，但客戶端仍需下載、解析、執行完整的 JavaScript bundle 來進行 hydration。SSR 不減少 bundle 大小，只改善首次內容顯示（FCP）。
- **資料獲取模式的演進困境**：從 `useEffect` fetch → Relay/SWR/React Query 等客戶端資料庫 → 仍無法避免客戶端 round-trip。伺服器端資料源（資料庫、檔案系統）始終需要額外的 API 層。

### 通用技術背景（文章中未明確提及但為必要脈絡）

- **JavaScript bundle 膨脹趨勢**：現代前端應用平均 bundle 大小超過 1MB（uncompressed），其中大量程式碼用於非互動性功能（Markdown 渲染、日期格式化、語法高亮）。
- **Web 效能指標演進**：Core Web Vitals（LCP、FID/INP、CLS）成為 SEO 排名因素，促使框架尋找減少 JS 傳輸量的方法。
- **Edge computing 興起**：CDN edge 可執行 serverless 函數，使「在靠近使用者的位置執行伺服器端元件」成為可行選項。
- **React 的元件模型與後端分離**：React 的 declarative 元件模型與 imperative 的後端存取模式之間存在斷層，開發者需手動橋接。

---

## 3. 這個技術是如何解決該問題的？

### 3.1 核心機制

RSC 引入兩種元件類型，透過 `'use client'` 指令區分：

```
┌─────────────────────────────────────────────────┐
│                  React 元件樹                      │
│                                                   │
│  ┌──────────────────┐  ┌──────────────────┐      │
│  │  Server Component │  │  Client Component │      │
│  │  (無 directive)   │  │  ('use client')   │      │
│  │                   │  │                   │      │
│  │ • 只在伺服器執行   │  │ • 在瀏覽器執行     │      │
│  │ • 可 async/await  │  │ • 可用 useState    │      │
│  │ • 可直接讀 DB/FS  │  │ • 可用 useEffect   │      │
│  │ • 0 bundle 貢獻   │  │ • 可處理事件       │      │
│  └──────────────────┘  └──────────────────┘      │
│         │                       ▲                  │
│         │ 傳遞序列化 props      │ 接收已渲染的 JSX  │
│         └───────────────────────┘                  │
└─────────────────────────────────────────────────┘
```

### 3.2 渲染流程

```
Step 1: 伺服器端
  ┌─────────────┐
  │  Router 匹配  │ → 決定根 Server Component
  └──────┬──────┘
         ↓
  ┌─────────────┐
  │ React 渲染   │ → 遞迴渲染 Server Components
  │ Server Tree  │   遇到 Client Component 時停止
  └──────┬──────┘   遇到 native element 時序列化為 JSON
         ↓
  ┌─────────────┐
  │ 串流輸出     │ → 輸出為「React 回應格式」(非 HTML)
  │             │   • native elements → JSON 描述
  │             │   • Client Components → 序列化 props + bundle reference
  │             │   • Suspense boundary → placeholder → 完成後補發
  └─────────────┘

Step 2: 客戶端接收
  ┌─────────────┐
  │ 接收串流     │ → 逐步反序列化
  └──────┬──────┘
         ↓
  ┌─────────────┐
  │ React 合併   │ → 將新 props 合併進現有 Client Components
  │ (reconcile)  │   保留 focus、state、動畫
  └─────────────┘
```

### 3.3 關鍵技術細節

**a) 序列化格式（非 HTML）**

RSC 的回應不是 HTML，而是 React 自訂的序列化格式（類似 JSON，但包含 React element tree 的結構化描述）。這使得 refetch 時 React 可以執行 reconciliation，將新 props 合併進現有 Client Component，而不會破壞客戶端狀態。

**b) 自動 code splitting**

Server Component 中對 Client Component 的 `import` 自動被 bundler 視為 code split point。與傳統 `React.lazy()` 的差異：

| 面向 | 傳統 lazy | RSC 自動 split |
|---|---|---|
| 觸發時機 | 客戶端渲染到該元件時才開始載入 | 伺服器端決定後立即通知客戶端載入 |
| 開發者工作量 | 需手動改寫 import | 無需改寫 |
| 條件式載入 | 需在客戶端 runtime 判斷 | 在伺服器端判斷，客戶端只收到結果 |

**c) async/await 支援**

Server Component 可以是 async function，直接在 render 階段 await 資料庫查詢或檔案讀取：

```jsx
// Server Component — 0 bundle cost
import db from './database';

async function Note({id}) {
  const note = await db.notes.get(id);  // 直接讀資料庫
  return <div>{note.title}: {note.body}</div>;
}
```

**d) Server Actions（React 19）**

`'use server'` 指令定義可在客戶端呼叫的伺服器端函數，用於處理 mutation：

```jsx
// Server Action
async function updateName(formData) {
  'use server';
  await db.users.updateName(formData.get('name'));
}

// Client Component 可直接呼叫
'use client';
function Form() {
  return <form action={updateName}>...</form>;
}
```

### 3.4 與傳統 SSR 的差異對照表

| 面向 | 傳統 SSR | RSC |
|---|---|---|
| **輸出格式** | HTML 字串 | React 序列化格式（結構化資料） |
| **bundle 大小** | 不減少（所有元件仍須下載） | Server Components 貢獻 0 bundle |
| **hydration** | 需完整 hydration（下載+解析+執行全部 JS） | 僅 Client Components 需 hydration |
| **資料獲取** | 需先建立 API endpoint | 可直接讀資料庫/檔案系統 |
| **狀態保留** | 每次 navigation 重新載入 HTML，狀態遺失 | refetch 時 reconciliation 保留 Client Component 狀態 |
| **串流** | React 18 支援 `renderToPipeableStream` | 原生串流 + Suspense boundary |
| **互動性** | 需等待 hydration 完成 | Server Components 無互動性，由 Client Components 處理 |
| **適用場景** | 改善 FCP，不減少 JS 傳輸量 | 減少 JS 傳輸量 + 改善資料獲取效率 |

### 3.5 RSC vs Streaming SSR 量化效能對比

Streaming SSR（React 18 `renderToPipeableStream` + Suspense）與 RSC 共享串流能力，但在 bundle 體積、hydration 範圍、記憶體使用等維度有根本差異。以下數據來自真實案例與 React 18 架構分析：

#### 3.5.1 量化指標對照表

| 效能指標 | 傳統 SSR（`renderToString`） | Streaming SSR（`renderToPipeableStream`） | RSC（React 19） | 數據來源 |
|---|---|---|---|---|
| **初始 JS bundle** | 100%（所有元件） | 100%（所有元件） | Server Component 部分 0%；僅 Client Component bundle | Vercel blog、Josh Comeau 圖解 |
| **hydration 範圍** | 全部 DOM 節點 | 全部 DOM 節點（但可 selective） | 僅 Client Component 對應的 DOM 節點 | React 18 架構討論 #37 |
| **FCP** | 改善（早期 HTML 輸出） | 改善（串流 HTML，Suspense boundary 可提前 flush） | 改善（串流 RSC Payload，但需轉換為 HTML） | Josh Comeau 時序分析 |
| **TTI** | 等於 FCP + 完整 JS 載入 + hydration | 等於 FCP + 完整 JS 載入 + hydration（selective hydration 可部分提前） | 等於 FCP + Client Component JS 載入 + 部分 hydration | React 18 架構討論 #37 |
| **LCP** | 依賴完整頁面渲染完成 | 串流可提前顯示關鍵內容 | 真實案例：4.5s → 220ms（20x 改善） | Dagster dbt docs 遷移報告 |
| **記憶體使用** | 高（客戶端需維持完整元件樹） | 中高（串流減少部分記憶體） | 真實案例：350MB → 16MB（20x 改善） | Dagster dbt docs 遷移報告 |
| **First Byte 延遲** | 低（直接輸出 HTML） | 低（直接輸出 HTML） | 較高（需序列化為 RSC Payload 格式） | 推估：RSC Payload 序列化開銷 |
| **資料獲取瀑布** | 存在（需先 fetch → render → hydrate） | 部分消除（fetch → stream HTML） | 消除（async component 直接 await DB） | React 18 架構討論 #37 |
| **blocking time** | 高（完整 hydration 阻塞主執行緒） | 中（selective hydration 可分散） | 真實案例：profiler 顯示 blocking time 歸零 | Dagster dbt docs 遷移報告 |

#### 3.5.2 時序差異（Josh Comeau 網路請求圖分析）

```
傳統 SSR:
  DB query ──→ renderToString ──→ HTML ──→ load JS ──→ hydrate ──→ interactive
  [server]       [server]        [network]  [client]    [client]

Streaming SSR:
  DB query ──→ renderToPipeableStream ──→ HTML chunks ──→ load JS ──→ selective hydrate
  [server]       [server streaming]      [network]       [client]    [client]

RSC:
  DB query ──→ render Server Components ──→ RSC Payload ──→ reconcile → interactive
  [server]       [server]                   [network]        [client]
  (無需 client round-trip，無需完整 hydration)
```

#### 3.5.3 關鍵差異總結

- **Bundle 體積**：Streaming SSR 不減少 bundle 大小，RSC 可消除 Server Component 全部 bundle。這是兩者最根本的量化差異。
- **Hydration 範圍**：Streaming SSR 的 selective hydration 僅改變 hydration 的時序（先 hydrate 可見區域），不改變總 hydration 量。RSC 從根本上減少需 hydration 的元件數量。
- **記憶體**：RSC 的真實案例（Dagster）顯示 20x 記憶體改善，來自 Server Component 的 JS 物件與 closure 完全不在客戶端建立。
- **First Byte 延遲**：RSC 的序列化格式（非 HTML）引入額外開銷，在極低延遲場景（< 100ms）可能劣於 Streaming SSR。但此開銷在真實案例中被 bundle 減少與瀑布消除的效益覆蓋。

### 3.6 與傳統 CSR 的差異

| 面向 | CSR | RSC |
|---|---|---|
| **首次渲染** | 空白頁 → 載入 JS → 渲染 | 串流 Server Component 輸出 → 逐步顯示 |
| **資料獲取** | useEffect → fetch → API → DB | 直接 await DB/FS |
| **SEO** | 需額外 SSR/SSG 處理 | 可搭配 SSR 輸出 HTML |
| **互動性** | 立即（JS 載入後） | 需等待 Client Component bundle 載入 |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **傳統 SSR（React 18 `renderToString` / `renderToPipeableStream`）** | 在伺服器端將 React 元件渲染為 HTML 字串，客戶端再 hydration | 需 Node.js 伺服器；需處理 hydration mismatch | bundle 大小不減少；hydration 期間頁面不可互動；複雜的資料預載入機制 | 改善 FCP 與 LCP，但 TTI 不受影響 |
| **Static Site Generation（SSG / Next.js `generateStaticParams`）** | 在建置階段預先渲染所有頁面為靜態 HTML | 頁面內容在建置時已知；資料變更頻率低 | 動態內容需 client-side fetch；大量頁面時建置時間長；不適合使用者特定內容 | 極佳 FCP/LCP，零伺服器成本，但動態性受限 |
| **Qwik / Resumable（含 `qwikloader`）** | 序列化應用狀態到 HTML 中，無需 hydration，僅在互動時 lazy load 對應 JS | 需專用框架（Qwik City）；元件需遵循 resumable 模型 | 框架生態較小；序列化開銷；部分 React 生態工具不相容 | 極小初始 JS（< 1KB），TTI 接近 FCP |
| **Islands Architecture（Astro / Fresh）** | 頁面預設為靜態 HTML，僅互動性元件（islands）載入客戶端 JS | 需 islands 框架；元件需明確標記為 interactive | 跨 island 通訊複雜；不適合高度互動的 SPA；React 生態整合有限 | 頁面層級零 JS，僅互動部分載入 bundle |
| **tRPC（TypeScript RPC）** | 在 TypeScript 專案中自動推導 API 型別，消除前後端型別不一致 | 前後端皆 TypeScript；需 tRPC server adapter | 僅解決型別問題，不減少 bundle；仍需要 API endpoint；不改變渲染模型 | 消除型別不一致，減少 API 文件維護成本 |
| **GraphQL + Relay** | 客戶端宣告資料需求，伺服器端精準回應，避免 over/under-fetching | 需 GraphQL server + schema；Relay 編譯步驟 | 學習曲線高；schema 維護成本；不減少 bundle 大小；仍需要 API endpoint | 精準資料獲取，消除 round-trip，型別安全 |

### 4.2 各方案切入點差異

```
問題維度                    SSR    SSG    Qwik   Islands  tRPC   GraphQL  RSC
─────────────────────────────────────────────────────────────────────────────
減少 bundle 大小            ✗      ✗      ✓      ✓        ✗      ✗       ✓
消除 API endpoint 需求      ✗      ✗      ✗      ✗        ✗      ✗       ✓
保留客戶端狀態              ✗      ✗      ✓      ✓        N/A    N/A     ✓
自動 code splitting         ✗      ✗      ✓      ✓        ✗      ✗       ✓
型別安全                    ✗      ✗      ✗      ✗        ✓      ✓       ✗
生態成熟度                  ✓      ✓      ✗      △        △      ✓       △
```

### 4.3 主流框架支援情況

| 框架 | RSC 支援狀態 | 實作方式 | 備註 |
|---|---|---|---|
| **Next.js App Router** | ✅ 完整支援（React 19） | 第一個完整實作 RSC 的框架；bundler 整合 webpack/turbopack | 由 Vercel 維護，與 React 團隊密切合作 |
| **React Router v7** | ✅ 支援 | 基於 Vite 的 full-stack 框架，支援 RSC + Server Functions | 由 Shopify 維護（原 Remix 團隊） |
| **Remix v2** | ❌ 不支援 | 使用 loader/action 模型，非 RSC | v3 計畫中 |
| **TanStack Start** | ✅ Beta 階段 | 基於 TanStack Router + Nitro + Vite | 2025 仍在 beta |
| **Expo** | ❌ 不支援 | React Native 不支援 RSC | 行動端無對應概念 |

### 4.4 2025-2026 發展趨勢

| 趨勢 | 說明 | 證據 |
|---|---|---|
| **RSC 成為 React 預設架構** | React 19 將 RSC 列為穩定功能，官方文件推薦 Next.js App Router 為起點 | React 19 發布 blog、react.dev 框架推薦頁面 |
| **框架層級 API 標準化** | React 團隊正與 bundler 開發者合作，穩定 RSC 底層 API | React 19 文件中明確指出 bundler API 仍在變動中 |
| **Server Actions 生態成熟** | `useActionState`、`useOptimistic`、`useFormStatus` 等 hooks 使表單處理與 mutation 標準化 | React 19 新 API |
| **Edge RSC 普及** | RSC 可在 edge runtime 執行，降低延遲 | Vercel Edge Runtime、Cloudflare Workers 支援 |
| **Partial Prerendering（PPR）** | Next.js 正在開發 PPR，結合 SSG 的靜態效率與 RSC 的動態能力 | Next.js 官方 roadmap |
| **非 React 框架跟進** | Qwik 的 resumable 模型、Solid 的 server components 概念類似但不同 | 各框架官方 blog |

---

## 5. User Q&A

### Q1：RSC 與 Streaming SSR 的效能對比數據為何不足？

**A**：R1 報告 §3.4 僅提供功能面對照（輸出格式、bundle 大小、hydration 範圍等），未包含量化效能指標。本輪補上 §3.5 的量化對照表，涵蓋 9 個維度。

| 維度 | R1 涵蓋 | R2 補充 |
|---|---|---|
| bundle 大小 | 功能描述（減少 vs 不減少） | 量化：Server Component 0% vs 100% |
| hydration | 功能描述（完整 vs 部分） | 量化：全部 DOM vs 僅 Client Component DOM |
| FCP/TTI/LCP | 無 | 時序圖 + 真實案例數據（LCP 4.5s→220ms） |
| 記憶體 | 無 | 真實案例（350MB→16MB） |
| First Byte 延遲 | 無 | 推估：RSC 序列化開銷較高 |
| blocking time | 無 | 真實案例：profiler 顯示歸零 |

**結論**：R1 報告缺少量化數據，R2 以真實案例（Dagster dbt docs 20x 改善）與 React 18 架構分析補足 9 維度對照。

### Q2：Streaming SSR 與 RSC 的效能差異根源是什麼？

**A**：兩者的效能差異根源在於「Streaming SSR 不改變 bundle 體積與 hydration 總量，僅改變傳輸時序；RSC 從根本上消除 Server Component 的 bundle 與 hydration 需求」。

| 面向 | Streaming SSR | RSC |
|---|---|---|
| 解決的問題 | 改善 FCP（提前顯示 HTML） | 減少 JS 傳輸量 + 消除資料獲取瀑布 |
| 機制 | 串流 HTML chunks + selective hydration | 序列化 RSC Payload + reconciliation |
| bundle 影響 | 無（所有 JS 仍須下載） | Server Component 0 bundle |
| hydration 影響 | 總量不變，時序分散 | 總量減少，僅 Client Component |
| 資料獲取 | 仍需要 API endpoint | 直接 await DB/FS |
| 客戶端狀態 | 每次 navigation 遺失 | reconciliation 保留 |

**結論**：Streaming SSR 是傳輸層最佳化（改善 FCP），RSC 是架構層變革（消除 bundle + 消除 API endpoint）。兩者非取代關係，RSC 可疊加在 Streaming SSR 之上（Next.js App Router 即為此組合）。

---

## 6. 附錄：關鍵名詞對照

| 名詞 | 說明 |
|---|---|
| **Server Component** | 僅在伺服器端執行的 React 元件，無 `'use client'` 指令，可 async |
| **Client Component** | 在瀏覽器執行的 React 元件，檔案頂部有 `'use client'` 指令 |
| **Server Action** | 在客戶端可呼叫的伺服器端函數，使用 `'use server'` 指令 |
| **RSC Payload** | React 伺服器端輸出的序列化格式，非 HTML |
| **Reconciliation** | React 將新 RSC payload 合併進現有 Client Component 的過程 |
| **Suspense** | 允許元件在等待非同步資源時顯示 fallback 的機制 |
