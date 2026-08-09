# 209_R1_step1-intent.md

## 狀況理解

使用者（issue #208）要求調研「TencentDB-Agent-Memory」——騰訊雲開源的團隊級 Agent 記憶系統（GitHub: TencentCloud/TencentDB-Agent-Memory）。這是 R1 首輪，PR body 僅給技術名與連結，無附帶條件。核心意圖：產出標準 5 點分析報告（解決什麼問題／背景／如何解決／替代方案／User Q&A）。技術標的屬「AI Agent 記憶」領域，與使用者第二大腦 MyBrain 及既有大量 agent-memory 評估高度相關，需在報告中對照其既有立場。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀取 PR body 與 issue #208 | 確認技術標的與附帶條件 | 確認調研對象 | TencentDB-Agent-Memory，團隊級 Agent 記憶 hub，無其他條件 |
| 讀取 AGENTS.md | 確認 step1 輸出格式 | 正確產出 4-section log | 格式確認完畢 |
| 讀取 MyBrain 骨幹檔（判定總表、技術取捨準則、專案現況表、下一步清單） | 理解使用者既有技術立場與 workflow | 判斷是否已評估過、取捨模式 | 判定總表無 TencentDB-Agent-Memory 條目（未評估）；使用者採「理解優先」策略，MVP→Feature 唯一閘門是能否影響個人 workflow |
| 搜尋 MyBrain 中 agent memory 相關內容 | 確認既有評估脈絡 | 避免重複、對照既有立場 | 已評估多個同類：EverOS（不採用）、OpenHuman（未判定）、planning-with-files（不採用）、codebase-memory-mcp（不採用）、HermesAgent（採用）、LeanCtx（採用）、Headroom（採用）、context-mode（觀望） |
| 抓取官方 README | 理解技術本體 | 掌握核心機制 | 四類記憶資產（Chat Memory/Skill/Wiki/CodeGraph）、L0-L3 分層、Memory Hub 控制面板、ACL 權限、跨框架（OpenClaw/Hermes/Claude Code/CodeBuddy） |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 技術標的 | 從 PR body 確認 | TencentDB-Agent-Memory（騰訊雲開源，18.6k stars，MIT） |
| 使用者既有評估 | 搜尋 MyBrain 判定總表與全文 | 無此標的評估紀錄；但同領域已評估 8+ 個 agent-memory 工具 |
| 使用者 workflow 關聯性 | 讀取專案現況表與技術取捨準則 | 使用者自建 MyBrain 即為個人記憶系統；LearnGhAgent 為進行中專案；採「理解優先」策略，重視「能否影響個人 workflow」 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研範圍 | (A) 僅限官方 README (B) 補網路搜尋架構細節、替代方案、benchmark | B | 標的屬使用者已深耕的 agent-memory 領域，需對照其既有 8+ 評估與 MyBrain 設計，才能回答「與我的方案差異」 |
| 是否需要先查 MyBrain | (A) 直接開始調研 (B) 先查使用者背景 | B | 標的與使用者自建 MyBrain 高度同域，需先理解其既有立場與取捨準則，避免報告與其舊結論衝突 |
