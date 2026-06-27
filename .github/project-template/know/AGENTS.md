# {{PROJECT_NAME}} AGENTS.md

> 本檔案定義 `{{PROJECT_NAME}}` project 的 agent 角色、執行流程、輸出規範。
> {{PROJECT_DESCRIPTION}}
>
> 重要：本 harness 內除 `memory/` 與 `output/` 之外的所有檔案在執行任務時都不會被變更。

---

## 角色

{{PROJECT_ROLE}}

## 重要規則

- 請使用中文
- 請盡量使用 表格、圖示、階層結構、強調符號 來強化心智模型的理解

## KV cache 注意事項

呼叫 LLM 時，system prompt 與本 AGENTS.md 內容構成 prompt 的固定前綴。動態內容應放在訊息後段，以最大化服務端 prefix cache 命中率。

---

## 輸入

- PR body：使用者自由文字（issue 內容複製到 PR body）。LLM 自行從中判斷任務標的。

## 檔名定位規則

所有 log 檔以 `(pr-id)_R(round-id)_*` 定位。
- `pr-id`：GitHub PR number
- `round-id`：該 PR 上 user 第幾次發言（PR body 算第 1 次，格式 `R1`, `R2`, ...）

檔案只會落在兩個目錄：
- `memory/log/`：每個 step 一個 log（agent 動作總結，非詳細產出內容）
- `output/`：最終成果物

---

## 執行流程（4 個 step，每個 step 產一個 log）

每個 step 的 log 格式固定（所有 workflow 共通），記錄的是 agent 在該階段「自己的動作總結」：

```markdown
# <檔名>

## 狀況理解
<你對現狀與使用者回饋的理解>

## 執行的動作與結果
<表格：執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果>

## 動作結束後的現狀
<執行後驗證的現狀（表格：驗證的面向 | 驗證的內容與方式 | 驗證結果）>

## 其中的決斷點
<過程中的意思決定（表格：意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由）>
```

### Step 1：意圖理解
讀取 PR body，理解使用者要執行的任務與任何附帶條件。

**log 檔：** `memory/log/(pr-id)_R(round-id)_step1-intent.md`
**最大長度：** 2000 字

### Step 2：執行計劃
根據 Step 1 的需求，執行任務。可拆成多個 sub-step（C1, C2, ...）。

**log 檔：** `memory/log/(pr-id)_R(round-id)_step2-plan_(step-id).md`
**最大長度：** 6000 字

### Step 3：品質保證
產出最終成果物（落於 `output/`）+ step log。同時做軟性驗證。

**成果物：** `output/(pr-id)_(標的名).md`（標的名由 LLM 自行判斷決定）
**成果物最大長度：** 50000 字
**log 檔：** `memory/log/(pr-id)_R(round-id)_step3-qa.md`
**log 最大長度：** 3000 字

### Step 4：總結
產出該輪 summary。

**log 檔：** `memory/log/(pr-id)_R(round-id)_step4-summary.md`
**最大長度：** 2000 字

---

## judge/ — 軟性驗證的 review 觀點

`judge/` 內的檔案定義的是「各 step 軟性驗證時 LLM 應採用的 review 觀點」，不是 review 紀錄。
review 觀點檔案本身在執行任務時不會被變更。