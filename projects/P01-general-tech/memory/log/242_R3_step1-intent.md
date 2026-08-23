# 242_R3_step1-intent.md

## 狀況理解

R3 是 R2 之後的追問，標的仍為 Switchyard（NVIDIA-NeMo）。R2 已回答「Switchyard vs OmniRoute 廣度差異」與兩套安裝手順，並結論：OmniRoute 內建聚合 340 Provider／90+ free；Switchyard 無 Provider 目錄，廣度＝使用者手動 route 清單。

R3 使用者把兩者推向「結合」：想用 **OmniRoute 維護免費 provider 聚合＋fallback 規則**，把結果餵給 **Switchyard**（基於特定寫法給 opencode/claudecode 自動切換對應 model），做到「用量用完自動 fallback」。使用者並提出自己想像的指令腳本（`omniroute gen-switchyard.toml`、`switchyard update opencode/claudecode`），明講預設沒有也沒事，甚至可接受用 AI 產出確定性 wrapping 程式碼來做轉換，前提是「思想能對上」。

R3 要答三件事：① 結合是否可行；② 若可行，具體配置步驟；③ 用到 AI wrapping 部分給 prompt 骨子。

**「第二步大腦」檢索發現（先查再定調）：**
- OmniRoute 在 MyBrain 已有評判 → **Accept**，判定理由「本質是 LLM Provider 解耦層，有學習必要，MVP 階段導入」。URL: https://github.com/FATESAIKOU/MyBrain/blob/main/技術/技術評估/OmniRoute.md（generated.by: `opencode/deepseek-v4-pro`，status: `draft`，2026-07-26）——注意是 AI 產、未 review，屬「AI 草稿」。此 Accept 符合使用者 R2 自述「我 Accept OmniRoute」。
- Switchyard 在第二大腦查無既有評估／動手做紀錄——直接寫「第二大腦無此主題」，不填空。
- 連結到進行中專案：下一步清單「LLM APIGateway 試用（解耦）——OmniRoute」一條（`技術-動手做`，優先度低，期限 `—`，理由是「判定為採用但尚未 MVP 驗證；MVP 階段要比較多個應用，那個比較還沒做」，對照組 LiteLLM／OpenRouter／Portkey）。URL: https://github.com/FATESAIKOU/MyBrain/blob/main/專案/下一步清單.md（generated.by: `claude-code/opus-5`，status: `draft`，2026-08-11）。R3 這個「結合兩套」的構想，正是這條「比較多個應用」尚未完成的延伸。
- 取捨準則：`技術取捨準則.md`（`claude-code/opus-5`，draft，2026-08-01）——「不夠穩定或不熟悉就先自己兜，MVP 是理解驗證點」「AI 產出確定性程式碼當 wrapping」符合他的 harness 驗證偏好；且他明言可接受「用 AI 產出確定性 wrapping 程式碼」，與「Harness 驗證程式化」精神一致。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| 讀 PR body R3 三問 | 抓 R3 意圖 | 掌握核心需求 | 需求＝OmniRoute 免費聚合 + Switchyard fallback 的結合可行性與步驟 |
| mybrain-read 查 OmniRoute | 確認標的既有評判 | 拿到判定與理由 | Accept、draft、解耦層有學習必要 |
| mybrain-read 查 Switchyard | 確認是否評過 | 確認結論 | 第二大腦無此主題 |
| mybrain-read 查下一步清單 | 連結進行中專案 | 找到動線 | 命中「OmniRoute 試用」一條，R3 為其延伸 |
| mybrain-read 查取捨準則 | 確認判準 | 對齊準則 | 確認「自己兜＋MVP 驗證」取向；可接受 AI 產確定性 wrapper |

## 動作結束後的現狀

| 驗證面向 | 驗證方式 | 結果 |
|---|---|---|
| OmniRoute 既有評判 | MyBrain | Accept（draft），MVP 階段導入 |
| Switchyard 是否評過 | MyBrain | 無此主題（需回報，不填空） |
| 進行中專案連結 | 下一步清單 | 命中「OmniRoute APIGateway 試用」一條 |
| 取捨準則 | 骨幹 | 「先自己兜＋MVP 驗證」相符；AI 包 wrapper 與 harness 驗證取向相容 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇 | 理由 |
|---|---|---|---|
| R3 核心意圖 | 深挖任一單元 / 融合 OmniRoute+Switch 可行性 | 融合可行性 | 使用者三問皆圍繞「免費聚合+fallback」結合 |
| OmniRoute 判定 | 當確立事實 / 標 draft | 標 draft | MyBrain 檔案是 AI 產生未 review，轉述需留餘地 |
| Switchyard 定位 | 接既有評估 / 當新標的 | 當新標的 | 第二大腦無此主題 |
| 下一步方向 | 直接給步驟 / 先對齊「思想能对上」前提 | 先確認思想是否對上 | 使用者明言「前提是思想能对上」，可行性取決此點 |
