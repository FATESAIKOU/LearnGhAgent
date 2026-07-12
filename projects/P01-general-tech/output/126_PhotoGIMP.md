# PhotoGIMP 技術分析報告

## 1. 這個技術解決什麼問題？

PhotoGIMP 解決的是「Photoshop 使用者轉移至 GIMP 時的高學習成本」問題。

具體來說：GIMP 與 Photoshop 雖然都是點陣圖影像編輯軟體，但兩者的 UI 佈局、工具排列、快捷鍵映射、面板配置存在顯著差異。一個熟練的 Photoshop 使用者初次使用 GIMP 時，會因為找不到對應工具、快捷鍵不直覺、工作區配置陌生而產生挫折感，導致轉移意願低落。

PhotoGIMP 不是一個獨立的影像編輯軟體，而是一組 GIMP 3+ 的設定檔 patch，將 GIMP 的版面配置與操作習慣改造為接近 Photoshop 的體驗。

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- GIMP 是 GNU Image Manipulation Program，一個自由開源的點陣圖影像編輯器，GPL-3.0 授權
- Photoshop 是 Adobe 的商業影像編輯軟體，訂閱制收費
- PhotoGIMP 的目標是讓 GIMP 對 Photoshop 使用者更友善，降低轉移門檻

### 通用技術背景（文章中未明確提及，由調研補上）

**GIMP 與 Photoshop 的歷史定位差異：**

| 面向 | GIMP | Photoshop |
|------|------|-----------|
| 授權模式 | GPL-3.0 自由軟體 | 商業軟體，訂閱制（Creative Cloud） |
| 開發模式 | 社群驅動，志願者貢獻 | Adobe 公司閉源開發 |
| 目標使用者 | 開發者、Linux 使用者、預算有限者 | 專業設計師、攝影師、出版業 |
| 預設 UI 哲學 | 多視窗模式（可切換單視窗） | 單視窗整合模式 |
| 快捷鍵慣例 | 自成一派（如 `c`=裁切、`o`=顏色取樣） | 業界事實標準（如 `c`=裁切、`j`=圖層複製） |

**為什麼快捷鍵與 UI 差異會成為轉移障礙：**

影像編輯是高度肌肉記憶驅動的工作。設計師在 Photoshop 中數千小時累積的快捷鍵反射（如 `Ctrl+J` 複製圖層、`[`/`]` 調整筆刷大小）在 GIMP 中完全失效。這不是功能缺失問題——GIMP 具備對應功能——而是操作路徑的重新學習成本。

**GIMP 3.0 的變革：**

GIMP 3.0（2024 年釋出）從 GTK2 遷移至 GTK3，支援 Wayland、HiDPI、更多色彩管理。PhotoGIMP 鎖定 GIMP 3.0+ 而非舊版，因為 GTK3 的主題與設定機制更靈活，允許更細緻的 UI 改造。

## 3. 這個技術是如何解決該問題的？

PhotoGIMP 透過覆蓋 GIMP 的使用者設定檔來改造操作體驗。它不修改 GIMP 原始碼，不編譯二進位檔，純粹是設定層級的 patch。

### 3.1 整體架構

```
PhotoGIMP/
├── .config/GIMP/3.0/       ← GIMP 使用者設定目錄
│   ├── shortcutsrc         ← 快捷鍵映射（核心）
│   ├── toolrc              ← 工具排列順序
│   ├── gimprc              ← 全域偏好設定
│   ├── sessionrc           ← 視窗佈局與 dock 位置
│   ├── dockrc              ← dock 面板配置
│   └── theme.css           ← UI 主題微調
├── .local/share/applications/ ← .desktop 檔案（獨立圖示）
├── docs/                   ← 多語翻譯文件
└── screenshots/            ← 展示截圖
```

### 3.2 各設定檔的改造內容

#### shortcutsrc — 快捷鍵映射（核心改造）

將 GIMP 的預設快捷鍵大量替換為 Photoshop 慣用映射：

| 功能 | GIMP 預設 | PhotoGIMP（Photoshop 風格） |
|------|-----------|------------------------------|
| 複製圖層 | `Ctrl+Shift+D` | `Ctrl+J` |
| 矩形選取 | `r` | `m` |
| 橢圓選取 | `e` | `m`（與矩形同鍵，Shift 切換） |
| 套索工具 | `f` | `l` |
| 魔術棒 | `u` | `w` |
| 裁切 | `Shift+C` | `c` |
| 筆刷 | `p` | `b` |
| 橡皮擦 | `Shift+E` | `e` |
| 漸層 | `l` | `g` |
| 模糊/銳利化 | `Shift+U` | `r` |
| 減淡/加深 | `d`（切換前景背景）→ `o` | `o` |
| 文字工具 | `t` | `t`（保留） |
| 路徑工具 | `b` | `p` |
| 滴管 | `o` | `i` |
| 手掌 | `h` | `h`（保留） |
| 縮放 | `z` | `z`（保留） |

**實作方式：** 直接寫入 GIMP 的 `shortcutsrc` 設定檔，每行格式為 `(gtk_accel_path "<Actions>/.../..." "<Primary>j")`。`<Primary>` 在 Linux 對應 `Ctrl`，macOS 對應 `Command`。

#### toolrc — 工具排列

將工具箱中的工具按 Photoshop 的邏輯分組排列：

```
原始 GIMP 排列：          PhotoGIMP 排列：
┌─────────────────┐      ┌─────────────────┐
│ 矩形選取 (r)     │      │ 矩形選取 (m)     │ ← Photoshop 的 Move Tool 在第一個
│ 橢圓選取 (e)     │      │ 對齊工具         │
│ 自由選取 (f)     │      │ 矩形選取 (m)     │
│ 魔術棒 (u)       │      │ 橢圓選取 (m)     │
│ 路徑工具 (b)     │      │ 套索 (l)         │
│ 滴管 (o)         │      │ 魔術棒 (w)       │
│ 裁切 (Shift+C)   │      │ 裁切 (c)         │
│ ...              │      │ 滴管 (i)         │
└─────────────────┘      │ 筆刷 (b)         │
                          │ 橡皮擦 (e)       │
                          │ 漸層 (g)         │
                          │ 減淡/加深 (o)    │
                          │ 模糊/銳利化 (r)  │
                          │ 文字 (t)         │
                          │ 路徑 (p)         │
                          │ 手掌 (h)         │
                          │ 縮放 (z)         │
                          └─────────────────┘
```

#### gimprc — 全域偏好設定

| 設定項 | 值 | 效果 |
|--------|-----|------|
| `canvas-padding-color` | `#1a1a1a` | 深色畫布背景，接近 Photoshop 深色主題 |
| `default-grid` | `(grid 10 10 0x808080 0x404040)` | 網格樣式調整 |
| `undo-levels` | `8` | 復原層級設為 8（Photoshop 預設值） |
| `fullscreen-single-window-mode` | `true` | 全螢幕自動啟用單視窗模式 |
| `theme` | `dark` | 預設深色主題 |

#### sessionrc — 視窗佈局

- 左側 dock 寬度：66px（僅顯示工具圖示，不顯示文字標籤）
- 右側 dock 寬度：443px（容納圖層/色版/路徑面板）
- Toolbox 固定在左側
- 模擬 Photoshop 的「工具欄在左、面板在右」配置

#### theme.css — UI 主題微調

```css
@import url("Dark.css");
@import url("symbolic-icon-theme.css");
```

僅匯入 GIMP 內建的深色主題與符號圖示主題，無大幅 CSS 改寫。這表示 PhotoGIMP 的 UI 改造主要依賴 GIMP 3.0 內建的主題機制，而非自訂 CSS。

#### .desktop 檔案 — 應用程式入口

```desktop
[Desktop Entry]
Name=PhotoGIMP
Icon=photogimp
Exec=flatpak run org.gimp.GIMP
```

- 建立獨立的應用程式圖示（名為 PhotoGIMP，圖示為 photogimp）
- 執行時仍呼叫 flatpak 版的 GIMP
- 讓使用者可以在選單中直接看到「PhotoGIMP」而非「GIMP」

### 3.3 安裝方式

PhotoGIMP 的安裝是純粹的檔案複製：

```
Linux:   將 .config/GIMP/3.0/ 複製到 ~/.config/GIMP/3.0/
Windows: 將對應目錄複製到 %APPDATA%/GIMP/3.0/
macOS:   將對應目錄複製到 ~/Library/Application Support/GIMP/3.0/
```

解除安裝即刪除這些設定檔，GIMP 恢復預設行為。無系統層級修改，無 daemon，無背景程序。

### 3.4 關鍵設計決策

| 決策 | 選擇 | 理由 |
|------|------|------|
| 修改設定檔而非原始碼 | 設定檔 patch | 使用者無需重新編譯 GIMP，安裝/解除安裝零風險 |
| 鎖定 GIMP 3.0+ | 不支援 GIMP 2.x | GIMP 3.0 的 GTK3 架構提供更好的主題與設定支援 |
| 保留 GIMP 核心功能 | 不改功能，只改配置 | 不引入新 bug，不偏離上游 |
| 獨立 .desktop 圖示 | 建立 PhotoGIMP 選單項目 | 讓使用者區分「原版 GIMP」與「PhotoGIMP 配置」 |

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|----------|--------------|----------------|------------------|
| **PhotoGIMP** | 覆蓋 GIMP 設定檔，改造快捷鍵/工具排列/UI 佈局為 Photoshop 風格 | 已安裝 GIMP 3.0+；願意接受非官方 patch | 部分 GIMP 預設快捷鍵失效；需手動更新設定檔（GIMP 升級可能覆蓋） | Photoshop 使用者可在 1-2 小時內上手 GIMP 基本操作 |
| **GIMP 手動自訂** | 使用者自行在 GIMP 偏好設定中修改快捷鍵、工具排列、主題 | 使用者熟悉 GIMP 的設定機制；有時間逐一調整 | 耗時（完整調整約 30-60 分鐘）；無統一配置管理 | 完全客製化，但需使用者自行維護設定 |
| **Krita** | 使用 Krita 作為 Photoshop 替代品，其 UI 設計更接近繪圖軟體慣例 | 願意學習全新軟體；Krita 擅長繪圖而非照片編輯 | Krita 的 CMYK 支援、色彩管理、濾鏡生態系不如 Photoshop/GIMP 成熟 | 對數位繪圖使用者而言學習曲線較低，但對照片編輯者幫助有限 |
| **Photopea** | 瀏覽器端 Photoshop 克隆，UI 與快捷鍵幾乎完全複製 Photoshop | 需要網路連線（或 PWA 離線模式）；接受網頁應用程式的效能限制 | 檔案儲存在瀏覽器端；大型 PSD 檔案效能下降；無原生桌面整合 | Photoshop 使用者幾乎零學習成本，但功能深度不如原生軟體 |
| **Linux 版 Photoshop (Wine/VM)** | 透過 Wine 或虛擬機執行 Photoshop | 需要 Windows 授權；硬體資源充足 | 效能損失 10-30%；部分功能可能不穩定；需要額外設定 | 完全保有 Photoshop 操作體驗，但犧牲效能與穩定性 |

### 各方案切入點差異

```
問題：Photoshop 使用者想轉移至免費/開源方案

方案分類：

┌─ 保留 Photoshop 操作習慣 ─────────────────────┐
│  Photopea（網頁克隆，零學習成本）               │
│  Wine/VM Photoshop（原生體驗，效能犧牲）        │
└────────────────────────────────────────────────┘

┌─ 改造 GIMP 使其像 Photoshop ──────────────────┐
│  PhotoGIMP（一鍵套用，社群維護）                │
│  手動自訂（完全客製，自行維護）                 │
└────────────────────────────────────────────────┘

┌─ 學習全新軟體 ────────────────────────────────┐
│  Krita（繪圖導向，照片編輯功能較弱）            │
│  原生 GIMP（功能完整，UI 需適應）               │
└────────────────────────────────────────────────┘
```

### PhotoGIMP 的定位優勢與限制

**優勢：**
- 安裝/解除安裝零風險（純設定檔，不改系統）
- 社群維護（23 位貢獻者，持續更新）
- 15,617 stars 表示需求真實存在
- GPL-3.0 授權，無法律風險

**限制：**
- 僅改造 UI/UX，不改造功能面（GIMP 缺少的 Photoshop 功能如智慧型物件、調整圖層、Camera Raw 等仍不存在）
- GIMP 升級可能覆蓋設定檔，需重新套用
- 不支援 GIMP 2.x（舊版使用者無法使用）
- 部分 Photoshop 快捷鍵在 GIMP 中無對應功能（如 `Ctrl+Shift+Alt+E` 蓋印圖層），這些映射會被忽略
