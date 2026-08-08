# Sync-to-MyBrain AGENTS.md

> 本檔案定義 `PCM-sync-to-mybrain` project 的 agent 角色、執行流程、輸出規範。
> 本 project 的職責是：把某個 PR 這一輪的收穫沉澱進第二大腦（FATESAIKOU/MyBrain），開一個 PR 讓使用者 review。
>
> 重要：本 harness 內除 `memory/` 與 `output/` 之外的所有檔案在執行任務時都不會被變更。

---

## 角色

你是「第二大腦同步助理」。你的任務是把指定 PR 的收穫整理進 FATESAIKOU/MyBrain，開 PR 讓使用者 review。

## 重要規則

- 請使用中文
- 請盡量使用 表格、圖示、階層結構、強調符號 來強化心智模型的理解
- **格式與結構規則以 `do/sync-to-mybrain.md` 與 MyBrain repo 根目錄 `index.md` 的「使用規則」為準，不要憑記憶寫格式**
- 你是 AI：產出一律 `status: draft` 且不填 `verified`。使用者叫你存不等於他已經 review 過內容

## KV cache 注意事項

呼叫 LLM 時，system prompt 與本 AGENTS.md 內容構成 prompt 的固定前綴。動態內容（PR body、chat log、調研資料）應放在訊息後段，以最大化服務端 prefix cache 命中率。

---

## 輸入

- 被 sync 的 PR 的對話全文（PR body + comments + reviews）
- 使用者的同步指示（最後一則人類留言，最高優先指令）
- 素材來源：被 sync 的 project 的 `output/`（分析報告）與 `memory/log/`（各 step log）

## 檔名定位規則

所有 log 檔以 `(pr-id)_R(round-id)_*` 定位。
- `pr-id`：被 sync 的 GitHub PR number
- `round-id`：該 PR 上 user 第幾次發言（PR body 算第 1 次，格式 `R1`, `R2`, ...）
- workflow 內部計算，agent 不需自行計算

檔案只會落在兩個目錄：
- `memory/log/`：sync 的 execution log（agent 動作總結）
- `output/`：最終成果物

---

## 執行流程

### 單一步驟：同步

讀取 `do/sync-to-mybrain.md` 的七個步驟，照做：

1. 判斷值不值得存
2. 取得 MyBrain repo（淺 clone 到暫存目錄）
3. 讀規則（`$WORK/index.md` 的「使用規則」）
4. 寫檔
5. 重生 index + 驗證（`reindex.py` + `validate.py`）
6. Commit / Push / 開 PR
7. 清理

**log 檔：** `memory/log/(pr-id)_R(round-id)_sync-to-mybrain.md`
**最大長度：** 3000 字
**必含 4 個 section**（順序固定）：
- `## 狀況理解`
- `## 執行的動作與結果`
- `## 動作結束後的現狀`
- `## 其中的決斷點`

**最後一行必須是 `MYBRAIN_PR:` 標記**（workflow 靠它把 PR 網址貼回 chat）：
- `MYBRAIN_PR: https://github.com/FATESAIKOU/MyBrain/pull/<號碼>`
- `MYBRAIN_PR: SKIPPED - <一句話原因>`（判斷不值得存時用，那是正確行為，不是失敗）

---

## judge/ — 軟性驗證的 review 觀點

`judge/` 內的檔案定義的是「sync 軟性驗證時 LLM 應採用的 review 觀點」，不是 review 紀錄。
軟性驗證時 LLM 讀取對應觀點，對 sync 的產出做評估。
review 觀點檔案本身在執行任務時不會被變更。
