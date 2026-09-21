# 272_R1_step2-plan_C1.md

## 狀況理解

C1 為 Step 2 第一個 sub-step：對標的 `ayghri/i-have-adhd` 執行「標準調研動作」的前段——取得 repo metadata、擷取主要文件（README / SKILL.md / AGENTS.md / plugin 實作）、並補查背景脈絡。Step 1 已確認：此標的與使用者第二大腦已判「試用」的 **Caveman** 屬同類（讓 coding agent 輸出更簡潔的 system-prompt skill），屬「下一步清單」第 69 行 context 治理比較軸。因此 C1 的擷取重點在於解析它的**具體機制**（規則內容、如何注入、跨 runtime 擴散、是否有實證評估），以利後續 C2 與 Caveman 對照。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view` metadata | 取得 repo 基礎資訊 | 定位技術屬性 | MIT、Python、49.6k stars、created 2026-05-13、updated 2026-09-21（近期仍活躍）、未封存；description 直指「stop your coding agent from burying the answer」 |
| 列 repo 根目錄 + 遞迴 tree | 了解專案結構 | 找出關鍵子文件 | 多元 runtime：Claude/Codex/Cursor/Gemini/Qwen/Kimi/OpenCode/Grok（`plugin.json`）、Pi/OMP（`extensions/`）、hooks、evals、tests、多語系 README（10 種） |
| 擷取 README.md | 掌握目的與行為 | 理解「做什麼／改變什麼」 | 「Before/After」對照：before 是贅述式回覆、after 是「先給動作、編號步驟、具體時限、無問候語」；聲明 10 條規則、源自《The Adult ADHD Tool Kit》 |
| 擷取 SKILL.md（canonical） | 取得規則來源 | 理解核心機制 | 10 條規則＋「何時打破規則」＋pre-send check；frontmatter `disable-model-invocation: true`，需 `/i-have-adhd` 觸發、會話內持續至「stop adhd mode」 |
| 擷取 AGENTS.md | 了解 runtime 擴散架構 | 定位「跨平台」如何實作 | 標示 `skills/i-have-adhd/SKILL.md` 為單一真相來源（source of truth），其餘平台為 mirror/adapter；每 runtime 有獨立 entry point |
| 擷取 `.opencode/plugins/i-have-adhd.mjs` | 看 OpenCode 側實作 | 驗證注入機制 | 兩種模式：隨選（註冊 skills + `/i-have-adhd` command）與 always-on（`~/.config/opencode/.i-have-adhd-always` 存在則每 turn 把規則體附到 system prompt）；strip frontmatter 後注入 |
| 擷取 `evals/RESULTS.md` | 確認是否有實證 | 判斷「效果有無被量化」 | 有 3-trial/14-case 盲評：candidate 加權 4.473 vs baseline 4.045（Δ+0.427），Concision +1.143、Actionability +0.714；**release gate FAILED**（仍有 3 blocking findings，規則寫死「有任何 blocker 即失敗」） |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo 有效性 | `gh repo view` | 存在、未封存、MIT、49.6k stars、2026-09-21 仍更新 |
| 核心機制 | 讀 SKILL.md + plugin | 規則注入（system prompt）＋隨選/always-on 兩模式；規則在會話內持續 |
| 跨平台 | 讀 AGENTS.md + tree | 單一 SKILL.md 為真相來源，8+ runtime adapter（Claude/Codex/Cursor/Gemini/Qwen/Kimi/OpenCode/Grok/Pi/OMP） |
| 實證效果 | 讀 evals/RESULTS.md | 有盲評，candidate 全面勝出但 release gate 仍失敗（blk 3） |
| 定位 | 對照 Step 1 | 與 Caveman 同軸（輸出簡潔 skill），但有「ADHD 認知理由化」＋「跨平台 plugin 基礎設施」＋「evals」三項差異 |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| 擷取範圍 | 僅 README / 深入 plugin+evals | 深入 plugin+evals | 機制（注入、persistence）與實證是與 Caveman 對照的關鍵差異點，僅 README 無法支撐 |
| 真相來源 | 各平台檔個別讀 / 以 SKILL.md 為準 | 以 SKILL.md 為準 | AGENTS.md 明確標示 SKILL.md 是 source of truth，其餘為 mirror，避免重複且確保抓到規則全貌 |
| 背景補查深度 | 只列通用知識 / 併查 ADHD 認知理由 | 併查 ADHD 認知理由 | SKILL.md 自述 5 個 ADHD 閱讀事實（working memory、starting friction、dopamine 等），是「為什麼這樣設計」的內文證據，C2 應展開 |
| C2 方向 | 直接寫報告 / 先對照 Caveman 與替代方案 | 對照 Caveman 與替代方案 | 使用者已把同類工具放入比較軸，C1 資料顯示 i-have-adhd 具 plugin 基建＋evals 差異，C2 需做成對照表 |
