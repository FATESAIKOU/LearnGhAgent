# 244_R2_step2-plan_C1.md

## 狀況理解

R2 使用者對 R1 報告 §3.7「AI 為一等公民」做情境化追問，要求三件事：①「AI 第一公民」具體是哪些 scene；② 每個 scene 中「人的動作與體驗」為何；③ 與「一般 Linux 自己裝 claude-code」的體驗差異。本 sub-step（C1）針對這輪意圖補調研：不走 R1 的 metadata 總覽，而是**深入抓取 repo 內 AI 相關的實作文件**（manual/17-ai.md、bin/ 下的 omarchy-agent* 腳本、theme→agent 同步、agents panel、crash 診斷），把「第一公民」從一句話拆成可講述的具體機制。目標是讓 R2 報告能逐場景描述「人做什麼動作、OS 給什麼回應、相對一般裝法的差異」。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 抓 `manual/17-ai.md` | 取得「AI 第一公民」的權威全文 | 掌握官方完整機制列表 | 拿到 9 個預接 agent CLI、lazy-loader(mise stub)、default agent、agents panel、crash 診斷、theme 同步、Omarchy skill 等完整條目 |
| 抓 `bin/omarchy-agent` 原始碼 | 看「按鍵啟動 default agent」的真實行為 | 確認每個 agent 的啟動旗標與工作目錄處理 | 明確 `Super+Shift+Ctrl+A` 走 `omarchy-launch-tui` 開固定 app-id 視窗；`a`/`c`/`cx`/`cy` 內聯；`$HOME` 起動自動改 `~/Work` |
| 抓 `bin/omarchy-default-agent` | 看 default 如何設定/安裝 | 確認選擇流程 | 未設定預設時靜默、menu 全不勾選；`omarchy default agent <name>` 可即裝即選 |
| 抓 `bin/omarchy-theme-set` | 確認 theme→agent 同步是「真的」 | 驗證不只文件宣稱 | 抓到 `omarchy-restart-opencode`、`omarchy-theme-set-claude`、`omarchy-theme-set-pi` 等被實際呼叫 |
| 抓 `bin/omarchy-agent-usage-update` + collectors | 看 agents panel 的資料來源 | 理解 panel 運作 | 3 個 collector（claude/codex/fireworks）每 15 分鐘寫 JSON 到 `~/.local/state/omarchy/agents/usage/`，panel watch 該目錄 |
| 抓 `bin/omarchy-agent-crash` + `toggle-crash-capture` | 看 crash 診斷的實際觸發 | 理解 crash scene | 監 `systemd-coredump`，點通知即把 pid/comm/signal 打包給 default agent + `diagnose-crash` skill；可 `systemctl --user` 停用 |

### 已收斂的 AI 機制清單（供 R2 情境化）

1. **lazy-loaded 啟動器**：`~/.local/bin/` 內 mise 管理的 stub，首次執行才下載對應 agent（claude/codex/opencode/agy/copilot/crush/grok/pi/omp）。
2. **default agent**：`omarchy default agent <name>` 設定，未設時靜默；`Super+Shift+Ctrl+A` 啟動（未設則開 picker）。
3. **agents panel**：頂部列出現，統一顯示各家 plan / 5 小時與週上限百分比 / prepaid 餘額 / 每日與模型 token；每 15 分鐘由 usage collector 刷新。
4. **crash 診斷**：systemd-coredump 監看 → 「Process crashed」通知 → 點擊把 crash 交給 default agent 的 `diagnose-crash` skill。
5. **theme→agent 同步**：切 Omarchy theme 時 `omarchy-theme-set-claude`/`-pi`/`restart-opencode` 等實際被呼叫。
6. **Omarchy Skill**：symlink 進各 agent skill 目錄，讓 agent 能對系統本身調參。
7. **自動批准（auto-approve）**：各 agent 各自以 `--auto`/`--permission-mode auto`/`--approve-for-me`/`--yolo` 等無停問模式跑。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 「第一公民」是否有可列舉機制 | `17-ai.md` 全文 | 有，7 項以上可具體描述 |
| 各 agent 啟動是否為真實 code | `bin/omarchy-agent` case 分派 | 是，逐 agent 有 flag 對應 |
| theme 同步是否真做 | `omarchy-theme-set` grep | 是，實際呼叫 claude/pi/opencode |
| panel 資料來源 | `usage-update` 腳本 | 3 collector + 目錄 watch |
| crash 診斷機制 | crash 腳本 + toggle | 完整（service 可停用、可手動 `omarchy agent crash <pid>`） |

## 其中的決斷點

| 意思決定面向 | 可選項 | 選擇 | 理由 |
|---|---|---|---|
| 調研範圍 | 重跑 metadata 總覽 / 深入 AI 機制 | 深入 AI 機制 | R2 意圖是「情境化 AI 第一公民」，metadata 已在 R1 完成，重跑浪費 |
| 文件深淺 | 只看 manual/ 摘要 / 追到 bin/ 實體腳本 | 追到實體腳本 | 使用者要「人的動作與體驗」，只有看懂實際啟動/同步/收集程式碼才能講「OS 回應」，非摘要可代 |
| 是否需要 CDP | 用 / 不用 | 不用 | `gh api` 全程成功，無 CAPTCHA，依 SKILL 優先一般 fetch |
| 是否進入替代方案 | 本 sub-step 做 / 後續 C2 | 後續 C2 | 使用者問「對比一般 Linux 裝 claude」，對照描述屬分析收斂，非資料收集，放後續 |
