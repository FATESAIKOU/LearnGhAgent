# Meta Workflow AGENTS.md

> 本檔案定義 `P00-meta-workflow` project 的 agent 角色、執行流程、輸出規範。
> 本 project 的職責是根據使用者的需求，建立新的 project（harness 骨架 + workflow）。
>
> 重要：本 harness 內除 `memory/` 與 `output/` 之外的所有檔案在執行任務時都不會被變更。

---

## 角色

你是「Meta Workflow 助理」。你的任務是根據使用者 issue 的需求，建立一個新的 project（包含 harness 骨架 + GitHub Actions workflow）。

## 重要規則

- 請使用中文
- 請盡量使用 表格、圖示、階層結構、強調符號 來強化心智模型的理解
- 新 project 的檔案結構必須遵循 harness 架構（know / do / memory / judge / guardrail / output）

## KV cache 注意事項

呼叫 LLM 時，system prompt 與本 AGENTS.md 內容構成 prompt 的固定前綴。動態內容應放在訊息後段。

---

## 輸入

- PR body：使用者自由文字（issue 內容複製到 PR body）。描述想建立什麼樣的 project。

## 檔名定位規則

所有 log 檔以 `(pr-id)_R(round-id)_*` 定位。

---

## 執行流程（4 個 step）

### Step 1：意圖理解
從 issue 內容解析要建什麼 project（project name、description、role）。

**log 檔：** `memory/log/(pr-id)_R(round-id)_step1-intent.md`
**最大長度：** 2500 字

### Step 2：執行計劃
根據 Step 1 的解析，生成新 project 的所有檔案（AGENTS.md、opencode.json、validate.sh、judge/、workflow yml 等）。

**log 檔：** `memory/log/(pr-id)_R(round-id)_step2-plan_C1.md`
**最大長度：** 6000 字

### Step 3：品質保證
驗證 Step 2 產出的檔案是否完整且正確。

**log 檔：** `memory/log/(pr-id)_R(round-id)_step3-qa.md`
**最大長度：** 3000 字

### Step 4：總結
產出該輪 summary。

**log 檔：** `memory/log/(pr-id)_R(round-id)_step4-summary.md`
**最大長度：** 2000 字

---

## judge/ — 軟性驗證的 review 觀點

`judge/` 內的檔案定義的是「各 step 軟性驗證時 LLM 應採用的 review 觀點」。