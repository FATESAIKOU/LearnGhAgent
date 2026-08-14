# Okdo ROCK 3 C Model C 1GB 單板電腦（RS112-D1W2P1）

> 調研標的：RS Components 日本站商品「Okdo ROCK 3 C Model C 1GB シングルボードコンピュータ」RS112-D1W2P1（RS品番 249-3157）。
> 本報告以 Radxa 官方產品頁與 docs 為一手規格來源，RS 商品頁作為型號／售價佐證。

---

## 1. 這個技術解決什麼問題？

**一句話**：這塊板子解決「在沒有整機 PC 的場景下，以低功耗、低成本、手掌大小的板卡形式，跑一個完整 Linux／Android 系統來控制或驅動電子裝置」的問題——也就是通用單板電腦（SBC, Single-Board Computer）的核心命題。

它被解決的具體問題可拆成三層：

| 層 | 被解決的問題 |
|---|---|
| 硬體層 | 需要一個具備 CPU／GPU／RAM／儲存／網路／顯示／GPIO 的完整計算機，但不想要一台桌上型主機的體積、功耗與成本 |
| 介面層 | 需要直接控制外部電子元件（GPIO 電壓腳位、I2C/SPI/UART、MIPI CSI/DSI 攝影機與顯示、USB 外接）的能力，這是普通 PC 難以做到的 |
| 開發層 | 需要一個可被重刷、可被燒錄韌體、硬體規格公開的實驗平台，讓開發者與 maker 反覆試錯而不用承擔整機損壞的風險 |

**使用者原始問題的定位**：使用者自述用過 Raspberry Pi（樹莓派）與 NVIDIA 開發板，但不知道「這啥能幹嘛」。就本板而言，它的定位是 **「低成本、通用、Linux 可跑的入門級 SBC」**——與樹莓派 3B/4 屬同級定位，不具備 NVIDIA 開發板那類專注於 AI 算力的特色。

**規格總覽（Radxa 官方，V1.4）**：

| 項目 | 規格 |
|---|---|
| SoC | Rockchip RK3566（四核 Cortex-A55 至 1.6GHz） |
| GPU | Mali-G52-2EE |
| RAM | LPDDR4（本商品 1GB；系列另有 2GB／4GB） |
| 儲存 | eMMC 模組＋microSD |
| 顯示 | 1080P@60 HDMI、2-lane MIPI DSI |
| 網路 | Gigabit Ethernet（支援 PoE HAT）＋ WiFi 6／BT 5.4（V1.4） |
| I/O | USB 2.0 OTG×1、USB 2.0 Host×2、USB 3.0 Host×1、2-lane MIPI CSI×1、40-pin GPIO、3.5mm 麥克風孔 |
| 電源 | 5V／2A |
| 尺寸 | 85×56mm（接近樹莓派 3B 尺寸） |
| OS | Linux（Radxa OS 基於 Debian）、Android |

**模糊之處**：官方列出的應用情境（HMI、機器人、智慧家庭、販賣機）是「可能用途」而非「獨佔用途」——它本質上是通用運算平台，能做的事取決於接上什麼周邊與寫什麼軟體，不是由板子本身限定。「能幹嘛」的答案不在此板，而在使用者的應用需求。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章中明確提到的背景

RS 商品頁本身提供的背景有限，僅說明這是「ROCK シングルボードコンピュータ」系列的一員，品牌掛「Okdo」，OS 支援 Linux／Android。這些是行銷資訊，不含技術成因。

### 2.2 通用技術背景（此為報告補上的一般知識，非文章內容）

**為什麼會有「SBC 這個產品類別」**：

- **成本與功耗的剪刀差**：桌上型／筆電的整機成本、功耗、體積，對「只要跑一個嵌入式 Linux 服務或控制一堆 GPIO」的場景而言過高。SBC 把 SoC、RAM、儲存、I/O 整合到單一板卡，把單點成本壓到整機的十分之一以下。
- **嵌入式開發的痛點**：傳統 MCU（如 Arduino）運算與記憶體極有限、只能跑即時韌體，撐不起 Linux 核心與使用者態生態。需要一個「比 MCU 強、比整機便宜」的中間層——SBC 就是這個中間層。
- **Raspberry Pi 開啟的生態**：樹莓派以降，SBC 從「開發者玩具」變成「Linux 學習＋物聯網＋邊緣控制的標準載體」。它降低了「碰 Linux 內核與硬體介面」的門檻，使得 40-pin GPIO＋可重刷韌體成為這個類別的隱性標準。
- **SoC 供應鏈的成熟**：瑞芯微（Rockchip）等廠商推出 RK3566 這類「中低階但功能齊全」的應用處理器，內建 Mali GPU、多媒體編解碼、網路與顯示控制器，讓板卡廠能一顆晶片拼出完整 SBC，價格低到可作為教育與 prototype 用途。
- **品牌脈絡（為何叫「Okdo ROCK 3C」）**：Radxa 是原廠品牌；OKdo 是 RS Components 旗下的 maker 自有品牌。兩者 co-brand 銷售同一塊 Radxa ROCK 3C 板，商品名掛 Okdo、硬體實為 Radxa 設計——使用者貼的並非獨立第三家廠商設計。

**RK3566 的定位**：屬瑞芯微中低階應用處理器，定位與樹莓派 Pi 3／Pi 4 相仿，通用運算與多媒體有餘，**沒有特別強調的 NPU／AI 加速**——這點與 NVIDIA 開發板有本質差異。

---

## 3. 這個技術是如何解決該問題的？

核心機制是「**把一台完整電腦的組成元件整合到單一板卡，並透過標準化的接腳與介面把控制能力開放出來**」。具體拆解：

```
┌───────────────────────────────────────────────────────────┐
│  Radxa ROCK 3 C（單一板卡）                                │
│                                                           │
│  SoC Rockchip RK3566（CPU + GPU + 多媒體 + 網路控制器）     │
│    └─ LPDDR4 RAM（1/2/4GB）                                │
│    └─ 儲存：eMMC 模組 + microSD                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 開放介面層                                          │   │
│  │  40-pin GPIO（I2C/SPI/UART/PWM 等）                │   │
│  │  MIPI CSI ×1（攝影機） / MIPI DSI（顯示）          │   │
│  │  HDMI（1080P@60）                                  │   │
│  │  USB 2.0 OTG×1 + Host×2 + USB 3.0 Host×1          │   │
│  │  Gigabit Ethernet（+PoE HAT）+ WiFi/BT             │   │
│  └────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
        │ 可重刷 / 可燒錄
        ▼
   Linux（Radxa OS/Debian） / Android
```

**怎麼運作：**

1. **整合運算**：RK3566 一顆 SoC 同時提供 CPU（四核 Cortex-A55）、GPU（Mali-G52-2EE）與多媒體／網路控制，配合板上 LPDDR4 與 eMMC／microSD 儲存，構成完整可自舉的運算平台。
2. **開放控制面**：40-pin GPIO 把 CPU 的電壓接腳與 I2C／SPI／UART／PWM 等匯流排拉出到使用者端，讓板卡直接驅動感測器、馬達、LED、外接螢幕——這是「控制外部世界」的實體管道。
3. **標準 OS 載體**：官方提供基於 Debian 的 Radxa OS 與 Android，意味著使用者態的 Linux 生態（套件管理、既有應用）可直接運行，不必像 MCU 那樣從裸機韌體起手。
4. **可重刷性**：系統寫在 microSD／eMMC，可反覆重刷映像檔，開發試錯不需更換硬體——這降低了實驗的不可逆風險。
5. **供電簡化**：僅需 5V／2A 電源（USB 供電等級），相較整機大幅簡化部署。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

此處先對照第二大腦 FATESAIKOU/MyBrain 的既有評估：**第二大腦的「技術／技術評估」與「專案／下一步清單」中，沒有任何關於 SBC／開發板／樹莓派／Jetson／Rockchip 硬體的評估或專案**（grep「樹莓／raspberry／jetson／開發板／sbc／rockchip／rock／單板／邊緣」零命中）。與本標的相關的既有判定只有兩筆，均為軟體性質：

| 既有判定 | 內容 | 信任層級 | URL |
|---|---|---|---|
| [nvidia cosmos](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/nvidia%20cosmos.md) | 判定 **不採用**，理由是「方向有趣但很難使用，且他傾向自己兜 MVP 理解本質」——這是 NVIDIA 的**世界基礎模型（軟體）**，非開發板 | `generated.by: human:fatesaikou`，`status: stable`，首見 2026-06-20 | 見連結 |
| [AirLLM](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/AirLLM.md) | 判定 **不採用**，理由含「**沒硬體**」（低顯存運行大模型的工具） | 判定總表（`generated.by: ollama-cloud/deepseek-v4-flash`，`status: draft`，**AI 草稿未經本人 review**） | 見連結 |

**與此標的相關的第二大腦判準**（見[技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md)，`draft`，2026-08-01）：他的技術採用與否最強判準是「**能不能影響個人的日常 workflow**」，且「理解優先」原則主張「不夠穩定或不熟悉就先自己兜，MVP 是理解的驗證點」。

**R2 追加查詢的既有判定（直接錨定本輪「AI agent 工作區＋硬體」意圖）：**

| 既有判定 | 內容 | 信任層級 | 與本輪結論的關係 |
|---|---|---|---|
| [OpenCode](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OpenCode.md) | 判定**試用**，「大致堪用 並且由於 Ollama 帶來極大自由度 避免綁定」；本人已實測開 opencode 配 Ollama | `generated.by: human:fatesaikou`，`status: stable`，2026-05-01 | **支援本輪結論**：opencode 靠 OllamaCloud／雲端推論、板子只當 CLI 客戶端，與「不綁定、雲端推論」一致 |
| [Openship](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Openship.md) | 判定 **Reject**，原話「目前只有一台低價 VPS 且沒打算在上面跑服務」，導入控制平面過重 | `generated.by: opencode/deepseek-v4-pro`，`human:fatesaikou` 2026-08-09 `verified`，`status: stable`，2026-07-26 | **與本輪需求潛在衝突**：他想自架常駐 agent，卻又曾明言「不打算開服務」；此衝突必須並陳 |
| [terminal-browser](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/terminal-browser.md) | 判定 **Reject**，最終目標是「**脫離終端機，在手機／GAS 上調用 code agent**」；mini-PC／固定桌面機是反方向 | `generated.by: claude-code/opus-5`，`status: draft`（**AI 草稿未經本人 review**），2026-08-01 | **與「微型電腦＋跑瀏覽器」需求潛在衝突**：他的長期方向是往手機／GAS 調用，不是固定一台桌面機 |
| [個人 AiAgent 入口](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/靈感/個人%20AiAgent%20入口.md) | 整個新專案卡在同一個未決問題「**執行環境：GAS vs 自架伺服器跑 opencode**」；已併入「下一步清單」待判定 | `generated.by: claude-code/opus-5`，`status: draft`（**AI 草稿，來源含本人 2026-08-11 登錄 ToDo**） | **本輪 R2 問題 2／3 正是把「自架」側具體化到硬體**，直擊這個未決判定 |

據此：**第二大腦對 ROCK 3C／樹莓派／Jetson／N100 mini-PC／任何 SBC 硬體皆無評估或專案紀錄**（grep 零命中），硬體軸是空白；但與「用這台硬體開 AI agent 工作區」直接相關的軟體判定則高度相關——`OpenCode` 支援、`Openship`「不開服務」立場衝突、`terminal-browser`「脫離終端機往手機」方向衝突、`個人 AiAgent 入口`「執行環境未決」直擊。本節將這些既有判定寫入，**不編造他對硬體的個人結論**。

**同級替代方案與切入點差異（DA 表）**：

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **樹莓派 Raspberry Pi（3B/4/5）** | 最成熟 SBC 生態，社群與文件最豐、OS（Raspberry Pi OS）支援最好 | 使用者已熟（自述用過）；需要最高社群支援度與相容性 | 價格較同級 RK 板高、部分型號供貨不穩 | 開發體驗最順、踩雷最少，標準 Linux 教育與 prototype 載體 |
| **NVIDIA Jetson 系列** | 內建 CUDA GPU／專用 AI 加速，主打邊緣端深度學習推理 | 需要邊緣 AI 推論算力、且接受較高功耗與單價 | 價格與功耗遠高於通用 SBC、非 AI 用途則效能過剩 | 在板端跑 CV／模型推理，不依賴雲端算力 |
| **其他 Rockchip RK 板（Orange Pi、Libre Computer 等）** | 與 ROCK 3C 同 SoC 家族，性價比與 GPIO 能力相近 | 需求與 ROCK 3C 相同但想貨比三家、或原廠缺貨 | 社群與文件密度較樹莓派低，踩坑要自己查 | 以相近預算達成同等通用 SBC 能力 |
| **x86 迷你 PC（N100 等）** | 以完整 x86 平台跑桌面 Linux／服務，原生相容性與效能更高 | 不需要 GPIO 直接控制、要跑常駐服務或桌面級應用 | 體積／功耗／價格均高於 SBC；失去 GPIO 直接控制能力 | 當輕量常駐伺服器或桌面機，相容性最好 |

**切入點差異總結**：解決「低功耗單板運算＋外接控制」的同類切入點分三軸——(a) **生態成熟度**（樹莓派最強）、(b) **AI 算力**（Jetson 專精）、(c) **性價比與開放規格**（ROCK 3C 與其他 RK 板）。ROCK 3C 落在 (c) 軸，與使用者熟悉的樹莓派（a）與 NVIDIA 板（b）在定位上各有不同偏重。

> 註：上述替代方案的比較屬報告的一般技術知識。第二大腦中**沒有**對樹莓派、Jetson、其他 RK 板的個人評估紀錄，故本節不引用任何他的舊結論，也不將其陳述為他已拍板過的決定。

---

## 5. User Q&A

### Q1：比起樹莓派，ROCK 3C 的優勢是「便宜＋雖不好開發但效能夠」嗎？

**A**：這個拆解有一半成立、一半不精確。「便宜」成立，但「不好開發」與「效能夠」兩個用語都需要校正。

| 宣稱 | 判定 | 理由 |
|---|---|---|
| 便宜 | ✅ 大方向成立 | RS 未稅 ¥7,835，屬入門級定價；但同級樹莓派（Pi 4 2GB 約 ¥6,000 級）價格差異不大，「便宜」優勢並非碾壓性，而是**同等入門定位** |
| 不好開發 | ⚠️ 不精確 | RK3566 有官方 Radxa OS（基於 Debian），**Linux 開發流程與樹莓派同質**（刷映像→SSH→套件管理）。差異在「**社群與文件的密度**」，不是「不能開發」；踩雷要自己查、範例較少，但開發入口一致 |
| 效能夠 | ⚠️ 需定義「夠」 | 指**通用運算／多媒體**（四核 A55 1.6GHz、1080P@60）夠用，**不是 AI 算力**——本板無 NPU 強調，與 NVIDIA 板在 AI 推論上是兩類東西 |

**關鍵校正**：你對標的「效能夠」若是指**跑 AI agent**，那效能瓶頸不在這塊板子——推論在雲端（OllamaCloud／Claude），板子只當 CLI 客戶端，瓶頸是 **1GB RAM 的多工承載**，不是 CPU 算力。

**與第二大腦對照**：第二大腦無任何樹莓派／ROCK 的個人評估，故無舊結論可比。ROCK 3C 相對樹莓派的差異是「社群成熟度」而非「能否開發」。

**結論**：ROCK 3C 相對樹莓派的正確優勢表述是「**同等的入門 Linux 定位＋相對低的價格**」，代價是「社群與文件較少、踩坑成本高」；「不好開發」應改寫為「社群支援少」，「效能夠」應限定為「通用運算夠，非 AI 算力」——你的假設方向對，但用詞需校正。

---

### Q2：我想用 OllamaCloud／Claude 搭配 opencode／claudecode 開常駐 agent 做事，ROCK 3C 合適嗎？

**A**：分工上「合適」，因為**推論不在本板**；但「1GB RAM 開常駐 agent」這題**不合適**，會被 RAM 掐死。

```
你設想的架構：
OllamaCloud / Claude（雲端推論，重算在遠端）
        ▲ API key / 網路
        │
   ROCK 3C（只當 CLI 客戶端，跑 opencode/claudecode 進程 + Node runtime）
```

**分工判定**：opencode 官方 docs 明示不帶本地模型、靠 provider API keys 連 LLM。所以這塊板子**不需要本地推論能力、不需要 NPU**，只需能跑 CLI agent 進程＋終端＋網路。**就分工而言任何一台能跑 Linux 的機器都行**，算力不是問題。

**但 RAM 是硬瓶頸**：

| 負載 | 1GB（本商品） | 系列 2GB／4GB |
|---|---|---|
| 1 個常駐 opencode agent（opencode 進程＋Node runtime＋git 工作樹） | 勉強，接近記憶體上限 | 可行 |
| 2–3 個常駐 agent（你要的） | **極緊，必然 swap 到儲存**，agent 回應延遲暴增 | 2GB 仍緊、4GB 較可行 |
| 瀏覽器（問題 3 需求） | **不可行** | 2GB 緊、4GB 勉強單分頁 |

**與第二大腦對照**：
- [OpenCode](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OpenCode.md) 已判定**試用**，「大致堪用 並且由於 Ollama 帶來極大自由度」（`human: stable`，2026-05-01）——軟體側你已驗證可行。
- 但[Openship](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Openship.md) 你判定 **Reject**，原話「目前只有一台低價 VPS 且沒打算在上面跑服務」（`human verified: stable`）——**與你現在「自架常駐 agent 硬體」的意圖直接衝突**，這點必須並陳。

**結論**：架構上 ROCK 3C 可當客戶端（雲端推論），但 **1GB 版開 2–3 個常駐 agent 不成立**，要選至少 4GB 才談得上多 agent；且此意圖與你第二大腦「Openship 不開服務」的既有判定衝突，須先解決「你到底要不要自架」這個未決題。

---

### Q3：還是微型電腦比較適合？預算 <3 萬日幣、開 2–3 個 agent、甚至跑瀏覽器。

**A**：**是的，就你這三項需求（2–3 agent＋瀏覽器＋<3 萬日幣），N100 級 x86 mini-PC 比 ROCK 3C 更貼合。**

| 需求 | ROCK 3C（1GB 版） | x86 mini-PC（N100、8GB RAM） |
|---|---|---|
| 2–3 常駐 agent | ❌ 1GB 必 swap | ✅ 8GB 可分 2–3 進程 |
| 跑瀏覽器 | ❌ 幾乎不可行 | ✅ x86 原生 Chrome／Node |
| 預算 <3 萬日幣 | ✅ 約 ¥7,835（未稅） | ✅ N100 8GB 機多落在 ¥15,000–¥25,000，仍在預算內 |
| 原生相容性 | ⚠️ ARM 生態，原生 binary 需有 ARM 版 | ✅ x86 原生，相容性最高 |
| 代價 | GPIO／嵌入式彈性 | 體積較大、功耗較高、失去 GPIO 直接控制 |

**核心取捨**：你要的「開多個 agent＋跑瀏覽器」是**桌面／伺服器級負載**，不是嵌入式 GPIO 控制場景。ROCK 3C 的價值在「低成本＋40-pin GPIO 控制外部元件」，而你的需求完全用不到 GPIO——這讓 ROCK 3C 的核心優勢落空。

**與第二大腦對照（方向衝突必須指出）**：
- [terminal-browser](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/terminal-browser.md) 你判定 **Reject**（`draft`，AI 草稿），原話「最終目標是**脫離終端機**，能在**手機／GAS**上調用 code agent」。**「固定一台微型電腦跑瀏覽器＋常駐 agent」與「脫離終端機、往手機／GAS 走」的長期方向相反**——這是你第二大腦裡最實質的方向衝突，必須先對齊。
- [個人 AiAgent 入口](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/靈感/個人%20AiAgent%20入口.md)（`draft`）：整個專案卡在「**執行環境：GAS vs 自架伺服器跑 opencode**」未決，且該檔明列自架側疑慮「先前判 Openship 時明講『我用 VPS 不是為了開服務』」。你的問題 3 正是把「自架」側落到一台硬體上。

**結論**：若你堅持「2–3 agent＋瀏覽器＋<3 萬日幣」，**x86 mini-PC（N100、8GB）是更貼合載體**，ROCK 3C 1GB 版不適合；但在花錢前，要先解決第二大腦已標記的兩個衝突——「自架 vs 不開服務（Openship）」與「固定桌面機 vs 脫離終端機往手機（terminal-browser）」——否則這台機器買下去會與你既定的方向打架。

---

## 附錄：資料來源與信任層級

| 來源 | 性質 | 信任層級 |
|---|---|---|
| [Radxa ROCK 3C 官方產品頁](https://radxa.com/products/rock3/3c/) | 一手規格（定位、SoC、RAM、無線） | 一手權威來源 |
| [Radxa docs ROCK 3C](https://docs.radxa.com/en/rock3/rock3c/) | 一手規格（Features 表：CPU/GPU/儲存/連接埠/尺寸/電源） | 一手權威來源 |
| RS Components 日本站商品頁 | 使用者貼的轉售頁（型號 RS112-D1W2P1、售價約 ¥7,835 未稅） | 二手轉售資訊，僅作型號與售價佐證 |
| RK3566 定位 | 報告補上的通用技術背景 | 一般知識 |
| Okdo×Radxa co-brand 關係 | 報告補上的品牌背景 | 一般知識 |

**第二大腦查詢結果**：FATESAIKOU/MyBrain 對 SBC／開發板／微型電腦／本板**無任何硬體評估或專案紀錄**。與本標的相關既有判定分兩層：(a) 硬體側全部空白（樹莓派／Jetson／ROCK／N100 皆未評估）；(b) 與「用硬體開 AI agent 工作區」意圖直接相關的軟體判定——`OpenCode`（試用，支援）、`Openship`（Reject，不開服務，與自架衝突）、`terminal-browser`（Reject，脫離終端機往手機，與固定桌面機衝突）、`個人 AiAgent 入口`（執行環境未決，直擊）。均已在上方 §4 與 §5 標註 URL 與信任層級；未命中的主題在此明示不存在，不編造為他的硬體結論。
