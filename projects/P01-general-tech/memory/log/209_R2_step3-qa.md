# 209_R2_step3-qa.md

## 狀況理解

R2 為使用者「接近 Reject 前的最後追問」，三問皆質問型句構：①與其自建 MyBrain 在解決問題/方式上如何比較；②是否組織級知識庫、有無人 Review＋存取規則、效果如何；③誰規定 raw session 分層留取/排除、誰驗證、如何避免腐化。依 AGENTS.md，質問型句構觸發報告 §5 User Q&A。Step 2 C1 已補查官方治理細節（Skill review、ACL 四可見度、L0-L3 pipeline、ROADMAP 自承單一硬編碼 prompt 瓶頸、無 dedup/回滾）。本 step 任務：把 R2 三問構造化為 §5 QA 追加進既有報告，並對照第二大腦既有機制（MyBrain 人 Review/存取規則/腐化防護）撰寫，產出 step3 log。

## 執行的動作與結果

| 動作 | 目的 | 預期效果 | 實際結果 |
|------|------|----------|----------|
| 讀取既有報告 209_TencentDB-Agent-Memory.md | 承接 R1 內容，不刪改 | 確認 §1-§4 可保留、無 §5 | R1 報告 4 節齊全，無 §5 Q&A |
| 讀取 209_R1_step3-qa.md | 掌握 R1 驗證標準與變更摘要 | 承接硬/軟驗證基準 | 確認 validate-report.sh 規則（<50000字、4節、檔名） |
| mybrain-read（refresh + 讀 技術取捨準則、判定總表、專案現況表、追加功能/mybrain-read） | 對照使用者既有 MyBrain 機制與判準 | 正確比較 MyBrain vs TencentDB、確認 Review/存取/腐化防護模型 | 取得：MyBrain 個人級、PR 人 review、唯讀鏡像/寫入僅本人、append-only+CI 防腐化 |
| 撰寫 §5 User Q&A（Q1/Q2/Q3） | 構造化回答 R2 三問 | 追加 QA，既有 QA 不刪改 | 完成 3 個 QA 條目（Q1 比較、Q2 Review/存取規則、Q3 分層/驗證/腐化） |
| 執行 validate-report.sh | 硬性驗證 | 確認格式合規 | OK: report valid（26,219 字 < 50000） |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 驗證結果 |
|----------|---------------|----------|
| 報告檔名 | 沿用 R1 `209_TencentDB-Agent-Memory.md` | 通過（未改檔名） |
| 報告長度 | validate-report.sh 測量 26,219 字 | 通過（< 50000） |
| 4 個 section | §1-§4 存在且未刪改 | 通過 |
| §5 位置 | 位於 §4 與附錄之間 | 通過 |
| QA 序號 | Q1/Q2/Q3 按序遞增 | 通過 |
| QA 觸發 | R2 三問皆質問型句構 | 通過 |
| 第二大腦對照 | Q1/Q2/Q3 皆對照 MyBrain 機制，帶信任層級（human:fatesaikou/stable、技術取捨準則為 claude-code/opus-5 draft） | 通過 |
| 語言合規 | 中文、無比喻/情緒/模糊用詞 | 通過 |
| 反證/對照表 | Q1 雙向對照表、Q2 Review 覆蓋對照表、Q3 腐化防護對照表 | 通過 |

**本輪變更摘要**：`output/209_TencentDB-Agent-Memory.md` 新增 §5 User Q&A 三條（Q1-Q3）。Q1 對照 MyBrain 個人級 vs TencentDB 團隊級，結論兩者不構成競爭、非同一層級；Q2 確認存取規則（ACL 四可見度/雙層角色/ownership/private 預設）完整，但人類 Review 僅覆蓋 Skill 一層，Chat Memory/Wiki/CodeGraph 無同等強制人閘門；Q3 確認分層由單一硬編碼 LLM prompt 決定、無人類規則、無獨立驗證閘門、文件無 dedup/衝突合併/回滾，ROADMAP 自承單一 prompt 是品質瓶頸且未支援面板編輯，與 MyBrain 的 append-only+CI 防腐化模型不對等。§1-§4 與附錄保留未刪改，附錄補列 ROADMAP 來源。

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 理由 |
|----------|----------|----------|------|
| R2 定位 | 併入 §5 Q&A / 重寫報告 | §5 Q&A | 三問為質問型句構，依 AGENTS.md 構造化追加；既有 QA 不可刪改 |
| QA 拆法 | 三問合一條 / 每問一條 | 每問一條（Q1/Q2/Q3） | AGENTS.md 規定同輪多子問題拆多條獨立 QA |
| Q2 判準 | 宣稱「無人 Review」/ 精確到「只 Skill 一層有」 | 只 Skill 一層有 | 根 README 明列 Skill 需 review 才 team 分享，Chat Memory/Wiki/CodeGraph 未見——如實分層，不整包否定 |
| 是否更新 §4 | 保留 R1 §4 / 重寫 | 保留 | R1 §4 已對照第二大腦與 EverOS 衝突，內容仍成立；R2 屬追問非新標的，避免重做 |
| 附錄 | 保留原列 / 補 ROADMAP | 補 ROADMAP | Q3 關鍵證據（單一 prompt 瓶頸、面板未支援）來自 ROADMAP，須列入來源 |
