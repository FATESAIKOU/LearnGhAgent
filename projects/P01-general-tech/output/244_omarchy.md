# Omarchy —— Basecamp/DHH 推出的「現代化、美好、有主見」Linux 發行版

> 標的：https://github.com/basecamp/omarchy
> 狀態：`4.0.0.alpha`，仍活躍（2026-08-21 有 push），star ~27.7k，MIT License
> 報告產出：R1（首次），無前輪 QA

---

## 1. 這個技術解決什麼問題？

**Omarchy 解決的是「想要一個現代、美觀、立即可用、且『開箱即重個性』的 Linux 桌面，但不想花數週把 Arch Linux＋平鋪視窗管理器＋桌面 shell 從零組起來」的門檻問題。**

具體來說，它把 DHH（Basecamp）個人電腦上整套經過美感與生產力取捨過的桌面環境，打包成一份**安裝 ISO**。使用者安裝後，不是拿到一台「裸的 Linux」，而是拿到一個已經配好 `Neovim`、`Chromium`、`Obsidian`、`LibreOffice`、`Kdenlive`、`OBS Studio`、Winamp 式音樂播放器、平鋪視窗管理與完整主題系統的成品桌面。

它對應的張力是：

| 選項 | 特徵 | 換到的東西 | 付出的代價 |
|---|---|---|---|
| macOS / Windows | 開箱即用、整合好 | 好用 | 封閉、不可控、被供應商綁定 |
| 自己組 Linux（Arch＋Hyprland＋Quickshell） | 完全可控、自由 | 可塑造的桌面 | 極高的上手成本、要自己裝上百個套件、自己寫 hyprland/shell config |
| **Omarchy** | 開箱即用、開放 | 把「開放 + 已經幫你組好」合一 | 接受 DHH 的預設主見（opinionated） |

因此這個技術要解決的問題的「具體且明確的部分」是：**Linux 桌面生態缺乏一個「由特定使用者親手打磨過、打包成發行版、其他人可一鍵復現」的成品**。它站在「要嘛自己從零倒、要嘛用封閉 OS」之間的第三條路。

**問題描述含糊之處**：
- 「現代」與「美」是主觀判準，Omarchy 的美感是 DHH 一人的品味，不是社群共識。
- 「有主見（opinionated）」同時是它的賣點與限制——它預設裝了一整套軟體，你不見得要用，也難以卸掉「他預設的整合方式」。
- 它目前是 `alpha`，還不算是「穩定可遷移日常主力機」的發行版。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章明確提到的背景

- 原文（welcome 手冊）點名三個基石：**Arch Linux**（底層發行）、**Hyprland**（平鋪視窗管理、wlroots 世代）、**Quickshell**（「desktop construction-kit」，用 QML 建桌面 shell 與 widget）。
- 原文把定位說成「**這不是一堆預裝套件的 grab bag**，而是一個以美觀與生產力兩者設計的完整系統」。並引 DHH 的觀點：「美的系統是『激勵的』系統，生產力是動機的下游」。
- 原文說明它「**不是要做得盡量像 Windows/macOS**，而是要美並更好，擁抱 Linux 本性（手動改 config、重終端機）」。

### 通用技術背景（文章未說、為脈絡）

- **Linux 桌面長期碎片化**：不像 macOS/Windows 是單一公司統一定義桌面，Linux 桌面是 GNOME/KDE（重量級、整合好但「不是你的美」）、與 tiling WM（i3 → sway → Hyprland 的 wlroots 世代，輕量可完全掌控但要自己組）兩大陣營的拉扯。近年「重個人化、重美感」的浪潮讓 Hyprland 成為 Linux 美感 subculture 的主要載體，但也顯現「要出個好看的桌面你要自己組很久」的痛點。
- **dotfiles 文化**：硬核 Linux 用戶「漫長組裝自己的 `~/.config`」長久以來是常態，組完也只是「單機可用」，無法無痛複製到新機器。
- **無自有發行版**：市場上把「個人打磨好的 Linux 桌面」直接出成一張 ISO 的，少數、多屬 experiment（如 Vanilla OS、各種 distro fork），且多數無大社群、無持續更新。Omarchy 是少數由知名工程師（DHH，Rails/Basecamp/HEY）背書並以**持續發行管道**運作的案例。
- **「Omakase」脈絡**：DHH 的產品線一貫帶「主廚建議」意涵（HEY 郵件、ON 的 `omakase`），強調「為你作主見」，Omarchy 是這條思路在作業系統層的延伸。

---

## 3. 這個技術是如何解決該問題的？

Omarchy 的解法是**把「一個人的整套打磨桌面」變成「一發可安裝、可更新、可回退的發行版」**，並以一套「system vs user」的分離架構避免使用者的個人化被系統更新覆蓋。以下是「怎麼做」，不含好壞評價。

### 3.1 底層棧（welcome 手冊明言）

```
Arch Linux（base）
   └── Hyprland（wlroots 世代平鋪 WM，Wayland）
        └── Quickshell（desktop construction-kit，QML）
             └── 自訂 shell（shell.qml）+ theme 系統
```

### 3.2 安裝與加密（getting-started）

- 用 **ISO** 安裝，選 `full-disk`（整顆磁碟）或 `free-space`（未分割空間，可與 Windows 雙開）。
- 安裝**預設全碟加密**（LUKS），可在磁碟格式化確認時 `Ctrl+C` 切到無加密模式（遠端/一次性機器用）。
- **必須關 Secure Boot / TPM**（DHH 稱其為「Microsoft security schemes」）。
- 提供 **unattended install**：把 config 放在第二張碟，ISO 可全自動安裝，適作 VM / 大規模佈建基礎。
- 可「替他人安裝」：在鍵盤選擇第一畫面 `Ctrl+C`，延後個人設定到首開機，加密密碼也由新主人首開時設定。

### 3.3 套件內容（the manual 羅列）

| 分類 | 內容 |
|---|---|
| 開發 | Neovim、Development Tools、Shell Tools、Shell Functions、TUIs、git 等 |
| 瀏覽 | Chromium、Firefox 等 |
| 知識/辦公 | Obsidian、LibreOffice、xournalpp |
| 影音/創作 | Kdenlive、OBS Studio、mpv、imv、Winamp 式播放器 |
| 終端 | foot（預設）、alacritty、ghostty、kitty、tmux、btop、lazygit |
| 其他 | Docker、Fastfetch、Starship、fcitx5（輸入）、wireplumber（音訊） |

### 3.4 檔案治理與「system vs user」分離

Omarchy 把配置分成兩層（見 dotfiles 手冊）：

| 層級 | 路徑 | 性質 |
|---|---|---|
| 系統層 | `/usr/share/omarchy` | Omarchy 自身擁有，不該動 |
| 使用者層 | `~/.config` | 「你的檔案」，用於改寫系統預設值 |

> 改 `/usr/share/omarchy` 內的值，做法是「在 `~/.config` 覆寫」，而不是直接改系統檔。這樣 `omarchy update` 的套件與 migration 更新不會被個人設定擋住。

關鍵 config 檔：
- `~/.config/hypr/hyprland.lua`：主 Hyprland config，載入預設＋你以下的 override 檔（bindings/monitors/input/looknfeel/autostart）。
- `~/.config/omarchy/shell.json`：控制 Omarchy shell（bar 位置、widget、screensaver、lock、idle）。
- `~/.config/omarchy/hooks/<event>.d/`：掛鉤機制，`post-boot`、`post-update` 等事件自動執行可執行檔。
- 檔工具建議 `Stow` 備份全部 dotfiles。

### 3.5 Theme 系統

- `themes/` 目錄內多套主題（catppuccin、gruvbox、kanagawa、everforest、flexoki-light、last-horizon、hackerman、lumon 等）。
- 主題由 Quickshell/Quickshell QML 驅動，並「同步到 AI agent」——切換 Omarchy theme 時，Claude Code、Pi、OpenCode 等 agent 的視覺也會跟著切。

### 3.6 更新、回退、與快照

- Omarchy 本身以**普通 pacman package** 安裝（`omarchy-pkgs` repo）。更新是執行 `omarchy update`（menu `Update > Omarchy`），過程包含：裝最新 Omarchy、跑 `migrations/` 內的 migration、更新 Arch mirror 與 AUR 套件。
- **四條更新管道**：`stable`（新機預設，mirror 晚最新一個月以抓不相容）、`RC`（重大發布前驗證）、`edge`（追開發版與最新 Arch 套件）、`dev`（直連 git checkout＋edge，供維護者）。
- **快照回退**：更新前有 `snapper` 快照，壞了可在 bootloader 選回更新前快照。
- 韌體可經 `fwupd`（Linux Vendor Firmware Service）更新。
- 避免用戶直接 `pacman -Syu` / `yay -Syu`，Omarchy 會攔下並導向 `omarchy update`（因為會跳過快照與 migration）。

### 3.7 AI 為一等公民（manual/17-ai.md）

- 不選邊、把主流 **coding-agent CLI** 預先接好成 lazy-loaded 啟動器（mise 管理的 stub，首次執行才下載）：`claude`、`codex`、`opencode`、`copilot`、`grok`、`pi` 等。
- 頂部列新增 **agents panel**，集中顯示各家訂閱的用量、session/週期百分比、prepaid 餘額、token 使用。
- **crash 診斷**：監看 `systemd-coredump`，程式 crash 時給通知，把 crash 交給預設 agent 搭配 `diagnose-crash` skill 自動追根因並決定是否回報上游。
- 熱鍵 `Super+Shift+Ctrl+A` 啟動預設 agent、`a` 內聯跑、`c`/`cx`/`cy` 直接開特定 agent（auto-approve 模式）。

### 3.8 組織與命令

- CLI 以 `omarchy-` 前綴（`omarchy-update`、`omarchy-agent`、`omarchy-default`、`omarchy-mise-install` 等），menu 用 `Super+Space`（如 Monitors、Keybindings、Input、Config）。
- 文件以 `manual/` 為權威來源，鏡像到 learn.omacom.io；repo 另有 `docs/`（參考）、`agents/`（agent skill 程序）三層，並配 `AGENTS.md`/`CLAUDE.md` 給 agent 用。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

> 同題「想要一個現代、美觀、可重現的 Linux 桌面 / 環境」，以下都是 Omarchy 的同級或替代切入點。先對照使用者第二大腦的既有判定（見下「第二大腦對照」）再列方案，避免推到使用者反對的方向。

### 4.1 替代方案

| 方案 | 切入點 | 適合的人 |
|---|---|---|
| **Arch Linux ＋ 個人 dotfiles（自兜）** | 不靠發行版打包，自己用 pacman + dotfiles 組出屬於自己的桌面，可完全控制 | 想要「理解本質」、習慣自己兜、重視掌控的人 |
| **NixOS ＋ home-manager** | 以 declarative Nix 描述整個系統（含桌面），可重現、可版本化，環境即設定 | 要「環境可重現、可 declarative 管理」的人 |
| **不可變發行版（如 Fedora Silverblue / openSUSE MicroOS）** | 以 image/OSTree 為主，系統層唯讀、應用以 Flatpak/容器，更新整機原子、易回退 | 想要「OS 更新風險低、以影像管控」的人 |
| **其他 Arch 系現成發行版（如 EndeavourOS / CachyOS）** | 給一個接近 Arch 的開箱安裝介面，但不帶一套強烈主見的桌面整合 | 想要「易裝的 Arch」但不想要整套既定美學的人 |

### 4.2 DA 對照表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Arch + 自組 dotfiles** | 手動組裝 WM/應用/dotfiles，全套可自控 | 熟悉 Linux、時間充足、願意長期維運自己的 config | 組裝與維運成本高；易「組完就亂」 | 桌面完全屬於你的意志，但**環境不可重現、遷移成本高** |
| **NixOS + home-manager** | 以 Nix 語言宣告整機（系統+ home），重現即 config | 接受 Nix 學習曲線、願用 declarative 取代手動 | 學習成本高、Nix 語法難查、某些桌面元件整合難 | 環境**可重現、可版本化**，跨機複製痛苦小 |
| **不可變發版（Silverblue）** | OS 唯讀、Atomic 更新、應用走 Flatpak/容器 | 接受「系統層不能隨意改」的規律 | 需要習慣以 Flatpak/容器裝應用；某些工具不易裝 | 更新/回退風險低、系統穩定；但自訂自由度受限 |
| **其他 Arch 系現成（CachyOS 等）** | 給 Arch 加個 installer 與預設套件，但「主見」輕 | 想要現成 Arch、不介意缺乏一套「綁定美觀」的整合 | 無系統性的主題/agent 整合；仍要自己組桌面 | 快速拿到可用的 Arch，但「開箱即用」的程度低於 Omarchy |
| **Omarchy（本題）** | 把「個人整套打磨桌面」打包成可裝/可更新/可回退的發行版 | 接受 DHH 的美感與預設套件、接受 alpha、接受全面遷移到 Linux/Hyprland | 若你不用它的整合，帶去預設包袱；alpha 不穩 | 開箱即用的現代化 Linux 桌面、有 system/user 分離與快照回退 |

### 4.3 切入點差異摘要

- **Omarchy vs 自組 dotfiles**：前者把「組裝」這一段外包出去並做成可持續更新的發行版；後者把組裝權留在自己手上，換來全控、失去打包與跨機可攜。
- **Omarchy vs NixOS**：Omarchy 是「把某人的成品打包成 ISO」，NixOS 是「把整個系統用程式描述出來」——前者偏「成品復原」，後者偏「config 即真相」、重現性更高但學習與定義成本高。
- **Omarchy vs 不可變發行版**：不可變版透過「唯讀/容器」換穩定性，Omarchy 則透過「system/user 分離＋snapshot＋migration」換穩定，方向不同。
- **Omarchy vs 其他 Arch 現成**：Omarchy 附帶「綁定的一套主見整合」＋AI agent 第一版公民；其他 Arch distro 通常只解決「安裝」不解決「整合主見」。

### 4.4 對照第二大腦（FATESAIKOU/MyBrain）

| 面向 | 查詢結果 | 信任層級 | 對照結論 |
|---|---|---|---|
| omarchy 是否已評估 | **第二大腦無此條目**（判定總表 92 筆無）。grep `omarchy` / `Hyprland` / `NixOS` / `dotfiles` 無命中 | —（查無） | 全新標的，無既有採用/拒絕結論 |
| 技術取捨準則（骨幹） | [技術取捨準則.md](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md) — 「先自己兜」如果方案不穩或不熟、「MVP→Feature 唯一閘門是能否影響個人 workflow」、「不追新、汰換看上游死沒死」 | `generated.by=claude-code/opus-5`，`status=draft`（未經 review 的 AI 草稿；內含 interview 直接引用） | **衝突**：Omarchy 是全新 alpha、單一主要作者（DHH 主導）、要求整套遷移。依此準則，對他不應「建議整機採用」而應視為「不穩/不熟→先當理解素材抽方案」，不構成汰換任何現有工具 |
| 現行環境 | `動手做/herdr 配置.md`、`追加功能/整理 claudecode/opencode 環境.md` — 他在 macOS 上以 `brew`/`colima`/`tmux`/`herdr`/`iterm`/`claude code`+`opencode` 工作 | `generated.by=claude-code/opus-5`，`status=draft` | **衝突**：Omarchy 是 Linux+Hyprland 硬遷移，與現 macOS workflow 主體相反；依「方向相反是最實質 Reject 訊號」（準則三）與「能跑就不動/汰換看上游死沒死」（準則四），**不建議遷移**，取其整合設計理解即可 |
| 目標環境 | `動手做/Pixel 國際版 FeliCa 與 bootloader 取捨.md`、`動手做/整理 claudecode-opencode 環境.md` — 他對「OS 層設定/整合」有自兜與接受採用 trade-off | `human:fatesaikou` 相關 | 強化「桌面整合設計」可抽取、但「整套遷移」不適用 |

**與本報告 §4 的衝突提示**：若把「解決方案」理解成「幫他建一個 modern Linux 桌面」，則照準則反而指向「自兜 dotfiles／NixOS 這類 declarative 重現」，而非採用 Omarchy。Omarchy 的價值在**抽取其機制**（system/user 分離、theme→agent 同步、AI 第一公民、snapshot+migration 更新），不在整套採用。**第二大腦無對應方案判定，NixOS/dotfiles 亦無既有結論，此為查無、非「確認建議」。**

---

## 5. User Q&A

> 以下 QA 依使用者 R2 追問沉澱。規則：不刪改既有內容；一輪含多子問則拆獨立 QA；遵守「不用比喻、不用情緒語言、不寫可能也許我認為」。

### Q1：具體來說，「AI 為一等公民」是哪幾個 scene？每個 scene 裡人做什麼動作、體驗是什麼？

**A**：「AI 為一等公民」不是一句口號，而是 **7 個可獨立觸發、由 Omarchy 系統層直接綁定**的具體 scene。每個 scene 拆成「人的動作 → OS 的反應 → 你看到的體驗」三層。

| # | Scene | 人的動作 | OS／agent 的反應 | 使用者體驗 |
|---|---|---|---|---|
| S1 | **首次使用任一家 coding agent** | 安裝完首次在終端敲 `claude`（或任一） | `~/.local/bin/` 內的 mise stub 偵測到首次執行 → 才實際下載對應 agent binary | 第一印象是「系統已經認識 agent」，不需要自己裝 runtime；下次即瞬間啟動 |
| S2 | **一鍵拉起 default agent** | 按 `Super+Shift+Ctrl+A` | `omarchy-launch-tui` 開固定 app-id 視窗載入 default agent（未設則開 picker） | 像按一個「打開 AI」的快捷鍵，而不是先想「我要開哪個終端再敲指令」 |
| S3 | **在任何 editor/終端內聯起 agent** | 按 `a`／`c`／`cx`／`cy` 內聯鍵 | `omarchy-agent` 以對應 agent 的旗標（`-p`/`--auto`/`--permission-mode auto` 等）在目前工作目錄啟動 | agent 以「無停問（auto-approve）」模式直接開工；從 `$HOME` 啟動會自動切到 `~/Work` |
| S4 | **隨時看各家 agent 用量** | 瞄一眼頂部 bar 的 agents panel | 3 個 collector（claude/codex/fireworks）每 15 分鐘寫 JSON 到 `~/.local/state/omarchy/agents/usage/`，panel watch 目錄即時刷新 | 一眼看到每家 plan、5 小時與週上限百分比、prepaid 餘額、token 使用 |
| S5 | **程式 crash 自動診斷** | 有 process crash → 收到「Process crashed」通知 → 點通知 | 監 `systemd-coredump` 抓到 pid/comm/signal → 打包給 default agent＋`diagnose-crash` skill 自動追根因 | crash 不是被動等使用者報，而是 OS 主動把 crash 丟給 agent 分析 |
| S6 | **切換桌面主題連帶 agent 一起換** | 切 Omarchy theme | 實際呼叫 `omarchy-theme-set-claude`／`-pi`／`omarchy-restart-opencode` 同步 agent 的視覺 | 桌面與 AI agent 的樣式是「一套」，不需各自設定 |
| S7 | **agent 能直接調用系統本身** | 對 agent 下指令調整 Omarchy 設定 | `Omarchy Skill` symlink 進各 agent 的 skill 目錄 → agent 呼叫 `omarchy-*` 指令改參數 | agent 不再只是「改你專案裡的 code」，能直接操作 OS 設定 |

#### 這些 scene 的共相

| 觀察 | 說明 |
|---|---|
| **啟動由 stub 延後** | 不做任何 agent 但系統內建整套 stub，首次用到才下載 → 零安裝成本、選擇開放 |
| **操作介面＝快捷鍵＋面板** | agent 從「重terminal 副程式」升格為「被桌面 shell 直接繫結的一等物件」 |
| **狀態可視** | 用量、餘額、上限全部集中可視，不靠各自 CLI 慢慢查 |
| **事故自動化** | crash 由 OS 主動交棒給 agent；theme 變更自動連動 agent |
| **系統可被 agent 治理** | agent 透過 skill 能碰 `omarchy-*`，即「AI 對 OS 本身有 write access」 |

**結論**：「AI 為一等公民」＝ Omarchy 把 coding agent 從「使用者自己安裝的第三方工具」重新包裝成「OS 內建、可按快捷鍵、可看面板、可自動接管事故、可被 theme 綁定、可反過來調系統」的第七類桌面元件（等同檔案、視窗、bar、theme 的地位）。

### Q2：這些 scene 相比「在一般 Linux 上自己裝 claude-code」體驗差異在哪？

**？**

**A**：「自己裝 claude-code」與「Omarchy 內建 agent」的差異，不是「多裝了幾個指令」，而是**責任歸屬從使用者手上移到 OS 身上**。逐場景對照如下。

| 面向 | 一般 Linux ＋自己裝 claude-code | Omarchy 一等公民 | 差異的本質 |
|---|---|---|---|
| 安裝 | 手動 curl/brew 安裝、設 PATH、裝 runtime | 系統預置 stub，首次執行 lazy-load | 安裝從「使用前必做」變成「OS 已處理」 |
| 啟動 | 自己開 terminal → cd 到專案 → 打 `claude` | `Super+Shift+Ctrl+A` 或 `a`/`c` 直接內鍵 | 啟動從「一段 workflow」變成「一個快捷鍵」 |
| 授權 | 各自 CLI 每次詢問是否批准指令 | auto-approve 旗標（`--auto` 等）預設跑 | 人不再逐問，信任邊界交給 agent 的 verify 機制 |
| 工作目錄 | 自己 `cd` 到正確路徑 | 從 `$HOME` 啟動自動切 `~/Work` | 減少「開錯目錄」的上下文錯誤 |
| 用量可視 | 分別登各 console 查 | 單一面板（plan/上限/餘額/token） | 集中化監看 |
| crash 處理 | 看到 core dump / 錯 log，自己動手追 | OS 收事故 → 交 default agent 自動診斷 | 從「被動診斷」到「主動接棒」 |
| 環境變動（theme） | agent 樣式與桌面無關、各自設定 | 切 theme 自動同步 agent | 系統與 agent 樣式綁定 |
| agent 能管系統 | 不行，agent 只碰專案檔 | agent 有 Omarchy skill 可調 OS 參數 | agent 信任邊界從「檔案層」擴到「系統層」 |

**反證表（這些差異未必都是好處）**：

| Omarchy 做法 | 可能付出的代價 |
|---|---|
| auto-approve 預設跑 | 權限過大；若沒有對應的 verify harness，錯誤的影響範圍比「每次確認」大 |
| crash 自動丟給 agent | agent 需要憑據才能碰 coredump，且預設 agent 要事先設定、品質因設而定 |
| theme→agent 同步 | 只綁定它能同步的 agent（claude/pi/opencode），非對應者不在此列 |
| stub lazy-load | 首次執行需連網下載，斷網環境不能開箱即用 |
| 綁定整套主見 | 換 agent 或不用 Omarchy 的整合時，這些機制全部失效 |

**結論**：差異核心是**「OS 把 agent 當內建元件收編，還是當外部程式各自裝」**。Omarchy 把安裝、啟動、授權、監視、crash、theme、系統治理七個環節全數 OS 化；代價是這些便利綁死在 Omarchy 的整合預設與 agent 選項上，離開 Omarchy 就全數失效。以使用者的第二大腦準則看，這不是「OS 級遷移」的理由，而是「抽取這套收編機制設計」的素材。

---

## 結語

Omarchy 的解法特徵是：把「一個權威使用者的整套打磨桌面」打包成**可安裝、可持續更新、可回退**的發行版，用 `system/user` 分離避免個人化被更新踩掉，並把 AI coding agent 當成第一公民整合進去。它解決「Linux 桌面開箱即用」的門檻，但代價是接受 DHH 的既有主見與 `alpha` 狀態；對照使用者第二大腦，這是一個「抽取其整合設計、而非整機採用」的標的。
