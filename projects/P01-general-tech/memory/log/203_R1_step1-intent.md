# 203_R1_step1-intent

## 狀況理解

本輪（R1）是 PR #203 的第一次發言，對應 issue #202。使用者要求調研 **opencode 的 LSP（Language Server Protocol）整合**，三個子題：① 是否支援 LSP server 管理（哪些 LSP、怎麼設定）② LSP 對 agent 補全／診斷的實際幫助 ③ 與 Claude Code 的 LSP 支援對比。

issue #202 同時標註為「測試端到端流程用」——驗證 refresh.sh 修復後 mybrain-read 在 CI 能取得最新鏡像。因此本輪除技術調研外，也承載流程驗證目的。技術標的明確：opencode 的 LSP 整合，並以 Claude Code 為對照組。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 跑 refresh.sh 更新鏡像 | 確保讀到最新第二大腦 | 取得最新內容 | ✅ 更新至 626e6ef（2026-08-09） |
| 讀骨幹檔（技術取捨準則、下一步清單、專案現況表、判定總表） | 確認判準與進行中專案 | 掌握評估框架 | ✅ 取得理解優先、MVP→Feature 閘門、Reject≠沒價值等準則 |
| grep「LSP／language server／opencode／claude code」 | 確認標的是否已評估 | 找出既有結論 | ✅ 見下方發現 |

**第二大腦查詢發現（每則帶 URL 與信任層級）：**

1. **opencode 已評估過，但無 LSP 內容** — `技術/技術評估/OpenCode.md`（https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OpenCode.md，`human:fatesaikou`／`stable`，2026-05-01）。結論「大致堪用，Ollama 整合帶來自由度與避免綁定」。判定總表列為採用。**全文未提及 LSP**。
2. **Claude Code 環境已整理，無 LSP 討論** — `技術/追加功能/整理 claudecode-opencode 環境.md`（https://github.com/FATESAIKOU/MyBrain/blob/main/技術/追加功能/整理%20claudecode-opencode%20環境.md，`human:fatesaikou`／`stable`，2026-07-13）。整理 Hook／Skill／MCP 三層，**未觸及 LSP**。
3. **LSP 唯一出現處是另一工具** — `技術/技術評估/codebase-memory-mcp.md`（https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/codebase-memory-mcp.md，`human:fatesaikou`／`stable`，2026-06-27）。用 tree-sitter＋LSP＋SQLite 建程式庫結構理解，判定 skip。**與 opencode 的 LSP 整合無關**。
4. **進行中專案** — LearnGhAgent（本專案，P01-general-tech 為產出處）；mybrain-read 為追加功能、日常在用。本 issue 屬 LearnGhAgent 的端到端流程驗證。

**第二大腦無此主題：** opencode／Claude Code 的 **LSP 整合**本身，第二大腦沒有既有評估或結論。上述 1、2 只證明「opencode／Claude Code 這兩個工具被用過」，不構成對 LSP 整合的判定。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 標的是否已評估 | grep 判定總表＋技術評估目錄 | opencode 已採用，但無 LSP 判定 |
| 是否與進行中專案相關 | 讀專案現況表、下一步清單 | 屬 LearnGhAgent 流程驗證 |
| 是否有取捨準則 | 讀技術取捨準則（骨幹） | 有：理解優先、MVP→Feature 閘門、Reject≠沒價值 |
| 鏡像是否最新 | refresh.sh 執行結果 | 最新（626e6ef） |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 標的判定 | ① opencode LSP 整合 ② 泛 LSP 技術 ③ 工具比較 | ①＋③ | issue 明列三子題，核心是 opencode 的 LSP 整合，Claude Code 為對照 |
| 是否沿用既有 opencode 結論 | ① 直接引用 ② 視為無 LSP 判定、重新調研 | ② | 既有結論不含 LSP，不能當成對 LSP 的舊結論 |
| 流程驗證定位 | ① 忽略 ② 納入意圖 | ② | issue 明示測試端到端流程，屬本輪附加目的 |
