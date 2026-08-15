# Muse Code 技術分析報告

> 調研標的：**Muse Code**（Meta 2026-08-05 發表的終端 coding agent，beta）＋基座模型 **Muse Spark 1.2**。
> 定位：**個人採用評估**——對照使用者現行 Claude Code（$22/月訂閱）＋ Ollama Cloud（deepseek-v4-flash）跑的 opencode。
> 資料來源：官方 blog（research.meta.ai）、官方 docs（dev.meta.ai pricing / permissions / cookbook）、OpenRouter、二級分析（agentpedia）。
> 報告完成日期：2026-08-11（R3 更新：2026-08-14，新增 §5 Q4/Q5 與 Contributor 地區限制歧義注記）。

---

## 1. 這個技術解決什麼問題？

Muse Code 解決的是「**在大規模程式庫上執行複雜、長時間、多步驟的軟體工程任務時，單次問答與單一 agent loop 不足以可靠完成，且中斷/崩潰會導致整段工作重來**」的問題。

具體拆成三個可被驗證的「問題」：

| 問題 | Muse Code 的聲稱解 |
|------|------------------|
| 複雜任務需要反覆資訊收集、多子任務協作，主 agent 單線處理慢且易偏離 | 一組**跨 session 持久的 async background agents**，持續活躍、自行決定何時回報主 agent，避免重複收集資訊 |
| 長時間任務一旦崩潰就需從頭來，restart 不精確 | **append-only 本地 event log**（每次 model call / tool run / approval / edit 全記錄），replay-exact、restart-safe，可精確續跑 |
| 任務缺乏結構化規劃與驗證，agent 容易憑印象亂做 | 內建 skills：`/plan`（把任務轉成需核准的計劃）、`/grill`（壓力測試該計劃）、`/goal`（朝目標收斂完成） |

**模糊之處（需標註）**：官方 blog 對「複雜任務」沒有量化定義，benchmark 用 Terminal-Bench 2.1 / DeepSWE 1.1 / Meta 內部 Coding Bench 三個標的，但「個人使用場景下感受得到的改善」不在官方驗證範圍內。async background agents 的「持久」指的是 session 內持久，**不保證跨 session**（跨 session 由 event log 提供 restart，而非 agents 記憶）。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到

- Meta 指出「下一步朝向 frontier，有更大、更強的模型在規劃中」——Muse Code 是這條路線的當前落地點。
- Muse Spark 1.2 是對 1.1 的 coding-focused 升級，重點是「在 coding 任務上大幅提升 training compute + 擴大訓練環境多樣性」。
- 官方自述：「co-training 了 Muse Spark 1.2 與 Muse Code」，讓模型在與該 harness 搭配時表現最佳——即**模型與 harness 是共同優化的**。
- 案例（kernel optimization）展示「1,000+ 次 tool call、最多 24 小時」的長時程自主迭代——這是傳統單次問答做不到的規模。

### 通用技術背景（非文章明說）

- 2025 年 Anthropic 推出 Claude Code，是「agentic coding」（讓 AI 自主執行多步驟開發任務）的第一個主流工具；其後 OpenAI 推出 Codex。Muse Code 是 Meta 對這兩者的直接回應。
- 終端 coding agent 取代「對話式補完」成為主流，源自兩個轉變：
  1. **從單次問答 → 長時程自主**：任務從「寫一個函式」擴大到「重構整個 repo」，需要的不是一次生成，而是規劃＋執行＋驗證＋自我修正的閉環。
  2. **從 stateless → stateful**：長任務需要跨 tool call 的狀態（檔案、shell、記憶），沒有持久化就無法在 crash 後接續。
- 「vibe coding」（無程式經驗者用 agent 建網站/App）的流行，把「agent 能不能自主完成多步任務」推到需求前列。
- 各供應商普遍以「模型 + 專屬 harness」捆綁（Claude Code＋Claude 模型、Codex＋OpenAI 模型、Muse Code＋Muse Spark 1.2），因為模型與 harness 的工具介面／trajectory 需要對齊才表現好。

---

## 3. 這個技術是如何解決該問題的？

Muse Code 的解法可拆為「harness（CLI）」「模型（Muse Spark 1.2）」「安全邊界」三層。只描述機制，不評好壞。

```
┌──────────────────────────────────────────────────────┐
│               Muse Code CLI (harness)                │
│  Main agent loop  +  async background agents (持久)    │
│  Bundled skills: /plan → /grill → /goal               │
│  Local event log (append-only, replay-exact, restart-safe) │
├──────────────────────────────────────────────────────┤
│            Muse Spark 1.2 (coding-focused model)     │
│  長時程訓練 / goal conditioning / context compaction   │
│  co-training with Muse Code harness                   │
├──────────────────────────────────────────────────────┤
│      Security: OS sandbox + staged approval          │
│  Seatbelt(mac) / bubblewrap(Linux) │ --yolo 關閉防護   │
└──────────────────────────────────────────────────────┘
```

### 3.1 async background agents（harness 層）

- 主 agent 用「簡單的 agent loop」；另有一組 **async background agents** 在整個 session 持續活躍，**不是為單一任務臨時 spawn**。
- 它們「執行 next steps、自行決定何時回報主 agent」，目的在「減少主 agent 的重複資訊收集、降低延遲與人工 steering」。
- 對應「跨 session 持久」的誤解：這裡的持久是 **session 內**的 agent 常駐，不是記憶層的持久。

### 3.2 local event log（可重放、可重啟）

- 每個 model call、tool run、approval、edit 都 append 進一個本地 event log，作為**單一 source of truth**。
- 因為是 append-only 且 replay-exact，**crash 後能精確從中斷處續跑（restart-safe）**——這是它能承接 24 小時長任務而不被失敗帶偏的關鍵。

### 3.3 bundled skills

| Skill | 行為 |
|-------|------|
| `/plan` | 把任務轉成「需核准的計劃」 |
| `/grill` | 壓力測試該計劃，直到計劃站得住 |
| `/goal` | 朝指定目標收斂地完成 |

### 3.4 Muse Spark 1.2（模型層）

- **co-training with Muse Code**：訓練包含 rejection-sampled harness trajectories 與 goals/compaction/subagents 的 recipe 優化，並整合 Muse Code toolset 以最大化 harness 相容。
- **long-horizon training**：涵蓋整 repo 生成、大型端到端專案、auto-research；靠 planning 排程、goal conditioning 維持方向、context compaction 保留關鍵知識。
- **self-improvement loop**：用 Muse Spark 1.1 生成難度高的 coding environment 與 instruction-following template，模型自評候選解，產出可擴充的訓練資料集給 1.2。

### 3.5 安全邊界（採用時需知道）

- 兩層獨立防護：**approval**（side-effect 前檢查策略）＋ **sandbox**（shell 在 OS 層級 sandbox 內跑）。
- 三種 approval mode：`on-request`（預設，僅內建危險集停下來審）、`untrusted`（所有未匹配 allow rule 的 shell stage 都停下來審）、`never`（都不審）。
- shell 命令**逐 stage 審查**（不是整行一條龍），`rm -rf` 等會被標危險。trust 以 workspace root 為 scope，可「allow once / always allow in this workspace / reject」。
- sandbox：macOS 用 Seatbelt，Linux 用 bubblewrap；`.git` / `.muse` / `.agents` 保持唯讀，防止 agent 改自己的歷史與設定。
- **`--yolo`**：關掉 approval＋sandbox 並 trust workspace，只在已隔離環境（如 disposable CI container）使用。

### 3.6 定價與資料條款（使用者核心疑慮的直接答案）

| Tier | 模型名 | Input | Cached input | Output | 資料是否訓練 Meta 模型 |
|------|--------|------:|-------------:|-------:|------------------------|
| **Standard** | `muse-spark-1.2` | $1.25/M | $0.15/M | $4.25/M | **否**（prompts/completions 不訓練 Meta 模型） |
| **Contributor** | `muse-spark-1.2-contributor` | $0.10/M | $0.002/M | $0.20/M | **是**（交換折扣，授權用 prompts/completions 訓練未來 Meta 模型） |

- **無長文 premium**：context 幾乎滿或幾乎空，單價相同。
- **Web search grounding**：$2.50 / 1,000 次搜尋，另外計。
- **Rate limits**：Standard 3,000 RPM / 4,000,000 TPM；Contributor 100 RPM / 3,000,000 TPM（per team，非 per key）。
- Contributor tier 有地區限制（select countries），且僅 `muse-spark-1.2-contributor` 此模型適用。
  - ⚠️ **R3 更新（地區限制歧義）**：R3 抓取的官方現行 pricing/models 文件**未再載明「select countries」地區限制**，僅說「以授權訓練換取大幅折扣」。此為**待驗證歧義**——R1/R2 的「限地區」可能源自較早或二級來源；若你所在區域被排除，Contributor 可能不可用，需以申請時官方回覆為準。

**「給 Meta 訓練坐到啥地步」的拆解**：
- 想「不給 Meta 訓練」→ 用 **Standard tier**（`muse-spark-1.2`），官方條款明載不訓練。
- 想要便宜 92%（in $1.25→$0.10、out $4.25→$0.20）→ 用 **Contributor tier**，代價是授權 Meta 用你的 prompt/completion 訓練未來模型，且限地區。
- 兩者是「價格 vs 資料授權」的明確二分，沒有第三種模糊地帶。

### 3.7 與現有棧相容（採用評估關鍵）

官方 model cookbook 宣稱 Muse Spark 1.2 **drop-in 相容**以下介面：
- OpenAI SDK / Anthropic SDK（改 `base_url` 為 `https://api.meta.ai/v1` 即可）
- **OpenCode**（Use case 11 是「OpenCode + Muse Spark」的 GitHub repo agent）
- **Claude Code**

意義：對使用者而言，**不需換 harness**——若只要用 Muse Spark 1.2 模型，在 opencode / Claude Code 改 base_url + model 即可；Muse Code CLI 本身才是「另一套 harness」。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|----------|-------------|---------------|-----------------|
| **Claude Code（Anthropic）** | 專屬 terminal agent harness，配 Claude 模型；使用者現行主力 | 付費訂閱（個人 $22/月）；接受 Anthropic 生態 | 綁定 Anthropic 模型與 harness；訂閱制，模型選擇受限 | 目前使用者日常主力；Opus5 系在 Terminal-Bench 系統對照（86.7%）仍高於 Muse Code 82.9% |
| **OpenCode（opencode.ai）＋ Ollama Cloud** | 開源 CLI harness，配任意 provider；使用者現行主司開發 | 接受自行組合 harness＋模型；對 harness 與 model 有理解 | 無內建 async 持久 subagent 框架（需自行搭建）；模型能力上限取決於所選 provider | 高度自由、避免綁定供應商；個人開發主力 |
| **OpenAI Codex** | OpenAI 的 terminal coding agent，配 GPT/Codex 模型 | 接受 OpenAI 生態與 API key | 綁定 OpenAI 模型；無 Meta 兩 tier 資料授權選項 | 與 Claude Code 同級的對抗者 |
| **Kimi Code（Moonshot）** | 開源長程程式設計模型 + 終端 agent，跨檔案重構、MCP 生態、子 agent 並行 | 接受開源/第三方案 | 模型品質為既有已覆蓋需求 | 使用者 MyBrain 判定：**Reject**（品質改善，已有更低價且品質滿足的替代方案） |
| **OmniRoute** | 本機 LLM API Gateway，統一 250+ provider、聚合免費額度 | 需自建/自維護本機 gateway | 非 coding agent harness，不提供 agent 執行框架 | 使用者 MyBrain 判定：**Accept**（LLM Provider 解耦層，有學習必要，MVP 導入） |

### 4.2 第二大腦既有判定對照（含信任層級與衝突）

| 主題 | 第二大腦內容 | GitHub URL | 信任層級 | 時間 |
|------|-------------|-----------|----------|------|
| **Muse Code** | 判定總表 86 筆**無此主題**，grep 無命中 → 本次為首次評估 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/判定總表.md | 未判定 | — |
| **Kimi Code** | **Reject**：基本上屬模型品質改善，已有更低價且品質滿足的替代方案 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Kimi%20K3.md | `process:learn-gh-agent` ＋ `stable` | 2026-07-26 |
| **OmniRoute** | **Accept**：本質是 LLM Provider 解耦層（API Gateway），因解耦所以有學習必要，MVP 階段導入 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OmniRoute.md | `opencode/deepseek-v4-pro` ＋ `draft` | 2026-07-26 |
| **OpenCode** | 大致堪用，Ollama 整合帶來自由度、避免綁定供應商 | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OpenCode.md | `human:fatesaikou` ＋ `stable` | 2026-05-01 |
| **技術取捨準則（骨幹）** | 不追新；MVP→Feature 唯一閘門＝能否影響個人 workflow；Reject≠沒價值；模型分級 | https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md | `claude-code/opus-5` ＋ `draft`（未 review） | 2026-08-01 |
| **LLM 降本增效** | 個人開發強烈推薦 Ollama Cloud；複雜推理/企業級才用 Gemini/Anthropic/Codex | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/LLM降本增效.md | `human:fatesaikou` ＋ `stable` | 2026-05-01 |

### 4.3 與個人取捨準則的衝突點（最重要）

查 MyBrain 後，Muse Code 對照使用者既有判準，存在**結構性衝突**，需明示：

1. **「不追新」與「beta 新產品」**：技術取捨準則明言「他不追新，出現更好的替代不構成汰換」。Muse Code 是 2026-08-05 剛發布的 beta。照此準則，單憑「Meta 出了新 agent」不構成切換理由。
2. **Kimi Code Reject 的可類比性**：使用者對同類「terminal coding agent + 新模型」的 Kimi Code 判定為 Reject，理由正是「已有更低價且品質滿足的替代方案」。Muse Code 面對的是同一問題域——若其核心價值（async background agents、event log restart-safe）已被現行 Claude Code + opencode 覆蓋，會落入相同的 Reject 論證。
3. **衝突（查詢最有價值處）**：Muse Code 有 Kimi Code 沒有的**可拆用性**——Muse Spark 1.2 可 drop-in 進 opencode/Claude Code（改 base_url），不必換 harness。這使「試 Muse Spark 1.2 模型」與「採用 Muse Code harness」**是兩件事**。若使用者只想試模型，不違反「不追新 harness」；若要換 harness，才撞上「不追新」與「已覆蓋需求」兩條準則。
4. **LLM 成本立場**：使用者個人開發強烈推薦 Ollama Cloud，僅「複雜推理/企業級」才用 Anthropic/Codex 等高價。Muse Code 是純 token 計費、無月費，**對低用量場景是零固定成本**——這與「Ollama Cloud 為主、高價模型為輔」的分級相容，不必然相衝。

### 4.4 切入點差異

| 切入點 | 代表 | 特徵 |
|--------|------|------|
| **模型 + 專屬 harness 捆綁 co-train** | Muse Code＋Muse Spark 1.2、Claude Code＋Claude | 模型為 harness 工具介面/trajectory 對齊優化，開箱即用但綁供應商 |
| **harness 可插模型（drop-in）** | opencode、Claude Code、Codex | 換 model 只改 base_url；模型本身也可跨 harness 用（Muse Spark 1.2 即此類） |
| **模型聚合 gateway** | OmniRoute、OpenRouter | 純解耦層，不提供 agent 執行框架，需自行組合 harness |
| **開源模型 + 自兜 harness** | Ollama Cloud＋opencode | 最高自由度、成本低，但無內建長時程持久 agent 框架 |

---

### 4.5 個人採用評估總論（給使用者的收斂）

**結論（情境化判準，非二選一）：**

| 情境 | 判斷 | 依據 |
|------|------|------|
| 只想試 Muse Spark 1.2 模型，不換 harness | **可低成本試**（零月費、token 計費，drop-in opencode/Claude Code 改 base_url） | 不撞「不追新 harness」；符合「模型分級」的評估習慣 |
| 想換 Muse Code harness | **暫緩**，進入 Judge 階段先理解 | 撞「不追新」＋「已覆蓋需求」（Kimi Code 同域 Reject 前例）＋ beta 未穩定 |
| 在意資料授權 | **Standard tier 才不訓練**；要便宜 92% 就用 Contributor（授權 Meta 訓練，限地區） | 官方 pricing 條款二分 |
| 性價比 | **低/中用量時 Muse Code 零固定成本**，但 Standard output $4.25/M 高於多數 coding model；Contributor 才接近低價 | 對照「Ollama Cloud 為主、高價模型為輔」分級 |

**MVP 到 Feature 的唯一閘門**（依技術取捨準則）：Muse Code / Muse Spark 是否影響你個人的 daily workflow。此點需實際試用才能判定，非本次調研可定案。

---

## 5. User Q&A

### Q1：相同用量下 MuseCode 的月費到底是多少？我 ClaudeCode 跟 OllamaCloud 每週都用 50~80% 周限額、集中在六日，算個數值給我比較

**A**：先講硬性限制——**官方不公開 Claude Code Pro 與 Ollama Cloud 的「周限額＝多少 token」**，因此「相同用量」無法從官方直接換算成 Muse 的 token 費用。要給數值，只能**自設 token 量假設**，以下用敏感度表呈現，並標明假設。

**計費結構對照（先釐清，避免誤比）：**

| 方案 | 計費型態 | 月固定成本 | 每 token 單價 |
|------|---------|-----------|--------------|
| Claude Code Pro | 固定月費 | $20/月（官方現行；你自述 $22） | 不公開（周限額內） |
| Ollama Cloud Pro | 固定月費 | $20/月 | 不公開（token 計但無單價） |
| Muse Spark 1.2 Standard | 純 token 計費 | $0 | $1.25 in / $0.15 cached / $4.25 out（每 M） |
| Muse Spark 1.2 Contributor | 純 token 計費 | $0 | $0.10 in / $0.002 cached / $0.20 out（每 M） |

**「相同用量」的換算假設**：你每週用 50~80% 周限額、集中六日。以「每週 4 週、每月 4 週」計，假設每週用量落在中位 65%，並以「input:output ≈ 3:1」的 coding agent 典型比例估算。因官方無周限額 token 數，以下為**假設性敏感度表**，非官方數字：

| 假設每週 token 量（in+out） | 每月 token 量 | Muse Standard 月費 | Muse Contributor 月費 |
|---------------------------|--------------|-------------------|----------------------|
| 5M（低） | 20M | ≈ $1.25×15M + $4.25×5M = **$40** | ≈ $0.10×15M + $0.20×5M = **$2.5** |
| 10M（中） | 40M | ≈ $1.25×30M + $4.25×10M = **$80** | ≈ $0.10×30M + $0.20×10M = **$5** |
| 20M（高） | 80M | ≈ $1.25×60M + $4.25×20M = **$160** | ≈ $0.10×60M + $0.20×20M = **$10** |

**結論**：
- Muse **Standard** 在「相同用量」下**不必然比現行 $40/月（Claude $20 + Ollama $20）便宜**——中高用量（每週 10M+）就超過 $80/月，是現行兩倍以上。Standard 的優勢只在**低用量**（每週 <5M）時才成立。
- Muse **Contributor**（授權 Meta 訓練、限地區）在相同用量下**遠低於現行**（$2.5~$10/月），但代價是資料授權。
- 真正的比較前提是：**你現行 $40/月是「固定費、周限額內無限用」；Muse 是「變動費、用多少付多少」**。若你六日集中衝量，Muse 的變動費在高峰週會放大，不像固定月費有上限保護。
- 因官方不公開周限額 token 數，**此數值無法精確**；要精確需先實測你每週實際 token 消耗（Claude Code 用量統計 / Ollama Cloud 用量頁）。

**結論**：Muse Standard 對你「每週 50~80% 周限額、集中六日」的用量，月費約落在 **$40~$160**（依每週 5M~20M token 假設），**中高用量下不具價格優勢**；Contributor 才便宜，但以資料授權為代價。

---

### Q2：Muse 有多模態嗎？

**A**：**有，多模態輸入、純文字輸出**。OpenRouter 的 `meta/muse-spark-1.2` model card 明載：

| 方向 | 支援 |
|------|------|
| 輸入 | **text / image / video / audio / PDF** |
| 輸出 | **text**（僅文字） |
| Context | 1M tokens |

- 官方 blog 的建站 demo 以 **mp4 影片**驅動生成，佐證 video 輸入。
- 注意：model card 表格列 image/video/PDF，**audio 僅出現於 prose 描述**，未在表格明列——若你依賴 audio 輸入，需實測確認。
- 對照你的現行棧：Claude Code（Opus/Fable 系）與 deepseek-v4-flash 皆支援多模態輸入；Muse 的多模態**不構成相對優勢**，僅是「有，不輸人」。

**結論**：Muse 支援 text/image/video/audio/PDF 輸入、text 輸出、1M context；多模態能力與你現行模型同級，非切換理由。

---

### Q3：Muse 在 Coding 效能上比 Anthropic 各模型（Opus/Fable 系）跟 deepseek-v4-flash 表現如何？給 benchmark 數據，沒有就官方數據

**A**：分兩層回答——**官方數據**與**獨立評測**，並**明確標註「與 deepseek-v4-flash 無同基準可比」**。

**官方數據（Meta vendor-run，各自 harness）：**

| Benchmark | Muse Spark 1.2 | 排名 | 對照 |
|-----------|---------------|------|------|
| Terminal-Bench 2.1 | **82.9** | 第 2 | 僅次 Claude Opus 5 |
| DeepSWE 1.1 | **59.3** | 第 2 | 僅次 Claude Opus 5 |
| Meta Internal Coding Bench | **70.6** | 第 2 | 僅次 Claude Opus 5 |
| Kernel case（speedup） | 68.7% | — | Opus 5 = 74.0% |

**獨立評測（Artificial Analysis）：**

| 指標 | Muse Spark 1.2 | Opus 5 | Fable 5 | GPT-5.6 Sol | Kimi K3 | Grok 4.5 |
|------|---------------|--------|---------|------------|---------|----------|
| AA Intelligence Index | 54（xhigh） | 61 | 60 | 59 | 57 | 54 |
| GDPval-AA Elo | 1631（#5） | 1852 | — | — | — | — |

**與 deepseek-v4-flash 的對照限制（必須明示）：**
- DeepSeek 官方報 **Terminal-Bench 2.0**（Max 56.9）＋ **SWE Verified 79.0**。
- Muse 官方報 **Terminal-Bench 2.1** 與 **DeepSWE 1.1**——**不同 benchmark 版本與不同標的**，**無法直接對等比較**。
- 因此「Muse vs deepseek-v4-flash」**沒有同基準的官方或獨立數據**，不能硬套同表。要公平對照需自行在相同任務集上實測。

**結論**：
- 官方與獨立評測一致顯示 Muse Spark 1.2 在 coding 上**居第 2、僅次 Claude Opus 5**，高於 Fable 5 之外的多數模型。
- **與 deepseek-v4-flash 無同基準可比**——DeepSeek 報的是不同 benchmark（Terminal-Bench 2.0 / SWE Verified），不能直接比較；需自行實測才能定論。
- 對你「Opus/Fable medium 以上」的日常主力，Muse 在官方數據上**低於 Opus 5**，與 Fable 5 接近；是否值得切換，取決於你實際任務的錯誤擴散範圍（見 §4.5 模型分級）。

---

### Q4：如果我想試用 Muse Spark 1.2，可以用 opencode 嗎？要訂閱哪個專案（我可以接受貢獻）？怎麼設定？給我一步步指令教學

**A**：**可以，opencode 是官方 cookbook 明載的 drop-in 目標**（Use case 11「OpenCode + Muse Spark」的 GitHub repo agent）。你不需要換 harness，只要在 opencode 加一個 provider 設定、改 `base_url` 與 model 即可。

**訂閱哪個 tier（你明說可接受貢獻）：**

| Tier | 模型 ID | Input | Cached | Output | 資料授權 | 適用 |
|------|---------|------:|-------:|-------:|---------|------|
| **Standard** | `muse-spark-1.2` | $1.25/M | $0.15/M | $4.25/M | 不訓練 Meta 模型 | 不想授權資料 |
| **Contributor** | `muse-spark-1.2-contributor` | $0.10/M | $0.002/M | $0.20/M | 授權 Meta 用你的 prompt/completion 訓練未來模型 | **你「可接受貢獻」→ 選這個，-92%** |

- Contributor 折扣：in $1.25→$0.10、cached $0.15→$0.002、out $4.25→$0.20。
- Rate limits：Standard 3,000 RPM / 4M TPM；Contributor 100 RPM / 3M TPM（**per team，非 per key**）。
- ⚠️ **地區限制歧義**：R1/R2 引用的「Contributor 限 select countries」在本輪（R3）抓取的官方現行 pricing/models 文件**未再載明**，僅說「以授權訓練換取大幅折扣」。此為**待驗證歧義**——若你所在區域被排除，Contributor 可能不可用，需以申請時官方回覆為準。

**一步步設定（opencode 接 Muse Spark 1.2）：**

官方 cookbook 提供兩版 config，官方建議用 **Responses API 版**（`@ai-sdk/openai`），理由見下方對照。

**步驟 1：取得 API key**
- 到 dev.meta.ai 註冊、選 Contributor tier（或 Standard）、取得 API key。

**步驟 2：在 opencode 設定 provider（Responses API 建議版）**

在 opencode 的 provider 設定（`opencode.json` 或對應 config）加入：

```jsonc
{
  "provider": {
    "meta": {
      "npm": "@ai-sdk/openai",
      "name": "Meta (Muse Spark)",
      "options": {
        "baseURL": "https://api.meta.ai/v1",
        "apiKey": "{你的 API key}"
      },
      "models": {
        "muse-spark-1.2": {
          "name": "Muse Spark 1.2 (Contributor)",
          "options": {
            "model": "muse-spark-1.2-contributor",
            "reasoning": { "include": ["reasoning.encrypted_content"] },
            "modalities": ["text"],
            "limit": { "context": 1000000 }
          }
        }
      }
    }
  }
}
```

**步驟 3：在 opencode 選用該模型**
- 在 opencode 的 model 選擇中選 `meta/muse-spark-1.2`，即可開始試用。

**兩版 adapter 對照（官方明載 tradeoff）：**

| 接法 | SDK | 優點 | 代價 |
|------|-----|------|------|
| **Responses API（建議）** | `@ai-sdk/openai` | 原生多模態輸入（image/PDF）；跨 turn 加密 reasoning 續傳（`reasoning.encrypted_content`），避免每 turn 從零推理、多步 tool loop 失焦 | 設定較繁 |
| **Chat Completions（簡化）** | `@ai-sdk/openai-compatible` | 設定簡單 | 不保證 reasoning 續傳；無原生 PDF 輸入 |

**結論**：opencode 可直接接 Muse Spark 1.2，不需換 harness；你「可接受貢獻」→ 選 **Contributor tier**（-92%），照上述 config 改 `base_url`＋model 即可。Contributor 的地區限制為待驗證歧義，申請時需確認。

---

### Q5：MuseCode 跟 opencode 比有優勢嗎？優勢是啥？對成本或成果的量化數值影響是多少？

**A**：先釐清比較層級——**MuseCode 與 opencode 都是 harness（CLI 執行框架），不是模型**。R2 已答的是「模型層」（Muse Spark vs Opus/DeepSeek）；此問是「harness 層」。**官方沒有 MuseCode vs opencode 的並排量化數據**，因此「成果量化」只能質性＋標明限制；「成本量化」有可計算部分。

**harness 層優勢對照（MuseCode 官方自述特性 vs opencode）：**

| 面向 | MuseCode | opencode | 差異 |
|------|----------|----------|------|
| 長時程 async 持久 agent | **內建**：background agents 常駐、自行決定回報主 agent | 無內建，需自行搭建 | MuseCode 有 |
| crash 續跑 | **內建**：append-only event log，replay-exact、restart-safe | 無同等內建 | MuseCode 有 |
| 結構化規劃 skill | **內建**：`/plan`→`/grill`→`/goal` | 無同等內建 | MuseCode 有 |
| 安全邊界 | **內建**：approvals（on-request/untrusted/never）＋ OS sandbox（Seatbelt/bubblewrap） | 依賴外部設定 | MuseCode 開箱即用 |
| 專案記憶 | **durable project memory** | 依賴外部方案 | MuseCode 有 |
| AGENTS.md 相容 | 支援 | 支援 | 同級 |
| 模型可插性 | 綁 Muse Spark 系 | 任意 provider（含 Muse Spark drop-in） | **opencode 較自由** |
| 成本結構 | usage-based token 計費（無月費） | 開源免費 harness，成本在模型 | 見下方量化 |

**成本面量化（可計算部分）：**

| 方案 | 固定成本 | 變動成本 | 對你「每週 50~80% 周限額、集中六日」的月費 |
|------|---------|---------|------------------------------------------|
| opencode（現行） | $0（開源） | 模型費：Claude $20 + Ollama $20 = **$40/月** | $40/月（固定） |
| MuseCode + Muse Spark Standard | $0 | token 計費 | $40~$160/月（依每週 5M~20M token，見 Q1） |
| MuseCode + Muse Spark Contributor | $0 | token 計費 | $2.5~$10/月（依每週 5M~20M token，見 Q1） |

- **換 harness 本身不改變模型成本**——MuseCode 的優勢不在「更便宜」，而在「內建長時程 agent 框架」。
- 若你**只把 Muse Spark 接進 opencode**（不換 harness），成本與「MuseCode + Muse Spark」相同，但保留 opencode 的模型自由。

**成果面量化限制（必須明示）：**
- 官方無「MuseCode vs opencode 在同一任務集上的完成率/耗時」並排數據。
- 唯一可推論的是：MuseCode 的 async background agents＋event log restart-safe 是為「1,000+ tool call、24 小時長任務」設計；opencode 無此內建。**若你的任務多為短時程（單次 session 內完成），此優勢不構成實際差異**；若常跑長時程自主迭代，MuseCode 的內建框架可省去自行搭建成本。

**結論**：MuseCode 對 opencode 的優勢集中在**長時程 async agent、crash 續跑、內建規劃 skill 與安全邊界**；成本上 harness 本身不省錢（模型費才是大頭），成果上無官方並排量化，需以「你的任務是否長時程」判斷此優勢是否落地。若只想試 Muse Spark 模型，**接進 opencode 即可，不必換 harness**。
