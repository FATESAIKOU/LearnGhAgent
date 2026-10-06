# 279_R2_step3-qa.md

## 狀況理解

R2 為 QA 追問輪。使用者在 R2 揭露真正目的為「建立 AI 公司」，並提三組質問：Q1 AX 是否內含（a）產出持久化（AiStorage 概念）（b）worker 間通訊手段；Q2 AX 與 herdr 的差別；Q3 AX 有無「AI 團隊運作」概念。

R2 Step 1 已完成意圖理解與 MyBrain 座標檢索；Step 2（C1）已取得 AX code／Substrate 契約／herdr 官網／官網事實，並得出四項判定。Step 3 任務＝把本輪沉澱進 `output/279_ax-agent-executor.md` 的 `## 5. User Q&A`，並依 AGENTS.md §5 規則補強 §4 對照與衝突，最後執行硬軟驗證。既有 QA 不存在，本輪為首次寫入 §5。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀既有報告 `output/279_ax-agent-executor.md` | 確認 §1–§4 與是否已有 §5 | 沿用檔名、不刪既有 | 讀完 347 行；無 §5，§4.2 止於 4.2.4 |
| 執行 mybrain-read：refresh 鏡像至 `530133b` | 取骨幹與最新判定 | 對照他的座標 | 成功；grep 骨幹 tag 得 11 檔 |
| 讀骨幹 `判定總表`、`技術取捨準則`、`專案現況表`、`下一步清單` | 取替代方案判定與採納閘門 | §4 帶 URL 與信任層級 | 判定總表 118 筆；閘門＝能否影響個人 workflow |
| 讀 `AiStorage`、`MyLinuxPool`、`AIContainer`、`個人 AiAgent 入口`、`herdr 配置`、`AI開發workflow實測`、`munder-difflin`、`統一的兩端稅` | 取 Q1–Q4 的對照座標 | 逐題可引他的判準 | 全命中，附 URL 與 `draft` 標記 |
| 追加 §4.2.5「AI 公司這條線的既有座標」 | 補齊本輪新座標 | 與既有 4.2.1–4.2.4 不衝突 | 新增 5 列；並在 4.2.1 補 herdr／AiStorage 兩列 |
| 追加 §4.3 小結 2 列（AI 公司／herdr 兩列） | 定位缺口層 | 指向自建層 | 完成 |
| 追加 `## 5. User Q&A`（Q1–Q4） | 沉澱本輪三問（Q1 拆 a／b） | 符合 §5 規則 | 4 則 QA；Q4 含 3 項衝突表 |
| 硬性驗證 `judge/validate-report.sh` | 檢查長度、4 section、檔名 | 格式合規 | PASS；25144 字 < 50000 |
| 軟性驗證（依 `judge/step3-qa.md` 7 項自評） | 內容品質檢核 | 找問題點 | 見下 |

軟性驗證自評：

| 項目 | 結果 | 備註 |
|---|---|---|
| 1. 4 section 齊全 | PASS | §1–§4 保留，新增 §5 |
| 2. DA 表完整 | PASS | §4.1 四替代五欄齊全，未動 |
| 3. 語言合規 | PASS | 中文；避開比喻與模糊用詞 |
| 4. 結構化呈現 | PASS | 通訊方向圖、層級圖、多張對照表 |
| 5. 反面論證 | PASS | Q3 反證表、Q4 衝突表、附錄 A 校正表 |
| 6. 檔名與長度 | PASS | 沿用 `279_ax-agent-executor.md`；25144 字 |
| 7. 第二大腦對照 | PASS | §4.2.5 每則帶 URL 與信任層級；`process:learn-gh-agent` 註明未 review；查不到明寫；Q4-C1/C2/C3 明列衝突 |

## 動作結束後的現狀

**產出的報告檔名**：`output/279_ax-agent-executor.md`（沿用 R1，未改檔名）

**本輪變更摘要**：
- 新增 `## 5. User Q&A`：Q1 持久化（AX 無資料層，四面向逐項對照 AiStorage）、Q2 worker 通訊（四方向表＋default-deny T-17）、Q3 herdr 差別（不同層、反證表）、Q4 AI 團隊（AX 有任務無職務＋3 衝突）
- 新增 `#### 4.2.5`「AI 公司」既有座標（munder-difflin／AIContainer／入口／統一的兩端稅／技術取捨準則）
- `#### 4.2.1` 補 herdr、AiStorage 兩列；`### 4.3` 補 2 列
- §1–§3、§4.1、附錄 A／B 未刪未改；鏡像 hash 由 `d2aeff7` 更正為 `530133b`
- 無既有 QA 可衝突，新 QA 由 Q1 起算

**驗證結果**：

| 驗證面向 | 內容與方式 | 結果 |
|---|---|---|
| 報告硬性驗證 | `bash judge/validate-report.sh` | PASS |
| 報告長度 | 25144 字 | < 50000 |
| section 齊全 | grep `## 1.`～`## 4.`＋`## 5.` | PASS |
| 既有內容完整 | diff 確認 §1–§4 原文保留 | PASS |
| step log 格式 | 4 section；`bash judge/validate-step3.sh` | PASS（2885 字 < 3000） |

## 其中的決斷點

| 意思決定面向 | 可選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| §5 章節位置 | 置於 §4 之後附錄之前／報告末尾 | §4 與附錄之間 | AGENTS.md §5 明文指定位置 |
| Q1 拆分 | 合併為一題／拆 a 持久化、b 通訊 | 拆兩題 | 規則「子問題不可合併」；兩者屬不同問題域 |
| 衝突呈現位置 | 集中於 §4.2.3／散在對應 QA | 散進 Q4 內 | 使用者此輪問的是「有沒有」，衝突須緊貼該結論才可讀 |
| 第二大腦引用深度 | 只引結論／附 URL＋信任層級＋衝突 | 後者 | judge 第 7 項明訂；`process:learn-gh-agent` 須標未 review |
| 報告既有段落處理 | 更新既有內容／僅追加 | 僅追加＋一處 hash 更正 | AGENTS.md 規定既有內容不可刪改 |
| Q3 對比軸 | 效能數據／層級定位 | 層級定位 | herdr 為不同層，效能對比無意義 |
