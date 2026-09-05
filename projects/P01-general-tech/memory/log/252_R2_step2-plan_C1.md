# 252_R2_step2-plan_C1.md

## 狀況理解

R2 非首次調研，是使用者對 R1 報告的 QA 追問，意圖為「**以個人三大建構標的（個人 AI 入口、MyBrain、LLMGateway）為落點，判定 maka 的採用價值**」。使用者自述「接近 Reject」，Q1 質疑 R1 是否把 maka 簡化成「會留稽核紀錄的多 AI 工作台」，Q2 要逐項評估 maka 對三大標的的幫助。

本 sub-step C1 依 document skill 標準動作，但**針對 R2 意圖**執行：不重做 R1 的 repo 全貌調研，而是補抓「與三大標的相關」的 repo 事實——尤其 remote Runtime Host（對應執行環境未定）、session 投影（對應 ChatSession 記錄切換）、custom relay provider（對應 LLMGateway）。同時以 mybrain-read 確認三大標的現況與取捨準則。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view apache/maka` | 更新 metadata | 確認 stars／更新時間 | **4713 stars**、updated 2026-09-05、description「keeps a complete record of everything it did」、TypeScript、Apache-2.0 |
| 讀 README 更新段 | 確認 R1 後 repo 定位是否變動 | 校正 R1 宣稱 | 新增「Measured, not claimed」benchmark 主張；「The log is the runtime」「Your machine, your model」「One Runtime Host」四支柱與 R1 一致 |
| 讀 `docs/runtime-host-remote-access.md` | 查 remote Runtime Host | 對應「執行環境未定」 | **Desktop/TUI/CLI 可經 TLS/SSH/WebSocket 連遠端 Runtime Host**；`maka runtime-host setup` 可裝 systemd/LaunchAgent 常駐服務、`--project-root` 白名單、`access issue` 發 credential——即「app＋拆開後端」的現成形狀 |
| 讀 `docs/blogs/log-is-the-runtime.md` | 深讀 log 機制 | 校正 Q1「只是留稽核紀錄」 | 明確「Log Is the Database→Log Is the Runtime」：log 是**權威歷史**，UI/next-prompt/crash-recovery 皆為 projection；compaction 只改讀取、log 仍 append-only；tool result prune 把大 payload 卸載到 ArtifactStore |
| 讀 `docs/architecture/runtime-resume-architecture.md` | 查 resume 機制 | 確認復原非 retry | Resume 是「從 crash facts 重建」，RecoveryResolver 分類 tool 狀態、安全才續跑，非盲目 retry |
| 讀 `docs/agent-swarm.md`＋`blogs/multi-agent-scheduling.md` | 查多 agent | 確認「多 AI 工作台」面向 | Agent Swarm 是 orchestration mode 非 tool；多 agent 走「explicit workflow graph」路徑（非 mailbox 訊息傳遞） |
| 讀 `packages/core/src/provider-registry.ts` | 查 provider 抽象 | 對應 LLMGateway | 有 `openai-compatible`／`openai-responses-compatible`／`anthropic-compatible` **custom relay**（`baseUrl` 可指任意 gateway）；內建 openrouter、vercel ai-gateway；model 目錄來自 models.dev（44 providers） |
| mybrain-read | 確認三大標的現況 | 定調價值對照基準 | 見下方「第二大腦查詢結果」 |

**第二大腦查詢結果（信任層級／時間已標註）：**

| 標的 | 現況 | 來源 | 信任層級 |
|---|---|---|---|
| 個人 AI 入口 | app＋拆開後端、ChatSession 記錄切換、擴張 MyBrain 讀寫權限；**卡在執行環境未定**（自架實體/雲端/終端三選）；MultiProvider 三方向未比較 | `技術/靈感/個人 AiAgent 入口.md` | `claude-code/opus-5`／`draft` |
| MyBrain | OKF 格式＋mybrain-read/write/okf-format 三 skill 讀寫閉環；log.md append-only；有定期校準構想 | `技術/追加功能/*` | 前者 `draft`；後者 `human`／`stable` |
| LLMGateway | 個人入口 MultiProvider 的一環；**OmniRoute 已採用**（`human`／`stable`）、Switchyard 觀望；三方向（接既有/自建/內嵌）未比較 | `技術/技術評估/OmniRoute.md`、`Switchyard.md` | OmniRoute `human`／`stable` |
| 取捨準則 | 「理解優先：先自己兜→MVP」「Reject≠沒價值」「MVP→Feature 唯一閘門＝能否影響個人 workflow」 | `抽象理解/本質洞察/技術取捨準則.md` | `draft` |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo 定位是否變動 | README 更新段 | 四支柱與 R1 一致，新增 benchmark 主張；R1 心智模型仍成立 |
| Q1 校正素材 | log-is-the-runtime.md | 有充分證據：log 是權威歷史、稽核是副作用非目的 |
| 執行環境未定 | runtime-host-remote-access.md | **maka 提供現成「app＋拆開後端」形狀**（remote Runtime Host 常駐＋多 client 連線）——直接對應個人 AI 入口卡點 |
| ChatSession 記錄切換 | log-is-the-runtime.md | session/UI/next-prompt 皆 log 投影，對應入口的 ChatSession 記錄切換需求 |
| LLMGateway | provider-registry.ts | maka 是 gateway **consumer**（custom relay 可指 OmniRoute），非 builder；不取代 gateway |
| MyBrain | mybrain-read | maka 是 harness 非記憶系統，直接助益弱；但 append-only log 哲學與 MyBrain log.md 同構 |
| 本 step 產出 | memory/log/252_R2_step2-plan_C1.md | 已產出，含 4 section |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研範圍 | 重做 R1 全貌／針對 R2 意圖補抓 | 針對 R2 意圖補抓 | R1 已建立 repo 事實，R2 是價值對照，只需補「與三大標的相關」的 repo 事實 |
| 是否下採用結論 | 代決／不代決 | 不代決 | 依取捨準則，採用與否屬使用者本人決策，僅提供價值對照 |
| 是否深讀 resume/swarm | 是／否 | 是（resume）、是（swarm 簡讀） | resume 是「復原非 retry」的關鍵證據；swarm 確認「多 AI 工作台」面向的實際機制 |
| 是否查 provider 原始碼 | 是／否 | 是 | 確認 maka 對 LLMGateway 的關係（consumer 非 builder）需看 provider-registry 實作，非僅 README |
| 背景脈絡補查 | 本 step 內完成／留待 C2 | 留待 C2 | 三大標的的價值對照收斂與替代方案（OmniRoute/Switchyard/Aionui 等）歸 C2 處理 |
