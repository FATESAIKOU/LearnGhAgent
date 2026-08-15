# 222_R1_step2-plan_C1.md

## 狀況理解

Step 1 已確認技術標的為「仕様駆動開発（Spec-Driven Development, SDD）」，主要素材為 watany 的 speakerdeck 簡報。本 sub-step C1 的任務是取得 repo metadata 與主要文件。重點：**標的不是 GitHub repo**，而是 speakerdeck 簡報頁，因此標準調研動作中的 `gh repo view` 不適用，改以 `webfetch` 抓取簡報頁並擷取其 transcript（含全部 51 張投影片文字）。C1 需先取得「主要文件」——即簡報全文——才能供後續 C2 分析。另需確認使用者提問的「賞味期限」與簡報實際標題「消費期限」的用字差異，此為 C2 分析的重點前導。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 確認標的是否為 GitHub repo | 決定用 gh 或 webfetch | 判斷調研工具 | 標的是 speakerdeck URL，非 GitHub repo，`gh repo view` 不適用 |
| `webfetch` 抓取 speakerdeck 簡報頁 | 取得簡報主要文件（全文 transcript） | 取得 51 張投影片的完整文字 | 成功取得完整 transcript，涵蓋全部 51 張投影片文字與所有外部引用來源 |
| 記錄簡報 metadata | 建立來源信任層級 | 掌握來源時效性 | 作者 watany（NTTテクノクロス）、登壇日期 2026/8/6、AI Native Dev Night Tokyo、8.2k views、分類 Programming、提供 PDF 下載連結 |
| 標註外部引用來源 | 供 C2 背景補查 | 建立引用清單 | 引用 Kiro、OpenSpec、Spec-Kit、Martin Fowler 文章、Karpathy LLM Knowledge Base、OKF、Thoughtworks Radar、arXiv 研究等 |

**簡報全文要點（transcript 收斂）：**

- 標題實際為「仕様駆動開発の**消費期限**」（使用者所寫「賞味期限」為用字差異，需於 C2 確認意涵）
- SDD 定義：2025/7 AWS 隨 IDE「Kiro」發表而提唱；「實作前先做仕様書」的 Vibe Coding 之後的 retro-ronym；實務兩面向：(1) 作為 AI workflow framework、(2) 作為 agent 的長期記憶文件管理
- spec 實作三模式：spec-first（用完即棄）、spec-anchored（保留持續更新）、spec-as-source（spec 為唯一來源）；作者註明實務上只有前兩種被實際使用
- 核心論點：SDD 的 workflow「仕様→設計→タスク化」在 2025/7〜9 成形，距今約一年；其後 LLM 自走性能大幅提升（GPT-5.2、Opus 4.5），「事前做任務清單再實作」已普遍化進 coding agent（= Plan Mode），SDD 不再唯一
- 對「守破離」框架：AI-DLC 太重、Skills 堆疊無型 → 選擇 OpenSpec（捨 Spec-Kit，因後者文件重厚）
- 已知課題：coding→review 瓶頸、spec 檔案群 drift 管理、被 spec 語言束縛而無法發揮 LLM 性能
- 結論：SDD 的「消費期限」＝「破型的時機」；遇到課題前 SDD 易懂，團隊全員覺得過期時就進到下一步

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 主要文件取得 | transcript 涵蓋 51 張投影片文字 | 完整取得，含每頁標題與內文、引用來源 |
| 標的性質 | 是否 GitHub repo | 非 repo，為 speakerdeck 簡報，已用 webfetch 完成 |
| 標題用字 | 使用者「賞味期限」 vs 簡報「消費期限」 | 簡報標題為「消費期限」，用字不同，須在分析中標示 |
| 背景脈絡來源 | 簡報內嵌引用清單 | 已蒐集 Kiro、OpenSpec、Spec-Kit、Martin Fowler、Karpathy、OKF、Thoughtworks 等引用，供 C2 補查 |
| 檔案落點 | C1 log 路徑 | 寫入 memory/log/222_R1_step2-plan_C1.md |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 調研工具 | gh repo view / webfetch | webfetch | 標的為 speakerdeck 網頁非 GitHub repo，gh 不適用 |
| 主要文件範圍 | 僅首頁 / 完整 transcript | 完整 transcript | 使用者要「調研理解內部的內容」，須完整取得所有投影片文字 |
| 「賞味期限/消費期限」用字 | 以使用者用字為主 / 以簡報標題為主 | 標記兩者差異，分析以簡報「消費期限」為準 | 簡報標題明確為「消費期限」，但使用者寫「賞味期限」，需在分析中對照並確認意涵是否一致 |
| 背景補查時機 | C1 全部做完 / 留給 C2 | C1 先收斂引用清單，C2 補查 | C1 定義為「取得主要文件」，背景查證屬 C2 範圍 |
