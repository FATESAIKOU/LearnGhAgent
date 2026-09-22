# 270_R1_step2-plan_C1.md

## 狀況理解

本輪為 R1 初次分析。Step 1 已鎖定標的＝`abue-ammar/tinycast`（原生 macOS 啟動器），並定調：第二大腦無此主題、也無 launcher 域舊評估，報告以通用知識為主、引使用者「日常在 Mac 上」硬體脈絡，正面處理「原生零相依開源 vs 成熟商業閉源（Raycast／Alfred）」的對照軸。C1 任務＝依 document skill 取得 repo metadata 與主要文件，為後續收斂（C2）建立事實基礎。

## 執行的動作與結果

以 `gh repo view` / `gh api`（tree、contents、commits）完成，全走一般 API，未遇 CAPTCHA、不需 CDP。

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view abue-ammar/tinycast --json ...` | 取得 metadata | stars、license、分支、更新時間、語言 | 7,023 stars；`main`；Swift 6.0；pushed 2026-09-21；homepage tinycast.dev；created **2026-06-29**（repo 僅約 3 個月）；desc「tiny, fully native macOS launcher, hotkeys, clipboard history」 |
| tree `?recursive=1` | 盤點文件結構 | 找出 key 子文件 | 根有 README、AGENTS.md、CLAUDE.md、CONTRIBUTING、SECURITY、NOTICE、LICENSE；`docs/` 有 architecture/standards/testing/ui/development/release/signing + 26 個 feature 文件；`docs/features/` 含 extensions/mcp/raycast-import；`Scripts/raycast-runtime/`（JS runtime build）；`website/` 為 Next.js 文件站 |
| 抓 `README.md` 全文 | 理解定位與機制 | 掌握定位、功能、安裝、權限 | 定位「one hotkey, everything under 100 MB RAM」；功能 20 項（launcher、per-app hotkey、Spotlight 檔案搜尋、clipboard、dict、計算機、Quicklinks、Shortcuts、Snippets、custom commands、window mgmt 34 種、calendar、notes、emoji、AI chat 預設關、Quick Actions、Raycast extensions）；SwiftUI＋AppKit、零第三方相依、無 Electron 無 telemetry；macOS 26+；brew tap 安裝、Apple silicon/Intel 兩 cask |
| 抓 `AGENTS.md`（repo 規範） | 理解工程判準 | 掌握 Non-negotiables 與 posture | **Posture＝latest-only always**（只支援單一最新 macOS，無相容層，此為 codebase 精簡主因）；Non-negotiables：RAM<100 MB 鐵則、零洩漏、`AppCore` 單一 owner、`Model/` 不可 import AppKit/SwiftUI、Swift 6 data-race 硬錯誤、dark baseline、extension 與核心 UI 嚴格隔離、AI 功能預設關閉且不隨 backup 授權 |
| 抓 `docs/architecture.md` | 理解架構分層 | 掌握機制如何達成「原生」 | PURE（Foundation-only，環境全注入）→ EFFECT（AppKit/CGEventTap/URLSession）→ OBSERVABLE（39 stores）→ VIEW（SwiftUI），由 `Tests/` harness 編譯 shipped 來源強制分層；`AppCore.shared` 單一 wiring point |
| 抓 `docs/standards.md` | 理解工程標準 | 掌握命名與風格規範 | 最新 API 優先、Observation 非 ObservableObject、Swift Concurrency 非 DispatchQueue、刪除而非 deprecate；Carbon 僅兩個 capability-gap 用途（RegisterEventHotKey、TIS input source） |
| 抓 `docs/features/extensions.md` | 理解 Raycast 相容機制 | 掌握「跑 Raycast extensions」如何做到 | 同一 `package.json`＋prebuilt CommonJS bundle，用 **JavaScriptCore**（macOS 內建、零 binary 成本）＋自製 `@raycast/api` shim 與 Node polyfills 原生渲染；`__slot` 與 `$fn` 機制把 React tree 序列化給 Swift；選配、確認後才啟用、不隨 backup |
| 抓 `LICENSE`＋`NOTICE.md`＋`SECURITY.md`＋`CONTRIBUTING.md` | 確認授權與維護判準 | 佐證成熟度與開源誠信 | **AGPL-3.0**；NOTICE 僅列品牌 icon（Simple Icons CC0 / Lobe MIT）；SECURITY 關注 TCC、clipboard 磁碟快取、網路 consent-gated、hotkey stack；CONTRIBUTING 以 RAM<100MB、zero-leak、before/after 影片為 PR 硬門檻，feature set 刻意封閉（「another launcher has it」不是理由） |
| `commits?per_page=15` | 看活躍度與節奏 | 佐證成熟度 | 每天多筆 commit（2026-09-19~21 密集），近期功能：extensions menu bar、Raycast TLS、clipboard pinned、window commands、Polar support 頁；無 CI，靠本地 harness＋CodeRabbit |

**關鍵發現（供 C2 收斂）**：
- **repo 極新（2026-06-29 創建、約 3 個月）但極活躍**（daily commits、7k stars）——「原生零相依」不是草稿願景而是可執行 codebase，架構文檔詳實（architecture/standards/testing 齊全），成熟度需以工程強度而非 star 數判斷。
- **核心矛盾定位**：README 主打「free, open source, staying that way」＋AGPL，正好對照 Raycast 閉源訂閱制；但其「跑既有 Raycast extensions」能力同時是對 Raycast 生態的相容策略（吸其擴充、免其費用）。
- **Posture「latest-only」**：macOS 26+、只支援單一最新 OS、刪除而非兼容——這是它保持 <100MB 的關鍵，也是對使用者「要不要為啟動器付費」判準的直接素材（開源可自建，但鎖死最新 macOS）。
- 隱私張力：無 telemetry、offline by default、AI 功能全預設關閉且 consent-gated、clipboard 僅本機——與 Step 1「無 telemetry」定位一致，可對照 Raycast 的 telemetry/訂閱。

查證來源（GitHub API，高信任）：
- `repos/abue-ammar/tinycast`（main @ 2026-09-21，created 2026-06-29，7,023 stars）
- README.md / AGENTS.md / docs/architecture.md / docs/standards.md / docs/features/extensions.md / LICENSE / NOTICE.md / SECURITY.md / CONTRIBUTING.md / 近 15 筆 commits

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Metadata 完整性 | gh repo view 全欄位 | stars/license/branch/created/pushed/desc 齊全；license 回傳 `other`，以 LICENSE 全文確認＝AGPL-3.0 |
| 文件取得 | git tree＋contents 逐檔 base64 decode | README、AGENTS、architecture、standards、extensions、LICENSE、NOTICE、SECURITY、CONTRIBUTING 皆成功讀取 |
| 機制理解 | 交叉比對 README「features」與 extensions.md「How it works」 | 「零相依原生」可由架構分層＋JS runtime build 驗證；JavaScriptCore 機制與「無 Electron 無 Node」宣稱一致 |
| 對照素材 | README 定位＋LICENSE＋extensions 相容策略 | 有充分素材支持「開源原生 vs 閉源訂閱」論點與「吸 Raycast 生態」切入點 |
| 反爬需求 | 全程一般 gh api | 無 CAPTCHA，CDP 未使用 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研深度 | 僅 README；README＋AGENTS＋架構＋features 重點 | README＋AGENTS＋architecture＋standards＋extensions＋LICENSE＋NOTICE＋SECURITY＋CONTRIBUTING | 標的宣稱「零相依、無 Electron」，架構與 AGENTS 是驗證此宣稱的關鍵，非僅行銷 README；extensions 為其最獨特賣點須深入 |
| license 判定 | 依 gh 回傳 `other`；讀 LICENSE 全文 | 以 LICENSE 全文判定 AGPL-3.0 | gh metadata license 欄對 AGPL 標示不精準（回 `other`），須以檔全文為準 |
| 「原生零相依」可信度 | 視為行銷詞；以架構文件＋JS runtime 交叉驗證 | 以架構分層＋`Scripts/raycast-runtime`（JavaScriptCore、無 Node binary）為據 | 避免把 README 行銷詞當事實，以可查證的 runtime/build 結構佐證 |
| repo 新舊權重 | 因極新而貶低；以工程強度評 | 以工程強度（文檔齊全＋harness 強制分層＋daily commit）評成熟度，star 僅作參考 | 依 Step 1 判準（理解優先），repo 年齡不直接等於品質或符合他的目的 |
