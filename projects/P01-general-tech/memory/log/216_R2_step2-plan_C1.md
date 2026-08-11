# 216_R2_step2-plan_C1.md

## 狀況理解

R2 是 R1 的定量追問輪，非新標的。MuseCode 是**商業產品非 GitHub repo**（無 metadata 可抓，也無 README），C1 因此以「官方 docs＋OpenRouter model card＋二級評測」作為一手/半手資料來源，補齊 R2 三問的缺口。三問與對應資料缺口：

1. **價格計算**：需把使用者「每週 50~80% 周限額、集中六日」換算成 Muse 的月 token 費用。R1 已有牌價（Standard $1.25/$0.15/$4.25；Contributor $0.10/$0.002/$0.20），缺的是「周限額→token 量」的換算依據。
2. **多模態**：R1 未涵蓋，需查官方 model card 確認支援哪些 modality。
3. **Coding 效能對照**：需 Muse Spark 1.2 vs Anthropic（Opus/Fable）與 deepseek-v4-flash 的 benchmark；沒有同基準就標明並引官方/二級數據。

## 執行的動作與結果

| 動作 | 目的 | 預期達成效果 | 實際結果 |
|---|---|---|---|
| fetch research.meta.ai 官方 blog | 取得 Muse Code／Spark 1.2 一手聲明 | 確認 async agents、event log、skills 機制 | 完成；確認 co-training、long-horizon、kernel case study（1,000+ tool calls、24h） |
| fetch OpenRouter /meta/muse-spark-1.2 model card | 確認 modality、context、pricing | 補 R2 問 2（多模態）與問 1（牌價交叉驗證） | **完成**：accepts text/image/video/audio/PDF，returns text，1M context；$1.25/$4.25/M |
| 讀官方 methodology PDF（static/muse-spark-1-2-methodology） | 取得 benchmark 官方數字與對手 | 補 R2 問 3 官方基準 | 部分；PDF 為 compressed 圖表流，無法直接讀文字數值，改由二級來源（VorpLabs/Artificial Analysis）補 |
| 子 agent 網研（並行） | 彙整 Claude Pro 周限額、Ollama Cloud 計費、跨模型 benchmark、多模態 | 一次補齊三問的可引用數字 | 完成；見下方關鍵發現 |
| mybrain-read 查周限額/成本紀律 | 確認是否已有換算基線或判例可引 | 找到可直接引用的成本立場與分級 | 完成；見下方第二大腦發現 |

### 關鍵一手/半手發現

**Q1 價格（可計算的前提與限制）**
- Claude Code Pro：官方定價 **$20/月**（月付）/ $17/月（年付）——**不是 $22**。官方明言「無固定 message 數」，周限額**不公開 token 量** → 無法從官方得出「Pro 周限額＝多少 token」。
- Ollama Cloud：**Pro $20/月**訂閱制，5 小時 session＋7 天 weekly 限額，以 token 計但不公開定價每 token；deepseek-v4-flash 為「Medium」用量等級。**無每 token 單價**。
- Muse Spark 1.2：**純 token 計費、無月費**。Standard $1.25/$0.15/$4.25/M；Contributor $0.10/$0.002/$0.20/M（換訓練權＋限地區）。
- → 結論：兩個現役方案是**固定月費**（~$40-44/月總計），Muse 是**變動費**。要算「相同用量下 Muse 月費」必須**自設 token 量假設**（官方無周限額 token 數），此為計算的硬性限制，需在報告中明示。

**Q2 多模態**：**支援**。text/image/video/audio/PDF 輸入、text 輸出，1M context（OpenRouter model card 明載；audio 僅出現於 prose，表格列 image/video/PDF）。

**Q3 benchmark（官方＋二級）**
- Meta 官方（vendor-run，各自 harness）：Terminal-Bench 2.1 = **82.9**、DeepSWE 1.1 = **59.3**、Meta Internal Bench = **70.6**，皆**第 2 名，僅次 Claude Opus 5**；kernel case：Muse 68.7% speedup vs Opus 5 的 74.0%。
- Artificial Analysis（獨立）：AA Intelligence Index Muse=54（xhigh）vs Opus 5=61、Fable 5=60、GPT-5.6 Sol=59、Kimi K3=57、Grok 4.5=54；GDPval-AA Elo Muse=1631（#5）vs Opus 5=1852。
- **與 deepseek-v4-flash 無同基準可比**：DeepSeek 官方報 Terminal-Bench **2.0**（56.9 Max）＋ SWE Verified 79.0，與 Muse 的 Terminal-Bench 2.1/DeepSWE 1.1 是**不同 benchmark**，無法直接對等。

### 第二大腦發現（帶 URL 與信任層級）

| 發現 | 內容 | GitHub URL | 信任層級 | 時間 |
|---|---|---|---|---|
| LLM 成本立場 | 個人開發強烈推薦 Ollama Cloud；複雜推理/企業級才用 Anthropic/Codex | …/技術/技術評估/LLM降本增效.md | `human:fatesaikou`＋`stable` | 2026-05-01 |
| 模型選用分級（骨幹） | 高=建構約束 harness、中高=重要資料調查、中低=一次性程式碼；軸=錯誤擴散範圍 | …/抽象理解/本質洞察/技術取捨準則.md | `claude-code/opus-5`＋`draft`（未 review） | 2026-08-01 |
| 周限額基線 | **第二大腦無此主題**——50~80% 周限額、集中六日為使用者 R2 新給事實 | （搜尋無對應檔） | 無 | — |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 結果 |
|---|---|---|
| 多模態（問 2） | OpenRouter model card 交叉官方 blog（mp4 驅動建站 demo） | **有，多模態**；text/image/video/audio/PDF 入，text 出 |
| 牌價（問 1 基礎） | OpenRouter＋R1 pricing 交叉 | Standard $1.25/$4.25、Contributor $0.10/$0.20 確認 |
| 現役方案計費（問 1） | 官方 pricing | Claude Pro/Ollama Pro 皆**固定月費**，**周限額 token 數皆未公開** |
| 跨模型 benchmark（問 3） | 官方＋Artificial Analysis | Muse 居第 2 僅次 Opus 5；**與 deepseek-v4-flash 無同基準可比** |
| 判準承接 | mybrain-read | 拿到「Ollama 為主、高價為輔」「錯誤擴散範圍分級」；**周限額數字無既有紀律** |
| 價格數值可計算性 | 檢核官方來源 | **無法從官方直接換算 token 量** → 需自設假設，報告中明示 |

## 其中的決斷點

| 決斷面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| C1 資料來源 | 假設 GitHub repo 抓 metadata vs 認作商業產品走 docs | **走官方 docs＋OpenRouter model card** | 無 repo 可抓；R2 三問皆需一手定價/模態/benchmark 文件 |
| 價格換算基線 | 用官方周限額 token 數（不存在） vs 自設 token 量假設 vs 只給牌價 | **自設 token 量假設＋明示限制** | 官方不公開周限額 token 數，但 R2 要「可比較的數值」；只能以明示假設的敏感度表給出數值，並標註這項限制 |
| Claude Pro 月費 | 用使用者所報 $22 vs 官方 $20 | **兩者並列，主用官方 $20、標註使用者實際 $22** | 官方現行價 $20，使用者自述 $22；避免硬指正，但需以官方數字為可引用基準 |
| deepseek-v4-flash 對照 | 硬套同表 vs 明示無同基準 | **明示不同 benchmark 無法對等** | DeepSeek 報 Terminal-Bench 2.0，Muse 報 2.1/DeepSWE 1.1，不同基準不可直接比較 |
| 後續 C2 分工 | 一次收斂 vs 拆 C2 算價格、C3 收 benchmark | **C2 收斂全部三問成報告** | 三問資料已足夠；不需再拆 sub-step，直接進收斂撰寫 |
