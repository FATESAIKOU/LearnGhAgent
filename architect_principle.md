# 程式架構規範

## 各節點的職責定義

強調「**main / node / lib 不可越權**」

## 1. `main_learn-tech.py` 的責責

只負責：

* setup
* orchestration
* transition control
* 每輪結束後呼叫 comment / commit
* teardown

**不得做：**

* prompt 細節組裝
* LLM 呼叫細節
* review 判定細節
* GitHub comment 內容生成細節

也就是說，`main` 只知道：

> 現在輪到誰、跑完結果是什麼、下一步去哪。

---

## 2. `node_base.py` 的責責

只負責定義：

* node metadata
* prompt building 共通骨架
* `run(state)` 介面
* 共通 logging helper
* 共通 output normalization helper

**不得做：**

* 直接寫死 workflow transition
* 直接操作 git / github
* 直接決定整體 orchestration

---

## 3. 各 `node_n_xxx.py` 的責責

只負責：

* 該節點自己的 prompt 組裝補充
* 該節點自己的 LLM 呼叫 / 固定邏輯
* 該節點自己的輸出解析
* 該節點自己的 status 判定

**不得做：**

* 決定下一個節點是誰
* 直接 git push / gh comment
* 改整體 workflow 規則

---

## 4. `lib/state.py` 的責責

只放：

* `State` 結構
* state clone / append helper
* state serialization

**不得做：**

* prompt build
* LLM call
* git / github 操作

---

## 5. `github_helper.py` 的責責

只負責：

* 讀 issue
* 讀 comments
* 寫 comment
* 將 state 中與審查有關內容轉成漂亮 markdown

**不得做：**

* 決定節點邏輯
* 決定 status
* 直接操作 git

---

# 建議的節點命名

你現在格式可以這樣固定：

```text
node_1_research_tech.py
node_2_define_mvp_scope.py
node_3_review_mvp_scope.py
node_4_implement_mvp.py
node_5_review_code.py
node_6_write_report.py
node_7_review_report.py
node_base.py
```

這樣有幾個好處：

1. **順序明確**
2. **職責明確**
3. **未來插新節點容易**
4. **Git commit title 很自然**

---

# 每個節點建議產出格式

這塊很重要，因為你後面要 comment 到 GitHub，還要做人審查。
所以我建議每個 node 的 output 都要是 **結構化 markdown**，不要只輸出散文。

---

## node_1_research_tech

**輸出格式建議**

```markdown
# Tech Research Result

## Problem Understanding
- ...

## Candidate Technologies / Approaches
1. ...
2. ...
3. ...

## Comparison
| Option | Pros | Cons | Complexity | Fitness for MVP |
|---|---|---|---|---|

## Recommended Direction
- ...

## Risks
- ...

## Assumptions
- ...
```

---

## node_2_define_mvp_scope

```markdown
# MVP Scope Definition

## Goal
- ...

## In Scope
- ...

## Out of Scope
- ...

## Functional Requirements
- ...

## Non-Functional Requirements
- ...

## Acceptance Criteria
- ...

## Implementation Notes
- ...
```

---

## node_3_review_mvp_scope

```markdown
# MVP Scope Review

## Review Result
- SUCCESS / NG / UNKNOWN / ERROR

## Findings
- ...

## Missing / Over-scoped / Inconsistent Points
- ...

## Required Fixes
- ...
```

---

## node_4_implement_mvp

```markdown
# MVP Implementation Result

## Implemented Files
- ...

## Main Design Decisions
- ...

## Remaining Gaps
- ...

## README Coverage
- ...
```

---

## node_5_review_code

```markdown
# Code Review Result

## Review Result
- SUCCESS / NG / UNKNOWN / ERROR

## Scope Coverage
- ...

## Code Quality Findings
- ...

## Required Fixes
- ...

## README Findings
- ...
```

---

## node_6_write_report

```markdown
# Development Report

## What Was Researched
- ...

## Chosen MVP Scope
- ...

## What Was Implemented
- ...

## How to Run
- ...

## Known Limitations
- ...

## Next Steps
- ...
```

---

## node_7_review_report

```markdown
# Report Review Result

## Review Result
- SUCCESS / NG / UNKNOWN / ERROR

## Completeness Check
- ...

## Consistency Check
- ...

## Missing Information
- ...

## Required Fixes
- ...
```

---

# 無限迴圈防止
在 get_node 時，一但以相同條件嘗試取得 node 超過三次時就直接變成 END

---

# GitHub comment 的建議格式

你要求「好看的方式」，那我建議每個節點 comment 都固定模板。

````markdown
## Workflow Update - node_4_implement_mvp

- Status: SUCCESS
- Issue: #123
- Branch: feature/learn-x
- Node: node_4_implement_mvp

### Node Objective
- Implement MVP code based on approved scope

### Input Summary
- ...
- ...

### Output Summary
- ...

### Full Output
```md
...
````

---

# 我建議的 review rubric

這個很值得直接寫進 node constraints。

## node_3_review_mvp_scope rubric

* 是否明確對應 issue 目標
* 是否可在 MVP 時間/規模內完成
* in-scope / out-of-scope 是否清楚
* acceptance criteria 是否可驗證
* 是否與技術調查結論一致

## node_5_review_code rubric

* 是否覆蓋 scope
* 是否有明顯未完成 stub
* README 是否足夠執行
* 專案結構是否合理
* 是否有不必要過度設計

## node_7_review_report rubric

* 是否完整描述研究、scope、實作、限制
* 是否與實際程式碼一致
* 是否足夠讓第三者理解
* 是否能支持後續擴充或重做
