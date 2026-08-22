# 245_R1_step2-plan_C1.md

## 狀況理解

- Step 1 判定標的為 **img2threejs**（`https://github.com/img2threejs/img2threejs`）：以單張參考圖為輸入，產出可於 Three.js 渲染之 3D 模型。
- 本 sub-step C1 依 document skill 標準動作，先取得 repo metadata 與主要文件，為後續分析（問題、背景、核心機制、替代方案）建立資料基礎。
- R1 首輪，無先前輪次重複需求；執行「repo metadata + 主要文件 + 背景脈絡」三動作。
- 網路搜尋未遭遇反爬，全程用 `gh api`／`curl` 成功，不需 CDP。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view img2threejs/img2threejs --json` | 取得 repo metadata | 取得 stars、license、分支、描述、建立時間 | 成功：12,695 stars；Apache-2.0；`main`；Python；建立於 2026-07-15；描述「Rebuild the object in a reference image as a code-only, procedural, quality-gated, animation-ready Three.js model」 |
| `gh api .../contents/` 根目錄 | 列舉 repo 結構 | 定位 README 與關鍵子文件 | 取得根層：README、SKILL.md、CLAUDE.md、CHANGELOG、ROADMAP、docs/、forge/、grimoire/、scripts/、skills/、integrations/ |
| `curl` 取 README.md | 讀取主說明文件 | 取得 pitch、pipeline、scripts、limits | 318 行。核心：以程式重建非 mesh，token 高效，agent-agnostic |
| `curl` 取 SKILL.md | 讀取核心 skill 文件（權威工作流） | 取得完整 pipeline 與 gates | 613 行。詳述：intake→assessment→spec→pass-gated build→vision review loop；Divine Eye、strict-quality、cs2、character、token 設計 |
| `curl` 取 docs/ARCHITECTURE.md | 取得機制圖與執行細節 | 取得 pipeline diagram、scripts 表、gates | 135 行。mermaid 流程、build pass 順序、Divine Eye 等 gates、token 效率理由 |
| `curl` 取 docs/TOKEN_COST.md | 取得 token 成本模型 | 量化效率主張 | 單物件 ~80k-180k tokens；render-review loop 為最大宗 |
| `curl` 取 docs/RESEARCH_TRELLIS2_TO_IMG2THREEJS.md | 補背景與替代方案（自評研究註記） | 提供核心與替代對照 | 明確定義兩系統對比（TRELLIS.2 可表示性 vs img2threejs 語義），為 §4 替代方案提供素材 |
| `curl` 取 CLAUDE.md／ROADMAP.md | 補驗證命令與版本脈絡 | 確認 verify 命令、路線圖 | 得 `python3 -m unittest discover -s forge/tests`；v1.0→v1.4.4 與長線 v2.0 世界生成 |

### 關鍵文件擷取內容要點

| 文件 | 內容要點 |
|---|---|
| README.md | 輸入單張參考圖→輸出 TypeScript `createXxxModel(spec)` factory 回傳 `THREE.Group`；pass 順序 blockout→…→optimization；「純 code、非 photogrammetry/藝術包下載」；Apache-2.0；v1.4.4 |
| SKILL.md | 權威流程：`forge/next.py` local state gate → probe → assessment（class/complexity/qualityContract）→ detail inventory → strict-quality validate → locked build pass → browser render → make_comparison_sheet → append_review（continue/refine-spec/refine-code/request-input/stop）；CS2 與 character profile 另加 gates |
| ARCHITECTURE.md | mermaid 主流程；gates：suitability、pre-spec/strict-quality、screenshot feedback、action-ready、attachment、material/lighting、assembly、Divine Eye（零 token 多訊號、hard 先於 soft）、correction_loop bounded |
| TOKEN_COST.md | 單物件總 token ~80k-180k；render-review loop 5-8 cycles 佔主成本（~30k-70k） |
| RESEARCH note | 定位 img2threejs = 最大語義／最小可表示力（14 種 primitive）；與 TRELLIS.2（O-Voxel、可表示力大、零語義）反向 |

## 動作結束後的現狀

| 驗證面向 | 內容與方式 | 結果 |
|---|---|---|
| metadata | `gh repo view` JSON 欄位齊全 | 12,695★、Apache-2.0、Python、2026-07-15 建立、repo 於 2026-08-22 仍更新 |
| 主要文件 | README / SKILL / ARCHITECTURE / TOKEN_COST 均成功抓取 | 全部讀取，無 404 |
| 背景資料 | 研究註記、ROADMAP | 取得核心替代與版本脈絡 |
| 反爬 | 全程 `gh api`／`curl` | 未觸發，不需 CDP |
| 本 sub-step 產出 | memory/log/245_R1_step2-plan_C1.md | 已產出 |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| C1 範圍切法 | (a) 一 sub-step 全部文件；(b) 拆 C1 metadata+主文件、C2 背景/替代 | 本次一次抓齊 metadata+README+SKILL+ARCH+dense 補充 | C1 定義為「取得 repo 資料與主要文件」，一次完成；後續 C2 再專注背景／替代方案／硬性驗證資料 |
| 抓取對象優先 | (a) 只讀 README；(b) README+SKILL+ARCHITECTURE | (b) 三份核心 | README 為 pitch、SKILL 為實際工作流、ARCHITECTURE 為機制圖，三者互相補足，缺一則機制理解不完整 |
| 背景資料來源 | (a) 外部搜尋 new； (b) 先取 repo 內含之 RESEARCH note | (b) repo 內研究註記先行 | repo 自含 TRELLIS.2 對照研究，是現成背景材料，避免重複外部搜尋；外部替代再於 C2 補 |
