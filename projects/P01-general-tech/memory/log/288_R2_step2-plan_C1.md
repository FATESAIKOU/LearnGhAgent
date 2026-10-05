# 288_R2_step2-plan_C1.md

## 狀況理解

- 本 sub-step 為 R2 的第一個調研動作，只服務本輪兩個追問：Q1「DBX 是否就是大一統的各種 DB client」、Q2「誰維護、投入規模」。
- 不重做 R1：R1 已取得架構、驅動、MCP/CLI、安全與替代方案。C1 只補兩類新事實：
  1. **定位的一手自述**（README「Why DBX」、功能清單）→ 供 Q1 正面回答「是／不只是」。
  2. **維護者身分、貢獻結構、投入量級、資金／基礎設施**→ 供 Q2 的 bus factor 與規模判定。
- 資料源：`gh api` metadata / contributors / commit activity / releases、raw README／Cargo.toml／CONTRIBUTING／ARCHITECTURE、`.github/workflows` 清單、dbxio.com。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh api repos/t8y2/dbx` 取 metadata | 取即時概況 | 建立快照 | stars 24,780、forks 2,241、open issues 966、size 210,353 KB、created 2026-04-29、pushed 2026-10-05、language Rust、license Apache-2.0、subscribers 104 |
| `gh api contributors` 全量 + 總和 | 算貢獻集中度 | bus factor 可量化 | 共 **327 位**（per_page=1 → 327 頁）、總貢獻 7,489 |
| 取 contributors top 群 | 找主要維護者 | 定位 top-N | t8y2 **3,893**（52%）、zipg 1,048（14%）、eryajf 330、github-actions[bot] 295、q396921921 166、Abeautifulsnow 151、0verme 119、CN-Scars 100 |
| 取最近 100 commits 作者分布 | 看「當下」誰在動 | 判現役人力 | lxk955 33、t8y2 15、eryajf 10、actions-bot 7、thailoc-dev 7、Tong-bit-art 6 |
| `gh api stats/commit_activity` | 量投入節奏 | 週頻趨勢 | 2026-05 起穩定 **260–480 commits/週**；近一週（10-04 起）116（未過完） |
| 取 releases / tags | 發布節奏 | 維運量級 | 三條 release 線（app `v0.6.x`、packages `packages-v0.4.x`、agents `agents-v0.2.x`），近 **每日一發**（v0.6.34 於 2026-10-04） |
| commits / PRs Link header 計數 | 吞吐量 | 專案活躍度 | commits ≈ 7,876；open PR ≈ 64；closed PR ≈ 3,827 |
| raw README「Why DBX」＋功能清單 | 取定位自述 | Q1 一手證據 | 明列「25 MB 無 JRE/Chromium」、「AI in editor」、「MCP」、「Desktop+Docker+Web」、「Not just databases（MQ／中介軟體 console）」、「Plugin ecosystem」 |
| raw Cargo.toml / ARCHITECTURE | 量程式規模 | 技術深度 | 27 個 workspace crate；並 vendor wry/tiberius/pageant/dirs-sys 等自維護；Rust 24.6M、TS 18.7M、Vue 11.0M、Go 3.67M、Java 3.25M 位元組 |
| `gh api users/t8y2`＋zipg | 維護者身分 | 個人 vs 組織 | t8y2＝個人 developer User（北京、bio「造物而已，尽心而已」、544 followers、2021 建帳、58 repos）；zipg＝個人 User |
| `.github/workflows` 清單 | 看自動化投入 | 維運基建 | 32 條 workflow（release／agents／mcp／plugin／docker／sync-mirrors／i18n-autofill／spam-guard 等） |
| README sponsors / partners / dbxio.com | 查資金與商業化 | 投入可持續性 | sponsors 8 家（RainYun、TrustAsia、UCloud、Qiniu、Jalapeño、AICodeMirror、HuaLongAI、Atlas Cloud）；partners 1Panel、Easysearch；自有官網、docs、外掛市集 `t8y2/dbx-store` |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| Q1 可答性 | 是否有定位自述一手資料 | 有：README「Why DBX」＋功能清單，足以判「不只是 DB client」 |
| Q2 可答性 | 是否有維護者＋投入量級硬資料 | 有：owner 身分、327 貢獻者、集中度、週頻、發布節奏、資金來源 |
| 資料即時性 | 是否為 2026-10-05 快照 | 是（pushed 2026-10-05T19:16Z） |
| 與 R1 的關係 | 是否重複 R1 | 不重複；僅補定位自述與治理／規模兩塊 |
| 缺口 | 尚待補的資料 | org 化程度（無 GitHub org，以個人帳號＋自有網站／市集為中樞）、實際全職人力（無公開數字，僅能以 commit／release 推估） |
| 來源性質 | 一手 vs 二手 | 全部 GitHub API／raw 檔／官網，皆一手 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 是否重抓 R1 架構 | 重抓／只補新事實 | **只補定位與治理兩塊** | 任務明示 R2 針對本輪意圖，避免重工 |
| bus factor 計法 | 看 single top-1／看 top-2 累計 | **兩者並列呈現** | t8y2 52% 近半、t8y2+zipg 66%，並列才不失真 |
| 維護者身分判斷 | 以 repo 名推測團隊／查帳號與網站 | **查 t8y2 帳號＋官網＋sponsor** | 需要「個人 or 公司」的實證，不可臆測 |
| 投入量級來源 | 只報 star／補 commits、release、CI、crate 數 | **多維並列** | star 非投入指標；週頻、發布、基建、程式量才是量級證據 |
| 定位判定素材 | 只看「100+ DB」標語／看整份功能面 | **看整個功能面** | Q1 問「是否只是 DB client」，須涵蓋 MQ／中介軟體／外掛才答得準 |
| 商業化資料處理 | 略過 sponsor／明列 | **明列 sponsor 與夥伴** | 直接關係「投入可持續性」，是 Q2 關鍵 |
