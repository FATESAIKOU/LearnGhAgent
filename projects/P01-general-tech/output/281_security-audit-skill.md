# security-audit-skill 分析報告

> 調研標的：cloudflare/security-audit-skill（GitHub）
> repo 描述：A coding-agent skill for multi-phase security audits with independently verified, machine-readable findings
> 版本資訊：21,758 stars／1,255 forks／MIT／JavaScript；建立 2026-06-18，最後 push 2026-09-14；open issues 50；無 topics、無 releases、無 tags
> 上位來源：Cloudflare blog〈Build your own vulnerability harness〉（2026-06-18）
> 一手文件：README ＋ `skills/security-audit/` 下 20 個檔案（`SKILL.md`、4 個流程檔、10 個 domain companion、`report-schema.json`、2 組 validator 及其 test）

---

## 1. 這個技術解決什麼問題？

**一句話：security-audit-skill 解決「直接叫 coding agent 檢查專案漏洞時，過程過度發散、結論摻雜未經證實的猜測，因而無法據以行動」的問題。**

| 被解決的具體子問題 | 症狀 |
|---|---|
| agent 一次只持有一個假設 | 換到下一個假設時，前一個的調查進度無法保留 |
| context window 在覆蓋真實 repo 的一小角後即填滿 | 覆蓋率低，且模型開始自我吞食記憶 |
| context 壓縮（compaction）過程中資訊遺失 | 早上追蹤到的線索，一小時後被遺忘 |
| 產出的「漏洞」缺乏可驗證來源 | 報告看似嚇人，細節多是未經 source trace 與實測的推測 |
| 發現者與判斷者同一 | 發現者替自己的推論背書，沒有反對者 |

**痛點的模糊之處：**

- 影片以「過度發散」描述，未給量化定義。對照一手來源，其可操作化版本是三條：一次一假設、context 快速填滿、compaction 遺失。
- 「細節多是猜測」在一手來源中對應「沒有完整 source trace 與有界實測結果的候選」；但 repo 與 blog 皆未提供 false-positive rate 作為驗收指標，blog 明言不宣稱 false-negative rate（無標註全集可比較）。
- 「已確認／還需要驗證／已排除」對應 repo 的三個 verdict：`confirmed`／`needs_validation`／`rejected`。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 文章中明確提到的背景（blog 與 repo 文件）

| 背景項 | 內容 |
|---|---|
| 前作脈絡（Project Glasswing） | 前一篇貼文已主張通用 coding agent 無法勝任此工作：一次一假設、context 很快填滿、compaction 遺失資訊 |
| 為何不用 sub-agent 就夠 | 安全分析需要數百個「跨 run 存活、不共用 context、可重新 scoped 與交叉引用」的獨立調查；這是 orchestration 問題，prompt 到不了 |
| 起源是 skill 而非 harness | 起點是約 450 行的 `security-audit` skill，單一 repo 執行、調 prompt 到能浮現真 bug；orchestration 為後加 |
| 三個牆 | Context exhaustion／Persistence（crash 即重來）／Cross-repo reasoning（單 repo 對消費者關係全盲） |
| 單次跑覆蓋不足 | 單次 run 找到的漏洞約為反覆執行總數的一半，且分佈偏向簡單、不 subtle 者 |
| 不綁模型 | 同一 target 換不同模型會各自找到不同比例的 bug；harness 才是長存的部分，設計需 model-agnostic |
| 規模化落差 | fleet 版覆蓋 128 repos、跨語言無 per-language tuning；該版約六週從 skill 演進而成 |

### 2.2 通用技術背景（文章未明說，為必要脈絡）

| 背景項 | 說明 |
|---|---|
| SAST 的結構限制 | 靜態分析不執行程式碼、僅做模式匹配，產出大量誤報，需人工驗證。此問題框架見第二大腦 Strix 紀錄（二手來源） |
| DAST 的結構限制 | 傳統 DAST 掃描器（Nessus、OpenVAS 等）只能「發現」潛在弱點，無法「驗證」其可被利用性。同上 |
| LLM 的知識性質 | LLM 為統計式生成器，對「某 repo 的具體可達性、本機實際安裝了什麼」沒有確定性知識；資安判斷需要確定性事實 |
| 沙箱隔離光譜 | runc（共享 kernel）→ seccomp → gVisor（用戶態 kernel）→ microVM（KVM）→ hardware VM；作業系統強制沙箱的構成要素為：無外網、allowlist 空環境、資源限制、read-only target/toolchain、僅 scratch 可寫 |
| context engineering | 把 agent state 外部化，將 LLM 當作 stateless compute engine，是長流程 agent 的通用解法，而非安全領域獨有 |
| 訊號分離 | severity／confidence／false positive 需分開處理；可信度不得推得為嚴重度 |

---

## 3. 這個技術是如何解決該問題的？

### 3.1 定位與兩種模式

本體是一個 markdown 指令包（agent skill），不是可執行軟體。核心流程以 agent 編排 + 確定性 validator 構成「文件式 harness 契約」。

| 模式 | 觸發條件 | 行為 |
|---|---|---|
| **Guidance mode**（預設） | 只問安全問題、聚焦 review、方法論、triage | 只取用相關段落，不自動跑六階段、不建 output 目錄、不寫 audit 產物 |
| **Full audit mode** | 明確要求 audit／pen-test codebase、full／comprehensive／end-to-end review、或要求 report artifacts | 跑完六階段，寫出 7 個共享檔 |

請求落在兩者之間時，須先問一個聚焦問題，再決定是否建檔或跑完整流程。

### 3.2 六階段流程

```
 Phase 1        Phase 2            Phase 3          Phase 4         Phase 5            Phase 6
 Recon          Coverage-led       Candidate        Structured      Independent        Target-neutral
                hunting            validation       output          record verify      reporting
   │                │                  │                │                │                  │
 4 個並行         ledger 單元        每個唯一候選      寫 findings.json  全新 agent 複核    由已驗證紀錄
 research agent   分派給隔離          交給未參與          對 schema 與     最終 source 主張   推導 REPORT.md
 寫 architecture  hunter agent；      hunt 的 verifier    ledger 跑確定    material 更換再    FINDINGS-DETAIL
 .md；parent 建   coverage-critic    ，verifier 的       性 validator      給另一位獨立       NEEDS-VALIDATION
 coverage-ledger   wave 找缺口        任務是推翻它       (.cjs)          verifier           .md
```

- **Phase 1**：`RECONNAISSANCE.md` 定義 4 個並行 research agent（1a 產品與技術棧、1b 主體與權限、1c 入口表面與 sink、1d 本地執行與部署可見性），只回傳結構化事實、不寫檔。parent 綜合出 `architecture.md`（約 1000 字上限），並建立確定性的 `coverage-ledger.json`。
- **Phase 2**：`HUNTING.md` 定義 hunter 契約與覆蓋 critic wave。每個 hunter prompt 依固定順序含 9 個部分（角色前言、architecture 全文、分派單元、逐字複製的攻擊類別區塊、排除區塊理由、方法、驗證規則、不得重複的同儕單元、scratch 路徑與結構化結果契約）。
- **Phase 3**：每個唯一候選給一個「沒有 hunt 過它」的全新 verifier，任務是從 source 與有界本地證據反駁。
- **Phase 4**：所有紀錄寫入 `findings.json`，以 `report-schema.json` 為契約，並跑確定性 validator 硬檢。
- **Phase 5**：對每個 `confirmed` 與 `needs_validation` 紀錄，各啟動一個全新 research verifier 複核結構化紀錄，而非 hunter 的敘述。
- **Phase 6**：僅由最終紀錄、ledger、hardening notes 推導三份 prose 報告，且不得改動 verdict、severity、blocker 或實測結果。

### 3.3 四個核心機制

| 機制 | 做法 | 對應痛點 |
|---|---|---|
| **覆蓋帳本（coverage-ledger）** | 每個單元為 `entry surface × trust boundary × subsystem × applicable attack class`（`deep` 再加 lifecycle）的組合；`coverage_id` 由 canonical refs 經 RFC 3986 percent-encoding 後以 `::` 連接，排序去重、碰撞即 fail。單元有狀態機：`planned`／`in_progress`／`blocked`／`covered`／`candidate`／`not_applicable`／`out_of_scope`／`deferred`；`attempts` 為 append-only 存證。parent 是唯一更新者 | 發散、覆蓋率不可證 |
| **對抗式驗證（adversarial validation）** | 「檢查 finding 的 agent，永遠不是找到它的 agent」；`confirmed` 需完整 source trace 與有界實測結果，且 severity 不得超過已證實 impact | 發現者自我背書 |
| **結構化輸出 + 確定性 validator** | `findings.json` 為三 verdict 分支的 oneOf 契約，`additionalProperties:false`；`validate-findings.cjs` 與 `validate-coverage-ledger.cjs` 為零依賴 Node 腳本，Phase 4 與每次 Phase 5 更換後重跑 | 結果不可機器讀、prose 與 JSON 不一致 |
| **寫入隔離與沙箱** | parent 為共享檔唯一寫者；每個 hunter／verifier 有自己的 `scratch/` 與 parent-owned `artifacts/`。目標控制碼只在 OS 強制沙箱內執行（無外網、allowlist 空環境、read-only target、scratch-only 寫入、資源限制）；artifact 只能由 parent 端以 no-follow、path-confined、regular-file、bounded-size 程序提升 | 目標碼反噬宿主；無沙箱則不執行 |

**確定性 validator 的能力邊界（repo 自陳）：** 只證明格式與 ledger 一致性，不證明正確性。blog 亦明確指出機械驗證「檢查 line numbers 與 functions 是否真的存在」，屬 schema adherence 而非 correctness。

**執行契約要點：**

```
source inspection（唯讀）
        │
        ▼
有 OS 強制沙箱？ ── 否 ──▶ 不執行目標碼 ⇒ lead 保持 needs_validation
        │ 是
        ▼
bounded local evidence（最小函式 harness／既有單元測試／小 fixture／dummy-tenant 測試）
        │
        ▼
止於最小邊界結果（錯誤回傳值、未授權 dummy 紀錄、sanitizer finding、policy 差異）
```

### 3.4 三類 verdict 契約

| verdict | 成立條件 | severity | 其他欄位 |
|---|---|---|---|
| `confirmed` | 完整 source trace ＋ 有界本地實測的 observed result ＋ 完整條件 ＋ 無可見阻擋層 | 有（likelihood × impact，且不得超過已證實 impact） | `root_cause`、`intended_behavior`、`remediation`、`confidence`、target-neutral `execution` |
| `needs_validation` | 有精確的未解事實（deployment／provider／OS／identity／runtime fact），有 nonempty `blockers` 與至少一個 `validation_plan.local` 或 `deployment` | 無 | `claimed_root_cause`、不得使用 severity／execution／remediation／reason |
| `rejected` | 驗證時被 source、本地行為、可見控制、缺有意義 impact 或不可能前提推翻 | 無 | `claimed_root_cause`、`reason` |

**severity anchors：** critical（未認證取得 code execution／全資料庫存取／任意帳號接管）／high（完整擊敗明確控制且有真實後果）／medium（真實邊界突破但 blast radius 有限、前置罕見）／low（非機密內部資訊洩漏、或需持續努力換極小利益）／informational。

**設計原則（README）：** 只確認已成立的邊界失效；defense-in-depth 缺口不是漏洞（若 Layer A 已阻止攻擊，缺 Layer B 只是 hardening note）；多次執行為 additive，用既有 ledger 與 findings 指向缺口、重驗變更來源。

### 3.5 安裝與執行前提

```bash
# 正確指令（README，Skills CLI：https://skills.sh）
npx skills add https://github.com/cloudflare/security-audit-skill \
  --skill security-audit

# 使用者層安裝
npx skills add https://github.com/cloudflare/security-audit-skill \
  --skill security-audit --global
```

觸發語句例：`security audit this codebase`／`find security vulnerabilities in ./src`／`do a security review, output to ~/audits/my-project`。full audit mode 未指定輸出目錄時，預設 `~/security-audit-skill/<repo-name>/run-<N>`；只有在使用者明確選定且版本控制忽略該目錄時，才寫入 target repo 內。

**Requirements：**

| 需求 | 用途 |
|---|---|
| 支援 tool use 與並行 sub-agent 的模型 | 六階段的編排與並行 hunter |
| Node.js | 跑零依賴的 findings 與 coverage-ledger validator |
| OS 強制沙箱（無外網、allowlist 環境、資源限制、scratch-only 寫入） | 執行 target-controlled build／test／process／browser／emulator／fuzzer／fixture。任一控制無法強制時，workflow 保持 lead 為 `needs_validation`，不執行目標碼 |

**Run profiles 與成本預算：** `quick`（一個 hunter wave + 一次 final critic）／`standard`（預設）／`deep`（高風險或大 target），另有 scoped run。`budget` 記為跨階段的最大 agent invocation 數；啟動任何 recon agent 前先過嚴格預算閘門，保留 recon 呼叫、critic 與 verifier 的額度。超支時設 `run_status: "incomplete"` 並揭露缺口，未驗證候選不得進 `findings.json`。

### 3.6 已知限制與與影片記述的出入

| 限制 | 一手來源實況 |
|---|---|
| 耗時耗算力 | blog：標準 repo（約 30k 行）單次 run 3–4 小時，最壞一次 14 小時；fleet 版 worker pool 50–200；大 scan 定位為 periodic backlog sweep，非 per-PR check |
| 需真正系統級沙箱 | README 明列 OS 強制沙箱；未具備時只保留 `needs_validation` |
| 單次覆蓋不足 | 單次約找到反覆執行總數的一半，且偏簡單 |
| 無 recall 主張 | blog 不宣稱 false-negative rate；效果以「re-run 是否仍找到新 bug」與「coverage 是否仍成長」為 proxy |
| repo 工程狀態 | 無 CI、無 topics、無 release/tag；活躍度集中於 2026-09-10 的大幅 rework（workflow、findings contract、validators 全面重寫） |

**與影片記述的兩處出入（以一手來源為準）：**

| 項目 | 影片／PR body 說法 | 一手來源實況 | 判定 |
|---|---|---|---|
| 安裝指令 | `npx skill add`（念作 mpx） | README：`npx skills add`（Skills CLI，skills.sh） | 以 README 為準 |
| 階段數 | 影片列 5 步；blog 稱 7-phase | README／`SKILL.md`：6 phases | 6 階段為對外現行版本；7 階段是 blog 描述的內部初始版，已演進 |

### 3.7 Cloudflare 的定位：skill 是 harness 的起點

README 明確定位：本 skill 是 Cloudflare vulnerability discovery harness 的種子，harness 已長成多階段、fleet-wide 系統，而本 skill 是其演進出的單 repo 起點。

blog 的 skill → harness 對映：

| Skill phase | Harness stage |
|---|---|
| Recon agents 寫 architecture.md | Recon |
| Hunters 依 attack class 執行 | Hunt |
| Validators 推翻 findings | Validate |
| 存活 findings 成報告 | Report |
| findings.json 機械檢查 schema（非正確性） | Mechanical validation of line numbers and functions |
| 全新 agent 重驗 findings | Independent validation |

**fleet 版的規模數字（blog 官方敘述）：** VDH 產出 20,799 raw candidates → 12,057 通過驗證 → 併入 VVS 後中央池 13,841 → Dedup 折掉 5,442 → 1,154 歸為 wrong-repo／low-risk → 最終 7,245 actionable findings。VDH 與 VVS 使用不同模型互相檢查；blog 自陳 initial validation rejection rate 由 40% 降到 11%，高完整性 findings 佔比由 35% 升到 58%。這些數字屬 fleet harness，非單 repo skill 的產能。

**blog 的一項實測觀察：** 團隊把 Semgrep 全程接進 pipeline，hunters 在一個月內呼叫它 0 次；hunters 偏好讀 code 與跑 code，而 wishlist 是最常被使用的工具。此觀察對「LLM agent 是否採用傳統 SAST」提供一手反面資料。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### 4.1 替代方案 DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **Strix**（usestrix/strix） | LLM Agent ＋ 隔離沙箱 ＋ 工具鏈 ＋ 多 Agent 協作；模擬駭客行為動態執行程式碼、發現弱點並以 PoC 驗證，產出修補建議 | Python ≥3.11、Docker、LLM API key；目標需可連線。支援 blackbox／whitebox | token 消耗大，依測試面向差異極大；Docker 沙箱與 LLM API 成本 | 端到端自動化滲透測試與可操作修補建議。**第二大腦判定：採用** |
| **PentestGPT**（GreyDGL/PentestGPT） | 三模組（Reasoning／Generation／Parsing）分工 ＋ Pentesting Task Tree（PTT）結構化全域脈絡，維持長流程脈絡 | LLM provider；目標需可連線 | 需維護全域脈絡；LLM 推理延遲；v1.0 agentic 模式綁 claude CLI | 以任務樹降低單一 LLM session 的 context loss。**第二大腦判定：未判定** |
| **reverse-skill**（zhaoxuya520/reverse-skill） | 逆向／滲透／安全研究的 Skill 路由包：`routing.json` 41 條規則計分路由、tool-index、授權門禁、163 個回歸測試 | 支援 skill 載入的 AI client；需授權 scope | 路由為關鍵字計分（非語意），選錯詞會路由錯；結果真偽仍需資安專業判斷 | 把「選對方法論」降到一般工程師可及。**第二大腦判定：不採用** |
| **傳統 SAST／DAST**（以 Semgrep 為 SAST 代表；Nessus／OpenVAS 為 DAST 代表） | SAST：不執行程式碼，以 pattern 匹配掃 source；DAST：對運行中的服務做動態掃描 | SAST 需 source 與規則集；DAST 需可連線的運行環境 | SAST 假陽性高、需人工驗證；DAST 只能發現潛在弱點、無法驗證可利用性 | 高頻、可 CI 化的廣度掃描。**第二大腦：無獨立評估紀錄（查無）**；僅在 Strix 紀錄的問題框架中被提及 |

> 另兩個同軸對照（形式或前提相關，非同級替代）：**agent-skills**（addyosmani/agent-skills，`human:fatesaikou`／stable／觀望，2026-08-11 由採用降級，理由為資源而非技術）同屬 skill 形式但為通用開發生命週期；**gVisor／microVM**（`human:fatesaikou`／stable／不採用，結論「Cloud 已有內建，知道就好」）是本標的落地前提（OS 強制沙箱）而非替代方案。兩者見 4.2 與 4.3。

### 4.2 切入點差異

| 方案 | 切入點 | 與本標的的抽象層關係 |
|---|---|---|
| Strix | **執行**：直接跑滲透、以 PoC 驗證 | 同為 AI agent 安全測試，但 Strix 是執行導向的獨立工具；本標的是 skill／流程編排 ＋ 驗證契約。兩者可並存：本標的管「覆蓋與驗證的編排」，Strix 管「實際攻擊執行」 |
| PentestGPT | **脈絡維持**：用任務樹對抗 long-context loss | 解的是「長流程不失憶」，本標的以外部化 ledger／findings 對抗同一問題。兩者對「狀態外部化」的手段不同：一為樹、一為帳本 ＋ JSON 契約 |
| reverse-skill | **任務分流**：把任務路由到正確方法論 | 解「該做什麼」，本標的解「怎麼把稽核收斂並驗證」。兩者形式同為 skill，但 reverse-skill 不產出 findings、不管驗證身分分離 |
| 傳統 SAST／DAST | **廣度掃描**：規則式或動態式覆蓋 | 本標的明確與其互補且對立：SAST 假陽性高、DAST 不能驗證可利用性；本標的以「完整 source trace ＋ 有界實測」要求取代純規則或純掃描 |
| agent-skills（addyosmani/agent-skills） | **工程紀律**：7 命令 × 6 階段生命週期 ＋ 4 個 persona（含 security-auditor） | 同屬 skill 形式，但通用開發生命週期，非安全稽核編排。第二大腦判定觀望（2026-08-11 由採用降級，理由為資源而非技術） |
| gVisor／microVM | **隔離層**：以用戶態 kernel 或最小 VM 隔離容器 | 是本標的 full audit 的落地前提（OS 強制沙箱），非同級替代。第二大腦判定不採用（「Cloud 已有內建，知道就好」） |

### 4.3 第二大腦對照與衝突

**本標的本身**：`cloudflare/security-audit-skill` 在第二大腦中**查無任何評估紀錄**；`技術/技術評估/判定總表.md`（`ollama-cloud/deepseek-v4-flash`，**draft，未經他 review**）117 筆索引中無此標的。以下同軸紀錄僅供對照，不得升格為他對本標的的既有判定。

| 標的 | GitHub URL | 信任層級 | 判定 | 與本標的關係 |
|---|---|---|---|---|
| Strix | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/Strix.md | `human:fatesaikou`／stable | **採用**（首見 2026-07-04） | 最接近的同級替代；已實測（見下） |
| 學習 Strix | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/動手做/學習%20Strix.md | `human:fatesaikou`／stable | 已實測（首見 2026-07-14） | 接 Ollama Cloud 掃 axross-recipe.com，效果不錯但吃 token；結論「限制攻擊面向、灰箱／白箱可降消耗」 |
| PentestGPT | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/PentestGPT.md | `process:learning-agent`／stable | **未判定** | 脈絡維持切入點；無採用結論可衝突 |
| reverse-skill | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/reverse-skill.md | `process:learn-gh-agent`／**draft** | **不採用**（首見 2026-08-10） | 理由「沒必要學一個 skill（依理解優先原則傾向自兜），且沒打算深入看資安，無法信任其產出」 |
| agent-skills | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/agent-skills.md | `human:fatesaikou`／stable | **觀望**（2026-08-11 由採用降級） | 同屬 skill 形式，內含 security-auditor persona 與 security checklist；降級理由為未排入下一步清單，非技術否定 |
| gVisor／microVM | https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/gVisor%20-%20microVM.md | `human:fatesaikou`／stable | **不採用**（首見 2026-05-31） | OS 沙箱隔離；結論「Cloud 已有內建，知道就好」 |
| 技術取捨準則 | https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/技術取捨準則.md | `claude-code/opus-5`／**draft（AI 草稿，未經他 review）** | 準則 | 理解優先；Reject≠沒價值；agent 約束在 harness；要補驗證機制而非人工審核關卡 |
| Harness Engineering | https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/本質洞察/Harness%20Engineering.md | `human:fatesaikou`／stable | 準則 | 關鍵五問：memory／read／action／permission／verify；AI Guardrails＝驗證規則程式化 |
| 不做清單 | https://github.com/FATESAIKOU/MyBrain/blob/main/抽象理解/價值觀/不做清單.md | `claude-code/opus-5`／**draft（AI 草稿，未經他 review）** | 準則 | 技術層幾乎無硬拒絕；閉源／無 license 是採用障礙而非價值否定 |
| 下一步清單 | https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md | `claude-code/opus-5`／**draft（AI 草稿，未經他 review）** | 現況 | 現無 security-audit 相關待辦；技術-動手做線在跑 AiStorage、LLM 推論骨架等 |

**明確指出的衝突：**

| # | 衝突／張力 | 內容 |
|---|---|---|
| 1 | **reverse-skill 的拒絕理由直接適用於本標的，結論方向相反** | reverse-skill 被判不採用，理由是「沒必要學一個 skill（理解優先傾向自兜）」與「沒打算深入看資安」。本標的同樣是 skill 包、同樣屬資安範疇，直接套用該理由會推往不採用。**差異點**：reverse-skill 是「選方法論的路由包」，本標的是「含確定性驗證的稽核編排」，且把「驗證機制程式化」實作進產品——命中技術取捨準則第五節「要補驗證機制而非人工審核關卡」。兩者是否同一類，需由使用者判定，不得由本報告代判 |
| 2 | **理解優先準則與「採用現成 skill」相抵** | 技術取捨準則（AI 草稿）記「不夠穩定或不熟悉就先自己兜，理解本質後才決定下一步」，並註明「用現成的比較快」打不動他。他對資安稽核不熟悉（reverse-skill 紀錄明言沒打算深入看資安），依此準則推得的方向是先自兜而非直接採用。此張力未解 |
| 3 | **Strix 已採用且已實測，本標的與其重疊** | 他已有一條執行導向的 AI 安全測試線（Ollama Cloud 掃 axross-recipe）。本標的若要進 workflow，需先回答與 Strix 的分工。反面地，`學習 Strix` 的結論「限制攻擊面向、灰箱／白箱降 token」，與本標的 coverage-ledger 收斂覆蓋＋source-first 的思路同構 |
| 4 | **沙箱前提與 gVisor 判定不衝突，但構成落地門檻** | 他判定沙箱技術「Cloud 已有內建，知道就好，不會進 workflow」，與本標的依賴 OS 提供沙箱一致（他不自建沙箱）。其結果是：若他的執行環境無現成沙箱，full audit 無法啟用，只能停在 guidance mode 或 `needs_validation`。這是採用前提，非價值否定 |
| 5 | **與技術取捨準則第五節高度一致（非衝突）** | 準則要求「補驗證機制（測試、validator、CI、可回滾）」，本標的的 `validate-findings.cjs`、`validate-coverage-ledger.cjs`、身分分離的獨立 verifier、coverage-ledger 狀態機，正是該準則的具體實作。此為對照中少數的正向一致點 |
| 6 | **無排程位置** | 下一步清單（AI 草稿）現無此標的；他每週可支配時間有限，納入即需排擠既有項目。此為資源層事實，非技術判定 |

---

## 附錄：資料來源

- repo README：https://github.com/cloudflare/security-audit-skill/blob/main/README.md
- `skills/security-audit/SKILL.md`、`RECONNAISSANCE.md`、`HUNTING.md`、`VALIDATION-AND-REPORTING.md`、`ATTACK-CLASSES.md`、`report-schema.json`
- repo metadata 與檔案樹：`gh api repos/cloudflare/security-audit-skill`
- commits：2026-09-10 大 rework（workflow、findings contract、validators）；2026-09-14 釐清兩模式
- blog：https://blog.cloudflare.com/build-your-own-vulnerability-harness
- 第二大腦（FATESAIKOU/MyBrain）：`技術/技術評估/判定總表.md`、`技術/技術評估/Strix.md`、`技術/技術評估/PentestGPT.md`、`技術/技術評估/reverse-skill.md`、`技術/技術評估/agent-skills.md`、`技術/技術評估/gVisor - microVM.md`、`技術/動手做/學習 Strix.md`、`抽象理解/本質洞察/技術取捨準則.md`、`抽象理解/本質洞察/Harness Engineering.md`、`抽象理解/價值觀/不做清單.md`、`專案/下一步清單.md`
