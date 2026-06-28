# 85_R1_step2-plan_C1.md

## 狀況理解

Step 1 已從 Issue #84 解析出三個核心參數：project_name = `02-news-catchup`、description = 每日抓取科技新聞網站分析趨勢產出摘要報告、role = 新聞分析助理。本 step 需據此建立完整 project 骨架。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 建立 `projects/02-news-catchup/` 目錄結構 | 建立 harness 骨架 | know/judge/do/memory/output/guardrail 目錄就緒 | 8 個子目錄全部建立成功 |
| 撰寫 `know/AGENTS.md` | 定義 agent 角色與 4 step 流程 | 新聞分析助理角色明確，含摘要報告格式規範 | 已產出，角色為「新聞分析助理」，報告格式改為新聞摘要專用（§1 本日新聞摘要、§2 趨勢分析、§3 來源分布統計、§4 值得關注項目） |
| 複製 `know/我.md` | 提供使用者 persona | agent 了解使用者偏好 | 從 P01-general-tech 複製完成 |
| 複製 `opencode.json` | LLM 設定 | 指向 know/AGENTS.md + know/我.md | 複製完成，instructions 路徑正確 |
| 複製 `validate.sh` | 硬性驗證腳本 | 支援 step-log/report 驗證 | 複製完成，report 檔名規則改為 `(pr-id)_(YYYY-MM-DD).md` |
| 建立 `judge/` 4 個 review 觀點 | 軟性驗證標準 | 各 step 有對應的 review 觀點 | 已依新聞分析特性調整（如 step1 強調新聞來源明確性、step3 強調來源分布統計） |
| 建立 `do/skills/news-fetch/SKILL.md` | 定義新聞抓取方法 | agent 有標準化抓取流程 | 已產出，含 Hacker News API、TechCrunch RSS 等來源方法 |
| 建立 `.gitkeep` 檔 | 保留空目錄 | memory/log/ output/ guardrail/ 可被 git 追蹤 | 3 個 .gitkeep 已建立 |
| 建立 `.github/workflows/P02-news-catchup.yml` | 定義 CI/CD workflow | 可被 watch workflow 觸發執行 | 從 P01-general-tech.yml 複製修改，label 改為 `project:02-news-catchup`、PROJECT_DIR 改為 `projects/02-news-catchup`、CHATLOG 路徑更新 |
| 複製 `chatlog.py` | 提供 chat log 工具 | workflow 可解析 PR 對話 | 從 P01-general-tech/scripts/ 複製完成 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 目錄結構完整性 | 檢查 `projects/02-news-catchup/` 下所有必要目錄 | 8 個目錄全部存在 |
| 核心檔案存在 | 檢查 know/AGENTS.md、know/我.md、opencode.json、validate.sh | 4 個核心檔案全部存在 |
| judge 檔案存在 | 檢查 judge/ 下 4 個 review 觀點 | 4 個檔案全部存在 |
| skill 檔案存在 | 檢查 do/skills/news-fetch/SKILL.md | 已存在 |
| workflow 檔案存在 | 檢查 `.github/workflows/P02-news-catchup.yml` | 已存在 |
| chatlog.py 存在 | 檢查 `.github/workflows/P02-news-catchup/scripts/chatlog.py` | 已存在 |
| .gitkeep 存在 | 檢查 memory/log/ output/ guardrail/ 下的 .gitkeep | 3 個全部存在 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 報告 section 設計 | (a) 沿用 P01 的 4 個技術分析 section；(b) 重新設計為新聞摘要專用 section | (b) 重新設計 | 新聞分析與技術分析的輸出格式完全不同，需有新聞摘要、趨勢分析、來源分布等專用 section |
| report 檔名規則 | (a) `(pr-id)_(技術名).md`；(b) `(pr-id)_(YYYY-MM-DD).md` | (b) 日期格式 | 新聞報告以日期為 key，非技術名 |
| skill 命名 | (a) 沿用 document/；(b) 新建 news-fetch/ | (b) news-fetch/ | 新聞抓取是獨立 skill，與 document 調研 skill 不同 |
| workflow label | (a) `project:02-news-catchup`；(b) `project:news-catchup` | (a) 含序號 | 與 project 資料夾名稱一致，便於 watch workflow 對應 |
