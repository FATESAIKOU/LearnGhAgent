# pxpipe — 視覺上下文壓縮代理

> 分析標的：https://github.com/teamchong/pxpipe
> 分析日期：2026-07-25

---

## 1. 這個技術解決什麼問題？

**LLM API 的輸入 Token 成本過高**，尤其是在 Claude Code 這類 agent 系統中，每次請求都會重複發送大量穩定的上下文內容（系統提示詞、工具定義、歷史對話），導致帳單快速膨脹。

具體來說，Claude Code 每次呼叫 `/v1/messages` 時會重新發送：
- 系統提示詞（system prompt）
- 工具定義（tool definitions / tool docs）
- 歷史對話（older conversation history）
- 工具輸出（tool results）

這些內容在多次請求間高度重複，但每次仍按完整文字 Token 計費。pxpipe 的目標是**在不顯著降低模型推理品質的前提下，減少輸入 Token 數量**。

**模糊之處**：此問題的嚴重程度取決於工作負載的「Token 密度」。密集內容（程式碼、JSON、日誌）的壓縮效益遠大於稀疏內容（英文散文）。pxpipe 並非通用解決方案，而是針對特定工作負載類型的優化。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **LLM Token 計費規則**：文字 Token 按字元數計費（約 1 token/4 字元英文，密集內容可達 1 token/1 字元）。圖像 Token 按像素面積計費（Claude 以 28×28 像素為一個 patch，一張 1568×728 的圖片約 1456 個視覺 Token），**與圖像內含的文字量無關**。
- **資訊密度差價**：密集文字（程式碼、JSON）在文字通道中約 1 字元/Token，在圖像通道中約 3.1 字元/視覺 Token。這創造了套利空間。
- **Claude Code 的請求模式**：每次請求都重新發送完整的系統提示詞 + 工具定義 + 歷史記錄，即使這些內容在多次請求間完全沒有變化。
- **Anthropic Prompt Caching**：提供 prefix-based 快取（cache read 0.1×、cache write 1.25×），但快取鍵基於精確的位元組內容，任何變動都會導致快取失效。

### 通用技術背景

- **多模態大模型（VLM）的視覺機制**：VLM 不是 OCR。它將圖像切割成固定大小的 patch，每個 patch 投影為一個連續的 embedding，語言模型在這些 embedding 上做注意力機制。沒有離散字元識別步驟，因此沒有「置信度低」的概念——錯誤是無聲的幻覺（silent confabulation）。
- **Agent 系統的上下文管理困境**：Agent 需要長期上下文來維持任務連貫性，但完整保留所有歷史的 Token 成本過高。現有方案（如 `/compact`）使用 LLM 摘要壓縮歷史，但這是**有損且不可逆**的——原始位元組被丟棄。
- **DeepSeek-OCR（2025年10月）**：訓練專用光學編碼器做長上下文壓縮，證明視覺通道可用於文字壓縮，但當時的通用模型無法讀取高密度渲染。

---

## 3. 這個技術是如何解決該問題的？

### 整體架構

pxpipe 是一個本地代理（local proxy），攔截 Claude Code 發送給 Anthropic API 的請求，在請求離開本機前將大量上下文內容即時渲染為 PNG 圖片，再以圖片形式發送。

```
Claude Code → pxpipe proxy (127.0.0.1:47821) → Anthropic API
                 │
                 ├── 靜態 slab（系統提示詞 + 工具定義）→ 渲染為圖片
                 ├── 舊歷史記錄 → 渲染為圖片
                 ├── 大工具輸出 → 渲染為圖片
                 └── 近期對話 → 保持純文字（精確工作區）
```

### 核心機制

#### 3.1 極致渲染壓縮（`src/core/render.ts`）

- **字體**：使用 Spleen 5×8 點陣字體（5 像素寬 × 8 像素高），極度緊湊
- **頁面尺寸**：1568 × 728 像素（1.14 MP），恰好低於 Anthropic 的降採樣閾值，確保 WYSIWYG
- **容量**：每頁 312 列 × 90 行 = **28,080 個字元**
- **Reflow 機制**：將原始換行符替換為 ↵ 標記，讓文字自動填滿行寬（填充率從 ~29% 提升至 75-80%）
- **灰階抗鋸齒**：使用 AA 灰階圖集提升字形辨識度
- **Glyph 逃逸**：圖集中不存在的 codepoint 以 `[U+HEX]` 形式保留

#### 3.2 分層記憶策略（`src/core/transform.ts`）

pxpipe 將請求內容分為三個層級，採用不同的處理策略：

| 層級 | 內容 | 處理方式 | 原因 |
|------|------|----------|------|
| **靜態 slab** | 系統提示詞、工具定義、CLAUDE.md | 渲染為圖片 + cache_control | 跨請求穩定，適合快取 |
| **近期對話** | 最近幾輪的 user/assistant 訊息 | 保持純文字 | 需要 100% 精確度 |
| **舊歷史** | 已完成的工具呼叫回合 | 折疊（collapse）後渲染為圖片 | 只需大意記憶 |

**keepSharp 逃生口**：呼叫方可指定哪些內容必須保持為純文字（如雜湊值、ID、金鑰），這些內容不會被渲染為圖片。

#### 3.3 Cache 對齊（`src/core/transform.ts` + `docs/CACHING_AND_SAVINGS.md`）

pxpipe 不新增 cache_control 標記，而是**將呼叫方既有的標記搬移到對應圖片區塊的末尾**。這確保：

- 快取斷點位置不變（仍在穩定內容的結尾）
- 圖片前綴與文字前綴使用同一個快取條目
- 快取折扣（0.1× cache read）不會被重複計算為 pxpipe 的節省

轉換後的請求形狀：
```
system:
  帳單行 / 動態上下文 / 其他純文字系統內容

messages[0] user:
  圖片區塊
  圖片區塊
  圖片區塊 + cache_control  ← 搬移至此
  [End of rendered context.]
  原始使用者內容 / 即時對話
```

#### 3.4 盈利閘門（Profitability Gate）

每個區塊在渲染前會計算：

```
imageTokens = 圖像 Token 成本（基於像素面積）
textTokens = 文字 Token 成本（基於字元數 × charsPerToken）

// 對稱燃燒懲罰（防止模式切換導致快取失效）
burnImageSide = priorWarmTokens × (1.25 - 0.10)
burnTextSide = priorWarmImageTokens × (1.25 - 0.10)

壓縮條件：imageTokens + burnImageSide < textTokens + burnTextSide
```

只有當圖像 Token 成本（含快取切換懲罰）低於文字 Token 成本時，才執行壓縮。

#### 3.5 歷史折疊（History Collapse）

對於 GPT/OpenAI Responses 路徑，pxpipe 會將已完成的工具呼叫回合折疊為歷史圖片：

- 最近的 N 個回合保持純文字
- 舊回合被渲染為圖片並附加到請求前綴
- 每個折疊回合的圖片保持穩定（相同的 cache key），實現跨回合快取

### 成本節省數據

| 指標 | 數值 | 來源 |
|------|------|------|
| 輸入 Token 減少 | ~68% | 生產流量測量（856k → 277k tokens） |
| 端到端帳單節省 | 59-70% | 13,709 請求快照（$100 → ~$41） |
| 密集內容密度 | 3.1 chars/vision-token | 生產渲染測量 |
| 文字密度（密集內容） | ~1.0 char/text-token | 生產流量測量 |
| Fable 5 上下文容量 | ~19.0M chars（4.8× 文字容量） | 1M token 視窗 |
| Gemini 3.6 Flash 容量 | ~21.3M chars（5.3× 文字容量） | 1M token 視窗 |

### 模型支援矩陣

| 模型 | 算術 (N=100) | Gist (N=98) | 狀態 (N=18) | 幻覺 (N=16) | 密集 Hex (N=15) | 預設狀態 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|
| `claude-fable-5` | **100/100** | **98/98** | **18/18** | **0/16** | **13/15** | ✅ 預設啟用 |
| `gemini-3.6-flash` | **100/100** | **98/98** | **18/18** | **0/16** | **14/15** | ✅ 預設啟用 |
| `gpt-5.6-sol` | 98/100 | 83/98 | 17/18 | 4/16 | 0/15 | ⚠️ 選擇加入 |
| `claude-opus-4-8` | 93/100 | — | — | — | 0/15 | ⚠️ 選擇加入 |
| `grok-4.5` | 82/100 | 83/98 | 13/18 | 0/16 | 0/15 | ⚠️ 選擇加入 |

### 已知限制

- **有損壓縮**：精確字串（12 位元十六進位雜湊）在 Fable 5 上 13/15，在 Opus 4.8 上 0/15。錯誤是**無聲幻覺**（silent confabulation），非錯誤回報。
- **byte-exact 內容必須保持純文字**：雜湊值、ID、金鑰、路徑等。
- **工作負載依賴**：密集內容（~1 char/token）獲益，稀疏散文（~3.5 chars/token）可能虧損。
- **PNG 編碼延遲**：大請求在發送前需額外渲染時間。
- **ASCII/Latin-1 測試充分**，CJK 支援較保守。

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|----------|-------------|---------------|-----------------|
| **Claude Code `/compact`** | 使用 LLM 將舊歷史摘要為散文摘要，丟棄原始內容 | 模型能正確摘要；使用者接受資訊損失 | 原始位元組不可恢復；摘要疊加摘要會累積誤差 | 減少歷史 Token 成本，但丟失精確細節 |
| **DeepSeek-OCR** | 訓練專用光學編碼器（~380M）+ 解碼器（~3B）做文字→圖像→文字壓縮 | 需要專用模型部署；編碼器/解碼器需針對目標模型微調 | 額外模型推理開銷；低壓縮比（<10×）時 ~97% 精確，高壓縮比（~20×）降至 ~60% | 專用模型可達較高精確度，但需額外基礎設施 |
| **Prompt Caching（Anthropic 原生）** | 基於 prefix 的快取機制，穩定前綴以 0.1× 費率重複使用 | 前綴必須位元組精確穩定；每次變動需以 1.25× 重新寫入 | 快取鍵對任何位元組變動敏感；跨會話快取有限 | 穩定前綴可大幅降低成本，但無法壓縮前綴本身的大小 |
| **Event-sourced Reducer（Codex 方案）** | 將對話歷史視為事件流，透過 reducer 折疊為結構化狀態圖，保留精確 payload | 需要事件溯源基礎設施；reducer 邏輯需覆蓋所有事件類型 | 診斷模式已實作但非即時；reducer 輸出仍可能為 prose 摘要 | 可恢復精確歷史，但 reducer 本身需 Token 成本 |

### 切入點差異

- **pxpipe vs `/compact`**：pxpipe 保留原始位元組（在 PNG 中），犧牲精確可讀性但保留可恢復性；`/compact` 丟棄原始位元組，犧牲內容但保留文字精確度。兩者都接受「舊歷史是有損的」這個前提，但損失方向相反。
- **pxpipe vs DeepSeek-OCR**：pxpipe 使用現成通用模型的視覺通道，不訓練任何參數；DeepSeek-OCR 訓練專用模型做同一件事。pxpipe 依賴模型供應商的視覺編碼器升級來改善，DeepSeek-OCR 可獨立優化。
- **pxpipe vs Prompt Caching**：兩者互補而非競爭。pxpipe 在快取之上運作，透過減少前綴大小來放大快取效益。pxpipe 不破壞快取（透過 cache 對齊），而是讓同一個快取條目容納更多內容。
- **pxpipe vs Event-sourced Reducer**：Reducer 是理論上的最優解（可恢復、可重播），但實作複雜度高。pxpipe 是工程上的實用解（利用現有視覺通道，零額外基礎設施）。

### 反證表

| 對 pxpipe 的常見質疑 | 專案方的回應 | 驗證 |
|---------------------|-------------|------|
| 「這不就是 OCR 嗎？」 | VLM 不是 OCR——沒有離散字元識別，錯誤是無聲幻覺 | `docs/NOT-OCR.md` 完整說明機制差異 |
| 「DeepSeek-OCR 證明這不可行」 | DeepSeek-OCR 證明通道可行，但當時無通用模型能讀；Fable 5 改變了這個前提 | FINDINGS.md 的 Opus 4.8 vs Fable 5 對比 |
| 「快取會失效」 | pxpipe 不新增快取標記，只搬移既有標記；快取對齊確保前綴穩定 | `docs/CACHING_AND_SAVINGS.md` 的對齊機制 |
| 「精確字串會讀錯」 | 承認此限制，提供 keepSharp 逃生口和 factsheet 保護 | 0/15 Opus vs 13/15 Fable 的 hex 測試 |
| 「這只是暫時的套利窗口」 | 同意，但指出模型視覺能力持續提升，窗口只會擴大 | 從 Opus 4.8 到 Fable 5 的 4× glyph 面積改善 |

---

## 5. User Q&A

### Q1：cache_control 是什麼東西？用來解決什麼問題？問題發生的背景？它如何解決問題？誰提出的？

**A**：

**定義**：`cache_control` 是 Anthropic Messages API 中，用於標記 prompt 快取斷點（cache breakpoint）的參數。格式為 `{"type": "ephemeral"}`，可附加在 `tools`、`system`、`messages` 陣列中的個別 content block 上。

**提出者**：Anthropic（該公司於 2025 年推出 Prompt Caching 功能時引入）。

**解決的問題**：LLM API 每次請求都重新處理完整 prompt，即使前綴內容在多次請求間完全相同。這導致：
- 重複計算相同內容的注意力機制（浪費算力）
- 重複計費（浪費成本）
- 增加端到端延遲

**問題發生的背景**：LLM 的 stateless 設計——API 不保留任何跨請求狀態，每次呼叫 `/v1/messages` 都是獨立請求。Agent 系統（如 Claude Code）每次請求都重新發送完整的系統提示詞 + 工具定義 + 歷史記錄，這些內容在多次請求間高度重複。

**解決機制**：

| 步驟 | 說明 |
|------|------|
| 1. 標記斷點 | 在穩定前綴的最後一個 content block 加上 `cache_control: {"type": "ephemeral"}` |
| 2. 寫入快取 | 首次請求時，系統計算從 prompt 開頭到斷點的前綴 hash，以 1.25× 費率寫入快取 |
| 3. 讀取快取 | 後續請求若前綴 hash 匹配，則以 0.1× 費率讀取快取，只處理斷點之後的新內容 |
| 4. Lookback | 若斷點 hash 不匹配，系統向後最多檢查 20 個 block，尋找先前寫入的快取條目 |

**定價**：

| 項目 | 倍率（相對於 base input） |
|------|--------------------------|
| Base input | 1.0× |
| Cache write（5 分鐘 TTL） | 1.25× |
| Cache write（1 小時 TTL） | 2.0× |
| Cache read | 0.1× |

**pxpipe 與 cache_control 的關係**：pxpipe 不新增 cache_control 標記，而是將呼叫方既有的標記搬移到對應圖片區塊的末尾。這確保快取斷點位置不變，圖片前綴與文字前綴使用同一個快取條目，快取折扣不會被重複計算為 pxpipe 的節省。

**結論**：`cache_control` 是 Anthropic 提出的 prompt 前綴快取機制，透過標記斷點讓重複前綴以 0.1× 費率重複使用。pxpipe 利用此機制但不新增標記，只搬移既有標記以維持快取對齊。

---

### Q2：導入 pxpipe 前後，傳輸給 LLM API 的具體全體 prompt 會長什麼樣子？請針對各種場景舉例，最後總結。

**A**：

以下以 Anthropic Messages API 格式為例，展示三種場景下導入 pxpipe 前後的 prompt 形狀。

#### 場景一：一般對話（無工具呼叫）

**導入前（純文字）**：
```json
{
  "model": "claude-fable-5",
  "system": [
    {"type": "text", "text": "你是 Claude Code，Anthropic 的 CLI 工具。\n\n## 規則\n- 使用 TypeScript\n- 遵循 ESLint 規則\n\n# Environment\nWorking directory: /home/user/project\nPlatform: linux\nToday's date: 2026-07-25", "cache_control": {"type": "ephemeral"}}
  ],
  "messages": [
    {"role": "user", "content": "幫我看看這個檔案有什麼問題"}
  ]
}
```
- 系統提示詞：~800 tokens（含規則 + 環境資訊）
- 使用者訊息：~10 tokens
- 總計：~810 tokens（前綴 ~800 可快取）

**導入後（pxpipe 代理）**：
```json
{
  "model": "claude-fable-5",
  "system": [
    {"type": "text", "text": "x-anthropic-billing-header: ..."}
  ],
  "messages": [
    {"role": "user", "content": [
      {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0KGgo..."}},
      {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0KGgo..."}, "cache_control": {"type": "ephemeral"}},
      {"type": "text", "text": "[End of rendered context.]"},
      {"type": "text", "text": "幫我看看這個檔案有什麼問題"}
    ]}
  ]
}
```
- 系統提示詞：僅帳單行 ~5 tokens
- 圖片區塊：2 張 PNG，每張 ~1568×728 px，約 1456 視覺 tokens/張，共 ~2912 tokens
- 使用者訊息：~10 tokens
- 總計：~2927 tokens（前綴 ~2912 可快取）
- 節省：文字 ~800 tokens → 圖片 ~2912 tokens，**此場景反而變貴**（因為一般對話文字量小，圖片固定成本高）

---

#### 場景二：工具呼叫（含系統提示詞 + 工具定義 + 歷史記錄）

**導入前（純文字）**：
```json
{
  "model": "claude-fable-5",
  "tools": [
    {"name": "Read", "description": "讀取檔案內容", "input_schema": {"type": "object", "properties": {"file_path": {"type": "string"}}}},
    {"name": "Edit", "description": "編輯檔案", "input_schema": {"type": "object", "properties": {"file_path": {"type": "string"}, "old_string": {"type": "string"}, "new_string": {"type": "string"}}}},
    {"name": "Bash", "description": "執行 shell 命令", "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}}}
  ],
  "system": [
    {"type": "text", "text": "你是 Claude Code...\n\n## 規則\n- 使用 TypeScript\n- 遵循 ESLint 規則\n\n<available_skills>\n<skill><name>explore</name><description>探索程式碼庫</description></skill>\n</available_skills>", "cache_control": {"type": "ephemeral"}}
  ],
  "messages": [
    {"role": "user", "content": "幫我找到所有 TypeScript 檔案"},
    {"role": "assistant", "content": [{"type": "tool_use", "id": "tu_1", "name": "Bash", "input": {"command": "find . -name '*.ts'"}}]},
    {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "tu_1", "content": "src/index.ts\nsrc/utils.ts\nsrc/core/render.ts"}]},
    {"role": "assistant", "content": "找到了 3 個 TypeScript 檔案"},
    {"role": "user", "content": "幫我看看 render.ts 的內容"}
  ]
}
```
- 工具定義：~300 tokens
- 系統提示詞：~1200 tokens
- 歷史記錄：~150 tokens
- 使用者訊息：~10 tokens
- 總計：~1660 tokens（前綴 ~1650 可快取）

**導入後（pxpipe 代理）**：
```json
{
  "model": "claude-fable-5",
  "tools": [
    {"name": "Read", "description": "讀取檔案內容", "input_schema": {"type": "object", "properties": {"file_path": {"type": "string"}}}},
    {"name": "Edit", "description": "編輯檔案", "input_schema": {"type": "object", "properties": {"file_path": {"type": "string"}, "old_string": {"type": "string"}, "new_string": {"type": "string"}}}},
    {"name": "Bash", "description": "執行 shell 命令", "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}}}
  ],
  "system": [
    {"type": "text", "text": "x-anthropic-billing-header: ..."}
  ],
  "messages": [
    {"role": "user", "content": [
      {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0KGgo..."}},
      {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0KGgo..."}, "cache_control": {"type": "ephemeral"}},
      {"type": "text", "text": "[End of rendered context.]"},
      {"type": "text", "text": "幫我找到所有 TypeScript 檔案"},
      {"type": "tool_use", "id": "tu_1", "name": "Bash", "input": {"command": "find . -name '*.ts'"}},
      {"type": "tool_result", "tool_use_id": "tu_1", "content": "src/index.ts\nsrc/utils.ts\nsrc/core/render.ts"},
      {"type": "text", "text": "找到了 3 個 TypeScript 檔案"},
      {"type": "text", "text": "幫我看看 render.ts 的內容"}
    ]}
  ]
}
```
- 系統提示詞：僅帳單行 ~5 tokens
- 工具定義：~300 tokens（保持純文字，因工具定義需精確）
- 圖片區塊：2 張 PNG，~2912 視覺 tokens
- 近期對話（純文字）：~160 tokens
- 總計：~3377 tokens（前綴 ~3212 可快取）
- 節省：文字 ~1660 tokens → 圖片 + 工具 + 近期對話 ~3377 tokens，**此場景仍略貴**（但歷史越長，節省越明顯）

---

#### 場景三：大工具輸出（pxpipe 最大效益場景）

**導入前（純文字）**：
```json
{
  "model": "claude-fable-5",
  "tools": [/* 3 個工具定義，~300 tokens */],
  "system": [
    {"type": "text", "text": "你是 Claude Code...\n\n## 規則\n- 使用 TypeScript\n- 遵循 ESLint 規則\n\n<available_skills>...</available_skills>", "cache_control": {"type": "ephemeral"}}
  ],
  "messages": [
    {"role": "user", "content": "執行測試並回報結果"},
    {"role": "assistant", "content": [{"type": "tool_use", "id": "tu_1", "name": "Bash", "input": {"command": "npm test"}}]},
    {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "tu_1", "content": "PASS src/core/render.test.ts (5.2s)\nPASS src/core/transform.test.ts (3.8s)\nPASS src/core/baseline.test.ts (4.1s)\n\nTest Suites: 3 passed, 3 total\nTests: 47 passed, 47 total\nSnapshots: 0 total\nTime: 13.1s\n\n# 以下是詳細的覆蓋率報告\n...（約 25000 字元的詳細輸出）"}]
    },
    {"role": "assistant", "content": "所有測試通過"},
    {"role": "user", "content": "幫我分析覆蓋率報告"}
  ]
}
```
- 工具定義 + 系統提示詞：~1500 tokens
- 歷史記錄（含大工具輸出 25000 字元）：~12500 tokens
- 使用者訊息：~10 tokens
- 總計：~14010 tokens（前綴 ~14000 可快取）

**導入後（pxpipe 代理）**：
```json
{
  "model": "claude-fable-5",
  "tools": [/* 3 個工具定義，~300 tokens */],
  "system": [
    {"type": "text", "text": "x-anthropic-billing-header: ..."}
  ],
  "messages": [
    {"role": "user", "content": [
      {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0KGgo..."}},
      {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0KGgo..."}, "cache_control": {"type": "ephemeral"}},
      {"type": "text", "text": "[End of rendered context.]"},
      {"type": "text", "text": "執行測試並回報結果"},
      {"type": "tool_use", "id": "tu_1", "name": "Bash", "input": {"command": "npm test"}},
      {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0KGgo..."}},
      {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0KGgo..."}},
      {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0KGgo..."}},
      {"type": "text", "text": "所有測試通過"},
      {"type": "text", "text": "幫我分析覆蓋率報告"}
    ]}
  ]
}
```
- 系統提示詞：僅帳單行 ~5 tokens
- 工具定義：~300 tokens
- 靜態 slab 圖片：2 張 PNG，~2912 視覺 tokens
- 近期對話（純文字）：~20 tokens
- 大工具輸出圖片：3 張 PNG（25000 字元 / 28080 字元每頁 ≈ 1 頁，但 pxpipe 使用 dense 模式），~4368 視覺 tokens
- 總計：~7605 tokens（前綴 ~7595 可快取）
- 節省：文字 ~14010 tokens → 圖片 ~7605 tokens，**節省約 46%**

---

#### 總結

| 場景 | 導入前（文字 tokens） | 導入後（圖片 tokens） | 節省比例 | 關鍵因素 |
|------|:---:|:---:|:---:|---------|
| 一般對話（短） | ~810 | ~2927 | **-261%**（變貴） | 文字量小，圖片固定成本高 |
| 工具呼叫（中等） | ~1660 | ~3377 | **-103%**（略貴） | 工具定義 + 近期對話保持純文字 |
| 大工具輸出（密集） | ~14010 | ~7605 | **+46%**（節省） | 大工具輸出轉圖片效益最大 |
| 生產流量平均 | ~25000 | ~2700（僅 slab） | **+59-70%** | 含歷史折疊 + 快取命中 |

**關鍵結論**：
- pxpipe 不是在所有場景都省錢——短對話反而更貴
- 節省來自「密集文字轉圖片的資訊密度套利」：密集文字 ~1 char/token，圖片 ~3.1 chars/vision-token
- 近期對話（最後幾輪）保持純文字以確保精確度，只有舊歷史和靜態內容轉圖片
- 快取命中時效益更大：圖片前綴 ~2700 tokens 以 0.1× 計費 vs 文字前綴 ~25000 tokens 以 0.1× 計費
- pxpipe 的盈利閘門（profitability gate）會自動跳過不划算的區塊，避免場景一、二的情況
