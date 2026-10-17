# 306_R1_step1-intent

## 狀況理解

本輪為 **R1、全新主題**（#297）。

- **技術標的**：**ArtCraft**（`storytold/artcraft`），自稱「intentional crafting engine for artists, designers, and filmmakers」；Rust，約 30,821★／4,895 fork，Apache-2.0（issue 實查）。定位看似「**給創作者（藝術家／設計師／影視工作者）的 AI IDE**」。
- **來源**：GitHub 一周熱點 135 期影片（https://youtu.be/n8jL89H5d-c ）。⚠️ issue 載明**該影片無字幕軌（transcripts disabled）、逐字稿取不到**，影片觀點待補——本輪已知來源缺口。
- **使用者要的**：依固定格式產出結構化分析報告（`output/306_<技術名>.md`，5 section：問題／背景／解法／替代 DA 表／User Q&A）。repo 概況 issue 已給，須補上影片缺席的技術內涵。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| refresh MyBrain 鏡像並讀骨幹檔 | 取得既有立場與判準 | 得知判定語意與取捨準則 | 鏡像 @ac9eaa2（2026-10-17）更新成功 |
| grep 標的與鄰近詞（`artcraft`／`storytold`／`AI IDE`／`crafting`／`創作`／`藝術家`／`three.js`／`影像`） | 找既有評估、關聯專案、準則 | 確認標的地位 | 標的本身**零命中**，見下 |

第二大腦查得（皆附 URL 與信任層級）：

1. **標的是否評估過：第二大腦無 ArtCraft 此主題。** `artcraft`／`storytold`／`AI IDE`／`crafting` 全 bundle **零命中**，無既有判定。鄰近者皆同域不同題：
   - [img2threejs](https://github.com/FATESAIKOU/MyBrain/blob/main/日誌/2026-08-22.md)（`process` 類日誌）判 **Reject**，拒的是「圖片轉 3D」、理由「無此需求」——**同屬 3D 域、問題域不同**，不可套用。
   - [munder-difflin](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/munder-difflin.md)（`process:learn-gh-agent`／`draft`）判**不採用**：GUI 型 agent 殼「還太早且包太多」。
   - [gods-eye-view](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/gods-eye-view.md)（`process:learn-gh-agent`／`draft`）判試用，屬 3D 地球／資料融合，軸不同。
     ⚠️ 依 [技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md)，**「不採用 ≠ 沒價值」**，鄰近 Reject 不構成對 ArtCraft 的預判。
2. **關聯的進行中專案**：[下一步清單](https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md)（`claude-code/opus-5`／`draft`／`骨幹`）與 [專案現況表](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/專案現況表.md)（`ollama-cloud/deepseek-v4-flash`／`draft`／`骨幹`）中**沒有任何創作／藝術／設計／遊戲引擎類專案**，技術軸全在 agent 基礎設施（MyLinuxPool、LLMGateway、gas-aiagent-core 等）。**即：此標的與他手上進行中的事無直接關聯。**
3. **取捨準則（骨幹）**：
   - [技術取捨準則](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md)（`claude-code/opus-5`／`draft`／`骨幹`）：①**理解優先**——不穩定或不熟就先自己兜；②**MVP→Feature 唯一閘門＝能否影響個人 workflow**；③**不要只用技術優劣評估工具**；④**agent 信任邊界放 harness 不放權限**。
   - [不做清單](https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/價值觀/不做清單.md)（`claude-code/opus-5`／`draft`／`骨幹`）：**技術層幾乎無硬拒絕**，閉源／無 license 只是採用障礙、非價值否定。
   - [下一步清單](https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md) 前設：可支配時間約 10～20 小時／週，**新開一件事必然要取代掉既有某件事**。
4. **來源缺口的先例**：[Paperclip](https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Paperclip.md)（`process:learn-gh-agent`／`draft`）明載「**來源限制：133 期影片無字幕軌，逐字稿取不到，影片觀點未納入**」——與本輪 135 期同處境，處理方式為**只採 repo 文件與 GitHub API 實查**。

⚠️ **第二大腦無此主題的部分**：ArtCraft 的定位、核心機制、與同類 creator-IDE 的差異，bundle 內全無既有結論——須靠外部資料（README／程式碼）補，不得當成他的舊結論。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 標的判定 | grep `artcraft`／`storytold`／`AI IDE`／`crafting` 全 bundle | **零命中，無既有評估** |
| 專案關聯 | 讀骨幹「下一步清單」「專案現況表」 | 無創作類專案；技術軸全為 agent 基礎設施 |
| 準則 | 讀骨幹「技術取捨準則」「不做清單」 | 理解優先、workflow 閘門、Reject≠沒價值、技術層無硬拒絕 |
| 本輪性質 | 對照 issue 與既有 QA | R1 全新，非追問 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 本輪定位 | R1 新主題／R2 追問 | **R1 新主題** | issue 為 `Closes #297` 的原始需求 |
| 標的邊界 | 只當「Rust repo」／當「藝術家 AI IDE 這一命題」 | **後者：命題本體** | 標的自稱 crafting engine 且服務創作者，須解析其問題定義 |
| 鄰近 Reject 是否沿用 | 沿用 img2threejs/munder-difflin 的 Reject／僅作背景 | **僅作背景** | 問題域不同，且準則明示 Reject≠沒價值 |
| 影片缺席的處理 | 停在「取不到」／以 repo 文件與外部資料補 | **後者** | 對齊 Paperclip 先例，issue 亦要求補上缺漏 |
| 與既有專案的關係 | 硬找關聯／明寫無直接關聯 | **明寫無關聯** | 骨幹清單實查無創作類專案，勿用通用知識填空 |
