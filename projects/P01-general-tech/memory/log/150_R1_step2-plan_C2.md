# 150_R1_step2-plan_C2.md

## 狀況理解

C2 補查背景脈絡：既有 web terminal 方案對比、原生 binary 在瀏覽器執行的限制、專案維護性評估。使用者核心問題是「能否在瀏覽器中執行原生 binary（opencode/claudecode）」，terminal-browser 的方向是反過來的（把瀏覽器放進 terminal），需要釐清這是否構成本質變化。

## 執行的動作與結果

| 動作 | 目的 | 預期達成效果 | 實際結果 |
|------|------|-------------|---------|
| 查 awrit（前身專案） | 了解 terminal-browser 的前身與演進 | 取得 awrit 的現狀與教訓 | awrit 已於 2026-04-25 被 owner 歸檔，owner 表示無時間維護，推薦改用 cmux |
| 查 cmux（manaflow-ai） | 了解同領域更成熟的專案 | 取得對比基準 | cmux 25.4k stars, 2.1k forks, 基於 Ghostty 的 macOS terminal，內建瀏覽器 + agent-browser 相容 API，GPL-3.0，團隊開發 |
| 查 Electron offscreen rendering | 了解 terminal-browser 的底層技術 | 確認技術可行性 | Electron 提供 GPU accelerated 與 software output device 兩種模式，terminal-browser 使用 GPU 模式直接讀取 texture |
| 查 terminal-browser Actions 頁面 | 了解 CI/CD 活躍度 | 評估開發活躍度 | 42 次 workflow runs，全部由 RobPruzan 一人觸發，每次約 30s-1m30s |
| 查 dependency graph | 了解依賴管理 | 確認專案成熟度 | dependency graph 未啟用，無安全掃描 |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 驗證結果 |
|---------|-------------|---------|
| 前身專案 awrit 狀態 | 已歸檔，owner 放棄維護 | 1.4k stars，BSD-3-Clause，2026-04-25 歸檔 |
| 同領域成熟專案 cmux | 25.4k stars，團隊開發，GPL-3.0 | cmux 內建瀏覽器功能與 terminal-browser 重疊，但 cmux 是 terminal emulator 本身 |
| terminal-browser 開發活躍度 | 42 次 workflow runs，全由 RobPruzan 一人 | 高頻率但單一開發者，無 code review 機制 |
| 使用者核心問題匹配度 | terminal-browser 是「瀏覽器進 terminal」，非「terminal 進瀏覽器」 | 方向相反，不解決使用者問題 |
| 專案成熟度 | 25 天，v0.3.2，無 license，Apple Silicon only | 極早期，不適合生產依賴 |
| 替代方案對比素材 | awrit（已死）、cmux（活躍）、xterm.js（web terminal）、ttyd（web terminal） | 素材充足 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---------|---------|---------|---------|
| 是否深入查 xterm.js / ttyd 等既有 web terminal | 是 / 否 | 否 | 使用者問的是「相比既有 web terminal 的亮點」，但 terminal-browser 根本不在同一賽道（它是 terminal 內的瀏覽器，不是瀏覽器內的 terminal），對比意義有限，報告中簡述即可 |
| 是否查 RobPruzan 背景 | 是 / 否 | 否 | 非必要，專案狀態已足夠判斷 |
| 是否查 Linux support PR 細節 | 是 / 否 | 否 | 報告中提及 roadmap 即可 |
