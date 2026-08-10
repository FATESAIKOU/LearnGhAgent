# 212_R2_step2-plan_C1.md

## 狀況理解

R2 為 QA loop，使用者質疑 pdf-inspector 的定位與學習優先度（Q1 是不是解析框架、Q2 通用需求應選最穩定而非最快、Q3 這種抽象需求值不值得學）。C1 為 Step 2 第一個 sub-step，**針對 R2 意圖**取得 repo metadata 與主要文件，重點不在重述 R1 的功能細節，而在補齊「定位、穩定度、成熟度」證據，供後續 C2 做 DA 對照與 Q&A 撰寫。R1 已抓過 README/src 關鍵檔，故 C1 聚焦**版本演進、活躍度、成熟度指標**。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view firecrawl/pdf-inspector --json ...` | 取得最新 metadata | 確認 stars/更新/語言 | 14180 stars（R1 時 13753，+427）、964 forks、MIT、Rust、created 2026-02-06、updated 2026-08-10、desc 同 R1 |
| `gh api .../releases` 與 `/tags` | 確認版本演進與成熟度 | 佐證「穩定 vs 新」 | releases 為空陣列（無 GitHub Release 標籤）；tags 有 v0.7.0（最新）→ v0.6.0 → v0.5.0 → v0.4.3 → v0.4.2 → v0.4.1 → v0.4.0 → v0.3.6，版本迭代快速 |
| `gh api .../stats/commit_activity` 與 `/contributors` | 評估活躍度與維護規模 | 判「穩定度」證據 | 近 8 週 commit 數：5,0,20,40,0,6,19,3（有週期性空窗）；contributors 12 人 |
| `gh api ...` open_issues/forks | 補成熟度指標 | 判專案健康度 | open_issues 126、forks 964、subscribers 38 |
| `curl` Cargo.toml 與 README 開頭 | 確認版本號與定位敘述 | 對照 R1 報告版本 | Cargo.toml version 0.1.7、edition 2021、單一依賴 lopdf 0.42.0；README 開頭重申「Fast Rust library for PDF classification and text extraction…without OCR」「Lightweight—Pure Rust, no ML models, no external services. Single dependency on lopdf」 |
| `curl` crates.io 與 PyPI | 確認各語言綁定最新版 | 佐證成熟度 | crates.io API 被反爬擋（data-access policy）；PyPI 最新 0.2.6（與 R1 benchmark 對照版本一致） |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 定位敘述 | README 開頭 | 明確為「PDF 分類＋文字抽取＋轉 Markdown」，非純底層解析框架；「不靠 OCR」「純 Rust 無 ML 模型」為核心賣點 |
| 成熟度（版本） | tags / PyPI | 迭代快（v0.3.6→v0.7.0），PyPI 0.2.6；但**無 GitHub Release**、Cargo 版本 0.1.7 與 tag 0.7.0 不一致，版本管理略亂 |
| 活躍度 | commit_activity / contributors | 近 8 週有週期性空窗（0 commit 週），12 位 contributor，屬**活躍但非高頻** |
| 健康度 | open_issues | 126 個 open issues，對 14180 stars 屬正常量級 |
| 與 R1 差異 | 對照 R1 報告 | stars 增加、版本已推進（R1 引用 0.2.6 benchmark），其餘定位不變 |

**C1 收斂（供 C2 使用）**：pdf-inspector 是「**新（2026-02 建立）、迭代快、活躍但非高頻維護**」的專案。這直接回應 Q2「穩定優先」——它**不具備成熟穩定套件的特徵**（無正式 Release、版本號混亂、單一依賴但專案年輕）。定位上它是「分類＋抽取＋轉換」的應用層工具，非底層解析框架（底層解析交給 lopdf）。

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| C1 抓取範圍 | (A) 重抓全部 README/src (B) 聚焦版本/活躍度/成熟度 | B | R1 已抓過功能細節；R2 意圖是「定位＋穩定度」，故 C1 只補成熟度證據，避免冗餘 |
| 成熟度證據來源 | (A) 僅 stars (B) tags+commit+issues+版本號 | B | 單看 stars 會誤判成熟；需版本演進、commit 頻率、open issues、Release 有無綜合判斷 |
| crates.io 被擋 | (A) 改用 CDP (B) 以 PyPI/tags 替代 | B | crates.io 僅為佐證，PyPI 0.2.6 與 tags 已足，不需為此走慢速 CDP |
| 版本號不一致的處理 | (A) 忽略 (B) 記為成熟度疑點 | B | Cargo 0.1.7 vs tag 0.7.0 不一致是「版本管理未成熟」的具體證據，對 Q2 有價值，須保留 |
