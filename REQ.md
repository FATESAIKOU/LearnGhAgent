## 目標

我需要你幫我寫一個基於 github / github actions 的 Agent 工作流控制台

我需要這個工作流是足夠泛用的，也就是

1. 創建工作流的工作流
2. 各種單一任務工作流
    - 典型工作流1. 每天抓新聞網站，分析，產出報告 → 接受我的QA & 把QA沉澱到報告(loop)
    - 典型工作流2. 我給定一個github連結(或技術名), 分析 & 產出報告 → 接受我的QA & 把QA沉澱到報告(loop)
    - 典型工作流3. 我給定一個技術跟需求, 分析 & 設計 & 開發 & 測試 & 產出可運行程式碼 → 接受我的 QA → 接受我的QA & 把QA沉澱到報告(loop or 重新回到需求分析與開發)

## 背景

現有的 llm web chat 服務跟 local cli Agent 全都沒辦法符合我的需求，這兩個應用對我來說都是一個指令一個動作。
我現在需要一個我登錄issue, agent 全自動運行，然後最後把結果輸出給我等 review 的全自動工作流模式。

## 詳細需求

### userflow
我想像的標準 user flow 如下

1. (user) 創建 github issue
2. (自動 or user) 啟動 github actions workflow(只創建 PR)
    - 創建 github pr
        - PR message = github issue 的內容複製到
        - branch 名 = (workflow-typename)_(issue-id)
3. (自動 or user) 啟動 github actions workflow(負責執行任務)
    - 判定是否有需要執行的 pr (條件就是 「open 的 pr」&「帶有對應必要tag」&「最後一個 pr chat/messag 是從 user 來的」)
    - 執行工作流(loop)
        - 給每一步(step(n)) 構建 prompt (參考 pr message/chatlog, memorylog 後構建, 每個 workflow 可能不壹樣)
        - 執行 step(n) 定義
        - 每一步軟性驗證(用 LLM 驗證成果, 可選)
        - 每一步硬性驗證(用確定性程式驗證輸出格式 輸出長度, 必選)
        - 登錄每一步總結報告到 github pr
4. (user) 觀看 PR chat log/file change -> 選擇 merge 或者追問(To 3.)

我想像的 user flow 有以下這些

- 創建工作流: 創造一個工作流(包含配套的 github actions workflow 跟 harness dir)
- 更新工作流: 更新一個既有工作流(包含配套的 github actions workflow 跟 harness dir)
- 創建工作: 基於現有工作流執行新工作
- 接續工作: 基於現有工作繼續執行一次工作流

## 成果物

- root dir
    - LLM 相關設定
    - 負責建立 project dir
    - 負責更新維護整體 project
- project dir(example)
    - 參考用檔案夾結構(harness)
        - know
            - AGENTS.md
            - 我.md
        - do
            - mcp
                - software implement
                - secret
            - skills
                - document
                - secret
        - memory
            - log
                - (issue-id)_req.md
                - (issue-id)_execution-log_(step-id).md
                - (issue-id)_summary_(round-id).md
        - judge
            - review_(step-id).md
        - guardrail
            - 一旦なし
        - output
            - 成果物格納
    - 參考用 AGENTS.md
    - 參考用 github actions workflow
        - 意圖理解
        - 執行計劃
        - 品質保證
        - 總結
        - ※ 每個 flow 都有硬性輸出規定(用確定性程式驗證)
            - 最大 message 長度限制
            - message 結構限制

## 追加情報

- 我打算使用 Ollama Cloud 的訂閱做底層 LLM 服務提供商
    - 我會給你 API token 以及 default model name
    - 但需要可以在 workflow step 動態選擇 model
- 我打算用 opencode 做最底層的執行模組

## 執行步驟

我需要你按照以下步驟執行

1. 建立基本 LLM 調用環境，在 Local 端做測試(輸出 hello world 即可)
2. 加上驗證用 github actions workflow 純手動啟動, 驗證可以在 github action 可以執行 opencode 並連接上 ollama cloud
3. 參考 /Users/fatesaikou/testAI/Learning-grp/Learning/01_general_tech 建立一個可以跑的 workflow(你要重構資料夾內容跟指示 變成符合我定義的 harness 架構) (也就是一個 project)
4. 把 3. 的 harness 跟 workflow 放上 github, 連接上 github issue/github pr new chat 觸發
5. 我來丟github issue測試 4. 的觸發狀況
6. 建立 root(也就是可以建立 project 的 workflow)
7. 把 root workflow 丟上 github, 連接上 github issue/github pr new chat 觸發
5. 我來丟github issue測試 7. 的觸發狀況
