# 305_R1_step2-plan_C1

## 狀況理解

Step 2 C1：取得技術標的 metadata 與主要文件。標的＝`wheresryan22/anatomy`——一個 **Agent Skill**（不是套件、不是服務），把技術概念「發明成一台真實機械」並輸出互動式等角圖。R1 首次調研，非追問。C1 目標：盤點 repo 定位與時序、檔案架構、SKILL.md 的工作流與工法、輸出型態、驗證機制、安裝與相容 agent；供 C2 補「輸出規格細節／反爬無關」與替代方案 DA 表所需的機制對照。影片逐字稿不可得（Step 1 已記），不以影片補。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh api repos/wheresryan22/anatomy` | 取 metadata | 定位、時序、授權 | created 2026-10-08、pushed 2026-10-15、branch `main`、size 1,699 KB、MIT、JavaScript |
| 同上 + `gh repo view`（欄位修正後） | 取計數 | 熱度 | 14,187★／1,074 forks／41 open issues／subscribers 34 |
| `gh api .../git/trees/main?recursive=1` | 取檔案結構 | 主要文件盤點 | 見下方架構 |
| `gh api .../releases` | 取版本 | 發佈節奏 | 僅 2 版：v1.0.0（2026-10-10）、v1.1.0（2026-10-12）；CHANGELOG 有 Unreleased |
| `gh api .../contributors` | 取協作 | 維護樣態 | 10 人；wheresryan22 90、rudycelekli 41、aakash-kharb 8 |
| 讀 `README.md`（25.8 KB） | 取定位與用法 | 一手 | 定位、安裝矩陣、三型輸出、Limits 齊 |
| 讀 `SKILL.md`（31.6 KB） | 取工作流與工法 | 核心機制 | 10 步工作流、三大工法、References 索引齊 |
| 讀 `CHANGELOG.md` | 取沿革 | 史實 | 原名 `isometric-objects`，2026-10-08 改名 Anatomy |
| 讀 `evals/evals.json`（5 例）、`agents/openai.yaml` | 取驗收與 agent 契約 | 佐證 | 5 條 eval 明列 expected_output |
| 抓官網 `skills.wheresryan.sh/anatomy` | 補背景 | 作者意圖 | 動機、耗時實測、33 圖 collection、npm `anatomy-figures` |

**repo 檔案架構（一手）**

| 目錄 | 內容 |
|---|---|
| 根 | `SKILL.md`（技能本體）、`README.md`、`CHANGELOG.md`、`CONTRIBUTING.md`、`LICENSE`(MIT)、`SECURITY.md`、`CODE_OF_CONDUCT.md` |
| `kit/` | 繪圖庫：`iso-kit.ts`／`.mjs`（相機、solids、SVG renderer、card／page、CSS）、`lathe.mjs`（旋成體）、`tube.mjs`（管路纜線）、`audit.mjs`（92 KB 幾何稽核）、`gl.mjs`（WebGL）、`turn*.mjs`（3D，beta）、`react/` |
| `references/` | 8 篇長文：`craft.md`(50 KB) `kit.md`(67 KB) `webgl.md`(61 KB) `3d.md`(44 KB) `verify.md` `motion.md` `react.md` `walkthrough.md` `publish.md` |
| `scripts/` | headless Chrome 檢查：`capture.mjs` `drive.mjs` `lines.mjs` `turn-check.mjs` `turn-bench.mjs` `publish.mjs` `session.mjs`；另有數十支 `*.test.mjs` |
| `examples/` | 8 個成品圖：`dial-indicator`（最小 ~300 行）、`desk-computer`、`arcade-cabinet`、`raptor-engine`、`ripple-tank`、`test-rig`、`spot-plate`、`turning-dial` |
| `evals/` | `evals.json`（5 條 prompt＋expected_output） |
| `agents/` | `openai.yaml`（Codex display name） |
| `.github/` | `workflows/ci.yml`（重build 全部 example、改動即 fail）、issue forms、PR template |

**核心機制（SKILL.md 一手）**

| 面向 | 內容 |
|---|---|
| 核心思想 | 「**The object is the explanation**」——不畫 boxes/arrows/labels，要發明一台「作動即概念」的真實機械（測試台、儀表、鎖、分信桌） |
| 工作流 | 10 步：Size→Truth first→Invent object→Parts list→Plan world→Build geometry once→Paint back-to-front→Frame→Make it live→Verify like a critic |
| 規模分級 | Figure（40–80 件零件，≤1 個 WebGL 層）、Hero（80–150）、Epic（>150，未經本人選不開工） |
| 三型輸出 | **SVG**（核心，四色調 shading）、**SVG+WebGL**（火焰/水/焦散，夾在前後 SVG 之間、同相機）、**3D**（beta，真 3D 旋轉重投影） |
| 相機 | 等角（isometric），預設方位角 45°、仰角 30° |
| 驗證 | 幾何稽核 `kit/audit.mjs`（`--audit` 須 `audit passed`、無管線穿模、深度序正確）＋線端檢查 `scripts/lines.mjs`（0 懸空線）＋headless Chrome 截圖/contact sheet/4× 特寫 |
| 交付形態 | framework-free Node build script 產 standalone HTML／lone SVG，或 React/Next 元件；成品即「你自己的原始碼」 |
| 安裝 | `npx skills add wheresryan22/anatomy -g`（vercel-labs `skills` CLI）／git clone／下載 zip；Node ≥20.10、檢查需 Chrome、React 輸出需 React 18+；零 npm 依賴 |
| 相容 agent | Agent Skills 格式（agentskills.io）：Claude Code、Antigravity、OpenCode、Codex、MiniMax Code |
| Limits（自陳） | 非圖表庫（無座標軸/資料繪圖）、只畫機械儀器非人/地圖、刻意慢、shader 需 WebGL |

**背景脈絡（一手）**

- 作者 Ryan（@wheresryan22）；2026-10-08 前私下開發名 `isometric-objects`，同日改名 Anatomy 並公開 repo，同日發 v1.0.0，兩天後 v1.1.0（加 OpenCode/Codex）。
- 官網自陳耗時實測：Watch 1h54m、Seasons 1h57m、Raptor 10h33m（首版 38 分）、Turbofan 14h（首版 4h41m＋5 輪 review）；collection 33 圖；另有 npm 套件 `anatomy-figures`（官網頁面展示，repo tree 未見，疑為另附發佈）。
- 與 MyBrain 軸：同軸對照 `archify`（採用）、`diagram-design`（不採用）；與 `img2threejs`(245) 同屬「生成視覺/3D」軸。

**待 C2 補**：kit API 與 audit 內部規格、craft 工法細節（painter's order、tone 表）、WebGL 層與 3D beta 的實作契約、替代方案 DA 表（Mermaid/diagram-design/archify/D3 或 img2threejs）。

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata | gh api 全欄位 | 完整（計數較 issue 略升：14,132→14,187★、1,068→1,074 forks） |
| 授權/語言 | license 欄位、language | MIT、JavaScript（主要） |
| 發佈時序 | releases＋CHANGELOG | v1.0.0/v1.1.0 兩版；Unreleased 已含 Antigravity/MiniMax |
| 檔案架構 | git tree recursive | 全樹盤點完成（kit/references/scripts/examples/evals） |
| 核心機制 | 讀 SKILL.md | 10 步工作流、三型輸出、稽核機制齊 |
| 背景脈絡 | CHANGELOG＋官網 | 原名、改名日、作者意圖、耗時實測取得 |
| 影片觀點 | YouTube transcripts disabled | 不可得，維持缺口 |

## 其中的決斷點

| 意思決定面向 | 可選選項條列 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 資料來源 | clone 全 repo／gh api＋raw 讀關鍵檔／只讀 README | gh api metadata＋raw 讀 README/SKILL/CHANGELOG/evals | 免 clone 開銷（repo 含 ~10 MB examples）；關鍵檔即足以還原機制 |
| 是否讀 kit/scripts 原始碼 | C1 全讀／C1 讀清單、C2 讀實作 | C1 僅盤點檔名與角色，實作留 C2 | C1 目標為 metadata 與主要文件；audit/webgl 細節屬 C2 |
| 官網是否採信 | 只信 repo／repo＋官網互證 | 兩者互證，官網標為「作者自陳」 | repo 為一手；官網補動機與耗時，屬自陳非客觀數據 |
| 影片立場 | 揣測補上／明列缺口 | 明列缺口，不揣測 | transcripts disabled，無從查證 |
| 替代方案 DA 表 | C1 先列／留 C2 | 留 C2 完整化 | C1 已鎖定同軸對照清單，DA 表需機制對讀後再成 |
| 計數落差 | 沿用 issue 數字／實查更新 | 實查更新並註記 | API 為即時值，issue 為 2026-10-17 舊值 |
