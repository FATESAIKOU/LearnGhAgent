# 232_R1_step1-intent.md

## 狀況理解

這是 R1（首輪）。使用者指定技術標的為「**macro**——開源團隊工作台與團隊級記憶系統」，GitHub 連結 `https://github.com/macro-inc/macro`，Closes #229。

標的定位：**開源團隊工作台（team workspace）＋ 團隊級記憶系統（team-level memory）**。這不是單一工具，而是「人與 Agent 協作的工作台」與「團隊級記憶治理」兩個問題域的疊加。使用者未附帶其他條件，屬標準「給定 GitHub 連結 → 分析 → 產出報告」流程。

需在 Step 2 釐清 macro 的實際定位（是工作台、記憶系統、還是兩者整合）、其核心機制、與既有已評估方案的差異。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 PR body 全文 | 理解技術標的與附帶條件 | 判斷要解析的對象與範圍 | 標的＝macro（開源團隊工作台＋團隊級記憶系統）；無附帶條件；R1 首輪 |
| 用 mybrain-read 查第二大腦 | 確認他是否已評估過此主題、與哪個專案相關、有無取捨準則 | 定調意圖前先掌握既有立場 | 見下方「第二大腦查詢結果」 |
| 讀取既有 step1 log 範例（224_R1） | 確認 log 格式與長度基準 | 產出符合規範的 log | 格式 4 section、精簡、表格化 |

### 第二大腦查詢結果

| 查詢面向 | 結果 | GitHub URL | 信任層級 |
|---|---|---|---|
| macro 是否已被技術評估 | **第二大腦無此主題**——`技術/技術評估/` 88 筆無 macro 相關評估；grep "macro" 僅命中 Chatwoot 的 Macros 功能（無關） | — | — |
| 同問題域既有評估（團隊級記憶） | **TencentDB-Agent-Memory**（團隊級 Agent 記憶系統）→ **Reject**：重點不是架構設計，而是讓資訊隨組織自我維護更新；無防腐化機制的大腦等同必定過期的文件 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/TencentDB-Agent-Memory.md | `generated.by: process:learn-gh-agent`、`status: draft`（機器產出，未 review） |
| 同問題域既有評估（人與 Agent 協作工作台） | **Buzz**（Block 人與 Agent 協作工作台）→ **Reject**：規模過大、採用效果未知、個人使用不必要；**Delta**（agent 協作環境）→ **Reject**：vendor 綁定、只是開發過程紀錄機制可自己兜、團隊效果難驗證 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Buzz.md 、 https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Delta.md | 皆 `process:learn-gh-agent`、`status: draft` |
| 同問題域既有評估（跨 session 記憶） | **EverOS**（跨 session 長期記憶 OS）→ **Reject**：機制複雜規模大、無自組織驗證、泛用未專門化 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/EverOS.md | `process:learn-gh-agent`、`status: draft` |
| 與哪個進行中專案相關 | **個人 AiAgent 入口**（進行中，執行環境未定）——個人級 agent 入口，與 macro 的「團隊級」不同層級；**MyBrain**（個人級記憶，日常在用）——macro 若含團隊記憶治理，與 MyBrain 的「人 review 當品質守門員」模型可對照 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/靈感/個人%20AiAgent%20入口.md 、 https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/專案現況表.md | `claude-code/opus-5`、`status: draft` |
| 相關取捨準則（技術評估方法） | 理解優先（先自己兜→MVP→才決定）；MVP→Feature 唯一閘門＝能否影響個人 workflow；Reject＝不採用≠沒價值；「讓資訊隨組織自我維護更新」是團隊級記憶的核心判準 | https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md | `claude-code/opus-5`、`status: draft`（AI 草稿，未 review） |

**結論**：第二大腦沒有 macro 的既有評估，此主題對他是全新的。但「團隊級記憶／人與 Agent 協作工作台」這個問題域他已評估過多個方案（TencentDB-Agent-Memory、Buzz、Delta、EverOS 皆 Reject），且核心判準明確——「資訊能否隨組織自我維護更新（防腐化）」與「能否影響個人 workflow」。macro 的解析應與這些既有判定對照，而非從零孤立分析。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 需求類型 | 首輪 / 追問 / 質疑 | 首輪（R1），新技術標的 |
| 技術標的 | 使用者指定 | macro——開源團隊工作台＋團隊級記憶系統 |
| 附帶條件 | PR body 是否含額外要求 | 無，標準分析流程 |
| 第二大腦 | 是否已有評估 | 無 macro 主題；但同問題域（團隊級記憶／協作工作台）已有 4 個 Reject 判定可作對照 |
| 專案關聯 | 與進行中專案關係 | 個人 AiAgent 入口（進行中）、MyBrain（日常在用）為個人級，與 macro 團隊級不同層級，僅作對照 |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 標的定位 | 當成「工作台」評估 / 當成「記憶系統」評估 / 當成「工作台＋記憶」整合評估 | 工作台＋記憶整合 | 使用者標題明示「團隊工作台與團隊級記憶系統」，兩者疊加；Step 2 需先釐清 macro 實際側重哪一側 |
| 第二大腦角色 | 當成報告主體 / 僅作背景對照 | 僅背景對照 | 無 macro 既有評估；但同問題域的 4 個 Reject 判定與「防腐化」判準是解析時的重要對照基準，可放進報告 §4 替代方案與 QA |
| 對照基準 | 孤立分析 macro / 與既有 Reject 方案對照 | 與既有 Reject 方案對照 | 使用者對團隊級記憶已有明確判準（防腐化、影響 workflow），不對照會重蹈其已拒絕的方向 |
| 個人 vs 團隊層級 | 混為一談 / 明確區分 | 明確區分 | macro 是團隊級，MyBrain／個人 AiAgent 入口是個人級，層級不同，報告需標明避免誤導 |
