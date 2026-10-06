# 292_R2_step2-plan_C1.md

## 狀況理解

R2 為 QA 輪，使用者判「觀望」並提 5 點追問（同構但不構成替換理由／規模大需觀望／整合全部→難局部擴張／需求不穩、重構必然、先續用同構服務／價值在需求想像與能力邊界）。C1 不重做 R1 的「這是什麼、如何運作」，而是取**能支撐這 5 點裁定**的資料：repo 現況（規模證據）、Paperclip 官方對「擴張單一能力」的設計立場、與他 MyBrain 判準的對應關係。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| refresh MyBrain 鏡像＋grep `paperclip` | 確認標的未被收錄、取最新判準 | 避免誤植判定 | 鏡像 @ `c3319a0`；`paperclip` 仍 0 命中 |
| 讀骨幹：Ai公司架構／技術取捨準則／統一的兩端稅／核心價值觀 | 取「同構」「汰換」「統一稅」「價值序列」原文 | 支撐 Q1、Q3、Q4 | 全部命中，見下表 |
| `gh repo view paperclipai/paperclip` | 交叉 R1 metadata | 規模證據 | stars 97,626（R1 97,420→續增）、fork 16,499、MIT、TypeScript、`master`、updated 2026-10-05 |
| `gh api contents/doc`（全目錄） | 找官方對擴張／整合的定義文件 | 補 §3、Q3 | 新增/確認 `SPEC.md`（DRAFT）、`SPEC-implementation.md`、`doc/plugins/PLUGIN_SPEC.md`、`architecture/`、`memory-landscape.md`、`connections/`、`DOC/sandbox` 等逾 80 檔 |
| `gh api releases` | 驗活躍度（Q2 規模側證） | 時序判準 | 27 個 release，最新 v2026.1001.0（2026-10-02），近月每 1–2 週一發 |
| `gh api contents/packages/...`（adapters／plugins／sandbox） | 量測「整合了什麼」 | Q3 具體化 | adapters 13 個（claude/codex/cursor/gemini/grok/hermes/kimi/opencode/pi/openclaw/cursor-cloud…）；sandbox-providers 8 個（cloudflare/daytona/e2b/exe-dev/kubernetes/modal/novita/createos）；plugins 6 子件＋mcp-server |
| 讀 `doc/SPEC.md`（Board Governance／Budget Delegation） | 官方治理模型定位 | 對照他「不要審核關卡」 | 明文 **V1: Single human Board**，Board＝「human oversight layer」＋approval gates（hire、CEO 策略）；budget 可逐層下放 |
| 讀 `doc/PRODUCT.md`（Principles／Do-Not） | 官方對擴張與整合的設計立場 | **直接回應 Q3** | 明列 **「Thin core, rich edges」**：把 chat／knowledge 等放進 plugins，避免膨脹控制面；同時明列五大 principle 與「Do not build enterprise-grade RBAC first」 |
| 讀 `doc/plugins/PLUGIN_SPEC.md`（Current implementation caveats） | 查擴張路徑的成熟度 | Q3 反面證據 | 自述現況：**single-tenant、self-hosted、single-node**；plugin UI 視為 trusted code 非沙箱；**dynamic plugin install 尚不 cloud-ready**、無共享 artifact store |
| 讀 `doc/memory-landscape.md` | 查「整合多記憶系統」的官方取徑 | Q3 對照 | 目標訂為「能坐在多個差異很大的 memory 系統之上的**最小契約**，而不抹平差異」 |

**關鍵發現（供 Q1／Q3 用）**

| # | 發現 | 出處 | 對他 5 點的意義 |
|---|---|---|---|
| A | 官方原則 4：「Control plane, not execution plane」；5：「All work traces to the goal」；2：「Company is the unit」 | `doc/PRODUCT.md` | 逐條對上 Ai公司架構「兩個東西不是兩層」「共用媒體」＋MyPMO 工單樹 |
| B | 官方明訂 **「Thin core, rich edges」** | `doc/PRODUCT.md` | **Q3 的官方反證**：Paperclip 自己也承認全包是風險，故設計上把可選面往 plugin 推 |
| C | 但 plugin runtime 自述**尚未 cloud-ready、single-tenant、UI 為 trusted code** | `doc/plugins/PLUGIN_SPEC.md` | **Q3 的官方正證**：設計意圖（thin core）與當前實作（擴張仍受限）有落差，使用者的「難局部擴張」知覺對**當前版本**成立 |
| D | V1 治理＝**Single human Board**＋approval gate | `doc/SPEC.md` | 對上他「不要人工審核關卡、要 verify」的衝突（R1 §4.4 已標） |
| E | memory-landscape 明言「不抹平差異」 | `doc/memory-landscape.md` | 與「統一的兩端稅」同構：官方亦警覺統一會抹平兩端 |
| F | stars 97,626／fork 16,499／27 releases | `gh api` | Q2「規模大」為客觀事實，非感知 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| metadata 真偽 | PR body(97,403) vs `gh api`(97,626) | 屬實，差值為時點落差 |
| 規模證據 | adapters 13／sandboxes 8／doc 80+ | 「整合很多」有硬數據 |
| 擴張立場 | 讀 PRODUCT＋PLUGIN_SPEC | 官方倡 thin core，但實作未達 |
| 治理衝突 | 讀 SPEC Board Governance | V1 approval gate 確認 |
| MyBrain 對應 | grep＋讀骨幹 | Q1/Q3/Q4 有原文依據；Q5 仍 0 命中 |

**C2 交棒項**：①將 5 點拆為 Q1–Q5 追加 `output/292_paperclip.md` `## 5.`；②Q3 須**同時**引 official「thin core」與 plugin caveat，避免單邊敘事；③Q1 對照 Ai公司架構原文、Q4 對照技術取捨準則四；④Q5 僅能以本輪原話呈現，不得歸因既有立場；⑤R1 §4.6 結論可補入「官方 thin core vs 實作未達」這條新反面論證。

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| C1 範圍 | 重抓 README / 抓官方新文件（SPEC、PLUGIN_SPEC） | 抓官方新文件 | R1 已取 README；Q3 需官方對擴張的定義 |
| 是否信 R1 的 97,420 | 沿用 / 重查 | 重查（97,626） | 規模是 Q2 核心，須當日實查 |
| Q3 證據取向 | 只用我的推論 / 官方文件正反並列 | 正反並列 | 不可用推論代替官方立場；thin core 與實作 caveat 皆須引 |
| 前案比較 | C1 重做 / 沿用 R1 §4.1 | 沿用 R1 | R1 已建 DA 表與判定對照，R2 只補新論證 |
| 影片缺口 | 重查字幕 / 維持註記 | 維持註記 | R1 已明列且來源仍不可得 |
