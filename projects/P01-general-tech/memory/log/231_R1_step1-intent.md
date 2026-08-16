# 231_R1_step1-intent

## 狀況理解

本輪（R1）是首輪意圖理解。使用者貼出 issue #230，標的為 **semantica（https://github.com/semantica-agi/semantica）——面向可審計 AI 系統的語義圖譜基礎設施**。屬「典型工作流 2」：給定 GitHub 連結 → 分析 → 產出報告。意圖單純：要對這項技術做一次完整結構化調研（Step 2→3→4），並接受後續 QA loop。無額外附帶條件，技術名已明示。

## 執行的動作與結果

先跑 mybrain-read 更新鏡像至 `bd1446f`，再查三件事：

| 動作 | 目的 | 結果 |
|---|---|---|
| 查「semantica」是否被評估過 | 確認是否已有判定 | **第二大腦無此主題。** 技術/技術評估 89 筆中無 semantica、也無同名的語義圖譜基礎設施筆記（grep semantica／語義圖譜無命中） |
| 查相關領域（knowledge graph／memory／trust／audit）判定 | 取得他對同域技術的既有立場 | 見下方「相關既有判定」 |
| 查進行中專案與取捨準則 | 定位此事與他手邊專案的關係 | 見「與使用者脈絡的對應」 |

**相關既有判定**（信任層級：皆 `stable`，本人或本人 + 流程來源；URL 為 MyBrain 路徑）：

| 技術 | 判定 | 理由（抽取） | URL |
|---|---|---|---|
| Understand-Anything（知識圖譜） | 採用 | Accept，公司中嘗試，用於讓人能 Review AI 產出 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Understand-Anything.md |
| CodeGraph（程式碼知識圖譜） | 試用 | 對開發流程侵入性小，值得嘗試 | .../技術/技術評估/CodeGraph.md |
| EverOS（LLM 長期記憶 OS） | 不採用 | 機制複雜規模大、無自組織驗證、泛用未專門化 | .../技術/技術評估/EverOS.md |
| TencentDB-Agent-Memory（團隊記憶治理） | 不採用 | 重點不是架構，是「資訊能否隨組織自我維護更新」；無防腐化機制 | .../技術/技術評估/TencentDB-Agent-Memory.md |
| OKF（知識標準格式） | 不採用 | 結構太固定；知識圖譜要擴張自適應 | .../技術/技術評估/OKF.md |
| DeerFlow（多智能體框架） | 不採用 | 動態流程無審計性、除錯成本高 | .../技術/技術評估/DeerFlow%20學習紀錄.md |
| QMD（向量搜尋） | 試用 | Accept 的是「至少試一次向量搜尋」此技術類別 | .../技術/技術評估/QMD.md |

**與使用者脈絡的對應**（信任層級：`stable`/`draft`，已註明）：

- **信任瓶頸是他的活主題**：《AI 分層商品化與信任瓶頸》（draft，opencode/glm-5.2 產出）明載「Agentic AI 瓶頸從能力轉向信任」，信任來自 runtime／身分／治理／安全，能力與可信賴性須分開評估——這與 semantica「可審計 AI 系統」的定位高度同軸。
- **Harness Engineering**（stable，本人）關鍵五問含「怎麼知道自己做對了（verify）」，Guardrails=驗證規則程式化。可審計性是他已在實作的信念。
- **進行中專案**：LearnGhAgent（本 harness 自身）、MyBrain（他自建的個人知識庫）最相關。「個人 AiAgent 入口」卡在執行環境選擇（draft，待定）。
- **取捨準則**（《技術取捨準則》draft，claude-code/opus-5）：①理解優先——不穩定或不熟悉就先自己兜，MVP 是理解驗證點；②Reject ≠ 沒價值，會抽取需求理解與方案方向；③不追新；④agent 約束在 harness 不在權限。**這些是他評估任何新技術的通用準則，非 semantica 專用結論。**

## 動作結束後的現狀

| 驗證面向 | 內容與方式 | 結果 |
|---|---|---|
| 標的未重複評估 | grep semantica／語義圖譜於全部技術評估 | 無命中，可安心新做一輪 |
| 同域既有判定 | 讀 EverOS/TencentDB/OKF/Understand-Anything/DeerFlow/QMD 等 | 取得「審計性、自適應、防腐化、理解優先」等既有判準 |
| 與進行中專案關係 | 讀下一步清單、專案現況表、LearnGhAgent.md | 此事無直接掛在某條下一步上；屬一般技術調研 |
| 判準可用 | 讀技術取捨準則、Harness Engineering | 有明確評估框架可供 Step 2 運用 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 理由 |
|---|---|---|---|
| 標的判斷 | 直接以 PR body 明示的 semantica 為標的 vs 自行擴張標的範圍 | 以 semantica 為唯一標的 | PR body 技術名明確，無需另判；Step 3 報告以該技術為主，其他技術放入 §4 替代方案 |
| 第二大腦查詢策略 | 只查標的本身 vs 標的＋相關領域＋判準 | 三路都查 | 標的本身無紀錄，需靠同域判定與準則來定調 Step 2 調研重點 |
| 「無此主題」處理 | 用通用知識填空 vs 明說無紀錄 | 明說「第二大腦無此主題」，並另以他的通用取捨準則輔助 | 遵守 mybrain-read 規則：不可把未經驗證內容講成他的舊結論 |
