# 個人先端技術研究 workflow

## 背景

每天自己讀，自己 catchup，自己內化文章跟新技術實在太累了。
想要利用AI建構workflow後，加速自己的學習速度
※ 必須使用 x0 的 raptor mini 做所有 llm node 的基底

## 目的

開發一個 ai workflow, 它可以根據被給定的

- github 學習 Repo 的issue id(數字)
- branch name

輸出

- MVP程式碼
- 程式碼Readme
- 開發紀錄(一個節點一個 issue comment)

## 限制

- workflow 要整個包在 docker 裡面跑，然後透過 launch_workflow_learn-tech.sh <issue_id> <branch_name> 一發啟動
- issue 跟 branch 都是預先在雲端建, docker 內只需要 git clone, git checkout, gh read, gh add comment
- 程式架構採用 main + node 的格式，詳細結構如下
    ```markdown
    - scripts
        - launch_workflow_learn-tech.sh
    - src
        - main_learn-tech.py (在這裡做 orchestration)
        - nodes(實際每個 node 做的事情)
            - node_1_xxx.py
            - node_2_xxx.py
            - ...
            - node_n_xxx.py
            - node_base.py
        - lib
            - state.py
            - github_helper.py
            - git_helper.py # 這就不寫範例了
    - workenv
        - learn-tech
            - Dockerfile
            - docker-compose.yml
    ```
### 虛擬碼
程式碼職責必須嚴格遵守以下，避免 main / node / lib 踰越職責範圍，我們要重視一個檔案的職責不會擴張
(相同類型的職責可以追加，但不同類型得職責則不得擴張)
```python
# main_xxx.py

def setup(issue_id, branchname):
    # clone git repo
    # git checkout git branch
    # remove git origin to prevent unexcepted write
    # initialize state

def teardown():
    # add git origin
    # git push

def get_node(from_node, status):
    transfer_matrix = [
        ('node_1_xxx', 'SUCCESS'): 'node_2_xxx',
        ('node_1_xxx', 'ERROR'): 'END',
        ('node_1_xxx', 'UNKNOWN'): 'node_1_xxx',
        ('node_2_xxx', 'SUCCESS'): 'node_3_xxx',
        ('node_2_xxx', 'NG'): 'node_1_xxx',
        ...
    ]

    ...


def main(issue_id, branchname):
    state: State = setup(issue_id, branchname)

    while next_node = get_next_node(state) != END:
        state = next_node.run(state) # 其中 status 有 SUCCESS NG ERROR UNKNOWN 三種
        GithubHelper.comment(issue_id, state)
        GitHelper.commit(state) # 總之把 node name 當 title 直接 commit(允許 empty commit)

    teardown(state, issue_id, branchname)
```
```python
# node_base
class NodeBase:
    # 成員變數 node_name
    # 成員變數 role
    # 成員變數 targets
    # 成員變數 constraints
    
    # 成員函數 build_prompt
    def build_prompt(issue_title, issue_body, issue_comments, workflow_output_histories) {
        return xxx # 格式如下
        """
        - issue
            - title: {issue_title}
            - body: {issue_body}
            - comments
                - {issue_comments}
        - workflow_progress
            - {workflow_output_histories}
        - node_instructions
            - role: {role}
            - targets
                - {targets}
            - constraints
                - {constraints}
        """
    }

    # run 核心函數的介面定義
    def run(state)
```
```python
# node
class Node_n_xxx: 
    # override
    def run(state):
        new_state = clone(state) # deep copy?
        new_state.from_node = self.node_name
        new_state.status = "UNKNOWN"

        ## 呼叫 llm 的話是這狀況，但如果是固定程式碼那就是寫固定程式碼，但是 input/output 要用類似的方式整理，並且要用相同方式維護 state
        input_prompt = self.build_prompt(state.issue_title, state.issue_body, state.issue_comments, state.workflow_output_histories)
        output = subprocessxxxx. gh copilot {input_prompt} # 單發啟動 開啟所有 logging(包含 fucntion, mcp, thinking 調用) 包含正常輸出全部搞出來

        new_state.workflow_input_histories.append((self.node_name, input_prompt))
        new_state.workflow_output_histories.append((self.node_name, output))
        new_state.status = # 客製化的判定邏輯
```
```python
# state.py
class State:
    # 成員變數 issue_id: int
    # 成員變數 branch_name: str
    # 成員變數 issue_title
    # 成員變數 issue_body
    # 成員變數 issue_comments
    # 成員變數 from_node
    # 成員變數 workflow_input_histories
    # 成員變數 workflow_output_histories
    # 成員變數 status
    # 成員變數 repo 的路徑 -> local_repo_path: str
    # retry_per_edge_cnt: [tuple(str(from_node_name), str(status)), int], 每個 edge 的 max 定義在 get_node 即可
```

```
```python
# github_helper.py
class GithubHelper:
    def comment(issue_id, state):
        ## 根據 issue_id, 把「這個 node 的input/output以及相關前提」以「好看的方式」comment回去github，給人審查
```

## 設計方案

### Workflow 定義表
| Node ID                 | 階段名             | 目的                                      | 是否使用 LLM | 主要輸入                                     | 主要輸出               | SUCCESS                 | NG                      | UNKNOWN                 | ERROR |
| ----------------------- | --------------- | --------------------------------------- | -------- | ---------------------------------------- | ------------------ | ----------------------- | ----------------------- | ----------------------- | ----- |
| node_1_research_tech    | 技術調查            | 根據 issue 主題整理相關技術、做法、候選方案、風險與建議方向       | 是        | issue title/body/comments、既有 workflow 紀錄 | 技術調查報告             | node_2_define_mvp_scope | -                       | node_1_research_tech    | END   |
| node_2_define_mvp_scope | MVP scope 決定    | 根據技術調查結果收斂 MVP 邊界、功能、非功能需求、驗收條件         | 是        | 技術調查結果、issue 內容                          | MVP scope 定義       | node_3_review_mvp_scope | -                       | node_2_define_mvp_scope | END   |
| node_3_review_mvp_scope | 審查 MVP scope    | 檢查 scope 是否過大、過小、不一致、不可實作、驗收條件不足        | 是        | MVP scope、技術調查結果、issue 內容                | scope review 結論    | node_4_implement_mvp    | node_2_define_mvp_scope | node_3_review_mvp_scope | END   |
| node_4_implement_mvp    | 實現程式碼           | 依 scope 實作 MVP 程式碼與基本專案檔案               | 是        | 已審查通過的 MVP scope、技術調查結果                  | MVP code、README 初稿 | node_5_review_code      | -                       | node_4_implement_mvp    | END   |
| node_5_review_code      | 審查程式碼           | 檢查程式碼是否符合 scope、結構、可讀性、可執行性、README 是否足夠 | 是        | code、README、scope、技術調查結果                 | code review 結論     | node_6_write_report     | node_4_implement_mvp    | node_5_review_code      | END   |
| node_6_write_report     | 撰寫開發報告以及程式碼內容報告 | 將研究、scope、實作、使用方式、限制與後續方向整理成報告          | 是        | 技術調查、scope、code、README、review 結果         | 開發報告 / 程式碼報告       | node_7_review_report    | -                       | node_6_write_report     | END   |
| node_7_review_report    | 審查報告            | 檢查報告是否完整、與程式碼一致、是否足夠讓人審查與接手             | 是        | 報告、code、README、scope、研究結果                | report review 結論   | END                     | node_6_write_report     | node_7_review_report    | END   |
