# ArtCraft 技術分析報告

> 調研標的：`storytold/artcraft`（自稱「The IDE for artists.」）
> 來源：GitHub 一周熱點 135 期（https://youtu.be/n8jL89H5d-c ）；該影片無字幕軌，逐字稿取不到，影片觀點未納入本報告（先例：133 期 Paperclip 同樣處理）
> 實查：GitHub API＋repo 文件＋官網（2026-10-17）；第二大腦鏡像 @`ac9eaa2`（2026-10-17）

---

## 1. 這個技術解決什麼問題？

### 1.1 被解決的具體問題

ArtCraft 針對的問題可收斂為一句：**「純文字提示（text prompt）不足以讓創作者精確控制生成式 AI 的構圖、角色一致性與鏡頭擺位，導致生成結果不可控、不可重現。」**

其官方敘事為「Turn prompting into *crafting*」——把「輸入提示、等待隨機結果」改成「先在場景中把畫面搭好，再讓模型渲染」。

| 面向 | 純提示（prompt-only）的處境 | ArtCraft 主張的處境 |
|---|---|---|
| 構圖 | 靠文字描述，結果由模型統計分布決定 | 在 2D 畫布／3D 場景中自行擺位 |
| 角色一致性 | 每張圖重新描述，身分漂移 | 以 mannequin 擺姿＋身分轉移固定 |
| 鏡頭擺位 | 文字難以指定 | 3D 場景中直接設定相機 |
| 可重現性 | 換一次取樣就變 | 場景檔案可保存、可重複渲染 |

### 1.2 問題陳述中模糊之處

| 模糊點 | 說明 |
|---|---|
| 「IDE」的類比 | 官網與 README 以「IDE for artists」定位，但實際產出是「可組合場景的生成工作台」，與程式設計 IDE 的「編輯—編譯—除錯」迴圈並不同構；IDE 一詞為行銷定位，非技術定義。 |
| 「開源」的邊界 | repo 為桌面端；後端生成服務、官網在**另一個未公開的** `artcraft-services` repo（`AGENTS.md` 明載）。官網稱「The whole studio is on GitHub」，實際上「產生結果」的那一段不在 GitHub。 |
| 「無中間人」 | 官網稱「No aggregator middleman」，但生成請求仍經 `api.storyteller.ai`（ArtCraft 自家服務）轉發；`ROADMAP.md` 的架構目標即為「Remove dependence on ArtCraft hosted services」，等於承認目前仍依賴自家中間層。 |

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 問題的技術根源

| 背景層次 | 內容 | 來源性質 |
|---|---|---|
| 生成模型的介面 | 擴散／自迴歸生成模型的輸出是提示的機率分布取樣；提示是一條有損（lossy）控制通道，無法表達空間關係、遮擋、相機參數 | 通用技術背景 |
| 控制手段的演進 | 業界先後出現 inpainting、ControlNet（姿態／深度／邊緣條件）、IP-Adapter（身分參考）等「以圖控制圖」的機制；ArtCraft 把這些能力包成場景工具 | 通用技術背景＋README 功能對照 |
| 工具鏈斷裂 | 生圖與生影工具多為網頁表單，輸入是文字、輸出是檔案，中間沒有可保存的「場景」物件 | 通用技術背景 |

### 2.2 問題的歷史與組織背景（實查）

| 面向 | 實查值 |
|---|---|
| repo 建立 | 2022-03-31 |
| 最後 push | 2026-10-15（高活躍） |
| stars／forks | 30,870★／4,907 fork |
| License | Apache-2.0（README 載明 MIT 或 Apache-2.0 雙授權） |
| 主要語言 | Rust 9.97 MB、TypeScript 6.60 MB、JavaScript/Python/CSS/Shell 等 |
| 最新 release | v0.41.0（2026-09-26），約每月一版 |
| open issues | 437 |
| 團隊同源 | org `storytold`；API 網域 `api.storyteller.ai`、CDN `cdn-2.fakeyou.com` 指向同團隊的 FakeYou／Storyteller.ai；官網聯絡信箱 `hello@storyteller.ai`、X handle `get_artcraft` |
| 更名史 | 由 storyteller.ai 更名為 ArtCraft（`AGENTS.md`、`artcraft-native/README.md` 與網域交叉指向） |

| 來自 ROADMAP.md 的自述目標 | 類型 |
|---|---|
| Make ArtCraft better than model aggregation websites（#1 goal） | 產品定位 |
| Add every model and provider into ArtCraft | 產品範圍 |
| Remove dependence on ArtCraft hosted services | 架構 |
| More Rust, more speed | 架構 |
| Build an *Open* OpenAI / Google / Anthropic | 長期願景 |

---

## 3. 這個技術是如何解決該問題的？

### 3.0 系統全貌（架構圖）

```
┌───────────────────────────────────────────────────────────────┐
│                    桌面 App（兩種實作，二選一）                 │
│  A. Tauri：Rust core + WebView（React / Vite / Zustand / Three.js）│
│  B. artcraft-native：純 Rust egui（無 Tauri、無 JS）             │
│  default member = Tauri app；native 為並行技術路線               │
└───────────────┬───────────────────────────────────────────────┘
                │  artcraft_client（typed）＋ ident headers
                ▼
┌───────────────────────────────────────────────────────────────┐
│  artcraft_router：provider 抽象層                              │
│   Artcraft｜Fal｜GMICloud｜Grok｜Midjourney｜OpenAI Sora｜      │
│   WorldLabs｜KinoviWeb                                         │
└───────────────┬───────────────────────────────────────────────┘
                │  OmniGen（能力由伺服器下發）
                ▼
┌───────────────────────────────────────────────────────────────┐
│  /v1/omni_gen/{models,cost,generate}/{image,video,audio}       │
│  → api.storyteller.ai（ArtCraft hosted services）              │
└───────────────┬───────────────────────────────────────────────┘
                │
                ▼
       62 模型目錄（伺服器端定義）
```

### 3.1 核心機制一：把「場景」變成生成的前置物件

| 機制 | 做法 | 對應 README 功能 |
|---|---|---|
| 2D 合成 | 圖層、去背、繪圖工具組成畫面 | 2D Image Compositing、Canvas Image Editing |
| 3D 合成 | 背景／前景／道具分層，建立有深度的構圖 | 3D Image Compositing |
| Image to Location | 把虛擬演員放進固定環境，同一房間拍多顆鏡頭 | Image to Location |
| Image to 3D Mesh | 圖片轉可擺位／旋轉／取景的 3D 物件 | Image to 3D Mesh |
| Character Posing | 生成前先擺姿、定相機 | Character Posing |
| Character Identity Transfer | 以擺姿 mannequin 引導角色身分與姿態 | Character Identity Transfer |
| Kitbashing | 組合 3D 資產套件控制相機角度、物件位置、景深 | Scene Blocking with Kitbashing |
| Mixed Asset Crafting | 在同一畫布混用圖片裁切、world、3D mesh | Mixed Asset Crafting |

### 3.2 核心機制二：模型／供應商路由

| 層次 | 做法 |
|---|---|
| 能力下發 | 模型與選項由伺服器端 OmniGen listings 下發，App 不需更新即可出現新模型 |
| 路由層 | `artcraft_router` crate 抽象多供應商；圖片可另走 Midjourney（自有帳號）或 fal（自有 API key），影片一律走 ArtCraft |
| 目錄 | 62 模型：圖 16／影 25／音 5／3D mesh 11／world＋splat 5（實查 README 目錄） |
| 程式化入口 | Omni API：`Authorization` 以 `artcraft_api_…` API key 認證；URL 輸入由伺服器下載並存成 media token；影片端點 `POST /v1/omni_api/generate/video` |

### 3.3 核心機制三：桌面端工程架構

| 模組 | 職責（native README 實查） |
|---|---|
| `backend` | Tokio runtime 與所有 API 呼叫，結果以 Event 回傳 UI |
| `backend::wire` | 寬鬆解碼（lenient decode），新伺服器 enum 值不會弄壞解碼 |
| `backend::media_cache` | 縮圖／預覽下載、解碼、未用則逐出 |
| `backend::providers` | Midjourney／fal 帳號、提交、worker 完成後入庫 |
| `models` | 來自 OmniGen listings 的模型目錄 |
| `prompt_box` | 共用提示框：編輯器、reference deck、keyframes、model selector |
| `feed` | 生成佇列：running／failed／finished、library 分頁 |
| `crates/schema/database/sqlite_tasks` | SQLite 任務持久化（sqlx） |

| 工程成熟度訊號 | 實查 |
|---|---|
| CI／測試 | `cargo test -p artcraft_native`；egui_kittest 無頭 UI 測試；前後端 dev launcher 有 node --test |
| 效能報告 | `docs/performance.md`（含裝置實測記錄） |
| 雙桌面實作 | Tauri（Rust+JS）與 native（純 Rust egui）並行，共用 `artcraft_client` |
| 建置腳本 | `script/artcraft/unix_dev.sh`（Vite 自動選埠、Tauri IPC） |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 DA 表（同級或替代方案）

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **ArtCraft（本標的）** | 在 2D／3D 場景中先搭好構圖、身分、鏡頭，再以 OmniGen 目錄模型渲染；桌面 App＋多供應商路由 | 需 ArtCraft 帳號與其 hosted services（生成不離線）；3D／合成需一定創作工具手感 | 後端未開源、生成依賴自家中間層；學習曲線為場景編輯器而非 prompt；62 模型目錄價值綁在伺服器 | 對構圖／一致性／鏡頭有可保存、可重現的控制；不鎖單一模型供應商 |
| **ComfyUI（節點圖本地管線）** | 以 node graph 把模型、ControlNet、IP-Adapter、inpaint 串成可重跑的生成管線 | 自備 GPU 與模型權重；懂節點接線 | 組裝與維護成本高；不是「畫布」，是資料流；生態破碎 | 完全本地、完全可重現；控制粒度最細 |
| **聚合網站（Midjourney web／OpenArt／Freepik）** | 訂閱制網頁，prompt-in、圖／影 out，跨模型代管 | 訂閱費用；素材上雲 | 素材離機（隱私）；被平台綁定；無可保存場景 | 上手最快、模型最齊、無需安裝 |
| **垂直 SaaS 創作套件（Runway／Pika／Krea）** | 針對單一創作動作（生成、編輯、放大、動態）做精緻網頁工具 | 訂閱；雲端處理 | 工具碎片化、資產散落；控制以既有模板為主 | 單點體驗成熟、迭代快 |
| **DCC＋AI 外掛（Photoshop＋Firefly／Blender＋add-ons）** | 把 AI 生成／inpaint／材質當外掛塞進既有專業工具 | 已熟悉該 DCC；付費授權 | 外掛與宿主版本耦合；AI 能力非核心 | 沿用既有專業流程，不換工具 |

### 4.2 各方案的切入點差異

| 切入軸 | ArtCraft | ComfyUI | 聚合網站 | 垂直 SaaS | DCC＋外掛 |
|---|---|---|---|---|---|
| 控制物件 | 場景（2D/3D） | 管線（node graph） | 提示（prompt） | 單一任務 | 圖層／mesh |
| 執行位置 | 桌面＋自家雲 | 本地 GPU | 雲 | 雲 | 本地 |
| 可重現性 | 場景檔 | 管線圖 | 低 | 低 | 專案檔 |
| 模型自由度 | 路由 62 模型 | 自裝任意 | 平台決定 | 平台決定 | 外掛決定 |
| 開源程度 | 桌面開源、後端閉源 | 開源 | 閉源 | 閉源 | 宿主閉源 |

### 4.3 對照第二大腦（FATESAIKOU/MyBrain，鏡像 @`ac9eaa2`）

> 先聲明：本輪查詢前，ArtCraft 在第二大腦**零命中**（`artcraft`／`storytold`／`AI IDE`／`crafting` 皆無既有評估）。以下為「同域或同軸」的既有判定，非對 ArtCraft 的預判。

#### 4.3.1 他的取捨準則（骨幹 tag；皆為 AI 草稿、未經他 review）

| 準則檔 | 信任層級 | 內容要點 | 與 ArtCraft 的關係 |
|---|---|---|---|
| [技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%BD%E8%B1%A1%E7%90%86%E8%A7%A3/%E6%9C%AC%E8%B3%AA%E6%B4%9E%E5%AF%9F/%E6%8A%80%E8%A1%93%E5%8F%96%E6%8D%A8%E6%BA%96%E5%89%87.md) | `claude-code/opus-5`／`draft`（AI 草稿，未經他 review） | ①理解優先——不穩定或不熟就先自己兜；②MVP→Feature 唯一閘門＝**能否影響個人 workflow**；③不要只用技術優劣評估工具；④agent 信任邊界放 harness 不放權限 | ArtCraft 之於他：不熟創作工具、無創作類 workflow → 依②③**難通過 workflow 閘門** |
| [不做清單](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%BD%E8%B1%A1%E7%90%86%E8%A7%A3/%E5%83%B9%E5%80%BC%E8%A7%80/%E4%B8%8D%E5%81%9A%E6%B8%85%E5%96%AE.md) | `claude-code/opus-5`／`draft`（AI 草稿） | 技術層幾乎無硬拒絕；閉源／無 license 只是採用障礙、非價值否定 | ArtCraft 後端閉源**不構成**價值否定，僅為採用障礙 |
| [下一步清單](https://github.com/FATESAIKOU/MyBrain/blob/main/%E5%B0%88%E6%A1%88/%E4%B8%8B%E4%B8%80%E6%AD%A5%E6%B8%85%E5%96%AE.md) | `claude-code/opus-5`／`draft`（骨幹） | 可支配時間約 10～20 小時／週；新開一件事**必然取代既有某件事** | 清單與專案現況表中**無任何創作／藝術／設計類專案**，技術軸全在 agent 基礎設施 |

#### 4.3.2 同域（創作／設計軸）既有判定

| 標的 | 判定 | `generated.by` | `status` | 判決理由與 ArtCraft 的關係 |
|---|---|---|---|---|
| [OpenCut-AI](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/OpenCut-AI.md) | 不採用 | `human:fatesaikou` | `stable`（本人定稿） | 全棧自託管 AI 影片剪輯；「專為剪輯設計，他用不上，不符日常 workflow」→ 同屬「創作工具、他用不上」的模式 |
| [PhotoGIMP](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/PhotoGIMP.md) | 不採用 | `human:fatesaikou` | `stable`（本人定稿） | 「我根本兩個都不會用，進不了日常 workflow」→ 直接對應 §4.3.1 準則② |
| [Taste Skill](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/Taste%20Skill.md) | 不採用 | `human:fatesaikou` | `stable`（本人定稿） | 「過分偏向設計師，知識與經驗儲備不足以運用」→ 同樣是「設計軸、他自認儲備不足」 |
| [nvidia cosmos](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/nvidia%20cosmos.md) | 不採用 | `human:fatesaikou` | `stable`（本人定稿） | 世界基礎模型；「方向有趣但很難使用，且他傾向自己兜 MVP 理解本質」→ 對應準則① |
| [HyperFrames](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/HyperFrames.md) | **採用** | `human:fatesaikou` | `stable`（本人定稿） | HTML+CSS+animation 逐幀渲染為確定性 MP4；「免費、將確定性 HTML 轉影片有價值，比多模態更穩定且成本更低」→ **他在創作域接受的是「確定性管線」，非 GUI 創作台** |
| [OpenDesign](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/OpenDesign.md) | **採用** | `human:fatesaikou` | `stable`（本人定稿） | 讓 coding agent 以檔案化 skills／design systems 產出設計物；「Accept, 可以在 Local 嘗試」→ 接受的設計路徑是**agent 產出設計物**，非互動畫布 |
| [awesome-gpt-image-2](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/awesome-gpt-image-2.md) | 不採用 | `process:learn-gh-agent` | `draft`（自動流程產出，未經他 review） | 提示詞資源庫；「目前沒有大量生圖需求，有也會用更程式化的方式」→ 生圖需求本身不在他身上 |
| [video-use](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/video-use.md) | 不採用 | `ollama-cloud/deepseek-v4.1-flash` | `draft`（AI 草稿） | 逐字稿＋ffmpeg 剪輯；「影片剪輯我用不到」 |
| [gods-eye-view](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/gods-eye-view.md) | 試用 | `process:learn-gh-agent` | `draft`（未經他 review） | 3D 地球／多源資料融合；與 ArtCraft 同屬 3D+Three.js 域但問題域不同 |
| [img2threejs](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%97%A5%E8%AA%8C/2026-08-22.md)（日誌判定） | Reject | 日誌（`2026-08-22`） | 日誌記述 | 圖轉 3D；「目前無圖片轉 3D 需求」→ 與 ArtCraft 的 Image to 3D Mesh 同名機制，但他無此需求 |

#### 4.3.3 直接衝突點（對照最有價值處）

| # | 衝突 | 第二大腦來源 | 明寫衝突 |
|---|---|---|---|
| C1 | **ArtCraft 的「多供應商模型路由」正是他已整條放棄的方向** | [Switchyard](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/Switchyard.md)（`opencode/deepseek-v4-flash`／`draft`）、[OmniRoute](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/OmniRoute.md)（`opencode/deepseek-v4-pro`／`draft`）皆判不採用 | Switchyard 判詞：「整條 Model Router 線放棄——真正握有 GPU、能持續供給的只有個位數，為個位數做路由政策層，**抽象的成本高於它省下的切換成本**」。ArtCraft 的賣點之一為 `artcraft_router`＋62 模型目錄＋8 供應商聚合——在準則④③下，**此賣點對他是負值而非正值**。⚠️ 兩筆皆為 AI 草稿、未經他 review，但方向與準則一致 |
| C2 | **ArtCraft 是 GUI 創作台，與他對 GUI 殼的判斷相衝** | [munder-difflin](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/munder-difflin.md)（`process:learn-gh-agent`／`draft`）判不採用 | 判詞：「基於 GUI，而打算打造 AI Container/AI Company 但沒打算被限制 UI……還太早而且包太多」。ArtCraft 高度整合 2D／3D／生成／目錄於一 GUI；對照準則③（不要只用技術優劣評估）適用 |
| C3 | **他在創作域接受的是「確定性管線」與「agent 產出設計物」** | [HyperFrames](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/HyperFrames.md)（`human:fatesaikou`／`stable`，採用）、[OpenDesign](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%80%E8%A1%93/%E6%8A%80%E8%A1%93%E8%A9%95%E4%BC%B0/OpenDesign.md)（`human:fatesaikou`／`stable`，採用） | 他採用的是「可重現／確定性的渲染管線」與「agent 產出可編輯設計物」；ArtCraft 主打互動式 3D 畫布＋生成，切入點與其接受路徑不同（非衝突，而是路徑差異） |
| C4 | **創作類工具有穩定的不採用模式，但非價值否定** | OpenCut-AI、PhotoGIMP、Taste Skill、nvidia cosmos（皆 `human:fatesaikou`／`stable`）；[不做清單](https://github.com/FATESAIKOU/MyBrain/blob/main/%E6%8A%BD%E8%B1%A1%E7%90%86%E8%A7%A3/%E5%83%B9%E5%80%BC%E8%A7%80/%E4%B8%8D%E5%81%9A%E6%B8%85%E5%96%AE.md) | 五筆創作／設計軸判定中四筆「不採用」、一筆「採用」，理由一律落在「進不了我 workflow／我用不上／儲備不足」，非「技術不好」。`不做清單` 明示技術層幾乎無硬拒絕 |

#### 4.3.4 「可當作他本人定稿判斷」的範圍

> 以下清單為 `generated.by: human:fatesaikou` 且 `status: stable` 的檔案，方可直接視為他的結論：**OpenCut-AI、nvidia cosmos、Taste Skill、PhotoGIMP、HyperFrames、OpenDesign**。
> 其餘（awesome-gpt-image-2、video-use、Switchyard、OmniRoute、gods-eye-view、munder-difflin、Paperclip，以及骨幹準則三檔）皆為 `draft`，屬**未經他 review 的 AI 產出**，轉述時不可說成他的定稿。

### 4.4 反證與對照（採用／抽取／不納入）

| 對 ArtCraft 的三種處置 | 支持此處置的第二大腦證據 | 反對此處置的證據 |
|---|---|---|
| **採用（直接當工具用）** | 官網免費、無訂閱，契合他對「不被租用」的偏好；桌面開源可讀原始碼 | 無任何創作類專案在 `下一步清單`／專案現況表；他自認不懂設計工具（PhotoGIMP、Taste Skill）；時間僅 10～20 小時／週且新事必取代舊事 |
| **抽取（只借鏡機制、自建）** | ①「場景先於生成」的可控制性思路，對應 HyperFrames／img2threejs 的「確定性腳本＋模型只做判斷」token 效率設計；②`artcraft_router` 的 provider 抽象可作對照（但他已放棄路由線）；③寬鬆解碼（lenient wire）與伺服器下發能力的設計，對 agent 基礎設施可參考 | 準則①「理解優先」——機制已在既有專案有同構來源（gods-eye-view 的圖層工廠、img2threejs 的 token 效率），抽取邊際價值低 |
| **不納入（連機制都不取）** | 準則④將 agent 約束放 harness 非權限；ArtCraft 之 GUI 畫布與其 agent／基礎設施軸不相交 | 準則③「不要只用技術優劣評估工具」——若未來出現明確生圖／生影需求，現行不納入的前提即失效 |

### 4.5 結論（對照後）

| 判斷 | 內容 |
|---|---|
| 對標的本身 | ArtCraft 對「prompt 控制力不足」的解法（場景先於生成）在技術上成立，且工程成熟度訊號充足（雙桌面實作、CI、效能報告、月度 release） |
| 對使用者 | 其問題域（創作／藝術／影像）在第二大腦中**無對應進行中專案**；且 ArtCraft 的兩大賣點（多供應商路由、GUI 整合創作台）分別對應他已放棄的路線（C1）與他對 GUI 殼的保留（C2） |
| 缺口 | 135 期影片無字幕軌，影片內示範與觀點未納入；本報告僅依 repo 文件、GitHub API 與官網。第二大腦之準則檔皆為 `draft`，其結論以「未經他 review 的 AI 草稿」對待 |
