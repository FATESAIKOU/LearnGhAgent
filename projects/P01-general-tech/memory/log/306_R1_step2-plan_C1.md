# 306_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1 任務：取得 ArtCraft（`storytold/artcraft`）repo metadata 與主要文件。R1 首輪、無前輪。Step 1 交棒缺口：技術定位、核心機制、與同類 creator-IDE 的差異、影片 135 期無字幕軌。C1 聚焦 metadata＋文件實查，補查背景脈絡與團隊來歷；替代方案 DA 表與更深的機制細節留待 C2。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh api repos/storytold/artcraft` | 驗證 issue 數值 | 確認 stars/license/語言/時間 | 30,867★、4,903 fork、Apache-2.0、Rust、2022-03-31 建立、2026-10-15 最後 push、437 open issues、topic：3d-graphics/ai/aivideo/filmmaking/imagegeneration、homepage getartcraft.com |
| `gh api` 列根目錄與子目錄 | 掌握 monorepo 結構 | 找出關鍵文件 | README/ROADMAP/AGENTS/Cargo.toml；`_docs/`、`docs/`、`crates/`、`frontend/`、`artcraft-native/`、`_database/` |
| curl README.md | 取得自述與問題陳述 | §1、§3 素材 | 定位「The IDE for artists.」；2D 合成＋3D 場景＋模型自選；62 模型目錄；provider 表 |
| curl ROADMAP.md／AGENTS.md／Cargo.toml | 補目標與工程邊界 | 確認架構與技術棧 | 目標：打敗聚合網站、去除自架服務依賴、更多 Rust；Tauri 桌面＋Nx/React/Vite/Zustand/Three.js；workspace 列出全部 crate |
| curl `_docs/dev_setup.md`／`artcraft_omni_api.md` | 取得開發與 API 機制 | 補「如何運作」 | Rust+Tauri 桌面；Omni API（`api_key` 認證）；後端 API 在 `api.storyteller.ai`、CDN `cdn-2.fakeyou.com` |
| curl `artcraft-native/README.md`、`docs/performance.md` | 看純 Rust 分支與工程成熟度 | 掌握技術路線 | 純 Rust egui 桌面（無 Tauri/JS），共用 ArtCraft API client；效能實測 M4 Pro 記錄 |
| `gh api` releases／commits／languages／org repos | 查活躍度與團隊背景 | 交叉驗證 | 最新 v0.41.0（2026-09-26）；近期 commit 集中 `artcraft-native`；Rust 9.97MB > TS 6.6MB；org 內有 fakeyou/vocodes 語音專案 |
| `webfetch` getartcraft.com | 取得產品定位與主張 | 補 §1 使用者面向 | 「Capable tools for artists」、免費開源、無訂閱、反聚合中間人；Craft Apps 系列（PhotoCraft/FilmCraft…） |
| `webfetch` 搜尋 | 查團隊來歷與更名史 | 補背景脈絡 | 同團隊做 FakeYou/Storyteller.ai，創辦人 echelon（Brandon Thomas），由 storyteller.ai 更名為 ArtCraft |

**關鍵發現**：ArtCraft 對自身命題的定義是「**把 prompt 變成 crafting**」——文本提示缺乏對構圖／角色一致性／鏡頭的控制，故先在 2D／3D 場景中「搭好景」再生成。核心機制：①Tauri 桌面＋可選純 Rust egui 版；②OmniGen 端點（`/v1/omni_gen/{models,cost,generate}/{image,video,audio}`，能力由伺服器下發）；③模型目錄 62 個（圖 16／影 25／音 5／3D 11／世界 5）；④Provider 抽象（`artcraft_router`：Artcraft/Fal/GMICloud/Grok/Midjourney/OpenAI Sora/WorldLabs/KinoviWeb）。`CLAUDE.md` 僅是 `AGENTS.md` 的軟連結。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| stars／license | `gh api` | 30,867★ 屬實（issue 30,821 為查詢時點落差）；Apache-2.0，README 載明 MIT/Apache 雙授權 |
| 語言組成 | `languages` | Rust 9.97MB＋TS 6.60MB 為主，含 Python/Shell |
| 活躍度 | releases＋commits | 高活躍；release 約每月，commit 近日集中 native 版 |
| 架構 | README＋Cargo.toml＋AGENTS | 桌面 monorepo；後端服務／官網在**另一個 repo** `artcraft-services`（本 repo 不含） |
| 核心機制 | README＋native README＋omni_api | 場景搭建（2D/3D）＋模型路由；OmniGen 為生成主通道 |
| 團隊來歷 | webfetch＋org repos | 與 FakeYou／Storyteller.ai 同源（API 網域、CDN 皆指向），由 storyteller.ai 更名 |
| 工程成熟度 | dev_setup／performance／releases | 有 CI、實測效能報告、雙桌面實作 |

**C2 待補缺口**：
1. 與同類替代方案（Photoshop/Figma＋外掛、ComfyUI、Krea、Runway/Pika、Midjourney 網頁、OpenArt/Freepik 聚合站）的切入點異同 → §4 DA 表。
2. 「intentional crafting」相對純 prompt 工具的具體可控性證據（場景圖、3D 資產管線細節）。
3. 後端 `artcraft-services` 架構（閉源？）與「去除自架服務依賴」的實現程度。
4. 開源邊界：repo 為 desktop，服務端與官網未開源 → 對「開源」主張的落差須釐清。
5. 影片 135 期無字幕，改尋文字版（GitHub Trending 週報）或註記缺口。

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| metadata 來源 | issue 數值 / `gh api` 實查 | 以 `gh api` 為準 | issue 為轉錄值，須交叉驗證 |
| 文件取用範圍 | 只 README / README＋ROADMAP＋native＋omni | 後者 | 定位與機制分佈在多檔（README 行銷面、native 補架構、omni 補 API） |
| 團隊背景是否查 | 不查 / webfetch 查來歷 | 查 | 「AI IDE」定位需脈絡，同源性影響對「開源」主張的判讀 |
| 後端是否追 | 深挖 `artcraft-services` / 留 C2 | 留 C2 | 本 repo 不含後端，C1 避免超量；落差留待 C2 釐清 |
| 替代方案 | C1 一併做 / 留 C2 | 留 C2 | C1 專注 metadata 與文件，避免 log 超長 |
| native 版定位 | 視為重點 / 視為分支 | 視為技術路線訊號 | ROADMAP 明示「More Rust」，近期 commit 集中此處 |
