# 232_R2_step2-plan_C1.md

## 狀況理解

R2 是追問輪，使用者已基本偏向 Reject，但要求把 macro 從「要不要採用」轉向「能借鑑什麼、怎麼套用」。三題：① 最可能借鑑的地方與方式；② 套用到個人 workflow 的 pattern；③ 利用範圍（個人/團隊/公司）× 利用領域（日常業務/程式開發/非日常業務）的可用性矩陣。

R1 已取得 repo metadata、README、unified-memory、blocks、faq、docs 等核心事實。C1 不需重做 R1，而是**針對 R2 三題的意圖補查**：借鑑點需要「資料模型原語」細節（blocks/mentions/properties/tagging）；套用 pattern 需要「agent 工作流」細節（agents/automations/recipes）；可用性矩陣需要「個人 vs 團隊 vs 公司」與「self-host/授權」細節（faq/teams）。C1 聚焦「取得事實」，不評論好壞。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| webfetch docs.macro.com/llms.txt | 取得文件索引 | 盤點官方文件，定位 R2 相關頁 | 完整索引：product/、concepts/、AI/、integrations/、account/、changelog/ |
| webfetch concepts/blocks | 補查「一切皆 block」資料模型原語 | 支撐借鑑點①（資料模型） | 16 種 block 型別；References 面板（backlink）；Loro CRDT + Cloudflare Durable Objects；embeds/previews |
| webfetch concepts/mentions | 補查 @mention 雙向連結與權限 | 支撐借鑑點①（連結語意） | @mention 跨所有 markdown 面；channel 內 mention 自動分享；email 內 mention 加 CC；agent 繼承權限 |
| webfetch concepts/properties | 補查結構化欄位系統 | 支撐借鑑點①（結構化資料） | 統一 property 系統跨 block；STRING/NUMBER/BOOLEAN/DATE/SELECT/ENTITY/LINK 型別；system vs custom |
| webfetch product/tagging | 補查跨 block 標籤 | 支撐借鑑點①（跨域組織） | 單一 tag 命名空間跨所有 block；personal vs team tag；Any/All 過濾 |
| webfetch product/search | 補查統一檢索 | 支撐借鑑點①（可計算性） | <50ms 跨 email/tasks/docs/calls/agents/files；全文索引；tag 過濾 |
| webfetch product/agents | 補查 agent 工作流 | 支撐套用 pattern② | agents 從 unified memory 工作；@Macro 進 channel；automation 排程；MCP server；model picker |
| webfetch AI/recipes | 補查 agent 使用範本 | 支撐套用 pattern② | 8 個 copy-paste 範本：daily inbox brief、project status、weekly recap、call→tasks、draft reply、channel 問答、import、Claude Code 整合 |
| webfetch product/unified-memory | 補查記憶機制細節 | 支撐借鑑點①與可用性矩陣③ | 每晚 cron 合成；個人 vs 團隊記憶；tasks/calls 預設進團隊記憶；email 依 CRM 情境自動分享 |
| webfetch faq | 補查個人/團隊/公司定位與 self-host | 支撐可用性矩陣③ | 個人與團隊同價；teams 才有團隊記憶；self-host 可行但非 focus（2026-06）；AGPLv3 copyleft；solo 與 team 皆可用 |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| 借鑑點①資料模型 | blocks/mentions/properties/tagging | 可借鑑原語：一切皆 block、@mention 雙向連結、統一 property、跨 block tag、統一 search |
| 借鑑點①記憶機制 | unified-memory | 每晚 cron 合成；個人 vs 團隊兩層；markdown 儲存；無防腐化閘門（與 R1 一致） |
| 套用 pattern② | agents/automations/recipes | 8 個可套用範本；automation 排程；@Macro 進 channel；MCP 對外 |
| 可用性矩陣③ | faq/teams/unified-memory | 個人與團隊同價；團隊記憶需 teams；self-host 可行但非 focus；AGPLv3 copyleft |
| 是否重做 R1 | 對照 R1 C1 | 未重做；R1 已取得 metadata/README/核心機制，C1 只補 R2 三題所需細節 |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| C1 範圍 | 重做 R1 全部 / 只補 R2 三題所需 | 只補 R2 三題所需 | R1 已取得 metadata 與核心機制，R2 是「借鑑/套用/可用性」，需的是原語細節與工作流範本 |
| 借鑑點資料來源 | 只靠 README / 深入 concepts 子頁 | 深入 concepts 子頁 | 借鑑點①要「怎麼借」，需 blocks/mentions/properties/tagging 的具體原語，README 一句話不夠 |
| 套用 pattern 來源 | 泛談 / 用官方 recipes 對照 | 用官方 recipes 對照 | recipes 是官方給的「可複製 prompt」，是套用 pattern 最直接的素材，可對照使用者個人 workflow |
| 可用性矩陣來源 | 只靠定位描述 / 補查 teams+self-host+授權 | 補查 teams+self-host+授權 | 矩陣要判「個人/團隊/公司 × 領域」，需 teams 定價、團隊記憶門檻、self-host 可行性、AGPL 限制 |
| 是否查 changelog | 是 / 否 | 否（留 C2） | C1 已足夠支撐三題；changelog 的近期功能演進留待 C2 補查 |
