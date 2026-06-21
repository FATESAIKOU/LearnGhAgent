有問題 請修正

1. 最終output的黨名不是基於日期 是 (pr id)_(技術名).md
2. 我不想讓抽取技術名變成一個共通script, 技術抽取讓 LLM 自己判斷就行，反正輸入就是使用者的自由文 body
3. judge/review_(step-id).md 裡面寫的是給各 step 的 soft validate 執行時的 review 觀點... 不是 review 紀錄
4. 基本上除了 memory/output 之外 所有 harness 要素都不會在執行任務(01-general-tech.yml)時被更動
5. memory/log 中應該是 一個 step(意圖理解, 執行計劃, 品質保證, 總結) 一個 md, 不是包含 LLM 的產出詳細內容, 而是 LLM 執行這階段任務時自己的動作總結, 格式就是下面這個，所有 workflow 都一樣
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

6. 不要寫 post-log.sh 這種外部 script
7. post log 就是直接把 memory/log 的 每個 step 的 log 照順序用 gh 丟上 pr chat
8. PR body 的留言者跟之後丟上去的 step log 要做區分，我想法是直接讓 pr body 留言者是 user，這樣好區分


所以請你照這順序做
1. 刪除 pr, branch
2. 改各種程式 push 上去
3. 重跑 create pr
4. (等)重跑 01-general-tech.yml
