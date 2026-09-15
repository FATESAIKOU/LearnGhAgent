# 256_R1_step2-plan_C1.md

## 狀況理解

R1 首次調研標的為 **sub2api**（`Wei-Shaw/sub2api`）。本 sub-step C1 依 document skill 標準動作：取得 repo metadata、擷取 README 與關鍵子文件、補查背景脈絡。目標是建立「問題定義、核心機制、架構邊界」的事實基礎，供後續 sub-step（替代方案）與 Step 3 報告撰寫使用。無先前輪次，不需針對舊意圖。

## 執行的動作與結果

| 執行的動作 | 動作的目的 | 預期達成效果 | 實際的結果 |
|---|---|---|---|
| `gh repo view Wei-Shaw/sub2api --json ...` | 取得 repo metadata | 確認 stars、license、分支、語言、活躍度 | 取得：Go、LGPL-3.0、**41592 stars / 8695 forks**、created 2025-12-18、pushed 2026-09-15（當日活躍）、description「一站式开源中转服务，让 Claude/OpenAI/Gemini/Grok 订阅统一接入，支持拼车共享分摊成本」 |
| 淺 clone 至 /tmp/opencode/sub2api | 取得完整文件與程式結構 | 檢視 README 全文、docs、backend 架構 | 取得 repo 全貌：README 905 行（中/英/日三語）、backend（Go）、frontend（Vue3）、deploy、openspec、docs/ |
| 讀 README Overview/Features/Tech Stack | 理解定位與能力 | 確認「解決什麼」與功能邊界 | 取得：**AI API Gateway Platform for Subscription Quota Distribution**；核心為多帳號管理、API Key 配發、token 級計費、智慧排程（sticky session）、併發/速率限制、內建支付、Admin 儀表板、Composite Groups |
| 讀 README Grok/Simple Mode/Async Image | 理解多供應商支援與模式 | 確認帳號型態與協定覆蓋 | 取得：支援 OAuth（Grok/OpenAI/Gemini/Claude）與 API Key 兩類帳號；Grok 走 `cli-chat-proxy.grok.com` 訂閱 proxy；Simple Mode 為個人/團隊免 SaaS 計費模式 |
| 讀 README Project Structure | 理解架構分層 | 建立 module 心智模型 | 取得：backend/cmd/server 入口、internal/{config,model,service,handler,gateway}、frontend Vue3、deploy docker-compose+install.sh |
| 掃 backend/internal 目錄與 go.mod | 核實技術棧與模組 | 確認實作框架 | 取得：Gin + Ent + PostgreSQL15 + Redis7 + Vue3；帳號/認證/支付/計費/admin 模組齊全；含 codex CLI、image generation、OAuth captcha 等 |
| 掃 docs/ 與 openspec/changes | 定位關鍵子文件 | 確認官方深度文件 | 取得：PAYMENT、ASYNC_IMAGE_TASKS、COMPOSITE_GROUPS、PLUGIN_DEVELOPMENT、channel-monitor-v2 等；openspec 兩筆變更（OpenAI 相容 prompt audit、codex manifest） |

## 動作結束後的現狀

| 驗證的面向 | 驗證的內容與方式 | 驗證結果 |
|---|---|---|
| repo metadata | gh repo view | 41592 stars、LGPL-3.0、Go 為主、2025-12-18 建立、當日活躍 |
| 定位與能力 | README Overview/Features | subscription quota 分發平台；多帳號/API Key/token 計費/智慧排程/內建支付 |
| 供應商與協定 | README Grok/Simple/OAuth | Claude/OpenAI/Gemini/Grok 訂閱統一接入；OAuth+API Key；走訂閱 proxy |
| 架構分層 | Project Structure + 目錄掃描 | Go backend（Gin+Ent）+ Vue3 frontend + PG + Redis |
| 官方深度文件 | docs/ + openspec | PAYMENT/ASYNC_IMAGE/COMPOSITE_GROUPS/PLUGIN_DEV 等子文件存在，可作 C2 佐證 |
| 本 step 產出 | memory/log/256_R1_step2-plan_C1.md | 已產出，含 4 section |

## 其中的決斷點

| 意思決定面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---|---|---|---|
| clone 方式 | 深 clone / 淺 clone（depth 1） | 淺 clone | 僅需文件與目錄結構，不需歷史；省時間 |
| README 語言 | 英 / 中 / 日 | 英文為主，中文本為參考 | 英文為權威且已讀全文；中文 description 提供定位補充 |
| 背景脈絡補查 | 本 step 內完成 / 留待 C2 | 留待 C2 | C1 聚焦 repo 內部事實；替代方案（New API / one-api / LiteLLM / subconverter 等）與 ToS 合規背景屬外部脈絡，歸 C2 處理 |
| 子文件深讀 | 本 step 全讀 / 僅掃標題留待後續 | 僅掃標題，深讀留待 C2 依報告需求 | 六個 docs 檔內容多，C1 已確認存在與主題；Step 3 撰寫時若需再逐篇取用 |
