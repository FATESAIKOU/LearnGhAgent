# search-from-mybrain：基於第二大腦的個人化上下文檢索 Skill

> 本報告解析 `search-from-mybrain` skill 的設計原理、運作機制與替代方案。此 skill 是 opencode 框架中用於查詢使用者個人上下文（身份、處境、決策歷史）的專用工具。

---

## 1. 這個技術解決什麼問題？

**LLM agent 缺乏使用者個人上下文，導致推薦與回答脫離使用者實際處境的問題。**

具體表現：
- agent 推薦技術方案時，不知道使用者已評估過哪些選項、結論是什麼
- agent 討論職涯取捨時，不知道使用者的角色定位、現職環境、長期目標
- agent 給出金融建議時，不知道使用者的投資原則與當前配置
- agent 回答人生議題時，不知道使用者的價值判斷與優先順序

`search-from-mybrain` 的目標：**讓 agent 在回答任何需要「知道他是誰」的問題之前，先從使用者的第二大腦取得相關上下文**。

---

## 2. 這個問題為什麼會發生？（背景）

### 2.1 LLM 的無狀態本質

LLM 本身是 stateless 的——每次對話都是獨立推理，不保留跨 session 的使用者記憶。即使在同一 session 內，使用者也不會主動提供完整的背景資訊（因為「知道自己是誰」是常識，使用者不會想到要告訴 agent）。

### 2.2 通用 agent 的資訊不對稱

- agent 擁有通用技術知識（網際網路訓練資料）
- agent 缺乏使用者個人知識（身份、處境、已做決策）
- 使用者預期 agent 能給出「針對我」的建議，但 agent 只能給出「針對一般人」的建議

### 2.3 現有解決方案的不足

| 方案 | 限制 |
|---|---|
| 使用者手動提供背景 | 每次都要重複，遺漏率高 |
| Agent 記憶功能（如 ChatGPT memory） | 自動擷取不可控，容易記錯或遺漏 |
| 靜態設定檔（如 AGENTS.md） | 只能寫規則，無法承載動態變化的個人事實 |

### 2.4 通用技術背景

- **Personalized AI** 是 LLM 應用層的核心挑戰之一
- 主流解法包括：system prompt 注入、RAG、fine-tuning、agent memory
- `search-from-mybrain` 屬於 RAG 變體，但資料來源是使用者自行維護的 markdown 知識庫

---

## 3. 這個技術是如何解決該問題的？

### 3.1 整體架構

```
使用者提問（需個人上下文）
  │
  ▼
┌─────────────────────────────────────┐
│  Step 1: 觸發 skill                  │
│  agent 偵測到問題需要「知道他是誰」    │
│  才能回答 → 呼叫 search-from-mybrain  │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│  Step 2: 更新鏡像                    │
│  refresh.sh 從 GitHub clone/pull     │
│  FATESAIKOU/MyBrain → /tmp/mybrain/  │
│  記錄 commit hash 供驗證             │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│  Step 3: 讀取骨幹檔                  │
│  先讀 bundle 中標了 ⚠️ 的骨幹檔       │
│  （直接回答「我是誰/在哪/要去哪」）    │
│  再 grep 關鍵詞補查                   │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│  Step 4: 回傳上下文給 agent           │
│  查到的內容標注信任層級與時間          │
│  agent 據此回答使用者問題              │
└─────────────────────────────────────┘
```

### 3.2 核心機制

**機制 A：鏡像同步（refresh.sh）**

```
git clone git@github.com:FATESAIKOU/MyBrain.git /tmp/mybrain/
git log --oneline -1  # 記錄 commit hash
```

- 每次搜尋前執行，確保使用最新版本
- 失敗時沿用既有副本（graceful degradation）
- commit hash 作為版本錨點，供後續驗證

**機制 B：分層檢索**

```
Layer 1: 骨幹檔（標了 ⚠️ tag 的檔案）
  → 直接回答三問：我是誰 / 我在哪裡 / 我要去哪
  → 優先讀取，建立基本 context

Layer 2: 關鍵詞 grep
  → 根據使用者問題提取關鍵詞
  → 搜尋所有 .md 檔案
  → 命中後讀取相關段落

Layer 3: 全文閱讀
  → 對 Layer 2 命中的檔案讀取全文
  → 取得完整論述與理由
```

**機制 C：信任層級標注**

```
查到的內容標注：
- 信任層級：human:fatesaikou stable（使用者定稿） / ai:assistant draft（AI 草稿）
- 時間戳：檔案最後修改時間
- ⚠️ 標記：直覺容易猜反的地方，必讀
```

### 3.3 虛擬碼

```
def search_from_mybrain(question):
    # Step 1: 更新鏡像
    try:
        refresh_mybrain_mirror()  # git pull
    except:
        use_existing_mirror()     # graceful degradation

    # Step 2: 讀取骨幹檔
    backbone_files = grep("骨幹", "/tmp/mybrain/")
    context = read_files(backbone_files)

    # Step 3: 關鍵詞檢索
    keywords = extract_keywords(question)
    matches = grep(keywords, "/tmp/mybrain/")
    for match in matches:
        file_content = read(match.path)
        context += annotate_trust_level(file_content)

    # Step 4: 回傳
    return context
```

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|---|---|---|---|---|
| **System Prompt 注入** | 將使用者背景寫入 system prompt（如 AGENTS.md、我.md） | 使用者需自行維護靜態描述檔 | 描述檔無法承載動態變化的事實；長度受限；需手動更新 | 簡單直接，但覆蓋率低 |
| **Agent Memory（如 ChatGPT Memory、MemGPT）** | agent 自動從對話中擷取使用者事實並存入向量資料庫 | 需 LLM provider 支援記憶功能；需足夠對話歷史 | 自動擷取不可控，可能記錯或遺漏；隱私風險；無法區分「使用者定稿」與「AI 草稿」 | 自動化程度高，但準確度與可控性低 |
| **RAG on 使用者文件** | 將使用者的筆記、日記、文件做向量化，每次查詢時做相似度檢索 | 使用者需有結構化或半結構化的個人文件；需建置 embedding pipeline | 語意檢索可能 miss 精確關鍵詞；無法區分信任層級；需維護向量資料庫 | 檢索彈性高，但缺乏結構化導航 |
| **Fine-tuned Persona Model** | 用使用者的歷史對話 fine-tune 一個專屬模型 | 需大量歷史對話資料；需 GPU 訓練資源；需定期重新訓練 | 訓練成本高；persona drift 難以追蹤；無法動態更新 | 最個人化，但維護成本最高 |

### 切入點差異

- **System Prompt 注入** vs `search-from-mybrain`：前者是靜態規則，後者是動態檢索。`search-from-mybrain` 能取得 system prompt 無法承載的動態事實（如「已評估過 DeepSpec 且 reject」）。
- **Agent Memory** vs `search-from-mybrain`：前者自動但不可控，後者手動維護但精確。`search-from-mybrain` 的資料來源是使用者自行撰寫的 markdown，使用者對內容有完全控制權。
- **RAG on 使用者文件** vs `search-from-mybrain`：前者用語意檢索，後者用結構化導航（骨幹檔 → grep → 全文）。`search-from-mybrain` 的「先讀骨幹檔再 grep」策略確保了關鍵上下文不會被語意檢索 miss。
- **Fine-tuned Persona Model** vs `search-from-mybrain`：前者是模型層的個人化，後者是 prompt 層的個人化。`search-from-mybrain` 不需要訓練資源，更新成本極低。
